from __future__ import annotations

from shared.validators.search.search_budget_validator import SearchBudgetValidator


def issue_types(issues):
    return {issue.issue_type for issue in issues}


def budget_row(**overrides):
    row = {
        "Campaign": "ARC - Search - Testing - V1",
        "Campaign Type": "Search",
        "Budget": "25.00",
        "Budget type": "Daily",
        "Status": "Enabled",
    }
    row.update(overrides)
    return row


def test_accepts_positive_daily_budget():
    issues = SearchBudgetValidator().validate_budget_row(budget_row(), 2)

    assert issues == []


def test_rejects_missing_budget():
    issues = SearchBudgetValidator().validate_budget_row(budget_row(Budget=""), 2)

    assert "missing_budget" in issue_types(issues)


def test_rejects_non_numeric_budget():
    issues = SearchBudgetValidator().validate_budget_row(budget_row(Budget="not money"), 2)

    assert "invalid_budget_format" in issue_types(issues)


def test_rejects_zero_budget():
    issues = SearchBudgetValidator().validate_budget_row(budget_row(Budget="0"), 2)

    assert "budget_not_positive" in issue_types(issues)


def test_rejects_old_monthly_budget_type():
    issues = SearchBudgetValidator().validate_budget_row(budget_row(**{"Budget type": "Monthly"}), 2)

    assert "invalid_budget_type" in issue_types(issues)
