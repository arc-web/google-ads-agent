"""
7-sweep copy grader for the google_ads_agent copy engine.

Runs all seven copy-editing sweeps in a single LLM call per asset and
returns a structured GradeReport. Sweep definitions follow the
copy_editing_sweeps.md framework (clarity, voice_tone, so_what,
prove_it, specificity, emotion, zero_risk).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from copy_engine.models import OpenRouterClient

GRADER_MODEL = "google/gemini-2.5-flash"  # structured output; kimi-k2 corrupts JSON

# ---------------------------------------------------------------------------
# Grading constants
# ---------------------------------------------------------------------------

SWEEP_NAMES = [
    "clarity",
    "voice_tone",
    "so_what",
    "prove_it",
    "specificity",
    "emotion",
    "zero_risk",
]

GRADE_THRESHOLDS = [
    (90, "A"),
    (75, "B"),
    (60, "C"),
    (40, "D"),
]  # below 40 -> F

SYSTEM_PROMPT = """\
You are a senior Google Ads copy analyst. You evaluate ad assets against
platform-native standards - NOT against long-form copywriting ideals.

Google Ads RSA headlines are ≤30 characters. A single headline has ONE job.
It cannot contain proof, a CTA, trust signals, AND a benefit bridge in 30 chars.
Never penalise a headline for lacking something that physically cannot fit.

=== HEADLINE EVALUATION (≤30 chars) ===

Each headline in an RSA serves a specific role. Identify the role first, then
score on whether it executes that role well. Roles:
  keyword_match — mirrors the search query ("Anxiety Therapy Ashburn")
  geo           — signals location ("Ashburn & Falls Church VA")
  credential    — signals trust/authority ("Licensed Therapists", "Board-Certified")
  benefit       — states outcome ("Feel Better. Start Healing.")
  question      — surfaces pain ("Struggling With Anxiety?")
  cta           — drives action ("Book Free Consult Today")
  proof         — number or stat ("15+ Years Helping Families")

Score each headline on these 7 dimensions, but interpret each for the role it serves:

1. clarity     — Does meaning land in under 2 seconds? Is the service or signal
                 instantly understood? Score 85+ if clear, penalise only true ambiguity.

2. voice_tone  — Human, not robotic. Avoid bland label-speak when a better angle
                 fits the same chars. "Compassionate Counseling" > "Counseling Services".
                 Score 70 (neutral) for pure keyword/geo headlines - tone not applicable.

3. so_what     — For benefit/question/CTA headlines: is there a clear implied or
                 stated outcome? For keyword/geo/credential headlines: score 70 (neutral)
                 - these headlines are not designed to carry a benefit bridge.

4. prove_it    — For proof/credential headlines: is the qualifier concrete and credible?
                 For all other roles: score 70 (neutral). Do NOT penalise keyword_match
                 or geo headlines for lacking evidence. That is not their job.

5. specificity — Is it specific vs. generic? "Anxiety & Depression Therapy" > "Therapy".
                 "Ashburn & Falls Church VA" > "Northern Virginia". Reward precision.

6. emotion     — For benefit/question headlines: does it connect to pain, relief, hope,
                 or desire? For geo/credential/keyword headlines: score 70 (neutral).
                 A geo headline ("Ashburn VA") should never fail emotion - it is not
                 attempting emotion. Score neutral, not fail.

7. zero_risk   — Score 70 (neutral) for all headlines. CTAs and trust blocks live in
                 descriptions. Do NOT score headlines down for missing a CTA.

HEADLINE overall_score weighting: clarity (25%) + specificity (25%) +
role-relevant dimensions (50%). A geo headline that clearly states a geo = 80+.
A credential headline that states a credential clearly = 80+.

=== DESCRIPTION EVALUATION (≤90 chars) ===

Descriptions have room for a full message. Hold them to a higher standard.
Each description should pack: benefit or problem acknowledgement + proof or
differentiator + CTA or next step signal - all within 90 chars.

1. clarity     — Does the sentence read cleanly in one pass? No run-ons or awkward cuts.

2. voice_tone  — Human and direct. No "we are proud to offer". Start with the reader's
                 problem or outcome, not the business.

