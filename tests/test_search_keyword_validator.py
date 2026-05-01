from __future__ import annotations

from shared.validators.search.search_keyword_validator import SearchKeywordValidator


def issue_types(issues):
    return {issue.issue_type for issue in issues}


def valid_phrase_row(**overrides):
    row = {
        "Campaign": "ARC - Search - Testing - V1",
        "Ad Group": "Testing - General",
        "Keyword": "child psychological evaluation",
        "Criterion Type": "Phrase",
        "Status": "Enabled",
    }
    row.update(overrides)
    return row


def test_accepts_current_plain_phrase_keyword_format():
    issues = SearchKeywordValidator().validate_keyword_row(valid_phrase_row(), 2)

    assert issues == []


def test_rejects_legacy_quoted_phrase_keyword_format():
    issues = SearchKeywordValidator().validate_keyword_row(
        valid_phrase_row(Keyword='"child psychological evaluation"'),
        2,
    )

    assert "plain_keyword_text" in issue_types(issues)


def test_rejects_broad_and_exact_criterion_types():
    validator = SearchKeywordValidator()

    broad_issues = validator.validate_keyword_row(valid_phrase_row(**{"Criterion Type": "Broad"}), 2)
    exact_issues = validator.validate_keyword_row(valid_phrase_row(**{"Criterion Type": "Exact"}), 3)

    assert "disallowed_match_type" in issue_types(broad_issues)
    assert "disallowed_match_type" in issue_types(exact_issues)


def test_accepts_campaign_level_negative_phrase_without_ad_group():
    issues = SearchKeywordValidator().validate_keyword_row(
        {
            "Campaign": "ARC - Search - Testing - V1",
            "Keyword": "free test",
            "Criterion Type": "Negative Phrase",
            "Status": "Enabled",
        },
        2,
    )

    assert issues == []


def test_rejects_leading_minus_negative_format():
    issues = SearchKeywordValidator().validate_keyword_row(
        {
            "Campaign": "ARC - Search - Testing - V1",
            "Keyword": "-free test",
            "Criterion Type": "Negative Phrase",
            "Status": "Enabled",
        },
        2,
    )

    assert "negative_keyword_format" in issue_types(issues)


def test_batch_validation_requires_positive_phrase_keywords():
    issues = SearchKeywordValidator().validate_keyword_data(
        [
            {
                "Campaign": "ARC - Search - Testing - V1",
                "Keyword": "free test",
                "Criterion Type": "Negative Phrase",
                "Status": "Enabled",
            }
        ]
    )

    assert "no_phrase_keywords" in issue_types(issues)
