#!/usr/bin/env python3
"""Validate Search location rows for the active Google Ads Agent workflow."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any


VALID_STATUSES = {"Enabled", "Paused", "Removed"}
VALID_RADIUS_UNITS = {"mi", "mile", "miles", "km", "kilometer", "kilometers"}
MAX_LOCATION_NAME_LENGTH = 255


@dataclass
class ValidationIssue:
    """Represents a validation issue found during Search location validation."""

    level: str
    severity: str
    row_number: int
    column: str
    issue_type: str
    message: str
    suggestion: str = ""
    auto_fixable: bool = False


class SearchLocationValidator:
    """
    Validates Search location rows without client or market assumptions.

    Active workflow rules prefer Google Ads Editor Location ID values when
    available, allow radius targets, and keep client service-area decisions out
    of shared validation code.
    """

    def __init__(self, validation_rules: dict[str, Any] | None = None):
        rules = validation_rules or {}
        self.valid_statuses = set(rules.get("valid_statuses", VALID_STATUSES))
        self.valid_radius_units = set(rules.get("valid_radius_units", VALID_RADIUS_UNITS))
        self.max_location_name_length = int(rules.get("max_location_name_length", MAX_LOCATION_NAME_LENGTH))

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
            level="location",
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

    def validate_location_row(self, row: dict[str, Any], row_number: int) -> list[ValidationIssue]:
        """
        Validate a single location row for Search campaign staging.

        Args:
            row: Dictionary representing a CSV row.
            row_number: Row number in the CSV for error reporting.

        Returns:
            List of validation issues found.
        """
        issues: list[ValidationIssue] = []

        campaign = self._value(row, "Campaign")
        location = self._value(row, "Location")
        location_id = self._value(row, "Location ID", "Location id")
        radius = self._value(row, "Radius")
        unit = self._value(row, "Unit", "Radius unit", "Radius Unit")
        status = self._value(row, "Status", "Location status", "Location Status")

        if not campaign:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Campaign",
                    "missing_campaign",
                    "Location row is missing Campaign.",
                    "Populate Campaign on every location row.",
                )
            )

        if not location and not location_id and not radius:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Location",
                    "missing_location_target",
                    "Location row has no location name, Location ID, or radius target.",
                    "Populate Location, Location ID, or Radius before import.",
                )
            )

        if location and len(location) > self.max_location_name_length:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Location",
                    "location_name_too_long",
                    f"Location text is {len(location)} characters.",
                    f"Keep Location text to {self.max_location_name_length} characters or fewer.",
                )
            )

        if location_id and not location_id.isdigit():
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Location ID",
                    "invalid_location_id",
                    f'Location ID "{location_id}" must be numeric.',
                    "Use the numeric Google geo target ID when available.",
                )
            )
        elif location and not location_id and not radius:
            issues.append(
                self._issue(
                    "warning",
                    row_number,
                    "Location ID",
                    "location_id_preferred",
                    "Location row is missing Location ID.",
                    "Add Location ID when available for safer Google Ads Editor imports.",
                )
            )

        if radius:
            issues.extend(self._validate_radius(radius, unit, row_number))

        if unit and not radius:
            issues.append(
                self._issue(
                    "warning",
                    row_number,
                    "Unit",
                    "unit_without_radius",
                    "Radius unit is populated without Radius.",
                    "Remove Unit or populate Radius.",
                )
            )

        if status and status not in self.valid_statuses:
            issues.append(
                self._issue(
                    "warning",
                    row_number,
                    "Status",
                    "invalid_location_status",
                    f'Location status "{status}" is not standard.',
                    f"Use one of: {', '.join(sorted(self.valid_statuses))}.",
                )
            )

        return issues

    def _validate_radius(self, radius: str, unit: str, row_number: int) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        try:
            radius_value = float(radius.replace(",", ""))
        except ValueError:
            return [
                self._issue(
                    "critical",
                    row_number,
                    "Radius",
                    "invalid_radius_format",
                    f'Radius "{radius}" is not numeric.',
                    "Use a positive numeric radius.",
                )
            ]

        if radius_value <= 0:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Radius",
                    "radius_not_positive",
                    "Radius must be greater than zero.",
                    "Use a positive numeric radius.",
                )
            )

        if unit and unit.lower() not in self.valid_radius_units:
            issues.append(
                self._issue(
                    "warning",
                    row_number,
                    "Unit",
                    "invalid_radius_unit",
                    f'Radius unit "{unit}" is not standard.',
                    f"Use one of: {', '.join(sorted(self.valid_radius_units))}.",
                )
            )

        return issues

    def validate_location_data(self, location_rows: list[dict[str, Any]]) -> list[ValidationIssue]:
        """
        Validate location rows across a staging file.

        Args:
            location_rows: List of location row dictionaries.

        Returns:
            List of validation issues found.
        """
        issues: list[ValidationIssue] = []
        seen_by_campaign: dict[str, set[str]] = defaultdict(set)

        for index, row in enumerate(location_rows, start=2):
            issues.extend(self.validate_location_row(row, index))

            campaign = self._value(row, "Campaign") or "(missing campaign)"
            key = self._location_key(row)
            if not key:
                continue

            if key in seen_by_campaign[campaign]:
                issues.append(
                    self._issue(
                        "warning",
                        index,
                        "Location",
                        "duplicate_location_target",
                        f'Duplicate location target "{key}" in campaign "{campaign}".',
                        "Keep one row per campaign location target.",
                    )
                )
            else:
                seen_by_campaign[campaign].add(key)

        return issues

    def _location_key(self, row: dict[str, Any]) -> str:
        location_id = self._value(row, "Location ID", "Location id")
        if location_id:
            return f"id:{location_id}"

        radius = self._value(row, "Radius")
        location = self._value(row, "Location")
        if radius:
            unit = self._value(row, "Unit", "Radius unit", "Radius Unit").lower()
            return f"radius:{location.lower()}:{radius}:{unit}"

        return f"location:{location.lower()}" if location else ""
