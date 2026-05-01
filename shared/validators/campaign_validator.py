#!/usr/bin/env python3
"""Generic campaign-level checks for active Google Ads Editor staging files."""

from __future__ import annotations

import csv
import io
from typing import Any


OFF_VALUES = {"Off", "Disabled", "No", "False", "0"}
SEARCH_NETWORK_VALUES = {"Google search", "Search"}


class CampaignValidator:
    """Validate campaign rows without imposing client-specific strategy."""

    def validate_campaign_settings(self, csv_path: str, csv_content: str) -> list[dict[str, Any]]:
        """Validate active Search campaign settings."""
        del csv_path
        issues: list[dict[str, Any]] = []

        try:
            reader = csv.DictReader(io.StringIO(csv_content), delimiter="\t")
            for row_num, row in enumerate(reader, start=2):
                if row.get("Campaign Type", "").strip() != "Search":
                    continue

                issues.extend(self._validate_search_campaign_row(row, row_num))
        except Exception as exc:
            issues.append(self._issue("critical", 0, "", "validation_error", f"Failed campaign validation: {exc}"))

        return issues

    def _validate_search_campaign_row(self, row: dict[str, str], row_num: int) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []

        budget = row.get("Budget", "").strip()
        if budget:
            try:
                if float(budget.replace(",", "")) <= 0:
                    issues.append(self._issue("error", row_num, "Budget", "budget_positive", "Budget must be greater than zero."))
            except ValueError:
                issues.append(self._issue("error", row_num, "Budget", "budget_numeric", f"Budget is not numeric: {budget}"))

        budget_type = row.get("Budget type", "").strip()
        if budget_type and budget_type not in {"Daily", "Monthly"}:
            issues.append(
                self._issue("error", row_num, "Budget type", "invalid_budget_type", f"Unsupported Budget type: {budget_type}")
            )

        networks = row.get("Networks", "").strip()
        if networks and networks not in SEARCH_NETWORK_VALUES:
            issues.append(
                self._issue("error", row_num, "Networks", "search_network", f"Unsupported Search network value: {networks}")
            )

        eu_political_ads = row.get("EU political ads", "").strip()
        if not eu_political_ads:
            issues.append(
                self._issue(
                    "error",
                    row_num,
                    "EU political ads",
                    "eu_political_ads_required",
                    "Search campaign rows must populate EU political ads.",
                )
            )

        broad_match = row.get("Broad match keywords", "").strip()
        if broad_match and broad_match not in OFF_VALUES:
            issues.append(
                self._issue(
                    "error",
                    row_num,
                    "Broad match keywords",
                    "broad_match_off",
                    "Broad match keywords must be off for the active phrase-only workflow.",
                )
            )

        return issues

    @staticmethod
    def _issue(severity: str, row: int, column: str, issue_type: str, message: str) -> dict[str, Any]:
        return {
            "level": "campaign",
            "severity": severity,
            "row_number": row,
            "column": column,
            "issue_type": issue_type,
            "message": message,
            "auto_fixable": False,
        }
