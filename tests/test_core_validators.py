from __future__ import annotations

import csv
from pathlib import Path

from shared.rebuild.staging_validator import REQUIRED_HEADERS, REQUIRED_RSA_DESCRIPTIONS, REQUIRED_RSA_HEADLINES
from shared.validators.account_validator import AccountValidator
from shared.validators.campaign_validator import CampaignValidator
from shared.validators.csv_stage_manager import CSVStageManager
from shared.validators.master_validator import MasterValidator
from shared.validators.targeting_validator import TargetingValidator

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


def staging_headers() -> list[str]:
    headers = list(REQUIRED_HEADERS)
    for header in REQUIRED_RSA_HEADLINES + REQUIRED_RSA_DESCRIPTIONS:
        if header not in headers:
            headers.append(header)
    for header in ("Path 1", "Path 2", "Radius", "Bid Modifier"):
        if header not in headers:
            headers.append(header)
    return headers


def row(**overrides: str) -> dict[str, str]:
    data = {header: "" for header in staging_headers()}
    data.update(overrides)
    return data


def campaign_row(**overrides: str) -> dict[str, str]:
    data = row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Campaign Type": "Search",
            "Networks": "Google search",
            "Budget": "25.00",
            "Budget type": "Daily",
            "EU political ads": "Doesn't have EU political ads",
            "Broad match keywords": "Off",
            "Status": "Enabled",
        },
    )
    data.update(overrides)
    return data


def ad_group_row(**overrides: str) -> dict[str, str]:
    data = row(Campaign="ARC - Search - Testing - V1", **{"Ad Group": "Testing - General", "Status": "Enabled"})
    data.update(overrides)
    return data


def keyword_row(**overrides: str) -> dict[str, str]:
    data = row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Ad Group": "Testing - General",
            "Keyword": "child psychological evaluation",
            "Criterion Type": "Phrase",
            "Status": "Enabled",
        },
    )
    data.update(overrides)
    return data


def rsa_row(**overrides: str) -> dict[str, str]:
    data = row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Ad Group": "Testing - General",
            "Ad type": "Responsive search ad",
            "Final URL": "https://example.com/testing",
            "Path 1": "Testing",
            "Path 2": "Care",
            "Status": "Enabled",
        },
    )
    for index in range(1, 16):
        data[f"Headline {index}"] = VALID_HEADLINES[index - 1]
    for index in range(1, 5):
        data[f"Description {index}"] = f"Review testing support options with a focused local care team {index}. Schedule Today."
    data.update(overrides)
    return data


def location_row(**overrides: str) -> dict[str, str]:
    data = row(
        Campaign="ARC - Search - Testing - V1",
        **{"Location": "Ashburn, Virginia, United States", "Location ID": "1027067", "Status": "Enabled"},
    )
    data.update(overrides)
    return data


def write_tsv(path: Path, rows: list[dict[str, str]], encoding: str = "utf-16") -> None:
    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=staging_headers(), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def tsv_content(rows: list[dict[str, str]]) -> str:
    output_path = Path("/tmp/core_validator_synthetic.tsv")
    write_tsv(output_path, rows, encoding="utf-8")
    return output_path.read_text(encoding="utf-8")


def issue_types(issues: list[dict]) -> set[str]:
    return {issue["issue_type"] for issue in issues}


def test_account_validator_accepts_active_headers_and_case() -> None:
    content = tsv_content([campaign_row(), ad_group_row(), keyword_row(), rsa_row(), location_row()])

    validator = AccountValidator()

    assert validator.validate_csv_structure("synthetic.csv", content) == []
    assert validator.validate_account_settings("synthetic.csv", content) == []


def test_campaign_validator_enforces_active_search_settings() -> None:
    content = tsv_content([campaign_row(**{"Budget": "0", "Broad match keywords": "On", "EU political ads": ""})])

    issues = CampaignValidator().validate_campaign_settings("synthetic.csv", content)

    assert {"budget_positive", "broad_match_off", "eu_political_ads_required"} <= issue_types(issues)


def test_targeting_validator_prefers_location_id_and_validates_radius() -> None:
    content = tsv_content([location_row(**{"Location ID": ""}), location_row(Radius="0")])

    issues = TargetingValidator().validate_targeting("synthetic.csv", content)

    assert {"location_id_preferred", "radius_positive"} <= issue_types(issues)


def test_master_validator_delegates_to_active_staging_validator(tmp_path: Path) -> None:
    csv_path = tmp_path / "Google_Ads_Editor_Staging_CURRENT.csv"
    write_tsv(csv_path, [campaign_row(), ad_group_row(), keyword_row(), rsa_row(), location_row()])

    result = MasterValidator().validate_csv_file(str(csv_path))

    assert result["success"] is True
    assert result["final_status"] == "PASS"
    assert result["validation_report"]["active_staging"]["status"] == "pass"


def test_master_validator_keeps_legacy_search_helpers_available() -> None:
    content = tsv_content([campaign_row(), keyword_row()])
    validator = MasterValidator()

    assert validator._is_search_campaign_csv(content) is True
    assert validator._apply_auto_fixes_to_csv(content, []) == (content, [])


def test_stage_manager_uses_repo_local_sidecar_metadata(tmp_path: Path) -> None:
    csv_path = tmp_path / "Google_Ads_Editor_Staging_REV1.csv"
    write_tsv(csv_path, [campaign_row(), keyword_row(), rsa_row(), location_row()])
    manager = CSVStageManager(base_path=tmp_path)

    assert manager.get_csv_stage(csv_path) == "initial"
    assert manager.should_trigger_validation(csv_path) is True
    assert manager.mark_csv_stage(csv_path, "analyzed", "validated in test") is True
    assert csv_path.exists()
    assert manager.get_csv_stage(csv_path) == "analyzed"
    assert manager.should_trigger_validation(csv_path) is False
