#!/usr/bin/env python3
"""
Generic asset group CSV validator.

Asset groups are PMAX salvage checks in the current Search-first process. This
validator skips ordinary Search rows and only validates rows that explicitly
look like PMAX or asset group data.
"""

import csv
import io
import re
from typing import Any, Dict, Iterable, List


class AssetGroupValidator:
    """Validates asset group structure without promoting PMAX into Search."""

    MAX_HEADLINES = 15
    MAX_DESCRIPTIONS = 5
    MAX_VIDEOS = 5

    _URL_PATTERN = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)

    def validate_asset_groups(self, csv_path: str, csv_content: str) -> List[Dict[str, Any]]:
        """Validate PMAX or asset group rows in a CSV string."""
        del csv_path
        issues: List[Dict[str, Any]] = []
        seen_asset_groups: Dict[str, Dict[str, str]] = {}

        try:
            for row_num, row in self._iter_rows(csv_content):
                if not self._is_asset_group_like_row(row):
                    continue

                issues.extend(self._validate_asset_group_identity(row, row_num, seen_asset_groups))
                issues.extend(self._validate_asset_counts(row, row_num))
                issues.extend(self._validate_urls(row, row_num))
        except Exception as exc:
            issues.append(self._issue(
                severity="critical",
                row_number=0,
                column="",
                issue_type="validation_error",
                message=f"Failed to validate asset groups: {exc}",
            ))

        return issues

    def _iter_rows(self, csv_content: str) -> Iterable[tuple[int, Dict[str, str]]]:
        sample = csv_content[:2048]
        delimiter = "\t" if sample.count("\t") >= sample.count(",") else ","
        reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter)
        for row_num, row in enumerate(reader, 2):
            yield row_num, {str(key): value for key, value in row.items() if key is not None}

    def _is_asset_group_like_row(self, row: Dict[str, str]) -> bool:
        if row.get("Campaign Type", "").strip().lower() == "performance max":
            return True
        return bool(row.get("Asset Group", "").strip())

    def _validate_asset_group_identity(
        self,
        row: Dict[str, str],
        row_num: int,
        seen_asset_groups: Dict[str, Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        campaign_type = row.get("Campaign Type", "").strip().lower()
        asset_group = row.get("Asset Group", "").strip()
        campaign = row.get("Campaign", "").strip()
        final_url = row.get("Final URL", "").strip()

        if campaign_type == "performance max" and not asset_group:
            issues.append(self._issue(
                severity="error",
                row_number=row_num,
                column="Asset Group",
                issue_type="missing_asset_group",
                message="Performance Max rows require Asset Group when PMAX validation is in use",
            ))
            return issues

        if not asset_group:
            return issues

        if "ad group" in asset_group.lower() or "ad_group" in asset_group.lower():
            issues.append(self._issue(
                severity="warning",
                row_number=row_num,
                column="Asset Group",
                issue_type="asset_group_mentions_ad_group",
                message="Asset Group name appears to reference an Ad Group",
            ))

        if not final_url:
            issues.append(self._issue(
                severity="error",
                row_number=row_num,
                column="Final URL",
                issue_type="missing_final_url",
                message=f'Asset group "{asset_group}" requires a Final URL',
            ))

        key = f"{campaign}::{asset_group}"
        if key not in seen_asset_groups:
            seen_asset_groups[key] = {"final_url": final_url}
        elif final_url and seen_asset_groups[key].get("final_url") != final_url:
            issues.append(self._issue(
                severity="error",
                row_number=row_num,
                column="Final URL",
                issue_type="inconsistent_final_url",
                message=f'Asset group "{asset_group}" has inconsistent Final URLs',
            ))

        return issues

    def _validate_asset_counts(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        asset_group = row.get("Asset Group", "").strip() or "(unnamed asset group)"

        headline_count = self._count_numbered_columns(row, "Headline", 15)
        description_count = self._count_numbered_columns(row, "Description", 5)
        video_count = self._count_numbered_columns(row, "Video ID", 5)

        if headline_count > self.MAX_HEADLINES:
            issues.append(self._issue(
                severity="error",
                row_number=row_num,
                column="Headlines",
                issue_type="too_many_headlines",
                message=f'Asset group "{asset_group}" has {headline_count} headlines, max is {self.MAX_HEADLINES}',
            ))

        if description_count > self.MAX_DESCRIPTIONS:
            issues.append(self._issue(
                severity="error",
                row_number=row_num,
                column="Descriptions",
                issue_type="too_many_descriptions",
                message=f'Asset group "{asset_group}" has {description_count} descriptions, max is {self.MAX_DESCRIPTIONS}',
            ))

        if video_count > self.MAX_VIDEOS:
            issues.append(self._issue(
                severity="error",
                row_number=row_num,
                column="Videos",
                issue_type="too_many_videos",
                message=f'Asset group "{asset_group}" has {video_count} videos, max is {self.MAX_VIDEOS}',
            ))

        return issues

    def _validate_urls(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        for column in ("Final URL", "Final mobile URL"):
            url = row.get(column, "").strip()
            if url and not self._URL_PATTERN.match(url):
                issues.append(self._issue(
                    severity="error",
                    row_number=row_num,
                    column=column,
                    issue_type="invalid_url_format",
                    message=f"Invalid URL format in {column}",
                ))
        return issues

    def _count_numbered_columns(self, row: Dict[str, str], prefix: str, limit: int) -> int:
        return sum(1 for index in range(1, limit + 1) if row.get(f"{prefix} {index}", "").strip())

    def _issue(
        self,
        severity: str,
        row_number: int,
        column: str,
        issue_type: str,
        message: str,
    ) -> Dict[str, Any]:
        return {
            "level": "asset_group",
            "severity": severity,
            "row_number": row_number,
            "column": column,
            "issue_type": issue_type,
            "message": message,
            "auto_fixable": False,
        }
