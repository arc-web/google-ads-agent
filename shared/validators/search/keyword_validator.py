#!/usr/bin/env python3
"""
Keyword Validator for Search Campaigns

Validates keyword targeting, match types, and keyword quality for Search campaigns.
"""

import logging
from typing import Dict, List, Any, Optional
import re

logger = logging.getLogger(__name__)


class KeywordValidator:
    """Validates keyword targeting for Search campaigns"""

    def __init__(self):
        # Valid match types
        self.valid_match_types = ['Exact', 'Phrase', 'Broad']

        # Keyword quality indicators
        self.keyword_pattern = r'^[A-Za-z0-9\s\-\&\(\)\'\"]{1,80}$'

        # Common negative keyword patterns to flag
        self.potential_negative_keywords = [
            'free', 'cheap', 'download', 'pdf', 'video', 'tutorial',
            'how to', 'guide', 'review', 'comparison', 'vs', 'versus'
        ]

        # Maximum keywords per ad group (Google's limit)
        self.max_keywords_per_ad_group = 20000

    def validate_keywords(self, csv_path: str, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        """Validate keyword settings in a Search campaign row"""
        issues = []

        campaign_type = row.get("Campaign Type", "").strip()
        if campaign_type != "Search":
            return issues

        keyword = row.get("Keyword", "").strip()
        if not keyword:
            # Keywords are optional in some rows (e.g., just ad rows)
            return issues

        # Validate keyword format
        if not re.match(self.keyword_pattern, keyword):
            issues.append({
                'level': 'keyword',
                'severity': 'warning',
                'row_number': row_num,
                'column': 'Keyword',
                'issue_type': 'invalid_keyword_format',
                'message': f'Keyword "{keyword}" contains invalid characters or is too long',
                'suggestion': 'Use only letters, numbers, spaces, hyphens, and basic punctuation (max 80 chars)',
                'auto_fixable': False
            })

        # Validate match type
        criterion_type = row.get("Criterion Type", "").strip()
        if not criterion_type:
            issues.append({
                'level': 'keyword',
                'severity': 'error',
                'row_number': row_num,
                'column': 'Criterion Type',
                'issue_type': 'missing_match_type',
                'message': f'Keyword "{keyword}" missing match type',
                'auto_fixable': True,
                'original_value': '',
                'fixed_value': 'Exact'  # Default to Exact
            })
        elif criterion_type not in self.valid_match_types:
            issues.append({
                'level': 'keyword',
                'severity': 'error',
                'row_number': row_num,
                'column': 'Criterion Type',
                'issue_type': 'invalid_match_type',
                'message': f'Invalid match type "{criterion_type}". Valid: {self.valid_match_types}',
                'auto_fixable': True,
                'original_value': criterion_type,
                'fixed_value': 'Exact'
            })

        # Validate keyword status
        keyword_status = row.get("Status", "").strip()
        if keyword_status and keyword_status not in ['Enabled', 'Paused', 'Removed']:
            issues.append({
                'level': 'keyword',
                'severity': 'error',
                'row_number': row_num,
                'column': 'Status',
                'issue_type': 'invalid_keyword_status',
                'message': f'Invalid keyword status: "{keyword_status}". Valid: Enabled, Paused, Removed',
                'auto_fixable': True,
                'original_value': keyword_status,
                'fixed_value': 'Enabled'
            })

        # Check for potentially problematic keywords
        keyword_lower = keyword.lower()

        # Flag single-word broad match keywords (often too broad)
        if criterion_type == 'Broad' and len(keyword.split()) == 1:
            issues.append({
                'level': 'keyword',
                'severity': 'warning',
                'row_number': row_num,
                'column': 'Keyword',
                'issue_type': 'single_word_broad_match',
                'message': f'Single-word Broad match keyword "{keyword}" may be too broad and expensive',
                'suggestion': 'Consider using Phrase or Exact match, or adding modifiers',
                'auto_fixable': False
            })

        # Flag keywords that might be better as negative keywords
        for negative_pattern in self.potential_negative_keywords:
            if negative_pattern in keyword_lower and len(keyword.split()) <= 3:
                issues.append({
                    'level': 'keyword',
                    'severity': 'info',
                    'row_number': row_num,
                    'column': 'Keyword',
                    'issue_type': 'potential_negative_keyword',
                    'message': f'Keyword "{keyword}" contains terms often used as negative keywords',
                    'suggestion': 'Consider if this should be a negative keyword instead',
                    'auto_fixable': False
                })
                break  # Only flag once per keyword

        # Validate keyword length
        word_count = len(keyword.split())
        if word_count > 10:
            issues.append({
                'level': 'keyword',
                'severity': 'warning',
                'row_number': row_num,
                'column': 'Keyword',
                'issue_type': 'long_keyword_phrase',
                'message': f'Very long keyword phrase "{keyword}" ({word_count} words) may have low search volume',
                'suggestion': 'Consider breaking into shorter, more targeted keywords',
                'auto_fixable': False
            })

        # Check for duplicate keywords (would need cross-row validation)
        # This would be handled at the ad group level

        # Validate search theme (for broad match keywords)
        search_theme = row.get("Search theme", "").strip()
        if not search_theme and criterion_type == 'Broad':
            issues.append({
                'level': 'keyword',
                'severity': 'info',
                'row_number': row_num,
                'column': 'Search theme',
                'issue_type': 'missing_search_theme',
                'message': f'Broad match keyword "{keyword}" missing search theme',
                'suggestion': 'Search themes help Google understand keyword context',
                'auto_fixable': False
            })

        return issues

    def validate_keyword_quality(self, keyword: str, match_type: str) -> Dict[str, Any]:
        """
        Assess keyword quality and provide recommendations.

        Args:
            keyword: The keyword text
            match_type: The match type (Exact/Phrase/Broad)

        Returns:
            Dictionary with quality assessment
        """
        quality_score = 0
        recommendations = []

        # Length assessment
        word_count = len(keyword.split())
        if 2 <= word_count <= 4:
            quality_score += 2  # Good length
        elif word_count == 1:
            quality_score += 1  # Single words can work but may be broad
        else:
            recommendations.append("Consider shorter keyword phrases for better performance")

        # Match type assessment
        if match_type == 'Exact':
            quality_score += 3  # Most targeted
        elif match_type == 'Phrase':
            quality_score += 2  # Good balance
        elif match_type == 'Broad':
            quality_score += 1  # Can be expensive/unpredictable
            recommendations.append("Broad match can be expensive; monitor performance closely")

        # Commercial intent assessment
        commercial_indicators = ['buy', 'purchase', 'price', 'cost', 'quote', 'estimate']
        has_commercial_intent = any(indicator in keyword.lower() for indicator in commercial_indicators)
        if has_commercial_intent:
            quality_score += 2

        # Competition assessment (rough heuristic)
        competitive_terms = ['insurance', 'lawyer', 'attorney', 'doctor']
        high_competition = any(term in keyword.lower() for term in competitive_terms)
        if high_competition:
            recommendations.append("High competition keyword; may require higher bids")

        return {
            'keyword': keyword,
            'quality_score': quality_score,
            'max_score': 7,
            'recommendations': recommendations,
            'quality_rating': 'High' if quality_score >= 5 else 'Medium' if quality_score >= 3 else 'Low'
        }