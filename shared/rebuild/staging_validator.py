#!/usr/bin/env python3
"""Validate Google Ads Editor staging CSVs for the active rebuild workflow."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ENCODINGS = ("utf-16", "utf-8-sig", "utf-8", "latin-1")
HEADLINE_LIMIT = 30
HEADLINE_MINIMUM = 25
DESCRIPTION_LIMIT = 90
PATH_LIMIT = 15

REQUIRED_HEADERS = [
    "Campaign",
    "Campaign Type",
    "Networks",
    "Budget",
    "Budget type",
    "EU political ads",
    "Broad match keywords",
    "Ad Group",
    "Criterion Type",
    "Keyword",
    "Final URL",
    "Location",
    "Location ID",
    "Ad type",
    "Status",
]

REQUIRED_RSA_HEADLINES = [f"Headline {index}" for index in range(1, 16)]
REQUIRED_RSA_DESCRIPTIONS = [f"Description {index}" for index in range(1, 5)]
ALLOWED_KEYWORD_TYPES = {"Phrase", "Negative Phrase"}
DISALLOWED_KEYWORD_TYPES = {"Broad", "Exact"}
SEARCH_NETWORK_VALUE = "Google search"
OFF_VALUES = {"Off", "Disabled", "No", "False", "0"}


@dataclass
class ValidationIssue:
    severity: str
    message: str
    row: int | None = None
    column: str | None = None
    value: str | None = None
    rule: str | None = None


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]], str]:
    """Read a Google Ads Editor tab-separated file with common export encodings."""
    last_error: Exception | None = None
    for encoding in ENCODINGS:
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle, delimiter="\t")
                rows = [{key: value or "" for key, value in row.items() if key is not None} for row in reader]
                headers = list(reader.fieldnames or [])
                if headers:
                    return headers, rows, encoding
        except UnicodeError as exc:
            last_error = exc
            continue

    if last_error:
        raise last_error
    raise ValueError(f"Could not read CSV headers from {path}")


def add_issue(
    issues: list[ValidationIssue],
    severity: str,
    message: str,
    row: int | None = None,
    column: str | None = None,
    value: str | None = None,
    rule: str | None = None,
) -> None:
    issues.append(
        ValidationIssue(
            severity=severity,
            message=message,
            row=row,
            column=column,
            value=value,
            rule=rule,
        )
    )


def has_any(row: dict[str, str], fields: list[str]) -> bool:
    return any(row.get(field, "").strip() for field in fields)


def is_rsa_row(row: dict[str, str]) -> bool:
    return row.get("Ad type", "").strip().lower() == "responsive search ad"


def is_keyword_row(row: dict[str, str]) -> bool:
    return bool(row.get("Keyword", "").strip())


def is_ad_group_row(row: dict[str, str]) -> bool:
    return bool(row.get("Ad Group", "").strip()) and not is_keyword_row(row) and not is_rsa_row(row)


def is_location_row(row: dict[str, str]) -> bool:
    return bool(row.get("Location", "").strip())


def validate_headers(headers: list[str], issues: list[ValidationIssue]) -> None:
    header_set = set(headers)
    for header in REQUIRED_HEADERS:
        if header not in header_set:
            add_issue(
                issues,
                "error",
                f"Missing required Google Ads Editor staging column: {header}",
                column=header,
                rule="required_header",
            )

    for header in REQUIRED_RSA_HEADLINES + REQUIRED_RSA_DESCRIPTIONS:
        if header not in header_set:
            add_issue(
                issues,
                "error",
                f"Missing required RSA column: {header}",
                column=header,
                rule="required_rsa_header",
            )


def validate_campaign_row(row: dict[str, str], row_number: int, issues: list[ValidationIssue]) -> None:
    campaign_type = row.get("Campaign Type", "").strip()
    if campaign_type != "Search":
        return

    networks = row.get("Networks", "").strip()
    if networks != SEARCH_NETWORK_VALUE:
        add_issue(
            issues,
            "error",
            "Search campaign row must use Google search only. Search partners are disabled 100 percent of the time.",
            row=row_number,
            column="Networks",
            value=networks,
            rule="search_partners_disabled",
        )

    budget = row.get("Budget", "").strip()
    if budget:
        try:
            if float(budget.replace(",", "")) <= 0:
                add_issue(
                    issues,
                    "error",
                    "Campaign budget must be greater than zero.",
                    row=row_number,
                    column="Budget",
                    value=budget,
                    rule="budget_positive",
                )
        except ValueError:
            add_issue(
                issues,
                "error",
                "Campaign budget is not numeric.",
                row=row_number,
                column="Budget",
                value=budget,
                rule="budget_numeric",
            )

    if not row.get("EU political ads", "").strip():
        add_issue(
            issues,
            "error",
            "Campaign row must populate EU political ads.",
            row=row_number,
            column="EU political ads",
            rule="eu_political_ads_required",
        )

    broad_match = row.get("Broad match keywords", "").strip()
    if broad_match and broad_match not in OFF_VALUES:
        add_issue(
            issues,
            "error",
            "Broad match keywords must be off for the current phrase-only workflow.",
            row=row_number,
            column="Broad match keywords",
            value=broad_match,
            rule="broad_match_off",
        )


def validate_keyword_row(
    row: dict[str, str],
    row_number: int,
    issues: list[ValidationIssue],
    keyword_counts: Counter[str],
) -> None:
    keyword = row.get("Keyword", "").strip()
    criterion_type = row.get("Criterion Type", "").strip()

    if not keyword:
        return

    if not row.get("Campaign", "").strip():
        add_issue(
            issues,
            "error",
            "Keyword row is missing Campaign.",
            row=row_number,
            column="Campaign",
            rule="keyword_campaign_required",
        )

    if criterion_type != "Negative Phrase" and not row.get("Ad Group", "").strip():
        add_issue(
            issues,
            "error",
            "Keyword row is missing Ad Group.",
            row=row_number,
            column="Ad Group",
            rule="keyword_ad_group_required",
        )

    if not criterion_type:
        add_issue(
            issues,
            "error",
            "Keyword row is missing Criterion Type.",
            row=row_number,
            column="Criterion Type",
            rule="criterion_type_required",
        )
    elif criterion_type in DISALLOWED_KEYWORD_TYPES:
        add_issue(
            issues,
            "error",
            "Broad and exact keyword match types are not active in the current workflow.",
            row=row_number,
            column="Criterion Type",
            value=criterion_type,
            rule="disallowed_match_type",
        )
    elif criterion_type not in ALLOWED_KEYWORD_TYPES:
        add_issue(
            issues,
            "error",
            "Keyword row has unsupported Criterion Type.",
            row=row_number,
            column="Criterion Type",
            value=criterion_type,
            rule="unsupported_criterion_type",
        )

    if keyword.startswith('"') or keyword.endswith('"') or keyword.startswith("[") or keyword.endswith("]"):
        add_issue(
            issues,
            "error",
            "Keyword must be plain text. Match type belongs in Criterion Type.",
            row=row_number,
            column="Keyword",
            value=keyword,
            rule="plain_keyword_text",
        )

    if keyword.startswith("-"):
        add_issue(
            issues,
            "error",
            "Negative keyword rows should use Criterion Type instead of a leading minus.",
            row=row_number,
            column="Keyword",
            value=keyword,
            rule="negative_keyword_format",
        )

    if len(keyword) > 80:
        add_issue(
            issues,
            "error",
            "Keyword exceeds the 80 character limit.",
            row=row_number,
            column="Keyword",
            value=keyword,
            rule="keyword_length",
        )

    if criterion_type:
        keyword_counts[criterion_type] += 1


def validate_rsa_row(row: dict[str, str], row_number: int, issues: list[ValidationIssue]) -> None:
    if not is_rsa_row(row):
        return

    if not row.get("Campaign", "").strip():
        add_issue(issues, "error", "RSA row is missing Campaign.", row=row_number, column="Campaign", rule="rsa_campaign_required")

    if not row.get("Ad Group", "").strip():
        add_issue(issues, "error", "RSA row is missing Ad Group.", row=row_number, column="Ad Group", rule="rsa_ad_group_required")

    if not row.get("Final URL", "").strip():
        add_issue(issues, "error", "RSA row is missing Final URL.", row=row_number, column="Final URL", rule="rsa_final_url_required")

    for headline in REQUIRED_RSA_HEADLINES:
        value = row.get(headline, "").strip()
        if not value:
            add_issue(issues, "error", f"RSA row is missing {headline}.", row=row_number, column=headline, rule="rsa_headline_required")
        elif len(value) > HEADLINE_LIMIT:
            add_issue(issues, "error", f"{headline} exceeds {HEADLINE_LIMIT} characters.", row=row_number, column=headline, value=value, rule="headline_length")
        elif len(value) < HEADLINE_MINIMUM:
            add_issue(
                issues,
                "error",
                f"{headline} is too short for current RSA quality rules. Use at least {HEADLINE_MINIMUM} characters with concrete value.",
                row=row_number,
                column=headline,
                value=value,
                rule="headline_minimum_value",
            )

    for description in REQUIRED_RSA_DESCRIPTIONS:
        value = row.get(description, "").strip()
        if not value:
            add_issue(issues, "error", f"RSA row is missing {description}.", row=row_number, column=description, rule="rsa_description_required")
        elif len(value) > DESCRIPTION_LIMIT:
            add_issue(issues, "error", f"{description} exceeds {DESCRIPTION_LIMIT} characters.", row=row_number, column=description, value=value, rule="description_length")

    for path_field in ("Path 1", "Path 2"):
        value = row.get(path_field, "").strip()
        if value and len(value) > PATH_LIMIT:
            add_issue(issues, "error", f"{path_field} exceeds {PATH_LIMIT} characters.", row=row_number, column=path_field, value=value, rule="path_length")


def validate_location_row(row: dict[str, str], row_number: int, issues: list[ValidationIssue]) -> None:
    if not is_location_row(row):
        return

    if row.get("Radius", "").strip():
        radius = row.get("Radius", "").strip()
        try:
            if float(radius) <= 0:
                add_issue(issues, "error", "Radius must be greater than zero.", row=row_number, column="Radius", value=radius, rule="radius_positive")
        except ValueError:
            add_issue(issues, "error", "Radius is not numeric.", row=row_number, column="Radius", value=radius, rule="radius_numeric")
        return

    if not row.get("Location ID", "").strip():
        add_issue(
            issues,
            "warning",
            "Location row is missing Location ID. Current process prefers Location ID when available.",
            row=row_number,
            column="Location ID",
            value=row.get("Location", "").strip(),
            rule="location_id_preferred",
        )


def validate_rows(headers: list[str], rows: list[dict[str, str]], source: Path, encoding: str) -> dict[str, Any]:
    issues: list[ValidationIssue] = []
    counts: Counter[str] = Counter()
    campaigns: Counter[str] = Counter()
    ad_groups_by_campaign: dict[str, set[str]] = defaultdict(set)
    keyword_counts: Counter[str] = Counter()

    validate_headers(headers, issues)

    for row_number, row in enumerate(rows, start=2):
        campaign = row.get("Campaign", "").strip()
        if campaign:
            campaigns[campaign] += 1

        if row.get("Campaign Type", "").strip() == "Search":
            counts["campaign_rows"] += 1
            validate_campaign_row(row, row_number, issues)

        if is_ad_group_row(row):
            counts["ad_group_rows"] += 1
            ad_group = row.get("Ad Group", "").strip()
            if campaign and ad_group:
                ad_groups_by_campaign[campaign].add(ad_group)

        if is_keyword_row(row):
            if row.get("Criterion Type", "").strip() == "Negative Phrase":
                counts["negative_keyword_rows"] += 1
            else:
                counts["keyword_rows"] += 1
            validate_keyword_row(row, row_number, issues, keyword_counts)

        if is_rsa_row(row):
            counts["rsa_rows"] += 1
            validate_rsa_row(row, row_number, issues)

        if is_location_row(row):
            if row.get("Radius", "").strip():
                counts["radius_rows"] += 1
            else:
                counts["location_rows"] += 1
            validate_location_row(row, row_number, issues)

        if row.get("Bid Modifier", "").strip():
            counts["bid_modifier_rows"] += 1

    for campaign, ad_groups in sorted(ad_groups_by_campaign.items()):
        if not ad_groups:
            add_issue(
                issues,
                "warning",
                "Campaign has no detected ad group rows.",
                column="Ad Group",
                value=campaign,
                rule="campaign_ad_groups_present",
            )

    if counts["campaign_rows"] == 0:
        add_issue(issues, "error", "No Search campaign rows were found.", rule="campaign_rows_present")

    if counts["keyword_rows"] == 0:
        add_issue(issues, "error", "No phrase keyword rows were found.", rule="keyword_rows_present")

    if counts["rsa_rows"] == 0:
        add_issue(issues, "error", "No responsive search ad rows were found.", rule="rsa_rows_present")

    if counts["location_rows"] == 0 and counts["radius_rows"] == 0:
        add_issue(issues, "error", "No location or radius targeting rows were found.", rule="location_rows_present")

    issue_counts = Counter(issue.severity for issue in issues)
    status = "pass" if issue_counts["error"] == 0 else "fail"

    return {
        "status": status,
        "source_csv": str(source),
        "encoding": encoding,
        "rows": len(rows),
        "headers": len(headers),
        "campaigns": sorted(campaigns),
        "ad_groups": sum(len(groups) for groups in ad_groups_by_campaign.values()),
        "counts": dict(counts),
        "keyword_criterion_types": dict(keyword_counts),
        "issue_counts": dict(issue_counts),
        "issues": [asdict(issue) for issue in issues],
    }


def validate_file(path: Path) -> dict[str, Any]:
    headers, rows, encoding = read_tsv(path)
    return validate_rows(headers, rows, path, encoding)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate active Google Ads Editor staging CSV output.")
    parser.add_argument("--csv", required=True, help="Path to a Google Ads Editor staging CSV or TSV file.")
    parser.add_argument("--json-output", help="Optional path to write validation JSON.")
    args = parser.parse_args()

    report = validate_file(Path(args.csv))
    output = json.dumps(report, indent=2)

    if args.json_output:
        Path(args.json_output).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)

    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
