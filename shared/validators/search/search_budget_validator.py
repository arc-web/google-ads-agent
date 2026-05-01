#!/usr/bin/env python3
"""Validate Search campaign budget rows for the active workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


VALID_BUDGET_TYPES = {"Daily"}
VALID_STATUSES = {"Enabled", "Paused", "Removed"}


@dataclass
class ValidationIssue:
    """Represents a validation issue found during Search budget validation."""

    level: str
    severity: str
    row_number: int
    column: str
    issue_type: str
    message: str
    suggestion: str = ""
    auto_fixable: bool = False


class SearchBudgetValidator:
    """
    Validates Search campaign budget rows.

    The validator checks import safety and active staging headers only. It does
    not enforce account-specific minimums, caps, or spend strategy.
    """

    def __init__(self, validation_rules: dict[str, Any] | None = None):
        rules = validation_rules or {}
        self.valid_budget_types = set(rules.get("valid_budget_types", VALID_BUDGET_TYPES))
        self.valid_statuses = set(rules.get("valid_statuses", VALID_STATUSES))

    def _issue(
        self,
        severity: str,
        row_number: int,
        column: str,
        issue_type: str,
        message: str,
        suggestion: str = "",
    ) -> ValidationIssue:
        return ValidationIssue(
            level="budget",
            severity=severity,
            row_number=row_number,
            column=column,
            issue_type=issue_type,
            message=message,
            suggestion=suggestion,
        )

    def _value(self, row: dict[str, Any], *headers: str) -> str:
        for header in headers:
            value = row.get(header)
            if value is not None and str(value).strip():
                return str(value).strip()
        return ""

    def validate_budget_row(self, row: dict[str, Any], row_number: int) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        campaign = self._value(row, "Campaign")
        campaign_type = self._value(row, "Campaign Type", "Campaign type")
        budget = self._value(row, "Budget")
        budget_type = self._value(row, "Budget type", "Budget Type")
        status = self._value(row, "Status", "Campaign Status", "Campaign status")

        if not campaign:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Campaign",
                    "missing_campaign",
                    "Budget row is missing Campaign.",
                    "Populate Campaign on every campaign budget row.",
                )
            )

        if campaign_type and campaign_type != "Search":
            issues.append(
                self._issue(
                    "warning",
                    row_number,
                    "Campaign Type",
                    "non_search_campaign_type",
                    f'Campaign Type "{campaign_type}" is outside this Search validator.',
                    "Route non-Search rows to the matching validator.",
                )
            )

        if not budget:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Budget",
                    "missing_budget",
                    "Search campaign row is missing Budget.",
                    "Populate a positive numeric daily budget.",
                )
            )
        else:
            issues.extend(self._validate_budget_amount(budget, row_number))

        if not budget_type:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Budget type",
                    "missing_budget_type",
                    "Search campaign row is missing Budget type.",
                    'Use "Daily" for the active Google Ads Editor staging format.',
                )
            )
        elif budget_type not in self.valid_budget_types:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Budget type",
                    "invalid_budget_type",
                    f'Budget type "{budget_type}" is not active in this workflow.',
                    f"Use one of: {', '.join(sorted(self.valid_budget_types))}.",
                )
            )

        if status and status not in self.valid_statuses:
            issues.append(
                self._issue(
                    "warning",
                    row_number,
                    "Status",
                    "invalid_campaign_status",
                    f'Campaign status "{status}" is not standard.',
                    f"Use one of: {', '.join(sorted(self.valid_statuses))}.",
                )
            )

        return issues

    def _validate_budget_amount(self, budget: str, row_number: int) -> list[ValidationIssue]:
        try:
            budget_value = float(budget.replace("$", "").replace(",", ""))
        except ValueError:
            return [
                self._issue(
                    "critical",
                    row_number,
                    "Budget",
                    "invalid_budget_format",
                    f'Budget "{budget}" is not numeric.',
                    "Use numeric format such as 25.00.",
                )
            ]

        if budget_value <= 0:
            return [
                self._issue(
                    "critical",
                    row_number,
                    "Budget",
                    "budget_not_positive",
                    "Budget must be greater than zero.",
                    "Use a positive numeric budget.",
                )
            ]

        return []

    def validate_budget_data(self, budget_rows: list[dict[str, Any]]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for index, row in enumerate(budget_rows, start=2):
            issues.extend(self.validate_budget_row(row, index))
        return issues
