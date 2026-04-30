"""
Search RSA description generator for the google_ads_agent copy engine.

Generates 2-4 descriptions per ad group following Google's RSA slot roles:
  D1 - pas           : Problem -> Agitate -> Solution in one sentence
  D2 - proof_cta     : Benefit + social proof element + booking CTA verb
  D3 - differentiator: Insurance/unique qualifier + CTA (optional)
  D4 - geo_urgency   : Location-specific or urgency signal (optional)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from copy_engine.context import AdGroupContext
from copy_engine.models import OpenRouterClient

# Google RSA hard limit
CHAR_LIMIT = 90

# Banned words (healthcare policy + Google policy)
BANNED_WORDS = {"guaranteed", "guarantee", "cure", "cures", "treat", "treats",
                "treating", "treatment", "diagnose", "diagnoses", "diagnosing"}

# Valid role identifiers
VALID_ROLES = {"pas", "proof_cta", "differentiator", "geo_urgency"}

# Role order used when sorting output
ROLE_ORDER = ["pas", "proof_cta", "differentiator", "geo_urgency"]

SYSTEM_PROMPT = """\
You are a Google Ads RSA copywriter. You write tightly compressed, benefit-led \
descriptions for Responsive Search Ads. Each description is a standalone unit - \
Google rotates them independently, so they must never reference each other.

Hard rules you must never break:
- Max 90 characters per description (count every character including spaces)
- No exclamation marks
- Never start with "We"
- Never use: guaranteed, guarantee, cure, treat, diagnose (or any inflection)
- No repeating the same core benefit across two or more descriptions
- Every description must end with a period or a CTA verb (never mid-sentence)
- At least 2 descriptions must include the primary keyword naturally (not forced)

Role definitions:
  pas           - Problem -> Agitate -> Solution compressed into one sentence
  proof_cta     - Lead with a concrete benefit, add a social proof element, \
end with a booking/action CTA verb
  differentiator - Highlight a unique qualifier (insurance accepted, \
specialist credential, etc.) and optionally close with a CTA
  geo_urgency   - Anchor to a specific location or genuine urgency signal

Output format: valid JSON array only, no markdown, no code fences.
Schema: [{"text": "<description>", "role": "<role>"}]
"""


def _build_user_prompt(ctx: AdGroupContext, count: int) -> str:
    geo_str = ", ".join(ctx.geo) if ctx.geo else "your area"
    kw_str = ", ".join(ctx.top_keywords[:5]) if ctx.top_keywords else ctx.service
    usp_str = "\n".join(f"- {u}" for u in ctx.USPs) if ctx.USPs else "- (none provided)"
    ins_str = (", ".join(ctx.insurance_accepted)
               if ctx.insurance_accepted else "not specified")

    roles_needed = ROLE_ORDER[:count]
    role_block = "\n".join(f"  {r}" for r in roles_needed)

    extra = f"\nExtra context: {ctx.additional_context}" if ctx.additional_context else ""

    return f"""\
Ad group: {ctx.name}
Service: {ctx.service}
Industry: {ctx.industry}
Locations: {geo_str}
Primary keywords: {kw_str}
USPs:
{usp_str}
Insurance accepted: {ins_str}
Practice name: {ctx.practice_name or "not specified"}{extra}

Write exactly {count} description(s) in this role order:
{role_block}

