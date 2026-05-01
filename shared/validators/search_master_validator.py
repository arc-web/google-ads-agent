#!/usr/bin/env python3
"""Legacy top-level Search master validator facade."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .search.search_master_validator import SearchMasterValidator as ActiveSearchMasterValidator


class SearchMasterValidator:
    """
    Compatibility facade for the active Search master validator.

    The old top-level validator inherited from a missing PMAX-era master class
    and attempted auto-fixes that defaulted to Exact. This facade keeps the old
    public entry points while delegating Search validation to the active staged
    workflow under shared.validators.search.search_master_validator.
    """

    def __init__(self, base_path: str = "google_ads_agent", validation_rules: dict[str, Any] | None = None):
        self.base_path = Path(base_path)
        self.active_validator = ActiveSearchMasterValidator(validation_rules)

    def validate_search_campaign_csv(self, csv_path: str, auto_fix: bool = False) -> dict[str, Any]:
        """Validate a Search staging CSV with the active validator."""
        if auto_fix:
            return {
                "csv_file": csv_path,
                "success": False,
                "error": "Auto-fix is disabled for active Search staging validation.",
                "validation_report": None,
                "campaign_type": "Search",
            }

        report = self.active_validator.validate_csv_file(csv_path)
        return {
            "csv_file": csv_path,
            "success": report.success,
            "error": None,
            "validation_report": self._report_dict(report),
            "campaign_type": "Search",
        }

    def validate_csv_file(self, csv_path: str, auto_fix: bool = False) -> dict[str, Any]:
        """Legacy alias for validate_search_campaign_csv."""
        return self.validate_search_campaign_csv(csv_path, auto_fix)

    def validate_client_directory(self, client_dir: str, auto_fix: bool = False) -> dict[str, Any]:
        """Validate CSV/TSV files below a client directory without changing them."""
        if auto_fix:
            return {
                "client_dir": client_dir,
                "success": False,
                "error": "Auto-fix is disabled for active Search staging validation.",
                "files": [],
            }

        root = Path(client_dir)
        files = sorted(
            path
            for pattern in ("*.csv", "*.tsv")
            for path in root.rglob(pattern)
            if path.is_file()
        )
        results = [self.validate_search_campaign_csv(str(path), auto_fix=False) for path in files]
        return {
            "client_dir": client_dir,
            "success": all(result.get("success") for result in results),
            "error": None,
            "files": results,
        }

    def get_detailed_issues(self) -> list[dict[str, Any]]:
        """Expose detailed issues from the active validator."""
        return self.active_validator.get_detailed_issues()

    def print_summary_report(self, result: dict[str, Any]) -> None:
        """Print a short legacy-compatible summary."""
        report = result.get("validation_report") or {}
        print(f"Search validation: {'PASS' if result.get('success') else 'FAIL'}")
        if result.get("error"):
            print(result["error"])
        elif report:
            print(f"Total issues: {report.get('total_issues', 0)}")

    def save_report(self, result: dict[str, Any], output_path: str) -> None:
        """Save a JSON validation report."""
        Path(output_path).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    def _report_dict(self, report: Any) -> dict[str, Any]:
        return {
            "csv_file": report.csv_file,
            "total_issues": report.total_issues,
            "critical_issues": report.critical_issues,
            "warning_issues": report.warning_issues,
            "info_issues": report.info_issues,
            "issues_by_level": report.issues_by_level,
            "validation_time": report.validation_time,
            "success": report.success,
            "issues": self.active_validator.get_detailed_issues(),
        }


def validate_search_campaign_file(csv_path: str, auto_fix: bool = False) -> dict[str, Any]:
    """Validate a single Search campaign staging file."""
    return SearchMasterValidator().validate_search_campaign_csv(csv_path, auto_fix)


def validate_search_client_directory(client_dir: str, auto_fix: bool = False) -> dict[str, Any]:
    """Validate all Search campaign staging files in a client directory."""
    return SearchMasterValidator().validate_client_directory(client_dir, auto_fix)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Search Campaign CSV Validator")
    parser.add_argument("--csv", help="Path to Search campaign CSV file")
    parser.add_argument("--client", help="Client directory containing Search CSVs")
    parser.add_argument("--output", help="Output JSON report file")
    parser.add_argument("--fix", action="store_true", help="Rejected. Auto-fix is disabled.")
    args = parser.parse_args()

    validator = SearchMasterValidator()
    if args.csv:
        validation_result = validator.validate_search_campaign_csv(args.csv, args.fix)
    elif args.client:
        validation_result = validator.validate_client_directory(args.client, args.fix)
    else:
        parser.print_help()
        raise SystemExit(2)

    validator.print_summary_report(validation_result)
    if args.output:
        validator.save_report(validation_result, args.output)
    raise SystemExit(0 if validation_result.get("success") else 1)
