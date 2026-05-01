"""
Search RSA headline generator for the google_ads_agent copy engine.

Generates 8-15 validated headlines per ad group with enforced mix types,
character limits, and forbidden word/pattern rejection.
"""

import re
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from copy_engine.context import AdGroupContext
from copy_engine.models import OpenRouterClient


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CHAR_LIMIT = 30
MIN_HEADLINES = 8
MAX_HEADLINES = 15

VALID_MIX_TYPES = {
    "keyword_lead",
    "benefit_lead",
    "question",
    "proof",
    "geo",
    "cta",
}

# Minimum required count per mix type
MIX_REQUIREMENTS: dict[str, int] = {
    "keyword_lead": 3,
    "benefit_lead": 2,
    "question": 1,
    "proof": 1,
    "geo": 1,
    "cta": 1,
}

# Words that trigger auto-rejection (case-insensitive whole-word match)
FORBIDDEN_WORDS = {
    "streamline",
    "streamlines",
    "streamlined",
    "streamlining",
    "innovative",
    "innovation",
    "cutting-edge",
    "best-in-class",
    "world-class",
    "comprehensive",
    "robust",
    "leverage",
    "leverages",
    "leveraged",
    "leveraging",
    "utilize",
    "utilizes",
    "utilized",
    "utilizing",
    "solution",
    "solutions",
    "seamless",
    "seamlessly",
}

# Known acronyms that are exempt from the ALL CAPS check
ALLOWED_ACRONYMS = {
    "ADHD",
    "PTSD",
    "EMDR",
    "OCD",
    "LGBTQ",
    "LGBTQIA",
    "ASD",
    "IOP",
    "PHP",
    "CBT",
    "DBT",
    "TMS",
    "ECT",
    "MDMA",
    "HIV",
    "AIDS",
    "STD",
    "STI",
    "CPR",
    "AED",
    "MRI",
    "CT",
    "ER",
    "ICU",
    "OB",
    "GYN",
    "ENT",
    "VA",
    "DC",
    "NY",
    "LA",
    "SF",
    "TX",
    "FL",
    "GA",
    "MD",
    "MA",
    "PA",
    "NJ",
    "OH",
    "IN",
    "IL",
    "WA",
    "OR",
    "CO",
    "AZ",
    "NV",
    "MN",
    "WI",
    "MO",
    "TN",
    "NC",
    "SC",
    "AL",
    "MS",
    "AR",
    "LA",
    "OK",
    "KS",
    "NE",
    "IA",
    "SD",
    "ND",
    "MT",
    "WY",
    "ID",
    "UT",
    "NM",
    "AK",
    "HI",
    "PR",
    "USA",
    "US",
    "UK",
    "PPC",
    "SEO",
    "ROI",
    "KPI",
    "CTA",
    "API",
    "SaaS",
}

# Healthcare policy-sensitive words - rejected when industry is healthcare/mental_health
HEALTHCARE_FORBIDDEN = {
    "cure",
    "cures",
    "cured",
    "curing",
    "treat",
    "treats",
    "treated",
    "treating",
    "treatment",
    "diagnose",
    "diagnoses",
    "diagnosed",
    "diagnosing",
    "diagnosis",
    "guaranteed",
    "guarantee",
}

HEALTHCARE_INDUSTRIES = {"healthcare", "mental_health", "medical", "therapy"}

# Semantic duplicate threshold - headline pairs with word overlap above this are rejected
SEMANTIC_OVERLAP_THRESHOLD = 0.60

# ---------------------------------------------------------------------------
# Prompt fragments (loaded from framework files at class build time)
# ---------------------------------------------------------------------------

_AD_COPY_TEMPLATES_HEADLINE_SECTION = """
## Headline Formulas for Search Ads

| Formula | Example |
|---------|---------|
| [Keyword] + [Benefit] | "Project Management That Teams Actually Use" |
| [Action] + [Outcome] | "Automate Reports | Save 10 Hours Weekly" |
| [Question] | "Tired of Manual Data Entry?" |
| [Number] + [Benefit] | "500+ Teams Trust [Product] for [Outcome]" |
| [Keyword] + [Differentiator] | "CRM Built for Small Teams" |
| [Price/Offer] + [Keyword] | "Free Project Management | No Credit Card" |

### Google Search Ads platform rules
- Headline limits: 30 characters each (up to 15 headlines per RSA)
- Include keywords naturally
- Use all available headline slots
- Include numbers and stats when possible
"""

