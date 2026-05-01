from __future__ import annotations

import csv
from pathlib import Path

import pytest

from shared.rebuild.staging_validator import (
    REQUIRED_HEADERS,
    REQUIRED_RSA_DESCRIPTIONS,
    REQUIRED_RSA_HEADLINES,
    validate_file,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
THLH_REV1_CSV = (
    REPO_ROOT
    / "clients"
    / "therappc"
    / "thinkhappylivehealthy"
    / "build"
    / "search_rebuild_test"
    / "THHL_Search_Services_Editor_Staging_REV1.csv"
)


def staging_headers() -> list[str]:
    headers = list(REQUIRED_HEADERS)
    for header in REQUIRED_RSA_HEADLINES + REQUIRED_RSA_DESCRIPTIONS:
        if header not in headers:
            headers.append(header)
    for header in ("Path 1", "Path 2", "Radius", "Bid Modifier"):
        if header not in headers:
            headers.append(header)
    return headers


def base_row(**overrides: str) -> dict[str, str]:
    row = {header: "" for header in staging_headers()}
    row.update(overrides)
    return row


def campaign_row(**overrides: str) -> dict[str, str]:
    row = base_row(
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
    row.update(overrides)
    return row


def ad_group_row(**overrides: str) -> dict[str, str]:
    row = base_row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Ad Group": "Testing - General",
            "Status": "Enabled",
        },
    )
    row.update(overrides)
    return row


def keyword_row(**overrides: str) -> dict[str, str]:
    row = base_row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Ad Group": "Testing - General",
            "Keyword": "child psychological evaluation",
            "Criterion Type": "Phrase",
            "Status": "Enabled",
        },
    )
    row.update(overrides)
    return row


def negative_phrase_row(**overrides: str) -> dict[str, str]:
    row = base_row(
        Campaign="ARC - Search - Testing - V1",
        Keyword="free test",
        **{
            "Criterion Type": "Negative Phrase",
            "Status": "Enabled",
        },
    )
    row.update(overrides)
    return row


def rsa_row(**overrides: str) -> dict[str, str]:
    row = base_row(
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
        row[f"Headline {index}"] = f"Testing Care {index}"
    for index in range(1, 5):
        row[f"Description {index}"] = f"Schedule testing support with a focused care team {index}."
    row.update(overrides)
    return row


def location_row(**overrides: str) -> dict[str, str]:
    row = base_row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Location": "Ashburn, Virginia, United States",
            "Location ID": "1027067",
            "Status": "Enabled",
        },
    )
    row.update(overrides)
    return row


def write_tsv(path: Path, rows: list[dict[str, str]], encoding: str = "utf-16") -> None:
    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=staging_headers(), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def issue_rules(report: dict) -> set[str]:
    return {issue["rule"] for issue in report["issues"]}


def test_valid_current_phrase_workflow_accepts_utf16_and_campaign_level_negatives(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(
        csv_path,
        [
            campaign_row(),
            ad_group_row(),
            keyword_row(),
            negative_phrase_row(),
            rsa_row(),
            location_row(),
        ],
        encoding="utf-16",
    )

    report = validate_file(csv_path)

    assert report["status"] == "pass"
    assert report["encoding"] == "utf-16"
    assert report["counts"]["keyword_rows"] == 1
    assert report["counts"]["negative_keyword_rows"] == 1
    assert report["keyword_criterion_types"] == {"Phrase": 1, "Negative Phrase": 1}
    assert report["issues"] == []


@pytest.mark.parametrize("criterion_type", ["Broad", "Exact"])
def test_broad_and_exact_keyword_types_fail(tmp_path: Path, criterion_type: str) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(), keyword_row(**{"Criterion Type": criterion_type})])

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "disallowed_match_type" in issue_rules(report)


def test_quoted_keyword_text_fails_even_when_criterion_type_is_phrase(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(), keyword_row(Keyword='"child psychological evaluation"')])

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "plain_keyword_text" in issue_rules(report)


def test_broad_match_campaign_setting_must_be_off(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(**{"Broad match keywords": "On"}), keyword_row()])

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "broad_match_off" in issue_rules(report)


def test_missing_location_id_is_warning_not_failure(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(), keyword_row(), rsa_row(), location_row(**{"Location ID": ""})])

    report = validate_file(csv_path)

    assert report["status"] == "pass"
    assert report["issue_counts"] == {"warning": 1}
    assert "location_id_preferred" in issue_rules(report)


def test_real_thlh_rev1_staging_file_matches_current_contract() -> None:
    report = validate_file(THLH_REV1_CSV)

    assert report["status"] == "pass"
    assert report["encoding"] == "utf-16"
    assert report["rows"] == 470
    assert report["headers"] == 203
    assert report["campaigns"] == [
        "ARC - Search - Adult Therapy - V1",
        "ARC - Search - Brand - V1",
        "ARC - Search - Psychiatry - V1",
        "ARC - Search - Testing - V1",
    ]
    assert report["ad_groups"] == 49
    assert report["counts"]["campaign_rows"] == 4
    assert report["counts"]["ad_group_rows"] == 49
    assert report["counts"]["keyword_rows"] == 295
    assert report["counts"]["negative_keyword_rows"] == 20
    assert report["counts"]["rsa_rows"] == 49
    assert report["counts"]["location_rows"] == 49
    assert report["counts"]["radius_rows"] == 4
    assert report["keyword_criterion_types"] == {"Phrase": 295, "Negative Phrase": 20}
    assert report["issue_counts"] == {}
    assert report["issues"] == []
