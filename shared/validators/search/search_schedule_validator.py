#!/usr/bin/env python3
"""Validate Search ad schedule rows for the active workflow."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


VALID_DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
SCHEDULE_PART = re.compile(
    r"^\(?(?P<day>[A-Za-z]+)(?:\[(?P<bracket_start>\d{1,2}:\d{2})-(?P<bracket_end>\d{1,2}:\d{2})\]|\s+(?P<plain_start>\d{1,2}(?::\d{2})?)-(?P<plain_end>\d{1,2}(?::\d{2})?))\)?$"
)


@dataclass
class ValidationIssue:
    """Represents a validation issue found during Search schedule validation."""

    level: str
    severity: str
    row_number: int
    column: str
    issue_type: str
    message: str
    suggestion: str = ""
    auto_fixable: bool = False


class SearchScheduleValidator:
    """
    Validates optional Search ad schedules.

    Empty schedules are allowed because always-on delivery can be represented by
    leaving the schedule blank. Populated schedules must use parseable day and
    time windows.
    """

    def __init__(self, validation_rules: dict[str, Any] | None = None):
        rules = validation_rules or {}
        self.valid_days = set(rules.get("valid_days", VALID_DAYS))

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
            level="schedule",
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

    def validate_schedule_row(self, row: dict[str, Any], row_number: int) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        campaign = self._value(row, "Campaign")
        schedule = self._value(row, "Ad Schedule", "Ad schedule")

        if schedule and not campaign:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Campaign",
                    "missing_campaign",
                    "Ad schedule row is missing Campaign.",
                    "Populate Campaign on every ad schedule row.",
                )
            )

        if not schedule:
            return issues

        for part in [piece.strip() for piece in schedule.split(";") if piece.strip()]:
            issues.extend(self._validate_schedule_part(part, row_number))

        return issues

    def _validate_schedule_part(self, part: str, row_number: int) -> list[ValidationIssue]:
        match = SCHEDULE_PART.match(part)
        if not match:
            return [
                self._issue(
                    "critical",
                    row_number,
                    "Ad Schedule",
                    "invalid_schedule_format",
                    f'Ad Schedule part "{part}" is not parseable.',
                    'Use a format like "(Monday[00:00-23:59])" or "Monday 9-17".',
                )
            ]

        day = match.group("day")
        start = match.group("bracket_start") or match.group("plain_start") or ""
        end = match.group("bracket_end") or match.group("plain_end") or ""
        issues: list[ValidationIssue] = []

        if day not in self.valid_days:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Ad Schedule",
                    "invalid_day",
                    f'Ad Schedule day "{day}" is not valid.',
                    f"Use one of: {', '.join(sorted(self.valid_days))}.",
                )
            )

        start_minutes = self._time_to_minutes(start)
        end_minutes = self._time_to_minutes(end)

        if start_minutes is None or end_minutes is None:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Ad Schedule",
                    "invalid_schedule_time",
                    f'Ad Schedule time window "{start}-{end}" is not valid.',
                    "Use 00:00 through 23:59 time values.",
                )
            )
        elif start_minutes >= end_minutes:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Ad Schedule",
                    "schedule_end_before_start",
                    f'Ad Schedule time window "{start}-{end}" does not end after it starts.',
                    "Use an end time later than the start time.",
                )
            )

        return issues

    def _time_to_minutes(self, time_text: str) -> int | None:
        if ":" in time_text:
            hour_text, minute_text = time_text.split(":", 1)
        else:
            hour_text, minute_text = time_text, "00"

        try:
            hour = int(hour_text)
            minute = int(minute_text)
        except ValueError:
            return None

        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None

        return hour * 60 + minute

    def validate_schedule_data(self, schedule_rows: list[dict[str, Any]]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for index, row in enumerate(schedule_rows, start=2):
            issues.extend(self.validate_schedule_row(row, index))
        return issues
