"""
Search Campaign Validator

Validates Search campaign CSVs with proper structure for Ad Groups.
Search campaigns are fundamentally different from PMAX campaigns.

Key Differences from PMAX Validation:
- Validates Ad Groups (not Asset Groups)
- Checks for Search network only
- Validates keyword match types
- Checks text ad structure
- No audience signals or asset validation
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import re


class ValidationLevel(Enum):
    CAMPAIGN = "campaign"
    AD_GROUP = "ad_group"
    KEYWORD = "keyword"
    AD = "ad"


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


class SearchCampaignValidator:
    """
    Validates Search campaign CSVs.

    Search campaigns use:
    - Ad Groups (not Asset Groups)
    - Keywords with match types
    - Text ads
    - Search network only
    """

    def __init__(self):
        self.issues: List[ValidationIssue] = []

    def validate_search_campaign_row(self, client_name: str, csv_path: str,
                                   row: Dict[str, str], row_num: int):
        """Validate a Search campaign row"""
        campaign_type = row.get("Campaign Type", "").strip()

        if campaign_type != "Search":
            return  # Skip non-Search campaigns

        # Validate Search network settings
        self._validate_search_network_settings(client_name, csv_path, row, row_num)

        # Validate bid strategy
        self._validate_search_bid_strategy(client_name, csv_path, row, row_num)

    def validate_search_ad_group_row(self, client_name: str, csv_path: str,
                                   row: Dict[str, str], row_num: int):
        """Validate a Search Ad Group row"""
        ad_group = row.get("Ad Group", "").strip()

        if not ad_group:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.AD_GROUP,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Ad Group",
                issue_type="missing_ad_group",
                message="Search campaigns require Ad Groups",
                auto_fixable=False
            ))
            return

        # Validate Ad Group naming (no Asset Group confusion)
        if "asset" in ad_group.lower():
            self.issues.append(ValidationIssue(
                level=ValidationLevel.AD_GROUP,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Ad Group",
                issue_type="invalid_ad_group_name",
                message="Ad Groups should not contain 'asset' - that's for PMAX campaigns",
                auto_fixable=False
            ))

        # Validate bid strategy for Ad Group
        self._validate_ad_group_bid_strategy(client_name, csv_path, row, row_num)

        # VALIDATE KEYWORD IN AD GROUP ROW (Google Ads Editor spec)
        keyword = row.get("Keyword", "").strip()
        criterion_type = row.get("Criterion Type", "").strip()
        final_url = row.get("Final URL", "").strip()

        if not keyword:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.AD_GROUP,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Keyword",
                issue_type="missing_keyword_in_ad_group",
                message="Ad Group rows must include keywords in the 'Keyword' column",
                auto_fixable=False
            ))
        else:
            # Validate keyword format
            if len(keyword.split()) < 2:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.AD_GROUP,
                    severity=IssueSeverity.WARNING,
                    client_name=client_name,
                    csv_file=csv_path,
                    row_number=row_num,
                    column="Keyword",
                    issue_type="short_keyword",
                    message=f"Keyword '{keyword}' is very short - consider longer, more specific keywords",
                    auto_fixable=False
                ))

        # Validate Criterion Type
        valid_match_types = ["Exact", "Phrase", "Broad"]
        if criterion_type and criterion_type not in valid_match_types:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.AD_GROUP,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Criterion Type",
                issue_type="invalid_criterion_type",
                message=f"Invalid Criterion Type '{criterion_type}'. Must be one of: {', '.join(valid_match_types)}",
                auto_fixable=True,
                fix_value="Exact"
            ))

        # Validate Final URL
        if not final_url:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.AD_GROUP,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Final URL",
                issue_type="missing_final_url",
                message="Final URL is required for keywords in Ad Group rows",
                auto_fixable=False
            ))
        elif not final_url.startswith(('http://', 'https://')):
            self.issues.append(ValidationIssue(
                level=ValidationLevel.AD_GROUP,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Final URL",
                issue_type="invalid_final_url",
                message=f"Final URL must start with http:// or https://, got: {final_url}",
                auto_fixable=True,
                fix_value=f"https://{final_url}"
            ))

    def validate_search_keyword_row(self, client_name: str, csv_path: str,
                                  row: Dict[str, str], row_num: int):
        """
        Validate a Search keyword row

        NOTE: In corrected Google Ads Editor format, keywords are in Ad Group rows,
        not separate keyword rows. This method now detects obsolete separate keyword rows.
        """
        ad_group = row.get("Ad Group", "").strip()
        status = row.get("Status", "").strip()
        keyword = row.get("Keyword", "").strip()

        # Check for old-style separate keyword rows (obsolete)
        if status == "Enabled" and not ad_group and keyword:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.KEYWORD,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Status",
                issue_type="obsolete_keyword_format",
                message="Separate keyword rows are obsolete. Keywords must be in Ad Group rows per Google Ads Editor spec.",
                auto_fixable=False
            ))
        # If this has an Ad Group and keyword, it's likely a duplicate validation (already checked in ad group validation)
        elif ad_group and keyword:
            # Keywords are validated in validate_search_ad_group_row, so just log this is expected
            pass
        # If this is a keyword row without proper structure, flag it
        elif not ad_group and keyword:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.KEYWORD,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Ad Group",
                issue_type="keyword_without_ad_group",
                message="Keyword row missing Ad Group - keywords should be in Ad Group rows",
                auto_fixable=False
            ))

    def validate_search_ad_row(self, client_name: str, csv_path: str,
                             row: Dict[str, str], row_num: int):
        """Validate a Search text ad row"""
        headline_1 = row.get("Headline 1", "").strip()
        description_1 = row.get("Description 1", "").strip()
        final_url = row.get("Final URL", "").strip()

        # Validate required ad components
        if not headline_1:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.AD,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Headline 1",
                issue_type="missing_headline",
                message="Headline 1 is required for Search ads",
                auto_fixable=False
            ))

        if not description_1:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.AD,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Description 1",
                issue_type="missing_description",
                message="Description 1 is required for Search ads",
                auto_fixable=False
            ))

        if not final_url:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.AD,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Final URL",
                issue_type="missing_final_url",
                message="Final URL is required for Search ads",
                auto_fixable=False
            ))

    def _validate_search_network_settings(self, client_name: str, csv_path: str,
                                        row: Dict[str, str], row_num: int):
        """Validate Search network settings"""
        networks = row.get("Networks", "").strip()
        search_partners = row.get("Search Partners", "").strip()
        display_network = row.get("Display Network", "").strip()

        # Must be Search network only
        if networks != "Search":
            self.issues.append(ValidationIssue(
                level=ValidationLevel.CAMPAIGN,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Networks",
                issue_type="invalid_network",
                message="Search campaigns must use 'Search' network only",
                auto_fixable=True,
                fix_value="Search"
            ))

        # Search Partners must be disabled
        if search_partners != "Disabled":
            self.issues.append(ValidationIssue(
                level=ValidationLevel.CAMPAIGN,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Search Partners",
                issue_type="search_partners_enabled",
                message="Search Partners must be Disabled for Search campaigns",
                auto_fixable=True,
                fix_value="Disabled"
            ))

        # Display Network must be disabled
        if display_network != "Disabled":
            self.issues.append(ValidationIssue(
                level=ValidationLevel.CAMPAIGN,
                severity=IssueSeverity.ERROR,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Display Network",
                issue_type="display_network_enabled",
                message="Display Network must be Disabled for Search campaigns",
                auto_fixable=True,
                fix_value="Disabled"
            ))

    def _validate_search_bid_strategy(self, client_name: str, csv_path: str,
                                    row: Dict[str, str], row_num: int):
        """Validate Search campaign bid strategy"""
        bid_strategy = row.get("Campaign Bid Strategy Type", "").strip()

        valid_strategies = ["Manual CPC", "Target CPA", "Maximize Conversions", "Maximize Clicks"]

        if bid_strategy not in valid_strategies:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.CAMPAIGN,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Campaign Bid Strategy Type",
                issue_type="invalid_bid_strategy",
                message=f"Search campaign bid strategy should be one of: {', '.join(valid_strategies)}",
                auto_fixable=False
            ))

    def _validate_ad_group_bid_strategy(self, client_name: str, csv_path: str,
                                      row: Dict[str, str], row_num: int):
        """Validate Ad Group bid strategy"""
        bid_strategy = row.get("Ad Group Bid Strategy Type", "").strip()

        valid_strategies = ["Manual CPC", "Target CPA", "Maximize Conversions", "Maximize Clicks"]

        if bid_strategy and bid_strategy not in valid_strategies:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.AD_GROUP,
                severity=IssueSeverity.WARNING,
                client_name=client_name,
                csv_file=csv_path,
                row_number=row_num,
                column="Ad Group Bid Strategy Type",
                issue_type="invalid_ad_group_bid_strategy",
                message=f"Ad Group bid strategy should be one of: {', '.join(valid_strategies)}",
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