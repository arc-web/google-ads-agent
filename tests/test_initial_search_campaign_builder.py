from __future__ import annotations

import json
import csv
import subprocess
import sys
from pathlib import Path

from shared.presentation.report_quality_audit import audit_html
from shared.rebuild.staging_validator import validate_file


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "new_campaign_site"


def test_one_shot_initial_search_build_with_temp_client(tmp_path: Path) -> None:
    client_root = tmp_path / "client_build"
    result = subprocess.run(
        [
            sys.executable,
            "shared/new_campaign/build_initial_search_campaign.py",
            "--agency",
            "fixture_agency",
            "--client",
            "fixture_client",
            "--display-name",
            "Fixture Client",
            "--website",
            (FIXTURE_DIR / "index.html").as_uri(),
            "--build-date",
            "2026-05-04",
            "--csv-timestamp",
            "20260504_153045",
            "--date-label",
            "May 4, 2026",
            "--build-dir",
            str(client_root),
            "--clients-dir",
            str(tmp_path / "clients"),
            "--location",
            "United States|2840",
            "--service",
            "Repair Services",
            "--service",
            "Consulting Services",
            "--negative",
            "jobs",
            "--max-pages",
            "5",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    artifacts = json.loads(result.stdout)

    staging = Path(artifacts["staging_csv"])
    html = Path(artifacts["client_report_html"])
    manifest = json.loads(Path(artifacts["run_manifest"]).read_text(encoding="utf-8"))
    website_scan = json.loads(Path(artifacts["website_scan"]).read_text(encoding="utf-8"))
    validation = validate_file(staging)
    asset_plan = json.loads(Path(artifacts["ad_asset_plan"]).read_text(encoding="utf-8"))
    human_review = Path(artifacts["human_review"]).read_text(encoding="utf-8")
    email_draft = Path(artifacts["client_email_draft"]).read_text(encoding="utf-8")

    assert validation["status"] == "pass"
    assert staging.name == "fixture_client_google_ads_editor_staging_20260504_153045.csv"
    assert validation["counts"]["sitelink_rows"] >= 2
    assert validation["counts"]["callout_rows"] >= 1
    assert validation["counts"]["structured_snippet_rows"] == 0
    assert validation["counts"]["business_name_rows"] == 1
    assert asset_plan["counts"]["sitelinks"] >= 2
    assert asset_plan["counts"]["callouts"] >= 1
    assert asset_plan["counts"]["structured_snippets"] == 0
    assert asset_plan["counts"]["business_names"] == 1
    assert "ad_asset_research_matrix_json" in manifest["artifacts"]
    assert "image_asset_manifest" in manifest["artifacts"]
    assert "qualified_non_homepage_landing_page" in human_review
    assert "no_confirmed_phone_number" in human_review
    assert "insufficient_explicit_pricing" in human_review
    assert "ad_asset_plan" in manifest["artifacts"]
    assert "client_email_draft" in manifest["artifacts"]
    assert manifest["report_type"] == "new_campaign"
    assert manifest["report_title"] == "Client_New_Campaign_Review"
    assert manifest["report_html"] == manifest["artifacts"]["client_report_html"]
    assert manifest["report_pdf"] == manifest["artifacts"]["client_report_pdf"]
    assert manifest["visual_audit_dir"] == manifest["artifacts"]["visual_audit_dir"]
    assert manifest["client_email_draft"] == manifest["artifacts"]["client_email_draft"]
    assert "campaign_structure" in manifest["report_sections"]
    assert "revision_changes" not in manifest["report_sections"]
    assert {item["key"] for item in manifest["approval_items"]} == {
        "ad_groups",
        "ads",
        "regional_targeting",
        "budget",
    }
    assert {gate["gate"]: gate["status"] for gate in manifest["quality_gate_results"]} == {
        "staging_validation": "pass",
        "static_html_audit": "pass",
        "pdf_visual_audit": "pass",
        "manual_contact_sheet_review": "pending",
    }
    assert "Attachment:" in email_draft
    assert "Client_New_Campaign_Review.pdf" in email_draft
    assert "CSV" not in email_draft
    assert "csv" not in email_draft
    findings, summary = audit_html(html)
    assert summary["errors"] == 0
    assert not [finding for finding in findings if finding.severity == "error"]
    assert manifest["live_upload"] is False
    assert manifest["launch_state"] == "staged_for_google_ads_editor_review"
    assert website_scan["fact_review"]["verified_website_facts"]
    assert website_scan["fact_review"]["strategy_inferences"]
    assert website_scan["fact_review"]["human_review_needed"]

    rebuilt = subprocess.run(
        [
            sys.executable,
            "presentations/tools/build_new_campaign_report.py",
            "--manifest-json",
            artifacts["run_manifest"],
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "static_audit" in rebuilt.stdout


def test_one_shot_state_targets_create_state_ad_group_tiers(tmp_path: Path) -> None:
    client_root = tmp_path / "state_client_build"
    result = subprocess.run(
        [
            sys.executable,
            "shared/new_campaign/build_initial_search_campaign.py",
            "--agency",
            "fixture_agency",
            "--client",
            "state_fixture_client",
            "--display-name",
            "State Fixture Client",
            "--website",
            (FIXTURE_DIR / "index.html").as_uri(),
            "--build-date",
            "2026-05-04",
            "--csv-timestamp",
            "20260504_163045",
            "--date-label",
            "May 4, 2026",
            "--build-dir",
            str(client_root),
            "--clients-dir",
            str(tmp_path / "clients"),
            "--location",
            "New York, United States|21167",
            "--location",
            "New Jersey, United States|21164",
            "--location",
            "Brooklyn, New York, United States|1023191",
            "--service",
            "Repair Services",
            "--max-pages",
            "5",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    artifacts = json.loads(result.stdout)
    staging = Path(artifacts["staging_csv"])
    validation = validate_file(staging)
    with staging.open("r", encoding="utf-16", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    campaigns = {row["Campaign"] for row in rows if row.get("Campaign")}
    ad_groups = {row["Ad Group"] for row in rows if row.get("Ad Group")}
    text = "\n".join(" ".join(row.values()) for row in rows)

    assert validation["status"] == "pass"
    assert "ARC - Search - Repair Services - NY - V1" in campaigns
    assert "ARC - Search - Repair Services - NJ - V1" in campaigns
    assert "Services - Repair Services - General" in ad_groups
    assert "Services - Repair Services - Near Me" in ad_groups
    assert "Services - Repair Services - New York" in ad_groups
    assert "Services - Repair Services - New Jersey" in ad_groups
    assert "Services - Repair Services - Brooklyn" in ad_groups
    assert "repair services in Brooklyn" in text
