#!/usr/bin/env python3
"""
Search Campaign Validator

Coordinates validation for Google Ads Search campaigns.
Validates ad groups, keywords, text ads, and search-specific configurations.
"""

import logging
from typing import Dict, List, Any, Optional
import csv
import io

logger = logging.getLogger(__name__)


class SearchValidator:
    """
    Comprehensive validator for Google Ads Search campaigns.

    Validates Search campaigns across all levels:
    - Campaign settings (search-specific)
    - Ad group structure and configuration
    - Keyword targeting and match types
    - Text ad format and content
    - Search-specific bidding and targeting
    """

    def __init__(self):
        # Import search-specific validators
        from .search_campaign_validator import SearchCampaignValidator
        from .ad_group_validator import AdGroupValidator
        from .keyword_validator import KeywordValidator
        from .text_ad_validator import TextAdValidator

        self.campaign_validator = SearchCampaignValidator()
        self.ad_group_validator = AdGroupValidator()
        self.keyword_validator = KeywordValidator()
        self.text_ad_validator = TextAdValidator()

    def validate_search_csv(self, csv_path: str, csv_content: str) -> List[Dict[str, Any]]:
        """
        Validate a Search campaign CSV file.

        Args:
            csv_path: Path to the CSV file
            csv_content: CSV content as string

        Returns:
            List of validation issues found
        """
        issues = []

        try:
            csv_io = io.StringIO(csv_content)
            reader = csv.DictReader(csv_io, delimiter='\t')

            # Track ad groups and their contents
            ad_groups_data = {}

            for row_num, row in enumerate(reader, 2):
                campaign_type = row.get("Campaign Type", "").strip()

                # Only validate Search campaigns
                if campaign_type == "Search":
                    # Campaign-level validation
                    campaign_issues = self.campaign_validator.validate_search_campaign_settings(
                        csv_path, row, row_num
                    )
                    issues.extend(campaign_issues)

                    # Ad group validation
                    ad_group_issues = self.ad_group_validator.validate_ad_group(
                        csv_path, row, row_num, ad_groups_data
                    )
                    issues.extend(ad_group_issues)

                    # Keyword validation
                    keyword_issues = self.keyword_validator.validate_keywords(
                        csv_path, row, row_num
                    )
                    issues.extend(keyword_issues)

                    # Text ad validation
                    text_ad_issues = self.text_ad_validator.validate_text_ad(
                        csv_path, row, row_num
                    )
                    issues.extend(text_ad_issues)

            # Cross-ad-group validation
            cross_group_issues = self._validate_cross_ad_group_relationships(ad_groups_data)
            issues.extend(cross_group_issues)

        except Exception as e:
            issues.append({
                'level': 'search_campaign',
                'severity': 'critical',
                'row_number': 0,
                'column': '',
                'issue_type': 'validation_error',
                'message': f'Failed to validate search campaign: {e}',
                'auto_fixable': False
            })

        return issues

    def _validate_cross_ad_group_relationships(self, ad_groups_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate relationships between ad groups"""
        issues = []

        # Check for ad groups with too many keywords
        for ad_group_name, data in ad_groups_data.items():
            keyword_count = data.get('keyword_count', 0)

            # Google recommends no more than 20,000 keywords per ad group
            if keyword_count > 20000:
                issues.append({
                    'level': 'ad_group',
                    'severity': 'error',
                    'row_number': 0,  # Cross-ad-group issue
                    'column': 'Ad group',
                    'issue_type': 'too_many_keywords',
                    'message': f'Ad group "{ad_group_name}" has {keyword_count} keywords (max recommended: 20,000)',
                    'auto_fixable': False
                })

            # Check for ad groups with no keywords
            elif keyword_count == 0:
                issues.append({
                    'level': 'ad_group',
                    'severity': 'error',
                    'row_number': 0,
                    'column': 'Ad group',
                    'issue_type': 'no_keywords',
                    'message': f'Ad group "{ad_group_name}" has no keywords',
                    'auto_fixable': False
                })

        return issues

    def get_search_campaign_requirements(self) -> Dict[str, Any]:
        """
        Get requirements for Search campaigns.

        Returns:
            Dictionary of Search campaign requirements
        """
        return {
            'campaign_type': 'Search',
            'required_headers': [
                'Campaign', 'Campaign Type', 'Ad group', 'Keyword', 'Criterion Type',
                'Headline 1', 'Headline 2', 'Headline 3', 'Description 1', 'Description 2'
            ],
            'ad_group_limits': {
                'max_keywords': 20000,
                'min_keywords': 1
            },
            'text_ad_limits': {
                'max_headlines': 3,
                'max_descriptions': 2,
                'headline_length': {'min': 25, 'max': 30},
                'description_length': {'min': 80, 'max': 90}
            },
            'keyword_match_types': ['Exact', 'Phrase', 'Broad'],
            'bidding_strategies': [
                'Manual CPC', 'Manual CPM', 'Target CPA', 'Target ROAS',
                'Maximize Clicks', 'Maximize Conversions', 'Maximize Conversion Value'
            ]
        }