from __future__ import annotations

from shared.validators.search.search_text_ad_validator import SearchTextAdValidator


def issue_types(issues):
    return {issue.issue_type for issue in issues}


def rsa_row(**overrides):
    row = {
        "Campaign": "ARC - Search - Testing - V1",
        "Ad Group": "Testing - General",
        "Ad type": "Responsive search ad",
        "Final URL": "https://example.com/testing",
        "Path 1": "Testing",
        "Path 2": "Care",
        "Status": "Enabled",
    }
    for index in range(1, 16):
        row[f"Headline {index}"] = f"Focused Testing Support {index}"
    for index in range(1, 5):
        row[f"Description {index}"] = f"Review testing support options with a focused local care team {index}. Schedule Today."
    row.update(overrides)
    return row


def test_accepts_active_rsa_with_15_headlines_and_4_descriptions():
    issues = SearchTextAdValidator().validate_text_ad_row(rsa_row(), 2)

    assert issues == []


def test_requires_active_rsa_structure():
    issues = SearchTextAdValidator().validate_text_ad_row({}, 2)

    assert {
        "missing_campaign",
        "missing_ad_group",
        "missing_ad_type",
        "missing_final_url",
        "rsa_headline_required",
        "rsa_description_required",
    } <= issue_types(issues)


def test_rejects_legacy_text_ad_type():
    issues = SearchTextAdValidator().validate_text_ad_row(rsa_row(**{"Ad type": "Text ad"}), 2)

    assert "invalid_ad_type" in issue_types(issues)


def test_rejects_headline_and_description_over_limits():
    issues = SearchTextAdValidator().validate_text_ad_row(
        rsa_row(
            **{
                "Headline 1": "This headline is definitely far too long",
                "Description 1": "X" * 91,
            }
        ),
        2,
    )

    assert {"headline_too_long", "description_too_long"} <= issue_types(issues)


def test_rejects_short_low_value_headline():
    issues = SearchTextAdValidator().validate_text_ad_row(
        rsa_row(**{"Headline 1": "Ashburn Care"}),
        2,
    )

    assert "headline_minimum_value" in issue_types(issues)


def test_rejects_invalid_final_url_and_path_characters():
    issues = SearchTextAdValidator().validate_text_ad_row(
        rsa_row(
            **{
                "Final URL": "example.com/testing",
                "Path 1": "Testing/Path",
            }
        ),
        2,
    )

    assert {"invalid_final_url", "invalid_path_chars"} <= issue_types(issues)


def test_batch_validation_flags_duplicate_headlines():
    issues = SearchTextAdValidator().validate_text_ad_data(
        [
            rsa_row(**{"Headline 1": "Focused Testing Support One"}),
            rsa_row(**{"Headline 1": "Focused Testing Support One"}),
        ]
    )

    assert "duplicate_headlines" in issue_types(issues)
