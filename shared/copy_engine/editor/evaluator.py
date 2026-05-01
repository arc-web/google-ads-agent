"""
Copy rules evaluator for the google_ads_agent copy engine.

Flag-only - no auto-fixing. All checks are rule-based; no LLM calls.

Loaded at init from framework files:
  - frameworks/plain_english.md  -> word swap suggestions
  - frameworks/ad_character_limits.yaml -> hard character limits
"""

from __future__ import annotations

import re
import os
import yaml
from dataclasses import dataclass, field
from typing import Optional

# Resolve paths relative to this file so the evaluator works regardless
# of the caller's working directory.
_FRAMEWORKS_DIR = os.path.join(os.path.dirname(__file__), "..", "frameworks")
_PLAIN_ENGLISH_PATH = os.path.join(_FRAMEWORKS_DIR, "plain_english.md")
_CHAR_LIMITS_PATH = os.path.join(_FRAMEWORKS_DIR, "ad_character_limits.yaml")


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PolicyFlag:
    text: str           # full asset text that triggered the flag
    flagged_term: str   # exact matched term
    reason: str         # human-readable explanation


@dataclass
class WordSwap:
    text: str           # full asset text that triggered the swap suggestion
    original_word: str  # complex word found in text
    suggested_word: str # plain English alternative


@dataclass
class CharViolation:
    text: str           # full asset text
    actual_chars: int
    limit: int
    asset_type: str     # e.g. "headline", "description"
    reason: str = "max"


@dataclass
class MixGap:
    missing_type: str   # headline mix type or coverage category
    required_count: int
    actual_count: int


@dataclass
class EvalReport:
    policy_flags: list[PolicyFlag] = field(default_factory=list)
    word_swaps: list[WordSwap] = field(default_factory=list)
    char_violations: list[CharViolation] = field(default_factory=list)
    mix_gaps: list[MixGap] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        """True only when there are no policy flags, char violations, or mix gaps.
        Word swaps are suggestions and do not affect cleanliness."""
        return not (self.policy_flags or self.char_violations or self.mix_gaps)

    def merge(self, other: "EvalReport") -> None:
        """Merge another EvalReport into this one in-place."""
        self.policy_flags.extend(other.policy_flags)
        self.word_swaps.extend(other.word_swaps)
        self.char_violations.extend(other.char_violations)
        self.mix_gaps.extend(other.mix_gaps)


# ---------------------------------------------------------------------------
# Policy term definitions
# ---------------------------------------------------------------------------

# Each entry: (term, reason)
# Terms are matched case-insensitively as whole words where possible.
_POLICY_TERMS: list[tuple[str, str]] = [
    # Superlatives (unprovable)
    ("best",          "Superlative - requires substantiation or Google may disapprove"),
    ("#1",            "Superlative - requires substantiation or Google may disapprove"),
    ("leading",       "Superlative - requires substantiation or Google may disapprove"),
    ("top-rated",     "Superlative - requires substantiation or Google may disapprove"),
    ("top rated",     "Superlative - requires substantiation or Google may disapprove"),
    ("award-winning", "Superlative - requires substantiation or Google may disapprove"),
    ("award winning", "Superlative - requires substantiation or Google may disapprove"),

    # Misrepresentation
    ("guaranteed",   "Misrepresentation - absolute guarantees restricted by Google policy"),
    ("guarantee",    "Misrepresentation - absolute guarantees restricted by Google policy"),
    ("promise",      "Misrepresentation - promise language restricted by Google policy"),
    ("assured",      "Misrepresentation - absolute assurance language restricted"),
    ("100%",         "Misrepresentation - absolute percentage claims restricted"),
    ("always",       "Misrepresentation - absolute frequency claims restricted"),
    ("never fails",  "Misrepresentation - absolute reliability claims restricted"),

    # Healthcare restricted
    ("cure",          "Healthcare restricted - treatment outcome claims require care"),
    ("cures",         "Healthcare restricted - treatment outcome claims require care"),
    ("treat",         "Healthcare restricted - treatment claims require care"),
    ("treats",        "Healthcare restricted - treatment claims require care"),
    ("treatment",     "Healthcare restricted - verify this does not imply medical cure"),
    ("heal",          "Healthcare restricted - healing claims require care"),
    ("heals",         "Healthcare restricted - healing claims require care"),
    ("prevent",       "Healthcare restricted - prevention claims require care"),
    ("prevents",      "Healthcare restricted - prevention claims require care"),
    ("diagnose",      "Healthcare restricted - diagnostic claims require care"),
    ("diagnoses",     "Healthcare restricted - diagnostic claims require care"),
    ("medical advice","Healthcare restricted - do not imply professional medical advice"),

    # Sensitive
    ("emergency",        "Sensitive - may trigger policy review; use carefully"),
    ("crisis",           "Sensitive - may trigger policy review; use carefully"),
    ("life-threatening", "Sensitive - may trigger policy review"),
    ("life threatening", "Sensitive - may trigger policy review"),
    ("dangerous",        "Sensitive - may trigger policy review"),

    # Clickbait
    ("you won't believe", "Clickbait - Google disapproves sensationalist language"),
    ("you wont believe",  "Clickbait - Google disapproves sensationalist language"),
    ("shocking",          "Clickbait - Google disapproves sensationalist language"),
    ("secret",            "Clickbait - secretive language may trigger disapproval"),
    ("hack",              "Clickbait - 'hack' used as a shortcut tip is clickbait language"),
]


