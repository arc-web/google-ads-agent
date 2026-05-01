"""
Human-in-the-loop HTML review report generator for the google_ads_agent copy engine.

Generates a self-contained, inline-CSS HTML report covering:
  A - Sweep Grades table (per asset, per ad group)
  B - Gap Analysis (mix gaps, char violations, policy flags, word swaps)
  C - Side-by-Side Proposals (current vs. proposed copy)
  D - Build Checklist (what will be generated upon approval)

Usage:
    reporter = HITLReporter()
    path = reporter.generate(client_ctx, grade_reports, eval_reports,
                             current_copy, proposed_copy, build_plan)
    # caller opens path
"""

from __future__ import annotations

import datetime
import html
import os
from pathlib import Path
from copy_engine.editor.grader import GradeReport
from copy_engine.editor.evaluator import EvalReport
from copy_engine.context import ClientContext


# ---------------------------------------------------------------------------
# Grade colour mapping
# ---------------------------------------------------------------------------

_GRADE_COLORS: dict[str, tuple[str, str]] = {
    # grade -> (background, text)
    "A": ("#16a34a", "#ffffff"),
    "B": ("#2563eb", "#ffffff"),
    "C": ("#ca8a04", "#ffffff"),
    "D": ("#ea580c", "#ffffff"),
    "F": ("#dc2626", "#ffffff"),
}


def _grade_badge(grade: str) -> str:
    bg, fg = _GRADE_COLORS.get(grade, ("#6b7280", "#ffffff"))
    return (
        f'<span style="display:inline-block;padding:2px 9px;border-radius:4px;'
        f'background:{bg};color:{fg};font-weight:700;font-size:0.85em;">'
        f"{html.escape(grade)}</span>"
    )


def _trunc(text: str, n: int = 50) -> str:
    """Truncate text to n chars, adding ellipsis if cut."""
    if len(text) <= n:
        return html.escape(text)
    return html.escape(text[:n]) + "&hellip;"


