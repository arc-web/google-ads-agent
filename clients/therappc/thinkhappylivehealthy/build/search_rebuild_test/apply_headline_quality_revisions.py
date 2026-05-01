#!/usr/bin/env python3
"""Create THLH REV2 staging CSV with headline quality repairs."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.rebuild.staging_validator import validate_file


BUILD_DIR = ROOT / "clients" / "therappc" / "thinkhappylivehealthy" / "build" / "search_rebuild_test"
INPUT_CSV = BUILD_DIR / "THHL_Search_Services_Editor_Staging_REV1.csv"
OUTPUT_CSV = BUILD_DIR / "THHL_Search_Services_Editor_Staging_REV2.csv"
VALIDATION_JSON = BUILD_DIR / "THHL_Search_Services_Editor_Staging_REV2_validation.json"
REVIEW_MD = BUILD_DIR / "THHL_Search_Services_Editor_Staging_REV2_review.md"
REPAIR_SUMMARY_JSON = BUILD_DIR / "THHL_Search_Services_Editor_Staging_REV2_headline_repair_summary.json"

HEADLINE_MINIMUM = 25
HEADLINE_LIMIT = 30

HEADLINE_REPAIRS = {
    "Child Psychiatry Ashburn": "Child Psychiatry In Ashburn",
    "Psych NP Appointments": "Psych NP Appointments Open",
    "Medication Mgmt Support": "Medication Management Care",
    "Ashburn Psychiatry Care": "Ashburn Psychiatry Support",
    "Accepting New Patients": "Accepting New Patients Now",
    "In-Person Psychiatry": "In-Person Psychiatry Care",
    "Anthem/CareFirst BCBS": "Anthem & CareFirst Support",
    "Care Planning Support": "Care Planning Support Now",
    "Northern Virginia Care": "Northern VA Therapy Support",
    "Think Happy Live Healthy": "Think Happy Live Healthy Care",
    "Book Psychiatry Consult": "Book Psychiatry Consult Today",
    "Mental Health Support": "Mental Health Care Support",
    "Adult Psychiatry Ashburn": "Adult Psychiatry In Ashburn",
    "Anxiety Therapy Near You": "Anxiety Therapy Near You Now",
    "Anxiety Therapy Help": "Anxiety Therapy Support Now",
    "Anxiety Counseling": "Anxiety Counseling Support",
    "Ashburn Care": "Ashburn Care Appointments",
    "Book Therapy Appointment": "Book Therapy Appointment Today",
    "Support That Fits Life": "Support That Fits Real Life",
    "Appointments Available": "New Appointments Available",
    "Local Appointments Open": "Local Appointments Open Now",
    "Care Near You Today": "Therapy Care Near You Today",
    "Anxiety Therapy Ashburn": "Anxiety Therapy Ashburn VA",
    "ADHD Therapist Near You": "ADHD Therapist Visits Near You",
    "ADHD Therapy Near You": "ADHD Therapy Near You Today",
    "Telehealth Available": "Telehealth Appointments Open",
    "ADHD Therapy Ashburn": "ADHD Therapy Ashburn Support",
    "Depression Therapy Help": "Depression Therapy Support",
    "LGBTQ Therapist Near You": "LGBTQ Therapy Near You Today",
    "LGBTQIA Therapy Help": "LGBTQIA Therapy Support Now",
    "LGBTQIA+ Therapy Ashburn": "LGBTQIA+ Therapy Ashburn VA",
    "Stress Therapy Near You": "Stress Therapy Near You Today",
    "Stress Therapy Help": "Stress Therapy Support Today",
    "Stress Therapy Ashburn": "Stress Therapy Ashburn VA",
    "Grief Therapist Near You": "Grief Therapy Near You Today",
    "Grief Therapy Help": "Grief Therapy Support Today",
    "Grief Support Counseling": "Grief Support Counseling Care",
    "Trauma Therapy Near You": "Trauma Therapy Near You Today",
    "Trauma Therapy Help": "Trauma Therapy Support Today",
    "Trauma Therapy Ashburn": "Trauma Therapy Ashburn VA",
    "Support For IEP Planning": "Support For School IEP Plans",
    "Child Psych Assessment": "Child Psych Assessment Help",
    "Learning Evaluation Help": "Learning Evaluation Support",
    "Gifted Testing Near You": "Gifted Testing Near You Today",
    "Schedule Gifted Testing": "Schedule Gifted Testing Now",
    "Gifted Testing Help": "Gifted Testing Support Today",
    "Book Your Assessment": "Book Your Assessment Today",
    "Gifted Testing Ashburn": "Gifted Testing Ashburn VA",
    "Young Adult ADHD Testing": "Young Adult ADHD Testing Care",
    "ADHD Evaluation for Kids": "ADHD Evaluation for Kids Now",
    "Ashburn & Falls Church": "Ashburn & Falls Church Care",
    "ADHD Assessment Near You": "ADHD Assessment Near You Now",
    "Kindergarten Assessment": "Kindergarten Assessment Help",
    "Autism Testing Near You": "Autism Testing Near You Today",
    "Schedule Autism Testing": "Schedule Autism Testing Now",
    "Autism Testing Help": "Autism Testing Support Today",
    "Autism Testing Ashburn": "Autism Testing Ashburn VA",
    "Official Practice Site": "Official Practice Website",
    "Testing Appointments": "Testing Appointments Open",
    "Licensed Clinicians": "Licensed Clinician Support",
    "Care For Families": "Care Support For Families",
    "Book Your Appointment": "Book Your Appointment Today",
    "Testing Through Age 21": "Testing Through Age 21 Only",
}


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-16", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_rows(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-16", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_repair_map() -> None:
    for source, replacement in HEADLINE_REPAIRS.items():
        if len(source) >= HEADLINE_MINIMUM:
            raise ValueError(f"Repair source is already long enough: {source}")
        if not HEADLINE_MINIMUM <= len(replacement) <= HEADLINE_LIMIT:
            raise ValueError(
                f"Replacement must be {HEADLINE_MINIMUM}-{HEADLINE_LIMIT} chars: "
                f"{replacement} ({len(replacement)})"
            )


def repair_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[str, object]]:
    replacement_counts: Counter[str] = Counter()
    unrepaired_short: list[dict[str, object]] = []

    for row_number, row in enumerate(rows, start=2):
        if row.get("Ad type") != "Responsive search ad":
            continue
        for index in range(1, 16):
            column = f"Headline {index}"
            value = row.get(column, "").strip()
            if value in HEADLINE_REPAIRS:
                row[column] = HEADLINE_REPAIRS[value]
                replacement_counts[value] += 1
            elif value and len(value) < HEADLINE_MINIMUM:
                unrepaired_short.append(
                    {
                        "row": row_number,
                        "column": column,
                        "headline": value,
                        "chars": len(value),
                    }
                )

    return rows, {
        "input_csv": str(INPUT_CSV),
        "output_csv": str(OUTPUT_CSV),
        "headline_minimum": HEADLINE_MINIMUM,
        "headline_limit": HEADLINE_LIMIT,
        "total_replacements": sum(replacement_counts.values()),
        "unique_replacements": len(replacement_counts),
        "replacement_counts": dict(sorted(replacement_counts.items())),
        "unrepaired_short_headlines": unrepaired_short,
    }


def write_review(summary: dict[str, object], validation: dict[str, object]) -> None:
    lines = [
        "# THHL Search Services Editor Staging REV2 Review",
        "",
        f"CSV: `{OUTPUT_CSV}`",
        "",
        f"Validation status: `{validation['status']}`",
        f"Headline replacements: `{summary['total_replacements']}`",
        f"Unique weak headlines repaired: `{summary['unique_replacements']}`",
        "",
        "## What Changed",
        "",
        "- Repaired REV1 RSA headlines that failed the 25-character headline quality gate.",
        "- Kept campaign structure, keywords, targeting, budgets, descriptions, and final URLs unchanged.",
        "- Kept Google Ads Editor staging-first. No live upload or API mutation was performed.",
        "",
        "## Validation",
        "",
        f"- Active staging validator status: `{validation['status']}`",
        f"- Active staging validator issues: `{len(validation.get('issues', []))}`",
        "",
        "## Remaining Review",
        "",
    ]
    if summary["unrepaired_short_headlines"]:
        lines.append("- Some short headlines were not repaired and need review.")
    else:
        lines.append("- No unrepaired short RSA headlines remain.")
    REVIEW_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    validate_repair_map()
    headers, rows = read_rows(INPUT_CSV)
    rows, summary = repair_rows(rows)
    if summary["unrepaired_short_headlines"]:
        raise RuntimeError("Short RSA headlines remain unrepaired.")
    write_rows(OUTPUT_CSV, headers, rows)
    validation = validate_file(OUTPUT_CSV)
    summary["staging_validator"] = {
        "status": validation["status"],
        "issue_count": len(validation.get("issues", [])),
    }
    REPAIR_SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    VALIDATION_JSON.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    write_review(summary, validation)
    print(json.dumps(summary, indent=2))
    print(json.dumps({"validation_status": validation["status"], "issue_count": len(validation.get("issues", []))}, indent=2))


if __name__ == "__main__":
    main()
