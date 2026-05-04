#!/usr/bin/env python3
"""Validate Search keyword rows for the active Google Ads Agent workflow."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from shared.rebuild.match_type_policy import evaluate_match_type

VALID_KEYWORD_STATUSES = {"Enabled", "Paused", "Removed"}
MAX_KEYWORD_LENGTH = 80
MAX_POSITIVE_KEYWORDS_PER_AD_GROUP = 20_000
MAX_NEGATIVE_KEYWORDS_PER_AD_GROUP = 5_000


@dataclass
class ValidationIssue:
    """Represents a validation issue found during Search keyword validation."""

    level: str
    severity: str
    row_number: int
    column: str
    issue_type: str
    message: str
    suggestion: str = ""
    auto_fixable: bool = False


class SearchKeywordValidator:
    """
    Validates Search keyword rows for the current Google Ads Editor staging format.

    Current agent rules:
    - Keyword text stays plain in the Keyword column.
    - Match type belongs in Criterion Type.
    - New positive keywords use Phrase by default.
    - Campaign-level or ad-group-level new negatives use Negative Phrase.
    - Source-proven existing Exact can be preserved in revision and optimization modes.
    - Broad is blocked in every mode.
    """

    def __init__(self, validation_rules: dict[str, Any] | None = None):
        """Initialize SearchKeywordValidator with optional rule overrides."""
        rules = validation_rules or {}
        self.match_type_mode = str(rules.get("match_type_mode", "new_rebuild"))
        self.keyword_origin_map = dict(rules.get("keyword_origin_map", {}))
        self.valid_keyword_statuses = set(rules.get("valid_keyword_statuses", VALID_KEYWORD_STATUSES))
        self.max_keyword_length = int(rules.get("max_keyword_length", MAX_KEYWORD_LENGTH))
        self.max_positive_keywords_per_ad_group = int(
            rules.get("max_positive_keywords_per_ad_group", MAX_POSITIVE_KEYWORDS_PER_AD_GROUP)
        )
        self.max_negative_keywords_per_ad_group = int(
            rules.get("max_negative_keywords_per_ad_group", MAX_NEGATIVE_KEYWORDS_PER_AD_GROUP)
        )

    def _issue(
        self,
        severity: str,
        row_number: int,
        column: str,
        issue_type: str,
        message: str,
        suggestion: str = "",
        auto_fixable: bool = False,
    ) -> ValidationIssue:
        return ValidationIssue(
            level="keyword",
            severity=severity,
            row_number=row_number,
            column=column,
            issue_type=issue_type,
            message=message,
            suggestion=suggestion,
            auto_fixable=auto_fixable,
        )

    def _ad_group_value(self, row: dict[str, Any]) -> str:
        """Support both the active Ad Group header and older Ad group casing."""
        return str(row.get("Ad Group") or row.get("Ad group") or "").strip()

    def validate_keyword_row(self, row: dict[str, Any], row_number: int) -> list[ValidationIssue]:
        """
        Validate a single keyword row for Search campaign compliance.

        Args:
            row: Dictionary representing a CSV row.
            row_number: Row number in the CSV for error reporting.

        Returns:
            List of validation issues found.
        """
        issues: list[ValidationIssue] = []

        keyword = str(row.get("Keyword", "") or "").strip()
        criterion_type = str(row.get("Criterion Type", "") or "").strip()
        campaign = str(row.get("Campaign", "") or "").strip()
        ad_group = self._ad_group_value(row)

        if not keyword:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Keyword",
                    "missing_keyword",
                    "Keyword is required.",
                    "Provide plain keyword text.",
                )
            )
            return issues

        if not campaign:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Campaign",
                    "missing_campaign",
                    "Keyword row is missing Campaign.",
                    "Populate Campaign on every keyword row.",
                )
            )

        if not criterion_type:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Criterion Type",
                    "missing_criterion_type",
                    "Criterion Type is required.",
                    'Use "Phrase" or "Negative Phrase".',
                )
            )
        else:
            match_decision = evaluate_match_type(
                row,
                mode=self.match_type_mode,
                origin_map=self.keyword_origin_map,
            )
            severity = "critical" if match_decision.status == "error" else "warning"
            if match_decision.status != "pass":
                issues.append(
                    self._issue(
                        severity,
                        row_number,
                        "Criterion Type",
                        match_decision.rule,
                        match_decision.message,
                        'Use "Phrase" for new additions, or attach source proof for preserved existing Exact.',
                    )
                )

        if criterion_type and criterion_type not in {"Phrase", "Exact", "Negative Phrase", "Negative Exact", "Broad"}:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Criterion Type",
                    "unsupported_criterion_type",
                    f'Criterion Type "{criterion_type}" is not supported by the current workflow.',
                    'Use "Phrase" for new positives or "Negative Phrase" for new negatives.',
                )
            )

        if not criterion_type.startswith("Negative") and not ad_group:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Ad Group",
                    "missing_ad_group",
                    "Positive keyword row is missing Ad Group.",
                    "Populate Ad Group for every positive keyword row.",
                )
            )

        if keyword.startswith('"') or keyword.endswith('"') or keyword.startswith("[") or keyword.endswith("]"):
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Keyword",
                    "plain_keyword_text",
                    "Keyword must be plain text. Match type belongs in Criterion Type.",
                    "Remove quotes or brackets from Keyword and set Criterion Type instead.",
                    auto_fixable=True,
                )
            )

        if keyword.startswith("-"):
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Keyword",
                    "negative_keyword_format",
                    "Negative keyword rows should use Criterion Type instead of a leading minus.",
                    'Remove the leading minus and set Criterion Type to "Negative Phrase".',
                    auto_fixable=True,
                )
            )

        if len(keyword) > self.max_keyword_length:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Keyword",
                    "keyword_too_long",
                    f'Keyword "{keyword}" is {len(keyword)} characters. Maximum is {self.max_keyword_length}.',
                    "Shorten keyword text before importing to Google Ads Editor.",
                )
            )

        keyword_status = str(row.get("Keyword status") or row.get("Status") or "").strip()
        if keyword_status and keyword_status not in self.valid_keyword_statuses:
            issues.append(
                self._issue(
                    "warning",
                    row_number,
                    "Status",
                    "invalid_keyword_status",
                    f'Keyword status "{keyword_status}" is not standard.',
                    f"Use one of: {', '.join(sorted(self.valid_keyword_statuses))}.",
                )
            )

        return issues

    def validate_keyword_data(self, keyword_rows: list[dict[str, Any]]) -> list[ValidationIssue]:
        """
        Validate keyword-level data across multiple rows.

        Args:
            keyword_rows: List of keyword row dictionaries.

        Returns:
            List of validation issues found.
        """
        issues: list[ValidationIssue] = []

        if not keyword_rows:
            return issues

        keywords_by_adgroup: dict[str, dict[str, list[str]]] = defaultdict(
            lambda: {"positive": [], "negative": []}
        )
        keyword_counts: Counter[str] = Counter()

        for index, row in enumerate(keyword_rows, start=2):
            issues.extend(self.validate_keyword_row(row, index))

            keyword = str(row.get("Keyword", "") or "").strip()
            if not keyword:
                continue

            criterion_type = str(row.get("Criterion Type", "") or "").strip()
            ad_group = self._ad_group_value(row) or "(campaign-level negative)"

            if criterion_type.startswith("Negative"):
                keywords_by_adgroup[ad_group]["negative"].append(keyword)
            else:
                keywords_by_adgroup[ad_group]["positive"].append(keyword)

            if criterion_type:
                keyword_counts[criterion_type] += 1

        for ad_group, keywords in sorted(keywords_by_adgroup.items()):
            positive_count = len(keywords["positive"])
            negative_count = len(keywords["negative"])

            if ad_group != "(campaign-level negative)" and positive_count == 0:
                issues.append(
                    self._issue(
                        "critical",
                        0,
                        "Keyword",
                        "no_positive_keywords",
                        f'Ad group "{ad_group}" has no positive keywords to target.',
                        "Add phrase keywords before activating the ad group.",
                    )
                )

            if positive_count > self.max_positive_keywords_per_ad_group:
                issues.append(
                    self._issue(
                        "warning",
                        0,
                        "Keyword",
                        "too_many_keywords",
                        f'Ad group "{ad_group}" has {positive_count} positive keywords.',
                        "Split oversized keyword sets into tighter ad groups.",
                    )
                )

            if negative_count > self.max_negative_keywords_per_ad_group:
                issues.append(
                    self._issue(
                        "warning",
                        0,
                        "Keyword",
                        "too_many_negative_keywords",
                        f'Ad group "{ad_group}" has {negative_count} negative keywords.',
                        "Review and consolidate negative keywords.",
                    )
                )

        if keyword_counts and self.match_type_mode == "new_rebuild" and keyword_counts["Phrase"] == 0:
            issues.append(
                self._issue(
                    "critical",
                    0,
                    "Criterion Type",
                    "no_phrase_keywords",
                    "No active phrase keyword rows were found.",
                    'Add positive keyword rows with Criterion Type "Phrase".',
                )
            )
        elif keyword_counts and self.match_type_mode != "new_rebuild" and not (keyword_counts["Phrase"] or keyword_counts["Exact"]):
            issues.append(
                self._issue(
                    "critical",
                    0,
                    "Criterion Type",
                    "no_positive_keywords",
                    "No positive keyword rows were found.",
                    'Preserve source-proven Exact or add Phrase keyword rows before activating the ad group.',
                )
            )

        return issues
