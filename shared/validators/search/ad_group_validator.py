#!/usr/bin/env python3
"""
Ad Group Validator for Search Campaigns

Validates ad group structure, settings, and organization in Search campaigns.
"""

import logging
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)


class AdGroupValidator:
    """Validates ad group settings and structure for Search campaigns"""

    def __init__(self):
        self.max_ad_groups_per_campaign = 20000
        self.min_keywords_per_ad_group = 1
        self.max_keywords_per_ad_group = 20000

        # Ad group status values
        self.valid_statuses = ['Enabled', 'Paused', 'Removed']

        # Ad group naming best practices
        self.ad_group_name_pattern = r'^[A-Za-z0-9\s\-_]{1,128}$'

    def validate_ad_group(self, csv_path: str, row: Dict[str, str], row_num: int,
                         ad_groups_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate ad group settings and track ad group data"""
        issues = []

        campaign_type = row.get("Campaign Type", "").strip()
        if campaign_type != "Search":
            return issues

        ad_group_name = row.get("Ad group", "").strip()

        # Validate ad group name exists
        if not ad_group_name:
            issues.append({
                'level': 'ad_group',
                'severity': 'error',
                'row_number': row_num,
                'column': 'Ad group',
                'issue_type': 'missing_ad_group_name',
                'message': 'Search campaigns require ad group names',
                'auto_fixable': False
            })
            return issues

        # Validate ad group name format
        if not re.match(self.ad_group_name_pattern, ad_group_name):
            issues.append({
                'level': 'ad_group',
                'severity': 'warning',
                'row_number': row_num,
                'column': 'Ad group',
                'issue_type': 'invalid_ad_group_name',
                'message': f'Ad group name "{ad_group_name}" contains invalid characters or is too long',
                'suggestion': 'Use only letters, numbers, spaces, hyphens, and underscores (max 128 chars)',
                'auto_fixable': False
            })

        # Validate ad group status
        ad_group_status = row.get("Ad Group Status", "").strip()
        if ad_group_status and ad_group_status not in self.valid_statuses:
            issues.append({
                'level': 'ad_group',
                'severity': 'error',
                'row_number': row_num,
                'column': 'Ad Group Status',
                'issue_type': 'invalid_ad_group_status',
                'message': f'Invalid ad group status: "{ad_group_status}". Valid: {self.valid_statuses}',
                'auto_fixable': True,
                'original_value': ad_group_status,
                'fixed_value': 'Enabled'
            })

        # Track ad group data for cross-validation
        if ad_group_name not in ad_groups_data:
            ad_groups_data[ad_group_name] = {
                'campaign': row.get("Campaign", "").strip(),
                'status': ad_group_status or 'Enabled',
                'keyword_count': 0,
                'text_ad_count': 0,
                'first_row': row_num,
                'keywords': [],
                'match_types': set()
            }

        # Count keywords in this ad group
        keyword = row.get("Keyword", "").strip()
        if keyword:
            ad_groups_data[ad_group_name]['keyword_count'] += 1
            ad_groups_data[ad_group_name]['keywords'].append(keyword)

            # Track match types
            criterion_type = row.get("Criterion Type", "").strip()
            if criterion_type:
                ad_groups_data[ad_group_name]['match_types'].add(criterion_type)

        # Count text ads in this ad group
        headline_1 = row.get("Headline 1", "").strip()
        if headline_1:
            ad_groups_data[ad_group_name]['text_ad_count'] += 1

        # Validate ad group bidding (if present)
        cpc_bid = row.get("Max CPC", "").strip()
        if cpc_bid:
            try:
                bid_value = float(cpc_bid)
                if bid_value <= 0:
                    issues.append({
                        'level': 'ad_group',
                        'severity': 'error',
                        'row_number': row_num,
                        'column': 'Max CPC',
                        'issue_type': 'invalid_cpc_bid',
                        'message': f'CPC bid must be greater than 0: {cpc_bid}',
                        'auto_fixable': False
                    })
                elif bid_value > 100:  # Very high bid warning
                    issues.append({
                        'level': 'ad_group',
                        'severity': 'warning',
                        'row_number': row_num,
                        'column': 'Max CPC',
                        'issue_type': 'high_cpc_bid',
                        'message': f'Very high CPC bid: ${bid_value}. Consider if this is intentional.',
                        'auto_fixable': False
                    })
            except ValueError:
                issues.append({
                    'level': 'ad_group',
                    'severity': 'error',
                    'row_number': row_num,
                    'column': 'Max CPC',
                    'issue_type': 'invalid_cpc_format',
                    'message': f'Invalid CPC bid format: {cpc_bid}',
                    'auto_fixable': False
                })

        # Validate target CPA for ad groups (if using Target CPA bidding)
        target_cpa = row.get("Target CPA", "").strip()
        if target_cpa:
            try:
                cpa_value = float(target_cpa)
                if cpa_value <= 0:
                    issues.append({
                        'level': 'ad_group',
                        'severity': 'error',
                        'row_number': row_num,
                        'column': 'Target CPA',
                        'issue_type': 'invalid_target_cpa',
                        'message': f'Target CPA must be greater than 0: {target_cpa}',
                        'auto_fixable': False
                    })
            except ValueError:
                issues.append({
                    'level': 'ad_group',
                    'severity': 'error',
                    'row_number': row_num,
                    'column': 'Target CPA',
                    'issue_type': 'invalid_cpa_format',
                    'message': f'Invalid Target CPA format: {target_cpa}',
                    'auto_fixable': False
                })

        return issues

    def validate_ad_group_structure(self, ad_groups_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate ad group structure and relationships"""
        issues = []

        for ad_group_name, data in ad_groups_data.items():
            keyword_count = data.get('keyword_count', 0)
            text_ad_count = data.get('text_ad_count', 0)

            # Validate keyword count
            if keyword_count == 0:
                issues.append({
                    'level': 'ad_group',
                    'severity': 'error',
                    'row_number': data.get('first_row', 0),
                    'column': 'Ad group',
                    'issue_type': 'ad_group_no_keywords',
                    'message': f'Ad group "{ad_group_name}" has no keywords',
                    'auto_fixable': False
                })
            elif keyword_count > self.max_keywords_per_ad_group:
                issues.append({
                    'level': 'ad_group',
                    'severity': 'error',
                    'row_number': data.get('first_row', 0),
                    'column': 'Ad group',
                    'issue_type': 'too_many_keywords',
                    'message': f'Ad group "{ad_group_name}" has {keyword_count} keywords (max: {self.max_keywords_per_ad_group})',
                    'auto_fixable': False
                })

            # Validate text ad count
            if text_ad_count == 0:
                issues.append({
                    'level': 'ad_group',
                    'severity': 'warning',
                    'row_number': data.get('first_row', 0),
                    'column': 'Ad group',
                    'issue_type': 'ad_group_no_text_ads',
                    'message': f'Ad group "{ad_group_name}" has no text ads',
                    'auto_fixable': False
                })

            # Validate match type diversity
            match_types = data.get('match_types', set())
            if len(match_types) == 1 and 'Broad' in match_types:
                issues.append({
                    'level': 'ad_group',
                    'severity': 'info',
                    'row_number': data.get('first_row', 0),
                    'column': 'Ad group',
                    'issue_type': 'single_match_type',
                    'message': f'Ad group "{ad_group_name}" only uses Broad match. Consider adding Exact/Phrase for better control.',
                    'auto_fixable': False
                })

        return issues