#!/usr/bin/env python3
"""Organize THHL search term and location reports into campaign build inputs."""

from __future__ import annotations

import csv
import io
from collections import defaultdict
from pathlib import Path


CLIENT_DIR = Path("/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy")
BUILD_DIR = CLIENT_DIR / "build" / "search_rebuild_test"
REPORTS_DIR = CLIENT_DIR / "reports" / "performance_inputs"

SEARCH_TERMS_SOURCE = Path("/Users/home/Downloads/Search terms report (2).csv")
LOCATION_SOURCE = Path("/Users/home/Downloads/Location report.csv")

SEARCH_TERMS_COPY = REPORTS_DIR / "search_terms_report_2026-04-28.csv"
LOCATION_COPY = REPORTS_DIR / "location_report_2026-04-28.csv"
ORGANIZED_SEARCH_TERMS = BUILD_DIR / "organized_search_terms_2026-04-28.csv"
ORGANIZED_LOCATIONS = BUILD_DIR / "organized_locations_2026-04-28.csv"
BUILD_PLAN = BUILD_DIR / "first_campaign_and_next_build_plan.md"


def parse_number(value: str) -> float:
    value = (value or "").replace(",", "").replace("%", "").replace("$", "").strip()
    if value in {"", "--"}:
        return 0.0
    return float(value)


def read_google_csv(path: Path, header_prefix: str) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    header_index = next(index for index, line in enumerate(lines) if line.startswith(header_prefix))
    reader = csv.DictReader(io.StringIO("\n".join(lines[header_index:])))
    return list(reader)


