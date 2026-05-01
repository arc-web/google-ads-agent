#!/usr/bin/env python3
"""Analyze search term variation and generate phrase keyword expansion candidates."""

from __future__ import annotations

import csv
import io
import re
from collections import Counter, defaultdict
from pathlib import Path


CLIENT_DIR = Path("/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy")
BUILD_DIR = CLIENT_DIR / "build" / "search_rebuild_test"
REPORTS_DIR = CLIENT_DIR / "reports" / "performance_inputs"

SOURCE = Path("/Users/home/Downloads/Search terms report (3).csv")
COPIED_SOURCE = REPORTS_DIR / "search_terms_report_min_10_impressions_2026-04-28.csv"
ANALYSIS_CSV = BUILD_DIR / "search_term_variation_analysis_2026-04-28.csv"
KEYWORD_EXPANSION_CSV = BUILD_DIR / "phrase_keyword_expansion_candidates_2026-04-28.csv"
SUMMARY_MD = BUILD_DIR / "keyword_variation_review_2026-04-28.md"


SERVICE_PATTERNS = [
    ("Testing - ADHD", ["adhd test", "adhd testing", "adhd assessment", "adhd evaluation"]),
    ("Testing - Autism", ["autism test", "autism testing", "autism evaluation", "autism assessment"]),
    ("Testing - Child Psychological", ["psychological testing", "psychological evaluation", "child psychologist", "child psychology"]),
    ("Testing - Psychoeducational", ["psychoeducational", "iep", "learning disability"]),
    ("Testing - Gifted", ["gifted"]),
    ("Testing - Kindergarten Readiness", ["kindergarten readiness"]),
    ("Therapy - Anxiety", ["anxiety", "panic"]),
    ("Therapy - ADHD", ["adhd therap", "adhd treatment", "add treatment", "adhd counseling", "adhd marriage"]),
    ("Therapy - Autism", ["autism therapy", "autism therapist"]),
    ("Therapy - Depression", ["depression", "esketamine"]),
    ("Therapy - Grief And Loss", ["grief", "loss counseling"]),
    ("Therapy - Trauma", ["trauma"]),
    ("Therapy - Postpartum Support", ["postpartum"]),
    ("Therapy - Children", ["child behavioral therapist", "child therapist", "children therapist", "kids therapist"]),
    ("Psychiatry - Children", ["child psychiat", "children psychiat", "adolescent psychiat", "children's psychiatric"]),
    ("Psychiatry - Adult", ["psychiatry", "psychiatrist", "psychiatric", "pmhnp", "psych np"]),
    ("Parent Child Services - Children", ["parent child", "parent-child"]),
]

NEGATIVE_PATTERNS = [
    "coach",
    "zviadi",
    "uva",
    "belgrade",
    "blackbird",
    "champs",
    "ari yares",
    "aislynn",
    "epic",
    "towson",
    "danville",
    "fredericksburg",
]

CITY_TERMS = ["ashburn", "falls church", "leesburg", "sterling", "dulles", "reston", "vienna", "herndon", "mclean", "arlington", "manassas"]
STATE_TERMS = ["virginia", " va", "maryland", " md", "dc", "district of columbia"]


def parse_number(value: str) -> float:
    value = (value or "").replace(",", "").replace("%", "").strip()
    if value in {"", "--"}:
        return 0.0
    return float(value)


