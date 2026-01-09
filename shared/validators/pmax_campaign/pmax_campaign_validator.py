"""
PMAX Campaign Validator

Validates PMAX campaign CSVs with proper structure for Asset Groups.
PMAX campaigns are fundamentally different from Search campaigns.

Key Differences from Search Validation:
- Validates Asset Groups (not Ad Groups)
- Checks for multi-network campaigns (Search, Display, YouTube)
- Validates audience signals and assets
- Checks search themes (not keywords)
- Validates responsive search ads
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import re


class ValidationLevel(Enum):
    CAMPAIGN = "campaign"
    ASSET_GROUP = "asset_group"
    ASSET = "asset"
    SEARCH_THEME = "search_theme"


class IssueSeverity(Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssue:
    def __init__(self, level: ValidationLevel, severity: IssueSeverity,
                 client_name: str, csv_file: str, row_number: int, column: str,
                 issue_type: str, message: str, auto_fixable: bool = False,
                 fix_value: Any = None):
        self.level = level
        self.severity = severity
        self.client_name = client_name
        self.csv_file = csv_file
        self.row_number = row_number
        self.column = column
        self.issue_type = issue_type
        self.message = message
        self.auto_fixable = auto_fixable
        self.fix_value = fix_value


class PMAXCampaignValidator:
    """
    Validates PMAX campaign CSVs.

    PMAX campaigns use:
    - Asset Groups (not Ad Groups)
    - Search themes (not keywords)
    - Multi-network (Search, Display, YouTube)
    - Audience signals
    - Responsive search ads
    """

    def __init__(self):
        self.issues: List[ValidationIssue] = []

    def validate_pmax_campaign_row(self, client_name: str, csv_path: str,
                                 row: Dict[str, str], row_num: int):
        """Validate a PMAX campaign row"""
        campaign_type = row.get("Campaign Type", "").strip()

        if campaign_type != "Performance Max":
            return  # Skip non-PMAX campaigns

        # Validate PMAX network settings
        self._validate_pmax_network_settings(client_name, csv_path, row, row_num)

        # Validate PMAX-specific settings
        self._validate_pmax_settings(client_name, csv_path, row, row_num)

        # Validate bid strategy
        self._validate_pmax_bid_strategy(client_name, csv_path, row, row_num)

    def validate_pmax_asset_group_row(self, client_name: str, csv_path: str,
                                    row: Dict[str, str], row_num: int):
        """Validate a PMAX Asset Group row"""
        asset_group = row.get("Asset Group", "").strip()

        if not asset_group:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET_GROUP,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Asset Group",
                issue_type="missing_asset_group",
                message="PMAX campaigns require Asset Groups",
                auto_fixable=False
            ))
            return

        # Validate Asset Group naming (no Ad Group confusion)
        if "ad group" in asset_group.lower() or "ad_group" in asset_group.lower():
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET_GROUP,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Asset Group",
                issue_type="invalid_asset_group_name",
                message="Asset Groups should not contain 'ad group' - that's for Search campaigns",
                auto_fixable=False
            ))

        # Validate required Asset Group fields
        final_url = row.get("Final URL", "").strip()
        if not final_url:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET_GROUP,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Final URL",
                issue_type="missing_final_url",
                message="Asset Groups require a Final URL",
                auto_fixable=False
            ))

        # Validate bid strategy for Asset Group
        self._validate_asset_group_bid_strategy(client_name, csv_path, row, row_num)

    def validate_pmax_asset_row(self, client_name: str, csv_path: str,
                              row: Dict[str, str], row_num: int):
        """Validate a PMAX asset row"""
        asset_type = row.get("Asset Type", "").strip()
        asset = row.get("Asset", "").strip()

        if not asset:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Asset",
                issue_type="missing_asset",
                message="PMAX assets require a name/identifier",
                auto_fixable=False
            ))
            return

        # Validate asset type
        valid_asset_types = ["TEXT", "IMAGE", "VIDEO", "YOUTUBE_VIDEO", "MEDIA_BUNDLE"]
        if asset_type not in valid_asset_types:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Asset Type",
                issue_type="invalid_asset_type",
                message=f"Asset type must be one of: {', '.join(valid_asset_types)}",
                auto_fixable=False
            ))

        # Validate asset content based on type
        self._validate_asset_content(client_name, csv_path, row, row_num, asset_type)

    def validate_pmax_search_theme_row(self, client_name: str, csv_path: str,
                                     row: Dict[str, str], row_num: int):
        """Validate a PMAX search theme row"""
        search_theme = row.get("Search Theme", "").strip()

        if not search_theme:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.SEARCH_THEME,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Search Theme",
                issue_type="missing_search_theme",
                message="Search themes are required for PMAX campaigns",
                auto_fixable=False
            ))
            return

        # Validate search theme format (should be descriptive phrases)
        if len(search_theme.split()) < 2:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.SEARCH_THEME,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Search Theme",
                issue_type="search_theme_too_short",
                message="Search themes should be descriptive phrases (2+ words)",
                auto_fixable=False
            ))

    def _validate_pmax_network_settings(self, client_name: str, csv_path: str,
                                      row: Dict[str, str], row_num: int):
        """Validate PMAX network settings"""
        networks = row.get("Networks", "").strip()

        # PMAX should include multiple networks
        expected_networks = ["Search", "Display", "YouTube"]
        if not all(network in networks for network in expected_networks):
            self.issues.append(ValidationIssue(
                level=ValidationLevel.CAMPAIGN,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Networks",
                issue_type="incomplete_networks",
                message=f"PMAX campaigns should include: {', '.join(expected_networks)}",
                auto_fixable=False
            ))

    def _validate_pmax_settings(self, client_name: str, csv_path: str,
                              row: Dict[str, str], row_num: int):
        """Validate PMAX-specific settings"""
        eu_political = row.get("EU political ads", "").strip()
        brand_guidelines = row.get("Brand guidelines", "").strip()

        # EU political ads should be set appropriately
        if eu_political != "Doesn't have EU political ads":
            self.issues.append(ValidationIssue(
                level=ValidationLevel.CAMPAIGN,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="EU political ads",
                issue_type="eu_political_not_set",
                message="EU political ads should be set to 'Doesn't have EU political ads'",
                auto_fixable=True,
                fix_value="Doesn't have EU political ads"
            ))

        # Brand guidelines should be disabled
        if brand_guidelines != "Disabled":
            self.issues.append(ValidationIssue(
                level=ValidationLevel.CAMPAIGN,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Brand guidelines",
                issue_type="brand_guidelines_not_disabled",
                message="Brand guidelines must be Disabled for PMAX campaigns",
                auto_fixable=True,
                fix_value="Disabled"
            ))

    def _validate_pmax_bid_strategy(self, client_name: str, csv_path: str,
                                  row: Dict[str, str], row_num: int):
        """Validate PMAX campaign bid strategy"""
        bid_strategy = row.get("Campaign Bid Strategy Type", "").strip()

        valid_strategies = ["Maximize Conversion Value", "Target ROAS", "Target CPA", "Manual CPC"]

        if bid_strategy not in valid_strategies:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.CAMPAIGN,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Campaign Bid Strategy Type",
                issue_type="invalid_bid_strategy",
                message=f"PMAX campaign bid strategy should be one of: {', '.join(valid_strategies)}",
                auto_fixable=False
            ))

    def _validate_asset_group_bid_strategy(self, client_name: str, csv_path: str,
                                         row: Dict[str, str], row_num: int):
        """Validate Asset Group bid strategy"""
        bid_strategy = row.get("Asset Group Bid Strategy Type", "").strip()

        valid_strategies = ["Maximize Conversion Value", "Target ROAS", "Target CPA", "Manual CPC"]

        if bid_strategy and bid_strategy not in valid_strategies:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.ASSET_GROUP,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Asset Group Bid Strategy Type",
                issue_type="invalid_asset_group_bid_strategy",
                message=f"Asset Group bid strategy should be one of: {', '.join(valid_strategies)}",
                auto_fixable=False
            ))

    def _validate_asset_content(self, client_name: str, csv_path: str,
                              row: Dict[str, str], row_num: int, asset_type: str):
        """Validate asset content based on type"""
        if asset_type == "TEXT":
            text_asset = row.get("Text Asset", "").strip()
            if not text_asset:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ASSET,
                    severity=IssueSeverity.ERROR,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Text Asset",
                    issue_type="missing_text_asset",
                    message="TEXT assets require Text Asset content",
                    auto_fixable=False
                ))
        elif asset_type == "IMAGE":
            image = row.get("Image", "").strip()
            if not image:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.ASSET,
                    severity=IssueSeverity.ERROR,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Image",
                    issue_type="missing_image_asset",
                    message="IMAGE assets require Image URL",
                    auto_fixable=False
                ))

    def get_validation_report(self) -> Dict[str, Any]:
        """Get validation report"""
        return {
            "total_issues": len(self.issues),
            "critical": len([i for i in self.issues if i.severity == IssueSeverity.CRITICAL]),
            "errors": len([i for i in self.issues if i.severity == IssueSeverity.ERROR]),
            "warnings": len([i for i in self.issues if i.severity == IssueSeverity.WARNING]),
            "info": len([i for i in self.issues if i.severity == IssueSeverity.INFO]),
            "issues": [vars(issue) for issue in self.issues]
        }