3. so_what     — Is a concrete reader benefit stated? Features alone don't count.
                 "Licensed therapists" → who cares? "Licensed therapists who get results" → yes.

4. prove_it    — Is there a credibility signal? Number, credential, timeframe, named
                 result, or social proof. Flag descriptions with zero proof elements.

5. specificity — Specific language beats generic. "Same-week appointments" > "fast".
                 "Anthem, BCBS, Aetna accepted" > "most insurance accepted".

6. emotion     — Does it acknowledge a feeling the reader has? Relief, hope, frustration,
                 desire for their child's success. Purely functional descriptions score low.

7. zero_risk   — Is there a CTA or action signal? Is the next step clear? Are objections
                 (cost, commitment, availability) pre-empted? This matters for descriptions.

DESCRIPTION overall_score: all 7 dimensions weighted equally.

=== SCORING SCALE ===
90-100  Excellent - publish as-is
75-89   Good - minor polish only
60-74   Acceptable - could be stronger
40-59   Weak - needs rewrite
0-39    Poor - start over

Neutral dimensions (score 70) do NOT drag overall score down. They are excluded
from the weighted average calculation when they are not applicable to the role.

=== OUTPUT FORMAT ===
Return valid JSON only. No markdown, no code fences. Schema:
{
  "sweeps": [
    {
      "name": "<sweep_name>",
      "score": <0-100 integer>,
      "issues": ["<specific issue, if any>"],
      "suggestions": ["<concrete rewrite or addition>"]
    }
  ],
  "overall_score": <0-100 integer>
}

