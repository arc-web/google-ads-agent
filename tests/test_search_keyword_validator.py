from __future__ import annotations

from shared.rebuild.match_type_policy import keyword_origin_key
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

    assert "broad_match_blocked" in issue_types(broad_issues)
    assert "new_exact_requires_approval" in issue_types(exact_issues)


def test_revision_mode_preserves_source_proven_exact_as_warning():
    exact_row = valid_phrase_row(**{"Criterion Type": "Exact"})
    validator = SearchKeywordValidator(
        {
            "match_type_mode": "revision_existing_account",
            "keyword_origin_map": {
                keyword_origin_key(exact_row): {
                    "origin": "source_account_export",
                    "preserve": True,
                    "relevance_status": "preserve",
                }
            },
        }
    )

    issues = validator.validate_keyword_row(exact_row, 2)

    assert "preserved_existing_exact" in issue_types(issues)
    assert all(issue.severity != "critical" for issue in issues)


def test_new_negative_exact_is_blocked():
    issues = SearchKeywordValidator({"match_type_mode": "revision_existing_account"}).validate_keyword_row(
        {
            "Campaign": "ARC - Search - Testing - V1",
            "Keyword": "free test",
            "Criterion Type": "Negative Exact",
            "Status": "Enabled",
        },
        2,
    )

    assert "new_negative_exact_blocked" in issue_types(issues)


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