def read_google_report(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    header = next(index for index, line in enumerate(lines) if line.startswith("Search term,"))
    return list(csv.DictReader(io.StringIO("\n".join(lines[header:]))))


def normalize(term: str) -> str:
    term = term.lower().strip()
    term = re.sub(r"\s+", " ", term)
    return term


def classify_layer(term: str) -> str:
    t = f" {term} "
    if " near me" in t or " nearby" in t:
        return "Local"
    if any(city in t for city in CITY_TERMS):
        return "City"
    if any(state in t for state in STATE_TERMS):
        return "State"
    return "General"


def classify_service(term: str) -> str:
    for service, patterns in SERVICE_PATTERNS:
        if any(pattern in term for pattern in patterns):
            return service
    return "Human Review"


def recommended_action(term: str, clicks: float, impressions: float, conversions: float, cost: float) -> str:
    if any(pattern in term for pattern in NEGATIVE_PATTERNS):
        return "review_negative"
    if conversions > 0:
        return "add_phrase"
    if impressions >= 50 and clicks == 0:
        return "review_low_ctr"
    if clicks >= 10 and conversions == 0:
        return "review_spend_no_conversion"
    if impressions >= 10:
        return "variation_candidate"
    return "observe"


def singular_plural_variants(term: str) -> list[str]:
    variants = {term}
    replacements = [
        (r"\btherapist\b", "therapists"),
        (r"\btherapists\b", "therapist"),
        (r"\bpsychiatrist\b", "psychiatrists"),
        (r"\bpsychiatrists\b", "psychiatrist"),
        (r"\bevaluation\b", "evaluations"),
        (r"\bevaluations\b", "evaluation"),
        (r"\bassessment\b", "assessments"),
        (r"\bassessments\b", "assessment"),
        (r"\bservice\b", "services"),
        (r"\bservices\b", "service"),
        (r"\btest\b", "tests"),
        (r"\btests\b", "test"),
    ]
    for pattern, replacement in replacements:
        updated = re.sub(pattern, replacement, term)
        if updated != term:
            variants.add(updated)
    return sorted(variants)


def ad_group_for(service: str, layer: str) -> str:
    if service == "Human Review":
        return "Human Review"
    return f"{service} - {layer}"


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    COPIED_SOURCE.write_bytes(SOURCE.read_bytes())

    rows = read_google_report(SOURCE)
    analysis_rows = []
    expansion = {}

    for row in rows:
        term = normalize(row["Search term"])
        if term.startswith("total:"):
            continue
        clicks = parse_number(row["Clicks"])
        impressions = parse_number(row["Impr."])
        conversions = parse_number(row["Conversions"])
        cost = parse_number(row["Cost"])
        ctr = row["CTR"]
        cpa = parse_number(row["Cost / conv."])
        service = classify_service(term)
        layer = classify_layer(term)
        action = recommended_action(term, clicks, impressions, conversions, cost)
        ad_group = ad_group_for(service, layer)
        analysis_rows.append({
            "search_term": term,
            "service": service,
            "intent_layer": layer,
            "recommended_ad_group": ad_group,
            "recommended_action": action,
            "clicks": clicks,
            "impressions": impressions,
            "ctr": ctr,
            "cost": cost,
            "conversions": conversions,
            "cost_per_conversion": cpa,
            "legacy_ad_group": row["Ad group"],
            "legacy_keyword": row["Keyword"],
        })
        if action == "add_phrase" and service != "Human Review":
            for variant in singular_plural_variants(term):
                key = (ad_group, variant)
                if key not in expansion:
                    expansion[key] = {
                        "ad_group": ad_group,
                        "keyword": variant,
                        "criterion_type": "Phrase",
                        "source_search_term": term,
                        "source_action": action,
                        "source_impressions": impressions,
                        "source_clicks": clicks,
                        "source_conversions": conversions,
                        "notes": "converting search-term variation",
                    }

    analysis_rows.sort(key=lambda r: (r["recommended_action"], -float(r["conversions"]), -float(r["impressions"])))
    expansion_rows = sorted(expansion.values(), key=lambda r: (r["ad_group"], r["keyword"]))

    with ANALYSIS_CSV.open("w", encoding="utf-8", newline="") as handle:
        headers = list(analysis_rows[0].keys())
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(analysis_rows)

    with KEYWORD_EXPANSION_CSV.open("w", encoding="utf-8", newline="") as handle:
        headers = list(expansion_rows[0].keys())
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(expansion_rows)

    action_counts = Counter(row["recommended_action"] for row in analysis_rows)
    service_counts = Counter(row["service"] for row in analysis_rows)
    top_high_impression = sorted(analysis_rows, key=lambda r: -float(r["impressions"]))[:25]
    top_converting = sorted(analysis_rows, key=lambda r: -float(r["conversions"]))[:25]

    lines = [
        "# Keyword Variation Review",
        "",
        "Date: 2026-04-28",
        "",
        f"Source: `{COPIED_SOURCE}`",
        f"Analysis CSV: `{ANALYSIS_CSV}`",
        f"Expansion CSV: `{KEYWORD_EXPANSION_CSV}`",
        "",
        "## Summary",
        "",
        f"- Search terms analyzed: `{len(analysis_rows)}`",
        f"- Phrase keyword expansion candidates: `{len(expansion_rows)}`",
        "",
        "## Action Counts",
        "",
    ]
    for action, count in action_counts.most_common():
        lines.append(f"- `{action}`: `{count}`")
    lines.extend(["", "## Service Counts", ""])
    for service, count in service_counts.most_common():
        lines.append(f"- `{service}`: `{count}`")
    lines.extend(["", "## Top Converting Terms", ""])
    for row in top_converting[:15]:
        lines.append(f"- `{row['search_term']}` -> `{row['recommended_ad_group']}`, {row['conversions']} conversions, {row['impressions']} impressions, action `{row['recommended_action']}`")
    lines.extend(["", "## Top High-Impression Terms", ""])
    for row in top_high_impression[:15]:
        lines.append(f"- `{row['search_term']}` -> `{row['recommended_ad_group']}`, {row['impressions']} impressions, {row['clicks']} clicks, {row['conversions']} conversions, action `{row['recommended_action']}`")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- Templates are necessary for coverage, but search-term variation should decide which terms graduate into extra phrase keywords.",
        "- High-impression, no-click terms should not automatically become keywords. They should either inform RSA wording, become negatives, or stay in review.",
        "- Singular and plural variants should be generated only when the root term is directly relevant to the service and landing page.",
        "- Provider names, institutions, competitors, coaching terms, and out-of-market cities should be review or negative candidates.",
        "",
    ])
    SUMMARY_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"analysis={ANALYSIS_CSV}")
    print(f"expansion={KEYWORD_EXPANSION_CSV}")
    print(f"summary={SUMMARY_MD}")


if __name__ == "__main__":
    main()
