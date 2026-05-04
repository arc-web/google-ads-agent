from __future__ import annotations

import csv
from pathlib import Path

import pytest

from shared.presentation.build_new_campaign_report import ad_group_rows, build_html, main, summarize_staging
from shared.presentation.report_quality_audit import audit_html


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = REPO_ROOT / "clients/therappc/nyc_mindful_mental_health_counseling/build/2026-05-02_initial_search_build"
VALID_HEADLINES = [
    "Practical Support Planning",
    "Training For Care Teams Now",
    "Support For Better Access",
    "Build Human Centered Care",
    "Clear Implementation Steps",
    "Review Team Support Needs",
    "Improve Care Team Readiness",
    "Plan Your Next Service Step",
    "Consulting For Care Teams",
    "Skills For Support Teams Now",
    "Focused Training Review Today",
    "Request Program Details Now",
    "Compare Support Options Today",
    "Talk With A Consulting Team",
    "Start With A Focused Review",
]


def clean_staging_csv(tmp_path: Path, *, duplicate_headline: bool = False) -> Path:
    source = BUILD_DIR / "Google_Ads_Editor_Staging_CURRENT.csv"
    target = tmp_path / "clean_staging.csv"
    with source.open("r", encoding="utf-16", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = [dict(row) for row in reader]
        fieldnames = list(reader.fieldnames or [])
    for row in rows:
        if row.get("Ad type") != "Responsive search ad":
            continue
        for index, headline in enumerate(VALID_HEADLINES, start=1):
            row[f"Headline {index}"] = headline
        if duplicate_headline:
            row["Headline 2"] = row["Headline 1"]
            break
    with target.open("w", encoding="utf-16", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    return target


def test_new_campaign_report_builds_client_facing_html(tmp_path: Path) -> None:
    staging_csv = clean_staging_csv(tmp_path)
    html = build_html(
        client="Mindful Mental Health Counseling",
        date_label="May 2, 2026",
        staging_csv=staging_csv,
        website_scan_json=BUILD_DIR / "website_scan.json",
        service_catalog_json=BUILD_DIR / "service_catalog.json",
        geo_strategy_json=BUILD_DIR / "geo_strategy.json",
        source_attribution_json=BUILD_DIR / "source_attribution.json",
    )
    output = tmp_path / "Client_New_Campaign_Review.html"
    output.write_text(html, encoding="utf-8")

    findings, summary = audit_html(output)

    assert "New Campaign Review" in html
    assert "What This Review Covers" in html
    assert "How The Campaign Can Grow Over Time" in html
    assert "Services We Are Running Ads For" in html
    assert "Client_New_Campaign_Review" not in html
    assert summary["errors"] == 0
    assert not [finding for finding in findings if finding.severity == "error"]
    assert "Headline quality gate: pass" in html


def test_new_campaign_report_renders_optional_capacity_goal_section(tmp_path: Path) -> None:
    staging_csv = clean_staging_csv(tmp_path)
    html = build_html(
        client="Mindful Mental Health Counseling",
        date_label="May 2, 2026",
        staging_csv=staging_csv,
        website_scan_json=BUILD_DIR / "website_scan.json",
        service_catalog_json=BUILD_DIR / "service_catalog.json",
        geo_strategy_json=BUILD_DIR / "geo_strategy.json",
        source_attribution_json=BUILD_DIR / "source_attribution.json",
        goal_facts={
            "section_title": "Capacity And Lead Goal",
            "initial_new_client_goal": 2,
            "planning_close_rate": 0.5,
            "minimum_qualified_leads": 4,
            "planning_qualified_lead_range": "4 to 8",
            "capacity_notes": ["Owner has immediate openings for about 2 to 3 clients."],
        },
    )

    assert "Capacity And Lead Goal" in html
    assert "Minimum leads needed" in html
    assert "4 to 8" in html


def test_new_campaign_report_omits_capacity_goal_section_without_facts(tmp_path: Path) -> None:
    staging_csv = clean_staging_csv(tmp_path)
    html = build_html(
        client="Mindful Mental Health Counseling",
        date_label="May 2, 2026",
        staging_csv=staging_csv,
        website_scan_json=BUILD_DIR / "website_scan.json",
        service_catalog_json=BUILD_DIR / "service_catalog.json",
        geo_strategy_json=BUILD_DIR / "geo_strategy.json",
        source_attribution_json=BUILD_DIR / "source_attribution.json",
    )

    assert "Capacity And Lead Goal" not in html


def test_new_campaign_report_blocks_bad_headline_export(tmp_path: Path) -> None:
    staging_csv = clean_staging_csv(tmp_path, duplicate_headline=True)

    with pytest.raises(ValueError, match="RSA headline quality audit failed"):
        build_html(
            client="Mindful Mental Health Counseling",
            date_label="May 2, 2026",
            staging_csv=staging_csv,
            website_scan_json=BUILD_DIR / "website_scan.json",
            service_catalog_json=BUILD_DIR / "service_catalog.json",
            geo_strategy_json=BUILD_DIR / "geo_strategy.json",
            source_attribution_json=BUILD_DIR / "source_attribution.json",
        )


def test_new_campaign_summary_counts_only_ad_group_rows() -> None:
    rows = [
        {"Campaign": "ARC - Search - Services - V1", "Campaign Type": "Search", "Networks": "Google search"},
        {"Campaign": "ARC - Search - Services - V1", "Ad Group": "Services - Consulting"},
        {"Campaign": "ARC - Search - Services - V1", "Ad Group": "Services - Consulting", "Criterion Type": "Phrase", "Keyword": "consulting services"},
        {"Campaign": "ARC - Search - Services - V1", "Ad Group": "Services - Consulting", "Ad type": "Responsive search ad"},
        {"Campaign": "ARC - Search - Services - V1", "Ad Group": "Services - Consulting", "Link text": "Consulting"},
        {"Campaign": "ARC - Search - Services - V1", "Ad Group": "Services - Consulting", "Callout text": "Focused Support"},
        {"Campaign": "ARC - Search - Services - V1", "Ad Group": "Services - Consulting", "Structured snippet header": "Services"},
        {"Campaign": "ARC - Search - Services - V1", "Ad Group": "Services - Consulting", "Phone number": "2097693923"},
        {"Campaign": "ARC - Search - Services - V1", "Ad Group": "Services - Consulting", "Business name": "EM Consulting"},
    ]

    summary = summarize_staging(rows)

    assert len(ad_group_rows(rows)) == 1
    assert summary.ad_groups == 1


def test_new_campaign_report_cli_writes_email_draft(tmp_path: Path, monkeypatch) -> None:
    output_html = tmp_path / "Client_New_Campaign_Review.html"
    output_email = tmp_path / "client_email_draft.md"
    staging_csv = clean_staging_csv(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "build_new_campaign_report.py",
            "--client",
            "Mindful Mental Health Counseling",
            "--date",
            "May 2, 2026",
            "--staging-csv",
            str(staging_csv),
            "--website-scan-json",
            str(BUILD_DIR / "website_scan.json"),
            "--service-catalog-json",
            str(BUILD_DIR / "service_catalog.json"),
            "--geo-strategy-json",
            str(BUILD_DIR / "geo_strategy.json"),
            "--source-attribution-json",
            str(BUILD_DIR / "source_attribution.json"),
            "--output-html",
            str(output_html),
            "--output-email",
            str(output_email),
        ],
    )

    assert main() == 0
    draft = output_email.read_text(encoding="utf-8")
    assert "Attachment:" in draft
    assert "Client_New_Campaign_Review.pdf" in draft
    assert "CSV" not in draft
    assert "csv" not in draft
