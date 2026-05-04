#!/usr/bin/env python3
"""Build a reader-facing report for a new campaign build."""

from __future__ import annotations

import argparse
import csv
import html
import json
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__:
    from .build_review_doc import export_pdf
    from .client_email_draft import EmailDraftInput, write_client_email_draft
    from .pdf_visual_audit import audit_pdf
    from .report_quality_audit import audit_html
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from shared.presentation.build_review_doc import export_pdf
    from shared.presentation.client_email_draft import EmailDraftInput, write_client_email_draft
    from shared.presentation.pdf_visual_audit import audit_pdf
    from shared.presentation.report_quality_audit import audit_html
from shared.rebuild.rsa_headline_quality import audit_rows, find_service_logic, service_from_ad_group
from shared.rebuild.service_logic_research import service_logic_by_name


@dataclass(frozen=True)
class CampaignSummary:
    campaigns: list[str]
    ad_groups: int
    phrase_keywords: int
    negative_phrase_keywords: int
    rsa_rows: int
    locations: list[str]
    networks: list[str]


@dataclass(frozen=True)
class RsaExample:
    campaign: str
    ad_group: str
    final_url: str
    path_1: str
    path_2: str
    headlines: list[str]
    descriptions: list[str]
    headline_quality_status: str = "pass"
    service_logic: dict | None = None


@dataclass(frozen=True)
class BudgetPlan:
    monthly_budget: float
    cpc_low: float | None = None
    cpc_high: float | None = None

    @property
    def daily_budget(self) -> float:
        return self.monthly_budget / 30

    @property
    def daily_click_range(self) -> tuple[float, float] | None:
        if not self.cpc_low or not self.cpc_high:
            return None
        return self.daily_budget / self.cpc_high, self.daily_budget / self.cpc_low


def esc(value: object) -> str:
    return (
        html.escape(str(value or ""), quote=True)
        .replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u00a0", " ")
    )


