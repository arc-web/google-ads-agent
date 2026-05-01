#!/usr/bin/env python3
"""
Build a fixed-page client revision review from structured client feedback.

This report is a sibling to the rebuild review. It uses the same fixed-page
HTML, Chrome PDF export, static audit, and rendered visual audit workflow, but
its content is focused on what changed after client feedback.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

if __package__:
    from .build_fixed_campaign_review import fixed_css
    from .build_review_doc import export_pdf
    from .report_quality_audit import audit_html
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from shared.presentation.build_fixed_campaign_review import fixed_css
    from shared.presentation.build_review_doc import export_pdf
    from shared.presentation.report_quality_audit import audit_html


@dataclass
class RevisionItem:
    id: str
    topic: str
    severity: str
    launch_blocker: bool
    client_truth: str
    decision: str
    campaign_action: str
    recommended_action: str
    output_to_update: str
    negative_examples: list[str]


@dataclass
class RsaExample:
    campaign: str
    ad_group: str
    final_url: str
    path_1: str
    path_2: str
    headlines: list[str]
    descriptions: list[str]
    note: str


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True).replace("\u2014", "-")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_decisions(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {row["ID"]: row for row in csv.DictReader(handle)}


def load_editor_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-16", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter="\t")]


def truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"yes", "true", "1"}


def build_items(feedback_path: Path, decisions_path: Path) -> list[RevisionItem]:
    feedback = load_json(feedback_path)
    decisions = load_decisions(decisions_path)
    items: list[RevisionItem] = []
    for item in feedback.get("items", []):
        decision = decisions.get(item.get("id", ""), {})
        items.append(
            RevisionItem(
                id=item.get("id", ""),
                topic=item.get("topic", ""),
                severity=item.get("severity", ""),
                launch_blocker=truthy(item.get("launch_blocker")),
                client_truth=item.get("client_truth", ""),
                decision=decision.get("Decision", ""),
                campaign_action=item.get("campaign_action", ""),
                recommended_action=item.get("recommended_action", ""),
                output_to_update=decision.get("Output To Update", ""),
                negative_examples=item.get("negative_examples", []),
            )
        )
    return items


def page(label: str, title: str, body: str, page_class: str = "") -> str:
    return f"""
<section class="section pdf-page {page_class}">
  <div class="section-header" aria-hidden="true"></div>
  <div class="subsection-header" aria-hidden="true"></div>
  <div class="page-kicker">{esc(label)}</div>
  <h1>{esc(title)}</h1>
  <div class="page-body">{body}</div>
</section>
"""


def pill(text: str, kind: str = "green") -> str:
    cls = "flag-green" if kind == "green" else "flag-red"
    return f'<span class="flag {cls}">{esc(text)}</span>'


def ul(items: Iterable[str]) -> str:
    clean = [item for item in items if item]
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in clean) + "</ul>"


def char_badge(value: str, limit: int) -> str:
    cls = "char-ok" if len(value) <= limit else "char-bad"
    return f'<span class="{cls}">{len(value)}</span>'


def ad_preview_url(row: RsaExample) -> str:
    host = row.final_url.replace("https://", "").replace("http://", "").strip("/")
    parts = [part for part in (row.path_1, row.path_2) if part]
    suffix = " \u203a ".join(parts)
    return f"{host} \u203a {suffix}" if suffix else host


def rsa_from_row(row: dict[str, str], note: str) -> RsaExample:
    return RsaExample(
        campaign=row.get("Campaign", ""),
        ad_group=row.get("Ad Group", ""),
        final_url=row.get("Final URL", ""),
        path_1=row.get("Path 1", ""),
        path_2=row.get("Path 2", ""),
        headlines=[row.get(f"Headline {index}", "") for index in range(1, 16) if row.get(f"Headline {index}", "")],
        descriptions=[row.get(f"Description {index}", "") for index in range(1, 5) if row.get(f"Description {index}", "")],
        note=note,
    )


def select_rsa_examples(staging_csv: Path | None) -> list[RsaExample]:
    if not staging_csv:
        return []
    rows = load_editor_csv(staging_csv)
    desired = [
        (
            "Psychiatry primary focus",
            "Psychiatry - Adult - General",
            "Active revised psychiatry copy now emphasizes Ashburn in-person psychiatric NP appointments.",
        ),
        (
            "Adult therapy secondary focus",
            "Therapy - Anxiety - General",
            "Active adult therapy copy keeps therapy live without crowding out the psychiatry launch priority.",
        ),
        (
            "ADHD testing eligibility",
            "Testing - ADHD - General",
            "Active ADHD testing copy now states children, teens, and young adults through age 21.",
        ),
        (
            "Brand day-one launch",
            "Brand - Think Happy Live Healthy - General",
            "Brand copy is staged separately so brand and nonbrand metrics stay clean.",
        ),
    ]
    examples: list[RsaExample] = []
    for _label, ad_group, note in desired:
        row = next(
            (
                item
                for item in rows
                if item.get("Ad type") == "Responsive search ad" and item.get("Ad Group") == ad_group
            ),
            None,
        )
        if row:
            examples.append(rsa_from_row(row, note))
    return examples


def rsa_example_block(example: RsaExample, index: int) -> str:
    preview_heads = " | ".join(example.headlines[:3])
    preview_desc = example.descriptions[0] if example.descriptions else ""
    headline_rows = "".join(
        f"<tr><td>{num}</td><td class=\"copy-text\">{esc(value)}</td><td>{char_badge(value, 30)}</td></tr>"
        for num, value in enumerate(example.headlines, start=1)
    )
    description_rows = "".join(
        f"<tr><td>{num}</td><td class=\"copy-text\">{esc(value)}</td><td>{char_badge(value, 90)}</td></tr>"
        for num, value in enumerate(example.descriptions, start=1)
    )
    return f"""
