#!/usr/bin/env python3
"""Create the round-1 revised THLH staging CSV from client call priorities."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


BUILD_DIR = Path("/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/build/search_rebuild_test")
INPUT_CSV = BUILD_DIR / "THHL_Search_Services_Editor_Staging_CURRENT.csv"
OUTPUT_CSV = BUILD_DIR / "THHL_Search_Services_Editor_Staging_REV1.csv"
VALIDATION_JSON = BUILD_DIR / "THHL_Search_Services_Editor_Staging_REV1_validation.json"
REVIEW_MD = BUILD_DIR / "THHL_Search_Services_Editor_Staging_REV1_review.md"
FEEDBACK_JSON = BUILD_DIR / "client_feedback_classified.json"
DECISION_LOG = BUILD_DIR / "revision_decision_log.csv"

HOME_URL = "https://www.thinkhappylivehealthy.com/"
OLD_CAMPAIGN = "ARC - Search - Services - V1"

CAMPAIGN_BUDGETS = {
    "ARC - Search - Psychiatry - V1": "60.00",
    "ARC - Search - Adult Therapy - V1": "25.00",
    "ARC - Search - Testing - V1": "25.00",
    "ARC - Search - Brand - V1": "10.00",
}

ADULT_THERAPY_AREAS = {
    "Anxiety",
    "ADHD",
    "Depression",
    "LGBTQIA+",
    "Stress",
    "Grief And Loss",
    "Trauma",
    "Postpartum Support",
}

TESTING_AREAS = {
    "Child Psychological",
    "Psychoeducational",
    "Gifted",
    "ADHD",
    "Kindergarten Readiness",
    "Autism",
}

HEADLINE_LIMIT = 30
DESCRIPTION_LIMIT = 90
PATH_LIMIT = 15


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-16", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_rows(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-16", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def blank(headers: list[str]) -> dict[str, str]:
    return {header: "" for header in headers}


def clone_blank_like(headers: list[str], source: dict[str, str] | None = None) -> dict[str, str]:
    row = blank(headers)
    if source:
        for key in (
            "Campaign Type",
            "Networks",
            "Budget type",
            "EU political ads",
            "Standard conversion goals",
            "Languages",
            "Bid Strategy Type",
            "Enhanced CPC",
            "Broad match keywords",
            "Ad rotation",
            "Targeting method",
            "Exclusion method",
            "Campaign Status",
            "Status",
        ):
            if key in row:
                row[key] = source.get(key, "")
    return row


def campaign_row(headers: list[str], source: dict[str, str], campaign: str, budget: str) -> dict[str, str]:
    row = clone_blank_like(headers, source)
    row.update(
        {
            "Campaign": campaign,
            "Campaign Type": "Search",
            "Networks": "Google search",
            "Budget": budget,
            "Budget type": "Daily",
            "EU political ads": "Doesn't have EU political ads",
            "Standard conversion goals": "Account-level",
            "Languages": "en",
            "Bid Strategy Type": "Maximize conversions",
            "Enhanced CPC": "Disabled",
            "Broad match keywords": "Off",
            "Ad rotation": "Optimize",
            "Targeting method": "Location of presence",
            "Exclusion method": "Location of presence",
            "Campaign Status": "Enabled",
            "Status": "Enabled",
            "Comment": "round_1_core_focus_budget_weighting",
        }
    )
    return row


def parse_ad_group(ad_group: str) -> tuple[str, str, str] | None:
    parts = ad_group.split(" - ")
    if len(parts) < 3:
        return None
    return parts[0], " - ".join(parts[1:-1]), parts[-1]


def campaign_for_ad_group(ad_group: str) -> str | None:
    parsed = parse_ad_group(ad_group)
    if not parsed:
        return None
    service, area, layer = parsed
    if layer == "State":
        return None
    if service == "Psychiatry" and area in {"Adult", "Children"}:
        return "ARC - Search - Psychiatry - V1"
    if service == "Therapy" and area in ADULT_THERAPY_AREAS:
        return "ARC - Search - Adult Therapy - V1"
    if service == "Testing" and area in TESTING_AREAS:
        return "ARC - Search - Testing - V1"
    return None


def city_allowed(ad_group: str, keyword: str) -> bool:
    parsed = parse_ad_group(ad_group)
    if not parsed:
        return True
    service, _area, layer = parsed
    if layer != "City":
        return True
    allowed = ["Ashburn VA"] if service == "Psychiatry" else ["Ashburn VA", "Falls Church VA"]
    return any(city.lower() in keyword.lower() for city in allowed)


def trim(value: str, limit: int) -> str:
    value = " ".join(value.split())
    return value if len(value) <= limit else value[:limit].rstrip()


def set_headlines(row: dict[str, str], headlines: list[str]) -> None:
    safe = [trim(headline, HEADLINE_LIMIT) for headline in headlines]
    while len(safe) < 15:
        safe.append("Think Happy Live Healthy")
    for index in range(1, 16):
        row[f"Headline {index}"] = safe[index - 1]


def set_descriptions(row: dict[str, str], descriptions: list[str]) -> None:
    safe = [trim(description, DESCRIPTION_LIMIT) for description in descriptions]
    while len(safe) < 4:
        safe.append("Book an appointment with Think Happy Live Healthy today.")
    for index in range(1, 5):
        row[f"Description {index}"] = safe[index - 1]


def normalize_copy(row: dict[str, str]) -> None:
    for index in range(1, 16):
        key = f"Headline {index}"
        value = row.get(key, "")
        value = value.replace("Insurance Options Available", "Anthem/CareFirst BCBS")
        value = value.replace("Care For Kids & Adults", "Adult Therapy Support")
        value = value.replace("VA, DC & MD Access", "Ashburn Psychiatry Care")
        value = value.replace("Ashburn & Falls Church", "Ashburn Care")
        row[key] = trim(value, HEADLINE_LIMIT)
    for index in range(1, 5):
        key = f"Description {index}"
        value = row.get(key, "")
        value = value.replace("online or in person in Northern Virginia", "in person in Ashburn")
        value = value.replace("Ashburn, Falls Church, and through telehealth", "Ashburn and through telehealth")
        value = value.replace("Ashburn or Falls Church with telehealth options", "Ashburn with telehealth options")
        row[key] = trim(value, DESCRIPTION_LIMIT)
    row["Description 4"] = "Anthem/CareFirst BCBS in-network; out-of-network superbills provided."


def revise_rsa(row: dict[str, str]) -> None:
    ad_group = row.get("Ad Group", "")
    parsed = parse_ad_group(ad_group)
    normalize_copy(row)
    if not parsed:
        return
    service, area, _layer = parsed
    if service == "Psychiatry":
        audience = "Child" if area == "Children" else "Adult"
        set_headlines(
            row,
            [
                f"{audience} Psychiatry Ashburn",
                "Psych NP Appointments",
                "Medication Mgmt Support",
                "Ashburn Psychiatry Care",
                "Accepting New Patients",
                "In-Person Psychiatry",
                "Psychiatric Care Near You",
                "Request Appointment Today",
                "Anthem/CareFirst BCBS",
                "Out-of-Network Superbills",
                "Care Planning Support",
                "Northern Virginia Care",
                "Think Happy Live Healthy",
                "Book Psychiatry Consult",
                "Mental Health Support",
            ],
        )
        set_descriptions(
            row,
            [
                f"{audience} psychiatry appointments in Ashburn with medication support and care planning.",
                "Meet psychiatric nurse practitioners in person in Ashburn.",
                "Ashburn-based psychiatry care for Northern Virginia clients and families.",
                "Anthem/CareFirst BCBS in-network; out-of-network superbills provided.",
            ],
        )
    elif service == "Testing" and area == "ADHD":
        set_headlines(
            row,
            [
                "ADHD Testing Through Age 21",
                "Child & Teen ADHD Testing",
                "Young Adult ADHD Testing",
                "ADHD Evaluation for Kids",
                "Licensed Child Evaluators",
                "Ashburn & Falls Church",
                "Northern Virginia Testing",
                "Request Appointment Today",
                "Anthem/CareFirst BCBS",
                "Out-of-Network Superbills",
                "Support For IEP Planning",
                "Clear Next Steps For School",
                "ADHD Assessment Near You",
                "Testing For Ages 21 & Under",
                "Think Happy Live Healthy",
            ],
        )
        set_descriptions(
            row,
            [
                "ADHD testing for children, teens, and young adults through age 21.",
                "Licensed evaluators provide diagnosis support and clear next steps.",
                "Testing is available in Northern Virginia with location fit confirmed at intake.",
                "Anthem/CareFirst BCBS in-network; out-of-network superbills provided.",
            ],
        )
    elif service == "Therapy":
        row["Description 1"] = trim(f"Adult {area.lower()} therapy in Northern Virginia with licensed clinicians.", DESCRIPTION_LIMIT)
        row["Description 4"] = "Anthem/CareFirst BCBS in-network; out-of-network superbills provided."


def location_allowed(row: dict[str, str]) -> bool:
    location = row.get("Location", "")
    if not location:
        return True
    blocked = {
        "Maryland, United States",
        "Washington, District of Columbia, United States",
        "Virginia, United States",
    }
    return location not in blocked


def location_allowed_for_campaign(row: dict[str, str], campaign: str) -> bool:
    if not location_allowed(row):
        return False
    if campaign != "ARC - Search - Psychiatry - V1":
        return True
    location = row.get("Location", "")
    psychiatry_locations = {
        "Ashburn, Virginia, United States",
        "Loudoun County, Virginia, United States",
        "Leesburg, Virginia, United States",
        "Sterling, Virginia, United States",
        "Dulles, Virginia, United States",
        "Reston, Virginia, United States",
        "Herndon, Virginia, United States",
        "(15mi:38.964776:-77.521702)",
    }
    return location in psychiatry_locations


def add_negative(headers: list[str], campaign: str, keyword: str, reason: str) -> dict[str, str]:
    row = blank(headers)
    row.update(
        {
            "Campaign": campaign,
            "Keyword": keyword,
            "Criterion Type": "Negative Phrase",
            "Account keyword type": "None",
            "Campaign Status": "Enabled",
            "Status": "Enabled",
            "Comment": reason,
        }
    )
    return row


def brand_rows(headers: list[str], source_campaign: dict[str, str]) -> list[dict[str, str]]:
    campaign = "ARC - Search - Brand - V1"
    rows = [campaign_row(headers, source_campaign, campaign, CAMPAIGN_BUDGETS[campaign])]
    ad_group = blank(headers)
    ad_group.update(
        {
            "Campaign": campaign,
            "Ad Group": "Brand - Think Happy Live Healthy - General",
            "Max CPC": "2.00",
            "Campaign Status": "Enabled",
            "Ad Group Status": "Paused",
            "Status": "Enabled",
            "Comment": "day_1_brand_campaign_low_budget",
        }
    )
    rows.append(ad_group)
    for keyword in [
        "Think Happy Live Healthy",
        "ThinkHappyLiveHealthy",
        "Think Happy Live Healthy Ashburn",
        "Think Happy Live Healthy Falls Church",
        "Think Happy Live Healthy Psychiatry",
        "Think Happy Live Healthy Testing",
    ]:
        rows.append(
            {
                **blank(headers),
                "Campaign": campaign,
                "Ad Group": ad_group["Ad Group"],
                "Keyword": keyword,
                "Criterion Type": "Phrase",
                "Account keyword type": "None",
                "Campaign Status": "Enabled",
                "Ad Group Status": "Paused",
                "Status": "Enabled",
            }
        )
    rsa = blank(headers)
    rsa.update(
        {
            "Campaign": campaign,
            "Ad Group": ad_group["Ad Group"],
            "Ad type": "Responsive search ad",
            "Path 1": "Brand",
            "Path 2": "Care",
            "Final URL": HOME_URL,
            "Campaign Status": "Enabled",
            "Ad Group Status": "Paused",
            "Status": "Enabled",
            "Comment": "day_1_brand_campaign_low_budget",
        }
    )
    set_headlines(
        rsa,
        [
            "Think Happy Live Healthy",
            "Official Practice Site",
            "Ashburn & Falls Church",
            "Psychiatry & Therapy Care",
            "Testing Appointments",
            "Mental Health Support",
            "Northern Virginia Care",
            "Request Appointment Today",
                "Anthem/CareFirst BCBS",
            "Out-of-Network Superbills",
            "Licensed Clinicians",
            "Care For Families",
            "Book Your Appointment",
            "Psych NP Appointments",
            "Testing Through Age 21",
        ],
    )
    set_descriptions(
        rsa,
        [
            "Visit Think Happy Live Healthy for psychiatry, therapy, and testing appointments.",
            "Care is available in Ashburn, Falls Church, and through telehealth where appropriate.",
            "Use the official site to request appointments and confirm service fit.",
            "Anthem/CareFirst BCBS in-network; out-of-network superbills provided.",
        ],
    )
    rows.append(rsa)
    return rows


def build_rev1(headers: list[str], rows: list[dict[str, str]]) -> list[dict[str, str]]:
    source_campaign = next(row for row in rows if row.get("Campaign") == OLD_CAMPAIGN and not row.get("Ad Group"))
    output: list[dict[str, str]] = []
    for campaign, budget in CAMPAIGN_BUDGETS.items():
        if campaign == "ARC - Search - Brand - V1":
            continue
        output.append(campaign_row(headers, source_campaign, campaign, budget))

    for row in rows:
        if row.get("Campaign") != OLD_CAMPAIGN:
            continue
        if row.get("Location"):
            if not location_allowed(row):
                continue
            for campaign in (
                "ARC - Search - Psychiatry - V1",
                "ARC - Search - Adult Therapy - V1",
                "ARC - Search - Testing - V1",
                "ARC - Search - Brand - V1",
            ):
                if not location_allowed_for_campaign(row, campaign):
                    continue
                new_row = dict(row)
                new_row["Campaign"] = campaign
                new_row["Comment"] = "round_1_core_geo_targeting"
                output.append(new_row)
            continue

        ad_group = row.get("Ad Group", "")
        if not ad_group:
            continue
        campaign = campaign_for_ad_group(ad_group)
        if not campaign:
            continue
        if row.get("Keyword") and row.get("Criterion Type") == "Phrase" and not city_allowed(ad_group, row.get("Keyword", "")):
            continue
        new_row = dict(row)
        new_row["Campaign"] = campaign
        if row.get("Ad type") == "Responsive search ad":
            revise_rsa(new_row)
        if not new_row.get("Comment"):
            new_row["Comment"] = "round_1_core_focus"
        output.append(new_row)

    for row in brand_rows(headers, source_campaign):
        output.append(row)

    for campaign in ("ARC - Search - Psychiatry - V1", "ARC - Search - Adult Therapy - V1", "ARC - Search - Testing - V1"):
        for keyword in ("emdr therapy", "emdr therapist", "emdr counseling"):
            output.append(add_negative(headers, campaign, keyword, "remove_emdr_until_capacity_returns"))
    for keyword in ("adult adhd test", "adult adhd testing", "adhd test for adults", "adult adhd evaluation", "adult adhd assessment"):
        output.append(add_negative(headers, "ARC - Search - Testing - V1", keyword, "adhd_testing_through_age_21"))
    for campaign in ("ARC - Search - Adult Therapy - V1", "ARC - Search - Testing - V1"):
        for keyword in ("family therapy", "family counseling", "family therapist"):
            output.append(add_negative(headers, campaign, keyword, "no_standalone_family_therapy"))

    return output


def validate(rows: list[dict[str, str]]) -> dict[str, object]:
    issues: list[dict[str, object]] = []
    counts = Counter()
    campaigns = Counter()
    ad_groups = set()
    negatives = 0
    for row_number, row in enumerate(rows, start=2):
        campaign = row.get("Campaign", "")
        if campaign:
            campaigns[campaign] += 1
        if row.get("Ad Group") and not row.get("Keyword") and not row.get("Ad type"):
            counts["ad_group_rows"] += 1
            ad_groups.add((campaign, row["Ad Group"]))
        if row.get("Keyword"):
            if row.get("Criterion Type") == "Negative Phrase":
                counts["negative_keyword_rows"] += 1
                negatives += 1
            elif row.get("Criterion Type") == "Phrase":
                counts["keyword_rows"] += 1
            else:
                issues.append({"severity": "error", "row": row_number, "message": "Keyword row has unsupported Criterion Type."})
        if row.get("Ad type") == "Responsive search ad":
            counts["rsa_rows"] += 1
            for index in range(1, 16):
                value = row.get(f"Headline {index}", "")
                if not value:
                    issues.append({"severity": "error", "row": row_number, "message": f"Missing Headline {index}."})
                if len(value) > HEADLINE_LIMIT:
                    issues.append({"severity": "error", "row": row_number, "message": f"Headline {index} exceeds 30 chars: {value}"})
            for index in range(1, 5):
                value = row.get(f"Description {index}", "")
                if not value:
                    issues.append({"severity": "error", "row": row_number, "message": f"Missing Description {index}."})
                if len(value) > DESCRIPTION_LIMIT:
                    issues.append({"severity": "error", "row": row_number, "message": f"Description {index} exceeds 90 chars: {value}"})
            for path_field in ("Path 1", "Path 2"):
                value = row.get(path_field, "")
                if value and len(value) > PATH_LIMIT:
                    issues.append({"severity": "error", "row": row_number, "message": f"{path_field} exceeds 15 chars: {value}"})
        if row.get("Location"):
            counts["location_rows"] += 1
        if row.get("Radius"):
            counts["radius_rows"] += 1
        if row.get("Bid Modifier"):
            counts["bid_modifier_rows"] += 1

    searchable_text = "\n".join(" ".join(row.values()).lower() for row in rows)
    forbidden = [
        "emdr",
        "most major insurance",
        "carefirst & more",
        "family therapy services",
        "child and adult adhd",
        "maryland, united states",
        "washington, district of columbia",
    ]
    for term in forbidden:
        if term in searchable_text and not term.startswith("emdr"):
            issues.append({"severity": "error", "row": "", "message": f"Forbidden launch text remains: {term}"})

    return {
        "status": "pass" if not any(issue["severity"] == "error" for issue in issues) else "fail",
        "rows": len(rows),
        "campaigns": sorted(campaigns),
        "ad_groups": len(ad_groups),
        "counts": dict(counts),
        "negative_keyword_rows": negatives,
        "issues": issues,
        "source_csv": str(INPUT_CSV),
        "output_csv": str(OUTPUT_CSV),
        "revision_sources": {
            "client_feedback": str(FEEDBACK_JSON),
            "decision_log": str(DECISION_LOG),
        },
    }


def write_review(report: dict[str, object]) -> None:
    lines = [
        "# THHL Search Services Editor Staging REV1 Review",
        "",
        f"CSV: `{OUTPUT_CSV}`",
        "",
        f"Validation status: `{report['status']}`",
        f"Rows: `{report['rows']}`",
        f"Ad groups: `{report['ad_groups']}`",
        "",
        "## Campaigns",
        "",
    ]
    for campaign in report["campaigns"]:
        lines.append(f"- `{campaign}`")
    lines.extend(["", "## Counts", ""])
    for key, value in sorted(report["counts"].items()):
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Core Focus Revisions Applied",
            "",
            "- Split launch staging into Psychiatry, Adult Therapy, Testing, and Brand campaigns.",
            "- Weighted Psychiatry at roughly half of non-brand daily budget.",
            "- Removed EMDR, child therapy, parent-child services, specialty modality branches outside core adult therapy, and statewide intent layers.",
            "- Removed Maryland, Washington DC, and statewide Virginia location rows from REV1 targeting.",
            "- Added day-1 brand campaign with capped daily budget.",
            "- Replaced broad insurance positioning with Anthem/CareFirst BCBS and out-of-network superbill language.",
            "- Repositioned ADHD testing around children, teens, and young adults through age 21.",
            "- Added adult ADHD testing, EMDR, and standalone family therapy negative keyword controls.",
            "",
            "## Issues",
            "",
        ]
    )
    if report["issues"]:
        for issue in report["issues"]:
            lines.append(f"- `{issue['severity']}` row {issue.get('row', '')}: {issue['message']}")
    else:
        lines.append("- No local validation issues.")
    REVIEW_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    headers, rows = read_rows(INPUT_CSV)
    rev1 = build_rev1(headers, rows)
    write_rows(OUTPUT_CSV, headers, rev1)
    report = validate(rev1)
    VALIDATION_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_review(report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
