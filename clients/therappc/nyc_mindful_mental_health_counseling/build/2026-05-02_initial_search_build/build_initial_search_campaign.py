#!/usr/bin/env python3
"""Build initial Search staging output for Mindful Mental Health Counseling."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.gads.core.search_campaigns.search_csv_generator import SearchCSVGenerator
from shared.rebuild.staging_validator import validate_file


CLIENT_DIR = ROOT / "clients" / "therappc" / "nyc_mindful_mental_health_counseling"
BUILD_DIR = CLIENT_DIR / "build" / "2026-05-02_initial_search_build"
OUTPUT_CSV = BUILD_DIR / "Google_Ads_Editor_Staging_CURRENT.csv"
VALIDATION_JSON = BUILD_DIR / "validation_report.json"
SOURCE_ATTRIBUTION_JSON = BUILD_DIR / "source_attribution.json"
WEBSITE_SCAN_JSON = BUILD_DIR / "website_scan.json"
SERVICE_CATALOG_JSON = BUILD_DIR / "service_catalog.json"
LANDING_PAGE_MAP_JSON = BUILD_DIR / "landing_page_map.json"
GEO_STRATEGY_JSON = BUILD_DIR / "geo_strategy.json"
CAMPAIGN_TAXONOMY_CSV = BUILD_DIR / "campaign_taxonomy.csv"
RSA_COPY_MATRIX_CSV = BUILD_DIR / "rsa_copy_matrix.csv"
HUMAN_REVIEW_MD = BUILD_DIR / "human_review.md"

CAMPAIGN = "ARC - Search - Anxiety Therapy - V1"
WEBSITE = "https://nycmindfulmentalhealthcounseling.com/"


AD_GROUPS = [
    {
        "name": "Anxiety Therapy - Core",
        "final_url": "https://nycmindfulmentalhealthcounseling.com/",
        "path_1": "Anxiety",
        "path_2": "Therapy",
        "keywords": [
            "anxiety therapy",
            "anxiety therapist",
            "anxiety counseling",
            "anxiety treatment",
            "online anxiety therapy",
            "anxiety therapist nyc",
            "anxiety therapy new jersey",
        ],
        "headlines": [
            "NYC Anxiety Therapy Online",
            "NJ Anxiety Therapy Online",
            "Anxiety Therapy For Adults",
            "Mindful Anxiety Counseling",
            "CBT And Mindfulness Support",
            "Therapy For Young Adults NY",
            "Practical Anxiety Skills NY",
            "Online Therapy In NY And NJ",
            "Support For Overthinking Care",
            "Book A Free Consult Today",
            "Out Of Network Superbills",
            "Licensed NY And NJ Therapy",
            "Anxiety Care With CBT Skills",
            "Mindful Mental Health Care",
            "Private Online Therapy Care",
        ],
        "descriptions": [
            "Online anxiety therapy for young adults in New York and New Jersey.",
            "Build practical skills with CBT, DBT, ACT, and mindfulness-informed care.",
            "Start with a consultation call and confirm whether the practice is a fit.",
            "Out-of-network superbills are available for eligible reimbursement.",
        ],
    },
    {
        "name": "Individual Therapy - Young Adults",
        "final_url": "https://nycmindfulmentalhealthcounseling.com/individual-therapy-nyc/",
        "path_1": "Individual",
        "path_2": "Therapy",
        "keywords": [
            "individual therapy nyc",
            "online individual therapy",
            "therapy for young adults",
            "young adult therapist",
            "young adult therapy nyc",
            "online therapy new york",
            "online therapy new jersey",
        ],
        "headlines": [
            "Individual Therapy Online",
            "Therapy For Young Adults NY",
            "NYC Young Adult Therapy Care",
            "Online Therapy In NY And NJ",
            "Mindful Therapy Support NY",
            "CBT Skills For Daily Life",
            "Support For Life Transitions",
            "Private Online Therapy Care",
            "Book A Free Consult Today",
            "Licensed NY And NJ Therapy",
            "Therapy For Overthinking Care",
            "Build Practical Coping Skills",
            "Mindful Mental Health Care",
            "Out Of Network Superbills",
            "Goal Oriented Therapy Care",
        ],
        "descriptions": [
            "Online individual therapy for young adults navigating anxiety and related concerns.",
            "Sessions focus on practical skills, mindfulness, and collaborative support.",
            "Care is available to clients living in New York or New Jersey.",
            "Out-of-network superbills are available for eligible reimbursement.",
        ],
    },
    {
        "name": "Group Therapy - NYC",
        "final_url": "https://nycmindfulmentalhealthcounseling.com/group-therapy-nyc/",
        "path_1": "Group",
        "path_2": "Therapy",
        "keywords": [
            "group therapy nyc",
            "online group therapy",
            "anxiety group therapy",
            "social anxiety group therapy",
            "cbt group therapy",
            "depression group therapy",
            "young adult group therapy",
        ],
        "headlines": [
            "Online Group Therapy NYC Care",
            "Skills Based Group Therapy",
            "Social Anxiety Group Care",
            "CBT Group Skills Support NY",
            "Group Therapy For Adults NYC",
            "Connect With Supportive Peers",
            "Guided Online Therapy Groups",
            "Therapy Groups For Anxiety",
            "Mindfulness Group Support",
            "Book A Free Consult Today",
            "Licensed NY And NJ Therapy",
            "Support For Depression Skills",
            "Private Online Group Care",
            "Out Of Network Superbills",
            "Mindful Mental Health Care",
        ],
        "descriptions": [
            "Online group therapy options for adults seeking skills and support.",
            "Groups may focus on social anxiety, depression skills, or mindfulness.",
            "Start with an intro call to review fit, timing, rates, and next steps.",
            "Out-of-network superbills are available for eligible reimbursement.",
        ],
    },
    {
        "name": "CBT Therapy - Skills",
        "final_url": "https://nycmindfulmentalhealthcounseling.com/cbt/",
        "path_1": "CBT",
        "path_2": "Therapy",
        "keywords": [
            "cbt therapy",
            "cognitive behavioral therapy",
            "cbt therapist",
            "cbt therapy nyc",
            "online cbt therapy",
            "cbt for anxiety",
            "cbt skills therapy",
        ],
        "headlines": [
            "Online CBT Therapy Support",
            "CBT Skills For Anxiety Care",
            "Cognitive Behavioral Therapy",
            "CBT Therapy Care In NY NJ",
            "Practical CBT Tools Online",
            "Therapy For Thought Patterns",
            "Mindfulness Informed CBT Care",
            "CBT Support For Young Adults",
            "Book A Free Consult Today",
            "Licensed NY And NJ Therapy",
            "Goal Oriented Therapy Care",
            "Build Practical Coping Skills",
            "Mindful Mental Health Care",
            "Out Of Network Superbills",
            "Online Therapy For Anxiety",
        ],
        "descriptions": [
            "CBT-informed online therapy for anxiety and related concerns in NY and NJ.",
            "Work on thought patterns, coping skills, mindfulness, and daily tools.",
            "Care is collaborative, practical, and matched to individual goals.",
            "Out-of-network superbills are available for eligible reimbursement.",
        ],
    },
    {
        "name": "DBT Therapy - Skills",
        "final_url": "https://nycmindfulmentalhealthcounseling.com/dbt/",
        "path_1": "DBT",
        "path_2": "Skills",
        "keywords": [
            "dbt therapy",
            "dbt skills therapy",
            "dbt therapist",
            "online dbt therapy",
            "dbt therapy nyc",
            "dbt for anxiety",
            "emotional regulation therapy",
        ],
        "headlines": [
            "Online DBT Skills Therapy",
            "DBT Skills For Daily Stress",
            "Emotional Regulation Support",
            "DBT Therapy Care In NY NJ",
            "Therapy For Life Transitions",
            "Practical Coping Skills Care",
            "Mindfulness Informed DBT Care",
            "DBT Support For Young Adults",
            "Book A Free Consult Today",
            "Licensed NY And NJ Therapy",
            "Private Online Therapy Care",
            "Build Practical Coping Skills",
            "Mindful Mental Health Care",
            "Out Of Network Superbills",
            "Support For Intense Emotions",
        ],
        "descriptions": [
            "DBT-informed online therapy for anxiety, emotions, and life transitions.",
            "Learn skills for emotional regulation, distress tolerance, and mindfulness.",
            "Care is available to clients living in New York or New Jersey.",
            "Out-of-network superbills are available for eligible reimbursement.",
        ],
    },
    {
        "name": "OCD Therapy - Support",
        "final_url": "https://nycmindfulmentalhealthcounseling.com/",
        "path_1": "OCD",
        "path_2": "Therapy",
        "keywords": [
            "ocd therapy",
            "ocd therapist",
            "ocd counseling",
            "online ocd therapy",
            "ocd therapy nyc",
            "ocd therapy new jersey",
            "obsessive compulsive therapy",
        ],
        "headlines": [
            "Online OCD Therapy Support",
            "OCD Therapy Care In NY NJ",
            "Support For OCD Patterns NY",
            "Therapy For Intrusive Thoughts",
            "CBT Skills For OCD Support",
            "Mindfulness For OCD Support",
            "Private Online Therapy Care",
            "Therapy For Young Adults NY",
            "Book A Free Consult Today",
            "Licensed NY And NJ Therapy",
            "Practical Coping Skills Care",
            "Mindful Mental Health Care",
            "Out Of Network Superbills",
            "Goal Oriented Therapy Care",
            "Online Therapy For Anxiety",
        ],
        "descriptions": [
            "Online therapy support for OCD-related concerns in New York and New Jersey.",
            "Use evidence-informed tools for intrusive thoughts and compulsive patterns.",
            "Start with a consultation call to confirm clinical fit and next steps.",
            "Out-of-network superbills are available for eligible reimbursement.",
        ],
    },
    {
        "name": "Depression Therapy - Support",
        "final_url": "https://nycmindfulmentalhealthcounseling.com/",
        "path_1": "Depression",
        "path_2": "Therapy",
        "keywords": [
            "depression therapy",
            "depression therapist",
            "depression counseling",
            "online depression therapy",
            "depression therapy nyc",
            "depression therapy new jersey",
            "therapy for depression",
        ],
        "headlines": [
            "Online Depression Therapy",
            "Depression Therapy Support",
            "Therapy For Low Mood Support",
            "Depression Care In NY And NJ",
            "CBT Skills For Depression",
            "Mindfulness Therapy Support",
            "Private Online Therapy Care",
            "Therapy For Young Adults NY",
            "Book A Free Consult Today",
            "Licensed NY And NJ Therapy",
            "Build Practical Coping Skills",
            "Goal Oriented Therapy Care",
            "Mindful Mental Health Care",
            "Out Of Network Superbills",
            "Support For Life Transitions",
        ],
        "descriptions": [
            "Online depression therapy support for young adults in New York and New Jersey.",
            "Sessions can focus on low mood, motivation, transitions, and daily skills.",
            "Care is collaborative and grounded in CBT, DBT, ACT, and mindfulness.",
            "Out-of-network superbills are available for eligible reimbursement.",
        ],
    },
    {
        "name": "Social Anxiety - Support",
        "final_url": "https://nycmindfulmentalhealthcounseling.com/",
        "path_1": "Social",
        "path_2": "Anxiety",
        "keywords": [
            "social anxiety therapy",
            "social anxiety therapist",
            "social anxiety counseling",
            "online social anxiety therapy",
            "social anxiety therapy nyc",
            "social anxiety group therapy",
            "cbt for social anxiety",
        ],
        "headlines": [
            "Social Anxiety Therapy Care",
            "Online Social Anxiety Support",
            "CBT Skills For Social Anxiety",
            "Social Anxiety In NY And NJ",
            "Group Therapy For Anxiety",
            "Therapy For Overthinking Care",
            "Private Online Therapy Care",
            "Therapy For Young Adults NY",
            "Book A Free Consult Today",
            "Licensed NY And NJ Therapy",
            "Mindfulness Therapy Support",
            "Build Practical Coping Skills",
            "Mindful Mental Health Care",
            "Out Of Network Superbills",
            "Goal Oriented Therapy Care",
        ],
        "descriptions": [
            "Online therapy and group support options for social anxiety concerns.",
            "Build practical skills for worry, avoidance, overthinking, and stress.",
            "Care is available to clients living in New York or New Jersey.",
            "Out-of-network superbills are available for eligible reimbursement.",
        ],
    },
]

NEGATIVE_KEYWORDS = [
    "free therapy",
    "inpatient",
    "psychiatrist",
    "medication management",
    "crisis hotline",
    "emergency therapy",
    "jobs",
    "career",
    "training",
    "certification",
]

SOURCE_ATTRIBUTION = {
    "client": "Mindful Mental Health Counseling",
    "website": WEBSITE,
    "source_pages": [
        {
            "url": "https://nycmindfulmentalhealthcounseling.com/",
            "used_for": [
                "anxiety focus",
                "online therapy for adolescents and young adults in New York and New Jersey",
                "services and modalities",
                "founder and licensing language",
            ],
        },
        {
            "url": "https://nycmindfulmentalhealthcounseling.com/contact/",
            "used_for": [
                "request appointment call to action",
                "out-of-network insurance and superbill language",
                "phone number",
            ],
        },
        {
            "url": "https://nycmindfulmentalhealthcounseling.com/group-therapy-nyc/",
            "used_for": [
                "group therapy process",
                "online sessions only",
                "group session pricing",
                "NY and NJ license/service eligibility",
            ],
        },
        {
            "url": "https://nycmindfulmentalhealthcounseling.com/cbt/",
            "used_for": ["CBT positioning and online therapy service area"],
        },
        {
            "url": "https://nycmindfulmentalhealthcounseling.com/dbt/",
            "used_for": ["DBT positioning and skills-based copy"],
        },
    ],
    "not_available": [
        "Google Ads account export",
        "search terms report",
        "location performance report",
        "conversion action report",
        "client-approved budgets",
        "client-approved priority service order",
    ],
}


def validate_copy() -> None:
    for ad_group in AD_GROUPS:
        for headline in ad_group["headlines"]:
            if not 25 <= len(headline) <= 30:
                raise ValueError(f"Headline must be 25-30 chars: {headline} ({len(headline)})")
        for description in ad_group["descriptions"]:
            if len(description) > 90:
                raise ValueError(f"Description exceeds 90 chars: {description} ({len(description)})")
        for path_key in ("path_1", "path_2"):
            if len(ad_group[path_key]) > 15:
                raise ValueError(f"{path_key} exceeds 15 chars: {ad_group[path_key]}")


def build_staging() -> dict[str, object]:
    validate_copy()
    generator = SearchCSVGenerator()
    generator.add_campaign(
        CAMPAIGN,
        "100.00",
        status="Paused",
        networks="Google search",
        eu_political_ads="No",
        broad_match_keywords="Off",
    )
    for location, location_id in [
        ("New York, United States", "21167"),
        ("New Jersey, United States", "21164"),
    ]:
        generator.add_location(CAMPAIGN, location, location_id=location_id)

    for ad_group in AD_GROUPS:
        generator.add_ad_group(CAMPAIGN, ad_group["name"], status="Paused")
        for keyword in ad_group["keywords"]:
            generator.add_keyword(
                CAMPAIGN,
                ad_group["name"],
                keyword,
                final_url=ad_group["final_url"],
                criterion_type="Phrase",
                status="Paused",
            )
        generator.add_rsa(
            CAMPAIGN,
            ad_group["name"],
            ad_group["final_url"],
            headlines=ad_group["headlines"],
            descriptions=ad_group["descriptions"],
            path_1=ad_group["path_1"],
            path_2=ad_group["path_2"],
            status="Paused",
        )

    for keyword in NEGATIVE_KEYWORDS:
        generator.add_negative_phrase(CAMPAIGN, keyword, status="Paused")

    report = generator.write_and_validate(OUTPUT_CSV)
    VALIDATION_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def write_json_artifacts() -> None:
    website_scan = {
        "client": "Mindful Mental Health Counseling",
        "website": WEBSITE,
        "extracted_facts": {
            "primary_positioning": "online therapy for anxiety and related concerns",
            "service_area": ["New York", "New Jersey"],
            "audience": ["adolescents", "young adults in their 20s and 30s", "adults for group therapy"],
            "services": [
                "individual therapy",
                "group therapy",
                "anxiety therapy",
                "depression therapy",
                "OCD therapy",
                "social anxiety support",
            ],
            "modalities": ["CBT", "DBT", "ACT", "mindfulness"],
            "billing": "out-of-network with superbills available for eligible reimbursement",
            "consultation": "introductory consultation call available",
        },
        "human_review_needed": [
            "confirm current capacity by service",
            "confirm whether adolescent-focused search should be active",
            "confirm whether New York and New Jersey should share one campaign or split by state",
            "confirm client-approved budget",
            "confirm whether group therapy is currently enrolling or waitlist only",
        ],
    }
    service_catalog = {
        "active_services_for_staging": [
            "Anxiety Therapy",
            "Individual Therapy",
            "Group Therapy",
            "CBT Therapy",
            "DBT Therapy",
            "OCD Therapy",
            "Depression Therapy",
            "Social Anxiety Therapy",
        ],
        "excluded_from_initial_staging": [
            {
                "service": "Adolescent therapy",
                "reason": "Website confirms adolescents, but age and guardian intake rules need client review before ad group activation.",
            },
            {
                "service": "ACT therapy",
                "reason": "Used as support language in copy, but not activated as a separate ad group in the first compact build.",
            },
            {
                "service": "Mindfulness-based therapy",
                "reason": "Used as brand differentiation, but not activated as a separate ad group in the first compact build.",
            },
        ],
    }
    landing_page_map = {
        ad_group["name"]: {
            "final_url": ad_group["final_url"],
            "path_1": ad_group["path_1"],
            "path_2": ad_group["path_2"],
        }
        for ad_group in AD_GROUPS
    }
    geo_strategy = {
        "targeting": [
            {"location": "New York, United States", "location_id": "21167"},
            {"location": "New Jersey, United States", "location_id": "21164"},
        ],
        "targeting_method": "Location of presence",
        "review_note": "Website says clients must live in New York or New Jersey. Confirm whether to split campaigns by state before launch.",
    }
    SOURCE_ATTRIBUTION_JSON.write_text(json.dumps(SOURCE_ATTRIBUTION, indent=2) + "\n", encoding="utf-8")
    WEBSITE_SCAN_JSON.write_text(json.dumps(website_scan, indent=2) + "\n", encoding="utf-8")
    SERVICE_CATALOG_JSON.write_text(json.dumps(service_catalog, indent=2) + "\n", encoding="utf-8")
    LANDING_PAGE_MAP_JSON.write_text(json.dumps(landing_page_map, indent=2) + "\n", encoding="utf-8")
    GEO_STRATEGY_JSON.write_text(json.dumps(geo_strategy, indent=2) + "\n", encoding="utf-8")


def write_csv_artifacts() -> None:
    with CAMPAIGN_TAXONOMY_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["campaign", "ad_group", "final_url", "keyword_count"])
        writer.writeheader()
        for ad_group in AD_GROUPS:
            writer.writerow(
                {
                    "campaign": CAMPAIGN,
                    "ad_group": ad_group["name"],
                    "final_url": ad_group["final_url"],
                    "keyword_count": len(ad_group["keywords"]),
                }
            )

    with RSA_COPY_MATRIX_CSV.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["campaign", "ad_group", "asset_type", "slot", "text", "chars"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for ad_group in AD_GROUPS:
            for index, headline in enumerate(ad_group["headlines"], start=1):
                writer.writerow(
                    {
                        "campaign": CAMPAIGN,
                        "ad_group": ad_group["name"],
                        "asset_type": "headline",
                        "slot": index,
                        "text": headline,
                        "chars": len(headline),
                    }
                )
            for index, description in enumerate(ad_group["descriptions"], start=1):
                writer.writerow(
                    {
                        "campaign": CAMPAIGN,
                        "ad_group": ad_group["name"],
                        "asset_type": "description",
                        "slot": index,
                        "text": description,
                        "chars": len(description),
                    }
                )


def write_human_review(report: dict[str, object]) -> None:
    lines = [
        "# Mindful Mental Health Counseling Initial Search Build Review",
        "",
        f"CSV: `{OUTPUT_CSV}`",
        "",
        f"Validation status: `{report['status']}`",
        "",
        "## Build Summary",
        "",
        f"- Campaign: `{CAMPAIGN}`",
        f"- Ad groups: `{len(AD_GROUPS)}`",
        f"- Phrase keywords: `{sum(len(ad_group['keywords']) for ad_group in AD_GROUPS)}`",
        f"- Negative phrase keywords: `{len(NEGATIVE_KEYWORDS)}`",
        "- Match type: `Phrase` only",
        "- Networks: `Google search` only",
        "- API upload: off",
        "- All rows are paused for Google Ads Editor review.",
        "",
        "## Source-Based Decisions",
        "",
        "- Website confirms online therapy for New York and New Jersey.",
        "- Website confirms anxiety, depression, OCD, individual therapy, group therapy, CBT, DBT, ACT, and mindfulness positioning.",
        "- Contact page confirms out-of-network insurance and superbill language.",
        "- Group therapy page confirms online sessions and NY/NJ licensing eligibility.",
        "",
        "## Human Review Before Launch",
        "",
        "- Confirm client-approved monthly or daily budget.",
        "- Confirm whether New York and New Jersey should be split into separate campaigns.",
        "- Confirm whether group therapy is actively enrolling or should remain paused.",
        "- Confirm whether adolescent therapy can be advertised and what age/guardian language is approved.",
        "- Confirm final negative keyword list against actual account search term data.",
        "- Import into Google Ads Editor and inspect platform warnings before upload.",
        "",
        "## Sources",
        "",
        "- https://nycmindfulmentalhealthcounseling.com/",
        "- https://nycmindfulmentalhealthcounseling.com/contact/",
        "- https://nycmindfulmentalhealthcounseling.com/group-therapy-nyc/",
        "- https://nycmindfulmentalhealthcounseling.com/cbt/",
        "- https://nycmindfulmentalhealthcounseling.com/dbt/",
    ]
    HUMAN_REVIEW_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    write_json_artifacts()
    write_csv_artifacts()
    report = build_staging()
    write_human_review(report)
    post_report = validate_file(OUTPUT_CSV)
    if post_report["status"] != "pass":
        raise RuntimeError(f"Staging validation failed: {post_report['issues']}")
    print(json.dumps(post_report, indent=2))


if __name__ == "__main__":
    main()
