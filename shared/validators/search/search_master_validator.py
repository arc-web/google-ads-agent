#!/usr/bin/env python3
"""
Search Master Validator

Orchestrates all Search campaign validation components.
Provides hierarchical validation from campaign to targeting level.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .search_campaign_validator import SearchCampaignValidator, ValidationIssue
from .search_adgroup_validator import SearchAdGroupValidator
from .search_keyword_validator import SearchKeywordValidator
from .search_text_ad_validator import SearchTextAdValidator
from .search_location_validator import SearchLocationValidator
from .search_schedule_validator import SearchScheduleValidator
from .search_budget_validator import SearchBudgetValidator
from .search_bid_strategy_validator import SearchBidStrategyValidator


@dataclass
class ValidationReport:
    """Comprehensive validation report for Search campaigns."""
    csv_file: str
    total_issues: int
    critical_issues: int
    warning_issues: int
    info_issues: int
    issues_by_level: Dict[str, int]
    validation_time: str
    success: bool


class SearchMasterValidator:
    """
    Master validator for Search campaigns.

    Orchestrates hierarchical validation:
    1. Campaign Level
    2. Ad Group Level
    3. Keyword Level
    4. Text Ad Level
    5. Location Level
    6. Schedule Level
    7. Budget Level
    8. Bid Strategy Level
    """

    def __init__(self, validation_rules: Optional[Dict[str, Any]] = None):
        """Initialize SearchMasterValidator with all component validators."""
        self.validation_rules = validation_rules or self._get_default_rules()

        # Initialize all validators
        self.campaign_validator = SearchCampaignValidator(self.validation_rules)
        self.adgroup_validator = SearchAdGroupValidator(self.validation_rules)
        self.keyword_validator = SearchKeywordValidator(self.validation_rules)
        self.text_ad_validator = SearchTextAdValidator(self.validation_rules)
        self.location_validator = SearchLocationValidator(self.validation_rules)
        self.schedule_validator = SearchScheduleValidator(self.validation_rules)
        self.budget_validator = SearchBudgetValidator(self.validation_rules)
        self.bid_strategy_validator = SearchBidStrategyValidator(self.validation_rules)

        # Validation state
        self.issues: List[ValidationIssue] = []
        self.fixed_issues: List[ValidationIssue] = []

        # Validation hierarchy order
        self.validation_order = [
            'campaign',
            'adgroup',
            'keyword',
            'text_ad',
            'location',
            'schedule',
            'budget',
            'bid_strategy'
        ]

    def _get_default_rules(self) -> Dict[str, Any]:
        """Get default validation rules for Search campaigns."""
        return {
            'search_campaign': {
                'hierarchical_validation': True,
                'stop_on_critical': False,
                'aggregate_cross_level_issues': True
            }
        }

    def validate_csv_file(self, csv_path: str) -> ValidationReport:
        """
        Validate a Search campaign CSV file hierarchically.

        Args:
            csv_path: Path to the CSV file to validate

        Returns:
            Comprehensive validation report
        """
        import csv
        from datetime import datetime

        self.issues = []
        start_time = datetime.now()

        try:
            # Read CSV file
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                # Skip stage comment if present
                first_line = f.readline()
                if first_line.strip().startswith('# STAGE:'):
                    pass  # Skip stage comment
                else:
                    f.seek(0)  # Reset if not a stage comment

                reader = csv.DictReader(f, delimiter='\t')
                rows = list(reader)

            if not rows:
                self.issues.append(ValidationIssue(
                    level='file',
                    severity='critical',
                    row_number=0,
                    column='',
                    issue_type='empty_csv',
                    message='CSV file contains no data rows',
                    suggestion='Ensure CSV has data rows after headers'
                ))
                return self._generate_report(csv_path, start_time)

            # Validate hierarchically
            self._validate_hierarchically(rows)

        except Exception as e:
            self.issues.append(ValidationIssue(
                level='file',
                severity='critical',
                row_number=0,
                column='',
                issue_type='file_read_error',
                message=f'Failed to read CSV file: {str(e)}',
                suggestion='Check file format and permissions'
            ))

        return self._generate_report(csv_path, start_time)

    def _validate_hierarchically(self, rows: List[Dict[str, Any]]) -> None:
        """
        Perform hierarchical validation of Search campaign data.

        Args:
            rows: List of CSV row dictionaries
        """
        # Group rows by validation level
        grouped_data = self._group_rows_by_level(rows)

        # Validate each level in order
        for level in self.validation_order:
            if level in grouped_data and grouped_data[level]:
                level_issues = self._validate_level(level, grouped_data[level])
                self.issues.extend(level_issues)

        # Perform cross-level validation
        cross_level_issues = self._validate_cross_level_consistency(grouped_data)
        self.issues.extend(cross_level_issues)

    def _group_rows_by_level(self, rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group CSV rows by validation level based on content.

        Args:
            rows: All CSV rows

        Returns:
            Dictionary of rows grouped by validation level
        """
        grouped = {
            'campaign': [],
            'adgroup': [],
            'keyword': [],
            'text_ad': [],
            'location': [],
            'schedule': [],
            'budget': [],
            'bid_strategy': []
        }

        for row in rows:
            # Determine row type based on content
            if self._is_campaign_row(row):
                grouped['campaign'].append(row)
            if self._is_adgroup_row(row):
                grouped['adgroup'].append(row)
            if self._is_keyword_row(row):
                grouped['keyword'].append(row)
            if self._is_text_ad_row(row):
                grouped['text_ad'].append(row)
            if self._is_location_row(row):
                grouped['location'].append(row)
            if self._is_schedule_row(row):
                grouped['schedule'].append(row)
            if self._is_budget_row(row):
                grouped['budget'].append(row)
            if self._is_bid_strategy_row(row):
                grouped['bid_strategy'].append(row)

        return grouped

    def _is_campaign_row(self, row: Dict[str, Any]) -> bool:
        """Check if row contains campaign-level data."""
        return bool(row.get('Campaign') and row.get('Campaign type') == 'Search')

    def _is_adgroup_row(self, row: Dict[str, Any]) -> bool:
        """Check if row contains ad group-level data."""
        return bool(row.get('Ad group'))

    def _is_keyword_row(self, row: Dict[str, Any]) -> bool:
        """Check if row contains keyword-level data."""
        return bool(row.get('Keyword'))

    def _is_text_ad_row(self, row: Dict[str, Any]) -> bool:
        """Check if row contains text ad-level data."""
        return bool(row.get('Headline 1') or row.get('Description 1'))

    def _is_location_row(self, row: Dict[str, Any]) -> bool:
        """Check if row contains location-level data."""
        return bool(row.get('Location'))

    def _is_schedule_row(self, row: Dict[str, Any]) -> bool:
        """Check if row contains schedule-level data."""
        return bool(row.get('Ad Schedule'))

    def _is_budget_row(self, row: Dict[str, Any]) -> bool:
        """Check if row contains budget-level data."""
        return bool(row.get('Budget'))

    def _is_bid_strategy_row(self, row: Dict[str, Any]) -> bool:
        """Check if row contains bid strategy-level data."""
        return bool(row.get('Bid Strategy Type') or row.get('Max CPC'))

    def _validate_level(self, level: str, rows: List[Dict[str, Any]]) -> List[ValidationIssue]:
        """
        Validate rows for a specific level using appropriate validator.

        Args:
            level: Validation level name
            rows: Rows to validate for this level

        Returns:
            List of validation issues
        """
        validator_map = {
            'campaign': self.campaign_validator.validate_campaign_data,
            'adgroup': self.adgroup_validator.validate_adgroup_data,
            'keyword': self.keyword_validator.validate_keyword_data,
            'text_ad': self.text_ad_validator.validate_text_ad_data,
            'location': self.location_validator.validate_location_data,
            'schedule': self.schedule_validator.validate_schedule_data,
            'budget': self.budget_validator.validate_budget_data,
            'bid_strategy': self.bid_strategy_validator.validate_bid_strategy_data
        }

        if level in validator_map:
            return validator_map[level](rows)

        return []

    def _validate_cross_level_consistency(self, grouped_data: Dict[str, List[Dict[str, Any]]]) -> List[ValidationIssue]:
        """
        Validate consistency across different validation levels.

        Args:
            grouped_data: Data grouped by validation level

        Returns:
            List of cross-level consistency issues
        """
        issues = []

        # Check campaign-ad group consistency
        campaign_names = set()
        adgroup_campaigns = set()

        for row in grouped_data.get('campaign', []):
            campaign_names.add(row.get('Campaign', ''))

        for row in grouped_data.get('adgroup', []):
            adgroup_campaigns.add(row.get('Campaign', ''))

        # Check for ad groups without campaigns
        orphan_adgroups = adgroup_campaigns - campaign_names
        if orphan_adgroups:
            issues.append(ValidationIssue(
                level='cross_level',
                severity='warning',
                row_number=0,
                column='Campaign',
                issue_type='orphan_adgroups',
                message=f'Ad groups reference campaigns not defined in CSV: {", ".join(orphan_adgroups)}',
                suggestion='Ensure all campaigns referenced by ad groups are defined'
            ))

        # Check keyword-ad group consistency
        adgroup_names = set()
        keyword_adgroups = set()

        for row in grouped_data.get('adgroup', []):
            adgroup_names.add(row.get('Ad group', ''))

        for row in grouped_data.get('keyword', []):
            keyword_adgroups.add(row.get('Ad group', ''))

        # Check for keywords without ad groups
        orphan_keywords = keyword_adgroups - adgroup_names
        if orphan_keywords:
            issues.append(ValidationIssue(
                level='cross_level',
                severity='warning',
                row_number=0,
                column='Ad group',
                issue_type='orphan_keywords',
                message=f'Keywords reference ad groups not defined in CSV: {", ".join(orphan_keywords)}',
                suggestion='Ensure all ad groups referenced by keywords are defined'
            ))

        return issues

    def _generate_report(self, csv_path: str, start_time) -> ValidationReport:
        """
        Generate comprehensive validation report.

        Args:
            csv_path: Path to validated CSV file
            start_time: Validation start time

        Returns:
            ValidationReport object
        """
        from datetime import datetime

        end_time = datetime.now()
        validation_time = f"{(end_time - start_time).total_seconds():.2f}s"

        # Count issues by severity
        critical_count = sum(1 for issue in self.issues if issue.severity == 'critical')
        warning_count = sum(1 for issue in self.issues if issue.severity == 'warning')
        info_count = sum(1 for issue in self.issues if issue.severity == 'info')

        # Count issues by level
        issues_by_level = {}
        for issue in self.issues:
            issues_by_level[issue.level] = issues_by_level.get(issue.level, 0) + 1

        # Determine success (no critical issues)
        success = critical_count == 0

        return ValidationReport(
            csv_file=csv_path,
            total_issues=len(self.issues),
            critical_issues=critical_count,
            warning_issues=warning_count,
            info_issues=info_count,
            issues_by_level=issues_by_level,
            validation_time=validation_time,
            success=success
        )

    def get_detailed_issues(self) -> List[Dict[str, Any]]:
        """
        Get detailed issue information for reporting.

        Returns:
            List of issue dictionaries
        """
        return [
            {
                'level': issue.level,
                'severity': issue.severity,
                'row_number': issue.row_number,
                'column': issue.column,
                'issue_type': issue.issue_type,
                'message': issue.message,
                'suggestion': issue.suggestion,
                'auto_fixable': issue.auto_fixable
            }
            for issue in self.issues
        ]