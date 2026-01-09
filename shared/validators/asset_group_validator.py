#!/usr/bin/env python3
"""
Asset Group-level CSV Validator

Validates asset groups and their relationships.
"""

import logging
from typing import Dict, List, Any, Optional
import csv
import io
import re

logger = logging.getLogger(__name__)


class AssetGroupValidator:
    """Validates asset group settings and relationships"""

    def __init__(self):
        self.max_headlines = 15
        self.max_descriptions = 5
        self.max_videos = 5
        self.max_images = 20

        self.required_fields = ['Asset Group', 'Final URL']

        # URL validation pattern
        self.url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'

        # Headline length limits
        self.headline_limits = {'min': 25, 'max': 30}
        self.description_limits = {'min': 80, 'max': 90}

    def validate_asset_groups(self, csv_path: str, csv_content: str) -> List[Dict[str, Any]]:
        """Validate asset group settings and structure"""
        issues = []

        try:
            csv_io = io.StringIO(csv_content)
            reader = csv.DictReader(csv_io, delimiter='\t')

            asset_groups_seen = {}

            for row_num, row in enumerate(reader, 2):
                campaign_type = row.get("Campaign Type", "").strip()

                # Only validate asset groups for Performance Max
                if campaign_type == "Performance Max":
                    asset_group_issues = self._validate_pmax_asset_group(row, row_num, asset_groups_seen)
                    issues.extend(asset_group_issues)

                # Validate asset counts
                asset_count_issues = self._validate_asset_counts(row, row_num)
                issues.extend(asset_count_issues)

                # Validate URLs
                url_issues = self._validate_urls(row, row_num)
                issues.extend(url_issues)

        except Exception as e:
            issues.append({
                'level': 'asset_group',
                'severity': 'critical',
                'row_number': 0,
                'column': '',
                'issue_type': 'validation_error',
                'message': f'Failed to validate asset groups: {e}',
                'auto_fixable': False
            })

        return issues

    def _validate_pmax_asset_group(self, row: Dict[str, str], row_num: int, asset_groups_seen: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Validate Performance Max asset group settings"""
        issues = []

        asset_group = row.get("Asset Group", "").strip()
        final_url = row.get("Final URL", "").strip()

        if not asset_group:
            issues.append({
                'level': 'asset_group',
                'severity': 'warning',
                'row_number': row_num,
                'column': 'Asset Group',
                'issue_type': 'missing_asset_group',
                'message': 'Performance Max campaigns require asset groups',
                'auto_fixable': False
            })
        else:
            # Track asset group properties
            if asset_group not in asset_groups_seen:
                asset_groups_seen[asset_group] = {
                    'final_url': final_url,
                    'headlines': 0,
                    'descriptions': 0,
                    'videos': 0,
                    'images': 0,
                    'first_row': row_num
                }

            # Check for consistent Final URL within asset group
            if asset_groups_seen[asset_group]['final_url'] != final_url:
                issues.append({
                    'level': 'asset_group',
                    'severity': 'error',
                    'row_number': row_num,
                    'column': 'Final URL',
                    'issue_type': 'inconsistent_final_url',
                    'message': f'Asset group "{asset_group}" has inconsistent Final URLs',
                    'context': {
                        'expected': asset_groups_seen[asset_group]['final_url'],
                        'found': final_url
                    },
                    'auto_fixable': False
                })

        # Validate required fields for asset groups
        if asset_group and not final_url:
            issues.append({
                'level': 'asset_group',
                'severity': 'error',
                'row_number': row_num,
                'column': 'Final URL',
                'issue_type': 'missing_final_url',
                'message': f'Asset group "{asset_group}" requires a Final URL',
                'auto_fixable': False
            })

        return issues

    def _validate_asset_counts(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate asset counts per asset group"""
        issues = []

        asset_group = row.get("Asset Group", "").strip()

        # Count headlines
        headline_count = 0
        for i in range(1, 16):
            headline_col = f"Headline {i}"
            if row.get(headline_col, "").strip():
                headline_count += 1

        # Count descriptions
        description_count = 0
        for i in range(1, 6):
            desc_col = f"Description {i}"
            if row.get(desc_col, "").strip():
                description_count += 1

        # Count videos
        video_count = 0
        for i in range(1, 6):
            video_col = f"Video ID {i}"
            if row.get(video_col, "").strip():
                video_count += 1

        # Validate counts
        if headline_count > self.max_headlines:
            issues.append({
                'level': 'asset_group',
                'severity': 'error',
                'row_number': row_num,
                'column': 'Headlines',
                'issue_type': 'too_many_headlines',
                'message': f'Asset group "{asset_group}" has {headline_count} headlines (max: {self.max_headlines})',
                'auto_fixable': False
            })

        if description_count > self.max_descriptions:
            issues.append({
                'level': 'asset_group',
                'severity': 'error',
                'row_number': row_num,
                'column': 'Descriptions',
                'issue_type': 'too_many_descriptions',
                'message': f'Asset group "{asset_group}" has {description_count} descriptions (max: {self.max_descriptions})',
                'auto_fixable': False
            })

        if video_count > self.max_videos:
            issues.append({
                'level': 'asset_group',
                'severity': 'error',
                'row_number': row_num,
                'column': 'Videos',
                'issue_type': 'too_many_videos',
                'message': f'Asset group "{asset_group}" has {video_count} videos (max: {self.max_videos})',
                'auto_fixable': False
            })

        # Check minimum requirements
        if headline_count == 0:
            issues.append({
                'level': 'asset_group',
                'severity': 'warning',
                'row_number': row_num,
                'column': 'Headlines',
                'issue_type': 'no_headlines',
                'message': f'Asset group "{asset_group}" has no headlines',
                'auto_fixable': False
            })

        if description_count == 0:
            issues.append({
                'level': 'asset_group',
                'severity': 'warning',
                'row_number': row_num,
                'column': 'Descriptions',
                'issue_type': 'no_descriptions',
                'message': f'Asset group "{asset_group}" has no descriptions',
                'auto_fixable': False
            })

        return issues

    def _validate_urls(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate URL formats"""
        issues = []

        urls_to_check = [
            ('Final URL', row.get('Final URL', '').strip()),
            ('Final mobile URL', row.get('Final mobile URL', '').strip())
        ]

        for url_name, url in urls_to_check:
            if url and not re.match(self.url_pattern, url):
                issues.append({
                    'level': 'asset_group',
                    'severity': 'error',
                    'row_number': row_num,
                    'column': url_name,
                    'issue_type': 'invalid_url_format',
                    'message': f'Invalid URL format in {url_name}: {url}',
                    'suggestion': 'URL should start with http:// or https://',
                    'auto_fixable': False
                })

        return issues