Remember: each description <= 90 characters, no exclamation marks, no banned \
words, at least 2 must include a primary keyword naturally, no repeated benefits, \
never start with "We", must end with period or CTA verb.
"""


@dataclass
class Description:
    text: str
    char_count: int
    role: str  # pas | proof_cta | differentiator | geo_urgency


class DescriptionGenerator:
    def __init__(self, client: OpenRouterClient) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, ctx: AdGroupContext, count: int = 4) -> list[Description]:
        """
        Generate RSA descriptions for the given ad group context.

        Args:
            ctx:   AdGroupContext with service, geo, USPs, keywords, etc.
            count: Number of descriptions to generate (2-4).

        Returns:
            List of Description objects, one per requested slot.

        Raises:
            ValueError: If count is out of range or LLM output cannot be parsed.
        """
        if not 2 <= count <= 4:
            raise ValueError(f"count must be between 2 and 4, got {count}")

        schema = [{"text": "string", "role": "pas|proof_cta|differentiator|geo_urgency"}]
        user_prompt = _build_user_prompt(ctx, count)

        raw: list[dict] = self._client.complete_json(
            system=SYSTEM_PROMPT,
            user=user_prompt,
            schema=schema,
            max_tokens=600,
        )

        descriptions = self._parse(raw)
        violations = self.validate(descriptions, ctx)

        # Retry once if D1 is not PAS or fewer than 2 descriptions contain
        # the primary keyword - the two most common structural failures.
        needs_retry = self._needs_retry(violations)
        if needs_retry:
            print(
                f"[descriptions] Retry triggered. Violations: {violations}"
            )
            retry_prompt = (
                user_prompt
                + "\n\nPrevious attempt failed these checks:\n"
                + "\n".join(f"- {v}" for v in violations)
                + "\nFix all issues and regenerate."
            )
            raw = self._client.complete_json(
                system=SYSTEM_PROMPT,
                user=retry_prompt,
                schema=schema,
                max_tokens=600,
            )
            descriptions = self._parse(raw)

        return descriptions

    def validate(
        self, descriptions: list[Description], ctx: AdGroupContext
    ) -> list[str]:
        """
        Validate a list of Description objects against all copy rules.

        Returns:
            List of human-readable violation strings. Empty = all clear.
        """
        violations: list[str] = []

        if len(descriptions) < 2:
            violations.append(
                f"Too few descriptions: got {len(descriptions)}, need at least 2."
            )
        if len(descriptions) > 4:
            violations.append(
                f"Too many descriptions: got {len(descriptions)}, max is 4."
            )

        seen_benefits: list[str] = []

        for i, desc in enumerate(descriptions, start=1):
            label = f"D{i} ({desc.role})"

            # Character limit
            if desc.char_count > CHAR_LIMIT:
                violations.append(
                    f"{label}: {desc.char_count} chars exceeds {CHAR_LIMIT} limit."
                )

            # Role validity
            if desc.role not in VALID_ROLES:
                violations.append(
                    f"{label}: unknown role '{desc.role}'."
                )

            # No exclamation marks
            if "!" in desc.text:
                violations.append(f"{label}: contains exclamation mark.")

            # Must not start with "We"
            if re.match(r"^We\b", desc.text, re.IGNORECASE):
                violations.append(f"{label}: starts with 'We'.")

            # Must end with period or CTA verb (not mid-sentence)
            if not _ends_cleanly(desc.text):
                violations.append(
                    f"{label}: does not end with a period or CTA verb."
                )

            # Banned words
            text_lower = desc.text.lower()
            for word in BANNED_WORDS:
                pattern = rf"\b{re.escape(word)}\b"
                if re.search(pattern, text_lower):
                    violations.append(
                        f"{label}: contains banned word '{word}'."
                    )
                    break

            # Duplicate benefit check (simple: flag if first 4 words repeat)
            lead = " ".join(desc.text.split()[:4]).lower()
            if lead in seen_benefits:
                violations.append(
                    f"{label}: opens with the same benefit as a previous description."
                )
            seen_benefits.append(lead)

        # D1 must be PAS role
        if descriptions and descriptions[0].role != "pas":
            violations.append(
                f"D1 role is '{descriptions[0].role}', expected 'pas'."
            )

        # At least 2 descriptions must contain the primary keyword
        keyword_hits = _count_keyword_hits(descriptions, ctx)
        if keyword_hits < 2:
            violations.append(
                f"Only {keyword_hits} description(s) contain a primary keyword; "
                f"need at least 2."
            )

        return violations

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse(self, raw: list[dict]) -> list[Description]:
        """Convert raw LLM JSON output into Description objects."""
        descriptions: list[Description] = []
        for item in raw:
            text = str(item.get("text", "")).strip()
            role = str(item.get("role", "")).strip().lower()
            descriptions.append(
                Description(
                    text=text,
                    char_count=len(text),
                    role=role,
                )
            )
        return descriptions

    def _needs_retry(self, violations: list[str]) -> bool:
        """True if any retry-triggering violation is present."""
        for v in violations:
            if "D1 role" in v and "expected 'pas'" in v:
                return True
            if "primary keyword" in v:
                return True
        return False


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _ends_cleanly(text: str) -> bool:
    """
    Return True if the text ends with a period or a recognized CTA verb.
    Allows for trailing whitespace.
    """
    stripped = text.rstrip()
    if stripped.endswith("."):
        return True
    # Common CTA verb endings (case-insensitive last word check)
    cta_verbs = {
        "book", "call", "schedule", "start", "get", "learn", "explore",
        "discover", "contact", "visit", "apply", "claim", "register",
        "request", "find", "see", "try",
    }
    last_word = stripped.split()[-1].lower().rstrip(".,!?") if stripped else ""
    return last_word in cta_verbs


def _count_keyword_hits(
    descriptions: list[Description], ctx: AdGroupContext
) -> int:
    """Count how many descriptions contain at least one primary keyword."""
    if not ctx.top_keywords:
        return len(descriptions)  # no keywords to check against - pass through

    keywords_lower = [kw.lower() for kw in ctx.top_keywords]
    hits = 0
    for desc in descriptions:
        text_lower = desc.text.lower()
        if any(kw in text_lower for kw in keywords_lower):
            hits += 1
    return hits
