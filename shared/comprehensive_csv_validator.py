#!/usr/bin/env python3
"""
Comprehensive CSV Validator for Google Ads Agent

This script implements hierarchical validation of Google Ads CSVs across all client directories.
It validates in order: Account Settings → Campaign Settings → Asset Groups → Assets → Targeting.
Auto-heals issues where possible and generates detailed reports.

Usage:
    python comprehensive_csv_validator.py --client <client_name>
    python comprehensive_csv_validator.py --all
    python comprehensive_csv_validator.py --client <client_name> --fix
    python comprehensive_csv_validator.py --client <client_name> --output report.json
"""

import sys
import os
import json
import csv
import io
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import re

# Add paths for imports
sys.path.append('gads/core/business_logic')

try:
    from google_ads_editor_exporter import GoogleAdsEditorExporter
except ImportError:
    GoogleAdsEditorExporter = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Hierarchical validation levels"""
    ACCOUNT = "account"
    CAMPAIGN = "campaign"
    ASSET_GROUP = "asset_group"
    AD_GROUP = "ad_group"
    ASSET = "asset"
    TARGETING = "targeting"


class IssueSeverity(Enum):
    """Issue severity levels"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a validation issue found during testing"""
    level: ValidationLevel
    severity: IssueSeverity
    client_name: str
    csv_file: str
    row_number: int
    column: str
    issue_type: str
    message: str
    suggestion: Optional[str] = None
    auto_fixable: bool = False
    original_value: Optional[str] = None
    fixed_value: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class ValidationReport:
    """Comprehensive validation report for a client"""
    client_name: str
    timestamp: str
    total_rows_validated: int
    issues_found: List[ValidationIssue]
    issues_fixed: List[ValidationIssue]
    summary: Dict[str, Any]
    final_status: str  # 'PASS', 'PASS_WITH_FIXES', 'FAIL'