def write_csv(path: Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def classify_term(term: str) -> tuple[str, str]:
    t = term.lower()
    if t.startswith("total:"):
        return "total", "exclude_from_keyword_build"
    if any(token in t for token in ["7032897560", "think happy live healthy"]):
        return "brand_or_phone", "separate_brand_or_call_only"
    if any(token in t for token in ["uva", "blackbird", "champs", "ari yares", "aislynn collier", "belgrade"]):
        return "competitor_or_person", "human_review_negative_or_competitor"
    if "epic" in t or "danville" in t or "towson" in t or "fredericksburg" in t:
        return "out_of_market_or_ambiguous", "human_review_negative"
    if "coach" in t:
        return "coaching_intent", "negative_or_separate_low_priority"
    if "behavioral therapist" in t:
        return "child_behavioral_therapy", "build_keyword"
    if "add treatment" in t:
        return "adhd_treatment", "build_keyword"
    if ("child" in t or "children" in t or "kids" in t) and "adhd" in t and ("assessment" in t or "testing" in t):
        return "child_adhd_testing", "build_keyword"
    if "adhd" in t:
        return "adhd_treatment", "build_keyword"
    if "anxiety" in t:
        return "anxiety_treatment", "build_keyword"
    if "child" in t and ("psychiatry" in t or "psychiatrist" in t or "psychologist" in t or "psychology" in t):
        return "child_psychiatry_psychology", "build_keyword"
    if "pmhnp" in t or "psych np" in t or "psychiatric nurse" in t:
        return "psychiatric_np", "build_keyword"
    if "psychiatr" in t or "psych evaluation" in t:
        return "psychiatry_eval", "build_keyword"
    if "esketamine" in t:
        return "depression_esketamine", "separate_later"
    return "general_mental_health", "human_review"


def keyword_variants(term: str) -> tuple[str, str]:
    cleaned = term.lower().strip()
    return f'"{cleaned}"', f"[{cleaned}]"


def organize_search_terms(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    organized = []
    for row in rows:
        term = row["Search term"]
        if term.startswith("Total:"):
            continue
        theme, action = classify_term(term)
        phrase, exact = keyword_variants(term)
        conversions = parse_number(row["Conversions"])
        cost = parse_number(row["Cost"])
        clicks = parse_number(row["Clicks"])
        cost_per_conv = parse_number(row["Cost / conv."])
        priority_score = conversions * 100 - cost_per_conv + clicks * 0.25
        organized.append({
            "theme": theme,
            "recommended_action": action,
            "search_term": term,
            "phrase_keyword": phrase if action in {"build_keyword", "separate_later"} else "",
            "exact_keyword": exact if action in {"build_keyword", "separate_later"} else "",
            "legacy_campaign": row["Campaign"],
            "legacy_ad_group": row["Ad group"],
            "triggering_keyword": row["Keyword"],
            "clicks": clicks,
            "impressions": parse_number(row["Impr."]),
            "ctr": row["CTR"],
            "cost": cost,
            "conversions": conversions,
            "cost_per_conversion": cost_per_conv,
            "priority_score": round(priority_score, 2),
            "notes": "",
        })
    return sorted(organized, key=lambda r: (r["recommended_action"] != "build_keyword", -float(r["conversions"]), float(r["cost_per_conversion"])))


def organize_locations(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    organized = []
    for row in rows:
        location = row["Location"]
        if location.startswith("Total:"):
            continue
        conversions = parse_number(row["Conversions"])
        cost_per_conv = parse_number(row["Cost / conv."])
        cost = parse_number(row["Cost"])
        if conversions >= 10 and cost_per_conv <= 300:
            tier = "tier_1_core"
            bid_modifier = "20"
        elif conversions >= 3 and cost_per_conv <= 400:
            tier = "tier_2_expansion"
            bid_modifier = "10"
        elif conversions == 0 and cost >= 150:
            tier = "tier_4_reduce_or_exclude"
            bid_modifier = "-25"
        else:
            tier = "tier_3_observe"
            bid_modifier = ""
        organized.append({
            "tier": tier,
            "location": location,
            "campaign": row["Campaign"],
            "impressions": parse_number(row["Impr."]),
            "interactions": parse_number(row["Interactions"]),
            "interaction_rate": row["Interaction rate"],
            "cost": cost,
            "conversions": conversions,
            "cost_per_conversion": cost_per_conv,
            "recommended_bid_modifier": bid_modifier,
        })
    return sorted(organized, key=lambda r: (r["tier"], -float(r["conversions"])))


def summarize_by_theme(rows: list[dict[str, object]]) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = defaultdict(lambda: {"terms": 0, "clicks": 0, "cost": 0, "conversions": 0})
    for row in rows:
        if row["recommended_action"] != "build_keyword":
            continue
        data = summary[str(row["theme"])]
        data["terms"] += 1
        data["clicks"] += float(row["clicks"])
        data["cost"] += float(row["cost"])
        data["conversions"] += float(row["conversions"])
    for data in summary.values():
        data["cost_per_conversion"] = data["cost"] / data["conversions"] if data["conversions"] else 0
    return dict(sorted(summary.items(), key=lambda item: -item[1]["conversions"]))


def write_build_plan(search_terms: list[dict[str, object]], locations: list[dict[str, object]]) -> None:
    themes = summarize_by_theme(search_terms)
    build_keywords = [row for row in search_terms if row["recommended_action"] == "build_keyword"]
    review_terms = [row for row in search_terms if row["recommended_action"] != "build_keyword"]
    tier_1 = [row for row in locations if row["tier"] == "tier_1_core"]
    tier_2 = [row for row in locations if row["tier"] == "tier_2_expansion"]
    reduce = [row for row in locations if row["tier"] == "tier_4_reduce_or_exclude"]

    def term_lines(theme: str) -> list[str]:
        rows = [row for row in build_keywords if row["theme"] == theme]
        lines = []
        for row in rows[:8]:
            lines.append(f"- `{row['phrase_keyword']}` and `{row['exact_keyword']}` from `{row['search_term']}`, {row['conversions']} conversions, CPA ${row['cost_per_conversion']}")
        return lines or ["- No source term in this report."]

    lines = [
        "# THHL First Search Campaign Buildout And Next Campaign Plan",
        "",
        "Date: 2026-04-28",
        "",
        "## Source Reports",
        "",
        f"- Search terms source: `{SEARCH_TERMS_COPY}`",
        f"- Location source: `{LOCATION_COPY}`",
        f"- Organized search terms: `{ORGANIZED_SEARCH_TERMS}`",
        f"- Organized locations: `{ORGANIZED_LOCATIONS}`",
        "",
        "## What The Reports Say",
        "",
        "- The search terms report is small but useful: after removing totals, it contains 39 usable search term rows.",
        "- Child and family terms are being caught by old child psychiatry keywords, but several terms are better mapped to more specific ad groups.",
        "- `child behavioral therapist` and `child behavioral therapist near me` should become their own clinical ad group, not stay buried under `Children's Psychiatry`.",
        "- ADHD terms split into two intents: child testing or assessment, and therapy or treatment.",
        "- `adhd coach` and `adhd coach near me` spent heavily with weak CPA, so they should not be added to the first keyword build.",
        "- The location report is too coarse for final ZIP-level buildout, but it gives enough to set first-pass campaign targeting and bid modifiers.",
        "",
        "## Theme Summary From Converting Terms",
        "",
    ]
    for theme, data in themes.items():
        lines.append(f"- `{theme}`: {data['terms']} terms, {data['clicks']:.0f} clicks, {data['conversions']:.2f} conversions, CPA ${data['cost_per_conversion']:.2f}")

    lines.extend([
        "",
        "## First Campaign",
        "",
        "Campaign name: `ARC - Search - Psychiatry + Child Behavioral - V1`",
        "",
        "Purpose: rebuild the old Psychiatry campaign into a tighter Search campaign that uses phrase match only. No broad match.",
        "",
        "Campaign settings:",
        "",
        "- Campaign type: Search",
        "- Networks: Google Search only",
        "- Search partners: off for initial test unless the client explicitly wants volume",
        "- Match type: phrase only",
        "- Location option: presence only",
        "- Budget: start from current campaign budget, then split only after ad group and geo signal is stable",
        "",
        "## Ad Groups And Seed Keywords",
        "",
        "### Child Behavioral Therapist",
        "",
        "Reason: this is the clearest structural correction from the search terms. It is clinical enough to build around and more specific than `child therapist`.",
        "",
    ])
    lines.extend(term_lines("child_behavioral_therapy"))
    lines.extend([
        "",
        "RSA angle: behavioral concerns, child therapy, parent support, evaluation-informed care, Northern Virginia access.",
        "",
        "### Child Psychiatry And Psychology",
        "",
    ])
    lines.extend(term_lines("child_psychiatry_psychology"))
    lines.extend([
        "",
        "RSA angle: child and adolescent psychiatric care, licensed clinicians, medication management when appropriate, telehealth and in-person options.",
        "",
        "### Child ADHD Testing",
        "",
    ])
    lines.extend(term_lines("child_adhd_testing"))
    lines.extend([
        "",
        "RSA angle: ADHD assessments for children, school support, clear next steps, Northern Virginia evaluation team.",
        "",
        "### ADHD Therapy And Treatment",
        "",
    ])
    lines.extend(term_lines("adhd_treatment"))
    lines.extend([
        "",
        "RSA angle: ADHD therapy and treatment, adult and child support, avoid `coach` language in the first build.",
        "",
        "### Anxiety Treatment",
        "",
    ])
    lines.extend(term_lines("anxiety_treatment"))
    lines.extend([
        "",
        "RSA angle: anxiety doctors, anxiety treatment, practical support, appointments in VA, DC, and MD.",
        "",
        "### Psychiatric Nurse Practitioner",
        "",
    ])
    lines.extend(term_lines("psychiatric_np"))
    lines.extend([
        "",
        "RSA angle: psychiatric nurse practitioners, medication management, psychiatry near me, accepted insurance where true.",
        "",
        "### Adult Psychiatry Evaluation",
        "",
    ])
    lines.extend(term_lines("psychiatry_eval"))
    lines.extend([
        "",
        "RSA angle: adult psych evaluations, psychiatry services, assessment and treatment planning.",
        "",
        "## First Campaign Geo Targeting",
        "",
        "Use the current report for first-pass geo targeting, but request a ZIP or city-level user location report before deeper segmentation.",
        "",
        "Tier 1, bid up:",
        "",
    ])
    for row in tier_1:
        lines.append(f"- `{row['location']}`: {row['conversions']} conversions, CPA ${row['cost_per_conversion']}, modifier `{row['recommended_bid_modifier']}`")
    lines.extend(["", "Tier 2, moderate bid up:", ""])
    for row in tier_2:
        lines.append(f"- `{row['location']}`: {row['conversions']} conversions, CPA ${row['cost_per_conversion']}, modifier `{row['recommended_bid_modifier']}`")
    lines.extend(["", "Reduce or review:", ""])
    for row in reduce:
        lines.append(f"- `{row['location']}`: {row['conversions']} conversions, CPA ${row['cost_per_conversion']}, modifier `{row['recommended_bid_modifier']}`")

    lines.extend([
        "",
        "Specific geo recommendation:",
        "",
        "- Keep Loudoun County and Fairfax County as core targets.",
        "- Keep Prince William County and Washington DC as expansion targets.",
        "- Avoid broad Maryland in the first clean rebuild because this report shows high cost and weak CPA.",
        "- Do not overreact to `Total: Other locations` yet, because it is an aggregate bucket. Pull a finer user-location report so the winning cities or ZIPs can be targeted directly.",
        "",
        "## Terms To Exclude Or Review",
        "",
        "- Add `coach` as a negative concept for this first campaign unless the client sells coaching.",
        "- Review competitor, provider-name, and institution terms before adding or excluding them.",
        "- Review out-of-market city terms like Danville, Towson, and Fredericksburg before deciding if they should be excluded.",
        "- Keep brand and phone searches out of this nonbrand campaign. Build a separate brand campaign if needed.",
        "",
        "High-priority review terms:",
        "",
    ])
    for row in review_terms[:16]:
        lines.append(f"- `{row['search_term']}`: action `{row['recommended_action']}`, {row['conversions']} conversions, CPA ${row['cost_per_conversion']}")

    lines.extend([
        "",
        "## Responsive Search Ad Direction",
        "",
        "The RSA builder should use old high-CTR converting themes, but improve relevance by ad group:",
        "",
        "- Put `Child Behavioral Therapist` language only in the child behavioral ad group.",
        "- Put `ADHD assessment` and `ADHD testing` language in the child ADHD testing ad group.",
        "- Keep `ADHD therapist` and `ADHD treatment` in a separate treatment ad group.",
        "- Keep `Psychiatric Nurse Practitioner`, `PMHNP`, and `Psych NP` together.",
        "- Keep anxiety ad copy direct, but avoid implying the user has a personal medical condition.",
        "",
        "Every RSA must pass headline and description character limits, landing page match, clinical specificity, and sensitive-category policy review before CSV assembly.",
        "",
        "## Next Campaigns",
        "",
        "Campaign 2: `ARC - Search - Child Testing - V1`",
        "",
        "- Build around child psychological testing, psychoeducational evaluations, autism testing, gifted testing, and kindergarten readiness.",
        "- Use only phrase keywords.",
        "- Use landing pages specific to each testing service.",
        "",
        "Campaign 3: `ARC - Search - Adult Therapy + Psychiatry - V1`",
        "",
        "- Build around adult therapy, adult psych evaluations, anxiety treatment, depression treatment, and medication management.",
        "- Separate therapy from medication management when enough volume exists.",
        "",
        "Campaign 4: `ARC - Search - Brand - V1`",
        "",
        "- Capture `think happy live healthy`, phone number searches, provider name searches if approved, and office-location brand variants.",
        "- Keep budget controlled and do not let brand conversion CPA distort nonbrand planning.",
        "",
        "Campaign 5: geo split campaigns after we get better location detail",
        "",
        "- `ARC - Search - Loudoun/Ashburn - V1`",
        "- `ARC - Search - Fairfax/Falls Church - V1`",
        "- `ARC - Search - DC/Arlington - V1` only if CPA improves or strategic need is confirmed.",
        "- Maryland should be split only after city or ZIP winners are identified.",
        "",
        "## Data Needed Before Deeper Segmentation",
        "",
        "- User location report by city and ZIP code.",
        "- Search term report segmented by campaign, ad group, conversion action, and network.",
        "- RSA asset report with impressions, CTR, conversion rate, and conversions by headline and description.",
        "- Landing page performance by final URL.",
        "- Client priority services and capacity constraints.",
        "",
        "## Google Ads Limit Note",
        "",
        "Google's account limit docs list 10,500 location targets per campaign and up to 500 proximity targets per campaign. That is not the blocker here yet. The practical blocker is clean reporting and campaign control, so we should split campaigns by service line and high-value geography before we hit hard platform limits.",
        "",
        "Source: https://support.google.com/google-ads/answer/6372658?hl=en",
        "",
        "## Build Sequence",
        "",
        "1. Add the first campaign structure above to the rebuild harness.",
        "2. Generate phrase keyword rows only.",
        "3. Generate one RSA per ad group, then a second variant only after review.",
        "4. Add Tier 1 and Tier 2 locations with bid modifiers.",
        "5. Add negatives for coaching, brand leakage, and clear out-of-market terms after human review.",
        "6. Import into Google Ads Editor as staging.",
        "7. Fix Editor validation issues, then repeat for Campaign 2.",
        "",
    ])
    BUILD_PLAN.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    SEARCH_TERMS_COPY.write_bytes(SEARCH_TERMS_SOURCE.read_bytes())
    LOCATION_COPY.write_bytes(LOCATION_SOURCE.read_bytes())

    search_rows = read_google_csv(SEARCH_TERMS_SOURCE, "Search term,")
    location_rows = read_google_csv(LOCATION_SOURCE, "Location,")

    organized_search = organize_search_terms(search_rows)
    organized_locations = organize_locations(location_rows)

    write_csv(ORGANIZED_SEARCH_TERMS, [
        "theme", "recommended_action", "search_term", "phrase_keyword", "exact_keyword",
        "legacy_campaign", "legacy_ad_group", "triggering_keyword", "clicks", "impressions",
        "ctr", "cost", "conversions", "cost_per_conversion", "priority_score", "notes",
    ], organized_search)
    write_csv(ORGANIZED_LOCATIONS, [
        "tier", "location", "campaign", "impressions", "interactions", "interaction_rate",
        "cost", "conversions", "cost_per_conversion", "recommended_bid_modifier",
    ], organized_locations)
    write_build_plan(organized_search, organized_locations)

    print(f"organized_search_terms={ORGANIZED_SEARCH_TERMS}")
    print(f"organized_locations={ORGANIZED_LOCATIONS}")
    print(f"build_plan={BUILD_PLAN}")


if __name__ == "__main__":
    main()
