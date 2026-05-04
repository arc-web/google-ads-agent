"""Reusable client feedback classification and revision staging helpers."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from shared.rebuild.csv_naming import generated_csv_path, validate_generated_csv_name
from shared.rebuild.geo_taxonomy import GeoAdGroupPlan, build_geo_ad_group_plans, parse_geo_target
from shared.rebuild.rsa_headline_quality import generate_quality_headlines
from shared.rebuild.staging_validator import validate_file


REVISION_CATEGORIES = [
    "business_fact",
    "capacity_constraint",
    "campaign_revision",
    "client_preference",
    "strategy_question",
    "expert_override_needed",
    "capacity_ramp",
    "audience_constraint",
    "geo_architecture",
    "budget_strategy",
    "service_pause",
    "future_service_launch",
    "client_growth_goal",
    "billing_question",
]

ADOLESCENT_TERMS = [
    "adolescent",
    "adolescents",
    "teen therapy",
    "therapy for teens",
    "child therapist",
    "minor therapy",
    "parent seeking therapy for teen",
]
GROUP_TERMS = ["group therapy", "therapy group", "social anxiety group"]
COLLEGE_KEYWORDS = [
    "college student therapy",
    "therapy for college students",
    "college anxiety therapy",
    "online therapy for college students",
]
STATE_TARGETS = [
    {"label": "NY", "location": "New York, United States", "location_id": "21167"},
    {"label": "NJ", "location": "New Jersey, United States", "location_id": "21164"},
]


@dataclass(frozen=True)
class ClassifiedFeedbackItem:
    id: str
    client_feedback: str
    categories: list[str]
    severity: str
    launch_blocker: bool
    campaign_effect: str
    report_effect: str
    client_hq_updates: dict[str, Any] = field(default_factory=dict)
    human_review_required: list[str] = field(default_factory=list)


def classify_revision_feedback(feedback_text: str, *, source: str = "client_response") -> dict[str, Any]:
    """Classify high-signal client feedback into campaign and report effects."""
    text = normalize_text(feedback_text)
    items: list[ClassifiedFeedbackItem] = []

    if any(token in text for token in ("openings", "caseload", "associate therapist", "end of may", "fall")):
        items.append(
            ClassifiedFeedbackItem(
                id="R001",
                client_feedback="Capacity changed: owner has 2 to 3 openings now, associate adds capacity end of May and ramps into fall.",
                categories=["business_fact", "capacity_constraint", "capacity_ramp", "client_growth_goal"],
                severity="High",
                launch_blocker=False,
                campaign_effect="Use conservative May pacing and document June capacity ramp before launch approval.",
                report_effect="Show optional Capacity And Lead Goal section when growth goal facts are present.",
                client_hq_updates={
                    "capacity_notes": [
                        "Owner has immediate openings for about 2 to 3 clients.",
                        "Associate therapist starts at the end of May with openings for 6 clients.",
                        "Associate capacity is expected to reach 10 to 12 clients in the fall.",
                    ],
                    "growth_goals": {
                        "initial_new_client_goal": 2,
                        "planning_close_rate": 0.5,
                        "minimum_qualified_leads": 4,
                        "planning_qualified_lead_range": "4 to 8",
                    },
                },
                human_review_required=["Confirm actual intake close rate after the first conversion data is available."],
            )
        )

    if "college students" in text or "adolescents" in text:
        items.append(
            ClassifiedFeedbackItem(
                id="R002",
                client_feedback="Audience changed: keep young adults and adults, target college students instead of adolescents.",
                categories=["campaign_revision", "audience_constraint", "client_preference"],
                severity="High",
                launch_blocker=True,
                campaign_effect="Remove adolescent targeting and add compliant college-student intent.",
                report_effect="Explain that the revised campaign focuses on adults, young adults, and college students.",
                client_hq_updates={
                    "audience_notes": [
                        "Target young adults and adults for now.",
                        "Target college students instead of adolescents.",
                    ],
                    "do_not_target": ["adolescents", "teens", "children", "minors"],
                },
            )
        )

    if "state makes the most sense" in text or "splitting it up by state" in text:
        items.append(
            ClassifiedFeedbackItem(
                id="R003",
                client_feedback="Geo architecture preference: split campaigns by state.",
                categories=["campaign_revision", "geo_architecture", "client_preference"],
                severity="Medium",
                launch_blocker=True,
                campaign_effect="Create state-specific NY and NJ campaign variants for staged review.",
                report_effect="Describe state split as the revised launch structure.",
                client_hq_updates={"revision_facts": {"geo_architecture": "split_by_state"}},
            )
        )

    if "budget" in text or "conservative in may" in text or "increase in june" in text:
        items.append(
            ClassifiedFeedbackItem(
                id="R004",
                client_feedback="Budget question: clarify management fee versus ad spend and recommend May conservative pacing with June ramp.",
                categories=["strategy_question", "budget_strategy", "billing_question"],
                severity="Medium",
                launch_blocker=True,
                campaign_effect="Do not force spend. Stage May conservative pacing and require budget approval before launch.",
                report_effect="Show budget pacing as a recommendation and include billing as an internal confirmation item.",
                client_hq_updates={
                    "billing_questions": [
                        "Client asked whether the amount already paid applies only to management fee or also to ad spend.",
                    ],
                    "revision_facts": {
                        "budget_strategy": "conservative_may_then_june_ramp",
                    },
                },
                human_review_required=["Account manager must confirm billing and ad spend treatment before replying as fact."],
            )
        )

    if "not currently enrolling any groups" in text or "two groups in september" in text:
        items.append(
            ClassifiedFeedbackItem(
                id="R005",
                client_feedback="Group therapy is not active now. Two groups are planned for September.",
                categories=["campaign_revision", "service_pause", "future_service_launch"],
                severity="High",
                launch_blocker=True,
                campaign_effect="Pause or exclude group therapy from the active revision build.",
                report_effect="Move groups to a September roadmap note instead of active launch scope.",
                client_hq_updates={
                    "paused_services": ["Group Therapy"],
                    "future_service_launches": ["Two groups planned for September."],
                },
            )
        )

    classified = {
        "status": "classified",
        "approved_for_rebuild": True,
        "feedback_source": source,
        "categories_available": REVISION_CATEGORIES,
        "items": [asdict(item) for item in items],
        "campaign_directives": {
            "exclude_terms": ADOLESCENT_TERMS + GROUP_TERMS,
            "add_college_student_intent": True,
            "split_by_state": True,
            "paused_services": ["Group Therapy"],
            "future_service_launches": ["Two groups planned for September."],
            "budget_strategy": "conservative_may_then_june_ramp",
        },
        "report_goal": {
            "section_title": "Capacity And Lead Goal",
            "initial_new_client_goal": 2,
            "planning_close_rate": 0.5,
            "minimum_qualified_leads": 4,
            "planning_qualified_lead_range": "4 to 8",
            "capacity_notes": [
                "Owner has immediate openings for about 2 to 3 clients.",
                "Associate therapist starts at the end of May with openings for 6 clients.",
                "Associate capacity is expected to reach 10 to 12 clients in the fall.",
            ],
            "pacing_recommendation": "Start more conservatively in May, then increase in June when associate capacity begins.",
            "assumption_note": "Close rate is a planning assumption until confirmed by campaign data.",
        },
        "email_notes": [
            "Reference the attached PDF and revised campaign build.",
            "Do not include raw CSV filenames.",
            "Ask account manager to confirm management fee versus ad spend before stating billing details as fact.",
        ],
    }
    return classified


def write_revision_artifacts(
    *,
    feedback_text: str,
    client_root: Path,
    build_dir: Path,
    source: str,
) -> dict[str, Path]:
    classified = classify_revision_feedback(feedback_text, source=source)
    classified_path = build_dir / "client_feedback_classified.json"
    decision_log_path = build_dir / "revision_decision_log.csv"
    classified_path.write_text(json.dumps(classified, indent=2) + "\n", encoding="utf-8")
    write_decision_log(decision_log_path, classified)
    merge_client_hq_revision_facts(client_root, classified)
    return {"client_feedback_classified": classified_path, "revision_decision_log": decision_log_path}


def write_decision_log(path: Path, classified: dict[str, Any]) -> Path:
    fieldnames = ["id", "decision", "why", "output_to_update", "engine_rule_update_needed", "owner"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in classified.get("items", []):
            writer.writerow(
                {
                    "id": item["id"],
                    "decision": item["campaign_effect"],
                    "why": item["client_feedback"],
                    "output_to_update": "staging_csv; client_report; client_email_draft; client_hq",
                    "engine_rule_update_needed": "Yes",
                    "owner": "ARC",
                }
            )
    return path


def merge_client_hq_revision_facts(client_root: Path, classified: dict[str, Any]) -> Path:
    hq_dir = client_root / "docs" / "client_hq"
    hq_dir.mkdir(parents=True, exist_ok=True)
    json_path = hq_dir / "client_hq.json"
    data = json.loads(json_path.read_text(encoding="utf-8")) if json_path.exists() else {}
    for item in classified.get("items", []):
        updates = item.get("client_hq_updates", {})
        for key, value in updates.items():
            if isinstance(value, list):
                current = list(data.get(key, []))
                data[key] = append_unique(current, [str(entry) for entry in value])
            elif isinstance(value, dict):
                current_dict = dict(data.get(key, {}))
                current_dict.update(value)
                data[key] = current_dict
            else:
                data[key] = value
    revision_facts = dict(data.get("revision_facts", {}))
    revision_facts.update(
        {
            "latest_feedback_status": classified.get("status"),
            "campaign_directives": classified.get("campaign_directives", {}),
            "report_goal": classified.get("report_goal", {}),
        }
    )
    data["revision_facts"] = revision_facts
    json_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return json_path


def build_revised_staging_csv(
    *,
    source_csv: Path,
    output_dir: Path,
    client_slug: str,
    classified: dict[str, Any],
    timestamp: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    with source_csv.open("r", encoding="utf-16", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = [dict(row) for row in reader]
        fieldnames = list(reader.fieldnames or [])
    revised_rows = revise_rows(rows, fieldnames, classified)
    output_csv = generated_csv_path(output_dir, client_slug, "google_ads_editor_staging_rev1", timestamp)
    validate_generated_csv_name(output_csv, client_slug)
    with output_csv.open("w", encoding="utf-16", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(revised_rows)
    validation = validate_file(output_csv)
    (output_dir / f"{output_csv.stem}_validation.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    return output_csv, validation


def revise_rows(rows: list[dict[str, str]], fieldnames: list[str], classified: dict[str, Any]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    base_campaign = source_base_campaign(rows)
    daily_budget = source_budget(rows)
    service_urls = extract_service_urls(rows)
    services = list(service_urls)
    targets = [parse_geo_target(f"{target['location']}|{target['location_id']}") for target in STATE_TARGETS]
    plans = build_geo_ad_group_plans(
        base_campaign=base_campaign,
        services=services,
        locations=targets,
        final_url_for_service=lambda service: service_urls.get(service, first_final_url_for_service(rows, service)),
        path_part=path_part,
        version_suffix="REV1",
        split_by_state=bool(classified.get("campaign_directives", {}).get("split_by_state", True)),
        ad_group_prefix="Therapy",
    )
    campaigns = []
    for plan in plans:
        if plan.campaign not in campaigns:
            campaigns.append(plan.campaign)
    for campaign in campaigns:
        output.append(
            blank_row(
                fieldnames,
                Campaign=campaign,
                **{
                    "Campaign Type": "Search",
                    "Networks": "Google search",
                    "Budget": daily_budget,
                    "Budget type": "Daily",
                    "EU political ads": "No",
                    "Broad match keywords": "Off",
                    "Status": "Paused",
                    "Campaign status": "Paused",
                },
            )
        )
        target = next((item for item in targets if f" - {item.label} - " in campaign), None)
        if target:
            output.append(blank_row(fieldnames, Campaign=campaign, Location=target.location, **{"Location ID": target.location_id}))
        for term in ADOLESCENT_TERMS + GROUP_TERMS:
            output.append(
                blank_row(
                    fieldnames,
                    Campaign=campaign,
                    **{"Criterion Type": "Negative Phrase", "Keyword": term, "Status": "Paused", "Keyword status": "Paused"},
                )
            )
    for plan in plans:
        write_plan_rows(output, fieldnames, plan)
    return output


def state_campaign_name(campaign: str, state_label: str) -> str:
    if campaign.endswith(" - V1"):
        return f"{campaign[:-5]} - {state_label} - REV1"
    if " - REV1" in campaign:
        return campaign
    return f"{campaign} - {state_label} - REV1"


def rewrite_rsa_copy(row: dict[str, str]) -> None:
    ad_group = row.get("Ad Group", "")
    service_label = service_from_ad_group(ad_group)
    headlines = generate_quality_headlines(client_name="", service_label=service_label, ad_group=ad_group)
    for index, headline in enumerate(headlines, start=1):
        if f"Headline {index}" in row:
            row[f"Headline {index}"] = headline
    descriptions = [
        "Review therapy fit, service area, and next steps in a focused consult. Book Today.",
        "Compare practical support options for anxiety, CBT, and related concerns. Call Today.",
        "Confirm availability, private pay details, and care fit before launch. Call Today.",
        "Schedule a consult to review goals, timing, and online therapy options. Book Today.",
    ]
    for index, description in enumerate(descriptions, start=1):
        if f"Description {index}" in row:
            row[f"Description {index}"] = description


def write_plan_rows(output: list[dict[str, str]], fieldnames: list[str], plan: GeoAdGroupPlan) -> None:
    output.append(
        blank_row(
            fieldnames,
            Campaign=plan.campaign,
            **{"Ad Group": plan.ad_group, "Status": "Paused", "Ad Group status": "Paused"},
        )
    )
    keywords = [*plan.keywords]
    if plan.intent_tier in {"general", "near_me"} and re.search(r"therapy|anxiety|cbt|dbt|ocd|depression", plan.service, re.I):
        keywords.extend(COLLEGE_KEYWORDS)
    for keyword in unique_keyword_list(keywords):
        output.append(
            blank_row(
                fieldnames,
                Campaign=plan.campaign,
                **{
                    "Ad Group": plan.ad_group,
                    "Criterion Type": "Phrase",
                    "Keyword": keyword,
                    "Final URL": plan.final_url,
                    "Status": "Paused",
                    "Keyword status": "Paused",
                },
            )
        )
    rsa = blank_row(
        fieldnames,
        Campaign=plan.campaign,
        **{
            "Ad Group": plan.ad_group,
            "Final URL": plan.final_url,
            "Ad type": "Responsive search ad",
            "Status": "Paused",
            "Ad status": "Paused",
            "Path 1": plan.path_1,
            "Path 2": plan.path_2,
        },
    )
    rewrite_rsa_copy(rsa)
    output.append(rsa)


def service_from_ad_group(ad_group: str) -> str:
    cleaned = re.sub(r"\s+-\s+(General|Near Me|New York|New Jersey|NY|NJ|REV1)\b", "", ad_group, flags=re.IGNORECASE)
    cleaned = cleaned.replace("Therapy - ", "").replace("Services - ", "")
    return cleaned.strip(" -") or "Online Therapy"


def skip_revised_row(row: dict[str, str]) -> bool:
    haystack = " ".join(
        [
            row.get("Campaign", ""),
            row.get("Ad Group", ""),
            row.get("Keyword", ""),
            row.get("Final URL", ""),
            row.get("Path 1", ""),
            row.get("Path 2", ""),
            *[row.get(f"Headline {index}", "") for index in range(1, 16)],
            *[row.get(f"Description {index}", "") for index in range(1, 5)],
        ]
    ).lower()
    return any(term in haystack for term in ["adolescent", "teen", "child", "minor", "group therapy", "therapy group"]) or bool(re.search(r"\bgroup\b", haystack))


def is_location_row(row: dict[str, str]) -> bool:
    return bool(row.get("Location") or row.get("Location ID")) and not any(
        row.get(field) for field in ("Campaign Type", "Ad Group", "Criterion Type", "Ad type", "Keyword")
    )


def first_final_url(rows: list[dict[str, str]], campaign: str, ad_group: str) -> str:
    for row in rows:
        if row.get("Campaign") == campaign and row.get("Ad Group") == ad_group and row.get("Final URL"):
            return row["Final URL"]
    return ""


def first_final_url_for_service(rows: list[dict[str, str]], service: str) -> str:
    lowered = service.lower()
    for row in rows:
        if row.get("Final URL") and lowered in service_from_ad_group(row.get("Ad Group", "")).lower():
            return row["Final URL"]
    for row in rows:
        if row.get("Final URL"):
            return row["Final URL"]
    return ""


def extract_service_urls(rows: list[dict[str, str]]) -> dict[str, str]:
    output: dict[str, str] = {}
    for row in rows:
        if skip_revised_row(row):
            continue
        ad_group = row.get("Ad Group", "")
        if not ad_group:
            continue
        service = service_from_ad_group(ad_group)
        if not service or service.lower() in {item.lower() for item in output}:
            continue
        final_url = row.get("Final URL") or first_final_url(rows, row.get("Campaign", ""), ad_group)
        output[service] = final_url
    return output or {"Online Therapy": first_final_url_for_service(rows, "Online Therapy")}


def source_base_campaign(rows: list[dict[str, str]]) -> str:
    for row in rows:
        campaign = row.get("Campaign", "")
        if row.get("Campaign Type") == "Search" and campaign:
            return campaign
    for row in rows:
        if row.get("Campaign"):
            return row["Campaign"]
    return "ARC - Search - Services - V1"


def source_budget(rows: list[dict[str, str]]) -> str:
    for row in rows:
        if row.get("Budget"):
            return row["Budget"]
    return "50.00"


def path_part(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "", value.title())
    return cleaned[:15] or "Services"


def unique_keyword_list(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        cleaned = re.sub(r"\s+", " ", value).strip()
        if cleaned and cleaned.lower() not in seen:
            output.append(cleaned)
            seen.add(cleaned.lower())
    return output


def blank_row(fieldnames: list[str], **values: str) -> dict[str, str]:
    row = {field: "" for field in fieldnames}
    row.update(values)
    return row


def append_unique(current: list[str], additions: list[str]) -> list[str]:
    seen = {value.lower() for value in current}
    for value in additions:
        if value.lower() not in seen:
            current.append(value)
            seen.add(value.lower())
    return current


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower())
