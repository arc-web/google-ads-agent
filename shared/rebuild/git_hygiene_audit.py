#!/usr/bin/env python3
"""Report credential-like files and generated cache noise in git status output."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


CREDENTIAL_PATTERNS = ("credentials", "google-ads.yaml", ".env", "refresh-token", "developer-token")
GENERATED_PATTERNS = ("__pycache__/", ".pyc", ".DS_Store", ".pytest_cache/")


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


def audit_status_lines(lines: list[str]) -> list[GitHygieneFinding]:
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
    parser = argparse.ArgumentParser(description="Audit git status for credentials and generated cache noise.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    findings = audit_status_lines(git_status_lines(args.root.resolve()))
    payload = {"status": "fail" if findings else "pass", "findings": [asdict(finding) for finding in findings]}
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
