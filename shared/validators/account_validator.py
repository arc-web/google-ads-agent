#!/usr/bin/env python3
"""Generic account-level checks for active Google Ads Editor staging files."""

from __future__ import annotations

import csv
import io
from typing import Any

from shared.rebuild.staging_validator import REQUIRED_HEADERS, REQUIRED_RSA_DESCRIPTIONS, REQUIRED_RSA_HEADLINES


class AccountValidator:
    """Validate file-level structure without assuming a client directory layout."""

    def __init__(self) -> None:
        self.required_headers = list(REQUIRED_HEADERS)
        for header in REQUIRED_RSA_HEADLINES + REQUIRED_RSA_DESCRIPTIONS:
            if header not in self.required_headers:
                self.required_headers.append(header)

        self.valid_campaign_types = {"Search", "Performance Max", "Display Network only", "Shopping", "Video"}
        self.valid_budget_types = {"Daily", "Monthly"}

    def validate_csv_structure(self, csv_path: str, csv_content: str) -> list[dict[str, Any]]:
        """Validate active Google Ads Editor staging headers."""
        del csv_path
        issues: list[dict[str, Any]] = []

        try:
            reader = csv.DictReader(io.StringIO(csv_content), delimiter="\t")
            headers = list(reader.fieldnames or [])
        except Exception as exc:
            return [self._issue("critical", 0, "", "structure_error", f"Failed to read CSV structure: {exc}")]

        if not headers:
            return [self._issue("critical", 0, "", "missing_headers", "CSV has no header row.")]

        empty_headers = [index + 1 for index, header in enumerate(headers) if not (header or "").strip()]
        if empty_headers:
            issues.append(
                self._issue(
                    "error",
                    0,
                    f"Column {empty_headers[0]}",
                    "empty_headers",
                    f"CSV has empty headers at positions: {empty_headers}",
                )
            )

        missing_headers = [header for header in self.required_headers if header not in headers]
        if missing_headers:
            issues.append(
                self._issue(
                    "critical",
                    0,
                    "",
                    "missing_headers",
                    f"Missing active staging headers: {missing_headers}",
                )
            )

        return issues

    def validate_account_settings(self, csv_path: str, csv_content: str) -> list[dict[str, Any]]:
        """Validate row-level account fields common to active staging files."""
        del csv_path
        issues: list[dict[str, Any]] = []

        try:
            reader = csv.DictReader(io.StringIO(csv_content), delimiter="\t")
            for row_num, row in enumerate(reader, start=2):
                if not any((value or "").strip() for value in row.values()):
                    continue

                campaign = row.get("Campaign", "").strip()
                if not campaign:
                    issues.append(
                        self._issue("critical", row_num, "Campaign", "missing_campaign_name", "Row is missing Campaign.")
                    )

                campaign_type = row.get("Campaign Type", "").strip()
                if campaign_type and campaign_type not in self.valid_campaign_types:
                    issues.append(
                        self._issue(
                            "error",
                            row_num,
                            "Campaign Type",
                            "invalid_campaign_type",
                            f"Unsupported Campaign Type: {campaign_type}",
                        )
                    )

                budget_type = row.get("Budget type", "").strip()
                if budget_type and budget_type not in self.valid_budget_types:
                    issues.append(
                        self._issue(
                            "error",
                            row_num,
                            "Budget type",
                            "invalid_budget_type",
                            f"Unsupported Budget type: {budget_type}",
                        )
                    )
        except Exception as exc:
            issues.append(self._issue("critical", 0, "", "validation_error", f"Failed account validation: {exc}"))

        return issues

    @staticmethod
    def _issue(severity: str, row: int, column: str, issue_type: str, message: str) -> dict[str, Any]:
        return {
            "level": "account",
            "severity": severity,
            "row_number": row,
            "column": column,
            "issue_type": issue_type,
            "message": message,
            "auto_fixable": False,
        }
