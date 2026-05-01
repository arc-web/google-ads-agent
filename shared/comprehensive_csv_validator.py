#!/usr/bin/env python3
"""Compatibility CSV validator for the active Google Ads Editor workflow.

The old comprehensive validator mixed Search, PMAX, account-specific copy
rules, and optional auto-fixes. Active CSV pass/fail authority now belongs to
``shared.rebuild.staging_validator`` through ``shared.validators.MasterValidator``.
This module keeps the legacy import path available without mutating source CSVs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.validators.master_validator import MasterValidator


class AutoFixDisabled(RuntimeError):
    """Raised when a caller asks this compatibility validator to mutate CSVs."""


class ComprehensiveCSVValidator(MasterValidator):
    """Legacy facade that delegates validation to the active staging validator."""

    def __init__(self, base_path: str | Path = "clients"):
        self.base_path = Path(base_path)

    def validate_csv_file(self, csv_path: str, auto_fix: bool = False) -> dict[str, Any]:
        """Validate one CSV without changing it."""
        self._reject_auto_fix(auto_fix)
        return super().validate_csv_file(csv_path, auto_fix=False)

    def validate_client_csvs(
        self,
        client_name: str,
        auto_fix: bool = False,
        output_path: str | None = None,
    ) -> dict[str, Any]:
        """Validate CSV files below a client directory.

        ``client_name`` may be a direct path, or a name below ``base_path``.
        """
        self._reject_auto_fix(auto_fix)
        client_path = self._resolve_client_path(client_name)
        result = super().validate_client_directory(str(client_path), auto_fix=False)
        if output_path:
            self.save_report(result, output_path)
        return result

    def validate_client_directory(self, client_dir: str, auto_fix: bool = False) -> dict[str, Any]:
        """Validate CSV files below any supplied directory."""
        self._reject_auto_fix(auto_fix)
        return super().validate_client_directory(client_dir, auto_fix=False)

    def validate_all_clients(self, base_dir: str | None = None, auto_fix: bool = False) -> dict[str, Any]:
        """Validate all immediate child directories below the active clients root."""
        self._reject_auto_fix(auto_fix)
        return super().validate_all_clients(str(Path(base_dir) if base_dir else self.base_path), auto_fix=False)

    def _resolve_client_path(self, client_name: str) -> Path:
        direct_path = Path(client_name)
        if direct_path.exists():
            return direct_path

        under_base = self.base_path / client_name
        if under_base.exists():
            return under_base

        raise ValueError(f"Client directory not found: {client_name}")

    def _reject_auto_fix(self, auto_fix: bool) -> None:
        if auto_fix:
            raise AutoFixDisabled(
                "Auto-fix is disabled. Active validation never mutates source CSVs."
            )


def validate_csv_file(csv_path: str, auto_fix: bool = False) -> dict[str, Any]:
    """Validate one staging CSV through the legacy module name."""
    return ComprehensiveCSVValidator().validate_csv_file(csv_path, auto_fix=auto_fix)


def save_report(result: dict[str, Any], output_path: str) -> None:
    """Write a JSON report for older scripts that imported this helper."""
    Path(output_path).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Compatibility wrapper for active Google Ads Editor staging validation."
    )
    parser.add_argument("--csv", help="Validate a single Google Ads Editor staging CSV.")
    parser.add_argument("--client", help="Validate CSV files below a client directory or clients/<name>.")
    parser.add_argument("--all", action="store_true", help="Validate all client directories below clients/.")
    parser.add_argument("--fix", action="store_true", help="Rejected. Active validation never mutates CSVs.")
    parser.add_argument("--output", help="Optional JSON report path.")
    args = parser.parse_args()

    validator = ComprehensiveCSVValidator()
    try:
        if args.fix:
            raise AutoFixDisabled("Auto-fix is disabled. Active validation never mutates source CSVs.")
        if args.csv:
            report = validator.validate_csv_file(args.csv)
        elif args.client:
            report = validator.validate_client_csvs(args.client)
        elif args.all:
            report = validator.validate_all_clients()
        else:
            parser.print_help()
            raise SystemExit(2)

        if args.output:
            validator.save_report(report, args.output)
        else:
            print(json.dumps(report, indent=2))

        final_status = report.get("final_status") or report.get("client_summary", {}).get("overall_status")
        if final_status is None:
            final_status = report.get("global_summary", {}).get("overall_status")
        raise SystemExit(0 if final_status == "PASS" else 1)
    except AutoFixDisabled as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
