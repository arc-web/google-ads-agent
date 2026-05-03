from __future__ import annotations

import json
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

    assert validate_file(staging)["status"] == "pass"
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
