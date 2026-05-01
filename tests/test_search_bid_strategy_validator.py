from __future__ import annotations

from shared.validators.search.search_bid_strategy_validator import SearchBidStrategyValidator


def issue_types(issues):
    return {issue.issue_type for issue in issues}


def bid_row(**overrides):
    row = {
        "Campaign": "ARC - Search - Testing - V1",
        "Bid Strategy Type": "Maximize conversions",
        "Target CPA": "50.00",
        "Max CPC": "2.50",
    }
    row.update(overrides)
    return row


def test_accepts_known_bid_strategy_and_numeric_targets():
    issues = SearchBidStrategyValidator().validate_bid_strategy_row(bid_row(), 2)

    assert issues == []


def test_warns_on_bid_strategy_outside_allow_list():
    issues = SearchBidStrategyValidator().validate_bid_strategy_row(
        bid_row(**{"Bid Strategy Type": "Experimental Strategy"}),
        2,
    )

    assert "unsupported_bid_strategy" in issue_types(issues)


def test_rejects_invalid_max_cpc():
    issues = SearchBidStrategyValidator().validate_bid_strategy_row(bid_row(**{"Max CPC": "free"}), 2)

    assert "invalid_max_cpc" in issue_types(issues)


def test_rejects_zero_target_cpa():
    issues = SearchBidStrategyValidator().validate_bid_strategy_row(bid_row(**{"Target CPA": "0"}), 2)

    assert "invalid_target_cpa" in issue_types(issues)


def test_warns_when_strategy_name_has_no_type():
    issues = SearchBidStrategyValidator().validate_bid_strategy_row(
        bid_row(**{"Bid Strategy Type": "", "Bid Strategy Name": "Portfolio"}),
        2,
    )

    assert "name_without_bid_strategy_type" in issue_types(issues)
