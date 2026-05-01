#!/usr/bin/env python3
"""Legacy Search ad group validator wrapper."""

from __future__ import annotations

from typing import Any

from .search_adgroup_validator import SearchAdGroupValidator


class AdGroupValidator:
    """
    Compatibility wrapper around the active Search ad group validator.

    Older code imports this class name. The implementation now delegates to
    SearchAdGroupValidator so active headers, generic rules, and test coverage
    stay in one place.
    """

    def __init__(self, validation_rules: dict[str, Any] | None = None):
        self.validator = SearchAdGroupValidator(validation_rules)

    def validate_ad_group(
        self,
        csv_path: str,
        row: dict[str, Any],
        row_num: int,
        ad_groups_data: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Validate one ad group row and update optional legacy aggregate data."""
        issues = self.validate_adgroup_row(row, row_num)

        if ad_groups_data is not None:
            campaign = str(row.get("Campaign", "") or "").strip()
            ad_group = str(row.get("Ad Group") or row.get("Ad group") or "").strip()
            if ad_group:
                ad_groups_data.setdefault(
                    ad_group,
                    {
                        "campaign": campaign,
                        "status": str(row.get("Status", "") or "").strip() or "Enabled",
                        "keyword_count": 0,
                        "text_ad_count": 0,
                        "first_row": row_num,
                        "keywords": [],
                        "match_types": set(),
                    },
                )

        return issues

    def validate_adgroup_row(self, row: dict[str, Any], row_num: int) -> list[dict[str, Any]]:
        """Validate one ad group row using active rules."""
        return [issue.__dict__ for issue in self.validator.validate_adgroup_row(row, row_num)]

    def validate_ad_group_structure(self, ad_groups_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Legacy aggregate check for callers that still pass grouped data."""
        rows: list[dict[str, Any]] = []
        for ad_group, data in ad_groups_data.items():
            rows.append(
                {
                    "Campaign": data.get("campaign", ""),
                    "Ad Group": ad_group,
                    "Status": data.get("status", ""),
                }
            )
        return self.validate_adgroup_data(rows)

    def validate_adgroup_data(self, adgroup_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate multiple ad group rows using active rules."""
        return [issue.__dict__ for issue in self.validator.validate_adgroup_data(adgroup_rows)]
