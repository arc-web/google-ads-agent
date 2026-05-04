#!/usr/bin/env python3
"""Report credential-like files, generated cache noise, and unresolved removals."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


CREDENTIAL_PATTERNS = ("credentials", "google-ads.yaml", ".env", "refresh-token", "developer-token")
GENERATED_PATTERNS = ("__pycache__/", ".pyc", ".DS_Store", ".pytest_cache/")
RESOLUTION_LEDGER_GLOB = "docs/system_review/*LEDGER*.md"
REMOVAL_STATUS_CODES = {"D", "R"}


@dataclass
class GitHygieneFinding:
    path: str
    status: str
    category: str


def classify_path(path: str) -> str:
    lowered = path.lower()
    if any(pattern in lowered for pattern in CREDENTIAL_PATTERNS):
        return "credential"
    if any(pattern.lower() in lowered for pattern in GENERATED_PATTERNS):
        return "generated"
    return ""


def has_resolution_ledger(root: Path) -> bool:
    return any(path.is_file() and "TEMPLATE" not in path.name.upper() for path in root.glob(RESOLUTION_LEDGER_GLOB))


def status_requires_resolution(status: str) -> bool:
    return any(code in status for code in REMOVAL_STATUS_CODES)


def audit_status_lines(
    lines: list[str],
    *,
    require_resolution_ledger: bool = False,
    resolution_ledger_present: bool = False,
) -> list[GitHygieneFinding]:
    findings: list[GitHygieneFinding] = []
    for line in lines:
        if not line.strip():
            continue
        status = line[:2].strip()
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        category = classify_path(path)
        if category:
            findings.append(GitHygieneFinding(path=path, status=status, category=category))
        if require_resolution_ledger and status_requires_resolution(status) and not resolution_ledger_present:
            findings.append(GitHygieneFinding(path=path, status=status, category="unresolved-removal"))
    return findings


def git_status_lines(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.splitlines()


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit git status for credentials, generated cache noise, and unresolved removals.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--require-resolution-ledger",
        action="store_true",
        help="Fail deletion or rename work unless docs/system_review contains a cleanup resolution ledger.",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    findings = audit_status_lines(
        git_status_lines(root),
        require_resolution_ledger=args.require_resolution_ledger,
        resolution_ledger_present=has_resolution_ledger(root),
    )
    payload = {
        "status": "fail" if findings else "pass",
        "resolution_ledger_required": args.require_resolution_ledger,
        "resolution_ledger_present": has_resolution_ledger(root),
        "findings": [asdict(finding) for finding in findings],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        for finding in findings:
            print(f"{finding.category}: {finding.status} {finding.path}")
        if not findings:
            print("pass")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
