from __future__ import annotations

import csv
from pathlib import Path

from shared.rebuild.staging_validator import (
    REQUIRED_HEADERS,
    REQUIRED_RSA_DESCRIPTIONS,
    REQUIRED_RSA_HEADLINES,
)
from shared.validators.search.search_master_validator import SearchMasterValidator


def headers() -> list[str]:
    output = list(REQUIRED_HEADERS)
    for header in REQUIRED_RSA_HEADLINES + REQUIRED_RSA_DESCRIPTIONS:
        if header not in output:
            output.append(header)
    for header in ("Path 1", "Path 2", "Radius", "Bid Modifier"):
        if header not in output:
            output.append(header)
    return output


def row(**overrides: str) -> dict[str, str]:
    output = {header: "" for header in headers()}
    output.update(overrides)
    return output


def campaign_row(**overrides: str) -> dict[str, str]:
    output = row(
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
    output.update(overrides)
    return output


def ad_group_row(**overrides: str) -> dict[str, str]:
    output = row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Ad Group": "Testing - General",
            "Status": "Enabled",
        },
    )
    output.update(overrides)
    return output


def keyword_row(**overrides: str) -> dict[str, str]:
    output = row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Ad Group": "Testing - General",
            "Keyword": "child psychological evaluation",
            "Criterion Type": "Phrase",
            "Status": "Enabled",
        },
    )
    output.update(overrides)
    return output


def negative_row(**overrides: str) -> dict[str, str]:
    output = row(
        Campaign="ARC - Search - Testing - V1",
        Keyword="free test",
        **{
            "Criterion Type": "Negative Phrase",
            "Status": "Enabled",
        },
    )
    output.update(overrides)
    return output


def rsa_row(**overrides: str) -> dict[str, str]:
    output = row(
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
        output[f"Headline {index}"] = f"Testing Care {index}"
    for index in range(1, 5):
        output[f"Description {index}"] = f"Schedule testing support with a focused care team {index}."
    output.update(overrides)
    return output


def location_row(**overrides: str) -> dict[str, str]:
    output = row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Location": "Ashburn, Virginia, United States",
            "Location ID": "1027067",
            "Status": "Enabled",
        },
    )
    output.update(overrides)
    return output


def write_tsv(path: Path, rows: list[dict[str, str]], encoding: str = "utf-16") -> None:
    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers(), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def issue_types(validator: SearchMasterValidator) -> set[str]:
    return {issue["issue_type"] for issue in validator.get_detailed_issues()}


def test_search_master_validator_constructs_without_old_argument_mismatch() -> None:
    validator = SearchMasterValidator()

    assert validator.keyword_validator is not None


def test_search_master_validator_accepts_active_utf16_staging_file(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(
        csv_path,
        [
            campaign_row(),
            ad_group_row(),
            keyword_row(),
            negative_row(),
            rsa_row(),
            location_row(),
        ],
    )
    validator = SearchMasterValidator()

    report = validator.validate_csv_file(str(csv_path))

    assert report.success is True
    assert report.total_issues == 0
    assert validator.get_detailed_issues() == []


def test_search_master_validator_reports_active_staging_errors(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(
        csv_path,
        [
            campaign_row(),
            ad_group_row(),
            keyword_row(**{"Criterion Type": "Broad"}),
            rsa_row(),
            location_row(),
        ],
    )
    validator = SearchMasterValidator()

    report = validator.validate_csv_file(str(csv_path))

    assert report.success is False
    assert "disallowed_match_type" in issue_types(validator)
