from __future__ import annotations

import csv
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DRY_RUN_DIR = (
    REPO_ROOT
    / "clients/therappc/thinkhappylivehealthy/build/dry_run_account_build_2026-05-01"
)
STAGING_CSV = DRY_RUN_DIR / "Google_Ads_Editor_Staging_DRY_RUN.csv"


def test_dry_run_staging_artifact_matches_active_search_contract() -> None:
    rows = list(csv.DictReader(STAGING_CSV.read_text(encoding="utf-16").splitlines(), delimiter="\t"))

    assert len(rows) == 11
    assert {row["Criterion Type"] for row in rows if row.get("Keyword")} == {"Phrase"}
    assert {row["Broad match keywords"] for row in rows if row.get("Campaign Type") == "Search"} == {"Off"}
    assert [row["Location ID"] for row in rows if row.get("Location")] == ["1027028", "1027118"]
    assert all(row.get("Campaign Type") in {"", "Search"} for row in rows)
    assert not [header for header in rows[0] if "upload" in header.lower() or "api" in header.lower()]


def test_dry_run_validation_reports_are_clean() -> None:
    staging = json.loads((DRY_RUN_DIR / "staging_validator_report.json").read_text(encoding="utf-8"))
    master = json.loads((DRY_RUN_DIR / "master_validator_report.json").read_text(encoding="utf-8"))
    search = json.loads((DRY_RUN_DIR / "search_master_validator_report.json").read_text(encoding="utf-8"))

    assert staging["status"] == "pass"
    assert staging.get("issues", []) == []
    assert master["final_status"] == "PASS"
    assert master["validation_report"]["total_issues"] == 0
    assert search["success"] is True
    assert search["validation_report"]["total_issues"] == 0
