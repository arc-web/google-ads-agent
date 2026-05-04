#!/usr/bin/env python3
"""Canonical Search-only rebuild pipeline for Google_Ads_Agent."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from shared.copy_engine.search.copy_matrix import (
    CopyCandidate,
    CopyConstraints,
    build_rsa_copy,
    keyword_roots,
    path_part,
    write_copy_candidates,
    write_rsa_copy_matrix,
)
from shared.gads.core.search_campaigns.search_csv_generator import SearchCSVGenerator
from shared.presentation.build_new_campaign_report import BudgetPlan, read_staging, summarize_staging, write_report
from shared.presentation.client_email_draft import EmailDraftInput, write_client_email_draft
from shared.presentation.report_quality_audit import audit_html
from shared.rebuild.csv_naming import generated_csv_path
from shared.rebuild.client_hq import parse_client_hq_docx
from shared.rebuild.geo_taxonomy import build_geo_ad_group_plans, parse_geo_target
from shared.rebuild.department_standards import (
    audit_audience_modes,
    audit_conversion_tracking,
    audit_policy_disapprovals,
    build_bid_strategy_recommendation,
    build_evidence_quality_report,
    build_optimization_cadence_plan,
    load_department_standards,
    triage_recommendations,
    write_json,
    write_launch_readiness_checklist,
    write_recommendations_csv,
)
from shared.rebuild.provider_token_validator import DEFAULT_BLOCKED_FIELDS, token_re, validate_csv
from shared.rebuild.revision_feedback import build_revised_staging_csv, write_revision_artifacts
from shared.rebuild.search_term_review import build_search_term_review, region_name
from shared.rebuild.staging_validator import validate_file
from shared.tools.website.website_scanner import WebsiteScanner


ROOT = Path(__file__).resolve().parents[2]
CLIENTS_DIR = ROOT / "clients"


@dataclass(frozen=True)
class ClientProfile:
    agency_slug: str
    client_slug: str
    display_name: str
    website_url: str
    agency_display_name: str
    campaign_prefix: str
    target_locations: list[str]
    target_services: list[str]
    competitor_terms: list[str]
    monthly_budget: float
    daily_budget: float


@dataclass(frozen=True)
class AdGroupPlan:
    campaign: str
    ad_group: str
    service: str
    final_url: str
    path_1: str
    path_2: str
    keywords: list[str]


def client_dir(agency: str, client: str, clients_dir: Path = CLIENTS_DIR) -> Path:
    return clients_dir / agency / client


def build_dir_for(client_root: Path, build_date: str) -> Path:
    return client_root / "build" / f"{build_date}_account_rebuild"


def load_profile(client_root: Path) -> ClientProfile:
    profile_path = client_root / "config" / "client_profile.yaml"
    if not profile_path.exists():
        raise FileNotFoundError(f"Missing client profile: {profile_path}")
    data = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    client = data.get("client", {})
    agency = data.get("agency", {})
    market = data.get("market", {})
    campaign_defaults = data.get("campaign_defaults", {})
    services = list(data.get("services", []))
    competitor_terms = extract_competitor_terms(data)
    budget = data.get("budget", {})
    monthly_budget = float(budget.get("monthly_budget", 3000.0))
    daily_budget = float(budget.get("daily_budget", campaign_defaults.get("daily_budget", monthly_budget / 30)))
    target_locations = normalize_locations(
        [
            *market.get("target_cities", []),
            *market.get("target_states", []),
            *market.get("target_zip_codes", []),
            *market.get("radius_targets", []),
        ]
    )
    if not target_locations:
        target_locations = ["United States|2840"]
    return ClientProfile(
        agency_slug=str(client.get("agency_slug") or agency.get("short_name") or "agency").lower(),
        client_slug=str(client.get("client_slug") or client_root.name),
        display_name=str(client.get("display_name") or client_root.name.replace("_", " ").title()),
        website_url=str(client.get("website_url") or "https://example.com/"),
        agency_display_name=str(agency.get("display_name") or "Advertising Report Card"),
        campaign_prefix=str(data.get("campaign_naming", {}).get("ownership_prefix") or "ARC"),
        target_locations=target_locations,
        target_services=services,
        competitor_terms=competitor_terms,
        monthly_budget=monthly_budget,
        daily_budget=daily_budget,
    )


def extract_competitor_terms(data: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for section_name in ("competitor_pruning", "competitors"):
        section = data.get(section_name, {})
        if isinstance(section, list):
            terms.extend(str(item) for item in section if item)
        elif isinstance(section, dict):
            for key in ("negative_phrase_terms", "competitor_terms", "brand_terms", "brands", "names"):
                value = section.get(key, [])
                if isinstance(value, list):
                    terms.extend(str(item) for item in value if item)
                elif value:
                    terms.append(str(value))
    return normalize_dedupe_terms(terms)


def normalize_dedupe_terms(values: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = " ".join(str(value).strip().strip('"').strip("'").lower().split())
        if not normalized or normalized in seen:
            continue
        output.append(normalized)
        seen.add(normalized)
    return output


def normalize_locations(values: list[Any]) -> list[str]:
    output: list[str] = []
    for value in values:
        if isinstance(value, dict):
            location = value.get("location") or value.get("name") or value.get("target")
            location_id = value.get("location_id") or value.get("id") or ""
            if location:
                output.append(f"{location}|{location_id}" if location_id else str(location))
        elif value:
            output.append(str(value))
    return output


def read_report_csv(path: Path) -> tuple[list[str], list[dict[str, str]], str]:
    if not path.exists():
        return [], [], "missing"
    for encoding in ("utf-16", "utf-8-sig", "utf-8", "latin-1"):
        try:
            text = path.read_text(encoding=encoding)
            delimiter = detect_delimiter(text)
            reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
            rows = [dict(row) for row in reader]
            headers = list(reader.fieldnames or [])
            if headers:
                return headers, rows, f"{encoding}:{delimiter_name(delimiter)}"
        except UnicodeError:
            continue
    text = path.read_text(encoding="utf-8")
    delimiter = detect_delimiter(text)
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    rows = [dict(row) for row in reader]
    return list(reader.fieldnames or []), rows, f"utf-8:{delimiter_name(delimiter)}"


def detect_delimiter(text: str) -> str:
    sample = "\n".join(line for line in text.splitlines()[:20] if line.strip())
    if not sample:
        return "\t"
    try:
        return csv.Sniffer().sniff(sample, delimiters="\t,").delimiter
    except csv.Error:
        first = sample.splitlines()[0]
        return "\t" if first.count("\t") >= first.count(",") else ","


def delimiter_name(delimiter: str) -> str:
    return "tab" if delimiter == "\t" else "comma"


def snapshot_account(client_root: Path, build_dir: Path) -> dict[str, Any]:
    export = client_root / "campaigns" / "account_export.csv"
    headers, rows, encoding = read_report_csv(export)
    counts = Counter()
    campaigns = sorted({row.get("Campaign", "") for row in rows if row.get("Campaign")})
    provider_tokens = detect_provider_tokens(rows)
    for row in rows:
        if row.get("Campaign Type") == "Search":
            counts["search_campaign_rows"] += 1
        if row.get("Ad Group"):
            counts["ad_group_references"] += 1
        if row.get("Keyword"):
            counts["keyword_rows"] += 1
            counts[f"criterion_type:{row.get('Criterion Type', '')}"] += 1
        if row.get("Ad type") == "Responsive search ad":
            counts["rsa_rows"] += 1
        if row.get("Location"):
            counts["location_rows"] += 1
    snapshot = {
        "source": str(export),
        "encoding": encoding,
        "headers": headers,
        "rows": len(rows),
        "campaigns": campaigns,
        "counts": dict(counts),
        "provider_tokens_detected": provider_tokens,
    }
    (build_dir / "account_snapshot.json").write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    audit = {
        "status": "complete",
        "search_campaigns_detected": counts.get("search_campaign_rows", 0),
        "phrase_keywords_detected": counts.get("criterion_type:Phrase", 0),
        "broad_or_exact_detected": counts.get("criterion_type:Broad", 0) + counts.get("criterion_type:Exact", 0),
        "provider_tokens_detected": provider_tokens,
    }
    (build_dir / "account_audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return snapshot


def detect_provider_tokens(rows: list[dict[str, str]]) -> list[str]:
    known = ["revkey"]
    text = "\n".join(" ".join(str(value) for value in row.values()).lower() for row in rows)
    return [token for token in known if token in text]


def write_source_attribution(profile: ClientProfile, build_dir: Path, snapshot: dict[str, Any], website_paths: dict[str, Path]) -> dict[str, Any]:
    website_source = json.loads(website_paths["source_attribution"].read_text(encoding="utf-8"))
    payload = {
        "agency": profile.agency_display_name,
        "client": profile.display_name,
        "website": profile.website_url,
        "account_export": snapshot.get("source"),
        "previous_provider_tokens": snapshot.get("provider_tokens_detected", []),
        "generated_work_owner": profile.campaign_prefix,
        "website_scan": str(website_paths["website_scan"]),
        "source_pages": website_source.get("source_pages", []),
        "requested_source_pages": website_source.get("requested_source_pages", []),
        "rules": [
            "Previous provider names are source attribution only.",
            "Generated campaign and label ownership uses ARC.",
        ],
    }
    path = build_dir / "source_attribution.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def infer_service_catalog(profile: ClientProfile, constraints: CopyConstraints, website_scan: dict[str, Any]) -> dict[str, Any]:
    services = []
    for source in (
        constraints.services_with_capacity,
        profile.target_services,
        website_scan.get("extracted_facts", {}).get("services", []),
    ):
        for service in source:
            service_text = str(service).strip()
            if service_text and service_text.lower() not in {item.lower() for item in services}:
                services.append(service_text)
    excluded = {service.lower() for service in constraints.services_excluded}
    services = [service for service in services if service.lower() not in excluded]
    if not services:
        services = ["Core Services"]
    return {
        "active_services_for_staging": services[:8],
        "excluded_from_initial_staging": sorted(constraints.services_excluded),
        "source": "client_constraints_profile_website",
        "human_review_needed": [
            "Confirm active services and priority order before launch.",
            "Confirm landing page fit for each ad group.",
        ],
    }


def landing_page_for_service(service: str, profile: ClientProfile, website_scan: dict[str, Any]) -> str:
    service_terms = {term for term in re_split(service.lower()) if len(term) > 2}
    best = profile.website_url
    best_score = 0
    page_evidence = website_scan.get("page_evidence", {})
    for page in website_scan.get("source_pages_scanned", []):
        evidence = page_evidence.get(page, {})
        page_text = " ".join(
            [
                str(page),
                str(evidence.get("title", "")),
                " ".join(evidence.get("headings", [])),
                str(evidence.get("text_sample", "")),
            ]
        ).lower()
        score = sum(1 for term in service_terms if term in page_text)
        if score > best_score:
            best = str(page)
            best_score = score
    return best


def re_split(value: str) -> list[str]:
    import re

    return re.split(r"\W+", value)


def build_geo_strategy(profile: ClientProfile, build_dir: Path) -> dict[str, Any]:
    targets = []
    for location in profile.target_locations:
        name, location_id = parse_location(location)
        targets.append({"location": name, "location_id": location_id, "bid_modifier": ""})
    payload = {
        "targeting": targets,
        "targeting_method": "Location of presence",
        "exclusion_method": "Location of presence",
        "human_review_needed": ["Confirm locations and location IDs in Google Ads Editor before upload."],
    }
    (build_dir / "geo_strategy.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def parse_location(value: str) -> tuple[str, str]:
    if "|" in value:
        location, location_id = value.split("|", 1)
        return location.strip(), location_id.strip()
    return value.strip(), ""


def plan_ad_groups(profile: ClientProfile, service_catalog: dict[str, Any], website_scan: dict[str, Any]) -> list[AdGroupPlan]:
    campaign = f"{profile.campaign_prefix} - Search - Services - V1"
    plans = []
    geo_targets = [parse_geo_target(location) for location in profile.target_locations]
    geo_plans = build_geo_ad_group_plans(
        base_campaign=campaign,
        services=[str(service) for service in service_catalog["active_services_for_staging"]],
        locations=geo_targets,
        final_url_for_service=lambda service: landing_page_for_service(service, profile, website_scan),
        path_part=path_part,
        version_suffix="V1",
        split_by_state=len([target for target in geo_targets if target.kind == "state"]) > 1,
        ad_group_prefix="Services",
    )
    for geo_plan in geo_plans:
        plans.append(
            AdGroupPlan(
                campaign=geo_plan.campaign,
                ad_group=geo_plan.ad_group,
                service=geo_plan.service,
                final_url=geo_plan.final_url,
                path_1=geo_plan.path_1,
                path_2=geo_plan.path_2,
                keywords=geo_plan.keywords or keyword_roots(geo_plan.service)[:6],
            )
        )
    return plans


def landing_page_evidence_for_plan(
    plan: AdGroupPlan,
    profile: ClientProfile,
    website_scan: dict[str, Any],
    constraints: CopyConstraints,
) -> dict[str, Any]:
    page_evidence = website_scan.get("page_evidence", {})
    evidence = dict(page_evidence.get(plan.final_url, {}))
    service_terms = {term.lower() for term in re_split(plan.service) if len(term) > 2}
    evidence_text = " ".join(
        [
            plan.final_url,
            str(evidence.get("title", "")),
            " ".join(evidence.get("headings", [])),
            str(evidence.get("text_sample", "")),
        ]
    ).lower()
    matched_terms = sorted(term for term in service_terms if term in evidence_text)
    status = str(evidence.get("status") or "missing")
    if not matched_terms and plan.final_url == profile.website_url:
        status = "fallback_homepage"
    copy_allowed_claims = [
        *evidence.get("delivery_modes", []),
        *evidence.get("availability_signals", []),
        *evidence.get("landing_page_claims", []),
    ]
    trust_signals = landing_trust_signals(evidence)
    message_match_status = "strong" if matched_terms else "weak"
    return {
        "final_url": plan.final_url,
        "status": status,
        "matched_terms": matched_terms,
        "message_match_status": message_match_status,
        "message_match_terms": matched_terms,
        "fit_score": len(matched_terms),
        "trust_signals": trust_signals,
        "page_speed_review": "manual_review_required",
        "mobile_experience_review": "manual_review_required",
        "value_props_used": evidence.get("landing_page_claims", [])[:4],
        "delivery_modes": evidence.get("delivery_modes", []),
        "availability_signals": evidence.get("availability_signals", []),
        "cta_signals": evidence.get("cta_signals", []),
        "landing_page_claims": evidence.get("landing_page_claims", []),
        "copy_allowed_claims": copy_allowed_claims,
        "human_review_needed": landing_human_review(status, matched_terms, constraints),
    }


def landing_trust_signals(evidence: dict[str, Any]) -> list[str]:
    text = " ".join(
        [
            str(evidence.get("title", "")),
            " ".join(evidence.get("headings", [])),
            str(evidence.get("text_sample", "")),
        ]
    ).lower()
    signals = []
    for label, pattern in (
        ("phone_visible", r"\b(phone|call|tel:|\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4})\b"),
        ("appointment_cta", r"\b(schedule|appointment|book|consultation|contact)\b"),
        ("credential_or_license", r"\b(licensed|certified|credential|years of experience|experienced)\b"),
        ("privacy_or_policy", r"\b(privacy policy|terms|hipaa|confidential)\b"),
        ("local_presence", r"\b(address|office|serving|location|near)\b"),
    ):
        if re.search(pattern, text, re.IGNORECASE):
            signals.append(label)
    return signals


def landing_human_review(status: str, matched_terms: list[str], constraints: CopyConstraints) -> list[str]:
    notes: list[str] = []
    if status in {"missing", "unreadable"}:
        notes.append("Landing page was not readable. Confirm the final URL before launch.")
    if status == "fallback_homepage" and not constraints.landing_page_fallback_allowed:
        notes.append("Service-specific landing page was not confirmed. Homepage fallback needs approval.")
    if not matched_terms:
        notes.append("Landing page did not strongly match the ad group service terms.")
    notes.append("Review mobile experience, page speed, and trust signals before launch.")
    return notes


def validate_landing_page_map(landing_map: dict[str, Any], constraints: CopyConstraints) -> None:
    failures = []
    for ad_group, evidence in landing_map.items():
        status = evidence.get("status")
        if status in {"missing", "unreadable"}:
            failures.append(f"{ad_group}: {status}")
        if status == "fallback_homepage" and not constraints.landing_page_fallback_allowed:
            failures.append(f"{ad_group}: fallback_homepage_unapproved")
    if failures:
        raise RuntimeError(f"Landing page validation failed: {failures}")


def write_strategy_artifacts(build_dir: Path, plans: list[AdGroupPlan], landing_map: dict[str, Any]) -> dict[str, Path]:
    taxonomy = build_dir / "campaign_taxonomy.csv"
    landing = build_dir / "landing_page_map.json"
    keyword_expansion = build_dir / "keyword_expansion_candidates.csv"
    negative_review = build_dir / "negative_review_candidates.csv"
    targeting = build_dir / "targeting_spec.json"

    with taxonomy.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["campaign", "ad_group", "service", "final_url", "keyword_count"])
        writer.writeheader()
        for plan in plans:
            writer.writerow(
                {
                    "campaign": plan.campaign,
                    "ad_group": plan.ad_group,
                    "service": plan.service,
                    "final_url": plan.final_url,
                    "keyword_count": len(plan.keywords),
                }
            )

    landing.write_text(json.dumps(landing_map, indent=2) + "\n", encoding="utf-8")

    with keyword_expansion.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["campaign", "ad_group", "keyword", "source_action"])
        writer.writeheader()
        for plan in plans:
            for keyword in plan.keywords:
                writer.writerow({"campaign": plan.campaign, "ad_group": plan.ad_group, "keyword": keyword, "source_action": "add_phrase"})

    with negative_review.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "keyword",
                "match_type",
                "level",
                "reason",
                "status",
                "source_search_terms",
                "clicks",
                "impressions",
                "conversions",
            ],
        )
        writer.writeheader()

    targeting.write_text(json.dumps({"source": "geo_strategy.json"}, indent=2) + "\n", encoding="utf-8")
    return {
        "campaign_taxonomy": taxonomy,
        "landing_page_map": landing,
        "keyword_expansion_candidates": keyword_expansion,
        "negative_review_candidates": negative_review,
        "targeting_spec": targeting,
    }


def write_search_term_analysis(client_root: Path, build_dir: Path, profile: ClientProfile, plans: list[AdGroupPlan]) -> Path:
    source = client_root / "reports" / "performance_inputs" / "search_terms_report.csv"
    output = build_dir / "search_term_analysis.csv"
    questions = build_dir / "search_term_client_question_groups.csv"
    headers, rows, encoding = read_google_report_with_header_scan(source, required_header="Search term")
    location_source = client_root / "reports" / "performance_inputs" / "location_report.csv"
    _location_headers, location_rows, _location_encoding = read_google_report_with_header_scan(location_source, required_header="Location")
    service_terms = [term for plan in plans for term in [plan.service, *plan.keywords]]
    approved_regions = profile.target_locations
    client_hq = load_client_hq_facts(client_root)
    if client_hq:
        service_terms = [*client_hq.primary_services, *service_terms]
        approved_regions = [*client_hq.service_area_regions, *approved_regions]
    candidate_regions = [region_name(row.get("Location", "")) for row in location_rows if row.get("Location", "")]
    fieldnames = [
        "search_term",
        "impressions",
        "clicks",
        "conversions",
        "category",
        "client_action",
        "internal_action",
        "action_term",
        "negative_match_type",
        "negative_level",
        "matched_service",
        "matched_regions",
        "unknown_regions",
        "reason",
        "source",
        "source_encoding",
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        if not rows:
            writer.writerow(
                {
                    "search_term": "",
                    "category": "missing_source_report",
                    "client_action": "No client question.",
                    "internal_action": "Add a search terms report before optimization review.",
                    "source": str(source),
                    "source_encoding": encoding,
                }
            )
            write_search_term_question_groups(questions, [])
            return output
        review = build_search_term_review(
            rows,
            service_terms=service_terms,
            approved_regions=approved_regions,
            competitor_terms=profile.competitor_terms,
            candidate_regions=candidate_regions,
            telehealth_regions=client_hq.telehealth_regions if client_hq else [],
            virtual_only=client_hq.virtual_only if client_hq else False,
            physical_locations=client_hq.physical_locations if client_hq else [],
        )
        for decision in review.decisions:
            writer.writerow(
                {
                    "search_term": decision.search_term,
                    "impressions": decision.impressions,
                    "clicks": decision.clicks,
                    "conversions": decision.conversions,
                    "category": decision.category,
                    "client_action": decision.client_action,
                    "internal_action": decision.internal_action,
                    "action_term": decision.action_term,
                    "negative_match_type": decision.negative_match_type,
                    "negative_level": decision.negative_level,
                    "matched_service": decision.matched_service,
                    "matched_regions": ";".join(decision.matched_regions),
                    "unknown_regions": ";".join(decision.unknown_regions),
                    "reason": decision.reason,
                    "source": str(source),
                    "source_encoding": encoding,
                }
            )
    write_competitor_negative_candidates(build_dir / "negative_review_candidates.csv", review.decisions if rows else [])
    write_search_term_question_groups(questions, review.question_group_rows() if rows else [])
    return output


def write_competitor_negative_candidates(path: Path, decisions: list[Any]) -> Path:
    fieldnames = [
        "keyword",
        "match_type",
        "level",
        "reason",
        "status",
        "source_search_terms",
        "clicks",
        "impressions",
        "conversions",
    ]
    grouped: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        if getattr(decision, "category", "") != "competitor_negative_candidate" or not getattr(decision, "action_term", ""):
            continue
        item = grouped.setdefault(
            decision.action_term,
            {
                "keyword": decision.action_term,
                "match_type": decision.negative_match_type or "Negative Phrase",
                "level": decision.negative_level or "Campaign",
                "reason": "Known competitor brand object matched search term report.",
                "status": "stage_for_negative_phrase",
                "source_search_terms": [],
                "clicks": 0.0,
                "impressions": 0.0,
                "conversions": 0.0,
            },
        )
        item["source_search_terms"].append(decision.search_term)
        item["clicks"] += decision.clicks
        item["impressions"] += decision.impressions
        item["conversions"] += decision.conversions

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in sorted(grouped.values(), key=lambda row: (-row["clicks"], row["keyword"])):
            writer.writerow({**item, "source_search_terms": "; ".join(sorted(set(item["source_search_terms"])))})
    return path


def load_client_hq_facts(client_root: Path):
    client_hq_dir = client_root / "docs" / "client_hq"
    json_path = client_hq_dir / "client_hq.json"
    if json_path.exists():
        from shared.rebuild.client_hq import ClientHQFacts

        data = json.loads(json_path.read_text(encoding="utf-8"))
        return ClientHQFacts(**data)
    docx_files = sorted(client_hq_dir.glob("*.docx"))
    if docx_files:
        return parse_client_hq_docx(docx_files[0])
    return None


def write_search_term_question_groups(path: Path, rows: list[dict[str, object]]) -> Path:
    fieldnames = ["group_id", "group_type", "title", "question", "terms", "regions", "services", "default_action"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return path


def write_department_operational_artifacts(
    client_root: Path,
    build_dir: Path,
    account_snapshot: dict[str, Any],
    landing_map: dict[str, Any],
) -> dict[str, Path]:
    standards = load_department_standards()
    performance_dir = client_root / "reports" / "performance_inputs"
    conversion_audit = audit_conversion_tracking(performance_dir / "conversion_action_report.csv", standards)
    bid_strategy = build_bid_strategy_recommendation(performance_dir / "conversion_action_report.csv", standards)
    cadence = build_optimization_cadence_plan(standards)
    audience_audit = audit_audience_modes(performance_dir / "audience_report.csv", standards)
    recommendation_summary, recommendation_rows = triage_recommendations(performance_dir / "recommendations_report.csv", standards)
    disapproval_audit = audit_policy_disapprovals(performance_dir / "disapproval_report.csv", standards)
    evidence_quality = build_evidence_quality_report(
        account_snapshot=account_snapshot,
        search_terms_path=build_dir / "search_term_analysis.csv",
        location_report_path=performance_dir / "location_report.csv",
        conversion_audit=conversion_audit,
        landing_map=landing_map,
    )
    paths = {
        "conversion_tracking_audit": write_json(build_dir / "conversion_tracking_audit.json", conversion_audit),
        "evidence_quality_report": write_json(build_dir / "evidence_quality_report.json", evidence_quality),
        "optimization_cadence_plan": write_json(build_dir / "optimization_cadence_plan.json", cadence),
        "bid_strategy_recommendation": write_json(build_dir / "bid_strategy_recommendation.json", bid_strategy),
        "audience_mode_audit": write_json(build_dir / "audience_mode_audit.json", audience_audit),
        "recommendations_triage": write_recommendations_csv(build_dir / "recommendations_triage.csv", recommendation_rows),
        "policy_disapproval_audit": write_json(build_dir / "policy_disapproval_audit.json", disapproval_audit),
        "recommendations_triage_summary": write_json(build_dir / "recommendations_triage_summary.json", recommendation_summary),
    }
    checklist_path = build_dir / "launch_readiness_checklist.md"
    write_launch_readiness_checklist(
        checklist_path,
        {
            "conversion_tracking_audit": conversion_audit,
            "policy_disapproval_audit": disapproval_audit,
            "audience_mode_audit": audience_audit,
        },
    )
    paths["launch_readiness_checklist"] = checklist_path
    return paths


def read_google_report_with_header_scan(path: Path, *, required_header: str) -> tuple[list[str], list[dict[str, str]], str]:
    if not path.exists():
        return [], [], "missing"
    for encoding in ("utf-16", "utf-8-sig", "utf-8", "latin-1"):
        try:
            text = path.read_text(encoding=encoding)
        except UnicodeError:
            continue
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if required_header.lower() not in line.lower():
                continue
            delimiter = detect_delimiter("\n".join(lines[index : index + 20]))
            reader = csv.DictReader(lines[index:], delimiter=delimiter)
            rows = [dict(row) for row in reader]
            headers = list(reader.fieldnames or [])
            if any(header.lower() == required_header.lower() for header in headers):
                return headers, rows, f"{encoding}:{delimiter_name(delimiter)}"
        delimiter = detect_delimiter(text)
        reader = csv.DictReader(lines, delimiter=delimiter)
        rows = [dict(row) for row in reader]
        headers = list(reader.fieldnames or [])
        if any(header.lower() == required_header.lower() for header in headers):
            return headers, rows, f"{encoding}:{delimiter_name(delimiter)}"
    return [], [], "unreadable"


def numeric_value(value: str) -> float:
    try:
        return float(str(value).replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def build_copy(
    profile: ClientProfile,
    constraints: CopyConstraints,
    plans: list[AdGroupPlan],
    build_dir: Path,
    landing_map: dict[str, Any],
) -> tuple[list[CopyCandidate], dict[str, Any]]:
    all_candidates: list[CopyCandidate] = []
    bundles = {}
    for plan in plans:
        bundle = build_rsa_copy(
            campaign=plan.campaign,
            ad_group=plan.ad_group,
            service=plan.service,
            client_name=profile.display_name,
            geo=profile.target_locations,
            keywords=plan.keywords,
            constraints=constraints,
            source_evidence=landing_map.get(plan.ad_group, {}),
        )
        all_candidates.extend(bundle.candidates)
        bundles[plan.ad_group] = {"headlines": bundle.headlines, "descriptions": bundle.descriptions}
    write_copy_candidates(build_dir / "copy_candidates.json", all_candidates)
    write_rsa_copy_matrix(build_dir / "rsa_copy_matrix.csv", [candidate for candidate in all_candidates if candidate.status == "pass"])
    return all_candidates, bundles


def write_staging(profile: ClientProfile, geo_strategy: dict[str, Any], plans: list[AdGroupPlan], bundles: dict[str, Any], build_dir: Path) -> dict[str, Any]:
    generator = SearchCSVGenerator()
    campaigns: list[str] = []
    for plan in plans:
        if plan.campaign not in campaigns:
            campaigns.append(plan.campaign)
    if not campaigns:
        campaigns = [f"{profile.campaign_prefix} - Search - Services - V1"]
    geo_targets = [parse_geo_target(f"{target['location']}|{target.get('location_id', '')}") for target in geo_strategy["targeting"]]
    for campaign in campaigns:
        generator.add_campaign(campaign, profile.daily_budget, status="Paused", eu_political_ads="No")
        matching_state = next((target for target in geo_targets if target.kind == "state" and f" - {target.label} - " in campaign), None)
        if matching_state:
            generator.add_location(campaign, matching_state.location, location_id=matching_state.location_id)
        else:
            for target in geo_strategy["targeting"]:
                generator.add_location(campaign, target["location"], location_id=target.get("location_id", ""), bid_modifier=target.get("bid_modifier", ""))
    for plan in plans:
        generator.add_ad_group(plan.campaign, plan.ad_group)
        for keyword in plan.keywords:
            generator.add_keyword(plan.campaign, plan.ad_group, keyword, final_url=plan.final_url)
        copy = bundles[plan.ad_group]
        generator.add_rsa(
            plan.campaign,
            plan.ad_group,
            plan.final_url,
            headlines=copy["headlines"],
            descriptions=copy["descriptions"],
            path_1=plan.path_1,
            path_2=plan.path_2,
        )
    staging = generated_csv_path(build_dir, profile.client_slug, "google_ads_editor_staging")
    validation = generator.write_and_validate(staging)
    (build_dir / "validation_report.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    if validation["status"] != "pass":
        raise RuntimeError(f"Staging validation failed: {validation['issues']}")
    return validation


def enrich_validation_report(
    build_dir: Path,
    validation: dict[str, Any],
    landing_map: dict[str, Any],
    candidates: list[CopyCandidate],
) -> dict[str, Any]:
    rejected_candidates = [candidate for candidate in candidates if candidate.status != "pass"]
    passed_with_issues = [candidate for candidate in candidates if candidate.status == "pass" and candidate.issues]
    landing_status = {
        ad_group: {
            "status": evidence.get("status", "missing"),
            "fit_score": evidence.get("fit_score", 0),
            "matched_terms": evidence.get("matched_terms", []),
            "human_review_needed": evidence.get("human_review_needed", []),
        }
        for ad_group, evidence in landing_map.items()
    }
    validation["copy_gate"] = {
        "status": "pass" if not passed_with_issues else "fail",
        "passed_assets": len([candidate for candidate in candidates if candidate.status == "pass"]),
        "rejected_internal_candidates": len(rejected_candidates),
        "blocked_rules": sorted({issue for candidate in rejected_candidates for issue in candidate.issues}),
    }
    validation["landing_page_status"] = landing_status
    validation["landing_page_gate"] = {
        "status": "pass",
        "checked_ad_groups": len(landing_status),
    }
    (build_dir / "validation_report.json").write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    if validation["copy_gate"]["status"] != "pass":
        raise RuntimeError(f"Copy gate validation failed: {validation['copy_gate']}")
    return validation


def write_human_review(
    profile: ClientProfile,
    build_dir: Path,
    plans: list[AdGroupPlan],
    validation: dict[str, Any],
    landing_map: dict[str, Any],
) -> Path:
    path = build_dir / "human_review.md"
    lines = [
        "# Search Rebuild Human Review",
        "",
        f"Client: {profile.display_name}",
        f"Website: {profile.website_url}",
        f"Validation status: `{validation['status']}`",
        "",
        "## Build Summary",
        "",
        f"- Ad groups: `{len(plans)}`",
        f"- Phrase keywords: `{sum(len(plan.keywords) for plan in plans)}`",
        "- Network: `Google search` only",
        "- Match type: `Phrase` only",
        "- Rows are paused for Google Ads Editor review.",
        "",
        "## Human Review",
        "",
        "- Confirm services, regions, budget, conversion tracking, and ad copy before upload.",
    ]
    landing_notes = [
        f"- `{ad_group}`: {note}"
        for ad_group, evidence in landing_map.items()
        for note in evidence.get("human_review_needed", [])
    ]
    if landing_notes:
        lines.extend(["", "## Landing Page Review", "", *landing_notes])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def latest_staging_csv(build_dir: Path) -> Path:
    dated = sorted(build_dir.glob("*_google_ads_editor_staging_*.csv"))
    if dated:
        return dated[-1]
    legacy = build_dir / "Google_Ads_Editor_Staging_CURRENT.csv"
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"No staging CSV found in {build_dir}")


def latest_initial_staging_csv(build_dir: Path) -> Path:
    dated = sorted(path for path in build_dir.glob("*_google_ads_editor_staging_*.csv") if "_rev" not in path.stem)
    if dated:
        return dated[-1]
    legacy = build_dir / "Google_Ads_Editor_Staging_CURRENT.csv"
    if legacy.exists():
        return legacy
    return latest_staging_csv(build_dir)


def goal_facts_from_client_root(client_root: Path) -> dict[str, Any] | None:
    path = client_root / "docs" / "client_hq" / "client_hq.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    goal = data.get("revision_facts", {}).get("report_goal") or data.get("growth_goals")
    return goal if isinstance(goal, dict) and goal else None


def build_report(
    profile: ClientProfile,
    client_root: Path,
    build_date: str,
    build_dir: Path,
    geo_strategy_path: Path,
    service_catalog_path: Path,
    source_attribution_path: Path,
) -> dict[str, Any]:
    output_html = build_dir / "Client_Rebuild_Review.html"
    output_pdf = build_dir / "Client_Rebuild_Review.pdf"
    staging_csv = latest_staging_csv(build_dir)
    goal_facts = goal_facts_from_client_root(client_root)
    goal_facts_path = build_dir / "goal_facts.json"
    if goal_facts:
        goal_facts_path.write_text(json.dumps(goal_facts, indent=2) + "\n", encoding="utf-8")
    write_report(
        client=profile.display_name,
        date_label=build_date,
        staging_csv=staging_csv,
        website_scan_json=build_dir / "website_scan.json",
        service_catalog_json=service_catalog_path,
        geo_strategy_json=geo_strategy_path,
        source_attribution_json=source_attribution_path,
        output_html=output_html,
        budget=BudgetPlan(profile.monthly_budget),
        goal_facts=goal_facts,
    )
    findings, summary = audit_html(output_html)
    if [finding for finding in findings if finding.severity == "error"]:
        raise RuntimeError("Generated client report failed static audit.")
    visual_dir = build_dir / "client_review_visual_audit"
    subprocess.run(
        [
            sys.executable,
            "presentations/tools/build_new_campaign_report.py",
            "--client",
            profile.display_name,
            "--date",
            build_date,
            "--staging-csv",
            str(staging_csv),
            "--website-scan-json",
            str(build_dir / "website_scan.json"),
            "--service-catalog-json",
            str(service_catalog_path),
            "--geo-strategy-json",
            str(geo_strategy_path),
            "--source-attribution-json",
            str(source_attribution_path),
            "--monthly-budget",
            str(profile.monthly_budget),
            *(
                ["--goal-facts-json", str(goal_facts_path)]
                if goal_facts
                else []
            ),
            "--output-html",
            str(output_html),
            "--output-pdf",
            str(output_pdf),
            "--visual-audit-dir",
            str(visual_dir),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {"summary": summary, "output_html": str(output_html), "output_pdf": str(output_pdf), "visual_audit_dir": str(visual_dir)}


def write_manifest(build_dir: Path, profile: ClientProfile, build_date: str, artifacts: dict[str, Path | str], validation: dict[str, Any], report_audit: dict[str, Any], state: str) -> Path:
    path = build_dir / "run_manifest.json"
    payload = {
        "workflow": "search_rebuild_account_pipeline",
        "client": profile.display_name,
        "agency": profile.agency_display_name,
        "date_label": build_date,
        "build_dir": str(build_dir),
        "artifacts": {key: str(value) for key, value in artifacts.items()},
        "validation": validation,
        "report_audit": report_audit,
        "launch_state": state,
        "live_upload": False,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def run_ingest(profile: ClientProfile, client_root: Path, build_dir: Path) -> dict[str, Any]:
    build_dir.mkdir(parents=True, exist_ok=True)
    website_paths = WebsiteScanner().write_artifacts(
        start_url=profile.website_url,
        output_dir=build_dir,
        explicit_services=profile.target_services,
        max_pages=12,
    )
    snapshot = snapshot_account(client_root, build_dir)
    source_attribution = write_source_attribution(profile, build_dir, snapshot, website_paths)
    return {"website_paths": website_paths, "snapshot": snapshot, "source_attribution": source_attribution}


def run_plan(profile: ClientProfile, client_root: Path, build_dir: Path) -> tuple[list[AdGroupPlan], dict[str, Any], dict[str, Path]]:
    constraints = CopyConstraints.from_file(client_root / "config" / "client_copy_constraints.json")
    website_scan_path = build_dir / "website_scan.json"
    if not website_scan_path.exists():
        run_ingest(profile, client_root, build_dir)
    website_scan = json.loads(website_scan_path.read_text(encoding="utf-8"))
    service_catalog = infer_service_catalog(profile, constraints, website_scan)
    service_catalog_path = build_dir / "service_catalog.json"
    service_catalog_path.write_text(json.dumps(service_catalog, indent=2) + "\n", encoding="utf-8")
    geo_strategy = build_geo_strategy(profile, build_dir)
    plans = plan_ad_groups(profile, service_catalog, website_scan)
    landing_map = {
        plan.ad_group: {
            "path_1": plan.path_1,
            "path_2": plan.path_2,
            **landing_page_evidence_for_plan(plan, profile, website_scan, constraints),
        }
        for plan in plans
    }
    validate_landing_page_map(landing_map, constraints)
    paths = write_strategy_artifacts(build_dir, plans, landing_map)
    search_term_analysis = write_search_term_analysis(client_root, build_dir, profile, plans)
    snapshot_path = build_dir / "account_snapshot.json"
    account_snapshot = json.loads(snapshot_path.read_text(encoding="utf-8")) if snapshot_path.exists() else {}
    operational_paths = write_department_operational_artifacts(client_root, build_dir, account_snapshot, landing_map)
    return plans, geo_strategy, {
        **paths,
        **operational_paths,
        "service_catalog": service_catalog_path,
        "geo_strategy": build_dir / "geo_strategy.json",
        "search_term_analysis": search_term_analysis,
        "search_term_client_question_groups": build_dir / "search_term_client_question_groups.csv",
    }


def run_build(profile: ClientProfile, client_root: Path, build_dir: Path, build_date: str) -> dict[str, Path | str]:
    ingest = run_ingest(profile, client_root, build_dir)
    plans, geo_strategy, strategy_paths = run_plan(profile, client_root, build_dir)
    constraints = CopyConstraints.from_file(client_root / "config" / "client_copy_constraints.json")
    landing_map = json.loads(Path(strategy_paths["landing_page_map"]).read_text(encoding="utf-8"))
    candidates, bundles = build_copy(profile, constraints, plans, build_dir, landing_map)
    validation = write_staging(profile, geo_strategy, plans, bundles, build_dir)
    staging_csv = Path(validation["source_csv"])
    validation = enrich_validation_report(build_dir, validation, landing_map, candidates)
    human_review = write_human_review(profile, build_dir, plans, validation, landing_map)
    source_attribution_path = build_dir / "source_attribution.json"
    report = build_report(profile, client_root, build_date, build_dir, strategy_paths["geo_strategy"], strategy_paths["service_catalog"], source_attribution_path)

    tokens = ingest["snapshot"].get("provider_tokens_detected", [])
    if tokens:
        findings = validate_csv(staging_csv, token_re(tokens), DEFAULT_BLOCKED_FIELDS)
        if findings:
            raise RuntimeError(f"Previous provider token leaked into generated staging CSV: {findings}")

    artifacts: dict[str, Path | str] = {
        "account_snapshot": build_dir / "account_snapshot.json",
        "account_audit": build_dir / "account_audit.json",
        "source_attribution": source_attribution_path,
        "website_scan": build_dir / "website_scan.json",
        "service_catalog": strategy_paths["service_catalog"],
        "landing_page_map": strategy_paths["landing_page_map"],
        "geo_strategy": strategy_paths["geo_strategy"],
        "search_term_analysis": strategy_paths["search_term_analysis"],
        "search_term_client_question_groups": strategy_paths["search_term_client_question_groups"],
        "campaign_taxonomy": strategy_paths["campaign_taxonomy"],
        "keyword_expansion_candidates": strategy_paths["keyword_expansion_candidates"],
        "negative_review_candidates": strategy_paths["negative_review_candidates"],
        "copy_candidates": build_dir / "copy_candidates.json",
        "rsa_copy_matrix": build_dir / "rsa_copy_matrix.csv",
        "targeting_spec": strategy_paths["targeting_spec"],
        "conversion_tracking_audit": strategy_paths["conversion_tracking_audit"],
        "evidence_quality_report": strategy_paths["evidence_quality_report"],
        "optimization_cadence_plan": strategy_paths["optimization_cadence_plan"],
        "bid_strategy_recommendation": strategy_paths["bid_strategy_recommendation"],
        "audience_mode_audit": strategy_paths["audience_mode_audit"],
        "recommendations_triage": strategy_paths["recommendations_triage"],
        "recommendations_triage_summary": strategy_paths["recommendations_triage_summary"],
        "policy_disapproval_audit": strategy_paths["policy_disapproval_audit"],
        "launch_readiness_checklist": strategy_paths["launch_readiness_checklist"],
        "human_review": human_review,
        "staging_csv": staging_csv,
        "validation_report": build_dir / "validation_report.json",
        "client_report_html": report["output_html"],
        "client_report_pdf": report["output_pdf"],
        "visual_audit_dir": report["visual_audit_dir"],
    }
    manifest = write_manifest(
        build_dir,
        profile,
        build_date,
        artifacts,
        validate_file(staging_csv),
        report["summary"],
        "staged_for_google_ads_editor_review",
    )
    artifacts["run_manifest"] = manifest
    return artifacts


def run_revise(profile: ClientProfile, client_root: Path, build_dir: Path) -> dict[str, Path | str]:
    feedback_path = client_root / "docs" / "client_revision_feedback.md"
    classified_path = build_dir / "client_feedback_classified.json"
    decision_log = build_dir / "revision_decision_log.csv"
    if feedback_path.exists():
        artifacts = write_revision_artifacts(
            feedback_text=feedback_path.read_text(encoding="utf-8"),
            client_root=client_root,
            build_dir=build_dir,
            source=str(feedback_path),
        )
        classified_path = Path(artifacts["client_feedback_classified"])
        decision_log = Path(artifacts["revision_decision_log"])
        classified = json.loads(classified_path.read_text(encoding="utf-8"))
    else:
        classified = {
            "approved_for_rebuild": False,
            "feedback_source": str(feedback_path),
            "status": "pending_classification",
            "notes": ["Add client revision feedback before rebuilding revised campaign output."],
        }
        classified_path.write_text(json.dumps(classified, indent=2) + "\n", encoding="utf-8")
        with decision_log.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["decision", "status", "source"])
            writer.writeheader()
            writer.writerow({"decision": "revision_rebuild", "status": "pending_approval", "source": str(classified_path)})
    approved = bool(classified.get("approved_for_rebuild"))
    if not approved:
        return {"client_feedback_classified": classified_path, "revision_decision_log": decision_log}
    source_csv = latest_initial_staging_csv(build_dir)
    rev1, validation = build_revised_staging_csv(
        source_csv=source_csv,
        output_dir=build_dir,
        client_slug=profile.client_slug,
        classified=classified,
    )
    if validation["status"] != "pass":
        raise RuntimeError(f"Revision staging validation failed: {validation['issues']}")
    service_catalog = build_dir / "service_catalog.json"
    geo_strategy = build_dir / "geo_strategy.json"
    source_attribution = build_dir / "source_attribution.json"
    report: dict[str, Any] = {}
    if service_catalog.exists() and geo_strategy.exists() and source_attribution.exists():
        report = build_report(profile, client_root, "Revision 1", build_dir, geo_strategy, service_catalog, source_attribution)
        email_path = build_dir / "client_email_draft.md"
        feedback_items = list(classified.get("items", []))
        client_notes = [
            str(item.get("report_effect"))
            for item in feedback_items
            if item.get("report_effect")
        ]
        if classified.get("report_goal", {}).get("pacing_recommendation"):
            client_notes.append(str(classified["report_goal"]["pacing_recommendation"]))
        if not client_notes:
            client_notes = ["The revised campaign build reflects the approved client feedback classification."]

        confirmation_items = [
            str(item.get("campaign_effect"))
            for item in feedback_items
            if item.get("launch_blocker") and item.get("campaign_effect")
        ]
        for item in feedback_items:
            confirmation_items.extend(str(entry) for entry in item.get("human_review_required", []))
        if not confirmation_items:
            confirmation_items = ["The revised staged campaign build is approved for launch review."]

        write_client_email_draft(
            email_path,
            EmailDraftInput(
                client=profile.display_name,
                date_label="Revision 1",
                report_type="revised campaign build",
                pdf_path=Path(report["output_pdf"]),
                summary=summarize_staging(read_staging(rev1)),
                client_notes=client_notes,
                confirmation_items=confirmation_items,
                next_step="Please review the attached PDF and confirm the revised campaign decisions before launch.",
            ),
        )
    human_review = build_dir / "human_review.md"
    if human_review.exists():
        with human_review.open("a", encoding="utf-8") as handle:
            handle.write("\n## Revision Feedback Review\n\n")
            for item in classified.get("items", []):
                if item.get("human_review_required"):
                    for note in item["human_review_required"]:
                        handle.write(f"- {note}\n")
                elif item.get("campaign_effect"):
                    handle.write(f"- {item['campaign_effect']}\n")
    return {
        "client_feedback_classified": classified_path,
        "revision_decision_log": decision_log,
        "revision_csv": rev1,
        "revision_validation": build_dir / f"{rev1.stem}_validation.json",
        **({"client_report_html": report["output_html"], "client_report_pdf": report["output_pdf"], "client_email_draft": build_dir / "client_email_draft.md"} if report else {}),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the canonical Search-only Google Ads account rebuild pipeline.")
    parser.add_argument("--agency", required=True)
    parser.add_argument("--client", required=True)
    parser.add_argument("--build-date", default=date.today().isoformat())
    parser.add_argument("--mode", choices=["ingest", "plan", "build", "revise"], required=True)
    parser.add_argument("--build-dir", type=Path, help="Optional explicit build directory for existing packages.")
    parser.add_argument("--clients-dir", type=Path, default=CLIENTS_DIR)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    root = client_dir(args.agency, args.client, args.clients_dir)
    if not root.exists():
        raise FileNotFoundError(f"Client directory does not exist: {root}")
    profile = load_profile(root)
    build_root = args.build_dir or build_dir_for(root, args.build_date)

    if args.mode == "ingest":
        result = run_ingest(profile, root, build_root)
        output = {key: str(value) for key, value in result["website_paths"].items()}
        output["account_snapshot"] = str(build_root / "account_snapshot.json")
        output["source_attribution"] = str(build_root / "source_attribution.json")
    elif args.mode == "plan":
        plans, _geo_strategy, paths = run_plan(profile, root, build_root)
        output = {key: str(value) for key, value in paths.items()}
        output["planned_ad_groups"] = str(len(plans))
    elif args.mode == "build":
        output = {key: str(value) for key, value in run_build(profile, root, build_root, args.build_date).items()}
    else:
        output = {key: str(value) for key, value in run_revise(profile, root, build_root).items()}

    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
