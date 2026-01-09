#!/usr/bin/env python3
"""
Search Text Ad Validator

Validates text ad content and format for Search campaigns.
Ensures headlines and descriptions meet Google Ads requirements.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class ValidationIssue:
    """Represents a validation issue found during Search text ad validation."""
    level: str
    severity: str  # 'critical', 'warning', 'info'
    row_number: int
    column: str
    issue_type: str
    message: str
    suggestion: str = ""
    auto_fixable: bool = False


class SearchTextAdValidator:
    """
    Validates text ad content and format for Search campaigns.

    Focuses on Search-specific text ad validation including:
    - Headline character limits (25-30 characters each)
    - Description character limits (70-90 characters each)
    - Display path validation
    - Ad text policy compliance
    - Formatting and special character restrictions
    """

    def __init__(self, validation_rules: Optional[Dict[str, Any]] = None):
        """Initialize SearchTextAdValidator with validation rules."""
        self.validation_rules = validation_rules or self._get_default_rules()

        # Headline validation limits
        self.headline_limits = {
            'min_length': 25,
            'max_length': 30,
            'max_headlines': 3
        }

        # Description validation limits
        self.description_limits = {
            'min_length': 70,
            'max_length': 90,
            'max_descriptions': 2
        }

        # Display path limits
        self.display_path_limits = {
            'max_length': 15,
            'max_paths': 2
        }

        # Invalid characters and patterns
        self.invalid_chars = ['|', '\t', '\n', '\r']
        self.excessive_punctuation = re.compile(r'[!?]{3,}|[.]{4,}|[,]{3,}')
        self.repeated_words = re.compile(r'\b(\w+)\s+\1\b', re.IGNORECASE)

        # Policy violation patterns
        self.policy_violations = [
            re.compile(r'\b(?:free|cheap|discount)\b.*\b(?:trial|sample)\b', re.IGNORECASE),
            re.compile(r'\bguarantee\b.*\b(?:100%|full)\b', re.IGNORECASE),
            re.compile(r'\b(?:click here|visit|go to)\b', re.IGNORECASE),
            re.compile(r'\b(?:best|top|leading|#1)\b.*\b(?:rated|reviewed)\b', re.IGNORECASE),
        ]

        # Valid ad types and statuses
        self.valid_ad_types = ['Text ad', 'Responsive search ad', 'Expanded text ad']
        self.valid_ad_statuses = ['Enabled', 'Paused', 'Removed']

    def _get_default_rules(self) -> Dict[str, Any]:
        """Get default validation rules for Search text ads."""
        return {
            'text_ad': {
                'headlines': {
                    'min_length': 25,
                    'max_length': 30,
                    'max_count': 3
                },
                'descriptions': {
                    'min_length': 70,
                    'max_length': 90,
                    'max_count': 2
                },
                'display_paths': {
                    'max_length': 15,
                    'max_count': 2
                },
                'policy_checks': {
                    'prohibited_phrases': [
                        'free trial', '100% guarantee', 'click here',
                        '#1 rated', 'best rated'
                    ]
                }
            }
        }

    def _count_characters(self, text: str) -> int:
        """
        Count characters in text, accounting for special characters.

        Args:
            text: Text to count

        Returns:
            Character count
        """
        return len(text.strip())

    def _validate_text_quality(self, text: str, field_name: str) -> List[str]:
        """
        Validate text quality and return list of issues.

        Args:
            text: Text to validate
            field_name: Name of the field for error messages

        Returns:
            List of quality issue messages
        """
        issues = []

        # Check for invalid characters
        for char in self.invalid_chars:
            if char in text:
                issues.append(f"Contains invalid character '{char}'")

        # Check for excessive punctuation
        if self.excessive_punctuation.search(text):
            issues.append("Contains excessive punctuation")

        # Check for repeated words
        if self.repeated_words.search(text):
            issues.append("Contains repeated words")

        # Check for ALL CAPS (more than 3 consecutive caps)
        all_caps_words = re.findall(r'\b[A-Z]{4,}\b', text)
        if all_caps_words:
            issues.append(f"Contains ALL CAPS words: {', '.join(all_caps_words[:3])}")

        # Check for policy violations
        for pattern in self.policy_violations:
            if pattern.search(text):
                issues.append("May violate Google Ads policies (prohibited phrases)")

        return issues

    def validate_text_ad_row(self, row: Dict[str, Any], row_number: int) -> List[ValidationIssue]:
        """
        Validate a single text ad row for Search campaign compliance.

        Args:
            row: Dictionary representing a CSV row
            row_number: Row number in the CSV (for error reporting)

        Returns:
            List of validation issues found
        """
        issues = []

        # Validate headlines (required)
        headlines = []
        for i in range(1, self.headline_limits['max_headlines'] + 1):
            headline_key = f'Headline {i}'
            headline = row.get(headline_key, '').strip()
            if headline:
                headlines.append((headline_key, headline))

        if not headlines:
            issues.append(ValidationIssue(
                level='text_ad',
                severity='critical',
                row_number=row_number,
                column='Headline 1',
                issue_type='no_headlines',
                message='At least one headline is required for text ads',
                suggestion='Add Headline 1 (25-30 characters recommended)'
            ))
        else:
            # Validate each headline
            for headline_key, headline in headlines:
                char_count = self._count_characters(headline)

                # Check length
                if char_count < self.headline_limits['min_length']:
                    issues.append(ValidationIssue(
                        level='text_ad',
                        severity='critical',
                        row_number=row_number,
                        column=headline_key,
                        issue_type='headline_too_short',
                        message=f'{headline_key} is {char_count} characters (minimum {self.headline_limits["min_length"]})',
                        suggestion=f'Expand headline to at least {self.headline_limits["min_length"]} characters'
                    ))
                elif char_count > self.headline_limits['max_length']:
                    issues.append(ValidationIssue(
                        level='text_ad',
                        severity='critical',
                        row_number=row_number,
                        column=headline_key,
                        issue_type='headline_too_long',
                        message=f'{headline_key} is {char_count} characters (maximum {self.headline_limits["max_length"]})',
                        suggestion=f'Shorten headline to {self.headline_limits["max_length"]} characters or less'
                    ))

                # Check text quality
                quality_issues = self._validate_text_quality(headline, headline_key)
                for issue in quality_issues:
                    severity = 'critical' if 'policy' in issue.lower() else 'warning'
                    issues.append(ValidationIssue(
                        level='text_ad',
                        severity=severity,
                        row_number=row_number,
                        column=headline_key,
                        issue_type='headline_quality_issue',
                        message=f'{headline_key}: {issue}',
                        suggestion='Review and fix text quality issues'
                    ))

        # Validate descriptions (required)
        descriptions = []
        for i in range(1, self.description_limits['max_descriptions'] + 1):
            desc_key = f'Description {i}'
            description = row.get(desc_key, '').strip()
            if description:
                descriptions.append((desc_key, description))

        if not descriptions:
            issues.append(ValidationIssue(
                level='text_ad',
                severity='critical',
                row_number=row_number,
                column='Description 1',
                issue_type='no_descriptions',
                message='At least one description is required for text ads',
                suggestion='Add Description 1 (70-90 characters recommended)'
            ))
        else:
            # Validate each description
            for desc_key, description in descriptions:
                char_count = self._count_characters(description)

                # Check length
                if char_count < self.description_limits['min_length']:
                    issues.append(ValidationIssue(
                        level='text_ad',
                        severity='critical',
                        row_number=row_number,
                        column=desc_key,
                        issue_type='description_too_short',
                        message=f'{desc_key} is {char_count} characters (minimum {self.description_limits["min_length"]})',
                        suggestion=f'Expand description to at least {self.description_limits["min_length"]} characters'
                    ))
                elif char_count > self.description_limits['max_length']:
                    issues.append(ValidationIssue(
                        level='text_ad',
                        severity='critical',
                        row_number=row_number,
                        column=desc_key,
                        issue_type='description_too_long',
                        message=f'{desc_key} is {char_count} characters (maximum {self.description_limits["max_length"]})',
                        suggestion=f'Shorten description to {self.description_limits["max_length"]} characters or less'
                    ))

                # Check text quality
                quality_issues = self._validate_text_quality(description, desc_key)
                for issue in quality_issues:
                    severity = 'critical' if 'policy' in issue.lower() else 'warning'
                    issues.append(ValidationIssue(
                        level='text_ad',
                        severity=severity,
                        row_number=row_number,
                        column=desc_key,
                        issue_type='description_quality_issue',
                        message=f'{desc_key}: {issue}',
                        suggestion='Review and fix text quality issues'
                    ))

        # Validate display paths (optional but recommended)
        display_paths = []
        for i in range(1, self.display_path_limits['max_paths'] + 1):
            path_key = f'Display path {i}'
            path = row.get(path_key, '').strip()
            if path:
                display_paths.append((path_key, path))

        for path_key, path in display_paths:
            char_count = self._count_characters(path)

            if char_count > self.display_path_limits['max_length']:
                issues.append(ValidationIssue(
                    level='text_ad',
                    severity='critical',
                    row_number=row_number,
                    column=path_key,
                    issue_type='display_path_too_long',
                    message=f'{path_key} is {char_count} characters (maximum {self.display_path_limits["max_length"]})',
                    suggestion=f'Shorten display path to {self.display_path_limits["max_length"]} characters or less'
                ))

            # Check for invalid characters in display path
            if any(char in path for char in ['/', '\\', '?', '#', '&']):
                issues.append(ValidationIssue(
                    level='text_ad',
                    severity='critical',
                    row_number=row_number,
                    column=path_key,
                    issue_type='invalid_display_path_chars',
                    message=f'{path_key} contains invalid characters',
                    suggestion='Use only letters, numbers, and hyphens in display paths'
                ))

        # Validate ad type
        ad_type = row.get('Ad type', '').strip()
        if ad_type and ad_type not in self.valid_ad_types:
            issues.append(ValidationIssue(
                level='text_ad',
                severity='warning',
                row_number=row_number,
                column='Ad type',
                issue_type='invalid_ad_type',
                message=f'Ad type "{ad_type}" is not standard for Search campaigns',
                suggestion=f'Use one of: {", ".join(self.valid_ad_types)}'
            ))

        # Validate ad status
        ad_status = row.get('Ad status', '').strip()
        if ad_status and ad_status not in self.valid_ad_statuses:
            issues.append(ValidationIssue(
                level='text_ad',
                severity='warning',
                row_number=row_number,
                column='Ad status',
                issue_type='invalid_ad_status',
                message=f'Ad status "{ad_status}" is not standard',
                suggestion=f'Use one of: {", ".join(self.valid_ad_statuses)}'
            ))

        return issues

    def validate_text_ad_data(self, text_ad_rows: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """
        Validate text ad-level data across multiple rows.

        Args:
            text_ad_rows: List of text ad row dictionaries

        Returns:
            List of validation issues found
        """
        issues = []

        if not text_ad_rows:
            return issues

        # Validate each text ad row
        for i, row in enumerate(text_ad_rows):
            row_issues = self.validate_text_ad_row(row, i + 2)  # +2 because row 1 is headers
            issues.extend(row_issues)

        # Cross-ad validation
        ad_counts_by_adgroup = {}

        for row in text_ad_rows:
            adgroup = row.get('Ad group', 'unknown')
            campaign = row.get('Campaign', 'unknown')

            key = f"{campaign}|{adgroup}"
            if key not in ad_counts_by_adgroup:
                ad_counts_by_adgroup[key] = 0
            ad_counts_by_adgroup[key] += 1

        # Check for optimal ad distribution
        for adgroup_key, ad_count in ad_counts_by_adgroup.items():
            campaign, adgroup = adgroup_key.split('|', 1)

            if ad_count < 2:
                issues.append(ValidationIssue(
                    level='text_ad',
                    severity='info',
                    row_number=0,
                    column='Ad group',
                    issue_type='few_ads_per_adgroup',
                    message=f'Ad group "{adgroup}" in campaign "{campaign}" has only {ad_count} ads',
                    suggestion='Consider adding more ad variations for better testing and optimization'
                ))
            elif ad_count > 50:
                issues.append(ValidationIssue(
                    level='text_ad',
                    severity='info',
                    row_number=0,
                    column='Ad group',
                    issue_type='many_ads_per_adgroup',
                    message=f'Ad group "{adgroup}" in campaign "{campaign}" has {ad_count} ads',
                    suggestion='Consider consolidating similar ads to improve management'
                ))

        # Check for headline uniqueness
        all_headlines = []
        for row in text_ad_rows:
            for i in range(1, 4):  # Headlines 1-3
                headline = row.get(f'Headline {i}', '').strip()
                if headline:
                    all_headlines.append(headline)

        # Look for duplicate headlines
        headline_counts = {}
        for headline in all_headlines:
            headline_counts[headline] = headline_counts.get(headline, 0) + 1

        duplicates = [h for h, count in headline_counts.items() if count > 1]
        if duplicates:
            issues.append(ValidationIssue(
                level='text_ad',
                severity='info',
                row_number=0,
                column='Headline 1',
                issue_type='duplicate_headlines',
                message=f'Found {len(duplicates)} duplicate headlines across ads',
                suggestion='Use unique headlines to maximize reach and testing'
            ))

        return issues