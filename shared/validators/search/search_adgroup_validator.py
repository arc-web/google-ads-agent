#!/usr/bin/env python3
"""Validate Search ad group rows for the active Google Ads Agent workflow."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any


VALID_STATUSES = {"Enabled", "Paused", "Removed"}
MAX_AD_GROUP_NAME_LENGTH = 255
MAX_LABELS = 10
MIN_CPC = 0.01
MAX_CPC = 50.00


@dataclass
class ValidationIssue:
    """Represents a validation issue found during Search ad group validation."""

    level: str
    severity: str
    row_number: int
    column: str
    issue_type: str
    message: str
    suggestion: str = ""
    auto_fixable: bool = False


class SearchAdGroupValidator:
    """
    Validates Search ad group rows without account-specific assumptions.

    This validator checks structural safety for the current Google Ads Editor
    staging format. It does not force a minimum number of ad groups, naming
    style, industry language, or one-account campaign architecture.
    """

    def __init__(self, validation_rules: dict[str, Any] | None = None):
        rules = validation_rules or {}
        self.valid_statuses = set(rules.get("valid_statuses", VALID_STATUSES))
        self.max_ad_group_name_length = int(rules.get("max_ad_group_name_length", MAX_AD_GROUP_NAME_LENGTH))
        self.max_labels = int(rules.get("max_labels", MAX_LABELS))
        self.min_cpc = float(rules.get("min_cpc", MIN_CPC))
        self.max_cpc = float(rules.get("max_cpc", MAX_CPC))

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
            level="adgroup",
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

    def validate_adgroup_row(self, row: dict[str, Any], row_number: int) -> list[ValidationIssue]:
        """
        Validate a single ad group row for Search campaign compliance.

        Args:
            row: Dictionary representing a CSV row.
            row_number: Row number in the CSV for error reporting.

        Returns:
            List of validation issues found.
        """
        issues: list[ValidationIssue] = []

        campaign = self._value(row, "Campaign")
        ad_group = self._value(row, "Ad Group", "Ad group")
        status = self._value(row, "Status", "Ad group status", "Ad Group status")

        if not campaign:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Campaign",
                    "missing_campaign",
                    "Ad group row is missing Campaign.",
                    "Populate Campaign on every ad group row.",
                )
            )

        if not ad_group:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Ad Group",
                    "missing_adgroup_name",
                    "Ad group name is required.",
                    "Populate Ad Group on every ad group row.",
                )
            )
        elif len(ad_group) > self.max_ad_group_name_length:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Ad Group",
                    "adgroup_name_too_long",
                    f'Ad group name "{ad_group}" is {len(ad_group)} characters.',
                    f"Shorten ad group name to {self.max_ad_group_name_length} characters or fewer.",
                )
            )

        if status and status not in self.valid_statuses:
            issues.append(
                self._issue(
                    "warning",
                    row_number,
                    "Status",
                    "invalid_adgroup_status",
                    f'Ad group status "{status}" is not standard.',
                    f"Use one of: {', '.join(sorted(self.valid_statuses))}.",
                )
            )

        max_cpc = self._value(row, "Ad group max CPC", "Max CPC", "CPC bid")
        if max_cpc:
            issues.extend(self._validate_cpc(max_cpc, row_number))

        labels = self._value(row, "Ad group labels", "Labels")
        if labels:
            label_list = [label.strip() for label in labels.split(",") if label.strip()]
            if len(label_list) > self.max_labels:
                issues.append(
                    self._issue(
                        "info",
                        row_number,
                        "Labels",
                        "too_many_labels",
                        f"Ad group has {len(label_list)} labels.",
                        f"Keep labels to {self.max_labels} or fewer when possible.",
                    )
                )

        return issues

    def _validate_cpc(self, cpc_text: str, row_number: int) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        try:
            cpc = float(cpc_text.replace("$", "").replace(",", ""))
        except ValueError:
            return [
                self._issue(
                    "critical",
                    row_number,
                    "Max CPC",
                    "invalid_cpc_format",
                    f'Invalid Max CPC format: "{cpc_text}".',
                    "Use numeric format such as 2.50 or $2.50.",
                )
            ]

        if cpc < self.min_cpc:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Max CPC",
                    "cpc_too_low",
                    f"Max CPC ${cpc:.2f} is below minimum ${self.min_cpc:.2f}.",
                    f"Increase Max CPC to at least ${self.min_cpc:.2f}.",
                )
            )
        elif cpc > self.max_cpc:
            issues.append(
                self._issue(
                    "warning",
                    row_number,
                    "Max CPC",
                    "cpc_too_high",
                    f"Max CPC ${cpc:.2f} is above ${self.max_cpc:.2f}.",
                    "Review the bid before importing.",
                )
            )

        return issues

    def validate_adgroup_data(self, adgroup_rows: list[dict[str, Any]]) -> list[ValidationIssue]:
        """
        Validate ad group-level data across multiple rows.

        Args:
            adgroup_rows: List of ad group row dictionaries.

        Returns:
            List of validation issues found.
        """
        issues: list[ValidationIssue] = []

        if not adgroup_rows:
            return issues

        campaign_adgroups: dict[str, set[str]] = defaultdict(set)

        for index, row in enumerate(adgroup_rows, start=2):
            issues.extend(self.validate_adgroup_row(row, index))

            campaign = self._value(row, "Campaign") or "(missing campaign)"
            ad_group = self._value(row, "Ad Group", "Ad group")
            if not ad_group:
                continue

            if ad_group in campaign_adgroups[campaign]:
                issues.append(
                    self._issue(
                        "warning",
                        index,
                        "Ad Group",
                        "duplicate_adgroup_name",
                        f'Duplicate ad group name "{ad_group}" in campaign "{campaign}".',
                        "Use unique ad group names within each campaign.",
                    )
                )
            else:
                campaign_adgroups[campaign].add(ad_group)

        return issues
