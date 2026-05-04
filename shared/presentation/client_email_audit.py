#!/usr/bin/env python3
"""Audit client email drafts for client-facing language issues."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from shared.presentation.client_language_rules import audit_client_email_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit client email draft language.")
    parser.add_argument("email", type=Path)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    findings, summary = audit_client_email_file(args.email)
    if args.json:
        print(json.dumps({"summary": summary, "findings": [asdict(finding) for finding in findings]}, indent=2))
    else:
        print(f"errors={summary['errors']} warnings={summary['warnings']}")
        for finding in findings:
            evidence = f" [{finding.evidence}]" if finding.evidence else ""
            print(f"{finding.severity.upper()} {finding.code}: {finding.message}{evidence}")
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