class ComprehensiveCSVValidator:
    """
    Comprehensive hierarchical CSV validator for Google Ads campaigns.

    Validates CSVs in order:
    1. Account-level settings and structure
    2. Campaign-level configurations
    3. Asset group settings and relationships
    4. Individual assets (headlines, descriptions, images, videos)
    5. Geographic and audience targeting
    """

    def __init__(self, base_path: str = "google_ads_agent"):
        self.base_path = Path(base_path)
        self.exporter = GoogleAdsEditorExporter() if GoogleAdsEditorExporter else None
        self.issues: List[ValidationIssue] = []
        self.fixed_issues: List[ValidationIssue] = []

        # Load validation rules
        self.validation_rules = self._load_validation_rules()

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load comprehensive validation rules"""
        return {
            'account': {
                'required_headers': [
                    'Campaign', 'Asset Group', 'Status', 'Campaign Type', 'Sub Type',
                    'Networks', 'Search Partners', 'Display Network', 'Targeting', 'Ad Schedule', 'Budget', 'Labels',
                    'Campaign Bid Strategy Type', 'Asset Group Bid Strategy Type',
                    'Asset Group Bid Strategy Name', 'Target CPA', 'Max CPC', 'Enhanced CPC',
                    'EU Political Content', 'Keywords', 'Geographic Targeting',
                    'City Targeting', 'ZIP Code Targeting', 'Regional Targeting',
                    'Service Category', 'Priority Level', 'Conversion Actions', 'Ad Group Labels'
                ],
                'campaign_types': [
                    'Search', 'Performance Max', 'Display Network only', 'Shopping', 'Video'
                ],
                'budget_types': ['Daily', 'Monthly'],
                'networks': ['Search'],
                'search_partners_options': ['Disabled'],
                'display_network_options': ['Disabled']
            },
            'campaign': {
                'required_fields': ['campaign_name', 'campaign_type', 'budget'],
                'pmax_requirements': {
                    'brand_guidelines': 'Disabled',
                    'eu_political_ads': "Doesn't have EU political ads"
                },
                'search_requirements': {
                    'ad_groups_required': True
                }
            },
            'asset_group': {
                'max_headlines': 15,
                'max_descriptions': 5,
                'max_videos': 5,
                'required_fields': ['asset_group', 'final_url']
            },
            'asset': {
                'headline_length': {'min': 22, 'max': 30, 'optimal_min': 22, 'optimal_max': 29},
                'description_length': {'min': 75, 'max': 90, 'optimal_min': 75, 'optimal_max': 85},
                'video_formats': ['video/mp4', 'video/avi', 'video/mov'],
                'image_formats': ['image/jpeg', 'image/png', 'image/gif'],
                # Ad copy best practices validation
                'headline_requirements': {
                    'number_one_headlines': {'min_required': 1, 'max_required': 2},
                    'brand_headlines': {'min_required': 2},
                    'service_headlines': {'min_required': 5},
                    'regional_headlines': {'min_required': 5}
                },
                'value_impact_keywords': [
                    'protect your home', 'family safety', 'peace of mind', 'insurance discount',
                    'energy savings', 'property value', 'hurricane protection', 'storm defense',
                    'lifetime guarantee', 'emergency preparedness', 'catastrophic loss prevention'
                ],
                'brand_terms': ['wright\'s impact', 'wright\'s window', 'wright\'s door', 'wrights impact']
            },
            'targeting': {
                'valid_currencies': ['USD', 'EUR', 'GBP'],
                'timezone_pattern': r'^[A-Za-z/_]+$',
                'location_formats': ['city, state', 'zip_code', 'coordinates']
            }
        }

    def validate_client_csvs(self, client_name: str, auto_fix: bool = False,
                           output_path: Optional[str] = None) -> ValidationReport:
        """
        Validate all CSVs for a specific client with hierarchical validation

        Args:
            client_name: Name of client directory
            auto_fix: Whether to auto-fix issues where possible
            output_path: Optional path to save detailed JSON report

        Returns:
            Comprehensive validation report
        """
        logger.info(f"Starting comprehensive validation for client: {client_name}")

        client_path = self.base_path / client_name
        if not client_path.exists():
            raise ValueError(f"Client directory not found: {client_name}")

        # Reset issues
        self.issues = []
        self.fixed_issues = []

        # Find all campaign CSVs (exclude reports, search_themes, etc.)
        campaign_csvs = self._find_campaign_csvs(client_path)

        total_rows = 0

        # Validate each CSV hierarchically
        for csv_file in campaign_csvs:
            logger.info(f"Validating CSV: {csv_file}")
            rows_validated = self._validate_single_csv(client_name, csv_file, auto_fix)
            total_rows += rows_validated

        # Generate report
        report = self._generate_report(client_name, total_rows)

        # Save report if requested
        if output_path:
            self._save_report(report, output_path)

        # Apply fixes if auto_fix enabled
        if auto_fix and self.issues:
            self._apply_fixes(client_name)

        return report

    def _find_campaign_csvs(self, client_path: Path) -> List[Path]:
        """Find all campaign CSV files for a client (excluding reports)"""
        campaign_csvs = []

        # Look in campaigns directory
        campaigns_dir = client_path / 'campaigns'
        if campaigns_dir.exists():
            for csv_file in campaigns_dir.glob('*.csv'):
                # Skip archived files and imports
                if 'archive' not in str(csv_file.parent) and 'import' not in str(csv_file.parent):
                    campaign_csvs.append(csv_file)

        # Also check root level campaign files
        for csv_file in client_path.glob('*.csv'):
            if 'campaign' in csv_file.name.lower() and 'report' not in csv_file.name.lower():
                campaign_csvs.append(csv_file)

        return campaign_csvs

    def _validate_single_csv(self, client_name: str, csv_path: Path, auto_fix: bool) -> int:
        """Validate a single CSV file hierarchically"""
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                csv_content = f.read()

            # Validate CSV structure and headers
            self._validate_csv_structure(client_name, str(csv_path), csv_content)

            # Parse and validate rows hierarchically
            rows_validated = self._validate_csv_rows_hierarchically(client_name, str(csv_path), csv_content)

            # Apply auto-fixes during validation if enabled
            if auto_fix:
                corrected_content = self._apply_auto_fixes_to_csv(csv_content)
                if corrected_content != csv_content:
                    # Save corrected version
                    with open(csv_path, 'w', encoding='utf-8-sig') as f:
                        f.write(corrected_content)
                    logger.info(f"Applied auto-fixes to {csv_path}")

            return rows_validated

        except Exception as e:
            logger.error(f"Error validating {csv_path}: {e}")
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ACCOUNT,
                severity=IssueSeverity.CRITICAL,
                client_name=client_name,
                csv_file=str(csv_path),
                row_number=0,
                column="",
                issue_type="file_error",
                message=f"Failed to validate CSV file: {e}",
                auto_fixable=False
            ))
            return 0

    def _validate_csv_structure(self, client_name: str, csv_path: str, csv_content: str):
        """Validate CSV structure and headers"""
        try:
            # Check for UTF-8 BOM
            if not csv_content.startswith('\ufeff'):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ACCOUNT,
                    severity=IssueSeverity.WARNING,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=0,
                    column="",
                    issue_type="encoding",
                    message="CSV file missing UTF-8 BOM - may cause Excel compatibility issues",
                    suggestion="Add UTF-8 BOM to CSV file",
                    auto_fixable=True
                ))

            # Parse CSV to validate headers (auto-detect delimiter)
            csv_io = io.StringIO(csv_content)
            sample = csv_content[:1024]  # Sample first 1KB
            sniffer = csv.Sniffer()
            try:
                delimiter = sniffer.sniff(sample, delimiters=',\t;|').delimiter
            except:
                delimiter = ','  # Default to comma if detection fails

            reader = csv.DictReader(csv_io, delimiter=delimiter)
            headers = reader.fieldnames or []

            # Determine campaign type from first data row to set appropriate required headers
            first_row = None
            try:
                rows = list(reader)
                if rows:
                    first_row = rows[0]
            except:
                pass

            # Dynamic header validation based on campaign type
            campaign_type = first_row.get('Campaign Type', '').strip() if first_row else ''

            if campaign_type == 'Performance Max':
                required_headers = [
                    'Campaign', 'Asset Group', 'Status', 'Campaign Type', 'Networks',
                    'Budget', 'Final URL', 'Headlines', 'Descriptions'
                ]
            elif campaign_type == 'Search':
                required_headers = [
                    'Campaign', 'Ad Group', 'Status', 'Campaign Type', 'Keywords',
                    'Budget', 'Final URL', 'Headlines', 'Descriptions'
                ]
            else:
                # Fallback to basic required headers
                required_headers = ['Campaign', 'Campaign Type', 'Budget']

            missing_headers = set(required_headers) - set(headers)

            if missing_headers:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ACCOUNT,
                    severity=IssueSeverity.CRITICAL,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=0,
                    column="",
                    issue_type="missing_headers",
                    message=f"Missing required headers for {campaign_type or 'unknown'} campaign type: {missing_headers}",
                    suggestion=f"Ensure CSV has required headers for {campaign_type} campaigns",
                    auto_fixable=False
                ))

        except Exception as e:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ACCOUNT,
                severity=IssueSeverity.CRITICAL,
                client_name=client_name,
                csv_file=csv_path,
                row_number=0,
                column="",
                issue_type="structure_error",
                message=f"Failed to validate CSV structure: {e}",
                auto_fixable=False
            ))

    def _validate_csv_rows_hierarchically(self, client_name: str, csv_path: str, csv_content: str) -> int:
        """Validate CSV rows in hierarchical order"""
        try:
            # Auto-detect delimiter
            sample = csv_content[:1024]
            sniffer = csv.Sniffer()
            try:
                delimiter = sniffer.sniff(sample, delimiters=',\t;|').delimiter
            except:
                delimiter = ','

            csv_io = io.StringIO(csv_content)
            reader = csv.DictReader(csv_io, delimiter=delimiter)

            row_count = 0
            for row_num, row in enumerate(reader, 2):  # Start from 2 (header is 1)
                row_count += 1

                # Level 1: Account-level validation
                self._validate_account_level(client_name, csv_path, row, row_num)

                # Level 2: Campaign-level validation
                self._validate_campaign_level(client_name, csv_path, row, row_num)

                # Level 3: Asset group validation
                self._validate_asset_group_level(client_name, csv_path, row, row_num)

                # Level 4: Asset validation
                self._validate_asset_level(client_name, csv_path, row, row_num)

                # Level 5: Targeting validation
                self._validate_targeting_level(client_name, csv_path, row, row_num)

            return row_count

        except Exception as e:
            logger.error(f"Error in hierarchical validation: {e}")
            return 0

    def _validate_account_level(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int):
        """Validate account-level settings"""
        # Check campaign name
        campaign_name = row.get("Campaign", "").strip()
        if not campaign_name:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ACCOUNT,
                severity=IssueSeverity.CRITICAL,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Campaign",
                issue_type="missing_campaign_name",
                message="Campaign name is required",
                auto_fixable=False
            ))

        # Validate campaign type
        campaign_type = row.get("Campaign Type", "").strip()
        valid_types = self.validation_rules['account']['campaign_types']
        if campaign_type and campaign_type not in valid_types:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ACCOUNT,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Campaign Type",
                issue_type="invalid_campaign_type",
                message=f"Invalid campaign type '{campaign_type}'. Valid types: {valid_types}",
                auto_fixable=False
            ))

    def _validate_campaign_level(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int):
        """Validate campaign-level settings"""
        campaign_type = row.get("Campaign Type", "").strip()

        # Budget validation
        budget = row.get("Budget", "").strip()
        if budget:
            try:
                budget_val = float(budget)
                if budget_val <= 0:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.CAMPAIGN,
                        severity=IssueSeverity.ERROR,
                        client_name=client_name,
                        csv_file=csv_path,
                        row_number=row_num,
                        column="Budget",
                        issue_type="invalid_budget",
                        message=f"Budget must be greater than 0: {budget}",
                        auto_fixable=False
                    ))
            except ValueError:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.CAMPAIGN,
                    severity=IssueSeverity.ERROR,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Budget",
                    issue_type="invalid_budget_format",
                    message=f"Invalid budget format: {budget}",
                    auto_fixable=False
                ))

        # PMAX-specific validations
        if campaign_type == "Performance Max":
            self._validate_pmax_campaign(client_name, csv_path, row, row_num)

        # Search campaign validations
        elif campaign_type == "Search":
            self._validate_search_campaign(client_name, csv_path, row, row_num)

    def _validate_pmax_campaign(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int):
        """Validate Performance Max campaign settings"""
        pmax_rules = self.validation_rules['campaign']['pmax_requirements']

        # Check brand guidelines
        brand_guidelines = row.get("Brand guidelines", "").strip()
        if brand_guidelines not in ["Disabled", "Enabled"]:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.CAMPAIGN,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Brand guidelines",
                issue_type="invalid_brand_guidelines",
                message=f"Brand guidelines must be 'Disabled' or 'Enabled': {brand_guidelines}",
                suggestion="Set to 'Disabled' for PMAX campaigns",
                auto_fixable=True,
                original_value=brand_guidelines
            ))

        # Check EU political ads
        eu_ads = row.get("EU political ads", "").strip()
        expected = pmax_rules['eu_political_ads']
        if eu_ads != expected:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.CAMPAIGN,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="EU political ads",
                issue_type="invalid_eu_political_ads",
                message=f"EU political ads should be '{expected}': {eu_ads}",
                suggestion=f"Set to '{expected}'",
                auto_fixable=True,
                original_value=eu_ads
            ))

    def _validate_search_campaign(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int):
        """ARCHITECTURAL VIOLATION: This function mixes Search and PMAX logic"""
        # CRITICAL: Search campaigns use AD GROUPS, not ASSET GROUPS
        # This function is checking for "Asset Group" in Search campaigns - WRONG!

        campaign_name = row.get("Campaign", "").strip()
        asset_group = row.get("Asset Group", "").strip()  # THIS IS WRONG FOR SEARCH
        campaign_type = row.get("Campaign Type", "").strip()

        # Validate county campaign structure (Wright's specific)
        if "broward" in campaign_name.lower() and "wrights" in campaign_name.lower():
            # Should be ONE county campaign with city AD GROUPS underneath (NOT asset groups)
            if not campaign_name.endswith("_search"):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.CAMPAIGN,
                    severity=IssueSeverity.ERROR,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Campaign",
                    issue_type="invalid_campaign_name",
                    message="Broward campaigns must end with '_search'",
                    auto_fixable=False
                ))

            # CRITICAL: Should validate AD GROUP naming, not ASSET GROUP naming
            if asset_group:  # THIS SHOULD BE "Ad Group" for Search campaigns
                expected_city_patterns = [
                    "_ftl_", "_pb_", "_hwd_", "_cs_", "_pp_", "_miramar_",
                    "fort_lauderdale_", "pompano_beach_", "hollywood_",
                    "coral_springs_", "pembroke_pines_"
                ]
                if not any(pattern in asset_group.lower() for pattern in expected_city_patterns):
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.AD_GROUP,  # Should be AD_GROUP, not ASSET_GROUP
                        severity=IssueSeverity.WARNING,
                        client_name=client_name,
                        csv_file=csv_path,
                        row_number=row_num,
                        column="Ad Group",  # Should be "Ad Group", not "Asset Group"
                        issue_type="invalid_ad_group_name",  # Should be ad_group, not asset_group
                        message="Ad groups should include city identifiers (ftl, pb, hwd, etc.)",
                        auto_fixable=False
                    ))

        # Validate EU Political Content is disabled
        eu_political = row.get("EU Political Content", "").strip()
        if eu_political and eu_political.lower() != "disabled":
            self.issues.append(ValidationIssue(
                level=ValidationLevel.CAMPAIGN,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="EU Political Content",
                issue_type="eu_political_not_disabled",
                message="EU Political Content must be Disabled",
                auto_fixable=True,
                fix_value="Disabled"
            ))

        # Validate Search Partners are disabled for Search campaigns
        if campaign_type == "Search":
            search_partners = row.get("Search Partners", "").strip()
            display_network = row.get("Display Network", "").strip()

            if search_partners and search_partners.lower() != "disabled":
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.CAMPAIGN,
                    severity=IssueSeverity.ERROR,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Search Partners",
                    issue_type="search_partners_not_disabled",
                    message="Search Partners must be Disabled for Search campaigns",
                    auto_fixable=True,
                    fix_value="Disabled"
                ))

            if display_network and display_network.lower() != "disabled":
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.CAMPAIGN,
                    severity=IssueSeverity.ERROR,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Display Network",
                    issue_type="display_network_not_disabled",
                    message="Display Network must be Disabled for Search campaigns",
                    auto_fixable=True,
                    fix_value="Disabled"
                ))

        # Validate regional targeting exists
        regional_targeting = row.get("Regional Targeting", "").strip()
        if not regional_targeting and "broward" in campaign_name.lower():
            self.issues.append(ValidationIssue(
                level=ValidationLevel.CAMPAIGN,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Regional Targeting",
                issue_type="missing_regional_targeting",
                message="Broward campaigns should include regional targeting (Broward County, FL)",
                auto_fixable=False
            ))

    def _validate_asset_group_level(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int):
        """Validate asset group settings - PMAX CAMPAIGNS ONLY"""
        campaign_type = row.get("Campaign Type", "").strip()

        # CRITICAL: Only validate asset groups for Performance Max campaigns
        if campaign_type != "Performance Max":
            return

        asset_group = row.get("Asset Group", "").strip()
        campaign_name = row.get("Campaign", "").strip()

        # Required asset group validation for PMAX campaigns
        if not asset_group:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET_GROUP,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Asset Group",
                issue_type="missing_asset_group_pmax",
                message="Performance Max campaigns require asset groups (not ad groups)",
                suggestion="PMAX campaigns use asset groups, not ad groups. Check PERFORMANCE_MAX_AD_RULES.md",
                auto_fixable=False
            ))
            return

        # Validate asset group name length (< 30 characters)
        if len(asset_group) > 30:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET_GROUP,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Asset Group",
                issue_type="asset_group_name_too_long",
                message=f"Asset group name '{asset_group}' is {len(asset_group)} characters (max 30)",
                auto_fixable=False
            ))

        # Validate PMAX-required fields
        final_url = row.get("Final URL", "").strip()
        if not final_url:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET_GROUP,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Final URL",
                issue_type="missing_final_url_pmax",
                message="Performance Max asset groups require a Final URL",
                auto_fixable=False
            ))

        # Validate regional targeting for Broward campaigns
        if "broward" in campaign_name.lower():
            regional_targeting = row.get("Regional Targeting", "").strip()
            city_targeting = row.get("City Targeting", "").strip()
            zip_targeting = row.get("ZIP Code Targeting", "").strip()

            # Must have regional targeting
            if not regional_targeting or "broward" not in regional_targeting.lower():
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ASSET_GROUP,
                    severity=IssueSeverity.ERROR,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Regional Targeting",
                    issue_type="missing_regional_targeting",
                    message="Broward asset groups must include regional targeting (Broward County, FL)",
                    auto_fixable=False
                ))

            # Must have city targeting for PMAX
            if not city_targeting:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ASSET_GROUP,
                    severity=IssueSeverity.ERROR,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="City Targeting",
                    issue_type="missing_city_targeting_pmax",
                    message="PMAX asset groups must specify city targeting for geographic precision",
                    auto_fixable=False
                ))

            # Must have ZIP targeting for PMAX
            if not zip_targeting:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ASSET_GROUP,
                    severity=IssueSeverity.ERROR,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="ZIP Code Targeting",
                    issue_type="missing_zip_targeting_pmax",
                    message="PMAX asset groups must include ZIP code targeting for local precision",
                    auto_fixable=False
                ))

    def _validate_ad_group_level(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int):
        """Validate ad group settings - SEARCH CAMPAIGNS ONLY"""
        campaign_type = row.get("Campaign Type", "").strip()

        # CRITICAL: Only validate ad groups for Search campaigns
        if campaign_type != "Search":
            return

        ad_group = row.get("Ad Group", "").strip()
        campaign_name = row.get("Campaign", "").strip()

        # Required ad group validation for Search campaigns
        if not ad_group:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET_GROUP,  # Using ASSET_GROUP level for consistency
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Ad Group",
                issue_type="missing_ad_group_search",
                message="Search campaigns require ad groups (not asset groups)",
                suggestion="Search campaigns use ad groups, not asset groups. Check SEARCH_CAMPAIGN_AD_RULES.md",
                auto_fixable=False
            ))
            return

        # Validate ad group name length (< 30 characters)
        if len(ad_group) > 30:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET_GROUP,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Ad Group",
                issue_type="ad_group_name_too_long",
                message=f"Ad group name '{ad_group}' is {len(ad_group)} characters (max 30)",
                auto_fixable=False
            ))

        # Validate Search campaign specific requirements
        keywords = row.get("Keywords", "").strip()
        if not keywords:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET_GROUP,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Keywords",
                issue_type="missing_keywords_search",
                message="Search ad groups require keyword targeting",
                auto_fixable=False
            ))

        # Validate geographic naming consistency for Broward campaigns
        if "broward" in campaign_name.lower():
            expected_city_patterns = [
                "_ftl_", "_pb_", "_hwd_", "_cs_", "_pp_", "_miramar_",
                "fort_lauderdale_", "pompano_beach_", "hollywood_",
                "coral_springs_", "pembroke_pines_"
            ]
            if not any(pattern in ad_group.lower() for pattern in expected_city_patterns):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ASSET_GROUP,
                    severity=IssueSeverity.WARNING,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Ad Group",
                    issue_type="invalid_ad_group_geographic",
                    message="Ad groups should include city identifiers (ftl, pb, hwd, etc.) for geographic targeting",
                    auto_fixable=False
                ))

    def _validate_asset_level(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int):
        """Validate individual assets - ROUTES TO APPROPRIATE VALIDATION BASED ON CAMPAIGN TYPE"""
        campaign_type = row.get("Campaign Type", "").strip()

        if campaign_type == "Performance Max":
            self._validate_pmax_assets(client_name, csv_path, row, row_num)
        elif campaign_type == "Search":
            self._validate_search_rsa_assets(client_name, csv_path, row, row_num)
        else:
            # For other campaign types, use general validation
            self._validate_general_assets(client_name, csv_path, row, row_num)

    def _validate_pmax_assets(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int):
        """Validate Performance Max assets (5 headlines max, 5 descriptions max)"""
        campaign_type = row.get("Campaign Type", "").strip()
        asset_group = row.get("Asset Group", "").strip()

        # Collect all headlines and descriptions for comprehensive validation
        headlines = []
        descriptions = []

        # Validate PMAX headlines (max 5)
        for i in range(1, 6):  # Headlines 1-5 for PMAX
            headline_col = f"Headline {i}"
            headline = row.get(headline_col, "").strip()

            if headline:
                headlines.append(headline)
                # PMAX headline validation (same technical writing rules)
                if len(headline) < self.validation_rules['asset']['headline_length']['min'] or len(headline) > self.validation_rules['asset']['headline_length']['max']:
                    severity = IssueSeverity.ERROR if len(headline) > 30 else IssueSeverity.WARNING
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ASSET,
                        severity=severity,
                        client_name=client_name,
                        csv_file=csv_path,
                        row_number=row_num,
                        column=headline_col,
                        issue_type="pmax_headline_length",
                        message=f"PMAX headline {i} length {len(headline)} chars (optimal: 22-29 for value density)",
                        auto_fixable=False
                    ))

                # Technical writing validation for PMAX
                self._validate_technical_writing_headline(client_name, csv_path, row_num, headline_col, headline)

        # Require at least 3 headlines for PMAX
        if len(headlines) < 3:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Headlines",
                issue_type="insufficient_pmax_headlines",
                message=f"PMAX asset group '{asset_group}' has {len(headlines)} headlines (minimum 3 required)",
                suggestion="Add 3-5 headlines per PMAX asset group for optimal performance",
                auto_fixable=False
            ))

        # Validate PMAX descriptions (max 5)
        for i in range(1, 6):  # Descriptions 1-5 for PMAX
            desc_col = f"Description {i}"
            description = row.get(desc_col, "").strip()

            if description:
                descriptions.append(description)
                # PMAX description validation (same technical writing rules)
                if len(description) < self.validation_rules['asset']['description_length']['min'] or len(description) > self.validation_rules['asset']['description_length']['max']:
                    severity = IssueSeverity.ERROR if len(description) > 90 else IssueSeverity.WARNING
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ASSET,
                        severity=severity,
                        client_name=client_name,
                        csv_file=csv_path,
                        row_number=row_num,
                        column=desc_col,
                        issue_type="pmax_description_length",
                        message=f"PMAX description {i} length {len(description)} chars (optimal: 75-85 for value density)",
                        auto_fixable=False
                    ))

                # Technical writing validation for PMAX
                self._validate_technical_writing_description(client_name, csv_path, row_num, desc_col, description)

        # Require at least 2 descriptions for PMAX
        if len(descriptions) < 2:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Descriptions",
                issue_type="insufficient_pmax_descriptions",
                message=f"PMAX asset group '{asset_group}' has {len(descriptions)} descriptions (minimum 2 required)",
                suggestion="Add 2-5 descriptions per PMAX asset group for optimal performance",
                auto_fixable=False
            ))

        # Client requirements validation for PMAX
        if client_name == "wrights_impact_window_and_door":
            self._validate_client_requirements_inclusion(client_name, csv_path, row, row_num, headlines, descriptions)

    def _validate_search_rsa_assets(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int):
        """Validate Search RSA assets (3 headlines max, 2 descriptions max - per Google API specs)"""
        campaign_type = row.get("Campaign Type", "").strip()
        ad_group = row.get("Ad Group", "").strip()

        # Only validate rows that actually contain ad content (have Headline 1)
        if not row.get("Headline 1", "").strip():
            return

        # Collect all headlines and descriptions for comprehensive validation
        headlines = []
        descriptions = []

        # Validate RSA headlines (max 15)
        for i in range(1, 4):  # Headlines 1-3 for RSA (Google API limit)
            headline_col = f"Headline {i}"
            headline = row.get(headline_col, "").strip()

            if headline:
                headlines.append(headline)
                # RSA headline validation (same technical writing rules)
                if len(headline) < self.validation_rules['asset']['headline_length']['min'] or len(headline) > self.validation_rules['asset']['headline_length']['max']:
                    severity = IssueSeverity.ERROR if len(headline) > 30 else IssueSeverity.WARNING
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ASSET,
                        severity=severity,
                        client_name=client_name,
                        csv_file=csv_path,
                        row_number=row_num,
                        column=headline_col,
                        issue_type="rsa_headline_length",
                        message=f"RSA headline {i} length {len(headline)} chars (optimal: 22-29 for value density)",
                        auto_fixable=False
                    ))

                # Technical writing validation for RSA
                self._validate_technical_writing_headline(client_name, csv_path, row_num, headline_col, headline)

        # RSA requires at least 3 headlines for AI optimization (Google recommendation)
        if len(headlines) < 3:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Headlines",
                issue_type="insufficient_rsa_headlines",
                message=f"RSA ad group '{ad_group}' has {len(headlines)} headlines (minimum: 3 for AI optimization)",
                suggestion="RSA requires at least 3 headlines for Google's AI to test combinations",
                auto_fixable=False
            ))

        # Validate RSA descriptions (max 2 per Google API)
        for i in range(1, 3):  # Descriptions 1-2 for RSA (Google API limit)
            desc_col = f"Description {i}"
            description = row.get(desc_col, "").strip()

            if description:
                descriptions.append(description)
                # RSA description validation (90 chars max per Google)
                if len(description) > 90:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ASSET,
                        severity=IssueSeverity.ERROR,
                        client_name=client_name,
                        csv_file=csv_path,
                        row_number=row_num,
                        column=desc_col,
                        issue_type="rsa_description_too_long",
                        message=f"RSA description {i} exceeds Google Ads limit: {len(description)} chars (max: 90)",
                        suggestion="Shorten description to 90 characters or less",
                        auto_fixable=False
                    ))

                # Technical writing validation for RSA
                self._validate_technical_writing_description(client_name, csv_path, row_num, desc_col, description)

        # RSA requires at least 2 descriptions for AI optimization (Google recommendation)
        if len(descriptions) < 2:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Descriptions",
                issue_type="insufficient_rsa_descriptions",
                message=f"RSA ad group '{ad_group}' has {len(descriptions)} descriptions (minimum: 2 for AI optimization)",
                suggestion="RSA requires at least 2 descriptions for Google's AI to test combinations",
                auto_fixable=False
            ))

        # Client requirements validation for Search RSA
        if client_name == "wrights_impact_window_and_door":
            self._validate_client_requirements_inclusion(client_name, csv_path, row, row_num, headlines, descriptions)

        # RSA-specific advanced validation
        self._validate_rsa_path_optimization(client_name, csv_path, row, row_num)
        self._validate_rsa_keyword_relevance(client_name, csv_path, row, row_num, headlines, descriptions)
        self._validate_rsa_mobile_optimization(client_name, csv_path, row, row_num, headlines, descriptions)
        self._validate_rsa_seasonal_hurricane_rules(client_name, csv_path, row, row_num, headlines, descriptions)
        self._validate_rsa_competitor_avoidance(client_name, csv_path, row, row_num, headlines, descriptions)
        self._validate_rsa_ab_testing_framework(client_name, csv_path, row, row_num, headlines, descriptions)
        self._validate_rsa_budget_allocation_rules(client_name, csv_path, row, row_num)
        self._validate_rsa_geographic_micro_targeting(client_name, csv_path, row, row_num)

    def _validate_general_assets(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int):
        """Validate assets for other campaign types (fallback)"""
        # Use original validation logic for non-PMAX/Search campaigns
        pass

    def _validate_technical_writing_headline(self, client_name: str, csv_path: str, row_num: int, column: str, headline: str):
        """Validate technical writing quality for headlines"""
        # Check for filler words
        filler_words = ['the', 'a', 'an', 'or', 'and', 'but', 'so', 'very', 'really', 'just', 'only', 'that', 'this', 'these', 'those']
        words = headline.lower().split()
        found_fillers = [word for word in words if word in filler_words]

        if found_fillers:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.INFO,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column=column,
                issue_type="headline_filler_words",
                message=f"Headline contains filler words: {found_fillers} - reduce for better value density",
                suggestion="Remove filler words to jam-pack more value per character",
                auto_fixable=False
            ))

        # Check for em dashes
        if '—' in headline or '–' in headline:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column=column,
                issue_type="headline_em_dash",
                message="Headline contains em dash - avoid for technical writing precision",
                suggestion="Use hyphens or restructure for clarity",
                auto_fixable=False
            ))

    def _validate_technical_writing_description(self, client_name: str, csv_path: str, row_num: int, column: str, description: str):
        """Validate technical writing quality for descriptions"""
        # Check for filler words
        filler_words = ['the', 'a', 'an', 'or', 'and', 'but', 'so', 'very', 'really', 'just', 'only', 'that', 'this', 'these', 'those']
        words = description.lower().split()
        found_fillers = [word for word in words if word in filler_words]

        if found_fillers:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.INFO,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column=column,
                issue_type="description_filler_words",
                message=f"Description contains filler words: {found_fillers} - reduce for better value density",
                suggestion="Remove filler words to jam-pack more value per character",
                auto_fixable=False
            ))

        # Check for em dashes
        if '—' in description or '–' in description:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column=column,
                issue_type="description_em_dash",
                message="Description contains em dash - avoid for technical writing precision",
                suggestion="Use hyphens or restructure for clarity",
                auto_fixable=False
            ))

        # Collect all headlines and descriptions for comprehensive validation
        headlines = []
        descriptions = []

        # Headline validation
        for i in range(1, 16):  # Headlines 1-15
            headline_col = f"Headline {i}"
            headline = row.get(headline_col, "").strip()

            if headline:
                headlines.append(headline)
                headline_rules = self.validation_rules['asset']['headline_length']

                # Check hard limits
                if len(headline) < headline_rules['min'] or len(headline) > headline_rules['max']:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ASSET,
                        severity=IssueSeverity.ERROR,
                        client_name=client_name,
                        csv_file=csv_path,
                        row_number=row_num,
                        column=headline_col,
                        issue_type="headline_length_violation",
                        message=f"Headline {i} length {len(headline)} chars violates limits ({headline_rules['min']}-{headline_rules['max']})",
                        auto_fixable=False
                    ))
                # Check optimal range (technical writing sweet spot)
                elif len(headline) < headline_rules['optimal_min'] or len(headline) > headline_rules['optimal_max']:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ASSET,
                        severity=IssueSeverity.WARNING,
                        client_name=client_name,
                        csv_file=csv_path,
                        row_number=row_num,
                        column=headline_col,
                        issue_type="headline_suboptimal_length",
                        message=f"Headline {i} length {len(headline)} chars (optimal: {headline_rules['optimal_min']}-{headline_rules['optimal_max']} for max value density)",
                        suggestion="Use technical writing to jam-pack value without filler words",
                        auto_fixable=False
                    ))

                # Check for filler words and poor technical writing
                filler_words = ['the', 'a', 'an', 'or', 'and', 'but', 'so', 'very', 'really', 'just', 'only', 'that', 'this', 'these', 'those']
                words = headline.lower().split()
                found_fillers = [word for word in words if word in filler_words]

                if found_fillers:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ASSET,
                        severity=IssueSeverity.INFO,
                        client_name=client_name,
                        csv_file=csv_path,
                        row_number=row_num,
                        column=headline_col,
                        issue_type="headline_filler_words",
                        message=f"Headline {i} contains filler words: {found_fillers} - reduce for better value density",
                        suggestion="Remove filler words to jam-pack more value per character",
                        auto_fixable=False
                    ))

                # Check for em dashes and poor punctuation
                if '—' in headline or '–' in headline:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ASSET,
                        severity=IssueSeverity.WARNING,
                        client_name=client_name,
                        csv_file=csv_path,
                        row_number=row_num,
                        column=headline_col,
                        issue_type="headline_em_dash",
                        message=f"Headline {i} contains em dash - avoid for technical writing precision",
                        suggestion="Use hyphens or restructure for clarity",
                        auto_fixable=False
                    ))

        # Comprehensive ad copy validation (Wright's Impact specific)
        if client_name == "wrights_impact_window_and_door" and headlines:
            self._validate_ad_copy_best_practices(client_name, csv_path, row, row_num, headlines, descriptions)

        # Description validation
        for i in range(1, 6):  # Descriptions 1-5
            desc_col = f"Description {i}"
            description = row.get(desc_col, "").strip()

            if description:
                desc_rules = self.validation_rules['asset']['description_length']

                # Check hard limits
                if len(description) < desc_rules['min'] or len(description) > desc_rules['max']:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ASSET,
                        severity=IssueSeverity.ERROR,
                        client_name=client_name,
                        csv_file=csv_path,
                        row_number=row_num,
                        column=desc_col,
                        issue_type="description_length_violation",
                        message=f"Description {i} length {len(description)} chars violates limits ({desc_rules['min']}-{desc_rules['max']})",
                        auto_fixable=False
                    ))
                # Check optimal range (technical writing sweet spot)
                elif len(description) < desc_rules['optimal_min'] or len(description) > desc_rules['optimal_max']:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ASSET,
                        severity=IssueSeverity.WARNING,
                        client_name=client_name,
                        csv_file=csv_path,
                        row_number=row_num,
                        column=desc_col,
                        issue_type="description_suboptimal_length",
                        message=f"Description {i} length {len(description)} chars (optimal: {desc_rules['optimal_min']}-{desc_rules['optimal_max']} for max value density)",
                        suggestion="Use technical writing to jam-pack value without filler words",
                        auto_fixable=False
                    ))

                # Check for filler words and poor technical writing
                filler_words = ['the', 'a', 'an', 'or', 'and', 'but', 'so', 'very', 'really', 'just', 'only', 'that', 'this', 'these', 'those']
                words = description.lower().split()
                found_fillers = [word for word in words if word in filler_words]

                if found_fillers:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ASSET,
                        severity=IssueSeverity.INFO,
                        client_name=client_name,
                        csv_file=csv_path,
                        row_number=row_num,
                        column=desc_col,
                        issue_type="description_filler_words",
                        message=f"Description {i} contains filler words: {found_fillers} - reduce for better value density",
                        suggestion="Remove filler words to jam-pack more value per character",
                        auto_fixable=False
                    ))

                # Check for em dashes and poor punctuation
                if '—' in description or '–' in description:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.ASSET,
                        severity=IssueSeverity.WARNING,
                        client_name=client_name,
                        csv_file=csv_path,
                        row_number=row_num,
                        column=desc_col,
                        issue_type="description_em_dash",
                        message=f"Description {i} contains em dash - avoid for technical writing precision",
                        suggestion="Use hyphens or restructure for clarity",
                        auto_fixable=False
                    ))

    def _validate_targeting_level(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int):
        """Validate geographic and audience targeting"""
        # Location validation
        location = row.get("Location", "").strip()
        if location:
            # Basic location format validation
            if not re.match(r'^[^,]+,\s*[A-Z]{2}$', location) and not re.match(r'^\d{5}$', location):
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.TARGETING,
                    severity=IssueSeverity.WARNING,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Location",
                    issue_type="location_format",
                    message=f"Location format may be invalid: {location}",
                    suggestion="Use 'City, ST' or ZIP code format",
                    auto_fixable=False
                ))

        # Language validation
        language = row.get("Languages", "").strip()
        if language and language != "en":
            self.issues.append(ValidationIssue(
                level=ValidationLevel.TARGETING,
                severity=IssueSeverity.INFO,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Languages",
                issue_type="non_english_language",
                message=f"Non-English language targeting: {language}",
                auto_fixable=False
            ))

    def _validate_ad_copy_best_practices(self, client_name: str, csv_path: str, row: Dict[str, str],
                                       row_num: int, headlines: List[str], descriptions: List[str]):
        """Validate Wright's Impact ad copy best practices"""
        asset_group = row.get("Asset group", "").strip()
        requirements = self.validation_rules['asset']['headline_requirements']

        # Count different types of headlines
        number_one_headlines = sum(1 for h in headlines if h.startswith('#1 '))
        brand_headlines = sum(1 for h in headlines if any(
            brand.lower() in h.lower() for brand in self.validation_rules['asset']['brand_terms']
        ))
        service_headlines = sum(1 for h in headlines if any(
            service in h.lower() for service in ['impact windows', 'impact doors', 'hurricane protection',
                                               'energy efficient', 'storm protection', 'commercial impact']
        ))
        regional_headlines = sum(1 for h in headlines if any(
            region in h.lower() for region in ['florida', 'fort myers', 'naples', 'cape coral',
                                             'lee county', 'broward county', 'fort lauderdale']
        ))

        # Validate #1 headlines requirement
        if number_one_headlines < requirements['number_one_headlines']['min_required']:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Headlines",
                issue_type="missing_number_one_headlines",
                message=f"Asset group '{asset_group}' missing #1 headlines. Found {number_one_headlines}, need {requirements['number_one_headlines']['min_required']}-{requirements['number_one_headlines']['max_required']}",
                suggestion="Add headlines starting with '#1' (e.g., '#1 Impact Windows Expert')",
                auto_fixable=False
            ))
        elif number_one_headlines > requirements['number_one_headlines']['max_required']:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Headlines",
                issue_type="too_many_number_one_headlines",
                message=f"Asset group '{asset_group}' has {number_one_headlines} #1 headlines, recommended max {requirements['number_one_headlines']['max_required']}",
                auto_fixable=False
            ))

        # Validate brand headlines requirement
        if brand_headlines < requirements['brand_headlines']['min_required']:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Headlines",
                issue_type="missing_brand_headlines",
                message=f"Asset group '{asset_group}' missing brand headlines. Found {brand_headlines}, need at least {requirements['brand_headlines']['min_required']}",
                suggestion="Add headlines with 'Wright's Impact', 'Wright's Window & Door', etc.",
                auto_fixable=False
            ))

        # Validate service headlines requirement
        if service_headlines < requirements['service_headlines']['min_required']:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Headlines",
                issue_type="insufficient_service_headlines",
                message=f"Asset group '{asset_group}' has {service_headlines} service headlines, recommended at least {requirements['service_headlines']['min_required']}",
                suggestion="Add more service-focused headlines (Impact Windows, Hurricane Protection, etc.)",
                auto_fixable=False
            ))

        # Validate regional headlines requirement
        if regional_headlines < requirements['regional_headlines']['min_required']:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Headlines",
                issue_type="insufficient_regional_headlines",
                message=f"Asset group '{asset_group}' has {regional_headlines} regional headlines, recommended at least {requirements['regional_headlines']['min_required']}",
                suggestion="Add regional headlines (Florida, Lee County, Fort Myers, etc.)",
                auto_fixable=False
            ))

        # Validate client requirements inclusion (Wright's Impact specific)
        if client_name == "wrights_impact_window_and_door":
            self._validate_client_requirements_inclusion(client_name, csv_path, row, row_num, headlines, descriptions)

    def _validate_client_requirements_inclusion(self, client_name: str, csv_path: str, row: Dict[str, str],
                                               row_num: int, headlines: List[str], descriptions: List[str]):
        """Validate that Wright's Impact client requirements are included in ad copy"""
        asset_group = row.get("Asset group", "").strip()
        all_text = ' '.join(headlines + descriptions).lower()

        # Client's 6 core value propositions (must be included intuitively)
        core_requirements = {
            'improve energy efficiency': ['energy efficiency', 'energy efficient', 'energy savings', 'utility bill', 'utility cost'],
            'noise reduction': ['noise reduction', 'sound dampening', 'quieter home', 'sound reduction'],
            'increase home security': ['home security', 'security enhancement', 'secure home', 'security protection'],
            'lower insurance rates': ['insurance rates', 'insurance discount', 'lower premiums', 'insurance savings'],
            'improve property value': ['property value', 'home value', 'increase value', 'property appreciation'],
            'safeguard your home': ['safeguard home', 'protect home', 'home protection', 'safeguard property']
        }

        # Florida lifetime guarantee requirement
        florida_guarantee = ['florida', 'lifetime guarantee', 'impact windows and doors']

        # PACE financing requirement
        pace_financing = ['pace finance', '100% financing', 'no money down', 'deferred payments']

        missing_requirements = []

        # Check core value propositions - at least 2 must be present per asset group
        core_found = 0
        for requirement, keywords in core_requirements.items():
            if any(keyword in all_text for keyword in keywords):
                core_found += 1

        if core_found < 2:
            missing_requirements.append(f"Only {core_found}/6 core value propositions found (need at least 2)")

        # Check Florida lifetime guarantee (must be present in Florida campaigns)
        if 'florida' in asset_group.lower() or 'regional' in asset_group.lower():
            guarantee_found = sum(1 for element in florida_guarantee if element in all_text)
            if guarantee_found < 2:  # Need at least Florida + lifetime guarantee
                missing_requirements.append("Missing Florida lifetime guarantee elements")

        # Check PACE financing (must be present in financing-focused asset groups)
        if 'financ' in asset_group.lower():
            financing_found = sum(1 for element in pace_financing if element in all_text)
            if financing_found < 2:  # Need at least 2 financing elements
                missing_requirements.append("Missing PACE financing elements")

        # Report issues
        if missing_requirements:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Headlines+Descriptions",
                issue_type="missing_client_requirements",
                message=f"Asset group '{asset_group}' missing mandatory client requirements: {'; '.join(missing_requirements)}",
                suggestion="Review CLIENT_AD_COPY_REQUESTS.md and ensure all client requirements are included intuitively",
                auto_fixable=False
            ))

    def _validate_rsa_path_optimization(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int):
        """Validate RSA display path optimization"""
        # Path validation for RSA
        path1 = row.get("Path 1", "").strip()
        path2 = row.get("Path 2", "").strip()

        # RSA requires Path 1 for display
        if not path1:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Path 1",
                issue_type="missing_rsa_path1",
                message="RSA requires Path 1 for display optimization",
                suggestion="Add Path 1 (max 15 chars) for RSA display paths",
                auto_fixable=False
            ))

        # Path length validation
        if path1 and len(path1) > 15:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Path 1",
                issue_type="path1_too_long",
                message=f"Path 1 exceeds 15 character limit: {len(path1)} chars",
                suggestion="Shorten Path 1 to 15 characters or less",
                auto_fixable=False
            ))

        if path2 and len(path2) > 15:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Path 2",
                issue_type="path2_too_long",
                message=f"Path 2 exceeds 15 character limit: {len(path2)} chars",
                suggestion="Shorten Path 2 to 15 characters or less",
                auto_fixable=False
            ))

        # Path keyword integration (should include location or service)
        all_paths = ' '.join([path1, path2]).lower()
        ad_group = row.get("Ad Group", "").lower()

        # Extract location/service keywords from ad group name
        path_keywords = []
        if 'fort myers' in ad_group:
            path_keywords.extend(['fort myers', 'ft myers'])
        if 'naples' in ad_group:
            path_keywords.append('naples')
        if 'broward' in ad_group:
            path_keywords.append('broward')
        if 'impact' in ad_group:
            path_keywords.extend(['impact', 'windows', 'doors'])

        if path_keywords and not any(keyword in all_paths for keyword in path_keywords):
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Path 1",
                issue_type="path_keyword_mismatch",
                message=f"RSA paths should include keywords from ad group: {path_keywords}",
                suggestion="Add relevant location or service keywords to display paths",
                auto_fixable=False
            ))

    def _validate_rsa_keyword_relevance(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int,
                                       headlines: List[str], descriptions: List[str]):
        """Validate RSA keyword-ad relevance"""
        ad_group = row.get("Ad Group", "").strip().lower()
        keywords = row.get("Keywords", "").strip()

        if not keywords:
            return

        # Extract keyword themes from ad group name
        ad_group_keywords = []
        if 'fort myers' in ad_group:
            ad_group_keywords.extend(['fort myers', 'ft myers'])
        if 'naples' in ad_group:
            ad_group_keywords.append('naples')
        if 'broward' in ad_group:
            ad_group_keywords.append('broward')
        if 'impact' in ad_group:
            ad_group_keywords.extend(['impact', 'windows', 'doors'])
        if 'hurricane' in ad_group:
            ad_group_keywords.extend(['hurricane', 'protection', 'storm'])
        if 'energy' in ad_group:
            ad_group_keywords.extend(['energy', 'efficient', 'efficiency'])

        # Check if headlines contain keyword variations
        all_headlines_text = ' '.join(headlines).lower()
        keyword_matches = sum(1 for keyword in ad_group_keywords if keyword in all_headlines_text)

        if keyword_matches < len(ad_group_keywords) * 0.5:  # At least 50% coverage
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Headline 1",
                issue_type="rsa_keyword_relevance",
                message=f"RSA headlines have low keyword relevance ({keyword_matches}/{len(ad_group_keywords)} matches)",
                suggestion="Include more keyword variations from ad group theme in headlines",
                auto_fixable=False
            ))

        # Check for exact keyword matches in at least one headline
        exact_keywords = [k.strip('"') for k in keywords.split(',') if k.strip().startswith('"')]
        exact_matches = sum(1 for keyword in exact_keywords if keyword.lower() in all_headlines_text)

        if exact_keywords and exact_matches == 0:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Headline 1",
                issue_type="missing_exact_keyword_match",
                message="No RSA headlines contain exact match keywords",
                suggestion="Include at least one headline with exact keyword match",
                auto_fixable=False
            ))

    def _validate_rsa_mobile_optimization(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int,
                                         headlines: List[str], descriptions: List[str]):
        """Validate RSA mobile optimization"""
        # Mobile headline optimization (22-26 chars optimal)
        mobile_unfriendly_headlines = []
        for i, headline in enumerate(headlines, 1):
            if len(headline) > 26:  # May be truncated on mobile
                mobile_unfriendly_headlines.append(f"Headline {i} ({len(headline)} chars)")

        if mobile_unfriendly_headlines:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.INFO,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Headline 1",
                issue_type="mobile_headline_truncation",
                message=f"Headlines may be truncated on mobile: {', '.join(mobile_unfriendly_headlines)}",
                suggestion="Consider shortening to 22-26 characters for optimal mobile display",
                auto_fixable=False
            ))

        # Mobile description optimization (first 75 chars visible)
        all_descriptions_text = ' '.join(descriptions)
        if len(all_descriptions_text) > 75:
            first_75_chars = all_descriptions_text[:75]
            # Check if call-to-action or key benefit is in first 75 chars
            key_phrases = ['call now', 'free estimate', 'contact', 'PACE finance', 'lifetime guarantee']
            has_key_phrase = any(phrase in first_75_chars.lower() for phrase in key_phrases)

            if not has_key_phrase:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ASSET,
                    severity=IssueSeverity.INFO,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Description 1",
                    issue_type="mobile_description_optimization",
                    message="Key call-to-action or benefit not visible in mobile description preview",
                    suggestion="Place important benefits or call-to-action within first 75 characters",
                    auto_fixable=False
                ))

    def _validate_rsa_seasonal_hurricane_rules(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int,
                                              headlines: List[str], descriptions: List[str]):
        """Validate RSA seasonal/hurricane optimization"""
        all_text = ' '.join(headlines + descriptions).lower()
        current_month = datetime.now().month  # 1-12

        # Hurricane season: June-November (6-11)
        is_hurricane_season = 6 <= current_month <= 11

        if is_hurricane_season:
            # Check for hurricane season messaging
            hurricane_keywords = ['hurricane', 'storm', 'emergency', 'protection', 'ready', 'insurance discount']
            hurricane_matches = sum(1 for keyword in hurricane_keywords if keyword in all_text)

            if hurricane_matches < 2:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ASSET,
                    severity=IssueSeverity.WARNING,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Headline 1",
                    issue_type="hurricane_season_optimization",
                    message="Hurricane season detected - consider adding emergency protection messaging",
                    suggestion="Include hurricane protection, emergency, or insurance discount messaging",
                    auto_fixable=False
                ))
        else:
            # Check for off-season messaging (energy efficiency, property value)
            offseason_keywords = ['energy efficient', 'utility savings', 'property value', 'noise reduction']
            offseason_matches = sum(1 for keyword in offseason_keywords if keyword in all_text)

            if offseason_matches < 2:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ASSET,
                    severity=IssueSeverity.INFO,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Headline 1",
                    issue_type="offseason_optimization",
                    message="Off-season detected - consider energy efficiency and property value messaging",
                    suggestion="Include energy efficiency, utility savings, or property value benefits",
                    auto_fixable=False
                ))

    def _validate_rsa_competitor_avoidance(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int,
                                          headlines: List[str], descriptions: List[str]):
        """Validate RSA competitor avoidance and combination diversity"""
        # Check for internal RSA similarity (avoid cannibalization)
        headline_combinations = []

        # Group headlines by theme to check for over-concentration
        service_headlines = []
        location_headlines = []
        value_headlines = []

        for headline in headlines:
            headline_lower = headline.lower()
            if any(word in headline_lower for word in ['impact', 'windows', 'doors', 'protection']):
                service_headlines.append(headline)
            if any(word in headline_lower for word in ['fort myers', 'naples', 'broward', 'florida']):
                location_headlines.append(headline)
            if any(word in headline_lower for word in ['energy', 'insurance', 'property', 'safeguard', 'security']):
                value_headlines.append(headline)

        # Check for balanced headline distribution
        total_headlines = len(headlines)
        if total_headlines >= 8:  # Only check if we have minimum headlines
            service_ratio = len(service_headlines) / total_headlines
            location_ratio = len(location_headlines) / total_headlines
            value_ratio = len(value_headlines) / total_headlines

            # Warn if any category dominates (>70% of headlines)
            if service_ratio > 0.7:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ASSET,
                    severity=IssueSeverity.WARNING,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Headline 1",
                    issue_type="headline_theme_imbalance",
                    message=f"Too many service-focused headlines ({len(service_headlines)}/{total_headlines})",
                    suggestion="Balance with more location and value proposition headlines",
                    auto_fixable=False
                ))

            if location_ratio > 0.7:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ASSET,
                    severity=IssueSeverity.WARNING,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Headline 1",
                    issue_type="headline_theme_imbalance",
                    message=f"Too many location-focused headlines ({len(location_headlines)}/{total_headlines})",
                    suggestion="Balance with more service and value proposition headlines",
                    auto_fixable=False
                ))

        # Check for duplicate messaging patterns
        headline_texts = [h.lower().strip() for h in headlines]
        duplicates = []
        seen = set()
        for headline in headline_texts:
            if headline in seen:
                duplicates.append(headline)
            else:
                seen.add(headline)

        if duplicates:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Headline 1",
                issue_type="duplicate_headline_messaging",
                message=f"Duplicate headline messaging detected: {', '.join(duplicates[:3])}",
                suggestion="Ensure headline variety and avoid repeating similar messages",
                auto_fixable=False
            ))

    def _validate_rsa_ab_testing_framework(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int,
                                          headlines: List[str], descriptions: List[str]):
        """Validate RSA A/B testing framework requirements"""
        total_headlines = len(headlines)
        total_descriptions = len(descriptions)

        # Check for minimum testing combinations
        # Google can create up to C(15,3) = 455 headline combinations and C(5,2) = 10 description combinations
        if total_headlines >= 8 and total_descriptions >= 3:
            headline_combinations = self._calculate_rsa_combinations(total_headlines, 3)
            description_combinations = self._calculate_rsa_combinations(total_descriptions, 2)
            total_possible_combinations = headline_combinations * description_combinations

            # Flag if combinations are too low for effective testing
            if total_possible_combinations < 50:  # Minimum for meaningful testing
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ASSET,
                    severity=IssueSeverity.WARNING,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Headline 1",
                    issue_type="insufficient_rsa_testing_combinations",
                    message=f"RSA has only {total_possible_combinations} possible combinations (need >50 for effective A/B testing)",
                    suggestion="Add more diverse headlines and descriptions to increase testing combinations",
                    auto_fixable=False
                ))

        # Check for testing group balance
        # Should have variety in messaging themes for proper A/B testing
        if total_headlines >= 8:
            # Ensure different themes are present for testing
            themes = {
                'urgency': ['now', 'today', 'call', 'contact', 'emergency'],
                'benefit': ['save', 'reduce', 'increase', 'improve', 'protect'],
                'authority': ['expert', '#1', 'lifetime', 'guarantee', 'professional'],
                'location': ['fort myers', 'naples', 'broward', 'florida']
            }

            theme_coverage = {}
            all_text = ' '.join(headlines + descriptions).lower()

            for theme_name, theme_words in themes.items():
                theme_coverage[theme_name] = any(word in all_text for word in theme_words)

            covered_themes = sum(theme_coverage.values())
            if covered_themes < len(themes) * 0.75:  # Need 75% theme coverage
                missing_themes = [theme for theme, covered in theme_coverage.items() if not covered]
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ASSET,
                    severity=IssueSeverity.INFO,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Headline 1",
                    issue_type="insufficient_rsa_theme_coverage",
                    message=f"RSA testing limited - missing themes: {', '.join(missing_themes)}",
                    suggestion="Include diverse themes (urgency, benefits, authority, location) for comprehensive A/B testing",
                    auto_fixable=False
                ))

    def _validate_rsa_budget_allocation_rules(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int):
        """Validate RSA budget allocation optimization"""
        # Check for budget allocation fields in CSV
        budget = row.get("Budget", "").strip()
        bid_strategy = row.get("Bid Strategy", "").strip()

        # Warn about missing performance-based budget allocation
        if not budget or budget == "0" or budget == "0.00":
            self.issues.append(ValidationIssue(
                level=ValidationLevel.CAMPAIGN,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Budget",
                issue_type="missing_rsa_budget_allocation",
                message="RSA campaign missing budget allocation for performance testing",
                suggestion="Allocate budget based on keyword competition and testing requirements",
                auto_fixable=False
            ))

        # Check for Target CPA strategy (recommended for RSA performance)
        if bid_strategy and "target cpa" not in bid_strategy.lower():
            self.issues.append(ValidationIssue(
                level=ValidationLevel.CAMPAIGN,
                severity=IssueSeverity.INFO,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Bid Strategy",
                issue_type="suboptimal_rsa_bid_strategy",
                message=f"Consider Target CPA for RSA performance optimization instead of {bid_strategy}",
                suggestion="Use Target CPA strategy for better RSA combination performance tracking",
                auto_fixable=False
            ))

    def _validate_rsa_geographic_micro_targeting(self, client_name: str, csv_path: str, row: Dict[str, str], row_num: int):
        """Validate RSA geographic micro-targeting"""
        geographic_targeting = row.get("Geographic Targeting", "").strip()
        zip_codes = row.get("ZIP Code Targeting", "").strip()
        ad_group = row.get("Ad Group", "").strip().lower()

        # Check for ZIP code targeting in high-value areas
        if 'fort myers' in ad_group or 'naples' in ad_group or 'broward' in ad_group:
            if not zip_codes:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.TARGETING,
                    severity=IssueSeverity.INFO,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="ZIP Code Targeting",
                    issue_type="missing_zip_micro_targeting",
                    message="Consider ZIP code micro-targeting for better geographic precision",
                    suggestion="Add specific ZIP codes for Fort Myers, Naples, or Broward County targeting",
                    auto_fixable=False
                ))
            else:
                # Validate ZIP code format
                zip_list = [z.strip() for z in zip_codes.split(',')]
                invalid_zips = []
                for zip_code in zip_list:
                    if not re.match(r'^\d{5}(-\d{4})?$', zip_code):
                        invalid_zips.append(zip_code)

                if invalid_zips:
                    self.issues.append(ValidationIssue(
                        level=ValidationLevel.TARGETING,
                        severity=IssueSeverity.ERROR,
                        client_name=client_name,
                        csv_file=csv_path,
                        row_number=row_num,
                        column="ZIP Code Targeting",
                        issue_type="invalid_zip_format",
                        message=f"Invalid ZIP code formats: {', '.join(invalid_zips)}",
                        suggestion="Use standard 5-digit or 5+4 ZIP code formats (e.g., 33901 or 33901-1234)",
                        auto_fixable=False
                    ))

        # Check geographic targeting relevance
        if geographic_targeting:
            geo_lower = geographic_targeting.lower()
            # Ensure geographic targeting matches ad group location
            if 'fort myers' in ad_group and 'fort myers' not in geo_lower:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.TARGETING,
                    severity=IssueSeverity.ERROR,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Geographic Targeting",
                    issue_type="geographic_targeting_mismatch",
                    message="Ad group targets Fort Myers but geographic targeting doesn't match",
                    suggestion="Ensure geographic targeting includes Fort Myers, FL",
                    auto_fixable=False
                ))

    def _calculate_rsa_combinations(self, n: int, r: int) -> int:
        """Calculate number of combinations for RSA testing (n choose r)"""
        if r > n or r < 0:
            return 0
        if r == 0 or r == n:
            return 1

        # Calculate combinations
        result = 1
        for i in range(1, r + 1):
            result = result * (n - r + i) // i
        return result

    def _apply_auto_fixes_to_csv(self, csv_content: str) -> str:
        """Apply auto-fixes to CSV content"""
        if not csv_content:
            return csv_content

        # Auto-detect delimiter
        sample = csv_content[:1024]
        sniffer = csv.Sniffer()
        try:
            delimiter = sniffer.sniff(sample, delimiters=',\t;|').delimiter
        except:
            delimiter = ','

        lines = csv_content.split('\n')
        if len(lines) < 2:
            return csv_content

        # Parse header
        header_line = lines[0]
        headers = header_line.split(delimiter)

        # Find column indices
        col_indices = {}
        for i, header in enumerate(headers):
            col_indices[header] = i

        # Process data rows
        fixed_lines = [header_line]

        for line in lines[1:]:
            if not line.strip():
                continue

            fields = line.split(delimiter)

            # Apply fixes based on issues
            for issue in self.issues:
                if issue.auto_fixable and issue.row_number == len(fixed_lines) + 1:  # +1 because header is already added
                    if issue.column in col_indices and issue.fixed_value is not None:
                        col_idx = col_indices[issue.column]
                        if col_idx < len(fields):
                            fields[col_idx] = issue.fixed_value
                            issue.fixed_value = fields[col_idx]  # Update the issue with the actual fixed value

            fixed_lines.append(delimiter.join(fields))

        return '\n'.join(fixed_lines)

    def _apply_fixes(self, client_name: str):
        """Apply fixes to issues that were marked as fixable"""
        for issue in self.issues:
            if issue.auto_fixable and issue.fixed_value is not None:
                # For now, fixes are applied during CSV processing
                # In the future, this could update external systems
                self.fixed_issues.append(issue)

    def _generate_report(self, client_name: str, total_rows: int) -> ValidationReport:
        """Generate comprehensive validation report"""
        # Count issues by severity and level
        severity_counts = {severity.value: 0 for severity in IssueSeverity}
        level_counts = {level.value: 0 for level in ValidationLevel}

        for issue in self.issues:
            severity_counts[issue.severity.value] += 1
            level_counts[issue.level.value] += 1

        # Determine final status
        if severity_counts['critical'] > 0 or severity_counts['error'] > 0:
            final_status = 'FAIL'
        elif len(self.fixed_issues) > 0:
            final_status = 'PASS_WITH_FIXES'
        else:
            final_status = 'PASS'

        summary = {
            'total_issues': len(self.issues),
            'issues_fixed': len(self.fixed_issues),
            'severity_breakdown': severity_counts,
            'level_breakdown': level_counts,
            'validation_levels': [level.value for level in ValidationLevel],
            'total_rows_validated': total_rows,
            'csv_files_processed': len(set(issue.csv_file for issue in self.issues))
        }

        return ValidationReport(
            client_name=client_name,
            timestamp=datetime.now().isoformat(),
            total_rows_validated=total_rows,
            issues_found=self.issues,
            issues_fixed=self.fixed_issues,
            summary=summary,
            final_status=final_status
        )

    def _save_report(self, report: ValidationReport, output_path: str):
        """Save validation report to file"""
        # Convert dataclasses to dictionaries for JSON serialization
        report_dict = asdict(report)

        # Convert enums to strings
        for issue in report_dict['issues_found']:
            issue['level'] = issue['level'].value if hasattr(issue['level'], 'value') else str(issue['level'])
            issue['severity'] = issue['severity'].value if hasattr(issue['severity'], 'value') else str(issue['severity'])

        for issue in report_dict['issues_fixed']:
            issue['level'] = issue['level'].value if hasattr(issue['level'], 'value') else str(issue['level'])
            issue['severity'] = issue['severity'].value if hasattr(issue['severity'], 'value') else str(issue['severity'])

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        logger.info(f"Report saved to: {output_path}")

    def validate_all_clients(self, auto_fix: bool = False, output_dir: Optional[str] = None) -> Dict[str, ValidationReport]:
        """Validate all client directories"""
        client_dirs = [d for d in self.base_path.iterdir() if d.is_dir() and not d.name.startswith('_')]

        reports = {}
        for client_dir in client_dirs:
            try:
                logger.info(f"Validating client: {client_dir.name}")
                report = self.validate_client_csvs(client_dir.name, auto_fix)

                if output_dir:
                    output_path = Path(output_dir) / f"{client_dir.name}_validation_report.json"
                    self._save_report(report, str(output_path))

                reports[client_dir.name] = report

            except Exception as e:
                logger.error(f"Failed to validate client {client_dir.name}: {e}")
                # Create error report
                reports[client_dir.name] = ValidationReport(
                    client_name=client_dir.name,
                    timestamp=datetime.now().isoformat(),
                    total_rows_validated=0,
                    issues_found=[ValidationIssue(
                        level=ValidationLevel.ACCOUNT,
                        severity=IssueSeverity.CRITICAL,
                        client_name=client_dir.name,
                        csv_file="",
                        row_number=0,
                        column="",
                        issue_type="validation_error",
                        message=f"Validation failed: {e}",
                        auto_fixable=False
                    )],
                    issues_fixed=[],
                    summary={'error': str(e)},
                    final_status='ERROR'
                )

        return reports

    def print_report_summary(self, report: ValidationReport):
        """Print a human-readable summary of the validation report"""
        print(f"\n{'='*80}")
        print(f"VALIDATION REPORT: {report.client_name.upper()}")
        print(f"{'='*80}")
        print(f"Timestamp: {report.timestamp}")
        print(f"Status: {report.final_status}")
        print(f"Rows Validated: {report.total_rows_validated}")
        print(f"Total Issues: {report.summary['total_issues']}")
        print(f"Issues Fixed: {report.summary['issues_fixed']}")

        if report.summary['severity_breakdown']['critical'] > 0:
            print(f"❌ Critical: {report.summary['severity_breakdown']['critical']}")
        if report.summary['severity_breakdown']['error'] > 0:
            print(f"❌ Errors: {report.summary['severity_breakdown']['error']}")
        if report.summary['severity_breakdown']['warning'] > 0:
            print(f"⚠️  Warnings: {report.summary['severity_breakdown']['warning']}")
        if report.summary['severity_breakdown']['info'] > 0:
            print(f"ℹ️  Info: {report.summary['severity_breakdown']['info']}")

        # Show top issues
        if report.issues_found:
            print(f"\nTOP ISSUES:")
            for i, issue in enumerate(report.issues_found[:10], 1):
                icon = {'critical': '🚨', 'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'}[issue.severity.value]
                print(f"{i}. {icon} [{issue.level.value.upper()}] {issue.message}")
                if issue.suggestion:
                    print(f"   💡 {issue.suggestion}")

        if len(report.issues_found) > 10:
            print(f"   ... and {len(report.issues_found) - 10} more issues")

        print(f"\n{'='*80}\n")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Comprehensive CSV Validator for Google Ads Agent')
    parser.add_argument('--client', help='Client name to validate')
    parser.add_argument('--all', action='store_true', help='Validate all clients')
    parser.add_argument('--fix', action='store_true', help='Auto-fix issues where possible')
    parser.add_argument('--output', help='Output directory for JSON reports')
    parser.add_argument('--output-file', help='Output file for single client report')

    args = parser.parse_args()

    validator = ComprehensiveCSVValidator()

    if args.all:
        print("🔍 Validating all client directories...")
        reports = validator.validate_all_clients(auto_fix=args.fix, output_dir=args.output)

        # Print summary of all clients
        total_issues = sum(r.summary['total_issues'] for r in reports.values())
        total_fixed = sum(r.summary['issues_fixed'] for r in reports.values())
        total_clients = len(reports)

        print(f"\n{'='*80}")
        print("ALL CLIENTS VALIDATION SUMMARY")
        print(f"{'='*80}")
        print(f"Clients Validated: {total_clients}")
        print(f"Total Issues Found: {total_issues}")
        print(f"Total Issues Fixed: {total_fixed}")

        # Show per-client status
        for client_name, report in reports.items():
            status_icon = {'PASS': '✅', 'PASS_WITH_FIXES': '⚠️', 'FAIL': '❌', 'ERROR': '🚨'}[report.final_status]
            print(f"{status_icon} {client_name}: {report.final_status} ({report.summary['total_issues']} issues)")

    elif args.client:
        print(f"🔍 Validating client: {args.client}")
        report = validator.validate_client_csvs(args.client, auto_fix=args.fix,
                                               output_path=args.output_file)
        validator.print_report_summary(report)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()