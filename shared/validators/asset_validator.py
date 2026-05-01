#!/usr/bin/env python3
"""
Generic asset CSV validator.

This module treats PMAX and asset rows as salvage checks. It does not make
asset validation active for Search workflows unless asset-specific columns are
present in the row.
"""

import csv
import io
import re
from typing import Any, Dict, Iterable, List


class AssetValidator:
    """Validates asset fields without client-specific assumptions."""

    HEADLINE_MAX = 30
    LONG_HEADLINE_MAX = 90
    DESCRIPTION_MAX = 90
    CTA_MAX = 25

    _URL_PATTERN = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)
    _YOUTUBE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{11}$")

    def validate_assets(self, csv_path: str, csv_content: str) -> List[Dict[str, Any]]:
        """Validate asset-like rows in a CSV string."""
        del csv_path
        issues: List[Dict[str, Any]] = []

        try:
            for row_num, row in self._iter_rows(csv_content):
                if not self._is_asset_like_row(row):
                    continue

                issues.extend(self._validate_headlines(row, row_num))
                issues.extend(self._validate_descriptions(row, row_num))
                issues.extend(self._validate_long_headlines(row, row_num))
                issues.extend(self._validate_videos(row, row_num))
                issues.extend(self._validate_images(row, row_num))
                issues.extend(self._validate_call_to_action(row, row_num))
        except Exception as exc:
            issues.append(self._issue(
                severity="critical",
                row_number=0,
                column="",
                issue_type="validation_error",
                message=f"Failed to validate assets: {exc}",
            ))

        return issues

    def _iter_rows(self, csv_content: str) -> Iterable[tuple[int, Dict[str, str]]]:
        sample = csv_content[:2048]
        delimiter = "\t" if sample.count("\t") >= sample.count(",") else ","
        reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter)
        for row_num, row in enumerate(reader, 2):
            yield row_num, {str(key): value for key, value in row.items() if key is not None}

    def _is_asset_like_row(self, row: Dict[str, str]) -> bool:
        campaign_type = row.get("Campaign Type", "").strip().lower()
        if campaign_type == "performance max":
            return True

        asset_markers = {
            "Asset",
            "Asset Type",
            "Asset Group",
            "Long headline 1",
            "Video ID 1",
            "Image URL",
            "Call to action",
        }
        return any(row.get(column, "").strip() for column in asset_markers)

    def _validate_headlines(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        for index in range(1, 16):
            column = f"Headline {index}"
            headline = row.get(column, "").strip()
            if not headline:
                continue

            if len(headline) > self.HEADLINE_MAX:
                issues.append(self._issue(
                    severity="error",
                    row_number=row_num,
                    column=column,
                    issue_type="headline_too_long",
                    message=f"Headline {index} is {len(headline)} characters, max is {self.HEADLINE_MAX}",
                ))
            issues.extend(self._validate_csv_safe_text(headline, row_num, column, "headline"))
        return issues

    def _validate_descriptions(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        for index in range(1, 6):
            column = f"Description {index}"
            description = row.get(column, "").strip()
            if not description:
                continue

            if len(description) > self.DESCRIPTION_MAX:
                issues.append(self._issue(
                    severity="error",
                    row_number=row_num,
                    column=column,
                    issue_type="description_too_long",
                    message=f"Description {index} is {len(description)} characters, max is {self.DESCRIPTION_MAX}",
                ))
            issues.extend(self._validate_csv_safe_text(description, row_num, column, "description"))
        return issues

    def _validate_long_headlines(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        for index in range(1, 6):
            column = f"Long headline {index}"
            headline = row.get(column, "").strip()
            if headline and len(headline) > self.LONG_HEADLINE_MAX:
                issues.append(self._issue(
                    severity="error",
                    row_number=row_num,
                    column=column,
                    issue_type="long_headline_too_long",
                    message=f"Long headline {index} is {len(headline)} characters, max is {self.LONG_HEADLINE_MAX}",
                ))
        return issues

    def _validate_videos(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        for index in range(1, 6):
            column = f"Video ID {index}"
            video_id = row.get(column, "").strip()
            if not video_id:
                continue

            if not (self._YOUTUBE_ID_PATTERN.match(video_id) or self._URL_PATTERN.match(video_id)):
                issues.append(self._issue(
                    severity="error",
                    row_number=row_num,
                    column=column,
                    issue_type="invalid_video_id",
                    message=f"Video ID {index} must be an 11-character YouTube ID or URL",
                ))
        return issues

    def _validate_images(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        for column, value in row.items():
            if "image" not in column.lower() or "url" not in column.lower():
                continue
            image_url = value.strip()
            if image_url and not self._URL_PATTERN.match(image_url):
                issues.append(self._issue(
                    severity="error",
                    row_number=row_num,
                    column=column,
                    issue_type="invalid_image_url",
                    message=f"Invalid image URL format in {column}",
                ))
        return issues

    def _validate_call_to_action(self, row: Dict[str, str], row_num: int) -> List[Dict[str, Any]]:
        cta = row.get("Call to action", "").strip()
        if cta and len(cta) > self.CTA_MAX:
            return [self._issue(
                severity="warning",
                row_number=row_num,
                column="Call to action",
                issue_type="cta_too_long",
                message=f"Call to action is {len(cta)} characters, recommended max is {self.CTA_MAX}",
            )]
        return []

    def _validate_csv_safe_text(
        self,
        text: str,
        row_num: int,
        column: str,
        issue_prefix: str,
    ) -> List[Dict[str, Any]]:
        if "|" not in text and "\t" not in text:
            return []

        return [self._issue(
            severity="error",
            row_number=row_num,
            column=column,
            issue_type=f"{issue_prefix}_unsafe_separator",
            message=f"{column} contains a pipe or tab separator",
        )]

    def _issue(
        self,
        severity: str,
        row_number: int,
        column: str,
        issue_type: str,
        message: str,
    ) -> Dict[str, Any]:
        return {
            "level": "asset",
            "severity": severity,
            "row_number": row_number,
            "column": column,
            "issue_type": issue_type,
            "message": message,
            "auto_fixable": False,
        }
