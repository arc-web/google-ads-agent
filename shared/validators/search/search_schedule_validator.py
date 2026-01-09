#!/usr/bin/env python3
"""
Search Schedule Validator

Validates ad scheduling for Search campaigns.
Ensures schedule settings are valid and properly formatted.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class ValidationIssue:
    level: str
    severity: str
    row_number: int
    column: str
    issue_type: str
    message: str
    suggestion: str = ""
    auto_fixable: bool = False


class SearchScheduleValidator:
    """Validates ad scheduling for Search campaigns."""

    def __init__(self, validation_rules: Optional[Dict[str, Any]] = None):
        self.validation_rules = validation_rules or self._get_default_rules()
        self.valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        self.valid_hours = list(range(24))

    def _get_default_rules(self) -> Dict[str, Any]:
        return {
            'schedule': {
                'valid_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                'valid_hours': list(range(24))
            }
        }

    def validate_schedule_row(self, row: Dict[str, Any], row_number: int) -> List[ValidationIssue]:
        issues = []
        schedule = row.get('Ad Schedule', '').strip()

        if schedule:
            # Parse schedule format (e.g., "Monday 9-17; Tuesday 9-17")
            schedule_parts = re.split(r'[;,]', schedule)

            for part in schedule_parts:
                part = part.strip()
                if not part:
                    continue

                # Check day and time format
                day_match = re.match(r'(\w+)\s+(\d+)-(\d+)', part)
                if day_match:
                    day, start_hour, end_hour = day_match.groups()
                    if day not in self.valid_days:
                        issues.append(ValidationIssue(
                            level='schedule', severity='critical', row_number=row_number,
                            column='Ad Schedule', issue_type='invalid_day',
                            message=f'Invalid day: {day}',
                            suggestion=f'Use: {", ".join(self.valid_days)}'
                        ))
                    if not (0 <= int(start_hour) <= 23 and 0 <= int(end_hour) <= 23):
                        issues.append(ValidationIssue(
                            level='schedule', severity='critical', row_number=row_number,
                            column='Ad Schedule', issue_type='invalid_hours',
                            message=f'Invalid hours: {start_hour}-{end_hour}',
                            suggestion='Use 0-23 range'
                        ))
                else:
                    issues.append(ValidationIssue(
                        level='schedule', severity='warning', row_number=row_number,
                        column='Ad Schedule', issue_type='invalid_format',
                        message=f'Invalid schedule format: {part}',
                        suggestion='Use "Day 9-17" format'
                    ))

        return issues

    def validate_schedule_data(self, schedule_rows: List[Dict[str, Any]]) -> List[ValidationIssue]:
        issues = []
        for i, row in enumerate(schedule_rows):
            issues.extend(self.validate_schedule_row(row, i + 2))
        return issues