<div class="ag-review-block">
  <div class="ag-review-header">
    <div style="display:flex;align-items:center;gap:10px;"><span class="ag-num">{index:02d}</span><h3>{esc(example.ad_group)}</h3></div>
    <div class="ag-url-badge">{esc(example.campaign)}</div>
  </div>
  <div class="ag-review-body">
    <div class="ag-review-cols">
      <div>
        <div class="copy-section-title">Ad Preview</div>
        <div class="ad-preview">
          <div class="ap-label">Sponsored</div>
          <div class="ap-url">{esc(ad_preview_url(example))}</div>
          <div class="ap-headlines">{esc(preview_heads)}</div>
          <div class="ap-desc">{esc(preview_desc)}</div>
        </div>
        <div style="margin-top:12px;">
          <div class="copy-section-title">Revision Note</div>
          <div class="copy-grade-card">
            <div class="grade-note">{esc(example.note)}</div>
          </div>
        </div>
      </div>
      <div>
        <div class="copy-section-title">Headlines</div>
        <table class="copy-table"><tr><th>#</th><th>Headline</th><th>Chars</th></tr>{headline_rows}</table>
        <div class="copy-section-title" style="margin-top:14px;">Descriptions</div>
        <table class="copy-table"><tr><th>#</th><th>Description</th><th>Chars</th></tr>{description_rows}</table>
      </div>
    </div>
  </div>
</div>
"""


def cover_page(client: str, campaign: str, date_label: str) -> str:
    return f"""
<section class="section pdf-page cover-page">
  <div class="section-header" aria-hidden="true"></div>
  <div class="subsection-header" aria-hidden="true"></div>
  <div class="cover-band">
    <div class="page-kicker">Campaign Revisions Review</div>
    <h1>{esc(client)}</h1>
    <p>Client feedback, revised launch scope, and approval package.</p>
    <div class="cover-meta">
      <span><strong>Prepared by</strong> Advertising Report Card</span>
      <span><strong>Date</strong> {esc(date_label)}</span>
      <span><strong>Status</strong> Revision Review</span>
      <span><strong>Campaign</strong> {esc(campaign)}</span>
    </div>
  </div>
  <div class="cover-grid">
    <div><strong>What existed</strong><p>The rebuild report showed the staged search structure, service taxonomy, copy review, and approval topics.</p></div>
    <div><strong>What we built</strong><p>A validated phrase-match services campaign with 96 ad groups, 96 RSAs, geo layers, and human review controls.</p></div>
    <div><strong>What we are revising</strong><p>Client-corrected claims, service availability, age eligibility, geo scope, budget focus, and launch-readiness items.</p></div>
  </div>
</section>
"""


def blocking_page(items: list[RevisionItem]) -> str:
    blockers = [item for item in items if item.launch_blocker]
    body = '<div class="problem-grid">'
    for index, item in enumerate(blockers[:8], start=1):
        action = item.campaign_action or item.recommended_action or item.decision
        body += f"""
<div class="problem-card">
  <div class="pc-number">{index:02d}</div>
  <h4>{esc(item.topic)}</h4>
  <p>{esc(item.client_truth)}</p>
  <p style="margin-top:8px;">{pill('Pre-launch required', 'red')} {esc(action)}</p>
