"""
PMAX campaign salvage validator.

The active Google Ads Agent rebuild flow is Search-first. This module keeps
PMAX validation available for explicit PMAX rows without making PMAX active for
Search workflows.
"""

from enum import Enum
from typing import Any, Dict, List, Optional


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
    """Simple serializable validation issue."""

    def __init__(
        self,
        level: ValidationLevel,
        severity: IssueSeverity,
        csv_file: str,
        row_number: int,
        column: str,
        issue_type: str,
        message: str,
        auto_fixable: bool = False,
        fix_value: Any = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.level = level.value
        self.severity = severity.value
        self.csv_file = csv_file
        self.row_number = row_number
        self.column = column
        self.issue_type = issue_type
        self.message = message
        self.auto_fixable = auto_fixable
        self.fix_value = fix_value
        self.context = context or {}


class PMAXCampaignValidator:
    """
    Validates explicit PMAX rows only.

    Existing callers may still pass a context value as the first argument. The
    value is accepted for compatibility and intentionally not stored on issues.
    """

    VALID_CAMPAIGN_BID_STRATEGIES = {
        "Maximize Conversion Value",
        "Target ROAS",
        "Target CPA",
    }
    VALID_ASSET_TYPES = {"TEXT", "IMAGE", "VIDEO", "YOUTUBE_VIDEO", "MEDIA_BUNDLE"}

    def __init__(self):
        self.issues: List[ValidationIssue] = []

    def validate_pmax_campaign_row(
        self,
        legacy_context: str,
        csv_path: str,
        row: Dict[str, str],
        row_num: int,
    ) -> None:
        """Validate a row only when it is explicitly Performance Max."""
        del legacy_context
        if not self._is_pmax_row(row):
            return

        self._validate_pmax_settings(csv_path, row, row_num)
        self._validate_pmax_bid_strategy(csv_path, row, row_num)

    def validate_pmax_asset_group_row(
        self,
        legacy_context: str,
        csv_path: str,
        row: Dict[str, str],
        row_num: int,
    ) -> None:
        """Validate PMAX asset group fields on explicit PMAX or asset rows."""
        del legacy_context
        if not self._is_pmax_or_asset_group_row(row):
            return

        asset_group = row.get("Asset Group", "").strip()
        if not asset_group:
            self._add_issue(
                ValidationLevel.ASSET_GROUP,
                IssueSeverity.ERROR,
                csv_path,
                row_num,
                "Asset Group",
                "missing_asset_group",
                "Explicit PMAX asset rows require Asset Group",
            )
            return

        if "ad group" in asset_group.lower() or "ad_group" in asset_group.lower():
            self._add_issue(
                ValidationLevel.ASSET_GROUP,
                IssueSeverity.WARNING,
                csv_path,
                row_num,
                "Asset Group",
                "asset_group_mentions_ad_group",
                "Asset Group name appears to reference an Ad Group",
            )

        if not row.get("Final URL", "").strip():
            self._add_issue(
                ValidationLevel.ASSET_GROUP,
                IssueSeverity.ERROR,
                csv_path,
                row_num,
                "Final URL",
                "missing_final_url",
                "Asset Groups require a Final URL",
            )

    def validate_pmax_asset_row(
        self,
        legacy_context: str,
        csv_path: str,
        row: Dict[str, str],
        row_num: int,
    ) -> None:
        """Validate PMAX asset rows when Asset or Asset Type is present."""
        del legacy_context
        asset_type = row.get("Asset Type", "").strip()
        asset = row.get("Asset", "").strip()
        if not asset_type and not asset:
            return

        if not asset:
            self._add_issue(
                ValidationLevel.ASSET,
                IssueSeverity.ERROR,
                csv_path,
                row_num,
                "Asset",
                "missing_asset",
                "Asset rows require an Asset value",
            )

        if asset_type and asset_type not in self.VALID_ASSET_TYPES:
            self._add_issue(
                ValidationLevel.ASSET,
                IssueSeverity.ERROR,
                csv_path,
                row_num,
                "Asset Type",
                "invalid_asset_type",
                f"Asset Type must be one of: {', '.join(sorted(self.VALID_ASSET_TYPES))}",
            )

        self._validate_asset_content(csv_path, row, row_num, asset_type)

    def validate_pmax_search_theme_row(
        self,
        legacy_context: str,
        csv_path: str,
        row: Dict[str, str],
        row_num: int,
    ) -> None:
        """Validate PMAX search theme rows when Search Theme exists."""
        del legacy_context
        search_theme = row.get("Search Theme", "").strip()
        if not search_theme:
            return

        if len(search_theme.split()) < 2:
            self._add_issue(
                ValidationLevel.SEARCH_THEME,
                IssueSeverity.WARNING,
                csv_path,
                row_num,
                "Search Theme",
                "search_theme_too_short",
                "Search themes are usually descriptive phrases",
            )

    def _validate_pmax_settings(self, csv_path: str, row: Dict[str, str], row_num: int) -> None:
        eu_political = row.get("EU political ads", "").strip()
        if not eu_political:
            self._add_issue(
                ValidationLevel.CAMPAIGN,
                IssueSeverity.ERROR,
                csv_path,
                row_num,
                "EU political ads",
                "missing_eu_political_ads",
                "Performance Max rows should populate EU political ads",
            )

        brand_guidelines = row.get("Brand guidelines", "").strip()
        if brand_guidelines and brand_guidelines not in {"Enabled", "Disabled"}:
            self._add_issue(
                ValidationLevel.CAMPAIGN,
                IssueSeverity.WARNING,
                csv_path,
                row_num,
                "Brand guidelines",
                "unexpected_brand_guidelines_value",
                "Brand guidelines should be Enabled or Disabled when provided",
            )

    def _validate_pmax_bid_strategy(self, csv_path: str, row: Dict[str, str], row_num: int) -> None:
        bid_strategy = row.get("Campaign Bid Strategy Type", "").strip()
        if not bid_strategy:
            return

        if bid_strategy not in self.VALID_CAMPAIGN_BID_STRATEGIES:
            self._add_issue(
                ValidationLevel.CAMPAIGN,
                IssueSeverity.WARNING,
                csv_path,
                row_num,
                "Campaign Bid Strategy Type",
                "unexpected_bid_strategy",
                f"PMAX bid strategy should be one of: {', '.join(sorted(self.VALID_CAMPAIGN_BID_STRATEGIES))}",
            )

    def _validate_asset_content(
        self,
        csv_path: str,
        row: Dict[str, str],
        row_num: int,
        asset_type: str,
    ) -> None:
        if asset_type == "TEXT" and not row.get("Text Asset", "").strip():
            self._add_issue(
                ValidationLevel.ASSET,
                IssueSeverity.ERROR,
                csv_path,
                row_num,
                "Text Asset",
                "missing_text_asset",
                "TEXT assets require Text Asset content",
            )

        if asset_type == "IMAGE" and not row.get("Image", "").strip():
            self._add_issue(
                ValidationLevel.ASSET,
                IssueSeverity.ERROR,
                csv_path,
                row_num,
                "Image",
                "missing_image_asset",
                "IMAGE assets require Image content",
            )

    def _is_pmax_row(self, row: Dict[str, str]) -> bool:
        return row.get("Campaign Type", "").strip().lower() == "performance max"

    def _is_pmax_or_asset_group_row(self, row: Dict[str, str]) -> bool:
        return self._is_pmax_row(row) or bool(row.get("Asset Group", "").strip())

    def _add_issue(
        self,
        level: ValidationLevel,
        severity: IssueSeverity,
        csv_path: str,
        row_num: int,
        column: str,
        issue_type: str,
        message: str,
        auto_fixable: bool = False,
        fix_value: Any = None,
    ) -> None:
        self.issues.append(ValidationIssue(
            level=level,
            severity=severity,
            csv_file=csv_path,
            row_number=row_num,
            column=column,
            issue_type=issue_type,
            message=message,
            auto_fixable=auto_fixable,
            fix_value=fix_value,
        ))

    def get_validation_report(self) -> Dict[str, Any]:
        """Get a serializable validation report."""
        return {
            "total_issues": len(self.issues),
            "critical": len([i for i in self.issues if i.severity == IssueSeverity.CRITICAL.value]),
            "errors": len([i for i in self.issues if i.severity == IssueSeverity.ERROR.value]),
            "warnings": len([i for i in self.issues if i.severity == IssueSeverity.WARNING.value]),
            "info": len([i for i in self.issues if i.severity == IssueSeverity.INFO.value]),
            "issues": [issue.__dict__ for issue in self.issues],
        }