Keep issues and suggestions empty arrays [] when a dimension is neutral/not applicable.
No text outside the JSON object.
"""

RESPONSE_SCHEMA = {
    "sweeps": [
        {
            "name": "string",
            "score": "integer 0-100",
            "issues": ["string"],
            "suggestions": ["string"],
        }
    ],
    "overall_score": "integer 0-100",
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class SweepResult:
    sweep_name: str
    score: int          # 0-100
    issues: list[str]
    suggestions: list[str]


@dataclass
class GradeReport:
    asset_type: str     # "headline" | "description" | "sitelink" | "callout"
    asset_text: str
    sweeps: list[SweepResult]
    overall_score: int
    overall_grade: str  # A / B / C / D / F
    top_issues: list[str]  # top 3 across all sweeps


# ---------------------------------------------------------------------------
# Grader
# ---------------------------------------------------------------------------


class CopyGrader:
    """Run the 7-sweep copy evaluation framework against Google Ads assets."""

    def __init__(self, client: OpenRouterClient) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def grade_asset(
        self,
        asset_text: str,
        asset_type: str,
        context: str = "",
    ) -> GradeReport:
        """
        Grade a single ad asset through all 7 sweeps in one LLM call.

        Args:
            asset_text: The headline, description, sitelink, or callout text.
            asset_type: One of "headline", "description", "sitelink", "callout".
            context:    Optional campaign/product context to help the grader
                        understand intent (e.g. "plumber in Austin, TX targeting
                        emergency leak repair searchers").

        Returns:
            GradeReport with per-sweep scores, issues, and suggestions.
        """
        user_prompt = self._build_user_prompt(asset_text, asset_type, context)
        raw = self._client.complete_json(
            system=SYSTEM_PROMPT,
            user=user_prompt,
            schema=RESPONSE_SCHEMA,
            max_tokens=1200,
            model=GRADER_MODEL,
        )
        return self._parse_response(raw, asset_text, asset_type)

    def grade_ad_group(
        self,
        headlines: list[str],
        descriptions: list[str],
        context: str = "",
    ) -> dict:
        """
        Grade all assets for one ad group.

        Args:
            headlines:    List of headline strings (typically up to 15 for RSAs).
            descriptions: List of description strings (typically up to 4 for RSAs).
            context:      Optional campaign/product context.

        Returns:
            {
                "headlines":    [GradeReport, ...],
                "descriptions": [GradeReport, ...],
                "summary": {
                    "avg_score": int,
                    "avg_grade": str,
                    "weakest_sweep": str,
                    "top_issues": [str, ...],
                }
            }
        """
        headline_reports = [
            self.grade_asset(h, "headline", context) for h in headlines
        ]
        description_reports = [
            self.grade_asset(d, "description", context) for d in descriptions
        ]

        all_reports = headline_reports + description_reports
        summary = self._build_group_summary(all_reports)

        return {
            "headlines": headline_reports,
            "descriptions": description_reports,
            "summary": summary,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _score_to_grade(self, score: int) -> str:
        """Map a 0-100 numeric score to a letter grade."""
        for threshold, grade in GRADE_THRESHOLDS:
            if score >= threshold:
                return grade
        return "F"

    def _build_user_prompt(
        self, asset_text: str, asset_type: str, context: str
    ) -> str:
        parts = [
            f"Asset type: {asset_type}",
            f'Asset text: "{asset_text}"',
        ]
        if context:
            parts.append(f"Campaign context: {context}")
        parts.append(
            "Evaluate this asset through all 7 sweeps and return the JSON report."
        )
        return "\n".join(parts)

    def _parse_response(
        self, raw: dict | list, asset_text: str, asset_type: str
    ) -> GradeReport:
        """Convert the raw LLM JSON into a GradeReport."""
        # Model sometimes wraps single result in an array
        if isinstance(raw, list):
            raw = raw[0] if raw else {}
        if not isinstance(raw, dict):
            raw = {}

        sweep_results: list[SweepResult] = []

        raw_sweeps = raw.get("sweeps", [])
        seen_names = {s["name"]: s for s in raw_sweeps if "name" in s}

        for name in SWEEP_NAMES:
            entry = seen_names.get(name, {})
            sweep_results.append(
                SweepResult(
                    sweep_name=name,
                    score=int(entry.get("score", 0)),
                    issues=entry.get("issues", []),
                    suggestions=entry.get("suggestions", []),
                )
            )

        overall_score = int(raw.get("overall_score", 0))
        overall_grade = self._score_to_grade(overall_score)
        top_issues = self._extract_top_issues(sweep_results)

        return GradeReport(
            asset_type=asset_type,
            asset_text=asset_text,
            sweeps=sweep_results,
            overall_score=overall_score,
            overall_grade=overall_grade,
            top_issues=top_issues,
        )

    def _extract_top_issues(self, sweeps: list[SweepResult]) -> list[str]:
        """
        Collect issues from lowest-scoring sweeps first and return up to 3.
        This surfaces the most impactful problems regardless of sweep order.
        """
        sorted_sweeps = sorted(sweeps, key=lambda s: s.score)
        issues: list[str] = []
        for sweep in sorted_sweeps:
            for issue in sweep.issues:
                prefixed = f"[{sweep.sweep_name}] {issue}"
                issues.append(prefixed)
                if len(issues) == 3:
                    return issues
        return issues

    def _build_group_summary(self, reports: list[GradeReport]) -> dict:
        """Summarise scores across all assets in an ad group."""
        if not reports:
            return {
                "avg_score": 0,
                "avg_grade": "F",
                "weakest_sweep": "",
                "top_issues": [],
            }

        avg_score = round(sum(r.overall_score for r in reports) / len(reports))

        # Aggregate sweep scores across all assets to find the weakest sweep
        sweep_totals: dict[str, list[int]] = {name: [] for name in SWEEP_NAMES}
        all_issues: list[tuple[int, str]] = []  # (score, prefixed_issue)

        for report in reports:
            for sweep in report.sweeps:
                sweep_totals[sweep.sweep_name].append(sweep.score)
                for issue in sweep.issues:
                    all_issues.append(
                        (sweep.score, f"[{sweep.sweep_name}] {issue}")
                    )

        sweep_avgs = {
            name: (sum(scores) / len(scores) if scores else 100)
            for name, scores in sweep_totals.items()
        }
        weakest_sweep = min(sweep_avgs, key=lambda n: sweep_avgs[n])

        # Top 3 issues from lowest-scoring context
        top_issues = [
            issue for _, issue in sorted(all_issues, key=lambda x: x[0])[:3]
        ]

        return {
            "avg_score": avg_score,
            "avg_grade": self._score_to_grade(avg_score),
            "weakest_sweep": weakest_sweep,
            "top_issues": top_issues,
        }