def money(value: float) -> str:
    return f"${value:,.0f}"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_staging(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-16", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter="\t")]


def summarize_staging(rows: list[dict[str, str]]) -> CampaignSummary:
    campaigns = sorted({row["Campaign"] for row in rows if row.get("Campaign")})
    ad_groups = len(ad_group_rows(rows))
    phrase_keywords = sum(1 for row in rows if row.get("Criterion Type") == "Phrase")
    negative_phrase_keywords = sum(1 for row in rows if row.get("Criterion Type") == "Negative Phrase")
    rsa_rows = sum(1 for row in rows if row.get("Ad type") == "Responsive search ad")
    locations = sorted({row["Location"] for row in rows if row.get("Location")})
    networks = sorted({row["Networks"] for row in rows if row.get("Networks")})
    return CampaignSummary(
        campaigns=campaigns,
        ad_groups=ad_groups,
        phrase_keywords=phrase_keywords,
        negative_phrase_keywords=negative_phrase_keywords,
        rsa_rows=rsa_rows,
        locations=locations,
        networks=networks,
    )


def select_rsa_examples(
    rows: list[dict[str, str]],
    limit: int | None = None,
    service_logic_map: dict[str, dict] | None = None,
) -> list[RsaExample]:
    examples: list[RsaExample] = []
    audit_by_ad_group = {
        audit.get("ad_group", ""): audit
        for audit in audit_rows(rows, service_logic_map).get("audits", [])
    }
    for row in rows:
        if row.get("Ad type") != "Responsive search ad":
            continue
        service_label = service_from_ad_group(row.get("Ad Group", ""))
        headline_audit = audit_by_ad_group.get(row.get("Ad Group", ""), {})
        examples.append(
            RsaExample(
                campaign=row.get("Campaign", ""),
                ad_group=row.get("Ad Group", ""),
                final_url=row.get("Final URL", ""),
                path_1=row.get("Path 1", ""),
                path_2=row.get("Path 2", ""),
                headlines=[row.get(f"Headline {index}", "") for index in range(1, 16)],
                descriptions=[row.get(f"Description {index}", "") for index in range(1, 5)],
                headline_quality_status=str(headline_audit.get("status", "unknown")),
                service_logic=find_service_logic(service_label, service_logic_map),
            )
        )
        if limit is not None and len(examples) == limit:
            break
    return examples


def css() -> str:
    return """
@page { size: Letter; margin: 0; }
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #eee9df;
  color: #211f1d;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.pdf-page {
  width: 8.5in;
  min-height: 11in;
  padding: 0.54in;
  background: #f8f4eb;
  position: relative;
  overflow: hidden;
}
.pdf-page + .pdf-page { break-before: page; }
.section-header {
  border-left: 7px solid #185c62;
  padding: 16px 20px;
  background: #ebe2d3;
  margin-bottom: 24px;
}
.section-header .eyebrow {
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #6b5c4b;
  font-weight: 800;
}
.section-header h1 {
  margin: 8px 0 0;
  font-size: 34px;
  line-height: 1.02;
  letter-spacing: 0;
}
.section-header p {
  margin: 10px 0 0;
  max-width: 660px;
  font-size: 15px;
  line-height: 1.45;
  color: #4b4037;
}
.subsection-header {
  margin: 16px 0 14px;
  padding: 10px 14px;
  border-left: 4px solid #c8753f;
  background: #fffaf1;
  font-weight: 800;
  color: #3d342b;
}
.continuation-header {
  margin: 16px 0 12px;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #766858;
  font-weight: 800;
}
.cover {
  background: linear-gradient(135deg, #f8f4eb 0%, #f3eadc 58%, #e5f0ee 100%);
}
.brand-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 92px;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #5e5144;
  font-weight: 800;
}
.cover-title {
  max-width: 720px;
}
.cover-title .label {
  color: #185c62;
  font-weight: 900;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-size: 13px;
}
.cover-title h1 {
  margin: 16px 0 18px;
  font-size: 54px;
  line-height: 0.98;
  letter-spacing: 0;
}
.cover-title p {
  margin: 0;
  max-width: 620px;
  font-size: 20px;
  line-height: 1.35;
  color: #40362f;
}
.metric-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 50px;
}
.metric {
  padding: 16px;
  background: rgba(255,255,255,0.72);
  border: 1px solid #dfd2bf;
}
.metric strong {
  display: block;
  font-size: 28px;
  color: #185c62;
}
.metric span {
  font-size: 12px;
  color: #6f6256;
  font-weight: 700;
}
.card-grid,
.two-col,
.approval-grid,
.ad-grid {
  display: grid;
  gap: 14px;
}
.card-grid { grid-template-columns: repeat(2, 1fr); }
.two-col { grid-template-columns: 1fr 1fr; }
.approval-grid { grid-template-columns: repeat(2, 1fr); }
.ad-grid { grid-template-columns: 1fr; }
.confirm-strip {
  margin-top: 16px;
  padding: 12px 14px;
  background: #e5f0ee;
  border-left: 4px solid #185c62;
  color: #234045;
}
.confirm-strip h3 {
  margin: 0 0 5px;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.confirm-strip p {
  margin: 0;
  font-size: 12px;
  line-height: 1.38;
}
.overview-steps {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}
.overview-step {
  background: #fffaf1;
  border: 1px solid #dfd2bf;
  padding: 16px;
}
.overview-step .step-number {
  display: inline-block;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #185c62;
  color: #fffaf1;
  text-align: center;
  line-height: 28px;
  font-weight: 900;
  margin-bottom: 10px;
}
.overview-step h3 {
  margin: 0 0 8px;
  font-size: 16px;
}
.overview-step p {
  margin: 0;
  font-size: 13px;
  line-height: 1.45;
  color: #4c4238;
}
.insight-card,
.approval-card,
.ad-card,
.source-card {
  background: #fffaf1;
  border: 1px solid #dfd2bf;
  padding: 15px;
}
.insight-card h3,
.approval-card h3,
.ad-card h3 {
  margin: 0 0 8px;
  font-size: 16px;
}
.insight-card p,
.approval-card p,
.source-card p {
  margin: 0;
  font-size: 13px;
  line-height: 1.45;
  color: #4c4238;
}
.badge {
  display: inline-block;
  padding: 5px 8px;
  margin: 4px 5px 0 0;
  background: #e5f0ee;
  color: #185c62;
  font-size: 11px;
  font-weight: 800;
}
.ad-preview {
  border-left: 4px solid #2f6f76;
  background: #fff;
  padding: 12px;
  margin: 10px 0 12px;
}
.ad-preview .sponsored {
  font-size: 11px;
  color: #6e6257;
  font-weight: 700;
}
.ad-preview .url {
  font-size: 12px;
  color: #247b4d;
  margin-top: 4px;
}
.ad-preview .headline {
  color: #1a0dab;
  font-size: 18px;
  line-height: 1.2;
  margin-top: 5px;
}
.ad-preview .desc {
  color: #3f3f3f;
  font-size: 12px;
  line-height: 1.35;
  margin-top: 5px;
}
.ad-copy-page .section-header {
  padding: 12px 16px;
  margin-bottom: 12px;
}
.ad-copy-page .section-header h1 {
  font-size: 28px;
}
.ad-copy-page .section-header p {
  font-size: 13px;
  margin-top: 7px;
}
.ad-copy-page .ad-card {
  padding: 10px;
}
.ad-copy-page .ad-card h3 {
  margin-bottom: 6px;
}
.ad-copy-page .ad-preview {
  padding: 8px;
  margin: 6px 0 0;
}
.ad-copy-page .ad-preview .headline {
  font-size: 16px;
}
.ad-copy-page .subsection-header {
  margin: 10px 0 6px;
  padding: 7px 10px;
}
.ad-copy-page .subsection-header + .ad-copy-table {
  margin-bottom: 10px;
}
.audit-note {
  margin: 0 0 6px;
  font-size: 10px;
  color: #6b5c4b;
  font-weight: 700;
}
.service-logic-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin: 8px 0 10px;
}
.service-logic-card {
  border: 1px solid #dfd2bf;
  background: #fffaf1;
  padding: 8px 10px;
  min-height: 58px;
}
.service-logic-card h3 {
  margin: 0 0 4px;
  color: #185c62;
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.service-logic-card p {
  margin: 0;
  font-size: 10.5px;
  line-height: 1.32;
  color: #4c4238;
}
.ad-copy-page table {
  font-size: 9.5px;
}
.ad-copy-page td,
.ad-copy-page th {
  padding: 3px 5px;
}
.ad-copy-table col.slot-col { width: 34px; }
.ad-copy-table col.char-col { width: 54px; }
.ad-copy-table th:first-child,
.ad-copy-table td:first-child,
.ad-copy-table th:last-child,
.ad-copy-table td:last-child {
  text-align: left;
}
.ad-copy-table th:nth-child(2),
.ad-copy-table td:nth-child(2) {
  padding-left: 5px;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}
td, th {
  border-bottom: 1px solid #e2d7c6;
  padding: 6px 5px;
  text-align: left;
  vertical-align: top;
}
th {
  color: #6b5c4b;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
ul {
  margin: 8px 0 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.42;
}
.footnote {
  position: absolute;
  left: 0.54in;
  right: 0.54in;
  bottom: 0.34in;
  font-size: 10px;
  color: #7c6d5c;
}
.budget-summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}
.budget-summary-card,
.budget-chart-card,
.budget-tile {
  background: #fffaf1;
  border: 1px solid #dfd2bf;
}
.budget-summary-card {
  padding: 14px 10px 15px;
  text-align: center;
}
.budget-summary-card .label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #746656;
  font-weight: 900;
  min-height: 28px;
}
.budget-summary-card strong {
  display: block;
  margin-top: 6px;
  font-size: 32px;
  line-height: 1;
  color: #185c62;
}
.budget-section-head {
  display: flex;
  gap: 12px;
  align-items: stretch;
  margin: 12px 0 10px;
}
.budget-accent {
  width: 5px;
  min-width: 5px;
  border-radius: 2px;
  background: #c8753f;
}
.budget-section-head h2 {
  margin: 0;
  font-size: 18px;
  line-height: 1.2;
}
.budget-section-head p {
  margin: 4px 0 0;
  font-size: 12px;
  color: #5e5144;
  line-height: 1.4;
}
.budget-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
  margin: 0 0 10px;
  color: #5e5144;
  font-size: 11px;
  font-weight: 700;
}
.budget-legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.budget-swatch {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}
.budget-chart-card {
  padding: 10px 12px 8px;
}
.budget-svg-main,
.budget-svg-ramp {
  display: block;
  width: 100%;
  height: auto;
}
.budget-svg-main { max-height: 250px; }
.budget-svg-ramp { max-height: 200px; }
.budget-guide {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
  line-height: 1.35;
  margin-top: 10px;
}
.budget-guide th,
.budget-guide td {
  border: 1px solid #dfd2bf;
  padding: 5px 8px;
  text-align: left;
  vertical-align: top;
}
.budget-guide th {
  background: rgba(255, 255, 255, 0.25);
}
.marker-cell {
  width: 36px;
  text-align: center;
  font-weight: 900;
  font-size: 13px;
  color: #185c62;
}
.budget-split {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  gap: 14px;
  align-items: start;
}
.budget-takeaways {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-top: 14px;
}
.budget-tile {
  padding: 10px 12px;
}
.budget-tile h3 {
  margin: 0 0 4px;
  font-size: 13px;
}
.budget-tile p {
  margin: 0;
  color: #5e5144;
  font-size: 11px;
  line-height: 1.35;
}
.goal-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin: 18px 0;
}
.goal-card {
  background: #fffaf1;
  border: 1px solid #dfd2bf;
  padding: 14px;
}
.goal-card .label {
  color: #756657;
  font-size: 10px;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.goal-card strong {
  display: block;
  color: #185c62;
  font-size: 24px;
  margin-top: 6px;
}
.goal-list {
  margin: 12px 0 0;
  padding-left: 18px;
  color: #4d4238;
  line-height: 1.45;
  font-size: 13px;
}
.launch-brief {
  border: 1px solid #dfd2bf;
  background: #fffaf1;
  padding: 28px;
}
.launch-brief-grid {
  display: grid;
  grid-template-columns: 1.45fr 0.9fr;
  gap: 28px;
  align-items: center;
}
.launch-kicker {
  color: #185c62;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  margin-bottom: 16px;
}
.launch-brief h2 {
  margin: 0;
  font-size: 42px;
  line-height: 0.98;
  letter-spacing: 0;
  color: #241f1b;
}
.launch-brief p {
  margin: 18px 0 0;
  color: #62584f;
  font-size: 16px;
  line-height: 1.45;
}
.launch-actions {
  display: flex;
  gap: 10px;
  margin-top: 22px;
}
.launch-pill {
  display: inline-block;
  padding: 11px 18px;
  border-radius: 22px;
  color: #fffaf1;
  font-size: 12px;
  font-weight: 900;
}
.launch-pill.primary { background: #0f7779; }
.launch-pill.secondary { background: #d9783d; }
.launch-stat-list {
  display: grid;
  gap: 10px;
}
.launch-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #efe6da;
  border-radius: 14px;
  padding: 14px 16px;
  font-weight: 900;
  color: #25211d;
}
.launch-stat span:first-child {
  font-size: 14px;
}
.launch-stat span:last-child {
  font-size: 16px;
}
.approval-list {
  margin-top: 20px;
  border: 1px solid #dfd2bf;
  background: #fffaf1;
}
.approval-row {
  display: grid;
  grid-template-columns: 44px 1fr 94px;
  gap: 14px;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid #dfd2bf;
}
.approval-row:last-child {
  border-bottom: 0;
}
.approval-icon {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  background: #0f7779;
  color: #fffaf1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  font-size: 16px;
}
.approval-icon.warn {
  background: #d9783d;
}
.approval-copy h3 {
  margin: 0 0 3px;
  font-size: 17px;
  line-height: 1.1;
  color: #241f1b;
}
.approval-copy p {
  margin: 0;
  color: #6a5f55;
  font-size: 12px;
  line-height: 1.35;
}
.approval-button {
  justify-self: end;
  border-radius: 20px;
  padding: 9px 15px;
  color: #fffaf1;
  background: #0f7779;
  font-size: 12px;
  font-weight: 900;
}
.approval-button.warn {
  background: #d9783d;
}
.state-chip {
  display: inline-block;
  margin: 4px 5px 0 0;
  padding: 6px 8px;
  background: #e5f0ee;
  color: #185c62;
  font-size: 11px;
  font-weight: 800;
}
.targeting-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.targeting-panel {
  background: #fffaf1;
  border: 1px solid #dfd2bf;
  padding: 14px;
}
.targeting-panel.compact {
  padding: 12px;
}
.targeting-table {
  font-size: 10px;
  line-height: 1.22;
}
.targeting-table th,
.targeting-table td {
  padding: 5px 6px;
}
.targeting-table col.type-col { width: 58px; }
.targeting-table col.area-col { width: 132px; }
.targeting-table col.status-col { width: 86px; }
.structure-flow {
  background: #fffaf1;
  border: 1px solid #dfd2bf;
  padding: 14px;
  margin-top: 14px;
}
.structure-flow svg {
  display: block;
  width: 100%;
  height: auto;
}
.flow-box {
  fill: #f8f4eb;
  stroke: #dfd2bf;
  stroke-width: 2;
}
.flow-current {
  fill: #e5f0ee;
  stroke: #185c62;
  stroke-width: 2;
}
.flow-future {
  fill: #fffaf1;
  stroke: #c8753f;
  stroke-width: 2;
}
.flow-line {
  stroke: #c43ad3;
  stroke-width: 5;
  fill: none;
  stroke-linecap: round;
}
.flow-muted {
  stroke: #d6a6dd;
  stroke-width: 4;
  fill: none;
  stroke-linecap: round;
}
.flow-label {
  fill: #2f3d45;
  font-size: 18px;
  font-weight: 800;
}
.flow-small {
  fill: #4c5c64;
  font-size: 12px;
  font-weight: 700;
}
.flow-note-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 14px;
}
.flow-note {
  background: #f8f4eb;
  border: 1px solid #dfd2bf;
  padding: 12px;
}
.flow-note h3 {
  margin: 0 0 6px;
  font-size: 13px;
}
.flow-note p {
  margin: 0;
  color: #4c4238;
  font-size: 12px;
  line-height: 1.4;
}
"""


def section(label: str, title: str, intro: str, body: str) -> str:
    return f"""
<section class="section pdf-page">
  <div class="section-header">
    <div class="eyebrow">{esc(label)}</div>
    <h1>{esc(title)}</h1>
    <p>{esc(intro)}</p>
  </div>
  {body}
</section>
"""


def cover(client: str, date_label: str, summary: CampaignSummary) -> str:
    return f"""
<section class="section pdf-page cover">
  <div class="section-header" style="display:none"></div>
  <div class="subsection-header" style="display:none">Report start</div>
  <div class="brand-row"><span>Advertising Report Card</span><span>{esc(date_label)}</span></div>
  <div class="cover-title">
    <div class="label">New Campaign Review</div>
    <h1>{esc(client)}</h1>
    <p>A new Google Ads Search campaign proposal, built from website evidence and prepared for your review.</p>
  </div>
  <div class="metric-row">
    <div class="metric"><strong>{len(summary.campaigns)}</strong><span>Search campaign</span></div>
    <div class="metric"><strong>{summary.ad_groups}</strong><span>ad groups</span></div>
    <div class="metric"><strong>{summary.phrase_keywords}</strong><span>phrase keywords</span></div>
    <div class="metric"><strong>{summary.rsa_rows}</strong><span>responsive ads</span></div>
  </div>
  <div class="footnote">{esc(date_label)}</div>
</section>
"""


def ad_group_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("Ad Group")
        and not row.get("Keyword")
        and not row.get("Ad type")
        and not row.get("Link text")
        and not row.get("Callout text")
        and not row.get("Structured snippet header")
        and not row.get("Phone number")
        and not row.get("Business name")
    ]


