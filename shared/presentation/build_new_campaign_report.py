#!/usr/bin/env python3
"""Build a client-facing report for a new campaign build."""

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
    from .pdf_visual_audit import audit_pdf
    from .report_quality_audit import audit_html
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from shared.presentation.build_review_doc import export_pdf
    from shared.presentation.pdf_visual_audit import audit_pdf
    from shared.presentation.report_quality_audit import audit_html


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


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_staging(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-16", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter="\t")]


def summarize_staging(rows: list[dict[str, str]]) -> CampaignSummary:
    campaigns = sorted({row["Campaign"] for row in rows if row.get("Campaign")})
    ad_groups = sum(
        1
        for row in rows
        if row.get("Ad Group") and not row.get("Keyword") and not row.get("Ad type")
    )
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


def select_rsa_examples(rows: list[dict[str, str]], limit: int = 4) -> list[RsaExample]:
    examples: list[RsaExample] = []
    for row in rows:
        if row.get("Ad type") != "Responsive search ad":
            continue
        examples.append(
            RsaExample(
                campaign=row.get("Campaign", ""),
                ad_group=row.get("Ad Group", ""),
                final_url=row.get("Final URL", ""),
                path_1=row.get("Path 1", ""),
                path_2=row.get("Path 2", ""),
                headlines=[row.get(f"Headline {index}", "") for index in range(1, 16)],
                descriptions=[row.get(f"Description {index}", "") for index in range(1, 5)],
            )
        )
        if len(examples) == limit:
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
.budget-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 22px;
}
.budget-card {
  background: #fffaf1;
  border: 1px solid #dfd2bf;
  padding: 18px;
}
.budget-card .label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #746656;
  font-weight: 900;
}
.budget-card strong {
  display: block;
  margin-top: 8px;
  font-size: 28px;
  color: #185c62;
}
.budget-chart {
  background: #fffaf1;
  border: 1px solid #dfd2bf;
  padding: 18px;
}
.budget-viz-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.line-chart {
  width: 100%;
  height: 232px;
}
.axis-line {
  stroke: #d5c8b7;
  stroke-width: 2;
}
.grid-line {
  stroke: #eadfce;
  stroke-width: 1;
}
.budget-line {
  fill: none;
  stroke: #185c62;
  stroke-width: 4;
}
.scenario-low {
  fill: none;
  stroke: #9cbfba;
  stroke-width: 3;
}
.scenario-mid {
  fill: none;
  stroke: #2f6f76;
  stroke-width: 3;
}
.scenario-high {
  fill: none;
  stroke: #c8753f;
  stroke-width: 3;
}
.chart-label {
  font-size: 10px;
  fill: #6b5c4b;
  font-weight: 800;
}
.legend-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
  font-size: 11px;
  color: #5e5144;
}
.legend-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  margin-right: 5px;
}
.chart-note {
  margin-top: 12px;
  font-size: 12px;
  color: #5e5144;
  line-height: 1.45;
}
.targeting-map {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 14px;
}
.map-panel {
  background: #fffaf1;
  border: 1px solid #dfd2bf;
  padding: 14px;
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
.mini-map {
  width: 100%;
  height: 260px;
}
.state-shape {
  fill: #d7e8e5;
  stroke: #185c62;
  stroke-width: 3;
}
.pin {
  fill: #c8753f;
  stroke: #fffaf1;
  stroke-width: 3;
}
.map-label {
  font-size: 13px;
  fill: #2f2b27;
  font-weight: 800;
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
    <p>A client-ready proposal for a new Google Ads Search campaign, built from website evidence and prepared for client review.</p>
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


def chart_polyline(values: list[float], *, width: int = 520, height: int = 172, pad: int = 28) -> str:
    low = min(values)
    high = max(values)
    span = high - low or 1
    points: list[str] = []
    for index, value in enumerate(values):
        x = pad + (width - pad * 2) * index / (len(values) - 1)
        y = pad + (height - pad * 2) * (1 - ((value - low) / span))
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def pacing_values(monthly_budget: float) -> tuple[list[float], list[float], list[float], list[float]]:
    days = list(range(1, 31))
    planned_weights = [0.72 + (day - 1) * (0.56 / 29) for day in days]
    low_weights = [0.86 + (day - 1) * (0.28 / 29) for day in days]
    high_weights = [0.58 + (day - 1) * (0.84 / 29) for day in days]

    def normalize(weights: list[float]) -> list[float]:
        total = sum(weights)
        return [monthly_budget * weight / total for weight in weights]

    planned_daily = normalize(planned_weights)
    low_daily = normalize(low_weights)
    high_daily = normalize(high_weights)
    remaining: list[float] = []
    spent = 0.0
    for value in planned_daily:
        spent += value
        remaining.append(max(monthly_budget - spent, 0))
    return remaining, low_daily, planned_daily, high_daily


def cpc_click_cards(budget: BudgetPlan) -> str:
    cpcs = [8.0, 13.0, 18.0]
    if budget.cpc_low and budget.cpc_high:
        midpoint = (budget.cpc_low + budget.cpc_high) / 2
        cpcs = [budget.cpc_low, midpoint, budget.cpc_high]
    cards = []
    for cpc in cpcs:
        clicks = budget.daily_budget / cpc
        cards.append(
            f"""
  <div class="budget-card">
    <div class="label">${cpc:.0f} CPC</div>
    <strong>{clicks:.0f}/day</strong>
  </div>
"""
        )
    return "".join(cards)


def budget_section(budget: BudgetPlan) -> str:
    remaining, low_daily, planned_daily, high_daily = pacing_values(budget.monthly_budget)
    body = f"""
<div class="budget-metrics">
  <div class="budget-card">
    <div class="label">Monthly Budget</div>
    <strong>${budget.monthly_budget:,.0f}</strong>
  </div>
  <div class="budget-card">
    <div class="label">Daily Average</div>
    <strong>${budget.daily_budget:,.0f}</strong>
  </div>
  <div class="budget-card">
    <div class="label">Planned Spend Curve</div>
    <strong style="font-size:20px;">Slower start, stronger finish</strong>
  </div>
</div>
<div class="budget-viz-grid">
  <div class="budget-chart">
    <div class="subsection-header" style="margin-top:0;">Budget remaining over 30 days</div>
    <svg class="line-chart" viewBox="0 0 520 220" role="img" aria-label="Budget remaining line chart">
      <line class="grid-line" x1="28" y1="58" x2="492" y2="58"/>
      <line class="grid-line" x1="28" y1="104" x2="492" y2="104"/>
      <line class="grid-line" x1="28" y1="150" x2="492" y2="150"/>
      <line class="axis-line" x1="28" y1="28" x2="28" y2="172"/>
      <line class="axis-line" x1="28" y1="172" x2="492" y2="172"/>
      <polyline class="budget-line" points="{chart_polyline(remaining)}"/>
      <text class="chart-label" x="30" y="205">Day 1</text>
      <text class="chart-label" x="450" y="205">Day 30</text>
      <text class="chart-label" x="38" y="42">${budget.monthly_budget:,.0f}</text>
      <text class="chart-label" x="38" y="166">$0</text>
    </svg>
    <div class="chart-note">The curve leaves more budget available while the campaign learns, then spends more confidently as search terms and service priorities become clearer.</div>
  </div>
  <div class="budget-chart">
    <div class="subsection-header" style="margin-top:0;">Daily spend scenarios</div>
    <svg class="line-chart" viewBox="0 0 520 220" role="img" aria-label="Daily spend scenario line chart">
      <line class="grid-line" x1="28" y1="58" x2="492" y2="58"/>
      <line class="grid-line" x1="28" y1="104" x2="492" y2="104"/>
      <line class="grid-line" x1="28" y1="150" x2="492" y2="150"/>
      <line class="axis-line" x1="28" y1="28" x2="28" y2="172"/>
      <line class="axis-line" x1="28" y1="172" x2="492" y2="172"/>
      <polyline class="scenario-low" points="{chart_polyline(low_daily)}"/>
      <polyline class="scenario-mid" points="{chart_polyline(planned_daily)}"/>
      <polyline class="scenario-high" points="{chart_polyline(high_daily)}"/>
      <text class="chart-label" x="30" y="205">Day 1</text>
      <text class="chart-label" x="450" y="205">Day 30</text>
    </svg>
    <div class="legend-row">
      <span><span class="legend-dot" style="background:#9cbfba"></span>Steady</span>
      <span><span class="legend-dot" style="background:#2f6f76"></span>Planned</span>
      <span><span class="legend-dot" style="background:#c8753f"></span>Faster ramp</span>
    </div>
    <div class="chart-note">These lines compare pacing choices. CPC changes the number of clicks the same budget can buy, not the approved monthly budget by itself.</div>
  </div>
</div>
<div class="subsection-header">Click examples at different CPCs</div>
<div class="budget-metrics">{cpc_click_cards(budget)}</div>
"""
    return section(
        "Budget",
        "Budget, Pacing, And Click Planning",
        "The launch budget should feel easy to approve. This page shows how the monthly budget turns into daily pacing, how spend can ramp as the campaign learns, and how CPC affects estimated click volume.",
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
    <p>The campaign is built for people already searching for therapy support, not broad awareness. All keywords use phrase match for cleaner early data.</p>
  </div>
  <div class="insight-card">
    <h3>Website-backed services</h3>
    <p>The launch focuses on services visible on the site: {esc(', '.join(services[:8]))}.</p>
  </div>
  <div class="insight-card">
    <h3>Priority still needs input</h3>
    <p>The client should confirm which services should receive the most traffic before the launch budget is finalized.</p>
  </div>
  <div class="insight-card">
    <h3>Launch review status</h3>
    <p>The CSV validates cleanly, but remains paused until budget, service priority, and client approval decisions are confirmed.</p>
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
        "This is the first version of the campaign plan. It keeps the launch focused on people already looking for therapy support, then gives the client a clear way to approve services, priorities, copy, and regions before spend begins.",
        body,
    )


def structure_section(summary: CampaignSummary, rows: list[dict[str, str]]) -> str:
    ad_group_rows = [
        row
        for row in rows
        if row.get("Ad Group") and not row.get("Keyword") and not row.get("Ad type")
    ]
    keyword_counts: dict[str, int] = {}
    for row in rows:
        if row.get("Criterion Type") == "Phrase":
            keyword_counts[row.get("Ad Group", "")] = keyword_counts.get(row.get("Ad Group", ""), 0) + 1
    table_rows = "".join(
        f"<tr><td>{esc(row.get('Ad Group'))}</td><td>{keyword_counts.get(row.get('Ad Group', ''), 0)}</td><td>Paused</td></tr>"
        for row in ad_group_rows
    )
    body = f"""
<div class="subsection-header">Campaign architecture</div>
<div class="two-col">
  <div class="insight-card">
    <h3>Build shape</h3>
    <p>{summary.ad_groups} ad groups organize service intent, modality intent, and social anxiety demand into one compact Search launch.</p>
  </div>
  <div class="insight-card">
    <h3>Keyword control</h3>
    <p>{summary.phrase_keywords} phrase keywords and {summary.negative_phrase_keywords} negative phrase keywords are staged. Broad and exact match are not active.</p>
  </div>
</div>
<div class="subsection-header">Ad groups staged for review</div>
<table>
  <tr><th>Ad group</th><th>Phrase keywords</th><th>Status</th></tr>
  {table_rows}
</table>
<div class="continuation-header">Campaign detail continues with representative ad previews</div>
"""
    return section(
        "Structure",
        "What The Campaign Contains",
        "The structure is intentionally compact so the first launch can validate service demand before expanding into separate state or specialty campaigns.",
        body,
    )


def targeting_section(geo_strategy: dict) -> str:
    targeting = geo_strategy.get("targeting", [])
    location_names = [item.get("location", "") for item in targeting]
    chips = "".join(f'<span class="state-chip">{esc(name)}</span>' for name in location_names)
    body = f"""
<div class="targeting-map">
  <div class="map-panel">
    <svg class="mini-map" viewBox="0 0 520 320" role="img" aria-label="Simple New York and New Jersey targeting sketch">
      <path class="state-shape" d="M150 44 L318 56 L396 96 L430 142 L382 160 L330 146 L292 172 L218 154 L168 116 Z"/>
      <path class="state-shape" d="M332 160 L458 166 L492 184 L438 202 L358 192 Z"/>
      <path class="state-shape" d="M222 166 L288 184 L300 238 L272 292 L226 276 L204 226 Z"/>
      <circle class="pin" cx="326" cy="168" r="10"/>
      <circle class="pin" cx="254" cy="220" r="8"/>
      <text class="map-label" x="205" y="112">New York</text>
      <text class="map-label" x="228" y="266">New Jersey</text>
      <text class="map-label" x="338" y="158">NYC</text>
    </svg>
  </div>
  <div class="map-panel">
    <div class="subsection-header" style="margin-top:0;">Current targeting</div>
    <p>The current staging file targets the approved service states, with New York City shown as the market anchor between New York and New Jersey.</p>
    <div style="margin:12px 0;">{chips}</div>
    <p style="margin-top:10px;">For a future revision, this can become a city or ZIP cluster view if the client wants to focus the launch around priority neighborhoods.</p>
    <p style="margin-top:10px;font-size:11px;color:#6b5c4b;">Simple sketch, not to scale. Source: <a href="https://support.google.com/google-ads/answer/1722043">Google Ads location targeting</a>.</p>
  </div>
</div>
"""
    return section(
        "Regional Targeting",
        "Where The Campaign Is Set To Reach",
        "This simple map-style view keeps regional targeting understandable without adding a heavy mapping system. The client can approve the current scope or request city and ZIP clusters.",
        body,
    )


def ad_preview_url(example: RsaExample) -> str:
    host = example.final_url.replace("https://", "").replace("http://", "").strip("/")
    paths = [path for path in (example.path_1, example.path_2) if path]
    return host + ("/" + "/".join(paths) if paths else "")


def ads_section(examples: list[RsaExample]) -> str:
    blocks = []
    for example in examples:
        headline_preview = " | ".join(example.headlines[:3])
        desc_preview = example.descriptions[0] if example.descriptions else ""
        headline_rows = "".join(
            f"<tr><td>{index}</td><td>{esc(value)}</td><td>{len(value)}</td></tr>"
            for index, value in enumerate(example.headlines[:8], start=1)
        )
        blocks.append(
            f"""
<div class="ad-card">
  <h3>{esc(example.ad_group)}</h3>
  <div class="ad-preview">
    <div class="sponsored">Sponsored</div>
    <div class="url">{esc(ad_preview_url(example))}</div>
    <div class="headline">{esc(headline_preview)}</div>
    <div class="desc">{esc(desc_preview)}</div>
  </div>
  <table><tr><th>#</th><th>Representative headline</th><th>Chars</th></tr>{headline_rows}</table>
</div>
"""
        )
    body = f"""
<div class="subsection-header">Representative ad copy</div>
<div class="ad-grid">{''.join(blocks)}</div>
"""
    return section(
        "Ad Copy",
        "Examples The Client Can Review",
        "Each responsive search ad has 15 headlines and 4 descriptions in the staging file. These examples show the tone and claims used across the build.",
        body,
    )


def approval_section(source_attribution: dict) -> str:
    approval_items = [
        (
            "Ad groups",
            "Confirm the service list is complete and no important service focus is missing.",
        ),
        (
            "Priority services",
            "Identify which ad groups should receive the most traffic first.",
        ),
        (
            "Ad copy",
            "Review the headline and description variations for tone, claims, and service fit.",
        ),
        (
            "Regional targeting",
            "Confirm the states, cities, ZIP clusters, or regional focus areas for launch.",
        ),
    ]
    source_pages = source_attribution.get("source_pages", [])
    approvals = "".join(
        f"<div class=\"approval-card\"><h3>{esc(title)}</h3><p>{esc(text)}</p></div>"
        for title, text in approval_items
    )
    sources = "".join(
        f"<p><strong>{esc(item.get('url'))}</strong><br>{esc(', '.join(item.get('used_for', [])))}</p>"
        for item in source_pages[:5]
    )
    body = f"""
<div class="subsection-header">Approval checklist</div>
<div class="approval-grid">{approvals}</div>
<div class="subsection-header">Source trail</div>
<div class="source-card">{sources}</div>
"""
    return section(
        "Approval",
        "What Needs Client Confirmation",
        "The campaign is valid as a staging file. The client review should focus on services, priority, ad copy, and regional targeting.",
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
    budget: BudgetPlan | None = None,
) -> str:
    rows = read_staging(staging_csv)
    summary = summarize_staging(rows)
    website_scan = read_json(website_scan_json)
    service_catalog = read_json(service_catalog_json)
    geo_strategy = read_json(geo_strategy_json)
    source_attribution = read_json(source_attribution_json)
    examples = select_rsa_examples(rows)
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
  {strategy_section(summary, website_scan, service_catalog, geo_strategy)}
  {budget_section(budget)}
  {structure_section(summary, rows)}
  {targeting_section(geo_strategy)}
  {ads_section(examples)}
  {approval_section(source_attribution)}
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
    budget: BudgetPlan | None = None,
) -> Path:
    html_text = build_html(
        client=client,
        date_label=date_label,
        staging_csv=staging_csv,
        website_scan_json=website_scan_json,
        service_catalog_json=service_catalog_json,
        geo_strategy_json=geo_strategy_json,
        source_attribution_json=source_attribution_json,
        budget=budget,
    )
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(html_text, encoding="utf-8")
    return output_html


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a new-campaign client review report.")
    parser.add_argument("--client", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--staging-csv", required=True, type=Path)
    parser.add_argument("--website-scan-json", required=True, type=Path)
    parser.add_argument("--service-catalog-json", required=True, type=Path)
    parser.add_argument("--geo-strategy-json", required=True, type=Path)
    parser.add_argument("--source-attribution-json", required=True, type=Path)
    parser.add_argument("--monthly-budget", type=float, default=3000)
    parser.add_argument("--cpc-low", type=float)
    parser.add_argument("--cpc-high", type=float)
    parser.add_argument("--output-html", required=True, type=Path)
    parser.add_argument("--output-pdf", type=Path)
    parser.add_argument("--visual-audit-dir", type=Path)
    args = parser.parse_args()
    budget = BudgetPlan(args.monthly_budget, args.cpc_low, args.cpc_high)

    html_path = write_report(
        client=args.client,
        date_label=args.date,
        staging_csv=args.staging_csv,
        website_scan_json=args.website_scan_json,
        service_catalog_json=args.service_catalog_json,
        geo_strategy_json=args.geo_strategy_json,
        source_attribution_json=args.source_attribution_json,
        output_html=args.output_html,
        budget=budget,
    )

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
    print(f"static_audit sections={summary['sections']} errors={summary['errors']} warnings={summary['warnings']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
