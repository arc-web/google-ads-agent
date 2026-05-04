#!/usr/bin/env python3
"""Validate Google Ads Editor staging CSVs for the active rebuild workflow."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.rebuild.rsa_headline_quality import audit_rsa_headlines


ENCODINGS = ("utf-16", "utf-8-sig", "utf-8", "latin-1")
HEADLINE_LIMIT = 30
HEADLINE_MINIMUM = 25
DESCRIPTION_LIMIT = 90
DESCRIPTION_MINIMUM = 75
PATH_LIMIT = 15
SITELINK_TEXT_LIMIT = 25
SITELINK_DESCRIPTION_LIMIT = 35
CALLOUT_TEXT_LIMIT = 25
PRICE_TEXT_LIMIT = 25
PRICE_MIN_ITEMS = 3
PROMOTION_TARGET_LIMIT = 20
BUSINESS_NAME_LIMIT = 25
STRUCTURED_SNIPPET_VALUE_LIMIT = 25
STRUCTURED_SNIPPET_MIN_VALUES = 3
STRUCTURED_SNIPPET_MAX_VALUES = 10
APPROVED_STRUCTURED_SNIPPET_HEADERS = {
    "Amenities",
    "Brands",
    "Courses",
    "Degree programs",
    "Destinations",
    "Featured hotels",
    "Insurance coverage",
    "Models",
    "Neighborhoods",
    "Services",
    "Shows",
    "Styles",
    "Types",
}

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
DEFAULT_DESCRIPTION_CTAS = {
    "apply today",
    "book a consultation",
    "book a tasting menu",
    "book today",
    "book your reservation",
    "call today",
    "call us today",
    "check availability",
    "compare options",
    "confirm fit",
    "plan next steps",
    "request a quote",
    "request details",
    "reserve your table",
    "review program fit",
    "schedule a review",
    "schedule service",
    "schedule today",
}
DESCRIPTION_VALUE_TERMS = {
    "available",
    "availability",
    "budget",
    "care",
    "clear",
    "compare",
    "confirm",
    "consult",
    "details",
    "experienced",
    "fit",
    "focused",
    "guidance",
    "licensed",
    "local",
    "options",
    "planning",
    "practical",
    "private",
    "process",
    "review",
    "schedule",
    "support",
    "team",
}
GENERIC_DESCRIPTION_PHRASES = {
    "account import",
    "campaign approval",
    "implementation needs",
    "launch readiness",
    "service fit",
}
SMART_BIDDING_STRATEGIES = {
    "Maximize conversions",
    "Maximize conversion value",
    "Target CPA",
    "Target ROAS",
}
EARLY_STAGE_BID_STRATEGIES = {
    "Manual CPC",
    "Maximize clicks",
    "Maximize Clicks",
}


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


def is_sitelink_row(row: dict[str, str]) -> bool:
    return bool(row.get("Link text", "").strip() or row.get("Description line 1", "").strip() or row.get("Description line 2", "").strip())


def is_callout_row(row: dict[str, str]) -> bool:
    return bool(row.get("Callout text", "").strip())


def is_structured_snippet_row(row: dict[str, str]) -> bool:
    return bool(row.get("Structured snippet header", "").strip() or row.get("Structured snippet values", "").strip())


def is_call_asset_row(row: dict[str, str]) -> bool:
    return bool(row.get("Phone number", "").strip() or row.get("Country code", "").strip())


def is_price_row(row: dict[str, str]) -> bool:
    return bool(row.get("Price header", "").strip() or row.get("Price amount", "").strip())


def is_promotion_row(row: dict[str, str]) -> bool:
    return bool(row.get("Promotion target", "").strip() or row.get("Percent off", "").strip() or row.get("Money amount off", "").strip() or row.get("Promotion code", "").strip())


def is_business_name_row(row: dict[str, str]) -> bool:
    return bool(row.get("Business name", "").strip())


def is_asset_row(row: dict[str, str]) -> bool:
    return (
        is_sitelink_row(row)
        or is_callout_row(row)
        or is_structured_snippet_row(row)
        or is_call_asset_row(row)
        or is_price_row(row)
        or is_promotion_row(row)
        or is_business_name_row(row)
    )


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
    if "display" in networks.lower():
        add_issue(
            issues,
            "error",
            "Search campaign rows must not opt into the Display Network.",
            row=row_number,
            column="Networks",
            value=networks,
            rule="search_display_opt_in_blocked",
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

    bid_strategy = first_value(row, "Bid Strategy Type", "Bid strategy type", "Bid Strategy", "Bid strategy")
    conversions_30d = first_value(row, "Conversions last 30 days", "Conversions 30d", "Conversions")
    if bid_strategy:
        validate_bid_strategy_setting(bid_strategy, conversions_30d, row_number, issues)

    audience_mode = first_value(row, "Audience targeting setting", "Audience mode", "Targeting setting", "Targeting mode")
    if audience_mode and "target" in audience_mode.lower() and "remarketing" not in row.get("Campaign", "").lower():
        add_issue(
            issues,
            "warning",
            "Audience Targeting mode needs explicit strategy approval for standard acquisition Search campaigns.",
            row=row_number,
            column="Audience targeting setting",
            value=audience_mode,
            rule="audience_targeting_mode_review",
        )

    conversion_status = first_value(row, "Conversion tracking status", "Conversion Status")
    normalized_conversion_status = re.sub(r"[^a-z]+", " ", conversion_status.lower()).strip()
    ready_statuses = {"recording", "active", "verified"}
    if conversion_status and not (set(normalized_conversion_status.split()) & ready_statuses):
        add_issue(
            issues,
            "error",
            "Conversion tracking must be recording or verified before launch.",
            row=row_number,
            column="Conversion tracking status",
            value=conversion_status,
            rule="conversion_tracking_not_ready",
        )

    time_zone = first_value(row, "Time zone", "Account time zone")
    if time_zone and "confirm" in time_zone.lower():
        add_issue(
            issues,
            "warning",
            "Account time zone is marked for confirmation before launch.",
            row=row_number,
            column="Time zone",
            value=time_zone,
            rule="time_zone_review",
        )


def first_value(row: dict[str, str], *columns: str) -> str:
    for column in columns:
        value = row.get(column, "").strip()
        if value:
            return value
    return ""


def validate_bid_strategy_setting(
    bid_strategy: str,
    conversions_30d: str,
    row_number: int,
    issues: list[ValidationIssue],
) -> None:
    conversions = 0.0
    if conversions_30d:
        try:
            conversions = float(conversions_30d.replace(",", ""))
        except ValueError:
            add_issue(
                issues,
                "warning",
                "Conversions last 30 days is not numeric, so bid strategy readiness needs manual review.",
                row=row_number,
                column="Conversions last 30 days",
                value=conversions_30d,
                rule="bid_strategy_conversion_volume_unreadable",
            )
            return
    if bid_strategy in SMART_BIDDING_STRATEGIES and conversions < 15:
        add_issue(
            issues,
            "warning",
            "Smart Bidding is staged with thin conversion volume. Confirm tracking and learning-period risk before launch.",
            row=row_number,
            column="Bid Strategy Type",
            value=bid_strategy,
            rule="smart_bidding_data_threshold_review",
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

    headline_audit = audit_rsa_headlines(
        ad_group=row.get("Ad Group", "").strip(),
        service_label=row.get("Ad Group", "").strip().replace("Services - ", "", 1),
        client_name="",
        headlines=[row.get(headline, "").strip() for headline in REQUIRED_RSA_HEADLINES],
    )
    for audit_issue in headline_audit.issues:
        if audit_issue.rule in {"rsa_headline_required", "headline_length", "headline_minimum_value"}:
            continue
        slot = audit_issue.slots[0] if audit_issue.slots else None
        add_issue(
            issues,
            audit_issue.severity,
            audit_issue.message,
            row=row_number,
            column=f"Headline {slot}" if slot else None,
            value=", ".join(audit_issue.headlines[:4]),
            rule=audit_issue.rule,
        )

    for description in REQUIRED_RSA_DESCRIPTIONS:
        value = row.get(description, "").strip()
        if not value:
            add_issue(issues, "error", f"RSA row is missing {description}.", row=row_number, column=description, rule="rsa_description_required")
        elif len(value) > DESCRIPTION_LIMIT:
            add_issue(issues, "error", f"{description} exceeds {DESCRIPTION_LIMIT} characters.", row=row_number, column=description, value=value, rule="description_length")
        elif len(value) < DESCRIPTION_MINIMUM:
            add_issue(
                issues,
                "error",
                f"{description} is too short for current RSA quality rules. Use at least {DESCRIPTION_MINIMUM} characters.",
                row=row_number,
                column=description,
                value=value,
                rule="description_under_value_minimum",
            )
        elif not has_description_cta(value):
            add_issue(
                issues,
                "error",
                f"{description} must include an approved call to action.",
                row=row_number,
                column=description,
                value=value,
                rule="description_missing_cta",
            )
        elif not has_description_value_prop(value):
            add_issue(
                issues,
                "error",
                f"{description} must include a concrete value proposition.",
                row=row_number,
                column=description,
                value=value,
                rule="description_missing_value_prop",
            )
        elif has_generic_description_phrase(value):
            add_issue(
                issues,
                "error",
                f"{description} uses internal workflow language instead of client-facing service copy.",
                row=row_number,
                column=description,
                value=value,
                rule="description_generic_workflow_language",
            )

    for path_field in ("Path 1", "Path 2"):
        value = row.get(path_field, "").strip()
        if value and len(value) > PATH_LIMIT:
            add_issue(issues, "error", f"{path_field} exceeds {PATH_LIMIT} characters.", row=row_number, column=path_field, value=value, rule="path_length")


def has_description_cta(value: str) -> bool:
    lower = value.lower()
    return any(cta in lower for cta in DEFAULT_DESCRIPTION_CTAS)


def has_description_value_prop(value: str) -> bool:
    tokens = {token for token in re_split(value.lower()) if token}
    return bool(tokens & DESCRIPTION_VALUE_TERMS)


def has_generic_description_phrase(value: str) -> bool:
    lower = value.lower()
    return any(phrase in lower for phrase in GENERIC_DESCRIPTION_PHRASES)


def re_split(value: str) -> list[str]:
    import re

    return re.split(r"\W+", value)


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


def validate_sitelink_row(row: dict[str, str], row_number: int, issues: list[ValidationIssue]) -> None:
    if not is_sitelink_row(row):
        return

    if not row.get("Campaign", "").strip():
        add_issue(issues, "error", "Sitelink row is missing Campaign.", row=row_number, column="Campaign", rule="sitelink_campaign_required")

    link_text = row.get("Link text", "").strip()
    if not link_text:
        add_issue(issues, "error", "Sitelink row is missing Link text.", row=row_number, column="Link text", rule="sitelink_link_text_required")
    elif len(link_text) > SITELINK_TEXT_LIMIT:
        add_issue(
            issues,
            "error",
            f"Sitelink Link text exceeds {SITELINK_TEXT_LIMIT} characters.",
            row=row_number,
            column="Link text",
            value=link_text,
            rule="sitelink_link_text_length",
        )

    if not row.get("Final URL", "").strip():
        add_issue(issues, "error", "Sitelink row is missing Final URL.", row=row_number, column="Final URL", rule="sitelink_final_url_required")

    description_1 = row.get("Description line 1", "").strip()
    description_2 = row.get("Description line 2", "").strip()
    if bool(description_1) != bool(description_2):
        add_issue(
            issues,
            "error",
            "Sitelink descriptions must include both Description line 1 and Description line 2, or neither.",
            row=row_number,
            column="Description line 1",
            rule="sitelink_description_pair_required",
        )

    for column, value in (("Description line 1", description_1), ("Description line 2", description_2)):
        if len(value) > SITELINK_DESCRIPTION_LIMIT:
            add_issue(
                issues,
                "error",
                f"{column} exceeds {SITELINK_DESCRIPTION_LIMIT} characters.",
                row=row_number,
                column=column,
                value=value,
                rule="sitelink_description_length",
            )


def validate_callout_row(row: dict[str, str], row_number: int, issues: list[ValidationIssue]) -> None:
    if not is_callout_row(row):
        return

    if not row.get("Campaign", "").strip():
        add_issue(issues, "error", "Callout row is missing Campaign.", row=row_number, column="Campaign", rule="callout_campaign_required")

    value = row.get("Callout text", "").strip()
    if len(value) > CALLOUT_TEXT_LIMIT:
        add_issue(
            issues,
            "error",
            f"Callout text exceeds {CALLOUT_TEXT_LIMIT} characters.",
            row=row_number,
            column="Callout text",
            value=value,
            rule="callout_text_length",
        )


def structured_snippet_values(row: dict[str, str]) -> list[str]:
    return [value.strip() for value in row.get("Structured snippet values", "").split(";") if value.strip()]


def validate_structured_snippet_row(row: dict[str, str], row_number: int, issues: list[ValidationIssue]) -> None:
    if not is_structured_snippet_row(row):
        return

    if not row.get("Campaign", "").strip():
        add_issue(
            issues,
            "error",
            "Structured snippet row is missing Campaign.",
            row=row_number,
            column="Campaign",
            rule="structured_snippet_campaign_required",
        )

    header = row.get("Structured snippet header", "").strip()
    if header not in APPROVED_STRUCTURED_SNIPPET_HEADERS:
        add_issue(
            issues,
            "error",
            "Structured snippet header must be a Google-approved header.",
            row=row_number,
            column="Structured snippet header",
            value=header,
            rule="structured_snippet_header",
        )

    values = structured_snippet_values(row)
    if len(values) < STRUCTURED_SNIPPET_MIN_VALUES:
        add_issue(
            issues,
            "error",
            f"Structured snippet needs at least {STRUCTURED_SNIPPET_MIN_VALUES} values.",
            row=row_number,
            column="Structured snippet values",
            value=row.get("Structured snippet values", "").strip(),
            rule="structured_snippet_min_values",
        )
    if len(values) > STRUCTURED_SNIPPET_MAX_VALUES:
        add_issue(
            issues,
            "error",
            f"Structured snippet allows at most {STRUCTURED_SNIPPET_MAX_VALUES} values.",
            row=row_number,
            column="Structured snippet values",
            value=row.get("Structured snippet values", "").strip(),
            rule="structured_snippet_max_values",
        )
    for value in values:
        if len(value) > STRUCTURED_SNIPPET_VALUE_LIMIT:
            add_issue(
                issues,
                "error",
                f"Structured snippet value exceeds {STRUCTURED_SNIPPET_VALUE_LIMIT} characters.",
                row=row_number,
                column="Structured snippet values",
                value=value,
                rule="structured_snippet_value_length",
            )


def validate_call_asset_row(row: dict[str, str], row_number: int, issues: list[ValidationIssue]) -> None:
    if not is_call_asset_row(row):
        return

    if not row.get("Campaign", "").strip():
        add_issue(issues, "error", "Call asset row is missing Campaign.", row=row_number, column="Campaign", rule="call_asset_campaign_required")
    if not row.get("Phone number", "").strip():
        add_issue(issues, "error", "Call asset row is missing Phone number.", row=row_number, column="Phone number", rule="call_asset_phone_required")
    if not row.get("Country code", "").strip():
        add_issue(issues, "error", "Call asset row is missing Country code.", row=row_number, column="Country code", rule="call_asset_country_required")


def validate_price_row(row: dict[str, str], row_number: int, issues: list[ValidationIssue]) -> None:
    if not is_price_row(row):
        return

    if not row.get("Campaign", "").strip():
        add_issue(issues, "error", "Price row is missing Campaign.", row=row_number, column="Campaign", rule="price_campaign_required")
    for column, rule in (
        ("Price type", "price_type_required"),
        ("Currency", "price_currency_required"),
        ("Price header", "price_header_required"),
        ("Price amount", "price_amount_required"),
        ("Final URL", "price_final_url_required"),
    ):
        if not row.get(column, "").strip():
            add_issue(issues, "error", f"Price row is missing {column}.", row=row_number, column=column, rule=rule)

    for column, rule in (("Price header", "price_header_length"), ("Price description", "price_description_length")):
        value = row.get(column, "").strip()
        if len(value) > PRICE_TEXT_LIMIT:
            add_issue(issues, "error", f"{column} exceeds {PRICE_TEXT_LIMIT} characters.", row=row_number, column=column, value=value, rule=rule)

    amount = row.get("Price amount", "").strip()
    if amount and not re.match(r"^\$?\d+(?:,\d{3})*(?:\.\d{2})?$", amount):
        add_issue(issues, "error", "Price amount must be a visible numeric price.", row=row_number, column="Price amount", value=amount, rule="price_amount_format")


def validate_promotion_row(row: dict[str, str], row_number: int, issues: list[ValidationIssue]) -> None:
    if not is_promotion_row(row):
        return

    if not row.get("Campaign", "").strip():
        add_issue(issues, "error", "Promotion row is missing Campaign.", row=row_number, column="Campaign", rule="promotion_campaign_required")
    target = row.get("Promotion target", "").strip()
    if not target:
        add_issue(issues, "error", "Promotion row is missing Promotion target.", row=row_number, column="Promotion target", rule="promotion_target_required")
    elif len(target) > PROMOTION_TARGET_LIMIT:
        add_issue(issues, "error", f"Promotion target exceeds {PROMOTION_TARGET_LIMIT} characters.", row=row_number, column="Promotion target", value=target, rule="promotion_target_length")
    if not row.get("Final URL", "").strip():
        add_issue(issues, "error", "Promotion row is missing Final URL.", row=row_number, column="Final URL", rule="promotion_final_url_required")
    if not (row.get("Percent off", "").strip() or row.get("Money amount off", "").strip() or row.get("Promotion code", "").strip()):
        add_issue(issues, "error", "Promotion row needs discount evidence or a promotion code.", row=row_number, column="Promotion target", rule="promotion_offer_required")


def validate_business_name_row(row: dict[str, str], row_number: int, issues: list[ValidationIssue]) -> None:
    if not is_business_name_row(row):
        return

    if not row.get("Campaign", "").strip():
        add_issue(issues, "error", "Business name row is missing Campaign.", row=row_number, column="Campaign", rule="business_name_campaign_required")
    value = row.get("Business name", "").strip()
    if len(value) > BUSINESS_NAME_LIMIT:
        add_issue(issues, "error", f"Business name exceeds {BUSINESS_NAME_LIMIT} characters.", row=row_number, column="Business name", value=value, rule="business_name_length")


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

        if is_ad_group_row(row) and not is_asset_row(row):
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

        if is_sitelink_row(row):
            counts["sitelink_rows"] += 1
            validate_sitelink_row(row, row_number, issues)

        if is_callout_row(row):
            counts["callout_rows"] += 1
            validate_callout_row(row, row_number, issues)

        if is_structured_snippet_row(row):
            counts["structured_snippet_rows"] += 1
            validate_structured_snippet_row(row, row_number, issues)

        if is_call_asset_row(row):
            counts["call_asset_rows"] += 1
            validate_call_asset_row(row, row_number, issues)

        if is_price_row(row):
            counts["price_rows"] += 1
            validate_price_row(row, row_number, issues)

        if is_promotion_row(row):
            counts["promotion_rows"] += 1
            validate_promotion_row(row, row_number, issues)

        if is_business_name_row(row):
            counts["business_name_rows"] += 1
            validate_business_name_row(row, row_number, issues)

        if row.get("Bid Modifier", "").strip():
            counts["bid_modifier_rows"] += 1

    sitelink_texts_by_branch: dict[tuple[str, str], dict[str, int]] = defaultdict(dict)
    for row_number, row in enumerate(rows, start=2):
        if not is_sitelink_row(row):
            continue
        branch = (row.get("Campaign", "").strip(), row.get("Ad Group", "").strip())
        link_text = row.get("Link text", "").strip().lower()
        if not link_text:
            continue
        if link_text in sitelink_texts_by_branch[branch]:
            add_issue(
                issues,
                "error",
                "Sitelink Link text must be unique within the same campaign and ad group branch.",
                row=row_number,
                column="Link text",
                value=row.get("Link text", "").strip(),
                rule="sitelink_duplicate_link_text",
            )
        else:
            sitelink_texts_by_branch[branch][link_text] = row_number

    price_counts_by_branch: Counter[tuple[str, str]] = Counter()
    for row in rows:
        if is_price_row(row):
            price_counts_by_branch[(row.get("Campaign", "").strip(), row.get("Ad Group", "").strip())] += 1
    for (campaign, ad_group), count in price_counts_by_branch.items():
        if count < PRICE_MIN_ITEMS:
            add_issue(
                issues,
                "error",
                "Price assets require at least three explicit price items in the same campaign and ad group branch.",
                column="Price amount",
                value=f"{campaign} / {ad_group}: {count}",
                rule="price_min_items",
            )

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

    stable_counts = {
        key: counts[key]
        for key in (
            "campaign_rows",
            "ad_group_rows",
            "keyword_rows",
            "negative_keyword_rows",
            "rsa_rows",
            "location_rows",
            "radius_rows",
            "sitelink_rows",
            "callout_rows",
            "structured_snippet_rows",
            "call_asset_rows",
            "price_rows",
            "promotion_rows",
            "business_name_rows",
            "bid_modifier_rows",
        )
    }

    return {
        "status": status,
        "source_csv": str(source),
        "encoding": encoding,
        "rows": len(rows),
        "headers": len(headers),
        "campaigns": sorted(campaigns),
        "ad_groups": sum(len(groups) for groups in ad_groups_by_campaign.values()),
        "counts": stable_counts,
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