def keyword_counts_by_ad_group(rows: list[dict[str, str]]) -> dict[str, int]:
    keyword_counts: dict[str, int] = {}
    for row in rows:
        if row.get("Criterion Type") == "Phrase":
            keyword_counts[row.get("Ad Group", "")] = keyword_counts.get(row.get("Ad Group", ""), 0) + 1
    return keyword_counts


def overview_section(summary: CampaignSummary) -> str:
    steps = [
        (
            "Structure",
            "How the launch is organized now and how it can expand later if performance supports it.",
        ),
        (
            "Ad groups",
            "Which services are ready to run ads and which priorities should be confirmed first.",
        ),
        (
            "Ads and regions",
            "Representative ad copy examples, proposed regional targeting, and the priority market questions to confirm before launch.",
        ),
        (
            "Budget and confirmation",
            "How the budget is paced through the month, then one final page for approval.",
        ),
    ]
    step_cards = "".join(
        f"""
<div class="overview-step">
  <div class="step-number">{index}</div>
  <h3>{esc(title)}</h3>
  <p>{esc(text)}</p>
</div>
"""
        for index, (title, text) in enumerate(steps, start=1)
    )
    body = f"""
<div class="overview-steps">{step_cards}</div>
<div class="subsection-header">Current launch snapshot</div>
<div class="metric-row" style="margin-top:0;">
  <div class="metric"><strong>{len(summary.campaigns)}</strong><span>Search campaign</span></div>
  <div class="metric"><strong>{summary.ad_groups}</strong><span>ad groups</span></div>
  <div class="metric"><strong>{summary.phrase_keywords}</strong><span>phrase keywords</span></div>
  <div class="metric"><strong>{summary.rsa_rows}</strong><span>responsive ads</span></div>
</div>
"""
    return section(
        "Overview",
        "What This Review Covers",
        "This report walks through the campaign structure, service ad groups, ads, proposed targeting, budget pacing, and final confirmation items before launch.",
        body,
    )


def budget_summary_cards(budget: BudgetPlan) -> str:
    low_range = budget.daily_budget * 0.60
    high_range = budget.daily_budget * 1.45
    return f"""
<div class="budget-summary-cards">
  <div class="budget-summary-card">
    <div class="label">Approved monthly budget</div>
    <strong>${budget.monthly_budget:,.0f}</strong>
  </div>
  <div class="budget-summary-card">
    <div class="label">Daily budget</div>
    <strong>${budget.daily_budget:,.0f}</strong>
  </div>
  <div class="budget-summary-card">
    <div class="label">Low daily range</div>
    <strong>${low_range:,.0f}</strong>
  </div>
  <div class="budget-summary-card">
    <div class="label">High daily range</div>
    <strong>${high_range:,.0f}</strong>
  </div>
</div>
"""


