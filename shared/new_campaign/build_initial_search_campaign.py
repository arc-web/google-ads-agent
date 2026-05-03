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

from shared.gads.core.search_campaigns.search_csv_generator import SearchCSVGenerator
from shared.presentation.build_new_campaign_report import BudgetPlan, write_report
from shared.presentation.report_quality_audit import audit_html
from shared.rebuild.scaffold_client import scaffold_client, slug
from shared.rebuild.staging_validator import validate_file
from shared.tools.website.website_scanner import WebsiteScanner


@dataclass
class LocationTarget:
    location: str
    location_id: str = ""


@dataclass
class AdGroupPlan:
    name: str
    final_url: str
    path_1: str
    path_2: str
    keywords: list[str]
    headlines: list[str]
    descriptions: list[str]


def clean_words(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9 &/-]+", " ", value)).strip()


def path_part(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "", value.title())
    return cleaned[:15] or "Services"


def fit_headline(value: str) -> str:
    text = clean_words(value)
    pads = [" Support", " Options", " Today", " Online", " Care", " Team"]
    index = 0
    while len(text) < 25:
        text = f"{text}{pads[index % len(pads)]}"
        index += 1
    if len(text) > 30:
        text = text[:30].rstrip()
        if len(text) < 25:
            text = f"{text} Support"[:30].rstrip()
    return text


def fit_description(value: str) -> str:
    text = clean_words(value)
    return text[:90].rstrip()


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


def headline_set(client: str, service: str) -> list[str]:
    seeds = [
        f"{service} Service Support",
        f"{service} Consult Today",
        f"{service} Options Online",
        f"{service} Help From Experts",
        f"{service} Appointment Help",
        f"{service} Answers Today",
        f"{service} Planning Support",
        f"{service} Local Support",
        f"{service} Next Step Help",
        f"{service} Clear Service Help",
        f"{client} Service Team",
        f"Book {service} Consult",
        f"Compare {service} Options",
        f"Start With {service} Help",
        f"Request {service} Details",
        f"Talk With A Service Team",
        f"Plan Your Service Next Step",
    ]
    headlines: list[str] = []
    for seed in seeds:
        headline = fit_headline(seed)
        if headline not in headlines:
            headlines.append(headline)
        if len(headlines) == 15:
            return headlines
    while len(headlines) < 15:
        headlines.append(fit_headline(f"{service} Support {len(headlines) + 1}"))
    return headlines


def description_set(service: str) -> list[str]:
    return [
        fit_description(f"Get clear next steps for {service.lower()} before launch decisions are finalized."),
        fit_description(f"Review service fit, availability, budget, and location details before ads go live."),
        fit_description(f"Start with a focused consultation and keep the first campaign easy to review."),
        fit_description(f"Campaign rows stay paused until the team approves services, regions, and copy."),
    ]


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
    source_pages: list[str],
) -> list[AdGroupPlan]:
    plans: list[AdGroupPlan] = []
    for service in service_catalog.get("active_services_for_staging", [])[:8]:
        final_url = landing_page_for_service(service, source_pages, website)
        keywords = unique(
            [
                service.lower(),
                f"{service.lower()} near me",
                f"{service.lower()} consultation",
                f"{service.lower()} services",
                f"{service.lower()} company",
                f"{service.lower()} online",
                f"best {service.lower()}",
            ],
            7,
        )
        plans.append(
            AdGroupPlan(
                name=f"Services - {service[:60]}",
                final_url=final_url,
                path_1=path_part(service),
                path_2="Services",
                keywords=keywords,
                headlines=headline_set(client, service),
                descriptions=description_set(service),
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
                    "campaign": campaign,
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
                        "campaign": campaign,
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
                        "campaign": campaign,
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
) -> None:
    keyword_count = sum(len(ad_group.keywords) for ad_group in ad_groups)
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
        "- Network: `Google search` only",
        "- Match type: `Phrase` only",
        "- API upload: off",
        "- Rows are paused for Google Ads Editor review.",
        "",
        "## Human Review Before Launch",
        "",
        "- Confirm services and priority order.",
        "- Confirm location targeting and location IDs.",
        "- Confirm budget, conversion tracking, and final URL readiness.",
        "- Import into Google Ads Editor and inspect platform warnings before upload.",
    ]
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
        source_pages=source_pages,
    )

    generator = SearchCSVGenerator()
    generator.add_campaign(campaign, args.daily_budget)
    for location in locations:
        generator.add_location(campaign, location.location, location_id=location.location_id)
    for ad_group in ad_groups:
        generator.add_ad_group(campaign, ad_group.name)
        for keyword in ad_group.keywords:
            generator.add_keyword(campaign, ad_group.name, keyword, final_url=ad_group.final_url)
        generator.add_rsa(
            campaign,
            ad_group.name,
            ad_group.final_url,
            headlines=ad_group.headlines,
            descriptions=ad_group.descriptions,
            path_1=ad_group.path_1,
            path_2=ad_group.path_2,
        )
    for negative in args.negative:
        generator.add_negative_phrase(campaign, negative)

    staging_csv = build_dir / "Google_Ads_Editor_Staging_CURRENT.csv"
    validation = generator.write_and_validate(staging_csv)
    validation_path = build_dir / "validation_report.json"
    validation_path.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    if validation["status"] != "pass":
        raise RuntimeError(f"Staging validation failed: {validation['issues']}")

    csv_paths = write_csv_artifacts(build_dir, campaign, ad_groups)
    human_review = build_dir / "human_review.md"
    write_human_review(path=human_review, campaign=campaign, ad_groups=ad_groups, validation=validation, website=args.website)

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

    artifacts = {
        "staging_csv": staging_csv,
        "validation_report": validation_path,
        "website_scan": scanner_paths["website_scan"],
        "source_attribution": scanner_paths["source_attribution"],
        "raw_crawl": scanner_paths["raw_crawl"],
        "service_catalog": service_catalog_path,
        "geo_strategy": geo_strategy_path,
        "human_review": human_review,
        "client_report_html": output_html,
        "client_report_pdf": output_pdf,
        "visual_audit_dir": visual_audit_dir,
        **csv_paths,
    }
    manifest = build_dir / "run_manifest.json"
    write_manifest(
        path=manifest,
        client=args.display_name,
        date_label=date_label,
        build_dir=build_dir,
        artifacts=artifacts,
        validation=validate_file(staging_csv),
        report_audit=summary,
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