# ---------------------------------------------------------------------------
# Global CSS / page chrome
# ---------------------------------------------------------------------------

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    font-size: 14px;
    background: #f3f4f6;
    color: #1f2937;
    line-height: 1.5;
}
header {
    background: #1a1a2e;
    color: #e2e8f0;
    padding: 24px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
header h1 { font-size: 1.4em; font-weight: 700; letter-spacing: 0.03em; }
header .meta { font-size: 0.82em; color: #94a3b8; text-align: right; }
.wrapper { max-width: 1200px; margin: 28px auto; padding: 0 24px 60px; }
.section {
    background: #ffffff;
    border-radius: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    margin-bottom: 28px;
    overflow: hidden;
}
.section-header {
    background: #1e293b;
    color: #f1f5f9;
    padding: 12px 20px;
    font-size: 1em;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.section-body { padding: 20px; }
.ad-group-title {
    font-size: 1em;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 2px solid #e2e8f0;
}
.ad-group-block { margin-bottom: 26px; }
.ad-group-block:last-child { margin-bottom: 0; }
table { width: 100%; border-collapse: collapse; font-size: 0.88em; }
th {
    background: #f8fafc;
    text-align: left;
    padding: 8px 10px;
    font-weight: 600;
    color: #475569;
    border-bottom: 1px solid #e2e8f0;
    white-space: nowrap;
}
td {
    padding: 7px 10px;
    border-bottom: 1px solid #f1f5f9;
    vertical-align: top;
}
tr:last-child td { border-bottom: none; }
.mono { font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace; }
.issues-list { list-style: disc; margin-left: 18px; }
.issues-list li { color: #dc2626; font-size: 0.82em; margin-top: 3px; }
.gap-list { list-style: none; padding: 0; }
.gap-list li { padding: 4px 0; }
.gap-tag {
    display: inline-block;
    font-size: 0.75em;
    font-weight: 700;
    padding: 1px 7px;
    border-radius: 3px;
    margin-right: 6px;
    vertical-align: middle;
}
.tag-mix    { background: #dbeafe; color: #1d4ed8; }
.tag-char   { background: #fef3c7; color: #92400e; }
.tag-policy { background: #fee2e2; color: #991b1b; }
.tag-swap   { background: #f0fdf4; color: #166534; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.copy-box {
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 12px 14px;
    background: #f9fafb;
}
.copy-box h4 {
    font-size: 0.78em;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
    margin-bottom: 8px;
}
.copy-item {
    font-family: "SFMono-Regular", Consolas, monospace;
    font-size: 0.82em;
    padding: 3px 0;
    border-bottom: 1px solid #f1f5f9;
    color: #1e293b;
}
.copy-item:last-child { border-bottom: none; }
.copy-item.changed { background: #fef9c3; border-radius: 3px; padding: 3px 5px; }
.copy-item.pending { color: #94a3b8; font-style: italic; }
.copy-new-badge {
    display: inline-block;
    font-size: 0.72em;
    font-weight: 700;
    padding: 1px 6px;
    background: #dbeafe;
    color: #1e40af;
    border-radius: 3px;
    margin-right: 4px;
    font-style: normal;
    font-family: -apple-system, sans-serif;
}
.checklist { list-style: none; padding: 0; }
.checklist li {
    padding: 5px 0;
    display: flex;
    align-items: center;
    gap: 9px;
    border-bottom: 1px solid #f1f5f9;
    font-size: 0.9em;
}
.checklist li:last-child { border-bottom: none; }
.checklist input[type=checkbox] {
    width: 15px;
    height: 15px;
    accent-color: #2563eb;
    cursor: pointer;
}
.clean-badge {
    display: inline-block;
    font-size: 0.78em;
    font-weight: 600;
    color: #16a34a;
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    padding: 2px 8px;
    border-radius: 3px;
}
"""


def _page_open(agency: str, client: str, date_str: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Copy Review - {html.escape(client)} - {html.escape(date_str)}</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <h1>Copy Review Report</h1>
  <div class="meta">
    <div><strong>{html.escape(client)}</strong></div>
    <div>Agency: {html.escape(agency)}</div>
    <div>{html.escape(date_str)}</div>
  </div>
</header>
<div class="wrapper">
"""


def _page_close() -> str:
    return "</div>\n</body>\n</html>\n"


# ---------------------------------------------------------------------------
# HITLReporter
# ---------------------------------------------------------------------------


class HITLReporter:
    """
    Generates a self-contained HTML human-in-the-loop review report.

    Call generate() and the file path is returned. Caller is responsible
    for opening the file - no os.system() calls here.
    """

    def __init__(self, base_path: str | None = None) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        self.base_path = os.fspath(Path(base_path).resolve() if base_path else repo_root)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def generate(
        self,
        client_ctx: ClientContext,
        grade_reports: dict,
        # {ad_group_name: {headlines: [GradeReport], descriptions: [GradeReport]}}
        eval_reports: dict,
        # {ad_group_name: EvalReport}
        current_copy: dict,
        # {ad_group_name: {headlines: [str], descriptions: [str]}}
        proposed_copy: dict,
        # same structure, from generators - can be empty {}
        build_plan: dict,
        # {ad_group_name: {headlines: N, descriptions: N, sitelinks: N, callouts: N}}
    ) -> str:
        """
        Build the HTML report and write it to:
          <base_path>/clients/<agency>/<client>/reports/<client>_copy_review_<date>.html

        Returns the absolute path to the created file.
        """
        date_str = datetime.date.today().isoformat()
        agency = client_ctx.agency
        client = client_ctx.client

        out_dir = os.path.join(
            self.base_path, "clients", agency, client, "reports"
        )
        os.makedirs(out_dir, exist_ok=True)

        filename = f"{client}_copy_review_{date_str}.html"
        out_path = os.path.join(out_dir, filename)

        parts: list[str] = [
            _page_open(agency, client, date_str),
            self._section_a(grade_reports),
            self._section_b(eval_reports),
            self._section_c(current_copy, proposed_copy),
            self._section_d(build_plan),
            _page_close(),
        ]

        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("".join(parts))

        return out_path

    # ------------------------------------------------------------------
    # Section A - Sweep Grades
    # ------------------------------------------------------------------

    def _section_a(self, grade_reports: dict) -> str:
        rows: list[str] = ['<div class="section">']
        rows.append('<div class="section-header">A - Sweep Grades</div>')
        rows.append('<div class="section-body">')

        if not grade_reports:
            rows.append("<p>No grade data provided.</p>")
            rows.append("</div></div>")
            return "".join(rows)

        for ad_group, components in grade_reports.items():
            rows.append('<div class="ad-group-block">')
            rows.append(
                f'<div class="ad-group-title">{html.escape(str(ad_group))}</div>'
            )
            rows.append(
                "<table>"
                "<thead><tr>"
                "<th>Type</th>"
                "<th>Asset Text</th>"
                "<th>Score</th>"
                "<th>Grade</th>"
                "<th>Top Issues</th>"
                "</tr></thead>"
                "<tbody>"
            )

            for component, reports in components.items():
                if not isinstance(reports, list):
                    continue
                for report in reports:
                    if not isinstance(report, GradeReport):
                        continue
                    issues_html = self._render_issues(report.top_issues[:2])
                    rows.append(
                        f"<tr>"
                        f'<td>{html.escape(str(component))}</td>'
                        f'<td class="mono">{_trunc(report.asset_text, 50)}</td>'
                        f"<td>{report.overall_score}</td>"
                        f"<td>{_grade_badge(report.overall_grade)}</td>"
                        f"<td>{issues_html}</td>"
                        f"</tr>"
                    )

            rows.append("</tbody></table>")
            rows.append("</div>")  # ad-group-block

        rows.append("</div></div>")
        return "".join(rows)

    def _render_issues(self, issues: list[str]) -> str:
        if not issues:
            return '<span style="color:#6b7280;font-size:0.82em;">None</span>'
        items = "".join(
            f"<li>{html.escape(str(i))}</li>" for i in issues
        )
        return f'<ul class="issues-list">{items}</ul>'

    # ------------------------------------------------------------------
    # Section B - Gap Analysis
    # ------------------------------------------------------------------

    def _section_b(self, eval_reports: dict) -> str:
        rows: list[str] = ['<div class="section">']
        rows.append('<div class="section-header">B - Gap Analysis</div>')
        rows.append('<div class="section-body">')

        if not eval_reports:
            rows.append("<p>No evaluation data provided.</p>")
            rows.append("</div></div>")
            return "".join(rows)

        for ad_group, report in eval_reports.items():
            if not isinstance(report, EvalReport):
                continue
            rows.append('<div class="ad-group-block">')
            rows.append(
                f'<div class="ad-group-title">{html.escape(str(ad_group))}</div>'
            )

            if report.is_clean and not report.word_swaps:
                rows.append('<span class="clean-badge">All clear - no gaps found</span>')
                rows.append("</div>")
                continue

            rows.append('<ul class="gap-list">')

            # Mix gaps
            for gap in report.mix_gaps:
                label = html.escape(gap.missing_type.replace("_", " ").title())
                rows.append(
                    f'<li><span class="gap-tag tag-mix">MIX</span>'
                    f"Missing <strong>{label}</strong>: "
                    f"need {gap.required_count}, have {gap.actual_count}</li>"
                )

            # Char violations
            for cv in report.char_violations:
                rows.append(
                    f'<li><span class="gap-tag tag-char">CHAR</span>'
                    f'<span class="mono">{_trunc(cv.text, 40)}</span> - '
                    f"{cv.actual_chars} chars (limit {cv.limit})</li>"
                )

            # Policy flags
            for pf in report.policy_flags:
                rows.append(
                    f'<li><span class="gap-tag tag-policy">POLICY</span>'
                    f"<strong>{html.escape(pf.flagged_term)}</strong> - "
                    f"{html.escape(pf.reason)}</li>"
                )

            # Word swap suggestions
            for ws in report.word_swaps:
                rows.append(
                    f'<li><span class="gap-tag tag-swap">SWAP</span>'
                    f"Replace <strong>{html.escape(ws.original_word)}</strong> "
                    f"with <strong>{html.escape(ws.suggested_word)}</strong></li>"
                )

            rows.append("</ul>")
            rows.append("</div>")  # ad-group-block

        rows.append("</div></div>")
        return "".join(rows)

    # ------------------------------------------------------------------
    # Section C - Side-by-Side Proposals
    # ------------------------------------------------------------------

    def _section_c(self, current_copy: dict, proposed_copy: dict) -> str:
        rows: list[str] = ['<div class="section">']
        rows.append('<div class="section-header">C - Side-by-Side Proposals</div>')
        rows.append('<div class="section-body">')

        # Gather all ad groups across both dicts
        all_groups = sorted(
            set(list(current_copy.keys()) + list(proposed_copy.keys()))
        )

        if not all_groups:
            rows.append("<p>No copy data provided.</p>")
            rows.append("</div></div>")
            return "".join(rows)

        for ad_group in all_groups:
            cur = current_copy.get(ad_group, {})
            prop = proposed_copy.get(ad_group, {})
            is_new = ad_group not in current_copy

            rows.append('<div class="ad-group-block">')
            rows.append(
                f'<div class="ad-group-title">{html.escape(str(ad_group))}</div>'
            )
            rows.append('<div class="two-col">')

            # Left - current
            rows.append('<div class="copy-box">')
            rows.append(
                '<h4>Current Copy</h4>'
                if not is_new
                else '<h4>Current Copy <span style="color:#2563eb;font-size:0.9em;">(NEW)</span></h4>'
            )
            if not cur:
                rows.append('<p class="copy-item pending">No existing copy</p>')
            else:
                rows.extend(self._copy_items(cur, highlight_set=set()))
            rows.append("</div>")

            # Right - proposed
            rows.append('<div class="copy-box">')
            rows.append('<h4>Proposed Copy</h4>')
            if not prop:
                rows.append(
                    '<p class="copy-item pending">PENDING APPROVAL</p>'
                )
            else:
                # Highlight items that differ from current
                cur_flat = set(
                    t.lower()
                    for items in cur.values()
                    for t in (items if isinstance(items, list) else [])
                )
                rows.extend(self._copy_items(prop, highlight_set=cur_flat))
            rows.append("</div>")

            rows.append("</div>")  # two-col
            rows.append("</div>")  # ad-group-block

        rows.append("</div></div>")
        return "".join(rows)

    def _copy_items(self, copy_dict: dict, highlight_set: set) -> list[str]:
        """Render copy items from a {component: [str]} dict."""
        out: list[str] = []
        for component, items in copy_dict.items():
            if not isinstance(items, list):
                continue
            out.append(
                f'<div style="font-size:0.75em;font-weight:700;color:#64748b;'
                f'text-transform:uppercase;letter-spacing:0.04em;'
                f'margin:8px 0 4px;">'
                f"{html.escape(str(component))}</div>"
            )
            for text in items:
                is_changed = text.lower() not in highlight_set
                cls = "copy-item changed" if (highlight_set and is_changed) else "copy-item"
                out.append(f'<div class="{cls}">{html.escape(str(text))}</div>')
        return out

    # ------------------------------------------------------------------
    # Section D - Build Checklist
    # ------------------------------------------------------------------

    def _section_d(self, build_plan: dict) -> str:
        rows: list[str] = ['<div class="section">']
        rows.append('<div class="section-header">D - Build Checklist</div>')
        rows.append('<div class="section-body">')

        if not build_plan:
            rows.append("<p>No build plan provided.</p>")
            rows.append("</div></div>")
            return "".join(rows)

        rows.append(
            '<p style="font-size:0.85em;color:#64748b;margin-bottom:14px;">'
            "Items below will be generated upon approval. "
            "Checkboxes are for human review reference only."
            "</p>"
        )

        # Global extension counts - aggregate sitelinks/callouts across all groups
        total_sitelinks = 0
        total_callouts = 0

        rows.append('<ul class="checklist">')

        for ad_group, counts in build_plan.items():
            if not isinstance(counts, dict):
                continue

            group_label = html.escape(str(ad_group))

            hl_count = counts.get("headlines", 0)
            desc_count = counts.get("descriptions", 0)
            sl_count = counts.get("sitelinks", 0)
            co_count = counts.get("callouts", 0)

            total_sitelinks += sl_count
            total_callouts += co_count

            if hl_count:
                rows.append(
                    f'<li><input type="checkbox" disabled>'
                    f"Headlines ({hl_count}) for <strong>{group_label}</strong></li>"
                )
            if desc_count:
                rows.append(
                    f'<li><input type="checkbox" disabled>'
                    f"Descriptions ({desc_count}) for <strong>{group_label}</strong></li>"
                )

        # Sitelinks and callouts are campaign-level - show totals once
        if total_sitelinks:
            rows.append(
                f'<li><input type="checkbox" disabled>'
                f"Sitelinks ({total_sitelinks})</li>"
            )
        if total_callouts:
            rows.append(
                f'<li><input type="checkbox" disabled>'
                f"Callouts ({total_callouts})</li>"
            )

        rows.append("</ul>")
        rows.append("</div></div>")
        return "".join(rows)