def budget_pacing_section(budget: BudgetPlan) -> str:
    body = f"""
{budget_summary_cards(budget)}
<div class="budget-section-head">
  <div class="budget-accent"></div>
  <div>
    <h2>How your budget moves through the month</h2>
    <p>The goal is to protect early spend while search terms, cost per click, and service demand become clearer.</p>
  </div>
</div>
<div class="budget-legend" role="list">
  <div class="budget-legend-item" role="listitem"><span class="budget-swatch" style="background: rgba(165, 201, 197, 0.38); border: 1px solid rgba(13, 104, 112, 0.28);"></span>Healthy daily range</div>
  <div class="budget-legend-item" role="listitem"><span class="budget-swatch" style="background:#d17a32;"></span>Amount spent over time</div>
  <div class="budget-legend-item" role="listitem"><span class="budget-swatch" style="background:#0d6870;"></span>Budget remaining</div>
  <div class="budget-legend-item" role="listitem"><span class="budget-swatch" style="background:#b65f3e;"></span>CPC and click movement</div>
</div>
<div class="budget-chart-card">
  <svg class="budget-svg-main" viewBox="0 0 920 400" role="img" aria-label="Budget pacing with healthy range, spend ramp, remaining budget, and daily variation">
    <defs>
      <linearGradient id="g-orange" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#e8883a" />
        <stop offset="100%" stop-color="#d17a32" />
      </linearGradient>
      <linearGradient id="g-teal" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#0d6870" />
        <stop offset="100%" stop-color="#0a5258" />
      </linearGradient>
    </defs>
    <rect x="88" y="52" width="758" height="292" fill="rgba(255,255,255,0.35)" stroke="#c9b79d" stroke-width="1.5" rx="4" />
    <line x1="88" y1="344" x2="846" y2="344" stroke="#9a8b78" stroke-width="2" stroke-linecap="round" />
    <line x1="88" y1="52" x2="88" y2="344" stroke="#9a8b78" stroke-width="2" stroke-linecap="round" />
    <g stroke="#d7c3aa" stroke-width="1" stroke-dasharray="3 5">
      <line x1="88" y1="96" x2="846" y2="96" />
      <line x1="88" y1="164" x2="846" y2="164" />
      <line x1="88" y1="232" x2="846" y2="232" />
      <line x1="88" y1="300" x2="846" y2="300" />
    </g>
    <text x="24" y="102" fill="#6b5f54" font-size="11" font-weight="700">High</text>
    <text x="15" y="238" fill="#6b5f54" font-size="11" font-weight="700">Target</text>
    <text x="28" y="306" fill="#6b5f54" font-size="11" font-weight="700">Low</text>
    <rect x="88" y="200" width="758" height="64" fill="rgba(165, 201, 197, 0.38)" rx="3" />
    <line x1="88" y1="232" x2="846" y2="232" stroke="#6eb3ad" stroke-width="4" stroke-linecap="round" stroke-dasharray="10 12" opacity="0.85" />
    <path d="M 88 312 L 88 312 C 200 292, 320 252, 430 198 C 540 152, 680 110, 846 42 L 846 344 L 88 344 Z" fill="url(#g-orange)" opacity="0.08" />
    <path d="M 88 312 C 200 292, 320 252, 430 198 C 540 152, 680 110, 846 42" fill="none" stroke="url(#g-orange)" stroke-width="5" stroke-linecap="round" />
    <path d="M 88 68 C 210 74, 320 104, 430 154 C 550 206, 680 274, 846 324" fill="none" stroke="url(#g-teal)" stroke-width="5.5" stroke-linecap="round" />
    <path d="M 88 244 C 150 218, 220 218, 280 246 C 350 284, 400 274, 450 246 C 500 218, 560 226, 620 258 C 700 294, 780 274, 846 246" fill="none" stroke="#b65f3e" stroke-width="4.5" stroke-linecap="round" opacity="0.95" />
    <g font-size="12" font-weight="800" text-anchor="middle" dominant-baseline="middle">
      <circle cx="88" cy="68" r="11" fill="#f6f0e7" stroke="#0d6870" stroke-width="3" />
      <text x="88" y="69" fill="#0d6870">A</text>
      <circle cx="164" cy="236" r="11" fill="#f6f0e7" stroke="#b65f3e" stroke-width="3" />
      <text x="164" y="237" fill="#b65f3e">B</text>
      <circle cx="430" cy="248" r="11" fill="#f6f0e7" stroke="#b65f3e" stroke-width="3" />
      <text x="430" y="249" fill="#b65f3e">C</text>
      <circle cx="662" cy="268" r="11" fill="#f6f0e7" stroke="#b65f3e" stroke-width="3" />
      <text x="662" y="269" fill="#b65f3e">D</text>
      <circle cx="636" cy="138" r="11" fill="#f6f0e7" stroke="#d17a32" stroke-width="3" />
      <text x="636" y="139" fill="#e27520">E</text>
      <circle cx="846" cy="324" r="11" fill="#f6f0e7" stroke="#0d6870" stroke-width="3" />
      <text x="846" y="325" fill="#0d6870">F</text>
    </g>
    <text x="88" y="378" fill="#6b5f54" font-size="12" font-weight="700">Day 1</text>
    <text x="778" y="378" fill="#6b5f54" font-size="12" font-weight="700">Day 30</text>
  </svg>
</div>
<table class="budget-guide">
  <tr><th>Key</th><th>What it shows</th></tr>
  <tr><td class="marker-cell">A</td><td>Most of the monthly budget is still available, so we can learn before pushing spend.</td></tr>
  <tr><td class="marker-cell">B</td><td>Day-to-day swings in CPC, demand, and clicks are normal early on.</td></tr>
  <tr><td class="marker-cell">C</td><td>We refine search terms and traffic while keeping daily spend inside the healthy band.</td></tr>
  <tr><td class="marker-cell">D</td><td>A quieter day is not always a problem. Auction conditions and CPC move too.</td></tr>
  <tr><td class="marker-cell">E</td><td>Spend steps up as results and intent become clearer.</td></tr>
  <tr><td class="marker-cell">F</td><td>Remaining budget eases down through the month instead of front-loading spend.</td></tr>
</table>
"""
    return section(
        "Budget",
        "How We Protect Your Budget While Improving Performance",
        "This page shows how the approved monthly budget turns into daily pacing, why spend should not be front-loaded, and how we keep room to improve once real search data appears.",
        body,
    )


def budget_learning_section(budget: BudgetPlan) -> str:
    body = f"""
<div class="budget-section-head">
  <div class="budget-accent"></div>
  <div>
    <h2>Why spend increases as performance gets clearer</h2>
    <p>Early spend is intentionally cautious. As waste is cut and signals improve, more of the same monthly budget can be committed with confidence.</p>
  </div>
</div>
<div class="budget-split">
  <div class="budget-chart-card">
    <svg class="budget-svg-ramp" viewBox="0 0 540 300" role="img" aria-label="Confidence in spending rises from early to late month">
      <defs>
        <linearGradient id="ramp-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#0d6870" stop-opacity="0.18" />
          <stop offset="100%" stop-color="#0d6870" stop-opacity="0.02" />
        </linearGradient>
      </defs>
      <rect x="56" y="36" width="464" height="232" fill="rgba(255,255,255,0.35)" stroke="#c9b79d" stroke-width="1.2" rx="3" />
      <line x1="56" y1="268" x2="520" y2="268" stroke="#9a8b78" stroke-width="1.8" />
      <line x1="56" y1="36" x2="56" y2="268" stroke="#9a8b78" stroke-width="1.8" />
      <g stroke="#d7c3aa" stroke-width="1" stroke-dasharray="3 5">
        <line x1="56" y1="210" x2="520" y2="210" />
        <line x1="56" y1="150" x2="520" y2="150" />
        <line x1="56" y1="90" x2="520" y2="90" />
      </g>
      <text x="8" y="96" fill="#6b5f54" font-size="11" font-weight="700">More</text>
      <text x="10" y="272" fill="#6b5f54" font-size="11" font-weight="700">Less</text>
      <path d="M 56 252 C 120 246, 180 220, 240 186 C 300 150, 360 102, 520 48 L 520 268 L 56 268 Z" fill="url(#ramp-fill)" />
      <path d="M 56 252 C 120 246, 180 220, 240 186 C 300 150, 360 102, 520 48" fill="none" stroke="#0d6870" stroke-width="5" stroke-linecap="round" />
      <g font-size="12" font-weight="800" text-anchor="middle" dominant-baseline="middle">
        <circle cx="118" cy="244" r="11" fill="#f6f0e7" stroke="#0d6870" stroke-width="3" />
        <text x="118" y="245" fill="#0d6870">A</text>
        <circle cx="232" cy="198" r="11" fill="#f6f0e7" stroke="#0d6870" stroke-width="3" />
        <text x="232" y="199" fill="#0d6870">B</text>
        <circle cx="352" cy="128" r="11" fill="#f6f0e7" stroke="#0d6870" stroke-width="3" />
        <text x="352" y="129" fill="#0d6870">C</text>
        <circle cx="488" cy="56" r="11" fill="#f6f0e7" stroke="#0d6870" stroke-width="3" />
        <text x="488" y="57" fill="#0d6870">D</text>
      </g>
      <text x="58" y="292" fill="#6b5f54" font-size="11" font-weight="700">Early month</text>
      <text x="404" y="292" fill="#6b5f54" font-size="11" font-weight="700">Later month</text>
    </svg>
  </div>
  <table class="budget-guide" style="margin-top:0;">
    <tr><th>Step</th><th>What improves</th></tr>
    <tr><td class="marker-cell">A</td><td>We see which searches are worth paying for before scaling.</td></tr>
    <tr><td class="marker-cell">B</td><td>Low-value traffic is trimmed.</td></tr>
    <tr><td class="marker-cell">C</td><td>CPC, conversions, and lead quality become easier to read.</td></tr>
    <tr><td class="marker-cell">D</td><td>We can raise spend because the data behind it is cleaner.</td></tr>
  </table>
</div>
<div class="budget-section-head" style="margin-top:20px;">
  <div class="budget-accent"></div>
  <h2>What this means for your campaign</h2>
</div>
<div class="budget-takeaways">
  <div class="budget-tile"><h3>We pace the full month</h3><p>Daily spend and clicks will move. The aim is healthy pacing through day 30.</p></div>
  <div class="budget-tile"><h3>Starting lighter protects budget</h3><p>Early limits leave room to learn before we push winning areas.</p></div>
  <div class="budget-tile"><h3>CPC changes click volume</h3><p>The same dollars buy more or fewer clicks as auctions shift.</p></div>
  <div class="budget-tile"><h3>Later spend is intentional</h3><p>Increases follow clearer performance, not reactive day-to-day changes.</p></div>
</div>
<div class="confirm-strip">
  <h3>Please confirm</h3>
  <p>Budget: confirm the {money(budget.monthly_budget)} monthly budget before launch.</p>
</div>
"""
    return section(
        "Budget",
        "Why Spend Increases As Performance Gets Clearer",
        "This page explains the operating logic behind the pacing curve. We do not spend more because the campaign is guessing. We spend more when the evidence is cleaner.",
        body,
    )


