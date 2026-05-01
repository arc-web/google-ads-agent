from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from shared.comprehensive_csv_validator import AutoFixDisabled, ComprehensiveCSVValidator
from shared.rebuild.staging_validator import REQUIRED_HEADERS, REQUIRED_RSA_DESCRIPTIONS, REQUIRED_RSA_HEADLINES


def _base_row() -> dict[str, str]:
    headers = REQUIRED_HEADERS + REQUIRED_RSA_HEADLINES + REQUIRED_RSA_DESCRIPTIONS + ["Path 1", "Path 2", "Radius"]
    return {header: "" for header in headers}


def _write_staging_csv(path: Path, criterion_type: str = "Phrase") -> None:
    headers = REQUIRED_HEADERS + REQUIRED_RSA_HEADLINES + REQUIRED_RSA_DESCRIPTIONS + ["Path 1", "Path 2", "Radius"]
    rows: list[dict[str, str]] = []

    campaign = _base_row()
    campaign.update(
        {
            "Campaign": "ARC - Search - Therapy - V1",
            "Campaign Type": "Search",
            "Networks": "Google search",
            "Budget": "100",
            "Budget type": "Daily",
            "EU political ads": "Doesn't have EU political ads",
            "Broad match keywords": "Off",
            "Status": "Enabled",
        }
    )
    rows.append(campaign)

    ad_group = _base_row()
    ad_group.update(
        {
            "Campaign": "ARC - Search - Therapy - V1",
            "Ad Group": "Therapy Services",
            "Status": "Enabled",
        }
    )
    rows.append(ad_group)

    keyword = _base_row()
    keyword.update(
        {
            "Campaign": "ARC - Search - Therapy - V1",
            "Ad Group": "Therapy Services",
            "Criterion Type": criterion_type,
            "Keyword": "therapy services",
            "Status": "Enabled",
        }
    )
    rows.append(keyword)

    rsa = _base_row()
    rsa.update(
        {
            "Campaign": "ARC - Search - Therapy - V1",
            "Ad Group": "Therapy Services",
            "Ad type": "Responsive search ad",
            "Final URL": "https://example.com/therapy",
            "Path 1": "therapy",
            "Path 2": "care",
            "Status": "Enabled",
        }
    )
    for index, headline in enumerate(REQUIRED_RSA_HEADLINES, start=1):
        rsa[headline] = f"Focused Therapy Support {index}"
    for index, description in enumerate(REQUIRED_RSA_DESCRIPTIONS, start=1):
        rsa[description] = f"Schedule therapy care with a local team today. Option {index}"
    rows.append(rsa)

    location = _base_row()
    location.update(
        {
            "Campaign": "ARC - Search - Therapy - V1",
            "Location": "New York",
            "Location ID": "1023191",
            "Status": "Enabled",
        }
    )
    rows.append(location)

    with path.open("w", encoding="utf-16", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def test_comprehensive_validator_delegates_to_active_staging_validator(tmp_path: Path) -> None:
    csv_path = tmp_path / "Google_Ads_Editor_Staging_CURRENT.csv"
    _write_staging_csv(csv_path)

    report = ComprehensiveCSVValidator().validate_csv_file(str(csv_path))

    assert report["success"] is True
    assert report["final_status"] == "PASS"
    assert report["active_staging_report"]["status"] == "pass"
    assert report["validation_report"]["active_staging"]["encoding"] == "utf-16"


def test_comprehensive_validator_rejects_exact_match_through_active_rules(tmp_path: Path) -> None:
    csv_path = tmp_path / "Google_Ads_Editor_Staging_CURRENT.csv"
    _write_staging_csv(csv_path, criterion_type="Exact")

    report = ComprehensiveCSVValidator().validate_csv_file(str(csv_path))
    active_issues = report["active_staging_report"]["issues"]

    assert report["final_status"] == "FAIL"
    assert any(issue["rule"] == "disallowed_match_type" for issue in active_issues)


def test_comprehensive_validator_auto_fix_is_disabled_and_file_is_unchanged(tmp_path: Path) -> None:
    csv_path = tmp_path / "Google_Ads_Editor_Staging_CURRENT.csv"
    _write_staging_csv(csv_path, criterion_type="Exact")
    before = csv_path.read_bytes()

    with pytest.raises(AutoFixDisabled):
        ComprehensiveCSVValidator().validate_csv_file(str(csv_path), auto_fix=True)

    assert csv_path.read_bytes() == before


def test_run_csv_validation_cli_writes_active_report(tmp_path: Path) -> None:
    csv_path = tmp_path / "Google_Ads_Editor_Staging_CURRENT.csv"
    report_path = tmp_path / "validation_report.json"
    _write_staging_csv(csv_path)

    result = subprocess.run(
        [
            sys.executable,
            "shared/run_csv_validation.py",
            "--csv",
            str(csv_path),
            "--json-output",
            str(report_path),
        ],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["final_status"] == "PASS"
    assert report["active_staging_report"]["status"] == "pass"


def test_run_csv_validation_cli_rejects_fix_without_mutating_source(tmp_path: Path) -> None:
    csv_path = tmp_path / "Google_Ads_Editor_Staging_CURRENT.csv"
    _write_staging_csv(csv_path, criterion_type="Exact")
    before = csv_path.read_bytes()

    result = subprocess.run(
        [sys.executable, "shared/run_csv_validation.py", "--csv", str(csv_path), "--fix"],
        cwd=Path(__file__).resolve().parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "Auto-fix is disabled" in result.stderr
    assert csv_path.read_bytes() == before
