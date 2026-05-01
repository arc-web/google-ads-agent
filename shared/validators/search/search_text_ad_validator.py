#!/usr/bin/env python3
"""Validate Search responsive search ad rows for the active workflow."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any


HEADLINE_LIMIT = 30
HEADLINE_MINIMUM = 25
DESCRIPTION_LIMIT = 90
PATH_LIMIT = 15
REQUIRED_RSA_HEADLINES = [f"Headline {index}" for index in range(1, 16)]
REQUIRED_RSA_DESCRIPTIONS = [f"Description {index}" for index in range(1, 5)]
VALID_AD_TYPES = {"Responsive search ad"}
VALID_STATUSES = {"Enabled", "Paused", "Removed"}
INVALID_TEXT_CHARS = {"\t", "\n", "\r"}
EXCESSIVE_PUNCTUATION = re.compile(r"[!?]{3,}|[.]{4,}|[,]{3,}")
REPEATED_WORDS = re.compile(r"\b(\w+)\s+\1\b", re.IGNORECASE)


@dataclass
class ValidationIssue:
    """Represents a validation issue found during Search ad validation."""

    level: str
    severity: str
    row_number: int
    column: str
    issue_type: str
    message: str
    suggestion: str = ""
    auto_fixable: bool = False


class SearchTextAdValidator:
    """
    Validates active Search Responsive Search Ad rows.

    This validator enforces generic Google Ads Editor staging structure only. It
    does not judge account strategy, vertical claims, tone, or service choices.
    """

    def __init__(self, validation_rules: dict[str, Any] | None = None):
        rules = validation_rules or {}
        self.headline_limit = int(rules.get("headline_limit", HEADLINE_LIMIT))
        self.headline_minimum = int(rules.get("headline_minimum", HEADLINE_MINIMUM))
        self.description_limit = int(rules.get("description_limit", DESCRIPTION_LIMIT))
        self.path_limit = int(rules.get("path_limit", PATH_LIMIT))
        self.required_headlines = list(rules.get("required_headlines", REQUIRED_RSA_HEADLINES))
        self.required_descriptions = list(rules.get("required_descriptions", REQUIRED_RSA_DESCRIPTIONS))
        self.valid_ad_types = set(rules.get("valid_ad_types", VALID_AD_TYPES))
        self.valid_statuses = set(rules.get("valid_statuses", VALID_STATUSES))

    def _issue(
        self,
        severity: str,
        row_number: int,
        column: str,
        issue_type: str,
        message: str,
        suggestion: str = "",
    ) -> ValidationIssue:
        return ValidationIssue(
            level="text_ad",
            severity=severity,
            row_number=row_number,
            column=column,
            issue_type=issue_type,
            message=message,
            suggestion=suggestion,
        )

    def _value(self, row: dict[str, Any], *headers: str) -> str:
        for header in headers:
            value = row.get(header)
            if value is not None and str(value).strip():
                return str(value).strip()
        return ""

    def _text_quality_issues(self, text: str, column: str, row_number: int) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        for character in INVALID_TEXT_CHARS:
            if character in text:
                issues.append(
                    self._issue(
                        "critical",
                        row_number,
                        column,
                        "invalid_text_character",
                        f"{column} contains a tab or line-break character.",
                        "Remove tabs and line breaks before importing.",
                    )
                )

        if EXCESSIVE_PUNCTUATION.search(text):
            issues.append(
                self._issue(
                    "warning",
                    row_number,
                    column,
                    "excessive_punctuation",
                    f"{column} contains excessive punctuation.",
                    "Use normal punctuation in ad copy.",
                )
            )

        if REPEATED_WORDS.search(text):
            issues.append(
                self._issue(
                    "warning",
                    row_number,
                    column,
                    "repeated_words",
                    f"{column} contains repeated words.",
                    "Remove repeated words unless intentional.",
                )
            )

        return issues

    def validate_text_ad_row(self, row: dict[str, Any], row_number: int) -> list[ValidationIssue]:
        """
        Validate a single Search RSA row.

        Args:
            row: Dictionary representing a CSV row.
            row_number: Row number in the CSV for error reporting.

        Returns:
            List of validation issues found.
        """
        issues: list[ValidationIssue] = []

        campaign = self._value(row, "Campaign")
        ad_group = self._value(row, "Ad Group", "Ad group")
        ad_type = self._value(row, "Ad type", "Ad Type")
        final_url = self._value(row, "Final URL")
        status = self._value(row, "Status", "Ad status", "Ad Status")

        if not campaign:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Campaign",
                    "missing_campaign",
                    "RSA row is missing Campaign.",
                    "Populate Campaign on every RSA row.",
                )
            )

        if not ad_group:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Ad Group",
                    "missing_ad_group",
                    "RSA row is missing Ad Group.",
                    "Populate Ad Group on every RSA row.",
                )
            )

        if not ad_type:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Ad type",
                    "missing_ad_type",
                    "RSA row is missing Ad type.",
                    'Set Ad type to "Responsive search ad".',
                )
            )
        elif ad_type not in self.valid_ad_types:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Ad type",
                    "invalid_ad_type",
                    f'Ad type "{ad_type}" is not active in the current workflow.',
                    'Use "Responsive search ad".',
                )
            )

        if not final_url:
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Final URL",
                    "missing_final_url",
                    "RSA row is missing Final URL.",
                    "Populate a reviewable landing page URL.",
                )
            )
        elif not final_url.startswith(("http://", "https://")):
            issues.append(
                self._issue(
                    "critical",
                    row_number,
                    "Final URL",
                    "invalid_final_url",
                    f'Final URL "{final_url}" must start with http:// or https://.',
                    "Use an absolute URL.",
                )
            )

        if status and status not in self.valid_statuses:
            issues.append(
                self._issue(
                    "warning",
                    row_number,
                    "Status",
                    "invalid_ad_status",
                    f'Ad status "{status}" is not standard.',
                    f"Use one of: {', '.join(sorted(self.valid_statuses))}.",
                )
            )

        issues.extend(self._validate_headlines(row, row_number))
        issues.extend(self._validate_descriptions(row, row_number))
        issues.extend(self._validate_paths(row, row_number))

        return issues

    def _validate_headlines(self, row: dict[str, Any], row_number: int) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        for headline in self.required_headlines:
            text = self._value(row, headline)
            if not text:
                issues.append(
                    self._issue(
                        "critical",
                        row_number,
                        headline,
                        "rsa_headline_required",
                        f"RSA row is missing {headline}.",
                        "Provide 15 headlines when possible.",
                    )
                )
                continue

            if len(text) > self.headline_limit:
                issues.append(
                    self._issue(
                        "critical",
                        row_number,
                        headline,
                        "headline_too_long",
                        f"{headline} is {len(text)} characters. Maximum is {self.headline_limit}.",
                        f"Shorten {headline} to {self.headline_limit} characters or fewer.",
                    )
                )
            elif len(text) < self.headline_minimum:
                issues.append(
                    self._issue(
                        "critical",
                        row_number,
                        headline,
                        "headline_minimum_value",
                        f"{headline} is {len(text)} characters. Minimum is {self.headline_minimum} for current quality rules.",
                        f"Rewrite {headline} with concrete value, specificity, action, proof, or a clear next step.",
                    )
                )

            issues.extend(self._text_quality_issues(text, headline, row_number))

        return issues

    def _validate_descriptions(self, row: dict[str, Any], row_number: int) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        for description in self.required_descriptions:
            text = self._value(row, description)
            if not text:
                issues.append(
                    self._issue(
                        "critical",
                        row_number,
                        description,
                        "rsa_description_required",
                        f"RSA row is missing {description}.",
                        "Provide 4 descriptions when possible.",
                    )
                )
                continue

            if len(text) > self.description_limit:
                issues.append(
                    self._issue(
                        "critical",
                        row_number,
                        description,
                        "description_too_long",
                        f"{description} is {len(text)} characters. Maximum is {self.description_limit}.",
                        f"Shorten {description} to {self.description_limit} characters or fewer.",
                    )
                )

            issues.extend(self._text_quality_issues(text, description, row_number))

        return issues

    def _validate_paths(self, row: dict[str, Any], row_number: int) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        for path_column in ("Path 1", "Path 2", "Display path 1", "Display path 2"):
            path = self._value(row, path_column)
            if not path:
                continue

            if len(path) > self.path_limit:
                issues.append(
                    self._issue(
                        "critical",
                        row_number,
                        path_column,
                        "path_too_long",
                        f"{path_column} is {len(path)} characters. Maximum is {self.path_limit}.",
                        f"Shorten {path_column} to {self.path_limit} characters or fewer.",
                    )
                )

            if any(character in path for character in ("/", "\\", "?", "#", "&")):
                issues.append(
                    self._issue(
                        "critical",
                        row_number,
                        path_column,
                        "invalid_path_chars",
                        f"{path_column} contains invalid path characters.",
                        "Use letters, numbers, spaces, or hyphens.",
                    )
                )

        return issues

    def validate_text_ad_data(self, text_ad_rows: list[dict[str, Any]]) -> list[ValidationIssue]:
        """
        Validate text ad-level data across multiple rows.

        Args:
            text_ad_rows: List of text ad row dictionaries.

        Returns:
            List of validation issues found.
        """
        issues: list[ValidationIssue] = []

        if not text_ad_rows:
            return issues

        headline_counter: Counter[str] = Counter()

        for index, row in enumerate(text_ad_rows, start=2):
            issues.extend(self.validate_text_ad_row(row, index))
            for headline in self.required_headlines:
                text = self._value(row, headline)
                if text:
                    headline_counter[text] += 1

        duplicates = sorted(headline for headline, count in headline_counter.items() if count > 1)
        if duplicates:
            issues.append(
                self._issue(
                    "info",
                    0,
                    "Headline",
                    "duplicate_headlines",
                    f"Found {len(duplicates)} duplicate RSA headlines across rows.",
                    "Use distinct headline assets when possible.",
                )
            )

        return issues
