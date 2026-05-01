#!/usr/bin/env python3
"""Compatibility master validator for active Google Ads Agent staging files."""

from __future__ import annotations

import json
import csv
import io
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from shared.rebuild.staging_validator import validate_file


class MasterValidator:
    """
    Coordinate validation without treating client folders as process authority.

    Active Google Ads Editor staging checks are delegated to
    ``shared.rebuild.staging_validator``. This class preserves the older public
    methods used by runner scripts while keeping the validation source of truth
    generic and repo-local.
    """

    def validate_csv_file(self, csv_path: str, auto_fix: bool = False) -> dict[str, Any]:
        """Validate a single active staging CSV file."""
        del auto_fix
        path = Path(csv_path)
        try:
            active_report = validate_file(path)
        except Exception as exc:
            return {
                "csv_file": csv_path,
                "success": False,
                "error": f"Failed to validate CSV file: {exc}",
                "validation_report": None,
                "final_status": "FAIL",
            }

        issues = [self._active_issue_to_legacy(issue) for issue in active_report.get("issues", [])]
        report = self._generate_validation_report(csv_path, issues, [], active_report)
        return {
            "csv_file": csv_path,
            "success": True,
            "error": None,
            "validation_report": report,
            "final_status": report["final_status"],
            "active_staging_report": active_report,
        }

    def validate_client_directory(self, client_dir: str, auto_fix: bool = False) -> dict[str, Any]:
        """Validate CSV files below any supplied directory."""
        client_path = Path(client_dir)
        if not client_path.exists():
            return {
                "client_directory": client_dir,
                "success": False,
                "error": f"Directory not found: {client_dir}",
                "validation_results": [],
            }

        validation_results = [self.validate_csv_file(str(csv_file), auto_fix) for csv_file in self._find_csv_files(client_path)]
        client_report = self._generate_client_report(client_dir, validation_results)
        return {
            "client_directory": client_dir,
            "success": True,
            "error": None,
            "validation_results": validation_results,
            "client_summary": client_report,
        }

    def validate_all_clients(self, base_dir: str = "clients", auto_fix: bool = False) -> dict[str, Any]:
        """Validate all immediate child directories under the active clients root."""
        base_path = Path(base_dir)
        if not base_path.exists():
            return {
                "base_directory": base_dir,
                "success": False,
                "error": f"Base directory not found: {base_dir}",
                "client_results": [],
            }

        client_dirs = [path for path in sorted(base_path.iterdir()) if path.is_dir() and not path.name.startswith(".")]
        client_results = [self.validate_client_directory(str(client_dir), auto_fix) for client_dir in client_dirs]
        global_report = self._generate_global_report(base_dir, client_results)
        return {
            "base_directory": base_dir,
            "success": True,
            "error": None,
            "client_results": client_results,
            "global_summary": global_report,
        }

    def _find_csv_files(self, directory: Path) -> list[Path]:
        """Find candidate staging CSV files below a directory."""
        skip_parts = {"__pycache__", ".git", "node_modules"}
        csv_files: list[Path] = []
        for path in sorted(directory.rglob("*.csv")):
            if any(part in skip_parts for part in path.parts):
                continue
            name = path.name.lower()
            if "report" in name and "staging" not in name and "editor" not in name:
                continue
            csv_files.append(path)
        return csv_files

    def _is_search_campaign_csv(self, csv_content: str) -> bool:
        """Compatibility helper for older SearchMasterValidator wrappers."""
        try:
            reader = csv.DictReader(io.StringIO(csv_content), delimiter="\t")
            headers = set(reader.fieldnames or [])
            if {"Keyword", "Criterion Type", "Ad Group"} & headers:
                return True
            return any(row.get("Campaign Type", "").strip() == "Search" for row in reader)
        except Exception:
            return False

    def _apply_auto_fixes(self, csv_content: str, all_issues: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
        """Compatibility no-op. Active staging validation does not mutate CSVs."""
        del all_issues
        return csv_content, []

    def _apply_auto_fixes_to_csv(
        self, csv_content: str, all_issues: list[dict[str, Any]]
    ) -> tuple[str, list[dict[str, Any]]]:
        """Compatibility alias for older search wrappers."""
        return self._apply_auto_fixes(csv_content, all_issues)

    def _generate_validation_report(
        self,
        csv_path: str,
        all_issues: list[dict[str, Any]],
        fixed_issues: list[dict[str, Any]],
        active_report: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate the legacy report shape expected by existing runners."""
        severity_counts = {"critical": 0, "error": 0, "warning": 0, "info": 0}
        level_counts: Counter[str] = Counter()

        for issue in all_issues:
            severity = issue.get("severity", "warning")
            severity_counts[severity if severity in severity_counts else "warning"] += 1
            level_counts[issue.get("level", "staging")] += 1

        final_status = "FAIL" if severity_counts["critical"] or severity_counts["error"] else "PASS"
        if fixed_issues and final_status == "PASS":
            final_status = "PASS_WITH_FIXES"

        return {
            "csv_file": csv_path,
            "timestamp": datetime.now().isoformat(),
            "total_issues": len(all_issues),
            "issues_fixed": len(fixed_issues),
            "severity_breakdown": severity_counts,
            "level_breakdown": dict(level_counts),
            "final_status": final_status,
            "issues": all_issues,
            "fixes_applied": fixed_issues,
            "active_staging": active_report or {},
        }

    def _generate_client_report(self, client_dir: str, validation_results: list[dict[str, Any]]) -> dict[str, Any]:
        total_csvs = len(validation_results)
        successful = [result for result in validation_results if result.get("success") and result.get("validation_report")]
        status_counts = Counter(result["validation_report"]["final_status"] for result in successful)
        return {
            "client_directory": client_dir,
            "timestamp": datetime.now().isoformat(),
            "csv_files_processed": total_csvs,
            "successful_validations": len(successful),
            "total_issues_found": sum(result["validation_report"]["total_issues"] for result in successful),
            "total_fixes_applied": sum(result["validation_report"]["issues_fixed"] for result in successful),
            "status_breakdown": {
                "PASS": status_counts.get("PASS", 0),
                "PASS_WITH_FIXES": status_counts.get("PASS_WITH_FIXES", 0),
                "FAIL": status_counts.get("FAIL", 0),
            },
            "overall_status": "FAIL" if status_counts.get("FAIL", 0) else "PASS",
        }

    def _generate_global_report(self, base_dir: str, client_results: list[dict[str, Any]]) -> dict[str, Any]:
        successful = [result for result in client_results if result.get("success") and result.get("client_summary")]
        status_counts = Counter(result["client_summary"]["overall_status"] for result in successful)
        return {
            "base_directory": base_dir,
            "timestamp": datetime.now().isoformat(),
            "clients_processed": len(client_results),
            "successful_clients": len(successful),
            "total_issues_found": sum(result["client_summary"]["total_issues_found"] for result in successful),
            "total_fixes_applied": sum(result["client_summary"]["total_fixes_applied"] for result in successful),
            "client_status_breakdown": {
                "PASS": status_counts.get("PASS", 0),
                "FAIL": status_counts.get("FAIL", 0),
            },
            "overall_status": "FAIL" if status_counts.get("FAIL", 0) else "PASS",
        }

    def save_report(self, report: dict[str, Any], output_path: str) -> None:
        """Save a validation report to JSON."""
        Path(output_path).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def print_summary_report(self, report: dict[str, Any]) -> None:
        """Print a small summary for CLI callers."""
        validation_report = report.get("validation_report") or report.get("client_summary") or report.get("global_summary")
        if not validation_report:
            print(f"Validation failed: {report.get('error', 'unknown error')}")
            return

        status = validation_report.get("final_status") or validation_report.get("overall_status")
        total_issues = validation_report.get("total_issues", validation_report.get("total_issues_found", 0))
        print(f"Status: {status}")
        print(f"Total issues: {total_issues}")

    @staticmethod
    def _active_issue_to_legacy(issue: dict[str, Any]) -> dict[str, Any]:
        return {
            "level": issue.get("rule", "staging"),
            "severity": issue.get("severity", "warning"),
            "row_number": issue.get("row") or 0,
            "column": issue.get("column") or "",
            "issue_type": issue.get("rule", "active_staging_issue"),
            "message": issue.get("message", ""),
            "value": issue.get("value"),
            "auto_fixable": False,
        }