def capacity_goal_section(goal_facts: dict | None) -> str:
    if not goal_facts:
        return ""
    title = esc(goal_facts.get("section_title") or "Capacity And Lead Goal")
    target_clients = goal_facts.get("initial_new_client_goal", 2)
    close_rate = float(goal_facts.get("planning_close_rate", 0.5) or 0.5)
    minimum_leads = goal_facts.get("minimum_qualified_leads", 4)
    lead_range = goal_facts.get("planning_qualified_lead_range", "4 to 8")
    notes = list(goal_facts.get("capacity_notes", []))
    pacing = goal_facts.get("pacing_recommendation")
    assumption = goal_facts.get("assumption_note")
    if pacing:
        notes.append(str(pacing))
    if assumption:
        notes.append(str(assumption))
    note_items = "".join(f"<li>{esc(note)}</li>" for note in notes)
    body = f"""
<div class="goal-grid">
  <div class="goal-card"><div class="label">Initial new client goal</div><strong>{esc(target_clients)}</strong></div>
  <div class="goal-card"><div class="label">Planning close rate</div><strong>{int(close_rate * 100)}%</strong></div>
  <div class="goal-card"><div class="label">Minimum leads needed</div><strong>{esc(minimum_leads)}</strong></div>
  <div class="goal-card"><div class="label">Planning lead range</div><strong>{esc(lead_range)}</strong></div>
</div>
<div class="subsection-header">How we use this goal</div>
<p>The campaign should create enough qualified conversations to support the client goal without forcing spend before capacity and lead quality are clear.</p>
<ul class="goal-list">{note_items}</ul>
"""
    return section(
        "Goals",
        title,
        "This section appears only when the client gives capacity, lead, or growth goals that should guide campaign pacing.",
        body,
    )


def strategy_section(
    summary: CampaignSummary,
    website_scan: dict,
    service_catalog: dict,
    geo_strategy: dict,
) -> str:
    facts = website_scan.get("extracted_facts", {})
    services = service_catalog.get("active_services_for_staging", [])
    locations = geo_strategy.get("targeting", [])
    body = f"""
<div class="subsection-header">What we are proposing</div>
<div class="card-grid">
  <div class="insight-card">
    <h3>Search-first launch</h3>
    <p>The campaign is built for people already searching for the client's services, not broad awareness. All keywords use phrase match for cleaner early data.</p>
  </div>
  <div class="insight-card">
    <h3>Website-backed services</h3>
    <p>The launch focuses on services visible on the site: {esc(', '.join(services[:8]))}.</p>
  </div>
  <div class="insight-card">
    <h3>Priority still needs input</h3>
    <p>Confirm which services should receive the most traffic before the launch budget is finalized.</p>
  </div>
  <div class="insight-card">
    <h3>Launch review status</h3>
    <p>The campaign build validates cleanly, but remains paused until budget, service priority, and your approval decisions are confirmed.</p>
  </div>
</div>
<div class="subsection-header">Audience and service area</div>
<div class="two-col">
  <div class="source-card">
    <p><strong>Audience from source material:</strong> {esc(', '.join(facts.get('audience', [])))}</p>
    <p style="margin-top:8px;"><strong>Positioning:</strong> {esc(facts.get('primary_positioning', ''))}</p>
  </div>
  <div class="source-card">
    <p><strong>Targeting:</strong> {esc(', '.join(item.get('location', '') for item in locations))}</p>
    <p style="margin-top:8px;"><strong>Targeting method:</strong> {esc(geo_strategy.get('targeting_method', 'Location of presence'))}</p>
  </div>
</div>
"""
    return section(
        "Strategy",
        "A Controlled New Search Campaign",
        "This is the first version of the campaign plan. It keeps the launch focused on people already looking for the prepared services, then gives you a clear way to approve services, priorities, copy, and regions before spend begins.",
        body,
    )


def department_operations_section(build_dir: Path) -> str:
    paths = {
        "conversion": build_dir / "conversion_tracking_audit.json",
        "evidence": build_dir / "evidence_quality_report.json",
        "cadence": build_dir / "optimization_cadence_plan.json",
        "bid": build_dir / "bid_strategy_recommendation.json",
        "audience": build_dir / "audience_mode_audit.json",
        "policy": build_dir / "policy_disapproval_audit.json",
    }
    if not any(path.exists() for path in paths.values()):
        return ""
    data = {key: read_json(path) if path.exists() else {} for key, path in paths.items()}
    conversion = data["conversion"]
    evidence = data["evidence"]
    bid = data["bid"]
    audience = data["audience"]
    policy = data["policy"]
    cadence = data["cadence"].get("cadence", {})
    cadence_items = "".join(
        f"<li><strong>{esc(name.title())}:</strong> {esc(', '.join(items[:4]))}</li>"
        for name, items in cadence.items()
    )
    body = f"""
<div class="card-grid">
  <div class="insight-card">
    <h3>Conversion readiness</h3>
    <p>Status: {esc(conversion.get('status', 'review_required'))}. Recording actions: {esc(conversion.get('summary', {}).get('recording_actions', 0))}.</p>
  </div>
  <div class="insight-card">
    <h3>Evidence quality</h3>
    <p>Status: {esc(evidence.get('status', 'review_required'))}. Weak or untested evidence stays in human review instead of driving automatic cuts.</p>
  </div>
  <div class="insight-card">
    <h3>Bidding path</h3>
    <p>Recommended phase: {esc(bid.get('recommended_phase', 'data_collection'))}. Recommended strategy: {esc(bid.get('recommended_strategy', 'manual_cpc'))}.</p>
  </div>
  <div class="insight-card">
    <h3>Launch controls</h3>
    <p>Audience audit: {esc(audience.get('status', 'review_required'))}. Policy audit: {esc(policy.get('status', 'review_required'))}.</p>
  </div>
</div>
<div class="subsection-header">Optimization cadence after launch</div>
<ul class="goal-list">{cadence_items}</ul>
<div class="confirm-strip">
  <h3>Please confirm</h3>
  <p>Measurement: confirm conversion tracking and policy status before any staged campaign moves from paused review to active launch.</p>
</div>
"""
    return section(
        "Operations",
        "Department Standards Added To The Build",
        "This review now includes the department training checks that affect launch readiness and post-launch management.",
        body,
    )