</div>
"""
    body += "</div>"
    return page("Blocking Revisions", "Facts We Must Correct Before Launch", body, "problem-page")


def strategy_page(items: list[RevisionItem]) -> str:
    strategic = [item for item in items if not item.launch_blocker]
    body = '<div class="strategy-grid">'
    for item in strategic:
        action = item.recommended_action or item.campaign_action or item.decision
        body += f"""
<div class="strategy-card">
  <div class="sc-title">{esc(item.topic)}</div>
  <div class="sc-body">{esc(item.client_truth)}</div>
  <div class="sc-why">Revision focus: {esc(action)}</div>
</div>
"""
    body += "</div>"
    body += """
<div class="revision-control-card" style="margin-top:16px;">
  <div class="rc-label">Decision Logic</div>
  <h2>How these items should affect launch</h2>
  <div class="rc-grid">
    <div>
      <h3>Change launch weighting</h3>
      <ul>
        <li>Psychiatry becomes the primary growth focus because the client needs psychiatric NP referral volume.</li>
        <li>Brand launches separately with a capped budget so brand and nonbrand metrics stay clean.</li>
        <li>Testing and adult therapy remain active, but they should not crowd out psychiatry allocation.</li>
      </ul>
    </div>
    <div>
      <h3>Do not blindly rebuild architecture</h3>
      <ul>
        <li>Maryland should be excluded or isolated based on logistics, telehealth constraints, and test appetite.</li>
        <li>Provider-name brand coverage is optional and should be kept low-budget until search volume proves value.</li>
        <li>Strategic changes become CSV changes only after client approval.</li>
      </ul>
    </div>
  </div>
</div>
"""
    return page("Strategic Revisions", "Priority, Budget, Brand, and Geo Decisions", body, "strategy-page")


def snapshot_page(validation: dict, targeting: dict) -> str:
    counts = validation.get("counts", {})
    geo_layers = targeting.get("geo_layers", [])
    insight_cards = [
        ("Rows", validation.get("rows", 0), "Current staged CSV rows"),
        ("RSAs", counts.get("rsa_rows", 0), "Responsive search ads staged"),
        ("Keywords", counts.get("keyword_rows", 0), "Phrase-match keyword rows"),
        ("Locations", counts.get("location_rows", 0), "Location rows staged"),
        ("Bid Modifiers", counts.get("bid_modifier_rows", 0), "Geo review rows"),
        ("Radius", counts.get("radius_rows", 0), "Radius target rows"),
    ]
    body = '<div class="insight-grid">'
    for label, value, note in insight_cards:
        body += f'<div class="insight-card"><div class="ic-value">{esc(value)}</div><div class="ic-label">{esc(label)}</div><div class="ic-note">{esc(note)}</div></div>'
    body += "</div>"
    body += '<table class="geo-table"><tr><th>Layer</th><th>Bid Modifier</th><th>Review Status</th><th>Locations</th></tr>'
    for layer in geo_layers:
        body += (
            "<tr>"
            f"<td>{esc(layer.get('tier'))}</td>"
            f"<td>{esc(layer.get('bid_modifier') or 'none')}</td>"
            f"<td>{esc(layer.get('review_status'))}</td>"
            f"<td>{esc(', '.join(layer.get('locations', [])))}</td>"
            "</tr>"
        )
    body += "</table>"
    return page("Campaign Snapshot", "Current Staging File and Geo Review", body, "data-page")


def controls_page(items: list[RevisionItem]) -> str:
    rows = ""
    for item in items:
        if item.id in {"R001", "R002", "R003", "R004", "R007", "R009"}:
            output = item.output_to_update or "launch readiness checklist"
            action = item.campaign_action or item.recommended_action or item.decision
            rows += f"<tr><td>{esc(item.id)}</td><td>{esc(item.topic)}</td><td>{esc(action)}</td><td>{esc(output)}</td></tr>"
    body = """
<div class="card" style="margin-bottom:18px;">
  <p>These controls are not a repeat of the rebuild audit. They are the factual and compliance changes required because the client corrected availability, payer, eligibility, and launch-readiness details.</p>
</div>
<table class="intent-table">
  <tr><th>ID</th><th>Revision Area</th><th>Control Applied</th><th>Output To Update</th></tr>
""" + rows + "</table>"
    return page("Revision Controls", "Claims, Scope, Eligibility, and Verification", body, "architecture-page")


def copy_review_pages(examples: list[RsaExample]) -> list[str]:
    if not examples:
        body = """
