#!/usr/bin/env python3
"""
Campaign-level CSV Validator

Validates campaign-level configurations and settings.
"""

import logging
from typing import Dict, List, Any, Optional
import csv
import io
import re

logger = logging.getLogger(__name__)


class CampaignValidator:
    """Validates campaign-level configurations"""

    def __init__(self):
        self.pmax_requirements = {
            'brand_guidelines': 'Disabled',
            'eu_political_ads': "Doesn't have EU political ads"
        }

        self.search_requirements = {
            'ad_groups_required': True
        }

        # Budget validation
        self.min_budget = 5.00
        self.max_budget = 10000.00

        # Ad schedule pattern
        self.ad_schedule_pattern = r'^\((Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\[\d{2}:\d{2}-\d{2}:\d{2}\]\);?\)*$'

    def validate_campaign_settings(self, csv_path: str, csv_content: str) -> List[Dict[str, Any]]:
        """Validate campaign-level settings"""
        issues = []

        try:
            csv_io = io.StringIO(csv_content)
            reader = csv.DictReader(csv_io, delimiter='\t')

            for row_num, row in enumerate(reader, 2):
                campaign_type = row.get("Campaign Type", "").strip()

                # Budget validation
                budget_issues = self._validate_budget(row, row_num)
                issues.extend(budget_issues)

                # Campaign type specific validations
                if campaign_type == "Performance Max":
                    pmax_issues = self._validate_pmax_campaign(row, row_num)
                    issues.extend(pmax_issues)
                elif campaign_type == "Search":
                    search_issues = self._validate_search_campaign(row, row_num)
                    issues.extend(search_issues)

                # Ad schedule validation
                schedule_issues = self._validate_ad_schedule(row, row_num)
                issues.extend(schedule_issues)

                # Language validation
                language_issues = self._validate_language(row, row_num)
                issues.extend(language_issues)

                # Bid strategy validation
                bid_issues = self._validate_bid_strategy(row, row_num)
                issues.extend(bid_issues)

        except Exception as e:
            issues.append({
                'level': 'campaign',
                'severity': 'critical',
                'row_number': 0,
                'column': '',
                'issue_type': 'validation_error',
                'message': f'Failed to validate campaign settings: {e}',
                'auto_fixable': False
            })

        return issues

    def _validate_budget(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate budget settings"""
        issues = []

        budget_str = row.get("Budget", "").strip()
        budget_type = row.get("Budget type", "").strip()

        if budget_str:
            try:
                budget_val = float(budget_str)

                # Check budget range
                if budget_val < self.min_budget:
                    issues.append({
                        'level': 'campaign',
                        'severity': 'warning',
                        'row_number': row_num,
                        'column': 'Budget',
                        'issue_type': 'budget_too_low',
                        'message': f'Budget ${budget_val} is below recommended minimum of ${self.min_budget}',
                        'auto_fixable': False
                    })
                elif budget_val > self.max_budget:
                    issues.append({
                        'level': 'campaign',
                        'severity': 'error',
                        'row_number': row_num,
                        'column': 'Budget',
                        'issue_type': 'budget_too_high',
                        'message': f'Budget ${budget_val} exceeds maximum of ${self.max_budget}',
                        'auto_fixable': False
                    })

                # Check budget type consistency
                if budget_type == 'Monthly' and budget_val < 150:
                    issues.append({
                        'level': 'campaign',
                        'severity': 'warning',
                        'row_number': row_num,
                        'column': 'Budget',
                        'issue_type': 'monthly_budget_low',
                        'message': f'Monthly budget ${budget_val} seems low for monthly pacing',
                        'auto_fixable': False
                    })

            except ValueError:
                issues.append({
                    'level': 'campaign',
                    'severity': 'error',
                    'row_number': row_num,
                    'column': 'Budget',
                    'issue_type': 'invalid_budget_format',
                    'message': f'Invalid budget format: {budget_str}',
                    'auto_fixable': False
                })

        return issues

    def _validate_pmax_campaign(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate Performance Max campaign settings"""
        issues = []

        # Check brand guidelines
        brand_guidelines = row.get("Brand guidelines", "").strip()
        expected = self.pmax_requirements['brand_guidelines']
        if brand_guidelines not in [expected, "Enabled"]:
            issues.append({
                'level': 'campaign',
                'severity': 'error',
                'row_number': row_num,
                'column': 'Brand guidelines',
                'issue_type': 'invalid_brand_guidelines',
                'message': f'Brand guidelines should be "{expected}" for PMAX campaigns: {brand_guidelines}',
                'suggestion': f'Set to "{expected}"',
                'auto_fixable': True,
                'original_value': brand_guidelines,
                'fixed_value': expected
            })

        # Check EU political ads
        eu_ads = row.get("EU political ads", "").strip()
        expected_eu = self.pmax_requirements['eu_political_ads']
        if eu_ads != expected_eu:
            issues.append({
                'level': 'campaign',
                'severity': 'error',
                'row_number': row_num,
                'column': 'EU political ads',
                'issue_type': 'invalid_eu_political_ads',
                'message': f'EU political ads should be "{expected_eu}": {eu_ads}',
                'suggestion': f'Set to "{expected_eu}"',
                'auto_fixable': True,
                'original_value': eu_ads,
                'fixed_value': expected_eu
            })

        # Check for required PMAX settings
        target_cpa = row.get("Target CPA", "").strip()
        if target_cpa:
            try:
                cpa_val = float(target_cpa)
                if cpa_val <= 0:
                    issues.append({
                        'level': 'campaign',
                        'severity': 'error',
                        'row_number': row_num,
                        'column': 'Target CPA',
                        'issue_type': 'invalid_target_cpa',
                        'message': f'Target CPA must be greater than 0: {target_cpa}',
                        'auto_fixable': False
                    })
            except ValueError:
                issues.append({
                    'level': 'campaign',
                    'severity': 'error',
                    'row_number': row_num,
                    'column': 'Target CPA',
                    'issue_type': 'invalid_cpa_format',
                    'message': f'Invalid Target CPA format: {target_cpa}',
                    'auto_fixable': False
                })

        return issues

    def _validate_search_campaign(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate Search campaign settings"""
        issues = []

        # Check if ad group exists for Search campaigns
        ad_group = row.get("Ad Group", "").strip()
        if not ad_group:
            issues.append({
                'level': 'campaign',
                'severity': 'warning',
                'row_number': row_num,
                'column': 'Ad Group',
                'issue_type': 'missing_ad_group',
                'message': 'Search campaigns should have ad groups defined',
                'auto_fixable': False
            })

        # Check bid strategy for Search
        bid_strategy = row.get("Bid Strategy Type", "").strip()
        if bid_strategy and bid_strategy not in ['Manual CPC', 'Target CPA', 'Target ROAS']:
            issues.append({
                'level': 'campaign',
                'severity': 'error',
                'row_number': row_num,
                'column': 'Bid Strategy Type',
                'issue_type': 'invalid_bid_strategy',
                'message': f'Invalid bid strategy for Search: {bid_strategy}',
                'auto_fixable': False
            })

        return issues

    def _validate_ad_schedule(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate ad scheduling"""
        issues = []

        ad_schedule = row.get("Ad Schedule", "").strip()
        if ad_schedule:
            # Basic format check - should contain day/time patterns
            if not ('[' in ad_schedule and ']' in ad_schedule):
                issues.append({
                    'level': 'campaign',
                    'severity': 'error',
                    'row_number': row_num,
                    'column': 'Ad Schedule',
                    'issue_type': 'invalid_ad_schedule_format',
                    'message': f'Invalid ad schedule format: {ad_schedule}',
                    'suggestion': 'Use format like (Monday[09:00-17:00]);(Tuesday[09:00-17:00])',
                    'auto_fixable': False
                })

        return issues

    def _validate_language(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate language settings"""
        issues = []

        language = row.get("Languages", "").strip()
        if language and language not in ['en', 'es', 'fr', 'de', 'it', 'pt', 'ja', 'ko', 'zh-CN', 'zh-TW']:
            issues.append({
                'level': 'campaign',
                'severity': 'info',
                'row_number': row_num,
                'column': 'Languages',
                'issue_type': 'non_standard_language',
                'message': f'Non-standard language code: {language}',
                'auto_fixable': False
            })

        return issues

    def _validate_bid_strategy(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate bid strategy settings"""
        issues = []

        bid_strategy_type = row.get("Bid Strategy Type", "").strip()
        bid_strategy_name = row.get("Bid Strategy Name", "").strip()

        campaign_type = row.get("Campaign Type", "").strip()

        # Performance Max should use Maximize conversions
        if campaign_type == "Performance Max" and bid_strategy_type != "Maximize conversions":
            issues.append({
                'level': 'campaign',
                'severity': 'warning',
                'row_number': row_num,
                'column': 'Bid Strategy Type',
                'issue_type': 'pmax_bid_strategy',
                'message': f'Performance Max campaigns should use "Maximize conversions": {bid_strategy_type}',
                'suggestion': 'Change to "Maximize conversions"',
                'auto_fixable': True,
                'original_value': bid_strategy_type,
                'fixed_value': 'Maximize conversions'
            })

        return issues