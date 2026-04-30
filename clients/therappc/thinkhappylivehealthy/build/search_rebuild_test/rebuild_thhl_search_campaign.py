#!/usr/bin/env python3
"""
Rebuild one ThinkHappyLiveHealthy Search campaign into a Google Ads Editor TSV.

This is intentionally client-scoped for the first automation test. It preserves
the manual campaign draft rows, expands the header to match the current account
export, then appends geo, radius, and demographic targeting rows from a static
targeting spec.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
CLIENT_DIR = ROOT / "clients" / "therappc" / "thinkhappylivehealthy"
BUILD_DIR = CLIENT_DIR / "build" / "search_rebuild_test"

MANUAL_CAMPAIGN = CLIENT_DIR / "campaigns" / "THHL_Search_Campaign_2026-04-28.csv"
CURRENT_EXPORT = CLIENT_DIR / "campaigns" / "ThinkHappyLiveHealthy_export_2026-04-27.csv"
TARGETING_SPEC = BUILD_DIR / "targeting_spec.json"
COPY_OVERRIDES = BUILD_DIR / "copy_overrides.json"
OUTPUT_CSV = BUILD_DIR / "THHL_Search_Rebuild_Test_2026-04-28.csv"
VALIDATION_REPORT = BUILD_DIR / "validation_report.json"
HUMAN_REVIEW = BUILD_DIR / "human_review.md"

HEADLINE_LIMIT = 30
DESCRIPTION_LIMIT = 90


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]], str]:
    for encoding in ("utf-16", "utf-8-sig", "utf-8"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle, delimiter="\t")
                rows = list(reader)
                if reader.fieldnames:
                    return reader.fieldnames, rows, encoding
        except UnicodeError:
            continue
    raise RuntimeError(f"Could not read TSV file: {path}")


def write_tsv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-16", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def ordered_union(*header_lists: list[str]) -> list[str]:
    headers: list[str] = []
    seen: set[str] = set()
    for header_list in header_lists:
        for header in header_list:
            if header not in seen:
                seen.add(header)
                headers.append(header)
    return headers


def normalize_rows(rows: list[dict[str, str]], headers: list[str]) -> list[dict[str, str]]:
    return [{header: row.get(header, "") for header in headers} for row in rows]


def apply_copy_overrides(rows: list[dict[str, str]], overrides: list[dict[str, str]]) -> list[dict[str, str]]:
    updated_rows = [dict(row) for row in rows]
    for override in overrides:
        matches = 0
        for row in updated_rows:
            if (
                row.get("Ad Group") == override["ad_group"]
                and row.get("Ad type") == "Responsive search ad"
                and row.get(override["field"]) == override["from"]
            ):
                row[override["field"]] = override["to"]
                matches += 1
        override["matches"] = str(matches)
    return updated_rows


def base_targeting_row(campaign: str, spec: dict[str, Any]) -> dict[str, str]:
    return {
        "Campaign": campaign,
        "Targeting method": spec["targeting_method"],
        "Exclusion method": spec["exclusion_method"],
        "Campaign Status": "Enabled",
        "Status": "Enabled",
    }


def build_targeting_rows(spec: dict[str, Any]) -> list[dict[str, str]]:
    campaign = spec["campaign"]
    rows: list[dict[str, str]] = []

    for layer in spec["geo_layers"]:
        for location in layer["locations"]:
            row = base_targeting_row(campaign, spec)
            row.update({
                "Location": location,
                "Bid Modifier": layer.get("bid_modifier", ""),
                "Comment": f"{layer['tier']} | {layer['review_status']}",
            })
            rows.append(row)

    for target in spec["radius_targets"]:
        row = base_targeting_row(campaign, spec)
        row.update({
            "Location": target["location"],
            "Radius": target["radius"],
            "Unit": target["unit"],
            "Bid Modifier": target.get("bid_modifier", ""),
            "Comment": f"radius | {target['source']} | {target['review_status']}",
        })
        rows.append(row)

    for item in spec["demographics"]["age"]:
        row = base_targeting_row(campaign, spec)
        row.update({
            "Age": item["value"],
            "Bid Modifier": item.get("bid_modifier", ""),
            "Comment": f"age | {item['review_status']}",
        })
        rows.append(row)

    for item in spec["demographics"]["gender"]:
        row = base_targeting_row(campaign, spec)
        row.update({
            "Gender": item["value"],
            "Bid Modifier": item.get("bid_modifier", ""),
            "Comment": f"gender | {item['review_status']}",
        })
        rows.append(row)

    for item in spec["demographics"]["household_income"]:
        row = base_targeting_row(campaign, spec)
        row.update({
            "Household income": item["value"],
            "Bid Modifier": item.get("bid_modifier", ""),
            "Comment": f"household_income | {item['review_status']}",
        })
        rows.append(row)

    return rows


def validate_rows(headers: list[str], rows: list[dict[str, str]], manual_count: int) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    counts = Counter()
    ad_groups = set()
    keywords = set()

    required_headers = [
        "Campaign",
        "Ad Group",
        "Keyword",
        "Ad type",
        "Location",
        "Age",
        "Gender",
        "Household income",
        "Bid Modifier",
        "Campaign Status",
        "Status",
    ]
    for header in required_headers:
        if header not in headers:
            issues.append({"severity": "error", "message": f"Missing required test header: {header}"})

    for row_number, row in enumerate(rows, start=2):
        if row.get("Campaign"):
            counts["campaign_rows_with_name"] += 1
        if row.get("Ad Group") and not row.get("Keyword") and not row.get("Ad type"):
            counts["ad_group_rows"] += 1
            ad_groups.add(row["Ad Group"])
        if row.get("Keyword"):
            counts["keyword_rows"] += 1
            keywords.add((row.get("Ad Group", ""), row["Keyword"]))
        if row.get("Ad type") == "Responsive search ad":
            counts["rsa_rows"] += 1
        if row.get("Location"):
            if row.get("Radius"):
                counts["radius_rows"] += 1
            else:
                counts["location_rows"] += 1
        if row.get("Age"):
            counts["age_rows"] += 1
        if row.get("Gender"):
            counts["gender_rows"] += 1
        if row.get("Household income"):
            counts["household_income_rows"] += 1
        if row.get("Bid Modifier"):
            counts["bid_modifier_rows"] += 1

        for index in range(1, 16):
            value = row.get(f"Headline {index}", "")
            if len(value) > HEADLINE_LIMIT:
                issues.append({
                    "severity": "error",
                    "row": row_number,
                    "column": f"Headline {index}",
                    "message": f"Headline exceeds {HEADLINE_LIMIT} characters: {value}",
                })

        for index in range(1, 6):
            value = row.get(f"Description {index}", "")
            if len(value) > DESCRIPTION_LIMIT:
                issues.append({
                    "severity": "error",
                    "row": row_number,
                    "column": f"Description {index}",
                    "message": f"Description exceeds {DESCRIPTION_LIMIT} characters: {value}",
                })

    if counts["location_rows"] == 0 and counts["radius_rows"] == 0:
        issues.append({"severity": "error", "message": "No location or radius rows were generated."})
    if counts["age_rows"] == 0 or counts["gender_rows"] == 0 or counts["household_income_rows"] == 0:
        issues.append({"severity": "warning", "message": "One or more demographic row types are missing."})

    return {
        "status": "pass" if not any(issue["severity"] == "error" for issue in issues) else "fail",
        "source_manual_rows": manual_count,
        "output_rows": len(rows),
        "headers": len(headers),
        "counts": dict(counts),
        "unique_ad_groups": sorted(ad_groups),
        "unique_keyword_count": len(keywords),
        "issues": issues,
    }


def write_human_review(report: dict[str, Any], spec: dict[str, Any]) -> None:
    lines = [
        "# ThinkHappyLiveHealthy Search Rebuild Human Review",
        "",
        f"Campaign: `{spec['campaign']}`",
        "",
        "## Validation Status",
        "",
        f"Status: `{report['status']}`",
        f"Output rows: `{report['output_rows']}`",
        f"Headers: `{report['headers']}`",
        "",
        "## Row Counts",
        "",
    ]
    for key, value in sorted(report["counts"].items()):
        lines.append(f"- {key}: `{value}`")

    lines.extend([
        "",
        "## Human Decisions Needed",
        "",
        "- Confirm Tier 1 geo bid modifier of `20`.",
        "- Confirm Tier 2 geo bid modifier of `10`.",
        "- Confirm whether the reused 15 mile radius target is still correct for this campaign.",
        "- Confirm age bid modifiers before upload.",
        "- Keep gender and household income at observation unless performance data supports changes.",
        "- Review policy risk on mental health copy before upload.",
        "- Review generated copy overrides before upload.",
        "",
        "## Issues",
        "",
    ])

    if report["issues"]:
        for issue in report["issues"]:
            location = f" row {issue['row']}" if "row" in issue else ""
            column = f" column `{issue['column']}`" if "column" in issue else ""
            lines.append(f"- `{issue['severity']}`{location}{column}: {issue['message']}")
    else:
        lines.append("- No validation issues from the rebuild harness.")

    lines.append("")
    HUMAN_REVIEW.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    manual_headers, manual_rows, manual_encoding = read_tsv(MANUAL_CAMPAIGN)
    export_headers, _export_rows, export_encoding = read_tsv(CURRENT_EXPORT)
    spec = json.loads(TARGETING_SPEC.read_text(encoding="utf-8"))
    copy_overrides = json.loads(COPY_OVERRIDES.read_text(encoding="utf-8"))

    headers = ordered_union(export_headers, manual_headers, ["Comment"])
    rebuilt_rows = normalize_rows(apply_copy_overrides(manual_rows, copy_overrides), headers)
    targeting_rows = normalize_rows(build_targeting_rows(spec), headers)
    output_rows = rebuilt_rows + targeting_rows

    write_tsv(OUTPUT_CSV, headers, output_rows)

    report = validate_rows(headers, output_rows, manual_count=len(manual_rows))
    report["sources"] = {
        "manual_campaign": str(MANUAL_CAMPAIGN),
        "manual_encoding": manual_encoding,
        "current_export": str(CURRENT_EXPORT),
        "current_export_encoding": export_encoding,
        "targeting_spec": str(TARGETING_SPEC),
        "copy_overrides": str(COPY_OVERRIDES),
        "output_csv": str(OUTPUT_CSV),
    }
    report["copy_overrides"] = copy_overrides
    VALIDATION_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_human_review(report, spec)

    print(json.dumps({
        "status": report["status"],
        "output_csv": str(OUTPUT_CSV),
        "validation_report": str(VALIDATION_REPORT),
        "human_review": str(HUMAN_REVIEW),
        "counts": report["counts"],
        "issues": len(report["issues"]),
    }, indent=2))


if __name__ == "__main__":
    main()