def campaign_structure_section(summary: CampaignSummary) -> str:
    campaign_label = "campaign" if len(summary.campaigns) == 1 else "campaigns"
    body = f"""
<div class="two-col">
  <div class="insight-card">
    <h3>Launch shape</h3>
    <p>The current launch uses {len(summary.campaigns)} controlled Search {campaign_label} with {summary.ad_groups} service and geo intent ad groups. This keeps early learning clean and easier to review.</p>
  </div>
  <div class="insight-card">
    <h3>Expansion rule</h3>
    <p>City ad groups should be added only when approved city priorities are supplied or performance data shows a region needs its own copy and reporting focus.</p>
  </div>
</div>
<div class="structure-flow" aria-label="Current campaign structure and future expansion path">
  <svg viewBox="0 0 900 470" role="img" aria-label="One current Search campaign can later split by services or regions when performance supports it">
    <rect class="flow-current" x="34" y="52" width="184" height="86" rx="8"/>
    <text class="flow-label" x="126" y="88" text-anchor="middle">Current</text>
    <text class="flow-small" x="126" y="114" text-anchor="middle">{len(summary.campaigns)} Search {campaign_label.title()}</text>
    <path class="flow-line" d="M218 95 C270 95, 288 95, 334 95"/>
    <rect class="flow-current" x="334" y="52" width="202" height="86" rx="8"/>
    <text class="flow-label" x="435" y="88" text-anchor="middle">{summary.ad_groups} Geo Intent Ad Groups</text>
    <text class="flow-small" x="435" y="114" text-anchor="middle">actual launch structure</text>
    <path class="flow-line" d="M536 95 C610 95, 620 64, 692 64"/>
    <path class="flow-line" d="M536 95 C610 95, 620 126, 692 126"/>
    <text class="flow-label" x="710" y="70">Priority services</text>
    <text class="flow-label" x="710" y="132">Support services</text>

    <rect class="flow-box" x="34" y="198" width="184" height="86" rx="8"/>
    <text class="flow-label" x="126" y="234" text-anchor="middle">Later Option</text>
    <text class="flow-small" x="126" y="260" text-anchor="middle">Split by service demand</text>
    <path class="flow-muted" d="M218 241 C300 241, 310 214, 392 214"/>
    <path class="flow-muted" d="M218 241 C300 241, 310 270, 392 270"/>
    <rect class="flow-future" x="392" y="184" width="198" height="62" rx="8"/>
    <rect class="flow-future" x="392" y="254" width="198" height="62" rx="8"/>
    <text class="flow-label" x="491" y="221" text-anchor="middle">Primary Services</text>
    <text class="flow-label" x="491" y="291" text-anchor="middle">Secondary Services</text>
    <path class="flow-muted" d="M590 215 C640 215, 652 196, 700 196"/>
    <path class="flow-muted" d="M590 215 C640 215, 652 234, 700 234"/>
    <path class="flow-muted" d="M590 285 C640 285, 652 266, 700 266"/>
    <path class="flow-muted" d="M590 285 C640 285, 652 304, 700 304"/>
    <text class="flow-small" x="716" y="200">highest demand services</text>
    <text class="flow-small" x="716" y="238">strongest lead quality</text>
    <text class="flow-small" x="716" y="270">secondary demand</text>
    <text class="flow-small" x="716" y="308">specialty follow-up</text>

    <rect class="flow-box" x="34" y="342" width="184" height="86" rx="8"/>
    <text class="flow-label" x="126" y="378" text-anchor="middle">Later Option</text>
    <text class="flow-small" x="126" y="404" text-anchor="middle">Split by regional demand</text>
    <path class="flow-muted" d="M218 385 C300 385, 310 358, 392 358"/>
    <path class="flow-muted" d="M218 385 C300 385, 310 414, 392 414"/>
    <rect class="flow-future" x="392" y="328" width="198" height="62" rx="8"/>
    <rect class="flow-future" x="392" y="398" width="198" height="62" rx="8"/>
    <text class="flow-label" x="491" y="365" text-anchor="middle">Primary Regions</text>
    <text class="flow-label" x="491" y="435" text-anchor="middle">Secondary Regions</text>
    <path class="flow-muted" d="M590 359 C640 359, 652 340, 700 340"/>
    <path class="flow-muted" d="M590 359 C640 359, 652 378, 700 378"/>
    <path class="flow-muted" d="M590 429 C640 429, 652 410, 700 410"/>
    <path class="flow-muted" d="M590 429 C640 429, 652 448, 700 448"/>
    <text class="flow-small" x="716" y="344">top priority states</text>
    <text class="flow-small" x="716" y="382">top cities or metros</text>
    <text class="flow-small" x="716" y="414">current strongest markets</text>
    <text class="flow-small" x="716" y="452">later regional tests</text>
  </svg>
</div>
<div class="flow-note-grid">
  <div class="flow-note"><h3>One campaign now</h3><p>The first launch stays compact so the early budget is not spread too thin.</p></div>
  <div class="flow-note"><h3>Split later by proof</h3><p>Future campaign splits should follow lead quality, conversion signals, and search demand.</p></div>
  <div class="flow-note"><h3>No extra campaigns yet</h3><p>The service and regional splits shown here are future paths, not active launch campaigns.</p></div>
</div>
"""
    return section(
        "Campaign Structure",
        "How The Campaign Can Grow Over Time",
        "The launch starts compact. Future campaigns can split by service or region only after the data shows where separate budgets and reporting would help.",
        body,
    )


def ad_groups_section(summary: CampaignSummary, rows: list[dict[str, str]]) -> str:
    rows_for_ad_groups = ad_group_rows(rows)
    keyword_counts = keyword_counts_by_ad_group(rows)
    table_rows = "".join(
        f"<tr><td>{esc(row.get('Ad Group'))}</td><td>{keyword_counts.get(row.get('Ad Group', ''), 0)}</td><td>Paused</td></tr>"
        for row in rows_for_ad_groups
    )
    body = f"""
<div class="two-col">
  <div class="insight-card">
    <h3>Services ready for ads</h3>
    <p>{summary.ad_groups} ad groups organize general, near-me, state, and approved city intent for the first launch.</p>
  </div>
  <div class="insight-card">
    <h3>Keyword control</h3>
    <p>{summary.phrase_keywords} phrase keywords and {summary.negative_phrase_keywords} negative phrase keywords are prepared. Active launch keywords use phrase match.</p>
  </div>
</div>
<div class="subsection-header">Ad groups ready for review</div>
<table>
  <tr><th>Ad group</th><th>Phrase keywords</th><th>Status</th></tr>
  {table_rows}
</table>
<div class="confirm-strip">
  <h3>Please confirm</h3>
  <p>Ad groups: confirm these are the services you want ads to run for and flag any service that should receive priority traffic.</p>
</div>
<div class="continuation-header">Campaign detail continues with representative ad previews</div>
"""
    return section(
        "Ad Groups",
        "Services We Are Running Ads For",
        "These are the service areas currently prepared in the Google Ads Editor file. Confirm the list is complete and identify which services should receive the most traffic first.",
        body,
    )