# ---------------------------------------------------------------------------
# Headline mix requirements
# ---------------------------------------------------------------------------

_HEADLINE_MIX_REQUIREMENTS: dict[str, int] = {
    "keyword_lead": 3,
    "benefit_lead": 2,
    "question":     1,
    "proof":        1,
    "geo":          1,
    "cta":          1,
}

_MIN_HEADLINES    = 8
_MIN_DESCRIPTIONS = 2
_MIN_KEYWORD_DESC = 2  # descriptions that must contain the primary keyword


# ---------------------------------------------------------------------------
# Loader helpers
# ---------------------------------------------------------------------------

def _load_word_swaps(md_path: str) -> dict[str, str]:
    """Parse plain_english.md and return {complex_word_lower: plain_alternative}."""
    swaps: dict[str, str] = {}
    table_row = re.compile(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|")
    try:
        with open(md_path, encoding="utf-8") as fh:
            for line in fh:
                m = table_row.match(line)
                if not m:
                    continue
                complex_word = m.group(1).strip()
                plain_alt    = m.group(2).strip()
                # Skip header rows
                if complex_word.lower() in ("complex", "---", "---"):
                    continue
                if complex_word.startswith("-"):
                    continue
                if complex_word and plain_alt and complex_word.lower() != "complex":
                    swaps[complex_word.lower()] = plain_alt
    except FileNotFoundError:
        pass
    return swaps


def _load_char_limits(yaml_path: str) -> dict[str, int]:
    """Load character limits from ad_character_limits.yaml.

    Returns a flat dict with the keys the evaluator actually uses:
        headline, description, sitelink_text, sitelink_description,
        callout, structured_snippet_value
    """
    limits: dict[str, int] = {
        # Sensible defaults if YAML is missing
        "headline":                 30,
        "headline_min":             25,
        "description":              80,
        "sitelink_text":            25,
        "sitelink_description":     35,
        "callout":                  25,
        "structured_snippet_value": 25,
    }
    try:
        with open(yaml_path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if not isinstance(data, dict):
            return limits

        rsa = data.get("responsive_search_ads", {})
        if rsa.get("headline_max_chars"):
            limits["headline"] = rsa["headline_max_chars"]
        if rsa.get("headline_min_chars"):
            limits["headline_min"] = rsa["headline_min_chars"]
        if rsa.get("description_max_chars"):
            limits["description"] = rsa["description_max_chars"]

        sitelink = data.get("sitelink_extensions", {})
        if sitelink.get("text_max_chars"):
            limits["sitelink_text"] = sitelink["text_max_chars"]
        if sitelink.get("description_max_chars"):
            limits["sitelink_description"] = sitelink["description_max_chars"]

        callout = data.get("callout_extensions", {})
        if callout.get("text_max_chars"):
            limits["callout"] = callout["text_max_chars"]

        snippet = data.get("structured_snippets", {})
        if snippet.get("values_max_chars"):
            limits["structured_snippet_value"] = snippet["values_max_chars"]

    except FileNotFoundError:
        pass
    return limits


# ---------------------------------------------------------------------------
# Main evaluator
# ---------------------------------------------------------------------------

class CopyEvaluator:
    """Rule-based copy evaluator. Flag-only, no auto-fixing, no LLM calls.

    Usage:
        ev = CopyEvaluator()
        report = ev.evaluate_headline("Best ADHD Testing in Ashburn")
        report = ev.evaluate_ad_group(headlines, descriptions, ctx)
    """

    def __init__(
        self,
        plain_english_path: str = _PLAIN_ENGLISH_PATH,
        char_limits_path:   str = _CHAR_LIMITS_PATH,
    ) -> None:
        self._word_swaps:  dict[str, str] = _load_word_swaps(plain_english_path)
        self._char_limits: dict[str, int] = _load_char_limits(char_limits_path)

    # ------------------------------------------------------------------
    # Public single-asset methods
    # ------------------------------------------------------------------

    def evaluate_headline(self, text: str) -> EvalReport:
        """Evaluate a single headline string."""
        report = EvalReport()
        self._check_policy(text, report)
        self._check_word_swaps(text, report)
        self._check_char_limit(text, "headline", report)
        self._check_min_char_quality(text, "headline", report)
        return report

    def evaluate_description(self, text: str) -> EvalReport:
        """Evaluate a single description string."""
        report = EvalReport()
        self._check_policy(text, report)
        self._check_word_swaps(text, report)
        self._check_char_limit(text, "description", report)
        return report

    def evaluate_sitelink(
        self,
        link_text: str,
        description: Optional[str] = None,
    ) -> EvalReport:
        """Evaluate a sitelink's link_text and optional description line."""
        report = EvalReport()
        self._check_policy(link_text, report)
        self._check_word_swaps(link_text, report)
        self._check_char_limit(link_text, "sitelink_text", report)
        if description:
            self._check_policy(description, report)
            self._check_word_swaps(description, report)
            self._check_char_limit(description, "sitelink_description", report)
        return report

    def evaluate_callout(self, text: str) -> EvalReport:
        """Evaluate a single callout string."""
        report = EvalReport()
        self._check_policy(text, report)
        self._check_word_swaps(text, report)
        self._check_char_limit(text, "callout", report)
        return report

    def evaluate_structured_snippet_value(self, text: str) -> EvalReport:
        """Evaluate a single structured snippet value string."""
        report = EvalReport()
        self._check_policy(text, report)
        self._check_word_swaps(text, report)
        self._check_char_limit(text, "structured_snippet_value", report)
        return report

    # ------------------------------------------------------------------
    # Ad group aggregate evaluation
    # ------------------------------------------------------------------

    def evaluate_ad_group(
        self,
        headlines: list[str],
        descriptions: list[str],
        ctx: "AdGroupContext",  # noqa: F821 - imported by callers
    ) -> EvalReport:
        """Aggregate all violations across all assets in an ad group.

        Also checks headline mix coverage and description keyword presence.

        Each headline dict may be either:
          - a plain str
          - a dict with at least {"text": str, "type": str}

        Passing dicts with a "type" key enables mix-type checking.
        """
        report = EvalReport()

        # --- Per-headline checks ---
        for item in headlines:
            text = item["text"] if isinstance(item, dict) else item
            report.merge(self.evaluate_headline(text))

        # --- Per-description checks ---
        for text in descriptions:
            report.merge(self.evaluate_description(text))

        # --- Mix compliance ---
        report.mix_gaps.extend(
            self._check_mix(headlines, descriptions, ctx)
        )

        return report

    # ------------------------------------------------------------------
    # Internal check helpers
    # ------------------------------------------------------------------

    def _check_policy(self, text: str, report: EvalReport) -> None:
        text_lower = text.lower()
        seen: set[str] = set()
        for term, reason in _POLICY_TERMS:
            if term in seen:
                continue
            # Whole-word match where the term is alpha-only; substring for
            # phrases or terms with punctuation like "#1".
            if _is_alpha_phrase(term):
                pattern = r"\b" + re.escape(term) + r"\b"
                matched = bool(re.search(pattern, text_lower))
            else:
                matched = term in text_lower
            if matched:
                seen.add(term)
                report.policy_flags.append(
                    PolicyFlag(text=text, flagged_term=term, reason=reason)
                )

    def _check_word_swaps(self, text: str, report: EvalReport) -> None:
        text_lower = text.lower()
        for complex_word, plain_alt in self._word_swaps.items():
            # Multi-word phrases: substring match; single words: whole-word
            if " " in complex_word:
                if complex_word in text_lower:
                    report.word_swaps.append(
                        WordSwap(
                            text=text,
                            original_word=complex_word,
                            suggested_word=plain_alt,
                        )
                    )
            else:
                pattern = r"\b" + re.escape(complex_word) + r"\b"
                if re.search(pattern, text_lower):
                    report.word_swaps.append(
                        WordSwap(
                            text=text,
                            original_word=complex_word,
                            suggested_word=plain_alt,
                        )
                    )

    def _check_char_limit(
        self, text: str, asset_type: str, report: EvalReport
    ) -> None:
        limit = self._char_limits.get(asset_type)
        if limit is None:
            return
        actual = len(text)
        if actual > limit:
            report.char_violations.append(
                CharViolation(
                    text=text,
                    actual_chars=actual,
                    limit=limit,
                    asset_type=asset_type,
                    reason="max",
                )
            )

    def _check_min_char_quality(
        self, text: str, asset_type: str, report: EvalReport
    ) -> None:
        minimum = self._char_limits.get(f"{asset_type}_min")
        if minimum is None:
            return
        actual = len(text)
        if actual < minimum:
            report.char_violations.append(
                CharViolation(
                    text=text,
                    actual_chars=actual,
                    limit=minimum,
                    asset_type=asset_type,
                    reason="min_value",
                )
            )

    def _check_mix(
        self,
        headlines: list,
        descriptions: list,
        ctx: "AdGroupContext",  # noqa: F821
    ) -> list[MixGap]:
        gaps: list[MixGap] = []

        # 1. Minimum headline count
        actual_hl_count = len(headlines)
        if actual_hl_count < _MIN_HEADLINES:
            gaps.append(
                MixGap(
                    missing_type="min_headlines",
                    required_count=_MIN_HEADLINES,
                    actual_count=actual_hl_count,
                )
            )

        # 2. Headline mix types - only checkable when items are dicts with "type"
        typed_headlines = [h for h in headlines if isinstance(h, dict) and "type" in h]
        if typed_headlines:
            type_counts: dict[str, int] = {}
            for h in typed_headlines:
                t = h["type"]
                type_counts[t] = type_counts.get(t, 0) + 1

            for mix_type, required in _HEADLINE_MIX_REQUIREMENTS.items():
                actual = type_counts.get(mix_type, 0)
                if actual < required:
                    gaps.append(
                        MixGap(
                            missing_type=mix_type,
                            required_count=required,
                            actual_count=actual,
                        )
                    )

        # 3. Minimum descriptions
        actual_desc_count = len(descriptions)
        if actual_desc_count < _MIN_DESCRIPTIONS:
            gaps.append(
                MixGap(
                    missing_type="min_descriptions",
                    required_count=_MIN_DESCRIPTIONS,
                    actual_count=actual_desc_count,
                )
            )

        # 4. Primary keyword in descriptions
        primary_keyword = (ctx.top_keywords[0].lower() if ctx.top_keywords else "")
        if primary_keyword:
            keyword_desc_count = sum(
                1 for d in descriptions if primary_keyword in d.lower()
            )
            if keyword_desc_count < _MIN_KEYWORD_DESC:
                gaps.append(
                    MixGap(
                        missing_type="keyword_in_descriptions",
                        required_count=_MIN_KEYWORD_DESC,
                        actual_count=keyword_desc_count,
                    )
                )

        return gaps


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _is_alpha_phrase(term: str) -> bool:
    """Return True if term contains only letters and spaces (safe for \\b boundary)."""
    return bool(re.match(r"^[a-zA-Z ]+$", term))
