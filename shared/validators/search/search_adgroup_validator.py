#!/usr/bin/env python3
"""
Search Ad Group Validator

Validates ad group-level settings specific to Search campaigns.
Ensures ad groups are properly configured for Search network targeting.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class ValidationIssue:
    """Represents a validation issue found during Search ad group validation."""
    level: str
    severity: str  # 'critical', 'warning', 'info'
    row_number: int
    column: str
    issue_type: str
    message: str
    suggestion: str = ""
    auto_fixable: bool = False


class SearchAdGroupValidator:
    """
    Validates ad group-level settings for Search campaigns.

    Focuses on Search-specific ad group configuration including:
    - Ad group status validation
    - Targeting method verification
    - Ad group-level bid strategy settings
    - Ad group organization and labeling
    """

    def __init__(self, validation_rules: Optional[Dict[str, Any]] = None):
        """Initialize SearchAdGroupValidator with validation rules."""
        self.validation_rules = validation_rules or self._get_default_rules()

        # Valid ad group statuses
        self.valid_statuses = ['Enabled', 'Paused', 'Removed']

        # Valid targeting methods for Search campaigns
        self.valid_targeting_methods = [
            'Manual CPC', 'Target CPA', 'Maximize conversions',
            'Target ROAS', 'Enhanced CPC'
        ]

        # Ad group naming best practices
        self.max_adgroup_name_length = 30
        self.adgroup_name_pattern = re.compile(r'^[a-zA-Z0-9\s\-_]+$')

    def _get_default_rules(self) -> Dict[str, Any]:
        """Get default validation rules for Search ad groups."""
        return {
            'adgroup': {
                'required_fields': ['Ad group', 'Ad group status'],
                'valid_statuses': ['Enabled', 'Paused', 'Removed'],
                'naming': {
                    'max_length': 30,
                    'allowed_chars': 'letters, numbers, spaces, hyphens, underscores'
                },
                'targeting_method_validation': {
                    'allowed_methods': [
                        'Manual CPC', 'Target CPA', 'Maximize conversions',
                        'Target ROAS', 'Enhanced CPC'
                    ]
                }
            }
        }

    def validate_adgroup_row(self, row: Dict[str, Any], row_number: int) -> List[ValidationIssue]:
        """
        Validate a single ad group row for Search campaign compliance.

        Args:
            row: Dictionary representing a CSV row
            row_number: Row number in the CSV (for error reporting)

        Returns:
            List of validation issues found
        """
        issues = []

        # Validate ad group name
        adgroup_name = row.get('Ad group', '').strip()
        if not adgroup_name:
            issues.append(ValidationIssue(
                level='adgroup',
                severity='critical',
                row_number=row_number,
                column='Ad group',
                issue_type='missing_adgroup_name',
                message='Ad group name is required',
                suggestion='Provide a descriptive ad group name (e.g., "Plumbing Services Broward")'
            ))
        else:
            # Check name length
            if len(adgroup_name) > self.max_adgroup_name_length:
                issues.append(ValidationIssue(
                    level='adgroup',
                    severity='warning',
                    row_number=row_number,
                    column='Ad group',
                    issue_type='adgroup_name_too_long',
                    message=f'Ad group name "{adgroup_name}" is {len(adgroup_name)} characters (max {self.max_adgroup_name_length})',
                    suggestion='Shorten ad group name to fit within limit'
                ))

            # Check for invalid characters
            if not self.adgroup_name_pattern.match(adgroup_name):
                issues.append(ValidationIssue(
                    level='adgroup',
                    severity='warning',
                    row_number=row_number,
                    column='Ad group',
                    issue_type='invalid_adgroup_name_chars',
                    message=f'Ad group name contains invalid characters: "{adgroup_name}"',
                    suggestion='Use only letters, numbers, spaces, hyphens, and underscores'
                ))

        # Validate ad group status
        adgroup_status = row.get('Ad group status', '').strip()
        if not adgroup_status:
            issues.append(ValidationIssue(
                level='adgroup',
                severity='warning',
                row_number=row_number,
                column='Ad group status',
                issue_type='missing_adgroup_status',
                message='Ad group status is not specified',
                suggestion='Set to "Enabled" for active ad groups'
            ))
        elif adgroup_status not in self.valid_statuses:
            issues.append(ValidationIssue(
                level='adgroup',
                severity='warning',
                row_number=row_number,
                column='Ad group status',
                issue_type='invalid_adgroup_status',
                message=f'Ad group status "{adgroup_status}" is not standard',
                suggestion=f'Use one of: {", ".join(self.valid_statuses)}'
            ))

        # Validate targeting method (if specified)
        targeting_method = row.get('Targeting method', '').strip()
        if targeting_method and targeting_method not in self.valid_targeting_methods:
            issues.append(ValidationIssue(
                level='adgroup',
                severity='info',
                row_number=row_number,
                column='Targeting method',
                issue_type='non_standard_targeting_method',
                message=f'Targeting method "{targeting_method}" is not in standard list',
                suggestion=f'Consider: {", ".join(self.valid_targeting_methods[:3])}'
            ))

        # Validate ad group bid strategy settings (if specified)
        adgroup_bid_strategy = row.get('Ad group bid strategy', '').strip()
        if adgroup_bid_strategy:
            # This should typically inherit from campaign, but if specified, validate it
            valid_adgroup_strategies = ['Manual CPC', 'Target CPA', 'Maximize conversions']
            if adgroup_bid_strategy not in valid_adgroup_strategies:
                issues.append(ValidationIssue(
                    level='adgroup',
                    severity='warning',
                    row_number=row_number,
                    column='Ad group bid strategy',
                    issue_type='invalid_adgroup_bid_strategy',
                    message=f'Ad group bid strategy "{adgroup_bid_strategy}" may not be optimal',
                    suggestion=f'Consider inheriting from campaign or use: {", ".join(valid_adgroup_strategies)}'
                ))

        # Validate ad group max CPC (if specified)
        max_cpc_str = row.get('Ad group max CPC', '').strip()
        if max_cpc_str:
            try:
                max_cpc = float(max_cpc_str.replace('$', '').replace(',', ''))
                if max_cpc < 0.01:
                    issues.append(ValidationIssue(
                        level='adgroup',
                        severity='critical',
                        row_number=row_number,
                        column='Ad group max CPC',
                        issue_type='cpc_too_low',
                        message=f'Max CPC ${max_cpc:.2f} is below minimum $0.01',
                        suggestion='Increase Max CPC to at least $0.01'
                    ))
                elif max_cpc > 50.00:
                    issues.append(ValidationIssue(
                        level='adgroup',
                        severity='warning',
                        row_number=row_number,
                        column='Ad group max CPC',
                        issue_type='cpc_too_high',
                        message=f'Max CPC ${max_cpc:.2f} is very high',
                        suggestion='Consider reducing Max CPC for better control'
                    ))
            except ValueError:
                issues.append(ValidationIssue(
                    level='adgroup',
                    severity='critical',
                    row_number=row_number,
                    column='Ad group max CPC',
                    issue_type='invalid_cpc_format',
                    message=f'Invalid Max CPC format: "{max_cpc_str}"',
                    suggestion='Use numeric format (e.g., 2.50 or $2.50)'
                ))

        # Validate labels (if specified)
        labels = row.get('Ad group labels', '').strip()
        if labels:
            # Check for label format (comma-separated)
            if ',' in labels:
                label_list = [label.strip() for label in labels.split(',')]
                if len(label_list) > 10:
                    issues.append(ValidationIssue(
                        level='adgroup',
                        severity='info',
                        row_number=row_number,
                        column='Ad group labels',
                        issue_type='too_many_labels',
                        message=f'Ad group has {len(label_list)} labels (recommended max: 10)',
                        suggestion='Consider reducing number of labels for better organization'
                    ))

        return issues

    def validate_adgroup_data(self, adgroup_rows: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """
        Validate ad group-level data across multiple rows.

        Args:
            adgroup_rows: List of ad group row dictionaries

        Returns:
            List of validation issues found
        """
        issues = []

        if not adgroup_rows:
            return issues

        # Validate each ad group row
        for i, row in enumerate(adgroup_rows):
            row_issues = self.validate_adgroup_row(row, i + 2)  # +2 because row 1 is headers
            issues.extend(row_issues)

        # Cross-adgroup validation
        adgroup_names = set()
        campaign_adgroups = {}

        for row in adgroup_rows:
            adgroup_name = row.get('Ad group', '').strip()
            campaign_name = row.get('Campaign', '').strip()

            if adgroup_name:
                # Check for duplicate ad group names within same campaign
                campaign_key = campaign_name or 'default'
                if campaign_key not in campaign_adgroups:
                    campaign_adgroups[campaign_key] = set()

                if adgroup_name in campaign_adgroups[campaign_key]:
                    issues.append(ValidationIssue(
                        level='adgroup',
                        severity='warning',
                        row_number=0,  # Multiple rows
                        column='Ad group',
                        issue_type='duplicate_adgroup_name',
                        message=f'Duplicate ad group name "{adgroup_name}" in campaign "{campaign_name}"',
                        suggestion='Use unique ad group names within each campaign'
                    ))
                else:
                    campaign_adgroups[campaign_key].add(adgroup_name)

        # Check for optimal ad group structure
        for campaign, adgroups in campaign_adgroups.items():
            if len(adgroups) < 3:
                issues.append(ValidationIssue(
                    level='adgroup',
                    severity='info',
                    row_number=0,
                    column='Ad group',
                    issue_type='few_adgroups',
                    message=f'Campaign "{campaign}" has only {len(adgroups)} ad groups',
                    suggestion='Consider creating more ad groups for better organization and targeting'
                ))
            elif len(adgroups) > 50:
                issues.append(ValidationIssue(
                    level='adgroup',
                    severity='info',
                    row_number=0,
                    column='Ad group',
                    issue_type='many_adgroups',
                    message=f'Campaign "{campaign}" has {len(adgroups)} ad groups',
                    suggestion='Consider consolidating some ad groups for easier management'
                ))

        return issues