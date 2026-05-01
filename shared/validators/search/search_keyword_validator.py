#!/usr/bin/env python3
"""
Search Keyword Validator

Validates keyword targeting and bidding for Search campaigns.
Ensures keywords are properly formatted and bids are within acceptable ranges.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class ValidationIssue:
    """Represents a validation issue found during Search keyword validation."""
    level: str
    severity: str  # 'critical', 'warning', 'info'
    row_number: int
    column: str
    issue_type: str
    message: str
    suggestion: str = ""
    auto_fixable: bool = False


class SearchKeywordValidator:
    """
    Validates keyword targeting and bidding for Search campaigns.

    Focuses on Search-specific keyword validation including:
    - Keyword match type formatting
    - CPC bid validation
    - Keyword quality and relevance
    - Negative keyword validation
    """

    def __init__(self, validation_rules: Optional[Dict[str, Any]] = None):
        """Initialize SearchKeywordValidator with validation rules."""
        self.validation_rules = validation_rules or self._get_default_rules()

        # Keyword match type patterns
        self.match_type_patterns = {
            'broad': re.compile(r'^[^"\[\]]+$'),  # No quotes or brackets
            'phrase': re.compile(r'^"[^"]+"$'),    # Surrounded by quotes
            'exact': re.compile(r'^\[[^\[\]]+\]$'), # Surrounded by brackets
            'negative': re.compile(r'^-.*$')       # Starts with minus
        }

        # Valid keyword statuses
        self.valid_keyword_statuses = ['Enabled', 'Paused', 'Removed']

        # CPC bid ranges
        self.min_cpc = 0.01
        self.max_cpc = 50.00
        self.recommended_max_cpc = 10.00

        # Keyword quality thresholds
        self.max_keyword_length = 80  # Google limit
        self.min_keyword_length = 1

    def _get_default_rules(self) -> Dict[str, Any]:
        """Get default validation rules for Search keywords."""
        return {
            'keyword': {
                'required_fields': ['Keyword', 'Criterion Type'],
                'match_types': {
                    'broad': {'pattern': '^[^"\\[\\]]+$', 'description': 'General term matching'},
                    'phrase': {'pattern': '^"[^"]+"$', 'description': 'Exact phrase matching'},
                    'exact': {'pattern': '^\\[[^\\[\\]]+\\]$', 'description': 'Exact term matching'},
                    'negative': {'pattern': '^-.*$', 'description': 'Exclude these terms'}
                },
                'bid_validation': {
                    'min_cpc': 0.01,
                    'max_cpc': 50.00,
                    'recommended_max': 10.00
                },
                'quality_checks': {
                    'max_length': 80,
                    'min_length': 1,
                    'special_chars_allowed': [' ', '-', '_', '&', '+', '/', "'", '"', '[', ']']
                }
            }
        }

    def _identify_match_type(self, keyword: str) -> str:
        """
        Identify the match type of a keyword based on its formatting.

        Args:
            keyword: The keyword string

        Returns:
            Match type: 'broad', 'phrase', 'exact', 'negative', or 'unknown'
        """
        keyword = keyword.strip()

        if self.match_type_patterns['negative'].match(keyword):
            return 'negative'
        elif self.match_type_patterns['exact'].match(keyword):
            return 'exact'
        elif self.match_type_patterns['phrase'].match(keyword):
            return 'phrase'
        elif self.match_type_patterns['broad'].match(keyword):
            return 'broad'
        else:
            return 'unknown'

    def _extract_keyword_text(self, keyword: str) -> str:
        """
        Extract the actual keyword text from formatted keyword.

        Args:
            keyword: Formatted keyword (e.g., "keyword phrase", [exact match])

        Returns:
            Clean keyword text
        """
        keyword = keyword.strip()

        if keyword.startswith('[') and keyword.endswith(']'):
            return keyword[1:-1]
        elif keyword.startswith('"') and keyword.endswith('"'):
            return keyword[1:-1]
        elif keyword.startswith('-'):
            return keyword[1:]
        else:
            return keyword

    def validate_keyword_row(self, row: Dict[str, Any], row_number: int) -> List[ValidationIssue]:
        """
        Validate a single keyword row for Search campaign compliance.

        Args:
            row: Dictionary representing a CSV row
            row_number: Row number in the CSV (for error reporting)

        Returns:
            List of validation issues found
        """
        issues = []

        # Validate Keyword field
        keyword = row.get('Keyword', '').strip()
        if not keyword:
            issues.append(ValidationIssue(
                level='keyword',
                severity='critical',
                row_number=row_number,
                column='Keyword',
                issue_type='missing_keyword',
                message='Keyword is required',
                suggestion='Provide a keyword to target'
            ))
            return issues  # Can't validate further without keyword

        # Validate keyword length
        keyword_text = self._extract_keyword_text(keyword)
        if len(keyword_text) < self.min_keyword_length:
            issues.append(ValidationIssue(
                level='keyword',
                severity='critical',
                row_number=row_number,
                column='Keyword',
                issue_type='keyword_too_short',
                message=f'Keyword "{keyword_text}" is too short (minimum {self.min_keyword_length} character)',
                suggestion='Use more specific keywords'
            ))
        elif len(keyword_text) > self.max_keyword_length:
            issues.append(ValidationIssue(
                level='keyword',
                severity='critical',
                row_number=row_number,
                column='Keyword',
                issue_type='keyword_too_long',
                message=f'Keyword "{keyword_text}" is {len(keyword_text)} characters (maximum {self.max_keyword_length})',
                suggestion='Shorten keyword to fit Google limit'
            ))

        # Validate match type formatting
        match_type = self._identify_match_type(keyword)
        if match_type == 'unknown':
            issues.append(ValidationIssue(
                level='keyword',
                severity='critical',
                row_number=row_number,
                column='Keyword',
                issue_type='invalid_match_type_format',
                message=f'Keyword "{keyword}" has invalid match type formatting',
                suggestion='Use: broad (keyword), phrase ("keyword phrase"), exact ([keyword]), negative (-keyword)'
            ))

        # Validate Criterion Type field
        criterion_type = row.get('Criterion Type', '').strip()
        expected_criterion_types = ['Keyword', 'Negative keyword']

        if not criterion_type:
            issues.append(ValidationIssue(
                level='keyword',
                severity='critical',
                row_number=row_number,
                column='Criterion Type',
                issue_type='missing_criterion_type',
                message='Criterion Type is required',
                suggestion='Set to "Keyword" for targeting or "Negative keyword" for exclusion'
            ))
        elif criterion_type not in expected_criterion_types:
            issues.append(ValidationIssue(
                level='keyword',
                severity='critical',
                row_number=row_number,
                column='Criterion Type',
                issue_type='invalid_criterion_type',
                message=f'Criterion Type "{criterion_type}" is not valid',
                suggestion=f'Use "Keyword" or "Negative keyword"'
            ))
        else:
            # Check consistency between keyword formatting and criterion type
            if criterion_type == 'Negative keyword' and not keyword.startswith('-'):
                issues.append(ValidationIssue(
                    level='keyword',
                    severity='critical',
                    row_number=row_number,
                    column='Keyword',
                    issue_type='negative_keyword_format_mismatch',
                    message='Negative keyword should start with "-"',
                    suggestion=f'Format as: -{keyword_text}'
                ))
            elif criterion_type == 'Keyword' and keyword.startswith('-'):
                issues.append(ValidationIssue(
                    level='keyword',
                    severity='critical',
                    row_number=row_number,
                    column='Keyword',
                    issue_type='positive_keyword_format_mismatch',
                    message='Positive keyword should not start with "-"',
                    suggestion=f'Remove "-" prefix: {keyword_text}'
                ))

        # Validate keyword status
        keyword_status = row.get('Keyword status', '').strip()
        if keyword_status and keyword_status not in self.valid_keyword_statuses:
            issues.append(ValidationIssue(
                level='keyword',
                severity='warning',
                row_number=row_number,
                column='Keyword status',
                issue_type='invalid_keyword_status',
                message=f'Keyword status "{keyword_status}" is not standard',
                suggestion=f'Use one of: {", ".join(self.valid_keyword_statuses)}'
            ))

        # Validate CPC bid
        cpc_bid_str = row.get('CPC bid', '').strip()
        if cpc_bid_str:
            try:
                cpc_bid = float(cpc_bid_str.replace('$', '').replace(',', ''))

                if cpc_bid < self.min_cpc:
                    issues.append(ValidationIssue(
                        level='keyword',
                        severity='critical',
                        row_number=row_number,
                        column='CPC bid',
                        issue_type='cpc_too_low',
                        message=f'CPC bid ${cpc_bid:.2f} is below minimum ${self.min_cpc:.2f}',
                        suggestion=f'Increase bid to at least ${self.min_cpc:.2f}'
                    ))
                elif cpc_bid > self.max_cpc:
                    issues.append(ValidationIssue(
                        level='keyword',
                        severity='critical',
                        row_number=row_number,
                        column='CPC bid',
                        issue_type='cpc_too_high',
                        message=f'CPC bid ${cpc_bid:.2f} exceeds maximum ${self.max_cpc:.2f}',
                        suggestion=f'Reduce bid to ${self.max_cpc:.2f} or less'
                    ))
                elif cpc_bid > self.recommended_max_cpc:
                    issues.append(ValidationIssue(
                        level='keyword',
                        severity='warning',
                        row_number=row_number,
                        column='CPC bid',
                        issue_type='cpc_highly_recommended',
                        message=f'CPC bid ${cpc_bid:.2f} is above recommended maximum ${self.recommended_max_cpc:.2f}',
                        suggestion='Consider lowering bid for better ROI'
                    ))

            except ValueError:
                issues.append(ValidationIssue(
                    level='keyword',
                    severity='critical',
                    row_number=row_number,
                    column='CPC bid',
                    issue_type='invalid_cpc_format',
                    message=f'Invalid CPC bid format: "{cpc_bid_str}"',
                    suggestion='Use numeric format (e.g., 2.50 or $2.50)'
                ))

        # Check for keyword quality issues
        if keyword_text:
            # Check for excessive special characters
            special_chars = re.findall(r'[^a-zA-Z0-9\s\-_&+/\']', keyword_text)
            if len(special_chars) > 2:
                issues.append(ValidationIssue(
                    level='keyword',
                    severity='warning',
                    row_number=row_number,
                    column='Keyword',
                    issue_type='excessive_special_chars',
                    message=f'Keyword contains many special characters: "{keyword_text}"',
                    suggestion='Simplify keyword to improve quality score'
                ))

            # Check for very short words (potential low quality)
            words = keyword_text.split()
            if len(words) > 0 and any(len(word) < 3 for word in words if len(word) > 0):
                issues.append(ValidationIssue(
                    level='keyword',
                    severity='info',
                    row_number=row_number,
                    column='Keyword',
                    issue_type='short_words',
                    message=f'Keyword contains very short words: "{keyword_text}"',
                    suggestion='Consider using more specific, longer keywords'
                ))

        return issues

    def validate_keyword_data(self, keyword_rows: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """
        Validate keyword-level data across multiple rows.

        Args:
            keyword_rows: List of keyword row dictionaries

        Returns:
            List of validation issues found
        """
        issues = []

        if not keyword_rows:
            return issues

        # Validate each keyword row
        for i, row in enumerate(keyword_rows):
            row_issues = self.validate_keyword_row(row, i + 2)  # +2 because row 1 is headers
            issues.extend(row_issues)

        # Cross-keyword validation
        keywords_by_adgroup = {}
        keyword_counts = {'broad': 0, 'phrase': 0, 'exact': 0, 'negative': 0}

        for row in keyword_rows:
            adgroup = row.get('Ad group', 'unknown')
            keyword = row.get('Keyword', '').strip()
            criterion_type = row.get('Criterion Type', '').strip()

            if adgroup not in keywords_by_adgroup:
                keywords_by_adgroup[adgroup] = {'positive': [], 'negative': []}

            if criterion_type == 'Negative keyword':
                keywords_by_adgroup[adgroup]['negative'].append(keyword)
            else:
                keywords_by_adgroup[adgroup]['positive'].append(keyword)

            # Count match types
            match_type = self._identify_match_type(keyword)
            if match_type in keyword_counts:
                keyword_counts[match_type] += 1

        # Validate ad group keyword distribution
        for adgroup, keywords in keywords_by_adgroup.items():
            positive_count = len(keywords['positive'])
            negative_count = len(keywords['negative'])

            if positive_count == 0:
                issues.append(ValidationIssue(
                    level='keyword',
                    severity='critical',
                    row_number=0,
                    column='Keyword',
                    issue_type='no_positive_keywords',
                    message=f'Ad group "{adgroup}" has no positive keywords to target',
                    suggestion='Add positive keywords to enable targeting'
                ))

            if positive_count > 20000:  # Google limit per ad group
                issues.append(ValidationIssue(
                    level='keyword',
                    severity='warning',
                    row_number=0,
                    column='Keyword',
                    issue_type='too_many_keywords',
                    message=f'Ad group "{adgroup}" has {positive_count} keywords (Google limit: 20,000)',
                    suggestion='Consider splitting into multiple ad groups'
                ))

            if negative_count > 5000:  # Google limit per ad group
                issues.append(ValidationIssue(
                    level='keyword',
                    severity='warning',
                    row_number=0,
                    column='Keyword',
                    issue_type='too_many_negative_keywords',
                    message=f'Ad group "{adgroup}" has {negative_count} negative keywords (Google limit: 5,000)',
                    suggestion='Review and consolidate negative keywords'
                ))

        # Validate match type distribution (recommendations)
        total_keywords = sum(keyword_counts.values())
        if total_keywords > 0:
            exact_percentage = (keyword_counts['exact'] / total_keywords) * 100
            if exact_percentage < 20:
                issues.append(ValidationIssue(
                    level='keyword',
                    severity='info',
                    row_number=0,
                    column='Keyword',
                    issue_type='low_exact_match_usage',
                    message='.1f',
                    suggestion='Consider adding more exact match keywords for better control'
                ))

        return issues
