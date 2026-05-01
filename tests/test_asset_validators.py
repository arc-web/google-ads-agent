from __future__ import annotations

from shared.validators.asset_group_validator import AssetGroupValidator
from shared.validators.asset_validator import AssetValidator
from shared.validators.pmax_campaign.pmax_campaign_validator import PMAXCampaignValidator


def issue_types(issues):
    return {issue["issue_type"] for issue in issues}


def csv_text(headers, rows):
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(row.get(header, "") for header in headers))
    return "\n".join(lines)


def test_asset_validator_skips_search_rows_without_asset_markers():
    content = csv_text(
        ["Campaign", "Ad Group", "Criterion Type", "Keyword"],
        [{"Campaign": "ARC - Search - Test - V1", "Ad Group": "Test", "Criterion Type": "Phrase", "Keyword": "therapy"}],
    )

    assert AssetValidator().validate_assets("search.csv", content) == []


def test_asset_validator_flags_asset_row_length_and_url_issues():
    content = csv_text(
        ["Campaign Type", "Asset Group", "Headline 1", "Description 1", "Image URL", "Video ID 1"],
        [
            {
                "Campaign Type": "Performance Max",
                "Asset Group": "Core Services",
                "Headline 1": "This headline is too long for asset use",
                "Description 1": "D" * 91,
                "Image URL": "not-a-url",
                "Video ID 1": "bad",
            }
        ],
    )

    issues = AssetValidator().validate_assets("pmax.csv", content)

    assert {
        "headline_too_long",
        "description_too_long",
        "invalid_image_url",
        "invalid_video_id",
    } <= issue_types(issues)


def test_asset_group_validator_skips_search_rows():
    content = csv_text(
        ["Campaign", "Ad Group", "Criterion Type", "Keyword", "Final URL"],
        [
            {
                "Campaign": "ARC - Search - Test - V1",
                "Ad Group": "Test",
                "Criterion Type": "Phrase",
                "Keyword": "therapy",
                "Final URL": "https://example.com",
            }
        ],
    )

    assert AssetGroupValidator().validate_asset_groups("search.csv", content) == []


def test_asset_group_validator_flags_explicit_pmax_asset_group_issues():
    content = csv_text(
        ["Campaign Type", "Campaign", "Asset Group", "Final URL"],
        [
            {
                "Campaign Type": "Performance Max",
                "Campaign": "ARC - PMAX - Test - V1",
                "Asset Group": "",
                "Final URL": "https://example.com",
            },
            {
                "Campaign Type": "Performance Max",
                "Campaign": "ARC - PMAX - Test - V1",
                "Asset Group": "Core Ad Group",
                "Final URL": "example.com",
            },
        ],
    )

    issues = AssetGroupValidator().validate_asset_groups("pmax.csv", content)

    assert {
        "missing_asset_group",
        "asset_group_mentions_ad_group",
        "invalid_url_format",
    } <= issue_types(issues)


def test_pmax_campaign_validator_ignores_search_rows():
    validator = PMAXCampaignValidator()
    row = {"Campaign Type": "Search", "Campaign": "ARC - Search - Test - V1"}

    validator.validate_pmax_campaign_row("unused-client", "search.csv", row, 2)
    validator.validate_pmax_asset_group_row("unused-client", "search.csv", row, 2)
    validator.validate_pmax_asset_row("unused-client", "search.csv", row, 2)
    validator.validate_pmax_search_theme_row("unused-client", "search.csv", row, 2)

    assert validator.get_validation_report()["total_issues"] == 0


def test_pmax_campaign_validator_reports_generic_pmax_issues():
    validator = PMAXCampaignValidator()

    validator.validate_pmax_campaign_row(
        "unused-client",
        "pmax.csv",
        {
            "Campaign Type": "Performance Max",
            "Campaign Bid Strategy Type": "Manual CPC",
            "EU political ads": "",
            "Brand guidelines": "Maybe",
        },
        2,
    )
    validator.validate_pmax_asset_group_row(
        "unused-client",
        "pmax.csv",
        {"Campaign Type": "Performance Max", "Asset Group": "Core Ad Group", "Final URL": ""},
        3,
    )
    validator.validate_pmax_asset_row(
        "unused-client",
        "pmax.csv",
        {"Asset Type": "TEXT", "Asset": "Headline asset", "Text Asset": ""},
        4,
    )

    report = validator.get_validation_report()
    types = {issue["issue_type"] for issue in report["issues"]}

    assert {
        "missing_eu_political_ads",
        "unexpected_bid_strategy",
        "unexpected_brand_guidelines_value",
        "asset_group_mentions_ad_group",
        "missing_final_url",
        "missing_text_asset",
    } <= types
    assert "legacy_context" not in report["issues"][0]
