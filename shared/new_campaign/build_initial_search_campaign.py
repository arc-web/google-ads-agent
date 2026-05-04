#!/usr/bin/env python3
"""One-shot initial Search campaign builder for new clients."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.gads.core.search_campaigns.search_asset_generator import SearchAssetGenerator, SearchAssetPlan, write_asset_artifacts
from shared.gads.core.search_campaigns.search_csv_generator import SearchCSVGenerator
from shared.presentation.build_new_campaign_report import BudgetPlan, write_report
from shared.presentation.build_new_campaign_report import read_staging, summarize_staging
from shared.presentation.client_email_draft import EmailDraftInput, write_client_email_draft
from shared.presentation.report_contract import QualityGateResult, ReportType, build_report_contract
from shared.presentation.report_quality_audit import audit_html
from shared.rebuild.csv_naming import generated_csv_path, normalize_timestamp, validate_generated_csv_name
from shared.rebuild.geo_taxonomy import build_geo_ad_group_plans, parse_geo_target
from shared.rebuild.rsa_headline_quality import audit_ad_group_plans, generate_quality_headlines
from shared.rebuild.scaffold_client import scaffold_client, slug
from shared.rebuild.service_logic_research import build_service_logic_research, service_logic_by_name, write_service_logic_research
from shared.rebuild.staging_validator import validate_file
from shared.tools.website.website_scanner import WebsiteScanner


@dataclass
class LocationTarget:
    location: str
    location_id: str = ""


@dataclass
class AdGroupPlan:
    campaign: str
    name: str
    service: str
    final_url: str
    path_1: str
    path_2: str
    keywords: list[str]
    headlines: list[str]
    descriptions: list[str]
    service_logic: dict[str, Any]


def clean_words(value: str) -> str:
    value = re.sub(r"(?i)\b([a-z]+)['’]s\b", r"\1", value)
    return re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9 &/-]+", " ", value)).strip()


def path_part(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "", value.title())
    return cleaned[:15] or "Services"


def fit_description(value: str) -> str:
    text = clean_words(value)
    if len(text) <= 90:
        return text
    trimmed = text[:90].rstrip(" ,;")
    if " " in trimmed:
        trimmed = trimmed.rsplit(" ", 1)[0].rstrip(" ,;")
    return trimmed


def description_with_cta(value: str, cta: str) -> str:
    base = clean_words(value).rstrip(".")
    joined = f"{base}. {cta}."
    if len(joined) <= 90:
        return joined
    remaining = 90 - len(f". {cta}.")
    trimmed = base[:remaining].rstrip(" ,;")
    if " " in trimmed:
        trimmed = trimmed.rsplit(" ", 1)[0].rstrip(" ,;")
    return f"{trimmed}. {cta}."


def unique(values: list[str], limit: int) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        cleaned = clean_words(value)
        if cleaned and cleaned.lower() not in seen:
            output.append(cleaned)
            seen.add(cleaned.lower())
        if len(output) >= limit:
            break
    return output


def description_list(values: list[str]) -> list[str]:
    return [description_with_cta(value, "Call Today") for value in values]


def description_set(service: str, service_logic: dict[str, Any] | None = None) -> list[str]:
    if service_logic:
        service_lower = service.lower()
        concept_text = " ".join(str(token) for token in service_logic.get("concept_tokens", [])).lower()
        if "restaurant" in concept_text or any(
            term in service_lower
            for term in ("chef", "dining", "dinner", "food", "menu", "pairing", "reservation", "restaurant", "tasting", "wine")
        ):
            return description_list([
                "Guests can reserve a private tasting menu with contemporary Guatemalan dining",
                "Guests can review restaurant reservation availability for Guatemalan dining",
                "Book an experienced restaurant team for contemporary Guatemalan dining",
                "Guests can schedule a clear tasting menu reservation in Guatemala City",
            ])
        if "lay counselor" in service_lower:
            return description_list([
                "Help organizations train staff in lay counseling skills and expand care access",
                "Build lay counselor teams so organizations can expand mental health access now",
                "Train care teams in counseling skills that support broader mental health access",
                "Review academy fit for staff training, care capacity, and counseling access",
            ])
        if "employee mental health" in service_lower:
            return description_list([
                "Help employers improve employee mental health support and counseling access",
                "Review employee mental health support for wellbeing, access, and workplace fit",
                "Plan employee counseling access that helps employers support staff wellbeing",
                "Compare employee mental health options for workplace support and care access",
            ])
        if "integrated behavioral" in service_lower:
            return description_list([
                "Help organizations use integrated behavioral health consulting for coordinated care",
                "Review integrated behavioral health consulting for clinical teams and care workflows",
                "Plan behavioral health workflows that help care teams coordinate patient support",
                "Compare integrated care consulting options for clinical teams and health workflows",
            ])
        if "empathic communication" in service_lower:
            return description_list([
                "Help organizations use empathic communication training for stronger care teams",
                "Review empathic communication training for organizations and care conversations",
                "Plan empathic communication training that helps teams handle support conversations",
                "Compare empathic communication training options for organizations and care skills",
            ])
        if "clinical support" in service_lower:
            return description_list([
                "Help clinical teams use clinical support consulting for clearer care practices",
                "Review clinical support consulting for healthcare teams, workflow, and care fit",
                "Plan clinical support around care delivery, team workflows, and patient support",
                "Compare clinical consulting options for care teams and practical support needs",
            ])
        if "learning and development" in service_lower:
            return description_list([
                "Help organizations use learning and development programs for stronger staff skills",
                "Review learning programs for staff development, team skills, and support practices",
                "Plan staff development programs that strengthen training paths for care teams",
                "Compare learning and development options for organizations and stronger team skills",
            ])
        if "human-centered" in service_lower or "human centered" in service_lower:
            return description_list([
                "Help healthcare organizations use human-centered care consulting for better care",
                "Review human-centered care consulting for healthcare organizations and care models",
                "Plan human-centered care delivery that helps organizations stay focused on people",
                "Compare human-centered care consulting options for healthcare organizations and care",
            ])
        if "trauma-informed" in service_lower or "trauma informed" in service_lower:
            return description_list([
                "Help organizations use trauma-informed care training for safer support teams",
                "Review trauma-informed training for staff skills, care teams, and support safety",
                "Plan trauma-informed care training that helps teams support people more safely",
                "Compare trauma-informed care training options for organizations and safer care teams",
            ])
        if service_logic.get("buyer_type") == "b2c":
            mechanism = clean_words(str(service_logic.get("service_mechanism", f"{service} support"))).lower()
            return description_list([
                f"Help customers use {mechanism} to compare clearer service options and next steps",
                f"Review {mechanism} for customers, clearer service options, and next steps",
                f"Plan {mechanism} around customer needs, clearer options, and next steps",
                f"Compare {mechanism} choices for customers and clearer service next steps",
            ])
        buyer = "organizations"
        if "clinical" in service_lower:
            buyer = "clinical teams"
        elif "human-centered" in service_lower or "human centered" in service_lower:
            buyer = "healthcare organizations"
        mechanism = clean_words(str(service_logic.get("service_mechanism", ""))).lower()
        outcome = clean_words(str(service_logic.get("outcome", ""))).lower()
        return description_list([
            f"Help {buyer} use {mechanism} to support {outcome}",
            f"Review {mechanism} for {buyer} and confirm fit, timing, scope, and budget",
            f"Plan {mechanism} so {buyer} can move toward {outcome}",
            f"Compare {mechanism} options for {buyer} focused on {outcome}",
        ])
    return description_list([
        "Request details to confirm service fit, audience needs, timing, and budget before launch",
        "Schedule today to review training and consulting options with a practical support team",
        "Request details on scope, stakeholders, implementation needs, and launch readiness",
        "Schedule today to compare support options before campaign approval and account import",
    ])


def parse_location(value: str) -> LocationTarget:
    if "|" in value:
        location, location_id = value.split("|", 1)
        return LocationTarget(location.strip(), location_id.strip())
    return LocationTarget(value.strip(), "")


def infer_service_catalog(website_scan: dict[str, Any], explicit_services: list[str]) -> dict[str, Any]:
    facts = website_scan.get("extracted_facts", {})
    services = unique([*explicit_services, *facts.get("services", [])], 8)
    if not services:
        services = ["Core Services"]
    return {
        "active_services_for_staging": services,
        "excluded_from_initial_staging": [],
        "fact_review": website_scan.get("fact_review", {}),
    }


def build_geo_strategy(locations: list[LocationTarget]) -> dict[str, Any]:
    return {
        "targeting": [asdict(location) for location in locations],
        "targeting_method": "Location of presence",
        "human_review_needed": ["Confirm each location and location ID before Google Ads Editor import."],
    }


def landing_page_for_service(service: str, source_pages: list[str], website: str) -> str:
    service_terms = set(re.split(r"\W+", service.lower()))
    best = website
    best_score = 0
    for page in source_pages:
        lowered = page.lower()
        score = sum(1 for term in service_terms if term and term in lowered)
        if score > best_score:
            best = page
            best_score = score
    return best


def plan_ad_groups(
    *,
    client: str,
    campaign: str,
    website: str,
    service_catalog: dict[str, Any],
    service_logic_map: dict[str, dict[str, Any]] | None = None,
    source_pages: list[str],
    locations: list[LocationTarget] | None = None,
) -> list[AdGroupPlan]:
    plans: list[AdGroupPlan] = []
    services = [str(service) for service in service_catalog.get("active_services_for_staging", [])[:8]]
    geo_locations = [parse_geo_target(location.location, location.location_id) for location in locations or []]
    geo_plans = build_geo_ad_group_plans(
        base_campaign=campaign,
        services=services,
        locations=geo_locations,
        final_url_for_service=lambda service: landing_page_for_service(service, source_pages, website),
        path_part=path_part,
        version_suffix="V1",
        split_by_state=len([target for target in geo_locations if target.kind == "state"]) > 1,
        ad_group_prefix="Services",
    )
    for geo_plan in geo_plans:
        service_logic = (service_logic_map or {}).get(geo_plan.service)
        if not service_logic or service_logic.get("status") != "pass":
            raise RuntimeError(f"Service logic research failed for {geo_plan.service}.")
        plans.append(
            AdGroupPlan(
                campaign=geo_plan.campaign,
                name=geo_plan.ad_group,
                service=geo_plan.service,
                final_url=geo_plan.final_url,
                path_1=geo_plan.path_1,
                path_2=geo_plan.path_2,
                keywords=geo_plan.keywords,
                headlines=generate_quality_headlines(
                    client_name=client,
                    service_label=geo_plan.service,
                    ad_group=geo_plan.ad_group,
                    service_logic=service_logic,
                ),
                descriptions=description_set(geo_plan.service, service_logic),
                service_logic=service_logic,
            )
        )
    return plans


def write_csv_artifacts(build_dir: Path, campaign: str, ad_groups: list[AdGroupPlan]) -> dict[str, Path]:
    taxonomy_path = build_dir / "campaign_taxonomy.csv"
    copy_path = build_dir / "rsa_copy_matrix.csv"
    landing_path = build_dir / "landing_page_map.json"

    with taxonomy_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["campaign", "ad_group", "final_url", "keyword_count"])
        writer.writeheader()
        for ad_group in ad_groups:
            writer.writerow(
                {
                    "campaign": ad_group.campaign,
                    "ad_group": ad_group.name,
                    "final_url": ad_group.final_url,
                    "keyword_count": len(ad_group.keywords),
                }
            )

    with copy_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["campaign", "ad_group", "asset_type", "slot", "text", "chars"])
        writer.writeheader()
        for ad_group in ad_groups:
            for slot, headline in enumerate(ad_group.headlines, start=1):
                writer.writerow(
                    {
                        "campaign": ad_group.campaign,
                        "ad_group": ad_group.name,
                        "asset_type": "headline",
                        "slot": slot,
                        "text": headline,
                        "chars": len(headline),
                    }
                )
            for slot, description in enumerate(ad_group.descriptions, start=1):
                writer.writerow(
                    {
                        "campaign": ad_group.campaign,
                        "ad_group": ad_group.name,
                        "asset_type": "description",
                        "slot": slot,
                        "text": description,
                        "chars": len(description),
                    }
                )

    landing_path.write_text(
        json.dumps(
            {
                ad_group.name: {
                    "final_url": ad_group.final_url,
                    "path_1": ad_group.path_1,
                    "path_2": ad_group.path_2,
                }
                for ad_group in ad_groups
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"campaign_taxonomy": taxonomy_path, "rsa_copy_matrix": copy_path, "landing_page_map": landing_path}


def write_human_review(
    *,
    path: Path,
    campaign: str,
    ad_groups: list[AdGroupPlan],
    validation: dict[str, Any],
    website: str,
    asset_plan: SearchAssetPlan | None = None,
) -> None:
    keyword_count = sum(len(ad_group.keywords) for ad_group in ad_groups)
    asset_counts = asset_plan.counts() if asset_plan else {}
    lines = [
        "# Initial Search Build Human Review",
        "",
        f"Website: {website}",
        f"Campaign: `{campaign}`",
        f"Validation status: `{validation['status']}`",
        "",
        "## Build Summary",
        "",
        f"- Ad groups: `{len(ad_groups)}`",
        f"- Phrase keywords: `{keyword_count}`",
        f"- Sitelink assets: `{asset_counts.get('sitelinks', 0)}`",
        f"- Callout assets: `{asset_counts.get('callouts', 0)}`",
        f"- Structured snippet assets: `{asset_counts.get('structured_snippets', 0)}`",
        f"- Call assets: `{asset_counts.get('calls', 0)}`",
        f"- Price asset items: `{asset_counts.get('prices', 0)}`",
        f"- Promotion assets: `{asset_counts.get('promotions', 0)}`",
        f"- Business name assets: `{asset_counts.get('business_names', 0)}`",
        f"- Image/logo candidates: `{asset_counts.get('candidate_assets', 0)}`",
        "- Network: `Google search` only",
        "- Match type: `Phrase` only",
        "- API upload: off",
        "- Rows are paused for Google Ads Editor review.",
        "",
        "## Staged Asset Review",
        "",
        "- Sitelinks are staged at ad group level only when landing pages are not the homepage and enough distinct URLs exist.",
        "- Campaign-level callouts and structured snippets are staged only as reviewable assets.",
        "- Price and promotion assets are staged only when explicit website evidence exists.",
        "- Image and logo assets are packaged for manual Editor review only after local manifest checks.",
        "- Location assets require Google Business Profile linking confirmation before launch.",
        "",
    ]
    if asset_plan:
        for decision in asset_plan.eligibility:
            status = "qualified" if decision.qualified else "skipped"
            target = decision.ad_group or campaign
            lines.append(f"- `{decision.asset_type}` for `{target}`: {status} `{decision.reason}`")
        lines.append("")
    lines.extend(
        [
        "## Human Review Before Launch",
        "",
        "- Confirm services and priority order.",
        "- Confirm location targeting and location IDs.",
        "- Confirm budget, conversion tracking, and final URL readiness.",
        "- Confirm staged assets, asset level, and platform warnings before upload.",
        "- Confirm business name and logo approval requirements before launch.",
        "- Import into Google Ads Editor and inspect platform warnings before upload.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_manifest(
    *,
    path: Path,
    client: str,
    date_label: str,
    build_dir: Path,
    artifacts: dict[str, Path],
    validation: dict[str, Any],
    report_audit: dict[str, Any],
    report_contract: dict[str, Any] | None = None,
) -> None:
    payload = {
        "workflow": "new_client_initial_search_campaign",
        "client": client,
        "date_label": date_label,
        "build_dir": str(build_dir),
        "artifacts": {key: str(value) for key, value in artifacts.items()},
        "validation": validation,
        "report_audit": report_audit,
        "launch_state": "staged_for_google_ads_editor_review",
        "live_upload": False,
    }
    if report_contract:
        payload.update(report_contract)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def ensure_client_dir(agency: str, client: str, display_name: str, website: str, clients_dir: Path) -> Path:
    target = clients_dir / slug(agency) / slug(client)
    if target.exists():
        return target
    return scaffold_client(agency, client, display_name, website, clients_dir=clients_dir)


def build_initial_campaign(args: argparse.Namespace) -> dict[str, Path]:
    run_date = args.build_date or date.today().isoformat()
    parsed_date = date.fromisoformat(run_date)
    date_label = args.date_label or f"{parsed_date.strftime('%B')} {parsed_date.day}, {parsed_date.year}"
    csv_timestamp = normalize_timestamp(args.csv_timestamp)
    client_dir = ensure_client_dir(args.agency, args.client, args.display_name, args.website, args.clients_dir)
    build_dir = args.build_dir or client_dir / "build" / f"{run_date}_initial_search_build"
    build_dir.mkdir(parents=True, exist_ok=True)

    scanner_paths = WebsiteScanner().write_artifacts(
        start_url=args.website,
        output_dir=build_dir,
        source_pages=args.source_page,
        explicit_services=args.service,
        max_pages=args.max_pages,
    )
    website_scan = json.loads(scanner_paths["website_scan"].read_text(encoding="utf-8"))
    source_attribution = json.loads(scanner_paths["source_attribution"].read_text(encoding="utf-8"))
    service_catalog = infer_service_catalog(website_scan, args.service)
    service_catalog_path = build_dir / "service_catalog.json"
    service_catalog_path.write_text(json.dumps(service_catalog, indent=2) + "\n", encoding="utf-8")
    service_logic = build_service_logic_research(
        services=[str(service) for service in service_catalog.get("active_services_for_staging", [])],
        website_scan=website_scan,
        source_attribution=source_attribution,
    )
    service_logic_path = build_dir / "service_logic_research.json"
    write_service_logic_research(service_logic_path, service_logic)
    if service_logic["status"] != "pass":
        failing = [record["service"] for record in service_logic.get("services", []) if record.get("status") != "pass"]
        raise RuntimeError(f"Service logic research failed for: {', '.join(failing)}")
    service_logic_map = service_logic_by_name(service_logic)

    locations = [parse_location(value) for value in args.location]
    geo_strategy = build_geo_strategy(locations)
    geo_strategy_path = build_dir / "geo_strategy.json"
    geo_strategy_path.write_text(json.dumps(geo_strategy, indent=2) + "\n", encoding="utf-8")

    campaign = args.campaign_name or f"ARC - Search - {service_catalog['active_services_for_staging'][0][:34]} - V1"
    source_pages = [page.get("url", "") for page in source_attribution.get("source_pages", [])]
    ad_groups = plan_ad_groups(
        client=args.display_name,
        campaign=campaign,
        website=args.website,
        service_catalog=service_catalog,
        service_logic_map=service_logic_map,
        source_pages=source_pages,
        locations=locations,
    )
    planned_campaigns = []
    for ad_group in ad_groups:
        if ad_group.campaign not in planned_campaigns:
            planned_campaigns.append(ad_group.campaign)
    if len(planned_campaigns) > 1:
        asset_plan = SearchAssetPlan()
    else:
        asset_plan = SearchAssetGenerator().generate(
            campaign=campaign,
            ad_groups=ad_groups,
            service_catalog=service_catalog,
            source_pages=source_pages,
            website=args.website,
            website_scan=website_scan,
        )
    headline_audit = audit_ad_group_plans(ad_groups, client_name=args.display_name)
    headline_audit_path = build_dir / "rsa_headline_quality_audit.json"
    headline_audit_path.write_text(json.dumps(headline_audit, indent=2) + "\n", encoding="utf-8")
    if headline_audit["status"] != "pass":
        raise RuntimeError(f"RSA headline quality audit failed: {headline_audit_path}")

    generator = SearchCSVGenerator()
    campaigns = planned_campaigns
    geo_targets = [parse_geo_target(location.location, location.location_id) for location in locations]
    for planned_campaign in campaigns:
        generator.add_campaign(planned_campaign, args.daily_budget)
        matching_state = next((target for target in geo_targets if target.kind == "state" and f" - {target.label} - " in planned_campaign), None)
        if matching_state:
            generator.add_location(planned_campaign, matching_state.location, location_id=matching_state.location_id)
        else:
            for location in locations:
                generator.add_location(planned_campaign, location.location, location_id=location.location_id)
    for ad_group in ad_groups:
        generator.add_ad_group(ad_group.campaign, ad_group.name)
        for keyword in ad_group.keywords:
            generator.add_keyword(ad_group.campaign, ad_group.name, keyword, final_url=ad_group.final_url)
        generator.add_rsa(
            ad_group.campaign,
            ad_group.name,
            ad_group.final_url,
            headlines=ad_group.headlines,
            descriptions=ad_group.descriptions,
            path_1=ad_group.path_1,
            path_2=ad_group.path_2,
        )
    for negative in args.negative:
        for planned_campaign in campaigns:
            generator.add_negative_phrase(planned_campaign, negative)
    for sitelink in asset_plan.sitelinks:
        generator.add_sitelink(
            sitelink.campaign,
            sitelink.link_text,
            sitelink.final_url,
            ad_group=sitelink.ad_group,
            description_1=sitelink.description_1,
            description_2=sitelink.description_2,
            level=sitelink.level,
            status=sitelink.status,
        )
    for callout in asset_plan.callouts:
        generator.add_callout(
            callout.campaign,
            callout.callout_text,
            ad_group=callout.ad_group,
            level=callout.level,
            status=callout.status,
        )
    for snippet in asset_plan.structured_snippets:
        generator.add_structured_snippet(
            snippet.campaign,
            snippet.header,
            snippet.values,
            ad_group=snippet.ad_group,
            level=snippet.level,
            status=snippet.status,
        )
    for call in asset_plan.calls:
        generator.add_call(
            call.campaign,
            call.phone_number,
            country_code=call.country_code,
            ad_group=call.ad_group,
            level=call.level,
            status=call.status,
        )
    for price in asset_plan.prices:
        generator.add_price(
            price.campaign,
            price.header,
            price.description,
            price.price,
            price.final_url,
            currency=price.currency,
            price_type=price.price_type,
            price_qualifier=price.price_qualifier,
            unit=price.unit,
            ad_group=price.ad_group,
            level=price.level,
            status=price.status,
        )
    for promotion in asset_plan.promotions:
        generator.add_promotion(
            promotion.campaign,
            promotion.promotion_target,
            promotion.final_url,
            percent_off=promotion.percent_off,
            money_amount_off=promotion.money_amount_off,
            promotion_code=promotion.promotion_code,
            ad_group=promotion.ad_group,
            level=promotion.level,
            status=promotion.status,
        )
    for business_name in asset_plan.business_names:
        generator.add_business_name(
            business_name.campaign,
            business_name.business_name,
            ad_group=business_name.ad_group,
            level=business_name.level,
            status=business_name.status,
        )

    staging_csv = generated_csv_path(
        build_dir,
        args.client,
        args.csv_purpose,
        csv_timestamp,
    )
    validate_generated_csv_name(staging_csv, args.client)
    validation = generator.write_and_validate(staging_csv)
    validation_path = build_dir / "validation_report.json"
    validation_path.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    if validation["status"] != "pass":
        raise RuntimeError(f"Staging validation failed: {validation['issues']}")

    csv_paths = write_csv_artifacts(build_dir, campaign, ad_groups)
    asset_paths = write_asset_artifacts(build_dir, asset_plan)
    human_review = build_dir / "human_review.md"
    write_human_review(
        path=human_review,
        campaign=campaign,
        ad_groups=ad_groups,
        validation=validation,
        website=args.website,
        asset_plan=asset_plan,
    )

    output_html = build_dir / "Client_New_Campaign_Review.html"
    output_pdf = build_dir / "Client_New_Campaign_Review.pdf"
    budget = BudgetPlan(args.monthly_budget, args.cpc_low, args.cpc_high)
    write_report(
        client=args.display_name,
        date_label=date_label,
        staging_csv=staging_csv,
        website_scan_json=scanner_paths["website_scan"],
        service_catalog_json=service_catalog_path,
        geo_strategy_json=geo_strategy_path,
        source_attribution_json=scanner_paths["source_attribution"],
        service_logic_research_json=service_logic_path,
        output_html=output_html,
        budget=budget,
    )
    findings, summary = audit_html(output_html)
    if [finding for finding in findings if finding.severity == "error"]:
        raise RuntimeError("Generated HTML report failed static audit.")

    visual_audit_dir = build_dir / "new_campaign_visual_audit"
    subprocess.run(
        [
            sys.executable,
            "presentations/tools/build_new_campaign_report.py",
            "--client",
            args.display_name,
            "--date",
            date_label,
            "--staging-csv",
            str(staging_csv),
            "--website-scan-json",
            str(scanner_paths["website_scan"]),
            "--service-catalog-json",
            str(service_catalog_path),
            "--geo-strategy-json",
            str(geo_strategy_path),
            "--source-attribution-json",
            str(scanner_paths["source_attribution"]),
            "--service-logic-research-json",
            str(service_logic_path),
            "--monthly-budget",
            str(args.monthly_budget),
            "--output-html",
            str(output_html),
            "--output-pdf",
            str(output_pdf),
            "--visual-audit-dir",
            str(visual_audit_dir),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    client_email_draft = build_dir / "client_email_draft.md"
    write_client_email_draft(
        client_email_draft,
        EmailDraftInput(
            client=args.display_name,
            date_label=date_label,
            report_type="new campaign build",
            pdf_path=output_pdf,
            summary=summarize_staging(read_staging(staging_csv)),
        ),
    )

    artifacts = {
        "staging_csv": staging_csv,
        "validation_report": validation_path,
        "website_scan": scanner_paths["website_scan"],
        "source_attribution": scanner_paths["source_attribution"],
        "raw_crawl": scanner_paths["raw_crawl"],
        "service_catalog": service_catalog_path,
        "service_logic_research": service_logic_path,
        "geo_strategy": geo_strategy_path,
        "rsa_headline_quality_audit": headline_audit_path,
        "human_review": human_review,
        "client_report_html": output_html,
        "client_report_pdf": output_pdf,
        "client_email_draft": client_email_draft,
        "visual_audit_dir": visual_audit_dir,
        **csv_paths,
        **asset_paths,
    }
    report_contract = build_report_contract(
        report_type=ReportType.NEW_CAMPAIGN,
        report_title="Client_New_Campaign_Review",
        source_artifacts={
            "website_scan": scanner_paths["website_scan"],
            "service_catalog": service_catalog_path,
            "service_logic_research": service_logic_path,
            "geo_strategy": geo_strategy_path,
            "source_attribution": scanner_paths["source_attribution"],
            "campaign_taxonomy": csv_paths["campaign_taxonomy"],
            "rsa_copy_matrix": csv_paths["rsa_copy_matrix"],
        },
        report_html=output_html,
        report_pdf=output_pdf,
        visual_audit_dir=visual_audit_dir,
        staging_csv=staging_csv,
        validation_report=validation_path,
        client_email_draft=client_email_draft,
        quality_gates=[
            QualityGateResult("staging_validation", validation["status"]),
            QualityGateResult(
                "static_html_audit",
                "pass" if summary.get("errors", 0) == 0 else "fail",
                details=summary,
            ),
            QualityGateResult("pdf_visual_audit", "pass", details={"visual_audit_dir": str(visual_audit_dir)}),
            QualityGateResult("manual_contact_sheet_review", "pending"),
        ],
    )
    manifest = build_dir / "run_manifest.json"
    write_manifest(
        path=manifest,
        client=args.display_name,
        date_label=date_label,
        build_dir=build_dir,
        artifacts=artifacts,
        validation=validate_file(staging_csv),
        report_audit=summary,
        report_contract=report_contract.manifest_fields(),
    )
    artifacts["run_manifest"] = manifest
    return artifacts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a one-shot initial Search campaign build for a new client.")
    parser.add_argument("--agency", required=True)
    parser.add_argument("--client", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--website", required=True)
    parser.add_argument("--build-date")
    parser.add_argument("--date-label")
    parser.add_argument("--build-dir", type=Path)
    parser.add_argument("--clients-dir", type=Path, default=ROOT / "clients")
    parser.add_argument("--campaign-name")
    parser.add_argument(
        "--csv-timestamp",
        help="Timestamp used in generated CSV filenames. Defaults to current UTC time.",
    )
    parser.add_argument(
        "--csv-purpose",
        default="google_ads_editor_staging",
        help="Purpose segment used in generated CSV filenames.",
    )
    parser.add_argument("--daily-budget", type=float, default=100.0)
    parser.add_argument("--monthly-budget", type=float, default=3000.0)
    parser.add_argument("--cpc-low", type=float)
    parser.add_argument("--cpc-high", type=float)
    parser.add_argument("--location", action="append", required=True, help="Location name or Location|ID. May repeat.")
    parser.add_argument("--source-page", action="append", default=[], help="Preferred source page URL. May repeat.")
    parser.add_argument("--service", action="append", default=[], help="Approved service. May repeat.")
    parser.add_argument("--negative", action="append", default=[], help="Campaign-level negative phrase keyword. May repeat.")
    parser.add_argument("--max-pages", type=int, default=12)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    artifacts = build_initial_campaign(args)
    print(json.dumps({key: str(path) for key, path in artifacts.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
