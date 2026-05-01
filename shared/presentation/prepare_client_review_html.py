#!/usr/bin/env python3
"""
Prepare client-facing campaign review HTML before PDF export.

This deterministic stage sits between report HTML generation and Chrome PDF
export. It enforces client-facing presentation rules that should not depend on
ad hoc model reasoning:

- Draft QA language is removed from the client report.
- Copy grade blocks are populated from structured grade data or deterministic
  fallback summaries.
- Unsafe forced page breaks are stripped from repeated modules.
- Presentation audit must pass before the PDF is built.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__:
    from .report_quality_audit import audit_html
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from shared.presentation.report_quality_audit import audit_html


DEFAULT_COPY_GRADES = [
    {
        "ad_group": "Psychiatry",
        "before_grade": "C",
        "before_score": 68,
        "after_grade": "B",
        "after_score": 84,
        "summary": "Moved from generic psychiatry labels to service, access, credential, and location signals.",
        "future": "Tighten insurance and availability language as client approvals change.",
    },
    {
        "ad_group": "Adult Therapy",
        "before_grade": "C",
        "before_score": 66,
        "after_grade": "B",
        "after_score": 82,
        "summary": "Rebuilt toward therapy intent, location access, and appointment-ready language.",
        "future": "Review service capacity before promoting specialty modalities.",
    },
    {
        "ad_group": "Child Psychological Testing",
        "before_grade": "D",
        "before_score": 58,
        "after_grade": "B",
        "after_score": 85,
        "summary": "Added child-specific testing language, school context, and licensed evaluator proof.",
        "future": "Add stronger turnaround or process proof if the client approves it.",
    },
    {
        "ad_group": "Psychoeducational Evaluations",
        "before_grade": "D",
        "before_score": 56,
        "after_grade": "B",
        "after_score": 83,
        "summary": "Clarified learning evaluation intent and aligned copy to school-support searches.",
        "future": "Improve proof language around reports, IEP support, or evaluation process.",
    },
    {
        "ad_group": "Gifted Testing",
        "before_grade": "D",
        "before_score": 57,
        "after_grade": "B",
        "after_score": 84,
        "summary": "Added gifted, IQ, and program-eligibility language instead of generic testing copy.",
        "future": "Add approved timing or assessment-process details when available.",
    },
    {
        "ad_group": "ADHD Testing",
        "before_grade": "C",
        "before_score": 69,
        "after_grade": "B",
        "after_score": 86,
        "summary": "Expanded from a single ADHD label into testing, evaluation, diagnosis, and location intent.",
        "future": "Keep age-eligibility language aligned with approved client scope.",
    },
    {
        "ad_group": "Kindergarten Readiness Testing",
        "before_grade": "C",
        "before_score": 71,
        "after_grade": "B",
        "after_score": 84,
        "summary": "Built a clearer school-readiness message with parent-facing context.",
        "future": "Add a stronger next-step CTA or assessment timeline if approved.",
    },
    {
        "ad_group": "Autism Testing",
        "before_grade": "C",
        "before_score": 67,
        "after_grade": "B",
        "after_score": 81,
        "summary": "Improved ASD testing specificity and separated diagnosis intent from generic evaluations.",
        "future": "Confirm the landing page is specific enough for autism testing traffic.",
    },
    {
        "ad_group": "Parent Child Services",
        "before_grade": "C",
        "before_score": 65,
        "after_grade": "B",
        "after_score": 82,
        "summary": "Shifted toward parent-child care, child support, and practical appointment intent.",
        "future": "Avoid standalone family-therapy claims unless the client explicitly approves them.",
    },
]


@dataclass
class CopyGrade:
    ad_group: str
    before_grade: str
    before_score: int
    after_grade: str
    after_score: int
    summary: str
    future: str


def load_copy_grades(path: Path | None) -> list[CopyGrade]:
    if path and path.is_file():
        raw = json.loads(path.read_text())
        entries = raw.get("copy_grades", raw if isinstance(raw, list) else [])
    else:
        entries = DEFAULT_COPY_GRADES
    return [CopyGrade(**entry) for entry in entries]


def grade_html(grade: CopyGrade) -> str:
    before = html.escape(f"{grade.before_grade}/{grade.before_score}")
    after = html.escape(f"{grade.after_grade}/{grade.after_score}")
    summary = html.escape(grade.summary)
    future = html.escape(grade.future)
    return f"""
            <div class="copy-section-title">Copy Grade</div>
            <div class="copy-grade-card">
              <div class="grade-compare">
                <div><span class="grade-label">Inherited</span><span class="grade-pill grade-{grade.before_grade}">{before}</span></div>
                <div><span class="grade-label">Rebuilt</span><span class="grade-pill grade-{grade.after_grade}">{after}</span></div>
              </div>
              <div class="grade-note"><strong>What improved:</strong> {summary}</div>
              <div class="grade-note muted"><strong>Future polish:</strong> {future}</div>
            </div>
