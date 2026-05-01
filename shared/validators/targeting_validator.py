#!/usr/bin/env python3
"""Generic targeting checks for active Google Ads Editor staging files."""

from __future__ import annotations

import csv
import io
from typing import Any


class TargetingValidator:
    """Validate location and radius targeting without hard-coded client geography."""

    def validate_targeting(self, csv_path: str, csv_content: str) -> list[dict[str, Any]]:
        """Validate targeting fields used by active staging CSVs."""
        del csv_path
        issues: list[dict[str, Any]] = []

        try:
            reader = csv.DictReader(io.StringIO(csv_content), delimiter="\t")
            for row_num, row in enumerate(reader, start=2):
                issues.extend(self._validate_location_row(row, row_num))
                issues.extend(self._validate_radius_row(row, row_num))
                issues.extend(self._validate_bid_modifier(row, row_num))
        except Exception as exc:
            issues.append(self._issue("critical", 0, "", "validation_error", f"Failed targeting validation: {exc}"))

        return issues

    def _validate_location_row(self, row: dict[str, str], row_num: int) -> list[dict[str, Any]]:
        location = row.get("Location", "").strip()
        location_id = row.get("Location ID", "").strip()
        if location and not location_id and not row.get("Radius", "").strip():
            return [
                self._issue(
                    "warning",
                    row_num,
                    "Location ID",
                    "location_id_preferred",
                    "Location rows should use Location ID when available.",
                )
            ]
        return []

    def _validate_radius_row(self, row: dict[str, str], row_num: int) -> list[dict[str, Any]]:
        radius = row.get("Radius", "").strip()
        if not radius:
            return []

        try:
            if float(radius) <= 0:
                return [self._issue("error", row_num, "Radius", "radius_positive", "Radius must be greater than zero.")]
        except ValueError:
            return [self._issue("error", row_num, "Radius", "radius_numeric", f"Radius is not numeric: {radius}")]

        return []

    def _validate_bid_modifier(self, row: dict[str, str], row_num: int) -> list[dict[str, Any]]:
        bid_modifier = row.get("Bid Modifier", "").strip()
        if not bid_modifier:
            return []

        try:
            if float(bid_modifier) <= 0:
                return [
                    self._issue(
                        "error",
                        row_num,
                        "Bid Modifier",
                        "bid_modifier_positive",
                        "Bid Modifier must be greater than zero when provided.",
                    )
                ]
        except ValueError:
            return [
                self._issue(
                    "error",
                    row_num,
                    "Bid Modifier",
                    "bid_modifier_numeric",
                    f"Bid Modifier is not numeric: {bid_modifier}",
                )
            ]

        return []

    @staticmethod
    def _issue(severity: str, row: int, column: str, issue_type: str, message: str) -> dict[str, Any]:
        return {
            "level": "targeting",
            "severity": severity,
            "row_number": row,
            "column": column,
            "issue_type": issue_type,
            "message": message,
            "auto_fixable": False,
        }
