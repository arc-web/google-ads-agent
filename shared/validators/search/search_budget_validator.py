#!/usr/bin/env python3
"""
Search Budget Validator

Validates budget settings for Search campaigns.
Ensures budget amounts and types are appropriate for Search campaigns.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


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


class SearchBudgetValidator:
    """Validates budget settings for Search campaigns."""

    def __init__(self, validation_rules: Optional[Dict[str, Any]] = None):
        self.validation_rules = validation_rules or self._get_default_rules()
        self.valid_budget_types = ['Daily', 'Monthly']
        self.min_daily_budget = 5.00
        self.max_daily_budget = 10000.00
        self.min_monthly_budget = 150.00
        self.max_monthly_budget = 300000.00

    def _get_default_rules(self) -> Dict[str, Any]:
        return {
            'budget': {
                'valid_types': ['Daily', 'Monthly'],
                'daily_limits': {'min': 5.00, 'max': 10000.00},
                'monthly_limits': {'min': 150.00, 'max': 300000.00}
            }
        }

    def validate_budget_row(self, row: Dict[str, Any], row_number: int) -> List[ValidationIssue]:
        issues = []
        budget_str = row.get('Budget', '').strip()
        budget_type = row.get('Budget type', '').strip()

        if budget_str:
            try:
                budget = float(budget_str.replace('$', '').replace(',', ''))

                if budget_type == 'Daily':
                    if budget < self.min_daily_budget:
                        issues.append(ValidationIssue(
                            level='budget', severity='critical', row_number=row_number,
                            column='Budget', issue_type='budget_too_low',
                            message=f'Daily budget ${budget:.2f} below minimum ${self.min_daily_budget:.2f}',
                            suggestion=f'Increase to at least ${self.min_daily_budget:.2f}'
                        ))
                    elif budget > self.max_daily_budget:
                        issues.append(ValidationIssue(
                            level='budget', severity='warning', row_number=row_number,
                            column='Budget', issue_type='budget_high',
                            message=f'Daily budget ${budget:.2f} above recommended ${self.max_daily_budget:.2f}',
                            suggestion='Consider reducing or using monthly budget'
                        ))
                elif budget_type == 'Monthly':
                    if budget < self.min_monthly_budget:
                        issues.append(ValidationIssue(
                            level='budget', severity='critical', row_number=row_number,
                            column='Budget', issue_type='budget_too_low',
                            message=f'Monthly budget ${budget:.2f} below minimum ${self.min_monthly_budget:.2f}',
                            suggestion=f'Increase to at least ${self.min_monthly_budget:.2f}'
                        ))
            except ValueError:
                issues.append(ValidationIssue(
                    level='budget', severity='critical', row_number=row_number,
                    column='Budget', issue_type='invalid_budget',
                    message=f'Invalid budget format: {budget_str}',
                    suggestion='Use numeric format'
                ))

        if budget_type and budget_type not in self.valid_budget_types:
            issues.append(ValidationIssue(
                level='budget', severity='critical', row_number=row_number,
                column='Budget type', issue_type='invalid_budget_type',
                message=f'Invalid budget type: {budget_type}',
                suggestion=f'Use: {", ".join(self.valid_budget_types)}'
            ))

        return issues

    def validate_budget_data(self, budget_rows: List[Dict[str, Any]]) -> List[ValidationIssue]:
        issues = []
        for i, row in enumerate(budget_rows):
            issues.extend(self.validate_budget_row(row, i + 2))
        return issues