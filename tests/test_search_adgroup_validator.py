from __future__ import annotations

from shared.validators.search.search_adgroup_validator import SearchAdGroupValidator


def issue_types(issues):
    return {issue.issue_type for issue in issues}


def ad_group_row(**overrides):
    row = {
        "Campaign": "ARC - Search - Testing - V1",
        "Ad Group": "Testing - General",
        "Status": "Enabled",
    }
    row.update(overrides)
    return row


def test_accepts_active_ad_group_header_without_noise():
    issues = SearchAdGroupValidator().validate_adgroup_row(ad_group_row(), 2)

    assert issues == []


def test_accepts_legacy_ad_group_header_alias():
    issues = SearchAdGroupValidator().validate_adgroup_row(
        {
            "Campaign": "ARC - Search - Testing - V1",
            "Ad group": "Testing - General",
            "Ad group status": "Enabled",
        },
        2,
    )

    assert issues == []


def test_requires_campaign_and_ad_group_name():
    issues = SearchAdGroupValidator().validate_adgroup_row({"Status": "Enabled"}, 2)

    assert {"missing_campaign", "missing_adgroup_name"} <= issue_types(issues)


def test_rejects_invalid_cpc_format():
    issues = SearchAdGroupValidator().validate_adgroup_row(ad_group_row(**{"Max CPC": "not-a-number"}), 2)

    assert "invalid_cpc_format" in issue_types(issues)


def test_flags_duplicate_ad_group_inside_same_campaign():
    issues = SearchAdGroupValidator().validate_adgroup_data(
        [
            ad_group_row(),
            ad_group_row(),
        ]
    )

    assert "duplicate_adgroup_name" in issue_types(issues)


def test_allows_same_ad_group_name_in_different_campaigns():
    issues = SearchAdGroupValidator().validate_adgroup_data(
        [
            ad_group_row(Campaign="ARC - Search - Testing - V1"),
            ad_group_row(Campaign="ARC - Search - Other - V1"),
        ]
    )

    assert "duplicate_adgroup_name" not in issue_types(issues)