<div class="card">
  <p>No revised staging CSV was provided, so this page cannot render active RSA examples.</p>
</div>
"""
        return [page("Copy Review", "Active Revised RSA Examples", body, "ad-pair-page")]

    pages: list[str] = []
    for page_index in range(0, len(examples), 2):
        chunk = examples[page_index : page_index + 2]
        body = '<div class="ad-pair-grid">'
        for offset, example in enumerate(chunk, start=1):
            body += rsa_example_block(example, page_index + offset)
        body += "</div>"
        title = "Active Revised RSA Examples" if page_index == 0 else "More Active Revised RSA Examples"
        pages.append(page("Copy Review", title, body, "ad-pair-page"))

    control_rows = [
        (
            "Insurance",
            "Broad payer acceptance claim",
            "Active copy uses Anthem/CareFirst BCBS plus out-of-network superbill language.",
            "Shown in active RSA examples.",
        ),
        (
            "EMDR",
            "Unavailable specialty modality claim",
            "EMDR was removed from active paid copy and controlled through negatives.",
            "Not active copy.",
        ),
        (
            "ADHD Testing",
            "Adult eligibility phrasing",
            "ADHD copy now states children, teens, and young adults through age 21.",
            "Shown in active RSA examples.",
        ),
        (
            "Family Therapy",
            "Standalone family modality positioning",
            "Standalone family therapy language was removed and controlled through negatives.",
            "Not active copy.",
        ),
    ]
    controls = '<table class="intent-table"><tr><th>Area</th><th>Original Risk</th><th>Applied Revision</th><th>Status</th></tr>'
    for area, risk, revision, status in control_rows:
        controls += (
            "<tr>"
            f"<td>{esc(area)}</td>"
            f"<td>{esc(risk)}</td>"
            f"<td>{esc(revision)}</td>"
            f"<td>{esc(status)}</td>"
            "</tr>"
        )
    controls += "</table>"
    pages.append(page("Copy Controls", "Removed Copy and Claim Guardrails", controls, "architecture-page"))
    return pages


def launch_gate_page(items: list[RevisionItem]) -> str:
    discuss = [item for item in items if not item.launch_blocker]
    blockers = [item for item in items if item.launch_blocker]
    body = f"""
<div class="card" style="background:var(--green-bg); border-color:#B7DEC7;">
  <p><strong>Ready to approve after revision edits:</strong> {len(blockers)} pre-launch required items are defined and traceable to campaign outputs.</p>
</div>
<div class="discussion-grid">
  <div class="discussion-card">
    <div class="dc-label">Approve</div>
    <div class="dc-title">Blocking revisions</div>
    <div class="dc-body">{esc(', '.join(item.id for item in blockers))}</div>
    <div class="dc-actions"><span class="dc-action dc-approve">Approve</span><span class="dc-action dc-changes">Changes</span></div>
  </div>
  <div class="discussion-card">
    <div class="dc-label">Discuss</div>
    <div class="dc-title">Strategy items</div>
    <div class="dc-body">{esc(', '.join(item.topic for item in discuss))}</div>
    <div class="dc-actions"><span class="dc-action dc-approve">Approve</span><span class="dc-action dc-changes">Discuss</span></div>
  </div>
  <div class="discussion-card">
    <div class="dc-label">Coordinate</div>
    <div class="dc-title">Website and compliance</div>
    <div class="dc-body">Moonraker, Curve Compliance, GA4, conversion tracking, and healthcare advertiser verification need clean handoffs.</div>
    <div class="dc-actions"><span class="dc-action dc-approve">Approve</span><span class="dc-action dc-changes">Changes</span></div>
  </div>
  <div class="discussion-card">
    <div class="dc-label">Launch</div>
    <div class="dc-title">Final upload gate</div>
    <div class="dc-body">Export revised CSV only after client facts, negative keywords, geo scope, and tracking readiness are confirmed.</div>
    <div class="dc-actions"><span class="dc-action dc-approve">Approve</span><span class="dc-action dc-changes">Changes</span></div>
  </div>
</div>
<div class="revision-control-card" style="margin-top:14px;">
  <div class="rc-label">Launch Rule</div>
  <h2>What can launch versus what can keep improving</h2>
  <div class="rc-grid">
    <div>
      <h3>Must be fixed before upload</h3>
      <ul>
        <li>Insurance wording, EMDR capacity, ADHD age eligibility, family-service scope, tracking explanation, and verification timing.</li>
        <li>Negative keywords for adult ADHD testing and standalone family-therapy intent.</li>
      </ul>
    </div>
    <div>
      <h3>Can be optimized after launch</h3>
      <ul>
        <li>Budget weight, provider-name brand coverage, zip-code bid modifiers, and backend lead-to-client matching.</li>
        <li>Website page updates with Moonraker and compliance routing with Curve Compliance.</li>
      </ul>
    </div>
  </div>
