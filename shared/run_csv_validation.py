#!/usr/bin/env python3
"""Run active Google Ads Editor staging validation through legacy CLI names."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.comprehensive_csv_validator import AutoFixDisabled, ComprehensiveCSVValidator


def _status_for(result: dict[str, Any]) -> str:
    return (
        result.get("final_status")
        or result.get("client_summary", {}).get("overall_status")
        or result.get("global_summary", {}).get("overall_status")
        or "FAIL"
    )


def _write_report(result: dict[str, Any], output_path: str | None) -> None:
    output = json.dumps(result, indent=2)
    if output_path:
        Path(output_path).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)


def _workflow_status(client: str, validator: ComprehensiveCSVValidator) -> dict[str, Any]:
    client_path = validator._resolve_client_path(client)
    csv_files = validator._find_csv_files(client_path)
    return {
        "client": client,
        "directory": str(client_path),
        "candidate_csvs": [str(path) for path in csv_files],
        "validation_authority": "shared/rebuild/staging_validator.py",
        "source_mutation": "disabled",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Google Ads Editor staging files without mutating source CSVs.",
    )
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--csv", help="Validate one Google Ads Editor staging CSV.")
    target.add_argument("--client", help="Validate CSV files below a client directory or clients/<name>.")
    target.add_argument("--all", action="store_true", help="Validate all client directories below clients/.")
    target.add_argument("--workflow-status", help="List validation candidates for a client without changing files.")
    target.add_argument("--monitor-new", help="Compatibility alias for --client. Does not stage or mutate files.")
    parser.add_argument("--fix", action="store_true", help="Rejected. Active validation never mutates CSVs.")
    parser.add_argument("--mark-final", help="Rejected. Stage mutation is disabled in this compatibility runner.")
    parser.add_argument("--output", help="Optional JSON report path.")
    parser.add_argument("--output-dir", help="Optional directory for --all report output.")
    parser.add_argument("--json-output", help="Optional JSON report path for --csv compatibility.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Accepted for compatibility.")
    args = parser.parse_args()

    del args.verbose
    validator = ComprehensiveCSVValidator()

    try:
        if args.fix:
            raise AutoFixDisabled("Auto-fix is disabled. Active validation never mutates source CSVs.")
        if args.mark_final:
            raise AutoFixDisabled("Stage mutation is disabled. This runner validates only.")

        output_path = args.json_output or args.output
        if args.csv:
            result = validator.validate_csv_file(args.csv)
        elif args.client:
            result = validator.validate_client_csvs(args.client)
        elif args.monitor_new:
            result = validator.validate_client_csvs(args.monitor_new)
        elif args.workflow_status:
            result = _workflow_status(args.workflow_status, validator)
        elif args.all:
            result = validator.validate_all_clients()
            if args.output_dir:
                output_dir = Path(args.output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / "validation_report.json")
        else:
            parser.print_help()
            return 2

        _write_report(result, output_path)
        if args.workflow_status:
            return 0
        return 0 if _status_for(result) == "PASS" else 1
    except AutoFixDisabled as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Validation runner failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
