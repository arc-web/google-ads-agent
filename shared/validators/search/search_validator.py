#!/usr/bin/env python3
"""Legacy Search validator coordinator for active Google Ads Editor staging."""

from __future__ import annotations

import csv
import io
from collections import Counter
from pathlib import Path
from typing import Any

from shared.rebuild.staging_validator import validate_rows

from .ad_group_validator import AdGroupValidator
from .keyword_validator import KeywordValidator
from .search_campaign_validator import SearchCampaignValidator
from .text_ad_validator import TextAdValidator


class SearchValidator:
    """
    Compatibility coordinator for Search validation.

    Older callers can still pass raw CSV content here. The active rebuild
    staging validator remains the source of truth, while the wrapper validators
    add generic row-level compatibility checks.
    """

    def __init__(self, validation_rules: dict[str, Any] | None = None):
        self.validation_rules = validation_rules or {}
        self.campaign_validator = SearchCampaignValidator(self.validation_rules)
        self.ad_group_validator = AdGroupValidator(self.validation_rules)
        self.keyword_validator = KeywordValidator(self.validation_rules)
        self.text_ad_validator = TextAdValidator(self.validation_rules)

    def validate_search_csv(self, csv_path: str, csv_content: str) -> list[dict[str, Any]]:
        """Validate a Search campaign CSV string."""
        try:
            headers, rows = self._read_rows(csv_content)
        except Exception as exc:
            return [
                {
                    "level": "search_campaign",
                    "severity": "critical",
                    "row_number": 0,
                    "column": "",
                    "issue_type": "validation_error",
                    "message": f"Failed to parse Search campaign CSV: {exc}",
                    "auto_fixable": False,
                }
            ]

        source = Path(csv_path)
        staging_report = validate_rows(headers, rows, source, "in-memory")
        issues = [self._issue_from_staging(issue) for issue in staging_report.get("issues", [])]

        campaign_rows = [row for row in rows if self._is_campaign_row(row)]
        ad_group_rows = [row for row in rows if self._is_ad_group_row(row)]
        keyword_rows = [row for row in rows if self._is_keyword_row(row)]
        text_ad_rows = [row for row in rows if self._is_text_ad_row(row)]

        issues.extend(self.campaign_validator_dicts(campaign_rows))
        issues.extend(self.ad_group_validator.validate_adgroup_data(ad_group_rows))
        issues.extend(self.keyword_validator.validate_keyword_data(keyword_rows))
        issues.extend(self.text_ad_validator.validate_text_ad_data(text_ad_rows))

        return self._deduplicate(issues)

    def campaign_validator_dicts(self, campaign_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Run campaign validation and normalize dataclass issues to dictionaries."""
        return [issue.__dict__ for issue in self.campaign_validator.validate_campaign_data(campaign_rows)]

    def _read_rows(self, csv_content: str) -> tuple[list[str], list[dict[str, str]]]:
        sample = csv_content[:2048]
        delimiter = "\t" if "\t" in sample else ","
        reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter)
        rows = [{key: value or "" for key, value in row.items() if key is not None} for row in reader]
        return list(reader.fieldnames or []), rows

    def _issue_from_staging(self, issue: dict[str, Any]) -> dict[str, Any]:
        severity_map = {"error": "critical", "warning": "warning", "info": "info"}
        return {
            "level": "active_staging",
            "severity": severity_map.get(issue.get("severity", "warning"), "warning"),
            "row_number": issue.get("row") or 0,
            "column": issue.get("column") or "",
            "issue_type": issue.get("rule") or "staging_rule",
            "message": issue.get("message") or "Staging validation issue.",
            "suggestion": "Follow the active Google Ads Editor staging rules.",
            "auto_fixable": False,
        }

    def _is_campaign_row(self, row: dict[str, Any]) -> bool:
        return str(row.get("Campaign Type") or row.get("Campaign type") or "").strip() == "Search"

    def _is_ad_group_row(self, row: dict[str, Any]) -> bool:
        return bool(str(row.get("Ad Group") or row.get("Ad group") or "").strip()) and not self._is_keyword_row(row) and not self._is_text_ad_row(row)

    def _is_keyword_row(self, row: dict[str, Any]) -> bool:
        return bool(str(row.get("Keyword", "") or "").strip())

    def _is_text_ad_row(self, row: dict[str, Any]) -> bool:
        return bool(str(row.get("Ad type") or row.get("Ad Type") or row.get("Headline 1") or row.get("Description 1") or "").strip())

    def _deduplicate(self, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[tuple[Any, ...]] = set()
        deduped: list[dict[str, Any]] = []
        for issue in issues:
            key = (
                issue.get("level"),
                issue.get("row_number"),
                issue.get("column"),
                issue.get("issue_type"),
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(issue)
        return deduped

    def _validate_cross_ad_group_relationships(self, ad_groups_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Legacy helper retained for callers with pre-grouped ad group data."""
        issues: list[dict[str, Any]] = []
        for ad_group_name, data in ad_groups_data.items():
            keyword_count = int(data.get("keyword_count", 0) or 0)
            if keyword_count > 20_000:
                issues.append(
                    {
                        "level": "ad_group",
                        "severity": "critical",
                        "row_number": data.get("first_row", 0),
                        "column": "Ad Group",
                        "issue_type": "too_many_keywords",
                        "message": f'Ad group "{ad_group_name}" has {keyword_count} keywords.',
                        "auto_fixable": False,
                    }
                )
        return issues

    def get_search_campaign_requirements(self) -> dict[str, Any]:
        """Return active Search staging requirements."""
        return {
            "campaign_type": "Search",
            "required_headers": [
                "Campaign",
                "Campaign Type",
                "Networks",
                "Budget",
                "Budget type",
                "EU political ads",
                "Broad match keywords",
                "Ad Group",
                "Keyword",
                "Criterion Type",
                "Ad type",
                "Final URL",
                "Location",
                "Location ID",
            ],
            "keyword_match_types": ["Phrase", "Negative Phrase"],
            "text_ad_limits": {
                "max_headlines": 15,
                "max_descriptions": 4,
                "headline_length": {"max": 30},
                "description_length": {"max": 90},
            },
            "staging": "Google Ads Editor CSV review before import",
        }