def targeting_section(geo_strategy: dict) -> str:
    targeting = geo_strategy.get("targeting", [])
    location_names = [item.get("location", "") for item in targeting]
    chips = "".join(f'<span class="state-chip">{esc(name)}</span>' for name in location_names)
    location_label = ", ".join(location_names) if location_names else "No location rows prepared"
    review_rows = [
        (
            "Country",
            location_label,
            "Ready for review",
            "Confirm these staged locations are the correct launch markets.",
        ),
        (
            "Top states",
            "Top 5 states",
            "Needed",
            "List only if state priorities differ from the current staged locations.",
        ),
        (
            "City",
            "Top 5 cities or metros",
            "Needed",
            "List the cities or metro areas where spend should concentrate first.",
        ),
        (
            "Current work",
            "Largest current markets",
            "Needed",
            "Tell us where most current clients or organizational relationships are located.",
        ),
        (
            "Fastest wins",
            "Priority growth markets",
            "Needed",
            "Tell us whether there are focus areas where stronger referrals, recognition, or capacity can produce faster wins.",
        ),
        (
            "Exclusions",
            "States, cities, or ZIPs",
            "Needed",
            "Identify anywhere inside the staged markets where the campaign should not spend.",
        ),
    ]
    review_table_rows = "".join(
        f"<tr><td>{esc(area_type)}</td><td>{esc(area)}</td><td>{esc(status)}</td><td>{esc(note)}</td></tr>"
        for area_type, area, status, note in review_rows
    )
    body = f"""
<div class="targeting-panel compact">
  <div class="subsection-header" style="margin-top:0;">Current targeting and review items</div>
  <p>The current build targets {esc(location_label)}. Treat this as a launch review item until the final market scope is approved.</p>
  <div style="margin:10px 0;">{chips}</div>
  <table class="targeting-table">
    <colgroup><col class="type-col"><col class="area-col"><col class="status-col"><col></colgroup>
    <tr><th>Area type</th><th>Area</th><th>Status</th><th>What to confirm</th></tr>
      {review_table_rows}
  </table>
  <p style="margin-top:10px;font-size:11px;color:#6b5c4b;">Location targeting can use countries, areas within a country, radius targets, or location groups. Source: <a href="https://support.google.com/google-ads/answer/1722043">Google Ads location targeting</a>.</p>
  <div class="confirm-strip">
    <h3>Please confirm</h3>
    <p>Regional targeting: confirm the staged markets, any city priorities, current strongest markets, fastest-win focus areas, and exclusions.</p>
  </div>
</div>
"""
    return section(
        "Regional Targeting",
        "Where The Campaign Is Set To Reach",
        "The current plan stays table-based so launch geography is easy to review. Confirm the staged markets or provide city priorities before launch.",
        body,
    )


def ad_preview_url(example: RsaExample) -> str:
    host = example.final_url.replace("https://", "").replace("http://", "").strip("/")
    paths = [path for path in (example.path_1, example.path_2) if path]
    return host + ("/" + "/".join(paths) if paths else "")


def service_logic_notes(example: RsaExample) -> str:
    logic = example.service_logic or {}
    if not logic:
        return ""
    cards = [
        ("Who this is for", logic.get("buyer", "")),
        ("What they are buying", logic.get("service_mechanism", "")),
        ("Why it matters", logic.get("outcome", "")),
        ("What to confirm", "Confirm this interpretation matches the service and buyer."),
    ]
    return "".join(
        f"""
<div class="service-logic-card">
  <h3>{esc(title)}</h3>
  <p>{esc(text)}</p>
</div>
"""
        for title, text in cards
        if text
    )


def ad_copy_section(example: RsaExample, index: int, total: int) -> str:
    headline_preview = " | ".join(example.headlines[:3])
    desc_preview = example.descriptions[0] if example.descriptions else ""
    headline_rows = "".join(
        f"<tr><td>{slot}</td><td>{esc(value)}</td><td>{len(value)}</td></tr>"
        for slot, value in enumerate(example.headlines, start=1)
    )
    description_rows = "".join(
        f"<tr><td>{slot}</td><td>{esc(value)}</td><td>{len(value)}</td></tr>"
        for slot, value in enumerate(example.descriptions, start=1)
    )
    body = f"""
<div class="ad-card">
  <h3>{esc(example.ad_group)}</h3>
  <div class="ad-preview">
    <div class="sponsored">Sponsored</div>
    <div class="url">{esc(ad_preview_url(example))}</div>
    <div class="headline">{esc(headline_preview)}</div>
    <div class="desc">{esc(desc_preview)}</div>
  </div>
</div>
<div class="service-logic-grid">{service_logic_notes(example)}</div>
<div class="subsection-header">Headline examples</div>
<p class="audit-note">Headline quality gate: {esc(example.headline_quality_status)}. This table shows 15 complete headlines with character counts for launch review.</p>
<table class="ad-copy-table">
  <colgroup><col class="slot-col"><col><col class="char-col"></colgroup>
  <tr><th>#</th><th>Headline</th><th>Chars</th></tr>{headline_rows}
</table>
<div class="subsection-header">Description examples</div>
<table class="ad-copy-table">
  <colgroup><col class="slot-col"><col><col class="char-col"></colgroup>
  <tr><th>#</th><th>Description</th><th>Chars</th></tr>{description_rows}
</table>
<div class="confirm-strip">
  <h3>Please confirm</h3>
  <p>Ads: confirm this ad copy direction for {esc(example.ad_group)} or note any headline or description changes needed.</p>
</div>
"""
    return f"""
<section class="section pdf-page ad-copy-page">
  <div class="section-header">
    <div class="eyebrow">Ad Copy</div>
    <h1>{esc(example.ad_group)}</h1>
    <p>Ad group {index} of {total}. Review the full headline and description set for this service before launch.</p>
  </div>
  {body}
</section>
"""


def ads_sections(examples: list[RsaExample]) -> str:
    total = len(examples)
    return "".join(ad_copy_section(example, index, total) for index, example in enumerate(examples, start=1))


def approval_section(
    summary: CampaignSummary,
    rows: list[dict[str, str]],
    geo_strategy: dict,
    budget: BudgetPlan,
) -> str:
    del rows
    targeting = geo_strategy.get("targeting", [])
    location_names = [item.get("location", "") for item in targeting if item.get("location")]
    location_label = ", ".join(location_names) if location_names else "the approved service area"
    checklist_items = [
        (
            "Approve ad group structure",
            f"{summary.ad_groups} service-specific ad groups are ready.",
            "Approve",
            False,
        ),
        (
            "Approve responsive search ads",
            f"{summary.rsa_rows} ads are written around the service categories.",
            "Approve",
            False,
        ),
        (
            "Confirm regional targeting",
            f"{location_label} is the current reach. Confirm this state split or send priority market changes.",
            "Confirm",
            True,
        ),
        (
            "Approve monthly budget",
            f"Proposed launch budget is {money(budget.monthly_budget)}/month.",
            "Approve",
            False,
        ),
    ]
    checklist = "".join(
        f"""
<div class="approval-row">
  <div class="approval-icon{' warn' if warn else ''}">{'!' if warn else '&#10003;'}</div>
  <div class="approval-copy">
    <h3>{esc(title)}</h3>
    <p>{esc(text)}</p>
  </div>
  <div class="approval-button{' warn' if warn else ''}">{esc(action)}</div>
</div>
"""
        for title, text, action, warn in checklist_items
    )
    body = f"""
<div class="launch-brief">
  <div class="launch-brief-grid">
    <div>
      <div class="launch-kicker">Launch brief</div>
      <h2>Campaign setup is ready. Confirm targeting.</h2>
      <p>The campaign is prepared with service-based structure, responsive search ads, and a proposed monthly budget. One regional coverage decision remains before launch.</p>
      <div class="launch-actions">
        <span class="launch-pill primary">Approve Core Setup</span>
        <span class="launch-pill secondary">Confirm Regions</span>
      </div>
    </div>
    <div class="launch-stat-list">
      <div class="launch-stat"><span>Ad Groups</span><span>{summary.ad_groups}</span></div>
      <div class="launch-stat"><span>Ads</span><span>{summary.rsa_rows}</span></div>
      <div class="launch-stat"><span>Regions</span><span>{len(location_names) or 1}</span></div>
      <div class="launch-stat"><span>Budget</span><span>{money(budget.monthly_budget)}</span></div>
    </div>
  </div>
</div>
<div class="approval-list">{checklist}</div>
"""
    return section(
        "Approval",
        "Ready for Approval",
        "The core campaign build is ready. Confirm service priority, ad copy, regional targeting, and budget so the launch can move forward.",
        body,
    )