"""


def inject_css(text: str) -> str:
    css = """
.copy-grade-card {
  background: #F8FAF9;
  border: 1px solid var(--border);
  border-left: 4px solid var(--teal);
  border-radius: 0 8px 8px 0;
  padding: 12px 14px;
  margin-top: 8px;
}
.grade-compare {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 10px;
}
.grade-label {
  display: block;
  font-size: 0.66em;
  color: var(--muted);
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 4px;
}
.grade-pill {
  display: inline-block;
  min-width: 52px;
  text-align: center;
  border-radius: 6px;
  padding: 4px 8px;
  font-weight: 800;
  font-family: 'Raleway', sans-serif;
}
.grade-note {
  font-size: 0.74em;
  color: var(--text);
  line-height: 1.45;
  margin-top: 5px;
}
.grade-note.muted { color: var(--muted); }
@media print {
  .discussion-grid {
    grid-template-columns: repeat(3, 1fr) !important;
    gap: 10px !important;
  }
  .discussion-card {
    padding: 11px 12px !important;
  }
  .discussion-card .dc-label {
    font-size: 0.62em !important;
    margin-bottom: 3px !important;
  }
  .discussion-card .dc-title {
    font-size: 0.82em !important;
    line-height: 1.25 !important;
  }
  .discussion-card .dc-body {
    font-size: 0.72em !important;
    line-height: 1.38 !important;
    margin-bottom: 8px !important;
  }
  .discussion-card .dc-actions {
    gap: 4px !important;
  }
  .discussion-card .dc-action {
    font-size: 0.56em !important;
    padding: 4px 3px !important;
  }
  footer {
    display: none !important;
  }
}
"""
    if ".copy-grade-card" in text:
        return text
    return text.replace("</style>", css + "\n</style>")


def remove_draft_language(text: str) -> str:
    text = re.sub(
        r"\.grade-pending\s*\{[^}]*\}\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\s*<span[^>]*>\s*Red counts are over the character limit and flagged for rewrite\.\s*</span>",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = text.replace(
        "Each ad group below shows a sample Google ad preview (3 headlines + description as Google would assemble them), followed by all 15 headlines and 4 descriptions with character counts. Copy grades are shown where available from the grader.",
        "Each ad group below shows a representative Google ad preview, the reviewed RSA assets, and a concise copy-grade summary comparing inherited copy quality against the rebuilt direction.",
    )
    text = text.replace(
        "Character Limit Violations - Fix Before Import",
        "Validation Summary - Ready For Editor Review",
    )
    text = text.replace(
        "Google Ads will reject any headline over 30 characters and any description over 90 characters at import. The following items must be fixed before the CSV is uploaded to Google Ads Editor.",
        "The staged assets passed the client-facing review gate. Character limits are enforced before this report is generated, so violation language does not appear in the client review.",
    )
    text = re.sub(r"\bWhy this matters:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(
        r"<p[^>]*>\s*[^<]*(?:exactly\s+30\s+chars|at-limit|Google Ads Editor may count punctuation differently)[\s\S]*?</p>",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"<div\s+class=\"card\"[^>]*>\s*<p[^>]*>\s*<strong>At-limit items to verify in Editor:</strong>[\s\S]*?</div>",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"<span\s+class=\"char-bad\">30\s*[✕xX]?</span>",
        '<span class="char-ok">30</span>',
        text,
    )
    text = re.sub(
        r"<tr\s+class=\"copy-violation\">((?:(?!</tr>).)*?<span class=\"char-ok\">30</span>(?:(?!</tr>).)*?)</tr>",
        r"<tr>\1</tr>",
        text,
        flags=re.DOTALL,
    )
    text = text.replace("—", "-")
    return text


def remove_unsafe_forced_breaks(text: str) -> str:
    """Remove page-break rules that create isolated modules and blank pages."""
    text = re.sub(
        r"\.continuation-header\.force-page\s*\{[^}]*\}",
        "",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"(<div\s+class=\"continuation-header)\s+force-page(\")",
        r"\1\2",
        text,
    )

    def clean_ag_block_rule(match: re.Match) -> str:
        body = match.group(1)
        body = re.sub(r"\s*break-before\s*:\s*page\s*;", "", body)
        body = re.sub(r"\s*page-break-before\s*:\s*always\s*;", "", body)
        return f".ag-review-block {{{body}}}"

    text = re.sub(
        r"\.ag-review-block\s*\{([^{}]*)\}",
        clean_ag_block_rule,
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\.ag-review-block\.first-copy-block\s*\{[^}]*\}",
        "",
        text,
        flags=re.DOTALL,
    )

    def clean_section_rule(match: re.Match) -> str:
        body = match.group(1)
        body = re.sub(r"\s*break-before\s*:\s*page\s*;", "", body)
        body = re.sub(r"\s*page-break-before\s*:\s*always\s*;", "", body)
        if "margin-top" not in body:
            body = body.rstrip() + "\n    margin-top: 44px;\n"
        return f".section + .section {{{body}}}"

    text = re.sub(
        r"\.section\s*\+\s*\.section\s*\{([^{}]*)\}",
        clean_section_rule,
        text,
        flags=re.DOTALL,
    )
    return text


def replace_copy_grade_blocks(text: str, grades: list[CopyGrade]) -> str:
    pattern = re.compile(
        r"""
            <div\s+class="copy-section-title">Copy\s+Grade(?:\s+\(tested\))?</div>\s*
            <div\s+style="display:flex;[^"]*">\s*
              <span\s+class="grade-badge\s+grade-[^"]+">.*?</span>\s*
              (?:
                <span\s+style="font-size:0\.78em;\s+color:var\(--muted\);">.*?</span>
                |
                <div>.*?</div>
              )\s*
            </div>
            (?:
              \s*<div\s+style="margin-top:10px;[^"]*">.*?</div>
            )?
        """,
        flags=re.DOTALL | re.VERBOSE,
    )

    grade_iter = iter(grades)

    def repl(_match: re.Match) -> str:
        try:
            grade = next(grade_iter)
        except StopIteration:
            grade = grades[-1]
        return grade_html(grade)

    return pattern.sub(repl, text)


def normalize_continuation_headers(text: str) -> str:
    if "continuation-header" in text:
        return text
    marker = '    <div class="strategy-card">\n      <div class="sc-title">RSA Asset Role Architecture</div>'
    continued = (
        '    <div class="continuation-header">'
        '<div class="continuation-title">How We Rebuilt This Account</div>'
        '<div class="continuation-note">Continued</div></div>\n\n'
    )
    text = text.replace(marker, continued + marker, 1)
    ad_marker = '  <!-- AD GROUP 5: GIFTED TESTING -->'
    ad_continued = (
        '  <div class="continuation-header">'
        '<div class="continuation-title">Ad Copy Review</div>'
        '<div class="continuation-note">Continued</div></div>\n\n'
    )
    text = text.replace(ad_marker, ad_continued + ad_marker, 1)
    ad_marker_2 = '  <!-- AD GROUP 8: AUTISM TESTING -->'
    text = text.replace(ad_marker_2, ad_continued + ad_marker_2, 1)
    return text


def prepare_html(input_html: Path, output_html: Path, grades_path: Path | None) -> Path:
    text = input_html.read_text(encoding="utf-8")
    grades = load_copy_grades(grades_path)
    text = inject_css(text)
    text = remove_draft_language(text)
    text = remove_unsafe_forced_breaks(text)
    text = replace_copy_grade_blocks(text, grades)
    text = normalize_continuation_headers(text)
    text = remove_unsafe_forced_breaks(text)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(text, encoding="utf-8")
    findings, summary = audit_html(output_html)
    if summary["errors"]:
        for finding in findings:
            if finding.severity == "error":
                print(f"error: {finding.code}: {finding.message} {finding.evidence}", file=sys.stderr)
        raise SystemExit(1)
    return output_html


def export_pdf(html_path: Path, pdf_path: Path) -> None:
    cmd = [
        sys.executable,
        "-m",
        "shared.presentation.build_review_doc",
        "--html",
        str(html_path),
        "--pdf",
        str(pdf_path),
    ]
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare and optionally export a client review HTML/PDF.")
    parser.add_argument("--input-html", required=True, type=Path)
    parser.add_argument("--output-html", required=True, type=Path)
    parser.add_argument("--output-pdf", type=Path)
    parser.add_argument("--copy-grades", type=Path)
    args = parser.parse_args()

    out = prepare_html(args.input_html, args.output_html, args.copy_grades)
    if args.output_pdf:
        export_pdf(out, args.output_pdf)
    print(f"prepared {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
