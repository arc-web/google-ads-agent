#!/usr/bin/env python3
"""
Audit HTML client reports for presentation risks before PDF export.

This is a static guardrail. It does not replace visual QA, but it catches
known report-design failures before hundreds of PDFs are generated from
the same weak pattern.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path


FORBIDDEN_BREAK_SELECTORS = (
    ".card",
    ".ag-review-block",
    ".card-grid",
    ".insight-grid",
    ".strategy-grid",
    ".problem-grid",
    ".roadmap",
    ".ag-grid",
    ".before-after",
    ".ag-review-cols",
    ".discussion-grid",
)

FORBIDDEN_FORCED_BREAK_SELECTORS = (
    ".ag-review-block",
    ".continuation-header",
    ".continuation-header.force-page",
    ".strategy-card",
    ".insight-card",
    ".problem-card",
    ".section + .section",
)

SECTION_HEADER_CLASSES = {"section-header"}
SUBSECTION_HEADER_CLASSES = {"subsection-header"}


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    evidence: str = ""


class ReportHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, set[str]]] = []
        self.sections: list[dict[str, int | bool]] = []
        self.current_section: dict[str, int | bool] | None = None
        self.style_text: list[str] = []
        self._in_style = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = set()
        for key, value in attrs:
            if key == "class" and value:
                classes.update(value.split())
        self.tags.append((tag, classes))

        if tag == "style":
            self._in_style = True

        if tag == "section" and "section" in classes:
            self.current_section = {
                "has_header": False,
                "section_subtitles": 0,
                "subsection_headers": 0,
                "ag_review_blocks": 0,
                "cards": 0,
                "continuation_headers": 0,
            }
            self.sections.append(self.current_section)

        if self.current_section is not None:
            if classes & SECTION_HEADER_CLASSES:
                self.current_section["has_header"] = True
            if "section-subtitle" in classes:
                self.current_section["section_subtitles"] += 1
            if classes & SUBSECTION_HEADER_CLASSES:
                self.current_section["subsection_headers"] += 1
            if "ag-review-block" in classes:
                self.current_section["ag_review_blocks"] += 1
            if "continuation-header" in classes:
                self.current_section["continuation_headers"] += 1
            if any(cls.endswith("-card") or cls == "card" for cls in classes):
                self.current_section["cards"] += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "style":
            self._in_style = False
        if tag == "section" and self.current_section is not None:
            self.current_section = None

    def handle_data(self, data: str) -> None:
        if self._in_style:
            self.style_text.append(data)


def strip_css_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def find_forbidden_break_rules(css: str) -> list[str]:
    findings: list[str] = []
    css = strip_css_comments(css)
    for selector, body in re.findall(r"([^{}]+)\{([^{}]+)\}", css):
        if "break-inside" not in body or "avoid" not in body:
            continue
        normalized_selector = " ".join(selector.split())
        for forbidden in FORBIDDEN_BREAK_SELECTORS:
            selector_parts = [part.strip() for part in normalized_selector.split(",")]
            forbidden_pattern = re.compile(rf"(^|[\s>+~]){re.escape(forbidden)}($|[\s>+~:.#[])")
            if any(forbidden_pattern.search(part) for part in selector_parts):
                findings.append(normalized_selector)
                break
    return findings


def find_forbidden_forced_break_rules(css: str) -> list[str]:
    findings: list[str] = []
    css = strip_css_comments(css)
    for selector, body in re.findall(r"([^{}]+)\{([^{}]+)\}", css):
        if not re.search(r"(?:break-before\s*:\s*page|page-break-before\s*:\s*always)", body):
            continue
        normalized_selector = " ".join(selector.split())
        selector_parts = [part.strip() for part in normalized_selector.split(",")]
        for forbidden in FORBIDDEN_FORCED_BREAK_SELECTORS:
            forbidden_pattern = re.compile(rf"(^|[\s>+~]){re.escape(forbidden)}($|[\s>+~:.#[])")
            if any(forbidden_pattern.search(part) for part in selector_parts):
                findings.append(normalized_selector)
                break
    return findings


def audit_html(path: Path) -> tuple[list[Finding], dict[str, int]]:
    parser = ReportHTMLParser()
    html_text = path.read_text(encoding="utf-8", errors="replace")
    parser.feed(html_text)

    findings: list[Finding] = []
    css = "\n".join(parser.style_text)
    classes = {cls for _tag, class_set in parser.tags for cls in class_set}

    if not parser.sections:
        findings.append(
            Finding(
                "error",
                "presentation.no_sections",
                "No top-level report sections were detected.",
            )
        )

    for index, section in enumerate(parser.sections, start=1):
        if not section["has_header"]:
            findings.append(
                Finding(
                    "error",
                    "presentation.section_missing_header",
                    "Every top-level section needs a substantial section header.",
                    f"section {index}",
                )
            )

        subtitle_count = int(section["section_subtitles"])
        subsection_header_count = int(section["subsection_headers"])
        if subtitle_count and not subsection_header_count:
            findings.append(
                Finding(
                    "warning",
                    "presentation.legacy_subtitle",
                    "Bare section subtitles can look broken when they start a PDF page. Use .subsection-header for variable or substantial content.",
                    f"section {index}, subtitles {subtitle_count}",
                )
            )

        ag_blocks = int(section["ag_review_blocks"])
        continuation_headers = int(section["continuation_headers"])
        average_blocks_per_chunk = ag_blocks / max(1, continuation_headers + 1)
        if ag_blocks > 4 and continuation_headers == 0:
            findings.append(
                Finding(
                    "warning",
                    "presentation.long_ad_review_section",
                    "Long ad-copy sections should be chunked into smaller subsections with repeated headers and summaries.",
                    f"section {index}, ad review blocks {ag_blocks}",
                )
            )
        elif average_blocks_per_chunk > 4:
            findings.append(
                Finding(
                    "warning",
                    "presentation.chunk_too_large",
                    "Ad-copy review chunks should stay small enough that page starts keep useful context.",
                    f"section {index}, average blocks per chunk {average_blocks_per_chunk:.1f}",
                )
            )

        card_count = int(section["cards"])
        if card_count > 12:
            findings.append(
                Finding(
                    "warning",
                    "presentation.dense_section",
                    "Dense sections need subsection headers, continuation labels, or a summary-first layout.",
                    f"section {index}, cards {card_count}",
                )
            )

    for selector in find_forbidden_break_rules(css):
        findings.append(
            Finding(
                "error",
                "presentation.forbidden_break_inside",
                "A grid, flex, or tall container has break-inside: avoid and may create blank pages.",
                selector,
            )
        )

    for selector in find_forbidden_forced_break_rules(css):
        findings.append(
            Finding(
                "error",
                "presentation.forbidden_forced_break",
                "Repeated modules cannot force a new page without measured page-fit logic.",
                selector,
            )
        )

    if "force-page" in classes:
        findings.append(
            Finding(
                "error",
                "presentation.force_page_class",
                "The force-page class is forbidden in client reports because it caused empty continuation pages.",
            )
        )

    if "subsection-header" not in classes:
        findings.append(
            Finding(
                "warning",
                "presentation.no_subsection_header_pattern",
                "No .subsection-header pattern was found. Variable reports need this pattern for page-start subsections.",
            )
        )

    if "continuation-header" not in classes:
        findings.append(
            Finding(
                "warning",
                "presentation.no_continuation_header_pattern",
                "No .continuation-header pattern was found. Multi-page modules need repeated context.",
            )
        )

    lower_html = html_text.lower()
    blocked_client_phrases = (
        "red counts are over the character limit",
        "flagged for rewrite",
        "run full sweep for grade",
        "why this matters:",
        "key takeaways",
        "game changer",
        "unlock growth",
        "supercharge",
        "seamlessly",
        "at-limit items",
        "exactly 30 chars",
        "may count punctuation differently",
    )
    for phrase in blocked_client_phrases:
        if phrase in lower_html:
            findings.append(
                Finding(
                    "error",
                    "presentation.client_facing_draft_language",
                    "Client-facing review contains draft-only copy QA language.",
                    phrase,
                )
            )

    if "—" in html_text:
        findings.append(
            Finding(
                "error",
                "presentation.em_dash",
                "Client-facing reports cannot use em dashes.",
            )
        )

    if re.search(r"<[^>]+class=\"[^\"]*\bgrade-pending\b", html_text):
        findings.append(
            Finding(
                "error",
                "presentation.missing_copy_grade",
                "Client-facing ad copy review cannot show missing or pending copy grades.",
            )
        )

    summary = {
        "sections": len(parser.sections),
        "errors": sum(1 for finding in findings if finding.severity == "error"),
        "warnings": sum(1 for finding in findings if finding.severity == "warning"),
    }
    return findings, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit HTML report presentation quality.")
    parser.add_argument("html", type=Path)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    findings, summary = audit_html(args.html)

    if args.json:
        print(json.dumps({"summary": summary, "findings": [asdict(f) for f in findings]}, indent=2))
    else:
        print(f"sections={summary['sections']} errors={summary['errors']} warnings={summary['warnings']}")
        for finding in findings:
            evidence = f" [{finding.evidence}]" if finding.evidence else ""
            print(f"{finding.severity.upper()} {finding.code}: {finding.message}{evidence}")

    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
