#!/usr/bin/env python3
"""Validate that previous-provider tokens do not leak into generated outputs."""

from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree


DEFAULT_BLOCKED_FIELDS = [
    "Campaign",
    "Ad Group",
    "Keyword",
    "Final URL",
    "Path 1",
    "Path 2",
    "Headline",
    "Description",
]


def token_re(tokens: list[str]) -> re.Pattern[str]:
    escaped = [re.escape(t) for t in tokens if t.strip()]
    if not escaped:
        raise ValueError("At least one provider token is required")
    return re.compile("|".join(escaped), re.IGNORECASE)


def read_text(path: Path) -> str:
    for encoding in ("utf-16", "utf-8-sig", "utf-8", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeError:
            continue
    return path.read_bytes().decode("utf-8", errors="ignore")


def read_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as docx:
        raw = docx.read("word/document.xml")
    root = ElementTree.fromstring(raw)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    return "\n".join(node.text or "" for node in root.findall(".//w:t", ns))


def is_blocked_field(field: str, blocked_fields: list[str]) -> bool:
    normalized = field.strip().lower()
    for blocked in blocked_fields:
        b = blocked.strip().lower()
        if normalized == b or normalized.startswith(f"{b} "):
            return True
    return False


def validate_csv(path: Path, pattern: re.Pattern[str], blocked_fields: list[str]) -> list[dict[str, str]]:
    text = read_text(path)
    dialect = csv.excel_tab if "\t" in text.splitlines()[0] else csv.excel
    reader = csv.DictReader(text.splitlines(), dialect=dialect)
    findings: list[dict[str, str]] = []
    for row_num, row in enumerate(reader, start=2):
        for field, value in row.items():
            if not field or not value or not is_blocked_field(field, blocked_fields):
                continue
            match = pattern.search(value)
            if match:
                findings.append(
                    {
                        "file": str(path),
                        "row": str(row_num),
                        "field": field,
                        "token": match.group(0),
                        "value": value,
                    }
                )
    return findings


def validate_text_file(path: Path, pattern: re.Pattern[str]) -> list[dict[str, str]]:
    text = read_docx_text(path) if path.suffix.lower() == ".docx" else read_text(path)
    findings: list[dict[str, str]] = []
    for line_num, line in enumerate(text.splitlines(), start=1):
        match = pattern.search(line)
        if match:
            findings.append(
                {
                    "file": str(path),
                    "line": str(line_num),
                    "field": "text",
                    "token": match.group(0),
                    "value": line.strip(),
                }
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Block previous-provider token leakage in generated outputs")
    parser.add_argument("--token", action="append", required=True, help="Provider token to block. May be repeated.")
    parser.add_argument("--file", action="append", required=True, help="Generated file to validate. May be repeated.")
    parser.add_argument("--blocked-field", action="append", default=[], help="CSV field to scan. Defaults to generated ad fields.")
    parser.add_argument("--json-output", help="Optional path for validation findings JSON.")
    args = parser.parse_args()

    pattern = token_re(args.token)
    blocked_fields = args.blocked_field or DEFAULT_BLOCKED_FIELDS
    findings: list[dict[str, str]] = []

    for file_name in args.file:
        path = Path(file_name)
        if path.suffix.lower() in {".csv", ".tsv"}:
            findings.extend(validate_csv(path, pattern, blocked_fields))
        else:
            findings.extend(validate_text_file(path, pattern))

    output = {
        "status": "failed" if findings else "passed",
        "blocked_tokens": args.token,
        "findings": findings,
    }

    if args.json_output:
        Path(args.json_output).write_text(json.dumps(output, indent=2), encoding="utf-8")
    else:
        print(json.dumps(output, indent=2))

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
