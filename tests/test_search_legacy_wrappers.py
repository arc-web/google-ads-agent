from __future__ import annotations

import csv
import sys
import types
from importlib import import_module
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def install_package_shim() -> None:
    """Bypass the broken legacy validators package __init__ during wrapper tests."""
    shared = sys.modules.setdefault("shared", types.ModuleType("shared"))
    shared.__path__ = [str(REPO_ROOT / "shared")]
    validators = sys.modules.setdefault("shared.validators", types.ModuleType("shared.validators"))
    validators.__path__ = [str(REPO_ROOT / "shared" / "validators")]
    search = sys.modules.setdefault("shared.validators.search", types.ModuleType("shared.validators.search"))
    search.__path__ = [str(REPO_ROOT / "shared" / "validators" / "search")]


install_package_shim()

SearchCampaignValidator = import_module(
    "shared.validators.search.search_campaign_validator"
).SearchCampaignValidator
AdGroupValidator = import_module("shared.validators.search.ad_group_validator").AdGroupValidator
KeywordValidator = import_module("shared.validators.search.keyword_validator").KeywordValidator
TextAdValidator = import_module("shared.validators.search.text_ad_validator").TextAdValidator
SearchValidator = import_module("shared.validators.search.search_validator").SearchValidator
SearchMasterValidator = import_module("shared.validators.search_master_validator").SearchMasterValidator

from shared.rebuild.staging_validator import REQUIRED_HEADERS, REQUIRED_RSA_DESCRIPTIONS, REQUIRED_RSA_HEADLINES


def headers() -> list[str]:
    output = list(REQUIRED_HEADERS)
    for header in REQUIRED_RSA_HEADLINES + REQUIRED_RSA_DESCRIPTIONS + ["Path 1", "Path 2"]:
        if header not in output:
            output.append(header)
    return output


def empty_row(**overrides: str) -> dict[str, str]:
    row = {header: "" for header in headers()}
    row.update(overrides)
    return row


def campaign_row(**overrides: str) -> dict[str, str]:
    row = empty_row(
        Campaign="ARC - Search - Example - V1",
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
    row = empty_row(Campaign="ARC - Search - Example - V1", **{"Ad Group": "Example Services", "Status": "Enabled"})
    row.update(overrides)
    return row


def keyword_row(**overrides: str) -> dict[str, str]:
    row = empty_row(
        Campaign="ARC - Search - Example - V1",
        **{
            "Ad Group": "Example Services",
            "Keyword": "example service support",
            "Criterion Type": "Phrase",
            "Status": "Enabled",
        },
    )
    row.update(overrides)
    return row


def rsa_row(**overrides: str) -> dict[str, str]:
    row = empty_row(
        Campaign="ARC - Search - Example - V1",
        **{
            "Ad Group": "Example Services",
            "Ad type": "Responsive search ad",
            "Final URL": "https://example.com/services",
            "Path 1": "Services",
            "Path 2": "Support",
            "Status": "Enabled",
        },
    )
    for index in range(1, 16):
        row[f"Headline {index}"] = f"Focused Example Support {index}"
    for index in range(1, 5):
        row[f"Description {index}"] = f"Schedule example support with a focused service team {index}."
    row.update(overrides)
    return row


def location_row(**overrides: str) -> dict[str, str]:
    row = empty_row(
        Campaign="ARC - Search - Example - V1",
        **{"Location": "Ashburn, Virginia, United States", "Location ID": "1027067", "Status": "Enabled"},
    )
    row.update(overrides)
    return row


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-16", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers(), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def test_legacy_campaign_validator_uses_active_search_rules() -> None:
    issues = SearchCampaignValidator().validate_campaign_row(campaign_row(**{"Broad match keywords": "On"}), 2)

    assert [issue.issue_type for issue in issues] == ["broad_match_off"]


def test_legacy_ad_group_validator_accepts_active_header() -> None:
    issues = AdGroupValidator().validate_ad_group("example.tsv", ad_group_row(), 2, {})

    assert issues == []


def test_legacy_keyword_validator_rejects_broad_and_exact_defaults() -> None:
    issues = KeywordValidator().validate_keywords(
        "example.tsv",
        keyword_row(**{"Criterion Type": "Exact"}),
        2,
    )

    assert {issue["issue_type"] for issue in issues} == {"disallowed_match_type"}


def test_legacy_text_ad_validator_requires_active_rsa_shape() -> None:
    issues = TextAdValidator().validate_text_ad("example.tsv", rsa_row(**{"Headline 15": ""}), 2)

    assert {issue["issue_type"] for issue in issues} == {"rsa_headline_required"}


def test_search_validator_coordinates_active_wrappers() -> None:
    content_rows = [campaign_row(), ad_group_row(), keyword_row(), rsa_row(), location_row()]
    buffer_path = REPO_ROOT / ".tmp-not-written.tsv"
    output = []
    from io import StringIO

    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=headers(), delimiter="\t")
    writer.writeheader()
    writer.writerows(content_rows)
    output.extend(SearchValidator().validate_search_csv(str(buffer_path), handle.getvalue()))

    assert output == []


def test_top_level_search_master_facade_validates_active_tsv(tmp_path: Path) -> None:
    csv_path = tmp_path / "active.tsv"
    write_tsv(csv_path, [campaign_row(), ad_group_row(), keyword_row(), rsa_row(), location_row()])

    result = SearchMasterValidator().validate_search_campaign_csv(str(csv_path))

    assert result["success"] is True
    assert result["validation_report"]["total_issues"] == 0
