#!/usr/bin/env python3
"""Audit Python files for client-specific assumptions in shared code."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_BLOCKED_PATTERNS = [
    "thinkhappylivehealthy",
    "think happy live healthy",
    "thhl",
    "therappc",
    "wright",
    "myexpertresume",
    "my expert resume",
    "my_expert_resume",
    "/users/home/",
    "arc - search -",
]

DEFAULT_SHARED_ROOTS = ["shared", "presentations/tools"]


@dataclass
class BoundaryFinding:
    file: str
    line: int
    pattern: str
    text: str


def iter_python_files(root: Path, scan_roots: list[str]) -> list[Path]:
    files: list[Path] = []
    for scan_root in scan_roots:
        path = root / scan_root
        if not path.exists():
            continue
        files.extend(sorted(path.rglob("*.py")))
    return files


def audit_files(root: Path, files: list[Path], patterns: list[str]) -> list[BoundaryFinding]:
    findings: list[BoundaryFinding] = []
    lowered_patterns = [pattern.lower() for pattern in patterns]
    for file_path in files:
        if file_path.name == "code_boundary_audit.py":
            continue
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line_number, line in enumerate(lines, start=1):
            lowered_line = line.lower()
            for pattern in lowered_patterns:
                if pattern in lowered_line:
                    findings.append(
                        BoundaryFinding(
                            file=str(file_path.relative_to(root)),
                            line=line_number,
                            pattern=pattern,
                            text=line.strip(),
                        )
                    )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit shared Python code for client-specific assumptions.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument(
        "--scan-root",
        action="append",
        default=[],
        help="Directory to scan. May be repeated. Defaults to shared and presentations/tools.",
    )
    parser.add_argument(
        "--pattern",
        action="append",
        default=[],
        help="Blocked client-specific pattern. May be repeated.",
    )
    parser.add_argument("--json-output", help="Optional path to write audit JSON.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    scan_roots = args.scan_root or DEFAULT_SHARED_ROOTS
    patterns = args.pattern or DEFAULT_BLOCKED_PATTERNS
    files = iter_python_files(root, scan_roots)
    findings = audit_files(root, files, patterns)
    output = {
        "status": "fail" if findings else "pass",
        "scanned_files": len(files),
        "scan_roots": scan_roots,
        "blocked_patterns": patterns,
        "findings": [asdict(finding) for finding in findings],
    }

    if args.json_output:
        Path(args.json_output).write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    else:
        print(json.dumps(output, indent=2))

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
