#!/usr/bin/env python3
"""Generate a Google Ads Editor staging CSV for the THHL services search build."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


CLIENT_DIR = Path("/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy")
BUILD_DIR = CLIENT_DIR / "build" / "search_rebuild_test"

CURRENT_EXPORT = CLIENT_DIR / "campaigns" / "ThinkHappyLiveHealthy_export_2026-04-27.csv"
TAXONOMY = BUILD_DIR / "service_ad_group_taxonomy_2026-04-28.csv"
BLUEPRINT = BUILD_DIR / "rsa_copy_blueprint.json"
TARGETING_SPEC = BUILD_DIR / "targeting_spec.json"
KEYWORD_EXPANSION = BUILD_DIR / "phrase_keyword_expansion_candidates_2026-04-28.csv"

OUTPUT_CSV = BUILD_DIR / "THHL_Search_Services_Editor_Staging_CURRENT.csv"
VALIDATION_REPORT = BUILD_DIR / "THHL_Search_Services_Editor_Staging_CURRENT_validation.json"
REVIEW_MD = BUILD_DIR / "THHL_Search_Services_Editor_Staging_CURRENT_review.md"

CAMPAIGN = "ARC - Search - Services - V1"
DEFAULT_FINAL_URL = "https://www.thinkhappylivehealthy.com/"

HEADLINE_LIMIT = 30
DESCRIPTION_LIMIT = 90
PATH_LIMIT = 15


SERVICE_PAGE_MAP = {
    ("Psychiatry", ""): "https://www.thinkhappylivehealthy.com/psychiatry",
    ("Therapy", "ADHD"): "https://www.thinkhappylivehealthy.com/adhd-therapy",
    ("Therapy", "EMDR"): "https://www.thinkhappylivehealthy.com/emdr-therapy",
    ("Therapy", "Trauma"): "https://www.thinkhappylivehealthy.com/emdr-therapy",
    ("Therapy", ""): "https://www.thinkhappylivehealthy.com/therapy-about",
    ("Testing", "Child Psychological"): "https://www.thinkhappylivehealthy.com/comprehensive-psychological-testing",
    ("Testing", "Psychoeducational"): "https://www.thinkhappylivehealthy.com/psychoeducational-evaluations",
    ("Testing", "Kindergarten Readiness"): "https://www.thinkhappylivehealthy.com/kindergarten-readiness",
    ("Testing", ""): "https://www.thinkhappylivehealthy.com/comprehensive-psychological-testing",
    ("Parent Child Services", ""): "https://www.thinkhappylivehealthy.com/parent-child",
}

PATH_1_MAP = {
    "Psychiatry": "Psychiatry",
    "Therapy": "Therapy",
    "Testing": "Testing",
    "Parent Child Services": "Parent-Child",
}

PATH_2_MAP = {
    "General": "Care",
    "Local": "Near-Me",
    "City": "Ashburn",
    "State": "Virginia",
}

LOCATION_IDS = {
    "Washington, District of Columbia, United States": "1014895",
    "Arlington, Virginia, United States": "1027027",
    "Ashburn, Virginia, United States": "1027028",
    "Dulles, Virginia, United States": "1027106",
    "Falls Church, Virginia, United States": "1027118",
    "Herndon, Virginia, United States": "1027163",
    "Leesburg, Virginia, United States": "1027188",
    "McLean, Virginia, United States": "1027213",
    "Prince William County, Virginia, United States": "1027258",
    "Reston, Virginia, United States": "1027266",
    "Sterling, Virginia, United States": "1027296",
    "Vienna, Virginia, United States": "1027317",
    "Maryland, United States": "21153",
    "Virginia, United States": "21178",
    "Arlington County, Virginia, United States": "9059705",
    "Fairfax County, Virginia, United States": "9059726",
    "Loudoun County, Virginia, United States": "9059749",
}

TARGET_CITIES = [
    "Ashburn VA",
    "Falls Church VA",
    "Leesburg VA",
    "Sterling VA",
    "Dulles VA",
    "Reston VA",
    "Vienna VA",
    "Herndon VA",
    "McLean VA",
    "Arlington VA",
]

STATE_MODIFIERS = ["Virginia", "VA", "Northern Virginia"]

ROOT_VARIANTS = {
    ("Psychiatry", "Children"): [
        "child psychiatry",
        "child psychiatrist",
        "children's psychiatrist",
        "child and adolescent psychiatry",
        "pediatric psychiatrist",
        "youth psychiatry",
    ],
    ("Psychiatry", "Adult"): [
        "psychiatry",
        "psychiatrist",
        "psychiatric care",
        "psychiatric services",
        "psychiatric nurse practitioner",
        "psych np",
        "pmhnp",
        "psychiatric evaluation",
    ],
    ("Therapy", "Anxiety"): [
        "anxiety therapy",
        "anxiety therapist",
        "anxiety counseling",
        "anxiety treatment",
        "cbt for anxiety",
    ],
    ("Therapy", "ADHD"): [
        "adhd therapy",
        "adhd therapist",
        "adhd treatment",
        "adhd counseling",
        "adhd therapist for kids",
        "adhd treatment for adults",
    ],
    ("Therapy", "Autism"): [
        "autism therapy",
        "autism therapist",
        "autism counseling",
    ],
    ("Therapy", "Depression"): [
        "depression therapy",
        "depression therapist",
        "depression treatment",
        "treatment resistant depression",
        "esketamine",
    ],
    ("Therapy", "LGBTQIA+"): [
        "lgbtqia therapy",
        "lgbtq therapist",
        "lgbtqia counseling",
        "lgbtq counseling",
    ],
    ("Therapy", "Stress"): [
        "stress therapy",
        "stress therapist",
        "stress counseling",
    ],
    ("Therapy", "Grief And Loss"): [
        "grief therapy",
        "grief therapist",
        "grief counseling",
        "loss counseling",
    ],
    ("Therapy", "Trauma"): [
        "trauma therapy",
        "trauma therapist",
        "trauma counseling",
    ],
    ("Therapy", "Postpartum Support"): [
        "postpartum counseling",
        "postpartum therapist",
        "postpartum therapy",
        "postpartum support counseling",
    ],
    ("Therapy", "Children"): [
        "child therapy",
        "child therapist",
        "children's therapist",
        "youth therapy",
        "child behavioral therapist",
        "child behavioral therapy",
    ],
    ("Therapy", "EMDR"): [
        "emdr therapy",
        "emdr therapist",
        "emdr counseling",
    ],
    ("Therapy", "CBT"): [
        "cognitive behavioral therapy",
        "cbt therapy",
        "cbt therapist",
        "cbt for anxiety",
    ],
    ("Therapy", "DBT"): [
        "dialectical behavior therapy",
        "dbt therapy",
        "dbt therapist",
    ],
    ("Therapy", "Somatic"): [
        "somatic therapy",
        "somatic therapist",
    ],
    ("Therapy", "Mindfulness"): [
        "mindfulness therapy",
        "mindfulness therapist",
        "mindfulness counseling",
    ],
    ("Testing", "Child Psychological"): [
        "child psychological testing",
        "children's psychological testing",
        "child psychological evaluation",
        "psychological evaluation for child",
        "child psychologist testing",
    ],
    ("Testing", "Psychoeducational"): [
        "psychoeducational evaluation",
        "psychoeducational evaluations",
        "psychoeducational testing",
        "learning disability testing",
        "iep testing",
    ],
    ("Testing", "Gifted"): [
        "gifted testing",
        "gifted evaluation",
        "gifted child testing",
    ],
    ("Testing", "ADHD"): [
        "adhd testing",
        "adhd assessment",
        "adhd evaluation",
        "adhd testing for children",
        "children adhd testing",
        "adhd screening for kids",
    ],
    ("Testing", "Kindergarten Readiness"): [
        "kindergarten readiness testing",
        "kindergarten readiness assessment",
        "school readiness testing",
    ],
    ("Testing", "Autism"): [
        "autism testing",
        "autism evaluation",
        "autism assessment",
        "autism testing for children",
    ],
    ("Parent Child Services", "Children"): [
        "parent child services",
        "parent child therapy",
        "parent child counseling",
        "parenting support",
    ],
}


def read_headers(path: Path) -> list[str]:
    with path.open("r", encoding="utf-16", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames:
            raise RuntimeError(f"No headers found in {path}")
        headers = list(reader.fieldnames)
        if "Location ID" not in headers:
            location_index = headers.index("Location") + 1 if "Location" in headers else len(headers)
            headers.insert(location_index, "Location ID")
        return headers


def read_taxonomy(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def blank_row(headers: list[str]) -> dict[str, str]:
    return {header: "" for header in headers}


def truncate(value: str, limit: int) -> str:
    value = " ".join(value.split()).strip()
    return value if len(value) <= limit else value[:limit].rstrip()


def title_words(value: str) -> str:
    acronyms = {
        "adhd": "ADHD",
        "add": "ADD",
        "emdr": "EMDR",
        "cbt": "CBT",
        "dbt": "DBT",
        "lgbtq": "LGBTQ",
        "lgbtqia": "LGBTQIA",
        "lgbtqia+": "LGBTQIA+",
        "pmhnp": "PMHNP",
        "np": "NP",
        "va": "VA",
        "dc": "DC",
        "iep": "IEP",
    }
    small_words = {"and", "or", "for", "of", "the", "to", "in"}
    formatted: list[str] = []
    for index, word in enumerate(value.replace("-", " - ").split()):
        lower = word.lower()
        if lower == "-":
            formatted.append("-")
        elif lower in acronyms:
            formatted.append(acronyms[lower])
        elif index > 0 and lower in small_words:
            formatted.append(lower)
        elif lower.endswith("'s") and len(lower) > 2:
            formatted.append(lower[:-2].capitalize() + "'s")
        else:
            formatted.append(lower.capitalize())
    text = " ".join(formatted).replace(" - ", "-")
    return text.replace("Mclean", "McLean")


def keyword_text(value: str) -> str:
    return title_words(value)


def headline_phrase(value: str) -> str:
    replacements = {
        "Cognitive Behavioral Therapy": "CBT Therapy",
        "Dialectical Behavior Therapy": "DBT Therapy",
        "Psychoeducational Evaluation": "Learning Evaluation",
        "Kindergarten Readiness Testing": "Kindergarten Readiness Test",
        "Psychoeducational Evaluations": "Psychoeducational Evals",
        "Treatment Resistant Depression": "Depression Therapy Support",
    }
    text = title_words(value)
    return replacements.get(text, text)


def read_keyword_expansion(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    expansion: dict[str, list[str]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("source_action") != "add_phrase":
                continue
            ad_group = row["ad_group"]
            keyword = keyword_text(row["keyword"])
            expansion.setdefault(ad_group, [])
            if keyword not in expansion[ad_group]:
                expansion[ad_group].append(keyword)
    return expansion


def keyword_roots(row: dict[str, str]) -> list[str]:
    roots = ROOT_VARIANTS.get((row["service"], row["audience_or_category"]))
    if roots:
        return roots
    return [row["seed_phrase_keyword"].strip('"')]


def layer_keywords(row: dict[str, str]) -> list[str]:
    roots = keyword_roots(row)
    layer = row["intent_layer"]
    if layer == "General":
        raw_keywords = roots
    elif layer == "Local":
        raw_keywords = [f"{root} near me" for root in roots]
    elif layer == "City":
        raw_keywords = [f"{root} {city}" for root in roots for city in TARGET_CITIES]
    elif layer == "State":
        raw_keywords = [f"{root} {state}" for root in roots for state in STATE_MODIFIERS]
    else:
        raw_keywords = roots

    seen: set[str] = set()
    output: list[str] = []
    for keyword in raw_keywords:
        formatted = keyword_text(keyword)
        key = formatted.lower()
        if key not in seen:
            seen.add(key)
            output.append(formatted)
    return output


def audience_label(value: str) -> str:
    return {
        "Children": "Child",
        "Adult": "Adult",
        "Grief And Loss": "Grief Support",
        "Postpartum Support": "Postpartum",
        "Child Psychological": "Child Psych",
        "Kindergarten Readiness": "Kindergarten",
        "Parent Child Services": "Parent Child",
    }.get(value, title_words(value))


def service_key(row: dict[str, str]) -> tuple[str, str]:
    service = row["service"]
    audience = row["audience_or_category"]
    if service == "Parent Child Services":
        return ("Parent Child Services", "")
    if service == "Psychiatry":
        return ("Psychiatry", "")
    if service == "Testing":
        return ("Testing", audience)
    if service == "Therapy":
        return ("Therapy", audience)
    return (service, audience)


def landing_page(row: dict[str, str]) -> tuple[str, bool]:
    key = service_key(row)
    if key in SERVICE_PAGE_MAP:
        return SERVICE_PAGE_MAP[key], True
    fallback = (key[0], "")
    if fallback in SERVICE_PAGE_MAP:
        return SERVICE_PAGE_MAP[fallback], False
    return DEFAULT_FINAL_URL, False


def base_campaign_row(headers: list[str]) -> dict[str, str]:
    row = blank_row(headers)
    row.update({
        "Campaign": CAMPAIGN,
        "Campaign Type": "Search",
        "Networks": "Google search",
        "Budget": "60.00",
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
    })
    return row


def ad_group_row(headers: list[str], ad_group: str) -> dict[str, str]:
    row = blank_row(headers)
    row.update({
        "Campaign": CAMPAIGN,
        "Ad Group": ad_group,
        "Max CPC": "5.00",
        "Campaign Status": "Enabled",
        "Ad Group Status": "Paused",
        "Status": "Enabled",
    })
    return row


def keyword_row(headers: list[str], ad_group: str, keyword: str) -> dict[str, str]:
    row = blank_row(headers)
    row.update({
        "Campaign": CAMPAIGN,
        "Ad Group": ad_group,
        "Keyword": keyword,
        "Criterion Type": "Phrase",
        "Account keyword type": "None",
        "Campaign Status": "Enabled",
        "Ad Group Status": "Paused",
        "Status": "Enabled",
    })
    return row


def make_headlines(row: dict[str, str]) -> list[str]:
    service = row["service"]
    audience = row["audience_or_category"]
    layer = row["intent_layer"]
    roots = [headline_phrase(root) for root in keyword_roots(row)]
    service_label = title_words(service)
    audience_display = audience_label(audience)

    if service == "Parent Child Services":
        service_label = "Parent Child Care"
    if service == "Testing":
        service_label = f"{audience_display} Testing"
    if service == "Therapy":
        service_label = f"{audience_display} Therapy"
    if service == "Psychiatry":
        service_label = f"{audience_display} Psychiatry"

    bare_terms = {service_label.lower(), service.lower(), audience_display.lower(), roots[0].lower()}

    geo_headlines = {
        "General": ["Northern Virginia Care", "Ashburn & Falls Church"],
        "Local": ["Care Near You Today", "Local Appointments Open"],
        "City": [f"{service_label} Ashburn", f"{service_label} Falls Church", "Ashburn & Falls Church"],
        "State": [f"{service_label} Virginia", "Virginia Telehealth Care", "Serving VA Clients"],
    }[layer]

    service_headlines: list[str]
    value_headlines: list[str]
    if service == "Testing":
        service_headlines = [
            f"Schedule {service_label}",
            f"{service_label} Near You",
            f"{roots[0]} Help",
            f"{roots[1]} Near You" if len(roots) > 1 else f"{audience_display} Evaluation",
            f"{audience_display} Assessment",
        ]
        value_headlines = [
            "Clear Next Steps For School",
            "Licensed Child Evaluators",
            "Testing For School Needs",
            "Support For IEP Planning",
            "Results You Can Use",
            "Book Your Assessment",
        ]
    elif service == "Psychiatry":
        service_headlines = [
            f"{service_label} Appointments",
            f"{service_label} Near You",
            f"{roots[0]} Care",
            f"{roots[1]} Near You" if len(roots) > 1 else "Psychiatric Care Near You",
            "Medication Mgmt Support",
        ]
        value_headlines = [
            "Accepting New Patients",
            "Telehealth & In-Person",
            "Care Planning Support",
            "Psych Nurse Practitioners",
            "Book Psychiatry Consult",
            "VA, DC & MD Access",
        ]
    elif service == "Parent Child Services":
        service_headlines = [
            "Parent-Child Therapy",
            "Parent-Child Services",
            "Child Counseling Near You",
            "Family Support Services",
            "Behavior Support For Kids",
        ]
        value_headlines = [
            "Support For Families",
            "Help Your Child Thrive",
            "Parent Guidance Available",
            "In-Person & Online Care",
            "Book A Family Consult",
        ]
    else:
        service_headlines = [
            f"{service_label} Appointments",
            f"{service_label} Near You",
            f"{roots[0]} Help",
            f"{roots[1]} Near You" if len(roots) > 1 else f"{audience_display} Therapist Near You",
            f"{audience_display} Counseling",
        ]
        value_headlines = [
            "Licensed Therapists Near You",
            "In-Person & Online Therapy",
            "Start With A Therapist",
            "Support That Fits Life",
            "Book Therapy Appointment",
            "Care For Kids & Adults",
        ]

    shared_headlines = [
        "Ashburn & Falls Church",
        "Northern Virginia Care",
        "Telehealth Available",
        "Appointments Available",
        "Insurance Options Available",
        "Think Happy Live Healthy",
        "Request Appointment Today",
    ]

    candidates = [
        *service_headlines,
        *geo_headlines,
        *value_headlines,
        *shared_headlines,
    ]

    filler = [
        f"{service_label} Appointments",
        "Personalized Care Plan",
        "Mental Health Support",
        "Schedule A Visit Today",
        "VA Mental Health Care",
    ]

    def useful(value: str) -> bool:
        value = value.strip()
        lower = value.lower()
        word_count = len(value.replace("&", " ").replace("/", " ").split())
        if lower in bare_terms:
            return False
        if word_count < 2:
            return False
        if len(value) < 16 and not any(token in value for token in ["ADHD", "EMDR", "CBT", "DBT"]):
            return False
        return True

    def score(value: str) -> int:
        lower = value.lower()
        points = len(value)
        if any(root.lower() in lower for root in roots):
            points += 12
        if any(term in lower for term in ["near you", "ashburn", "falls church", "virginia", "northern va"]):
            points += 8
        if any(term in lower for term in ["licensed", "appointment", "telehealth", "in-person", "support", "assessment", "evaluators", "medication"]):
            points += 6
        if len(value) < 18:
            points -= 10
        return points

    seen: set[str] = set()
    clean_candidates: list[str] = []
    for candidate in [*candidates, *filler]:
        value = truncate(candidate, HEADLINE_LIMIT)
        lower = value.lower()
        if lower in seen or not useful(value):
            continue
        seen.add(lower)
        clean_candidates.append(value)

    clean_candidates.sort(key=score, reverse=True)
    headlines = clean_candidates[:15]

    backup = [
        "Licensed Mental Health Care",
        "Book Your Appointment Today",
        "Ashburn & Falls Church Care",
        "Telehealth And In-Person",
        "Support With Clear Next Steps",
    ]
    for candidate in backup:
        if len(headlines) == 15:
            break
        value = truncate(candidate, HEADLINE_LIMIT)
        if value.lower() not in {h.lower() for h in headlines}:
            headlines.append(value)

    return headlines


def make_descriptions(row: dict[str, str]) -> list[str]:
    service = row["service"]
    audience = row["audience_or_category"]
    layer = row["intent_layer"]
    audience_display = audience_label(audience).lower()
    audience_title = audience_label(audience)

    if service == "Testing":
        service_phrase = f"{audience_title} testing"
        service_sentence = f"Schedule {service_phrase} with licensed evaluators in Northern Virginia."
        process = "Get clear recommendations for school, support planning, and next steps."
    elif service == "Psychiatry":
        service_phrase = f"{audience_title} psychiatry"
        service_sentence = f"{title_words(service_phrase)} with medication support and care planning options."
        process = "Meet psychiatric nurse practitioners online or in person in Northern Virginia."
    elif service == "Parent Child Services":
        service_phrase = "parent child services"
        service_sentence = "Parent child services with practical support for families and children."
        process = "Get guidance for behavior, connection, and family communication goals."
    else:
        service_phrase = f"{audience_title} therapy"
        service_sentence = f"Find {service_phrase} with licensed therapists in Northern Virginia."
        process = "Choose in-person or online therapy with support matched to your goals."

    location = {
        "General": "Care is available in Ashburn, Falls Church, and through telehealth.",
        "Local": "Find local care near you in Ashburn, Falls Church, or online.",
        "City": "Get care in Ashburn or Falls Church with telehealth options available.",
        "State": "Virginia clients can access care in person or through telehealth.",
    }[layer]

    descriptions = [
        service_sentence,
        process,
        location,
        "Book an appointment with Think Happy Live Healthy today.",
    ]
    return [truncate(description, DESCRIPTION_LIMIT) for description in descriptions]


def rsa_row(headers: list[str], taxonomy_row: dict[str, str]) -> dict[str, str]:
    row = blank_row(headers)
    final_url, exact_page = landing_page(taxonomy_row)
    path_1 = PATH_1_MAP.get(taxonomy_row["service"], "Care")
    path_2 = PATH_2_MAP.get(taxonomy_row["intent_layer"], "Care")
    headlines = make_headlines(taxonomy_row)
    descriptions = make_descriptions(taxonomy_row)

    row.update({
        "Campaign": CAMPAIGN,
        "Ad Group": taxonomy_row["ad_group"],
        "Ad type": "Responsive search ad",
        "Path 1": truncate(path_1, PATH_LIMIT),
        "Path 2": truncate(path_2, PATH_LIMIT),
        "Final URL": final_url,
        "Campaign Status": "Enabled",
        "Ad Group Status": "Paused",
        "Status": "Enabled",
        "Comment": "" if exact_page else "Landing page fallback needs human review",
    })
    for index, headline in enumerate(headlines, start=1):
        row[f"Headline {index}"] = headline
    for index, description in enumerate(descriptions, start=1):
        row[f"Description {index}"] = description
    return row


def targeting_rows(headers: list[str], spec: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def base() -> dict[str, str]:
        row = blank_row(headers)
        row.update({
            "Campaign": CAMPAIGN,
            "Targeting method": "Location of presence",
            "Exclusion method": "Location of presence",
            "Campaign Status": "Enabled",
            "Status": "Enabled",
        })
        return row

    for layer in spec["geo_layers"]:
        for location in layer["locations"]:
            row = base()
            row.update({
                "Location": location,
                "Location ID": LOCATION_IDS.get(location, ""),
                "Bid Modifier": layer.get("bid_modifier", ""),
                "Comment": f"{layer['tier']} | {layer['review_status']}",
            })
            rows.append(row)

    for target in spec["radius_targets"]:
        row = base()
        row.update({
            "Location": target["location"],
            "Radius": target["radius"],
            "Unit": target["unit"],
            "Bid Modifier": target.get("bid_modifier", ""),
            "Comment": f"radius | {target['review_status']}",
        })
        rows.append(row)

    return rows


def validate(headers: list[str], rows: list[dict[str, str]]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    counts = Counter()

    for row_number, row in enumerate(rows, start=2):
        if row.get("Ad Group") and not row.get("Keyword") and not row.get("Ad type"):
            counts["ad_group_rows"] += 1
        if row.get("Keyword"):
            counts["keyword_rows"] += 1
            if row.get("Criterion Type") != "Phrase":
                issues.append({"severity": "error", "row": row_number, "message": "Keyword is not phrase match."})
            if row["Keyword"].startswith('"') or row["Keyword"].startswith("["):
                issues.append({"severity": "error", "row": row_number, "message": "Keyword text should be plain when Criterion Type is Phrase."})
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
                if not value:
                    issues.append({"severity": "error", "row": row_number, "message": f"Missing {path_field}."})
                if len(value) > PATH_LIMIT:
                    issues.append({"severity": "error", "row": row_number, "message": f"{path_field} exceeds 15 chars: {value}"})
            if not row.get("Final URL"):
                issues.append({"severity": "error", "row": row_number, "message": "Missing Final URL."})
        if row.get("Location"):
            counts["location_rows"] += 1
            if not row.get("Radius") and not row.get("Location ID"):
                issues.append({"severity": "warning", "row": row_number, "message": f"Named location has no Location ID: {row.get('Location')}"})
        if row.get("Radius"):
            counts["radius_rows"] += 1
        if row.get("Bid Modifier"):
            counts["bid_modifier_rows"] += 1

    return {
        "status": "pass" if not any(issue["severity"] == "error" for issue in issues) else "fail",
        "headers": len(headers),
        "rows": len(rows),
        "counts": dict(counts),
        "issues": issues,
    }


def write_tsv(headers: list[str], rows: list[dict[str, str]]) -> None:
    with OUTPUT_CSV.open("w", encoding="utf-16", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_review(report: dict[str, Any]) -> None:
    lines = [
        "# THHL Search Services Editor Staging Review",
        "",
        f"CSV: `{OUTPUT_CSV}`",
        "",
        f"Validation status: `{report['status']}`",
        f"Rows: `{report['rows']}`",
        f"Headers: `{report['headers']}`",
        "",
        "## Counts",
        "",
    ]
    for key, value in sorted(report["counts"].items()):
        lines.append(f"- {key}: `{value}`")
    lines.extend([
        "",
        "## Review Notes",
        "",
        "- All ad groups are paused for staging review.",
        "- Keywords are phrase match only.",
        "- One RSA is generated per ad group.",
        "- Some final URLs are service-family fallbacks and need human review.",
        "- Import this file into Google Ads Editor first, then inspect errors before upload.",
        "",
        "## Issues",
        "",
    ])
    if report["issues"]:
        for issue in report["issues"]:
            lines.append(f"- `{issue['severity']}` row {issue.get('row', '')}: {issue['message']}")
    else:
        lines.append("- No local validation issues.")
    REVIEW_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    headers = read_headers(CURRENT_EXPORT)
    taxonomy = read_taxonomy(TAXONOMY)
    json.loads(BLUEPRINT.read_text(encoding="utf-8"))
    spec = json.loads(TARGETING_SPEC.read_text(encoding="utf-8"))
    keyword_expansion = read_keyword_expansion(KEYWORD_EXPANSION)

    rows: list[dict[str, str]] = [base_campaign_row(headers)]
    keyword_seen: set[tuple[str, str]] = set()
    for item in taxonomy:
        rows.append(ad_group_row(headers, item["ad_group"]))
        for phrase_keyword in layer_keywords(item):
            key = (item["ad_group"], phrase_keyword.lower())
            if key in keyword_seen:
                continue
            keyword_seen.add(key)
            rows.append(keyword_row(headers, item["ad_group"], phrase_keyword))
        for keyword in keyword_expansion.get(item["ad_group"], []):
            key = (item["ad_group"], keyword.lower())
            if key in keyword_seen:
                continue
            keyword_seen.add(key)
            rows.append(keyword_row(headers, item["ad_group"], keyword))
        rows.append(rsa_row(headers, item))
    rows.extend(targeting_rows(headers, spec))

    write_tsv(headers, rows)
    report = validate(headers, rows)
    report["output_csv"] = str(OUTPUT_CSV)
    report["sources"] = {
        "taxonomy": str(TAXONOMY),
        "blueprint": str(BLUEPRINT),
        "targeting_spec": str(TARGETING_SPEC),
        "keyword_expansion": str(KEYWORD_EXPANSION),
        "headers_source": str(CURRENT_EXPORT),
    }
    VALIDATION_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_review(report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
