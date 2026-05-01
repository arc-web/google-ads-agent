#!/usr/bin/env python3
"""Validate Search bid strategy rows for the active workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


VALID_BID_STRATEGIES = {
    "Manual CPC",
    "Maximize conversions",
    "Maximize clicks",
    "Target CPA",
    "Target ROAS",
    "Target impression share",
    "Enhanced CPC",
}
VALID_ENHANCED_CPC_VALUES = {"Enabled", "Disabled", "On", "Off", "Yes", "No", "True", "False"}


@dataclass
class ValidationIssue:
    """Represents a validation issue found during Search bid strategy validation."""

    level: str
    severity: str
    row_number: int
    column: str
    issue_type: str
    message: str
    suggestion: str = ""
    auto_fixable: bool = False


class SearchBidStrategyValidator:
    """
    Validates bid strategy rows without making client-specific strategy calls.

    This validator checks recognized structural fields and numeric bid inputs. It
    does not decide which bidding model is right for a client.
    """

    def __init__(self, validation_rules: dict[str, Any] | None = None):
        rules = validation_rules or {}
        self.valid_bid_strategies = set(rules.get("valid_bid_strategies", VALID_BID_STRATEGIES))
        self.valid_enhanced_cpc_values = set(rules.get("valid_enhanced_cpc_values", VALID_ENHANCED_CPC_VALUES))

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
            level="bid_strategy",
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

    def validate_bid_strategy_row(self, row: dict[str, Any], row_number: int) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        campaign = self._value(row, "Campaign")
        bid_strategy = self._value(row, "Bid Strategy Type", "Campaign Bid Strategy Type")
        bid_strategy_name = self._value(row, "Bid Strategy Name", "Campaign Bid Strategy Name")
        max_cpc = self._value(row, "Max CPC", "CPC bid")
        target_cpa = self._value(row, "Target CPA")
        target_roas = self._value(row, "Target ROAS")
        enhanced_cpc = self._value(row, "Enhanced CPC")

        if not campaign:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Campaign",
                    "missing_campaign",
                    "Bid strategy row is missing Campaign.",
                    "Populate Campaign on every bid strategy row.",
                )
            )

        if bid_strategy and bid_strategy not in self.valid_bid_strategies:
            issues.append(
                self._issue(
                    "warning",
                    row_number,
                    "Bid Strategy Type",
                    "unsupported_bid_strategy",
                    f'Bid Strategy Type "{bid_strategy}" is not in the shared validator allow-list.',
                    "Confirm the value is valid for Google Ads Editor or add it to the validator rules.",
                )
            )

        if bid_strategy_name and not bid_strategy:
            issues.append(
                self._issue(
                    "warning",
                    row_number,
                    "Bid Strategy Name",
                    "name_without_bid_strategy_type",
                    "Bid Strategy Name is populated without Bid Strategy Type.",
                    "Populate Bid Strategy Type or remove the strategy name.",
                )
            )

        if max_cpc:
            issues.extend(self._validate_positive_money(max_cpc, "Max CPC", "invalid_max_cpc", row_number))
        if target_cpa:
            issues.extend(self._validate_positive_money(target_cpa, "Target CPA", "invalid_target_cpa", row_number))
        if target_roas:
            issues.extend(self._validate_positive_number(target_roas, "Target ROAS", "invalid_target_roas", row_number))

        if enhanced_cpc and enhanced_cpc not in self.valid_enhanced_cpc_values:
            issues.append(
                self._issue(
                    "warning",
                    row_number,
                    "Enhanced CPC",
                    "invalid_enhanced_cpc",
                    f'Enhanced CPC value "{enhanced_cpc}" is not standard.',
                    f"Use one of: {', '.join(sorted(self.valid_enhanced_cpc_values))}.",
                )
            )

        return issues

    def _validate_positive_money(
        self,
        value: str,
        column: str,
        issue_type: str,
        row_number: int,
    ) -> list[ValidationIssue]:
        return self._validate_positive_number(value.replace("$", "").replace(",", ""), column, issue_type, row_number)

    def _validate_positive_number(
        self,
        value: str,
        column: str,
        issue_type: str,
        row_number: int,
    ) -> list[ValidationIssue]:
        try:
            number = float(value.replace("%", "").replace(",", ""))
        except ValueError:
            return [
                self._issue(
                    "critical",
                    row_number,
                    column,
                    issue_type,
                    f'{column} "{value}" is not numeric.',
                    "Use a positive numeric value.",
                )
            ]

        if number <= 0:
            return [
                self._issue(
                    "critical",
                    row_number,
                    column,
                    issue_type,
                    f"{column} must be greater than zero.",
                    "Use a positive numeric value.",
                )
            ]

        return []

    def validate_bid_strategy_data(self, bid_strategy_rows: list[dict[str, Any]]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for index, row in enumerate(bid_strategy_rows, start=2):
            issues.extend(self.validate_bid_strategy_row(row, index))
        return issues
