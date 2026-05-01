#!/usr/bin/env python3
"""Validate Search campaign rows for the active Google Ads Agent workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SEARCH_NETWORK_VALUES = {"Google search", "Search"}
OFF_VALUES = {"Off", "Disabled", "No", "False", "0"}
VALID_CAMPAIGN_STATUSES = {"Enabled", "Paused", "Removed"}


@dataclass
class ValidationIssue:
    """Represents a validation issue found during Search campaign validation."""

    level: str
    severity: str
    row_number: int
    column: str
    issue_type: str
    message: str
    suggestion: str = ""
    auto_fixable: bool = False


class SearchCampaignValidator:
    """
    Validates campaign-level Search rows without client-specific assumptions.

    This is a legacy wrapper kept for older imports. It follows the same active
    staging rules used by the rebuild validator: Search campaigns, Search
    network, positive budgets, broad match off, and EU political ads populated.
    """

    def __init__(self, validation_rules: dict[str, Any] | None = None):
        rules = validation_rules or {}
        self.search_network_values = set(rules.get("search_network_values", SEARCH_NETWORK_VALUES))
        self.off_values = set(rules.get("off_values", OFF_VALUES))
        self.valid_campaign_statuses = set(rules.get("valid_campaign_statuses", VALID_CAMPAIGN_STATUSES))

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
            level="campaign",
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

    def validate_campaign_row(self, row: dict[str, Any], row_number: int) -> list[ValidationIssue]:
        """Validate a single Search campaign row."""
        issues: list[ValidationIssue] = []

        campaign = self._value(row, "Campaign")
        campaign_type = self._value(row, "Campaign Type", "Campaign type")
        networks = self._value(row, "Networks")
        budget = self._value(row, "Budget")
        budget_type = self._value(row, "Budget type", "Budget Type")
        eu_political_ads = self._value(row, "EU political ads", "EU Political Ads")
        broad_match = self._value(row, "Broad match keywords", "Broad Match Keywords")
        status = self._value(row, "Status", "Campaign status", "Campaign Status")

        if not campaign:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Campaign",
                    "missing_campaign",
                    "Campaign row is missing Campaign.",
                    "Populate Campaign on every campaign row.",
                )
            )

        if campaign_type and campaign_type != "Search":
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Campaign Type",
                    "unsupported_campaign_type",
                    f'Campaign Type "{campaign_type}" is not supported by this Search validator.',
                    'Use "Search" for Search campaign staging rows.',
                )
            )

        if not networks:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Networks",
                    "missing_networks",
                    "Search campaign row is missing Networks.",
                    'Use "Google search" or "Search".',
                )
            )
        elif networks not in self.search_network_values:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Networks",
                    "search_network",
                    f'Networks "{networks}" is not supported for the active Search workflow.',
                    f"Use one of: {', '.join(sorted(self.search_network_values))}.",
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
                    "Populate a positive daily budget before staging.",
                )
            )
        else:
            try:
                if float(budget.replace("$", "").replace(",", "")) <= 0:
                    issues.append(
                        self._issue(
                            "critical",
                            row_number,
                            "Budget",
                            "budget_positive",
                            "Campaign budget must be greater than zero.",
                            "Use a positive numeric budget.",
                        )
                    )
            except ValueError:
                issues.append(
                    self._issue(
                        "critical",
                        row_number,
                        "Budget",
                        "budget_numeric",
                        f'Campaign budget "{budget}" is not numeric.',
                        "Use numeric format such as 25.00.",
                    )
                )

        if budget_type and budget_type != "Daily":
            issues.append(
                self._issue(
                    "warning",
                    row_number,
                    "Budget type",
                    "non_daily_budget",
                    f'Budget type "{budget_type}" is not the expected daily staging format.',
                    'Use "Daily" unless the build intentionally uses another budget type.',
                )
            )

        if not eu_political_ads:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "EU political ads",
                    "eu_political_ads_required",
                    "Campaign row must populate EU political ads.",
                    "Set the Google Ads Editor EU political ads value before import.",
                )
            )

        if broad_match and broad_match not in self.off_values:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Broad match keywords",
                    "broad_match_off",
                    "Broad match keywords must be off for the current phrase-only workflow.",
                    f"Use one of: {', '.join(sorted(self.off_values))}.",
                )
            )

        if status and status not in self.valid_campaign_statuses:
            issues.append(
                self._issue(
                    "warning",
                    row_number,
                    "Status",
                    "invalid_campaign_status",
                    f'Campaign status "{status}" is not standard.',
                    f"Use one of: {', '.join(sorted(self.valid_campaign_statuses))}.",
                )
            )

        return issues

    def validate_campaign_data(self, campaign_rows: list[dict[str, Any]]) -> list[ValidationIssue]:
        """Validate campaign-level data across multiple rows."""
        issues: list[ValidationIssue] = []
        seen_campaigns: set[str] = set()

        for index, row in enumerate(campaign_rows, start=2):
            issues.extend(self.validate_campaign_row(row, index))
            campaign = self._value(row, "Campaign")
            if not campaign:
                continue
            if campaign in seen_campaigns:
                issues.append(
                    self._issue(
                        "warning",
                        index,
                        "Campaign",
                        "duplicate_campaign_row",
                        f'Duplicate campaign row for "{campaign}".',
                        "Keep one campaign settings row per campaign unless the duplicate is intentional.",
                    )
                )
            else:
                seen_campaigns.add(campaign)

        return issues

    def validate_search_campaign_row(
        self, client_name: str, csv_path: str, row: dict[str, Any], row_num: int
    ) -> None:
        """Legacy mutating API retained for old callers."""
        if not hasattr(self, "issues"):
            self.issues = []
        self.issues.extend(self.validate_campaign_row(row, row_num))

    def get_validation_report(self) -> dict[str, Any]:
        """Return issues collected through the legacy mutating API."""
        issues = list(getattr(self, "issues", []))
        return {
            "total_issues": len(issues),
            "critical": len([issue for issue in issues if issue.severity == "critical"]),
            "errors": len([issue for issue in issues if issue.severity == "error"]),
            "warnings": len([issue for issue in issues if issue.severity == "warning"]),
            "info": len([issue for issue in issues if issue.severity == "info"]),
            "issues": [issue.__dict__ for issue in issues],
        }