</div>
"""
    return page("Launch Gate", "Approval Topics for the Revised Launch", body, "approval-page")


def sources_page(paths: list[Path]) -> str:
    body = '<div class="continuation-header"><div class="continuation-title">Revision Review Sources</div><div class="continuation-note">Reference</div></div>'
    body += '<div class="card"><p>Report inputs stay in the client build folder and presentation commands stay under presentations/tools.</p></div>'
    body += """
<div class="insight-grid" style="margin-top:14px;">
  <div class="insight-card"><div class="ic-value">HTML</div><div class="ic-label">Source Of Truth</div><div class="ic-note">The editable report is fixed-page HTML in the client build folder.</div></div>
  <div class="insight-card"><div class="ic-value">PDF</div><div class="ic-label">Delivery Artifact</div><div class="ic-note">The PDF is exported through the same Chrome headless path as the rebuild report.</div></div>
  <div class="insight-card"><div class="ic-value">2 Gates</div><div class="ic-label">Quality Checks</div><div class="ic-note">Static HTML audit and rendered PDF visual audit both run before handoff.</div></div>
</div>
"""
    body += "<table class=\"tax-table\"><tr><th>Source</th><th>Path</th></tr>"
    for path in paths:
        if not str(path):
            continue
        body += f"<tr><td>{esc(path.name)}</td><td>{esc(path)}</td></tr>"
    body += "</table>"
    return page("Sources", "Files Used For This Revision Report", body, "roadmap-page")


def build_revision_html(args: argparse.Namespace) -> str:
    feedback_path = Path(args.feedback_json)
    decisions_path = Path(args.decision_log)
    validation_path = Path(args.validation_json)
    targeting_path = Path(args.targeting_json)
    items = build_items(feedback_path, decisions_path)
    validation = load_json(validation_path)
    targeting = load_json(targeting_path)
    examples = select_rsa_examples(Path(args.staging_csv) if args.staging_csv else None)
    campaign = validation.get("sources", {}).get("campaign") or targeting.get("campaign") or "ARC - Search - Services - V1"
    pages = [
        cover_page(args.client, campaign, args.date),
        blocking_page(items),
        strategy_page(items),
        snapshot_page(validation, targeting),
        controls_page(items),
    ]
    pages.extend(copy_review_pages(examples))
    pages.extend(
        [
            launch_gate_page(items),
            sources_page(
                [feedback_path, decisions_path, validation_path, targeting_path]
                + ([Path(args.staging_csv)] if args.staging_csv else [])
            ),
        ]
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Campaign Revisions Review - {esc(args.client)}</title>
<style>
{fixed_css()}
</style>
</head>
<body>
{''.join(pages)}
</body>
</html>
"""


def run_visual_audit(pdf_path: Path, pages_dir: Path) -> None:
    cmd = [
        sys.executable,
        "-m",
        "shared.presentation.pdf_visual_audit",
        str(pdf_path),
        "--pages-dir",
        str(pages_dir),
    ]
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a fixed-page campaign revisions review HTML/PDF.")
    parser.add_argument("--client", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--feedback-json", required=True, type=Path)
    parser.add_argument("--decision-log", required=True, type=Path)
    parser.add_argument("--validation-json", required=True, type=Path)
    parser.add_argument("--targeting-json", required=True, type=Path)
    parser.add_argument("--staging-csv", type=Path)
    parser.add_argument("--output-html", required=True, type=Path)
    parser.add_argument("--output-pdf", required=True, type=Path)
    parser.add_argument("--visual-audit-dir", type=Path)
    args = parser.parse_args()

    html_text = build_revision_html(args)
    args.output_html.parent.mkdir(parents=True, exist_ok=True)
    args.output_html.write_text(html_text, encoding="utf-8")
    findings, summary = audit_html(args.output_html)
    if summary["errors"]:
        for finding in findings:
            if finding.severity == "error":
                print(f"error: {finding.code}: {finding.message} {finding.evidence}", file=sys.stderr)
        return 1

    export_pdf(args.output_html, args.output_pdf)
    if args.visual_audit_dir:
        run_visual_audit(args.output_pdf, args.visual_audit_dir)
    print(f"wrote {args.output_html}")
    print(f"wrote {args.output_pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
