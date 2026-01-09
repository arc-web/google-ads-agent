#!/usr/bin/env python3
"""
Account-level CSV Validator

Validates account-level settings and CSV structure.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import csv
import io

logger = logging.getLogger(__name__)


class AccountValidator:
    """Validates account-level settings and CSV structure"""

    def __init__(self):
        # EXACT OFFICIAL GOOGLE ADS EDITOR REQUIRED HEADERS
        # Must match official specification exactly - no assumptions
        self.required_headers = [
            'Campaign', 'Campaign type', 'Networks', 'Budget', 'Budget type',  # FIXED: Campaign type (exact case)
            'Status',  # ADDED: Core required column
            'Ad group', 'Criterion Type',  # Core ad group and keyword columns
            'Headline 1', 'Headline 2', 'Headline 3', 'Description 1', 'Description 2',  # Core ad columns
            'Location', 'Location id', 'Location type'  # ADDED: Core location columns
        ]

        self.valid_campaign_types = [
            'Search', 'Performance Max', 'Display Network only', 'Shopping', 'Video'
        ]

        self.valid_budget_types = ['Daily', 'Monthly']
        self.valid_networks = ['Google search', 'Search Partners', 'Display Network']

    def validate_csv_structure(self, csv_path: str, csv_content: str) -> List[Dict[str, Any]]:
        """Validate CSV structure and headers"""
        issues = []

        # Check for UTF-8 BOM
        if not csv_content.startswith('\ufeff'):
            issues.append({
                'level': 'account',
                'severity': 'warning',
                'row_number': 0,
                'column': '',
                'issue_type': 'encoding',
                'message': 'CSV file missing UTF-8 BOM - may cause Excel compatibility issues',
                'suggestion': 'Add UTF-8 BOM to CSV file',
                'auto_fixable': True
            })

        # CRITICAL: Check that row 1 contains headers, not comments/metadata
        lines = csv_content.split('\n')
        if lines and lines[0].strip().startswith(('#', '//', '/*')):
            issues.append({
                'level': 'account',
                'severity': 'critical',
                'row_number': 0,
                'column': '',
                'issue_type': 'invalid_csv_structure',
                'message': 'CSV row 1 contains comments/metadata instead of headers - this violates CSV format standards',
                'suggestion': 'Row 1 MUST contain CSV headers only. Move comments to separate files or filename.',
                'auto_fixable': False
            })

        # Parse CSV to validate headers
        # NOTE: CSV content should NEVER contain stage comments in data rows
        # Stage information is stored in filenames and metadata files only
        csv_io = io.StringIO(csv_content)
        try:
            reader = csv.DictReader(csv_io, delimiter='\t')
            headers = reader.fieldnames or []

            # Check required headers
            missing_headers = set(self.required_headers) - set(headers)
            if missing_headers:
                issues.append({
                    'level': 'account',
                    'severity': 'critical',
                    'row_number': 0,
                    'column': '',
                    'issue_type': 'missing_headers',
                    'message': f'Missing required headers: {missing_headers}',
                    'auto_fixable': False
                })

            # Check for empty headers
            empty_headers = [i for i, h in enumerate(headers) if not h or h.strip() == '']
            if empty_headers:
                issues.append({
                    'level': 'account',
                    'severity': 'error',
                    'row_number': 0,
                    'column': f'Column {empty_headers[0] + 1}',
                    'issue_type': 'empty_headers',
                    'message': f'Found empty column headers at positions: {empty_headers}',
                    'auto_fixable': False
                })

        except Exception as e:
            issues.append({
                'level': 'account',
                'severity': 'critical',
                'row_number': 0,
                'column': '',
                'issue_type': 'structure_error',
                'message': f'Failed to validate CSV structure: {e}',
                'auto_fixable': False
            })

        return issues

    def validate_account_settings(self, csv_path: str, csv_content: str) -> List[Dict[str, Any]]:
        """Validate account-level settings in CSV rows"""
        issues = []

        try:
            csv_io = io.StringIO(csv_content)
            reader = csv.DictReader(csv_io, delimiter='\t')

            for row_num, row in enumerate(reader, 2):  # Start from 2 (header is 1)
                # Validate campaign name
                campaign_name = row.get("Campaign", "").strip()
                if not campaign_name:
                    issues.append({
                        'level': 'account',
                        'severity': 'critical',
                        'row_number': row_num,
                        'column': 'Campaign',
                        'issue_type': 'missing_campaign_name',
                        'message': 'Campaign name is required',
                        'auto_fixable': False
                    })

                # Validate campaign type
                campaign_type = row.get("Campaign Type", "").strip()
                if campaign_type and campaign_type not in self.valid_campaign_types:
                    issues.append({
                        'level': 'account',
                        'severity': 'error',
                        'row_number': row_num,
                        'column': 'Campaign Type',
                        'issue_type': 'invalid_campaign_type',
                        'message': f'Invalid campaign type "{campaign_type}". Valid types: {self.valid_campaign_types}',
                        'auto_fixable': False
                    })

                # Validate budget type
                budget_type = row.get("Budget type", "").strip()
                if budget_type and budget_type not in self.valid_budget_types:
                    issues.append({
                        'level': 'account',
                        'severity': 'error',
                        'row_number': row_num,
                        'column': 'Budget type',
                        'issue_type': 'invalid_budget_type',
                        'message': f'Invalid budget type "{budget_type}". Valid types: {self.valid_budget_types}',
                        'auto_fixable': True,
                        'original_value': budget_type,
                        'fixed_value': 'Daily'  # Default to Daily
                    })

                # Validate networks
                networks = row.get("Networks", "").strip()
                if networks:
                    network_list = [n.strip() for n in networks.split(';')]
                    invalid_networks = set(network_list) - set(self.valid_networks)
                    if invalid_networks:
                        issues.append({
                            'level': 'account',
                            'severity': 'error',
                            'row_number': row_num,
                            'column': 'Networks',
                            'issue_type': 'invalid_networks',
                            'message': f'Invalid networks: {invalid_networks}. Valid networks: {self.valid_networks}',
                            'auto_fixable': False
                        })

        except Exception as e:
            issues.append({
                'level': 'account',
                'severity': 'critical',
                'row_number': 0,
                'column': '',
                'issue_type': 'validation_error',
                'message': f'Failed to validate account settings: {e}',
                'auto_fixable': False
            })

        return issues