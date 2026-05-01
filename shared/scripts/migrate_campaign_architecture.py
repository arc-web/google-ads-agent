#!/usr/bin/env python3
"""Audit legacy campaign-architecture migration status without mutating files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
ACTIVE_CONTRACTS = {
    "staging_validator": "shared/rebuild/staging_validator.py",
    "search_campaign_builder": "shared/tools/campaign/search_campaign_builder.py",
    "search_exporter": "shared/gads/core/business_logic/google_ads_editor_exporter.py",
}
LEGACY_MUTATION_MESSAGE = (
    "This migration script is inactive. It audits legacy migration assumptions only "
    "and does not create directories, copy files, or rewrite source code."
)


class CampaignArchitectureMigrator:
    """Audit old migration assumptions against the current Search-first system."""

    def __init__(self, root_dir: Path = ROOT_DIR):
        self.root_dir = root_dir

    def analyze_current_architecture(self) -> dict[str, Any]:
        """Return a non-mutating inventory of current architecture status."""
        expected_active_files = {
            name: {
                "path": path,
                "exists": (self.root_dir / path).exists(),
            }
            for name, path in ACTIVE_CONTRACTS.items()
        }
        stale_targets = [
            "validators/search_campaign",
            "validators/pmax_campaign",
            "tools/campaign/search",
            "tools/campaign/pmax",
            "docs/search_campaigns",
            "docs/pmax_campaigns",
        ]
        return {
            "mode": "audit_only",
            "mutations_enabled": False,
            "root_dir": str(self.root_dir),
            "active_contracts": expected_active_files,
            "inactive_migration_targets": [
                {
                    "path": target,
                    "exists": (self.root_dir / target).exists(),
                    "reason": "Old separated-directory migration target, not active workflow authority.",
                }
                for target in stale_targets
            ],
            "current_policy": {
                "campaign_type": "Search",
                "match_type": "Phrase",
                "staging": "Google Ads Editor",
                "api_upload": "off",
            },
        }

    def run_migration(self) -> None:
        """Reject legacy mutation mode."""
        raise RuntimeError(LEGACY_MUTATION_MESSAGE)

    def validate_migration(self) -> dict[str, Any]:
        """Validate that active contracts exist without changing files."""
        report = self.analyze_current_architecture()
        missing = [
            item["path"]
            for item in report["active_contracts"].values()
            if not item["exists"]
        ]
        report["status"] = "fail" if missing else "pass"
        report["missing_active_contracts"] = missing
        return report


def _write_json(report: dict[str, Any], output_path: str | None) -> None:
    output = json.dumps(report, indent=2)
    if output_path:
        Path(output_path).write_text(output + "\n", encoding="utf-8")
    else:
        print(output)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit legacy campaign architecture migration status without mutating files."
    )
    parser.add_argument("--analyze", action="store_true", help="Print a non-mutating architecture audit.")
    parser.add_argument("--validate", action="store_true", help="Validate active contract files exist.")
    parser.add_argument("--migrate", action="store_true", help="Rejected. Legacy migration is inactive.")
    parser.add_argument("--json-output", help="Optional JSON output path for audit or validation results.")
    args = parser.parse_args()

    migrator = CampaignArchitectureMigrator()
    try:
        if args.migrate:
            migrator.run_migration()
        elif args.validate:
            report = migrator.validate_migration()
            _write_json(report, args.json_output)
            return 0 if report["status"] == "pass" else 1
        else:
            report = migrator.analyze_current_architecture()
            _write_json(report, args.json_output)
            return 0
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