_COPY_FRAMEWORKS_HEADLINE_SECTION = """
## Headline Formulas

### Outcome-Focused
- {Achieve desirable outcome} without {pain point}
- {Achieve desirable outcome} by {how product makes it possible}
- Turn {input} into {outcome}
- [Achieve outcome] in [timeframe]

### Problem-Focused
- Never {unpleasant event} again
- {Question highlighting the main pain point}
- Stop [pain]. Start [pleasure].

### Audience-Focused
- {Key feature/product type} for {target audience}

### Differentiation-Focused
- The [category] that [key differentiator]

### Proof-Focused
- [Number] [people] use [product] to [outcome]

### Additional Formulas
- The simple way to {outcome}
- {Outcome} without {common pain}
- What if you could {desirable outcome}?
- Everything you need to {outcome}
"""

# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass
class Headline:
    text: str
    char_count: int
    mix_type: str  # keyword_lead | benefit_lead | question | proof | geo | cta


# ---------------------------------------------------------------------------
# HeadlineGenerator
# ---------------------------------------------------------------------------


class HeadlineGenerator:
    """
    Generates validated RSA headlines for a Google Ads ad group.

    Uses OpenRouter (Kimi-K2 by default) to produce headlines, then enforces:
    - 30-char hard limit
    - Mix type requirements (keyword_lead x3, benefit_lead x2, etc.)
    - Forbidden words / ALL CAPS / exclamation rejection
    - Semantic duplicate detection
    - Root-word repetition check (same root in 3+ headlines)
    - Healthcare policy-sensitive word rejection
    """

    def __init__(self, client: OpenRouterClient):
        self._client = client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, ctx: AdGroupContext, count: int = 12) -> list[Headline]:
        """
        Generate and validate headlines for the given ad group context.

        Args:
            ctx:   AdGroupContext with service, geo, keywords, USPs, industry, etc.
            count: Target number of headlines (clamped to MIN_HEADLINES..MAX_HEADLINES).

        Returns:
            Validated list of Headline objects meeting all mix requirements.

        Raises:
            RuntimeError: If mix requirements cannot be met after 2 retry attempts.
        """
        count = max(MIN_HEADLINES, min(MAX_HEADLINES, count))

        system_prompt = self._build_system_prompt(ctx)
        user_prompt = self._build_user_prompt(ctx, count, gaps=None)

        raw = self._client.complete_json(
            system=system_prompt,
            user=user_prompt,
            schema={"type": "array", "items": {"type": "object", "properties": {"text": {"type": "string"}, "mix_type": {"type": "string"}}}},
            max_tokens=1500,
        )
        headlines = self._parse_raw(raw)
        headlines = self._filter(headlines, ctx)

        # Retry loop - up to 2 attempts to fill mix gaps
        for attempt in range(2):
            gaps = self._find_mix_gaps(headlines)
            if not gaps:
                break
            gap_prompt = self._build_user_prompt(ctx, count, gaps=gaps)
            raw_retry = self._client.complete_json(
                system=system_prompt,
                user=gap_prompt,
                schema={"type": "array", "items": {"type": "object", "properties": {"text": {"type": "string"}, "mix_type": {"type": "string"}}}},
                max_tokens=1000,
            )
            new_batch = self._parse_raw(raw_retry)
            new_batch = self._filter(new_batch, ctx)
            headlines = self._merge_deduped(headlines, new_batch, ctx)

        final_gaps = self._find_mix_gaps(headlines)
        if final_gaps:
            gap_summary = ", ".join(
                f"{mix_type} needs {needed} more"
                for mix_type, needed in final_gaps.items()
            )
            raise RuntimeError(
                f"HeadlineGenerator: mix requirements not met after 2 retries. "
                f"Remaining gaps: {gap_summary}"
            )

        return headlines[:MAX_HEADLINES]

    def validate(self, headlines: list[Headline]) -> list[str]:
        """
        Validate a list of headlines and return all violation strings.

        Args:
            headlines: List of Headline objects to check.

        Returns:
            List of human-readable violation strings. Empty list = all clean.
        """
        violations: list[str] = []

        for hl in headlines:
            violations.extend(self._check_single(hl.text, hl.mix_type))

        # Cross-headline checks
        violations.extend(self._check_root_repetition([hl.text for hl in headlines]))
        violations.extend(self._check_semantic_duplicates([hl.text for hl in headlines]))

        mix_gaps = self._find_mix_gaps(headlines)
        for mix_type, needed in mix_gaps.items():
            violations.append(
                f"Mix gap: need {needed} more '{mix_type}' headline(s)"
            )

        return violations

    # ------------------------------------------------------------------
    # Prompt builders
    # ------------------------------------------------------------------

    def _build_system_prompt(self, ctx: AdGroupContext) -> str:
        healthcare_note = ""
        if ctx.industry.lower() in HEALTHCARE_INDUSTRIES:
            healthcare_note = """
## Healthcare Industry Policy Rules
NEVER use these words - they violate Google Ads healthcare policies:
cure, cures, cured, curing, treat, treats, treated, treating, treatment,
diagnose, diagnoses, diagnosed, diagnosing, diagnosis, guaranteed, guarantee

Safe alternatives:
- Instead of "treat anxiety" -> "support for anxiety" or "anxiety care"
- Instead of "cure depression" -> "relief from depression" or "feel better"
- Instead of "diagnose ADHD" -> "ADHD evaluation" or "ADHD testing"
"""

        return f"""You are a Google Ads RSA headline copywriter. You write high-converting,
policy-compliant headlines for Search campaigns.

{_AD_COPY_TEMPLATES_HEADLINE_SECTION}

{_COPY_FRAMEWORKS_HEADLINE_SECTION}

## Mix Type Requirements
You MUST produce headlines labeled with these exact mix_type values:

| mix_type     | min_count | Formula |
|--------------|-----------|---------|
| keyword_lead | 3         | [Keyword] + [Benefit] |
| benefit_lead | 2         | [Outcome verb] + [Result] |
| question     | 1         | [Pain point?] |
| proof        | 1         | [Number/stat] + [Credibility] |
| geo          | 1         | [City/Region] + [Service] |
| cta          | 1         | [Action verb] + [Offer] |

## Hard Rules - Every headline MUST comply
1. Max 30 characters (including spaces). Count carefully before writing.
2. No exclamation marks (!) anywhere.
3. No ALL CAPS words (3+ uppercase letters) unless they are recognized acronyms
   like ADHD, PTSD, EMDR, OCD, CBT, DBT, IOP, PHP.
4. Never use these forbidden words (any form):
   streamline, innovative, cutting-edge, best-in-class, world-class,
   comprehensive, robust, leverage, utilize, solution, seamless
5. Each headline must be distinct - no two should say the same thing in different words.
6. Do not repeat the same root word (book, booking, booked) across 3 or more headlines.
{healthcare_note}
## Output Format
Return a JSON array only. No markdown. No explanation. No code fences.
Each item: {{"text": "<headline>", "mix_type": "<mix_type>"}}
"""

    def _build_user_prompt(
        self,
        ctx: AdGroupContext,
        count: int,
        gaps: Optional[dict[str, int]],
    ) -> str:
        geo_str = ", ".join(ctx.geo) if ctx.geo else "not specified"
        kw_str = ", ".join(ctx.top_keywords[:8]) if ctx.top_keywords else "not specified"
        usp_str = "\n".join(f"- {u}" for u in ctx.USPs) if ctx.USPs else "- not specified"
        ins_str = (
            ", ".join(ctx.insurance_accepted)
            if ctx.insurance_accepted
            else "not listed"
        )

        base = f"""Ad Group: {ctx.name}
Service: {ctx.service}
Practice / Brand: {ctx.practice_name or "not provided"}
Industry: {ctx.industry}
Locations: {geo_str}
Target Keywords: {kw_str}
USPs:
{usp_str}
Insurance Accepted: {ins_str}
Additional Context: {ctx.additional_context or "none"}

Write {count} headlines following all rules in the system prompt."""

        if gaps:
            gap_lines = "\n".join(
                f"- {needed} more '{mix_type}' headline(s)"
                for mix_type, needed in gaps.items()
            )
            base += f"""

IMPORTANT - The previous batch was missing these headline types. Generate ONLY these gap headlines:
{gap_lines}

Return only the gap headlines as a JSON array."""

        return base

    # ------------------------------------------------------------------
    # Parsing and filtering
    # ------------------------------------------------------------------

    def _parse_raw(self, raw: list | dict) -> list[Headline]:
        """Convert raw LLM JSON output into Headline objects, skipping malformed entries."""
        if isinstance(raw, dict):
            # Some models wrap the array in a key
            for key in ("headlines", "data", "results", "items"):
                if key in raw and isinstance(raw[key], list):
                    raw = raw[key]
                    break
            else:
                raw = list(raw.values())[0] if raw else []

        headlines: list[Headline] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            text = str(item.get("text", "")).strip()
            mix_type = str(item.get("mix_type", "")).strip().lower()
            if not text or mix_type not in VALID_MIX_TYPES:
                continue
            headlines.append(Headline(text=text, char_count=len(text), mix_type=mix_type))
        return headlines

    def _filter(self, headlines: list[Headline], ctx: AdGroupContext) -> list[Headline]:
        """
        Filter a list of headlines, removing any that fail single-headline checks.
        Cross-headline checks (root repetition, semantic duplicates) are applied
        after the mix is assembled.
        """
        passing: list[Headline] = []
        for hl in headlines:
            violations = self._check_single(hl.text, hl.mix_type)
            if not violations:
                # Update char_count after strip (LLM may have added spaces)
                hl.char_count = len(hl.text)
                passing.append(hl)
        # Apply cross-headline checks and remove offending headlines
        return self._apply_cross_checks(passing)

    def _apply_cross_checks(self, headlines: list[Headline]) -> list[Headline]:
        """Remove headlines that cause root repetition or semantic duplicate violations."""
        headlines = self._prune_root_repeats(headlines)
        headlines = self._prune_semantic_duplicates(headlines)
        return headlines

    def _merge_deduped(
        self,
        existing: list[Headline],
        new_batch: list[Headline],
        ctx: AdGroupContext,
    ) -> list[Headline]:
        """Add new headlines to existing list, re-applying cross-headline checks."""
        combined = existing + new_batch
        return self._apply_cross_checks(combined)

    # ------------------------------------------------------------------
    # Single-headline validation
    # ------------------------------------------------------------------

    def _check_single(self, text: str, mix_type: str) -> list[str]:
        violations: list[str] = []

        # Char limit
        if len(text) > CHAR_LIMIT:
            violations.append(
                f"'{text}' exceeds {CHAR_LIMIT} chars ({len(text)} chars)"
            )

        # Min length sanity
        if len(text) < 3:
            violations.append(f"'{text}' is too short to be a headline")

        # Exclamation mark
        if "!" in text:
            violations.append(f"'{text}' contains an exclamation mark")

        # ALL CAPS words (3+ uppercase letters, not in allowed acronyms)
        for word in re.findall(r"[A-Z]{3,}", text):
            if word not in ALLOWED_ACRONYMS:
                violations.append(
                    f"'{text}' contains ALL CAPS word '{word}' (not a recognized acronym)"
                )

        # Forbidden words
        text_lower = text.lower()
        for fw in FORBIDDEN_WORDS:
            # Use word boundary matching
            if re.search(r"\b" + re.escape(fw) + r"\b", text_lower):
                violations.append(f"'{text}' contains forbidden word '{fw}'")

        # Valid mix_type
        if mix_type not in VALID_MIX_TYPES:
            violations.append(f"'{mix_type}' is not a valid mix_type")

        return violations

    def check_single_healthcare(self, text: str) -> list[str]:
        """Additional check for healthcare industries. Call after check_single."""
        violations: list[str] = []
        text_lower = text.lower()
        for hw in HEALTHCARE_FORBIDDEN:
            if re.search(r"\b" + re.escape(hw) + r"\b", text_lower):
                violations.append(
                    f"'{text}' contains healthcare policy-sensitive word '{hw}'"
                )
        return violations

    # ------------------------------------------------------------------
    # Cross-headline validation helpers
    # ------------------------------------------------------------------

    def _check_root_repetition(self, texts: list[str]) -> list[str]:
        """
        Return violations for any root word (4+ chars) appearing in 3+ headlines.
        Uses a simple stem: lowercase first 5 chars as a proxy for root.
        """
        violations: list[str] = []
        root_to_headlines: dict[str, list[str]] = {}

        for text in texts:
            words = re.findall(r"[a-zA-Z]{4,}", text.lower())
            for word in set(words):
                root = word[:5]  # crude stem
                root_to_headlines.setdefault(root, [])
                if text not in root_to_headlines[root]:
                    root_to_headlines[root].append(text)

        for root, affected in root_to_headlines.items():
            if len(affected) >= 3:
                violations.append(
                    f"Root '{root}*' appears in {len(affected)} headlines: "
                    + ", ".join(f"'{h}'" for h in affected)
                )
        return violations

    def _prune_root_repeats(self, headlines: list[Headline]) -> list[Headline]:
        """
        Remove the later-occurring headlines that cause a root-word to appear
        in 3+ headlines, preserving the first two occurrences.
        """
        root_seen: dict[str, int] = {}  # root -> count so far
        kept: list[Headline] = []

        for hl in headlines:
            words = set(re.findall(r"[a-zA-Z]{4,}", hl.text.lower()))
            roots = {w[:5] for w in words}
            # Check if adding this headline would push any root to 3+
            would_exceed = any(root_seen.get(r, 0) >= 2 for r in roots)
            if would_exceed:
                continue
            # Accept headline and update counts
            for r in roots:
                root_seen[r] = root_seen.get(r, 0) + 1
            kept.append(hl)

        return kept

    def _check_semantic_duplicates(self, texts: list[str]) -> list[str]:
        """
        Return violations for pairs of headlines with >60% word overlap.
        Overlap = |intersection| / |union| (Jaccard similarity).
        """
        violations: list[str] = []
        tokenized = [set(re.findall(r"[a-z]+", t.lower())) for t in texts]

        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, b = tokenized[i], tokenized[j]
                if not a or not b:
                    continue
                overlap = len(a & b) / len(a | b)
                if overlap > SEMANTIC_OVERLAP_THRESHOLD:
                    violations.append(
                        f"Semantic duplicate ({overlap:.0%} overlap): "
                        f"'{texts[i]}' vs '{texts[j]}'"
                    )
        return violations

    def _prune_semantic_duplicates(self, headlines: list[Headline]) -> list[Headline]:
        """
        Remove later headlines that are semantic duplicates of an earlier one.
        Preserves order and keeps the first of each duplicate pair.
        """
        kept: list[Headline] = []
        tokenized_kept: list[set[str]] = []

        for hl in headlines:
            tokens = set(re.findall(r"[a-z]+", hl.text.lower()))
            is_dup = False
            for existing_tokens in tokenized_kept:
                if not existing_tokens:
                    continue
                overlap = len(tokens & existing_tokens) / len(tokens | existing_tokens)
                if overlap > SEMANTIC_OVERLAP_THRESHOLD:
                    is_dup = True
                    break
            if not is_dup:
                kept.append(hl)
                tokenized_kept.append(tokens)

        return kept

    # ------------------------------------------------------------------
    # Mix gap detection
    # ------------------------------------------------------------------

    def _find_mix_gaps(self, headlines: list[Headline]) -> dict[str, int]:
        """
        Return a dict of {mix_type: count_still_needed} for any type below minimum.
        Empty dict means all requirements are met.
        """
        counts: Counter[str] = Counter(hl.mix_type for hl in headlines)
        gaps: dict[str, int] = {}
        for mix_type, required in MIX_REQUIREMENTS.items():
            have = counts.get(mix_type, 0)
            if have < required:
                gaps[mix_type] = required - have
        return gaps
