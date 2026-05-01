#!/usr/bin/env python3
"""Orchestrate Search CSV validation for the active Google Ads Agent workflow."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from shared.rebuild.staging_validator import read_tsv, validate_rows

from .search_adgroup_validator import SearchAdGroupValidator
from .search_bid_strategy_validator import SearchBidStrategyValidator
from .search_budget_validator import SearchBudgetValidator
from .search_keyword_validator import SearchKeywordValidator
from .search_location_validator import SearchLocationValidator
from .search_schedule_validator import SearchScheduleValidator
from .search_text_ad_validator import SearchTextAdValidator


@dataclass
class ValidationIssue:
    """Issue shape used by the Search master validator."""

    level: str
    severity: str
    row_number: int
    column: str
    issue_type: str
    message: str
    suggestion: str = ""
    auto_fixable: bool = False


@dataclass
class ValidationReport:
    """Comprehensive validation report for Search campaigns."""

    csv_file: str
    total_issues: int
    critical_issues: int
    warning_issues: int
    info_issues: int
    issues_by_level: dict[str, int]
    validation_time: str
    success: bool


class SearchMasterValidator:
    """
    Master validator for Search campaign staging files.

    The active source of truth is the shared rebuild staging validator. Older
    component validators are still salvage material, so this class uses them
    only where they can add compatible row-level checks without overriding the
    active phrase-only staging rules.
    """

    def __init__(self, validation_rules: dict[str, Any] | None = None):
        self.validation_rules = validation_rules or self._get_default_rules()

        self.keyword_validator = SearchKeywordValidator(self.validation_rules)
        self.adgroup_validator = SearchAdGroupValidator(self.validation_rules)
        self.text_ad_validator = SearchTextAdValidator(self.validation_rules)
        self.location_validator = SearchLocationValidator(self.validation_rules)
        self.schedule_validator = SearchScheduleValidator(self.validation_rules)
        self.budget_validator = SearchBudgetValidator(self.validation_rules)
        self.bid_strategy_validator = SearchBidStrategyValidator(self.validation_rules)

        self.issues: list[ValidationIssue] = []
        self.fixed_issues: list[ValidationIssue] = []

    def _get_default_rules(self) -> dict[str, Any]:
        """Get default validation rules for Search campaigns."""
        return {
            "search_campaign": {
                "hierarchical_validation": True,
                "stop_on_critical": False,
                "aggregate_cross_level_issues": True,
            }
        }

    def validate_csv_file(self, csv_path: str) -> ValidationReport:
        """
        Validate a Search campaign CSV file hierarchically.

        Args:
            csv_path: Path to the CSV file to validate.

        Returns:
            Comprehensive validation report.
        """
        self.issues = []
        start_time = datetime.now()
        source = Path(csv_path)

        try:
            headers, rows, encoding = read_tsv(source)
        except Exception:
            try:
                headers, rows, encoding = self._read_csv(source)
            except Exception as exc:
                self.issues.append(
                    ValidationIssue(
                        level="file",
                        severity="critical",
                        row_number=0,
                        column="",
                        issue_type="file_read_error",
                        message=f"Failed to read CSV file: {exc}",
                        suggestion="Check file format, encoding, and permissions.",
                    )
                )
                return self._generate_report(csv_path, start_time)

        if not rows:
            self.issues.append(
                ValidationIssue(
                    level="file",
                    severity="critical",
                    row_number=0,
                    column="",
                    issue_type="empty_csv",
                    message="CSV file contains no data rows.",
                    suggestion="Ensure CSV has data rows after headers.",
                )
            )
            return self._generate_report(csv_path, start_time)

        active_report = validate_rows(headers, rows, source, encoding)
        self.issues.extend(self._issues_from_staging_report(active_report))

        grouped_data = self._group_rows_by_level(rows)
        self._validate_salvage_components(grouped_data)
        self.issues.extend(self._validate_cross_level_consistency(grouped_data))

        return self._generate_report(csv_path, start_time)

    def _read_csv(self, source: Path) -> tuple[list[str], list[dict[str, str]], str]:
        """Read comma-delimited CSV as a fallback for older exports."""
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = [{key: value or "" for key, value in row.items() if key is not None} for row in reader]
            return list(reader.fieldnames or []), rows, "utf-8-sig"

    def _issues_from_staging_report(self, report: dict[str, Any]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        severity_map = {"error": "critical", "warning": "warning", "info": "info"}

        for issue in report.get("issues", []):
            issues.append(
                ValidationIssue(
                    level="active_staging",
                    severity=severity_map.get(issue.get("severity", "warning"), "warning"),
                    row_number=issue.get("row") or 0,
                    column=issue.get("column") or "",
                    issue_type=issue.get("rule") or "staging_rule",
                    message=issue.get("message") or "Staging validation issue.",
                    suggestion="Follow the active Google Ads Editor staging rules.",
                    auto_fixable=False,
                )
            )

        return issues

    def _canonical_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """Add older header aliases so salvage validators can read active rows."""
        canonical = dict(row)
        if "Ad Group" in canonical and "Ad group" not in canonical:
            canonical["Ad group"] = canonical.get("Ad Group", "")
        if "Campaign Type" in canonical and "Campaign type" not in canonical:
            canonical["Campaign type"] = canonical.get("Campaign Type", "")
        if "Status" in canonical:
            canonical.setdefault("Ad group status", canonical.get("Status", ""))
            canonical.setdefault("Ad status", canonical.get("Status", ""))
            canonical.setdefault("Keyword status", canonical.get("Status", ""))
        if "Ad type" in canonical:
            canonical.setdefault("Ad Type", canonical.get("Ad type", ""))
        return canonical

    def _group_rows_by_level(self, rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Group CSV rows by validation level based on active Google Ads Editor columns."""
        grouped: dict[str, list[dict[str, Any]]] = {
            "adgroup": [],
            "keyword": [],
            "text_ad": [],
            "location": [],
            "schedule": [],
            "budget": [],
            "bid_strategy": [],
        }

        for raw_row in rows:
            row = self._canonical_row(raw_row)
            if self._is_adgroup_row(row):
                grouped["adgroup"].append(row)
            if self._is_keyword_row(row):
                grouped["keyword"].append(row)
            if self._is_text_ad_row(row):
                grouped["text_ad"].append(row)
            if self._is_location_row(row):
                grouped["location"].append(row)
            if self._is_schedule_row(row):
                grouped["schedule"].append(row)
            if self._is_budget_row(row):
                grouped["budget"].append(row)
            if self._is_bid_strategy_row(row):
                grouped["bid_strategy"].append(row)

        return grouped

    def _is_adgroup_row(self, row: dict[str, Any]) -> bool:
        return bool(row.get("Ad group")) and not row.get("Keyword") and not row.get("Ad type")

    def _is_keyword_row(self, row: dict[str, Any]) -> bool:
        return bool(row.get("Keyword"))

    def _is_text_ad_row(self, row: dict[str, Any]) -> bool:
        return bool(row.get("Ad type") or row.get("Headline 1") or row.get("Description 1"))

    def _is_location_row(self, row: dict[str, Any]) -> bool:
        return bool(row.get("Location"))

    def _is_schedule_row(self, row: dict[str, Any]) -> bool:
        return bool(row.get("Ad Schedule"))

    def _is_budget_row(self, row: dict[str, Any]) -> bool:
        return bool(row.get("Budget"))

    def _is_bid_strategy_row(self, row: dict[str, Any]) -> bool:
        return bool(row.get("Bid Strategy Type") or row.get("Max CPC"))

    def _validate_salvage_components(self, grouped_data: dict[str, list[dict[str, Any]]]) -> None:
        validators: dict[str, Callable[[list[dict[str, Any]]], list[Any]]] = {
            "keyword": self.keyword_validator.validate_keyword_data,
            "schedule": self.schedule_validator.validate_schedule_data,
            "budget": self.budget_validator.validate_budget_data,
            "bid_strategy": self.bid_strategy_validator.validate_bid_strategy_data,
        }

        for level, validator in validators.items():
            rows = grouped_data.get(level, [])
            if not rows:
                continue
            self.issues.extend(self._normalize_component_issues(validator(rows)))

    def _normalize_component_issues(self, issues: list[Any]) -> list[ValidationIssue]:
        normalized: list[ValidationIssue] = []

        for issue in issues:
            data = asdict(issue) if hasattr(issue, "__dataclass_fields__") else dict(getattr(issue, "__dict__", {}))
            severity = data.get("severity", "warning")
            if hasattr(severity, "value"):
                severity = severity.value
            level = data.get("level", "component")
            if hasattr(level, "value"):
                level = level.value

            normalized.append(
                ValidationIssue(
                    level=str(level),
                    severity=str(severity),
                    row_number=int(data.get("row_number") or 0),
                    column=str(data.get("column") or ""),
                    issue_type=str(data.get("issue_type") or "component_rule"),
                    message=str(data.get("message") or "Component validation issue."),
                    suggestion=str(data.get("suggestion") or ""),
                    auto_fixable=bool(data.get("auto_fixable", False)),
                )
            )

        return normalized

    def _validate_cross_level_consistency(
        self, grouped_data: dict[str, list[dict[str, Any]]]
    ) -> list[ValidationIssue]:
        """Validate consistency across active row levels."""
        issues: list[ValidationIssue] = []
        adgroups_by_campaign: dict[str, set[str]] = defaultdict(set)
        keyword_adgroups_by_campaign: dict[str, set[str]] = defaultdict(set)

        for row in grouped_data.get("adgroup", []):
            campaign = str(row.get("Campaign", "") or "").strip()
            adgroup = str(row.get("Ad group", "") or "").strip()
            if campaign and adgroup:
                adgroups_by_campaign[campaign].add(adgroup)

        for row in grouped_data.get("keyword", []):
            campaign = str(row.get("Campaign", "") or "").strip()
            adgroup = str(row.get("Ad group", "") or "").strip()
            criterion_type = str(row.get("Criterion Type", "") or "").strip()
            if campaign and adgroup and criterion_type != "Negative Phrase":
                keyword_adgroups_by_campaign[campaign].add(adgroup)

        for campaign, keyword_adgroups in sorted(keyword_adgroups_by_campaign.items()):
            missing = keyword_adgroups - adgroups_by_campaign.get(campaign, set())
            if missing:
                issues.append(
                    ValidationIssue(
                        level="cross_level",
                        severity="warning",
                        row_number=0,
                        column="Ad Group",
                        issue_type="orphan_keywords",
                        message=(
                            f'Keywords reference ad groups not defined in campaign "{campaign}": '
                            f"{', '.join(sorted(missing))}"
                        ),
                        suggestion="Add matching ad group rows or correct the keyword Ad Group values.",
                    )
                )

        return issues

    def _generate_report(self, csv_path: str, start_time: datetime) -> ValidationReport:
        """Generate comprehensive validation report."""
        validation_time = f"{(datetime.now() - start_time).total_seconds():.2f}s"

        severity_counts = Counter(issue.severity for issue in self.issues)
        issues_by_level = Counter(issue.level for issue in self.issues)

        return ValidationReport(
            csv_file=csv_path,
            total_issues=len(self.issues),
            critical_issues=severity_counts["critical"],
            warning_issues=severity_counts["warning"],
            info_issues=severity_counts["info"],
            issues_by_level=dict(issues_by_level),
            validation_time=validation_time,
            success=severity_counts["critical"] == 0,
        )

    def get_detailed_issues(self) -> list[dict[str, Any]]:
        """Get detailed issue information for reporting."""
        return [asdict(issue) for issue in self.issues]
