#!/usr/bin/env python3
"""
Search Bid Strategy Validator

Validates bid strategies for Search campaigns.
Ensures bid strategy settings are appropriate and properly configured.
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


class SearchBidStrategyValidator:
    """Validates bid strategies for Search campaigns."""

    def __init__(self, validation_rules: Optional[Dict[str, Any]] = None):
        self.validation_rules = validation_rules or self._get_default_rules()
        self.valid_bid_strategies = [
            'Manual CPC', 'Target CPA', 'Maximize conversions',
            'Target ROAS', 'Enhanced CPC', 'Target impression share'
        ]
        self.min_cpc = 0.01
        self.max_cpc = 50.00

    def _get_default_rules(self) -> Dict[str, Any]:
        return {
            'bid_strategy': {
                'valid_strategies': [
                    'Manual CPC', 'Target CPA', 'Maximize conversions',
                    'Target ROAS', 'Enhanced CPC', 'Target impression share'
                ],
                'cpc_limits': {'min': 0.01, 'max': 50.00}
            }
        }

    def validate_bid_strategy_row(self, row: Dict[str, Any], row_number: int) -> List[ValidationIssue]:
        issues = []
        bid_strategy = row.get('Bid Strategy Type', '').strip()
        bid_strategy_name = row.get('Bid Strategy Name', '').strip()

        if bid_strategy and bid_strategy not in self.valid_bid_strategies:
            issues.append(ValidationIssue(
                level='bid_strategy', severity='warning', row_number=row_number,
                column='Bid Strategy Type', issue_type='invalid_bid_strategy',
                message=f'Bid strategy "{bid_strategy}" may not be optimal for Search',
                suggestion=f'Consider: {", ".join(self.valid_bid_strategies[:3])}'
            ))

        # Validate Max CPC
        max_cpc_str = row.get('Max CPC', '').strip()
        if max_cpc_str:
            try:
                max_cpc = float(max_cpc_str.replace('$', ''))
                if max_cpc < self.min_cpc:
                    issues.append(ValidationIssue(
                        level='bid_strategy', severity='critical', row_number=row_number,
                        column='Max CPC', issue_type='cpc_too_low',
                        message=f'Max CPC ${max_cpc:.2f} below minimum ${self.min_cpc:.2f}',
                        suggestion=f'Increase to at least ${self.min_cpc:.2f}'
                    ))
                elif max_cpc > self.max_cpc:
                    issues.append(ValidationIssue(
                        level='bid_strategy', severity='warning', row_number=row_number,
                        column='Max CPC', issue_type='cpc_high',
                        message=f'Max CPC ${max_cpc:.2f} above recommended ${self.max_cpc:.2f}',
                        suggestion='Consider reducing Max CPC'
                    ))
            except ValueError:
                issues.append(ValidationIssue(
                    level='bid_strategy', severity='critical', row_number=row_number,
                    column='Max CPC', issue_type='invalid_cpc',
                    message=f'Invalid Max CPC format: {max_cpc_str}',
                    suggestion='Use numeric format'
                ))

        return issues

    def validate_bid_strategy_data(self, bid_strategy_rows: List[Dict[str, Any]]) -> List[ValidationIssue]:
        issues = []
        for i, row in enumerate(bid_strategy_rows):
            issues.extend(self.validate_bid_strategy_row(row, i + 2))
        return issues