def build_html(
    *,
    client: str,
    date_label: str,
    staging_csv: Path,
    website_scan_json: Path,
    service_catalog_json: Path,
    geo_strategy_json: Path,
    source_attribution_json: Path,
    service_logic_research_json: Path | None = None,
    budget: BudgetPlan | None = None,
    goal_facts: dict | None = None,
) -> str:
    rows = read_staging(staging_csv)
    service_logic_map = service_logic_by_name(read_json(service_logic_research_json)) if service_logic_research_json and service_logic_research_json.exists() else None
    headline_audit = audit_rows(rows, service_logic_map)
    if headline_audit["status"] != "pass":
        failing = [
            issue["rule"]
            for audit in headline_audit["audits"]
            for issue in audit.get("issues", [])
        ]
        raise ValueError(f"RSA headline quality audit failed before report export: {sorted(set(failing))}")
    summary = summarize_staging(rows)
    website_scan = read_json(website_scan_json)
    service_catalog = read_json(service_catalog_json)
    geo_strategy = read_json(geo_strategy_json)
    source_attribution = read_json(source_attribution_json)
    examples = select_rsa_examples(rows, service_logic_map=service_logic_map)
    budget = budget or BudgetPlan(monthly_budget=3000)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{esc(client)} New Campaign Review</title>
  <style>{css()}</style>
</head>
<body>
  {cover(client, date_label, summary)}
  {overview_section(summary)}
  {department_operations_section(staging_csv.parent)}
  {campaign_structure_section(summary)}
  {ad_groups_section(summary, rows)}
  {ads_sections(examples)}
  {targeting_section(geo_strategy)}
  {capacity_goal_section(goal_facts)}
  {budget_pacing_section(budget)}
  {budget_learning_section(budget)}
  {approval_section(summary, rows, geo_strategy, budget)}
</body>
</html>
"""


def write_report(
    *,
    client: str,
    date_label: str,
    staging_csv: Path,
    website_scan_json: Path,
    service_catalog_json: Path,
    geo_strategy_json: Path,
    source_attribution_json: Path,
    output_html: Path,
    service_logic_research_json: Path | None = None,
    budget: BudgetPlan | None = None,
    goal_facts: dict | None = None,
) -> Path:
    html_text = build_html(
        client=client,
        date_label=date_label,
        staging_csv=staging_csv,
        website_scan_json=website_scan_json,
        service_catalog_json=service_catalog_json,
        geo_strategy_json=geo_strategy_json,
        source_attribution_json=source_attribution_json,
        service_logic_research_json=service_logic_research_json,
        budget=budget,
        goal_facts=goal_facts,
    )
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(html_text, encoding="utf-8")
    return output_html


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a new-campaign review report.")
    parser.add_argument("--manifest-json", type=Path, help="Optional one-shot run manifest.")
    parser.add_argument("--client")
    parser.add_argument("--date")
    parser.add_argument("--staging-csv", type=Path)
    parser.add_argument("--website-scan-json", type=Path)
    parser.add_argument("--service-catalog-json", type=Path)
    parser.add_argument("--service-logic-research-json", type=Path)
    parser.add_argument("--geo-strategy-json", type=Path)
    parser.add_argument("--source-attribution-json", type=Path)
    parser.add_argument("--monthly-budget", type=float, default=3000)
    parser.add_argument("--cpc-low", type=float)
    parser.add_argument("--cpc-high", type=float)
    parser.add_argument("--goal-facts-json", type=Path)
    parser.add_argument("--output-html", type=Path)
    parser.add_argument("--output-email", type=Path)
    parser.add_argument("--output-pdf", type=Path)
    parser.add_argument("--visual-audit-dir", type=Path)
    args = parser.parse_args()

    if args.manifest_json:
        manifest = read_json(args.manifest_json)
        artifacts = manifest.get("artifacts", {})
        args.client = args.client or manifest.get("client")
        args.date = args.date or manifest.get("date_label")
        args.staging_csv = args.staging_csv or Path(artifacts.get("staging_csv", ""))
        args.website_scan_json = args.website_scan_json or Path(artifacts.get("website_scan", ""))
        args.service_catalog_json = args.service_catalog_json or Path(artifacts.get("service_catalog", ""))
        if not args.service_logic_research_json and artifacts.get("service_logic_research"):
            args.service_logic_research_json = Path(artifacts["service_logic_research"])
        args.geo_strategy_json = args.geo_strategy_json or Path(artifacts.get("geo_strategy", ""))
        args.source_attribution_json = args.source_attribution_json or Path(artifacts.get("source_attribution", ""))
        args.output_html = args.output_html or Path(artifacts.get("client_report_html", ""))
        args.output_pdf = args.output_pdf or Path(artifacts.get("client_report_pdf", ""))
        args.output_email = args.output_email or Path(artifacts.get("client_email_draft", ""))
        if not args.goal_facts_json and artifacts.get("goal_facts"):
            args.goal_facts_json = Path(artifacts["goal_facts"])
        visual_dir = artifacts.get("visual_audit_dir")
        args.visual_audit_dir = args.visual_audit_dir or (Path(visual_dir) if visual_dir else None)

    required = {
        "--client": args.client,
        "--date": args.date,
        "--staging-csv": args.staging_csv,
        "--website-scan-json": args.website_scan_json,
        "--service-catalog-json": args.service_catalog_json,
        "--geo-strategy-json": args.geo_strategy_json,
        "--source-attribution-json": args.source_attribution_json,
        "--output-html": args.output_html,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        parser.error(f"missing required arguments: {', '.join(missing)}")

    budget = BudgetPlan(args.monthly_budget, args.cpc_low, args.cpc_high)
    goal_facts = read_json(args.goal_facts_json) if args.goal_facts_json else None

    try:
        html_path = write_report(
            client=args.client,
            date_label=args.date,
            staging_csv=args.staging_csv,
            website_scan_json=args.website_scan_json,
            service_catalog_json=args.service_catalog_json,
            geo_strategy_json=args.geo_strategy_json,
            source_attribution_json=args.source_attribution_json,
            service_logic_research_json=args.service_logic_research_json,
            output_html=args.output_html,
            budget=budget,
            goal_facts=goal_facts,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    findings, summary = audit_html(html_path)
    errors = [finding for finding in findings if finding.severity == "error"]
    if errors:
        for finding in errors:
            print(f"error: {finding.code}: {finding.message}", file=sys.stderr)
        return 1

    if args.output_pdf:
        pdf_path = export_pdf(html_path, args.output_pdf)
        if args.visual_audit_dir:
            audits, _pages_dir = audit_pdf(pdf_path, args.visual_audit_dir, 0.055, 72)
            failures = [audit for audit in audits if audit.status == "fail"]
            if failures:
                for failure in failures:
                    print(f"error: visual audit failed page {failure.page}", file=sys.stderr)
                return 1
        print(f"wrote {pdf_path}")
    else:
        print(f"wrote {html_path}")
    email_path = args.output_email or html_path.with_name("client_email_draft.md")
    write_client_email_draft(
        email_path,
        EmailDraftInput(
            client=args.client,
            date_label=args.date,
            report_type="new campaign build",
            pdf_path=args.output_pdf or html_path.with_suffix(".pdf"),
            summary=summarize_staging(read_staging(args.staging_csv)),
        ),
    )
    print(f"static_audit sections={summary['sections']} errors={summary['errors']} warnings={summary['warnings']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
