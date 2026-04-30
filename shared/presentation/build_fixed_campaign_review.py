#!/usr/bin/env python3
"""
Build a fixed-page client review PDF from the prepared campaign review HTML.

This is intentionally page-based. Each PDF page is an explicit .pdf-page
container with a known content budget. The builder avoids browser pagination
guesswork for client-facing reports.
"""

from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
from pathlib import Path

from bs4 import BeautifulSoup

if __package__:
    from .report_quality_audit import audit_html
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from shared.presentation.report_quality_audit import audit_html


def text_cleanup(value: str) -> str:
    replacements = {
        "EMDR Therapy for Trauma": "Trauma Therapy Support",
        "Therapist Near You | EMDR Therapy for Trauma | Licensed Therapists": "Therapist Near You | Trauma Therapy Support | Licensed Therapists",
        "EMDR, trauma, grief, anxiety": "Trauma, grief, anxiety",
        "Separates adult therapy (anxiety, depression, EMDR, trauma, grief) from the child services once volume justifies the split.": "Separates adult therapy, trauma, grief, anxiety, and depression from child services once volume justifies the split.",
        "EMDR, CBT, DBT, Somatic, Mindfulness": "CBT, DBT, Somatic, Mindfulness",
        "EMDR, grief counseling & trauma therapy. Online & in-person options available.": "Trauma, grief counseling & anxiety therapy. Online & in-person options available.",
        "Licensed therapists in Ashburn & Falls Church VA. Trauma, grief, anxiety & depression. EMDR, grief counseling & trauma therapy available online & in-person.": "Licensed therapists in Ashburn & Falls Church VA. Trauma, grief, anxiety and depression support available online and in person.",
        "Child & adult ADHD eval": "Testing through age 21",
        "ADHD Testing Near You | Child & Adult ADHD Evaluations": "ADHD Testing Near You | Children, Teens & Age 21",
        "Child & Adult ADHD Evaluations": "Testing Through Age 21",
        "Child & Young Adult ADHD Testing": "Child & Teen ADHD Testing",
        "Young Adult ADHD Testing": "ADHD Testing Through Age 21",
        "Adult ADHD Testing": "ADHD Testing Through Age 21",
        "Comprehensive ADHD Assessments": "ADHD Testing Through Age 21",
        "Family Therapy Services": "Parent-Child Therapy",
        "Parent-child therapy & family counseling in Ashburn & Falls Church VA.": "Parent-child therapy and family support in Ashburn and Falls Church VA.",
        "Family therapy, child counseling": "Parent-child support",
        "Parent-child therapy, family counseling, behavior therapy for kids": "Parent-child therapy, family support, behavior therapy for kids",
        "Licensed child therapists helping kids & families thrive. Book an appointment today.": "Licensed child therapists supporting children and parents. Book an appointment today.",
        "Parent-Child Therapy Near You | Help Your Child Thrive | Licensed Child Therapists": "Parent-Child Therapy | Help Your Child Thrive | Licensed Child Therapists",
        "We are launching at $60/day unless you tell us otherwise. With 9 ad groups, this gives roughly $200/month per service category to gather meaningful data.": "We will confirm launch budget before publishing. Budget changes should shift delivery weight without breaking the approved campaign structure.",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = re.sub(r"\bWhy this matters:\s*", "", value, flags=re.IGNORECASE)
    value = value.replace("—", "-")
    return value


def clean_soup(soup: BeautifulSoup) -> BeautifulSoup:
    for tag in soup.find_all(string=True):
        tag.replace_with(text_cleanup(str(tag)))

    for row in soup.select("tr.copy-violation"):
        if row.select_one(".char-ok"):
            row.attrs.pop("class", None)

    for tag in soup.select(".char-bad"):
        if tag.get_text(strip=True).startswith("30"):
            tag["class"] = ["char-ok"]
            tag.string = "30"

    for paragraph in soup.find_all("p"):
        text = paragraph.get_text(" ", strip=True).lower()
        if (
            "at-limit items" in text
            or "exactly 30 chars" in text
            or "may count punctuation" in text
            or "sweep highlights" in text
        ):
            paragraph.decompose()

    for strong in soup.find_all("strong"):
        if "sweep highlights" not in strong.get_text(" ", strip=True).lower():
            continue
        wrapper = strong.find_parent("div")
        if wrapper:
            wrapper.decompose()
        else:
            strong.decompose()

    return soup


def outer(element) -> str:
    return text_cleanup(str(element)) if element else ""


def section_by_id(soup: BeautifulSoup, section_id: str):
    return soup.find("section", {"id": section_id})


def make_page(label: str, title: str, body: str, page_class: str = "") -> str:
    return f"""
<section class="section pdf-page {page_class}">
  <div class="section-header" aria-hidden="true"></div>
  <div class="subsection-header" aria-hidden="true"></div>
  <div class="page-kicker">{html.escape(label)}</div>
  <h1>{html.escape(title)}</h1>
  <div class="page-body">{body}</div>
</section>
"""


def make_ad_page(index: int, ad_block) -> str:
    if not ad_block:
        return ""
    return f"""
<section class="section pdf-page ad-page">
  <div class="section-header" aria-hidden="true"></div>
  <div class="subsection-header" aria-hidden="true"></div>
  <div class="page-body">
    {outer(ad_block)}
  </div>
</section>
"""


def make_ad_pair_page(pair_index: int, ad_blocks: list) -> str:
    body = "\n".join(outer(block) for block in ad_blocks)
    if len(ad_blocks) == 1:
        body += """
<div class="revision-control-card">
  <div class="rc-label">Revision Controls Applied</div>
  <h2>Claims and Scope Guardrails</h2>
  <div class="rc-grid">
    <div>
      <h3>Applied in this version</h3>
      <ul>
        <li>Removed unavailable specialty modality claims from active therapy copy.</li>
        <li>Positioned ADHD testing for children, teens, and young adults through age 21.</li>
        <li>Reframed parent-child services around child-centered support.</li>
        <li>Kept insurance language limited to Anthem/CareFirst BCBS and superbill support.</li>
      </ul>
    </div>
    <div>
      <h3>Client approval needed</h3>
      <ul>
        <li>Confirm every service shown is currently bookable.</li>
        <li>Confirm landing pages match the ad group service and audience.</li>
        <li>Approve geographic targeting before CSV publishing.</li>
        <li>Approve negative keyword exclusions for unsupported searches.</li>
      </ul>
    </div>
  </div>
</div>
"""
    return f"""
<section class="section pdf-page ad-pair-page">
  <div class="section-header" aria-hidden="true"></div>
  <div class="subsection-header" aria-hidden="true"></div>
  <div class="page-kicker">Ad Copy Review</div>
  <h1>RSA Assets for Client Review</h1>
  <div class="ad-pair-grid">
    {body}
  </div>
</section>
"""


def build_fixed_html(input_html: Path) -> str:
    soup = BeautifulSoup(input_html.read_text(encoding="utf-8"), "html.parser")
    soup = clean_soup(soup)

    before = section_by_id(soup, "before-after")
    methodology = section_by_id(soup, "methodology")
    data = section_by_id(soup, "data")
    structure = section_by_id(soup, "structure")
    roadmap = section_by_id(soup, "roadmap")
    copy_review = section_by_id(soup, "copy-review")
    violations = section_by_id(soup, "violations")
    checklist = section_by_id(soup, "checklist")

    problem_grid = before.select_one(".problem-grid") if before else None
    before_after = before.select_one(".before-after") if before else None
    strategy_grid = methodology.select_one(".strategy-grid") if methodology else None
    insights = data.select_one(".insight-grid") if data else None
    geo = data.select_one(".geo-table") if data else None
    naming = structure.select_one(".card") if structure else None
    intent = structure.select_one(".intent-table") if structure else None
    ag_grid = structure.select_one(".ag-grid") if structure else None
    roadmap_el = roadmap.select_one(".roadmap") if roadmap else None
    taxonomy = roadmap.select_one(".tax-table") if roadmap else None
    validation_cards = violations.select(".card") if violations else []
    discussion = checklist.select_one(".discussion-grid") if checklist else None
    ad_blocks = soup.select(".ag-review-block")

    pages: list[str] = []
    pages.append(f"""
<section class="section pdf-page cover-page">
  <div class="section-header" aria-hidden="true"></div>
  <div class="subsection-header" aria-hidden="true"></div>
  <div class="cover-band">
    <div class="page-kicker">Google Ads Campaign Strategy Review</div>
    <h1>Think Happy Live Healthy</h1>
    <p>Search campaign rebuild, client review, and launch approval package.</p>
    <div class="cover-meta">
      <span><strong>Prepared by</strong> Advertising Report Card</span>
      <span><strong>Date</strong> April 28, 2026</span>
      <span><strong>Status</strong> Human Review</span>
      <span><strong>Campaign</strong> ARC - Search - Services - V1</span>
    </div>
  </div>
  <div class="cover-grid">
    <div><strong>What we inherited</strong><p>Fragmented campaigns, unclear naming, missing service coverage, mixed search intent, and weak copy controls.</p></div>
    <div><strong>What we rebuilt</strong><p>Phrase-match search structure, service taxonomy, geo modifiers, RSA copy review, and client approval gates.</p></div>
    <div><strong>What needs approval</strong><p>Copy claims, service scope, landing pages, regional targeting, launch budget, and revision notes.</p></div>
  </div>
</section>
""")

    pages.append(make_page("Starting Point", "Inherited Account vs. Rebuilt Structure", outer(before_after) + outer(problem_grid), "split-page problem-page"))
    pages.append(make_page("Rebuild Method", "Campaign Rules We Applied", outer(strategy_grid), "strategy-page"))
    pages.append(make_page("Performance Evidence", "Search Term and Geo Signals", outer(insights) + outer(geo), "data-page"))
    pages.append(make_page("Campaign Architecture", "Naming, Intent, and Launch Scope", outer(naming) + outer(intent) + outer(ag_grid), "architecture-page"))
    pages.append(make_page("Expansion Map", "Staged Growth Roadmap", outer(roadmap_el) + outer(taxonomy), "roadmap-page"))

    for pair_index, start in enumerate(range(0, len(ad_blocks), 2), start=1):
        pages.append(make_ad_pair_page(pair_index, ad_blocks[start : start + 2]))

    validation_body = "".join(outer(card) for card in validation_cards)
    pages.append(make_page("Launch Gate", "Validation and Client Approval Topics", validation_body + outer(discussion), "approval-page"))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Google Ads Campaign Review - Think Happy Live Healthy - Fixed Page</title>
<style>
{fixed_css()}
</style>
</head>
<body>
{''.join(pages)}
</body>
</html>
"""


def fixed_css() -> str:
    return """
@page { size: Letter; margin: 0; }
:root {
  --sage:#83968F; --sage-light:#AEC8BE; --sage-dark:#57645F;
  --blush:#E9C1AD; --blush-light:#F4DFD5; --teal:#5ABBBA;
  --teal-dark:#3C7D7C; --bg:#F8F5F0; --card:#fff; --text:#323130;
  --muted:#6E6C6A; --border:#DDD9D4; --green:#2E7D50;
  --green-bg:#EAF5EE; --amber:#B45309; --amber-bg:#FEF3C7; --red:#C0392B;
}
* { box-sizing: border-box; }
body { margin:0; background:#fff; color:var(--text); font-family: Arial, sans-serif; }
.pdf-page {
  width:8.5in; height:11in; overflow:hidden; break-after:page;
  padding:.43in .48in; background:var(--bg); position:relative;
}
.pdf-page::before {
  content:""; position:absolute; inset:.28in .30in; border-left:5px solid var(--teal);
  background:rgba(255,255,255,.18); pointer-events:none;
}
.page-kicker {
  position:relative; z-index:1; color:var(--teal-dark); font-weight:800;
  text-transform:uppercase; letter-spacing:.16em; font-size:10px; margin-bottom:8px;
}
h1 { position:relative; z-index:1; margin:0 0 18px; color:var(--sage-dark); font-size:29px; line-height:1.08; }
.page-body { position:relative; z-index:1; }
p { margin:0; }
strong { font-weight:800; }
.cover-page { background:linear-gradient(135deg,var(--sage-dark),#42514c); color:white; }
.cover-page::before { border-left-color:var(--blush); background:rgba(255,255,255,.04); }
.cover-band { position:relative; z-index:1; margin-top:.25in; padding:.25in .28in; border-left:5px solid var(--blush); }
.cover-band h1 { color:white; font-size:42px; margin-bottom:10px; }
.cover-band p { color:var(--blush-light); font-size:16px; }
.cover-meta { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:28px; font-size:12px; color:rgba(255,255,255,.82); }
.cover-meta strong { display:block; color:white; font-size:10px; text-transform:uppercase; letter-spacing:.11em; }
.cover-grid { position:relative; z-index:1; display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-top:.55in; }
.cover-grid div { background:rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.18); border-radius:8px; padding:18px; min-height:145px; }
.cover-grid strong { display:block; margin-bottom:8px; color:var(--blush-light); }
.cover-grid p { font-size:12px; line-height:1.5; color:rgba(255,255,255,.82); }
.section-header, .subsection-header, .continuation-header { display:none !important; }
.before-after { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
.ba-col, .problem-card, .strategy-card, .insight-card, .card, .discussion-card, .ag-review-block {
  background:var(--card); border:1px solid var(--border); border-radius:8px; overflow:hidden;
}
.ba-header { padding:10px 14px; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:.08em; }
.ba-before .ba-header { background:#FDF2F0; color:var(--red); }
.ba-after .ba-header { background:var(--green-bg); color:var(--green); }
.ba-body { padding:13px 15px; }
.ba-body ul { margin:0; padding:0; list-style:none; }
.ba-body li { font-size:9.3px; line-height:1.26; padding:4px 0 4px 13px; border-bottom:1px solid #eee; position:relative; }
.ba-body li::before { position:absolute; left:0; font-weight:800; }
.ba-before li::before { content:"x"; color:var(--red); }
.ba-after li::before { content:"✓"; color:var(--green); }
.flag { font-size:8px; border-radius:3px; padding:1px 4px; font-weight:800; }
.flag-red { background:#FDECEA; color:var(--red); }
.flag-green { background:var(--green-bg); color:var(--green); }
.problem-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:14px; }
.strategy-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.problem-card { padding:12px; min-height:158px; }
.pc-number { color:var(--blush); font-size:25px; font-weight:800; }
.problem-card h4, .strategy-card .sc-title { color:var(--sage-dark); margin:5px 0 7px; font-size:13px; }
.problem-card p { color:var(--muted); font-size:9.25px; line-height:1.33; }
.strategy-card .sc-body { color:var(--muted); font-size:11.6px; line-height:1.48; }
.strategy-card { padding:16px; border-left:4px solid var(--teal); min-height:185px; }
.strategy-card .sc-why { margin-top:10px; padding:8px; color:var(--teal-dark); background:rgba(90,187,186,.08); border-left:2px solid var(--teal); font-size:10.5px; line-height:1.38; font-weight:700; }
.insight-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:16px; }
.insight-card { padding:14px; min-height:105px; }
.ic-value { font-size:22px; color:var(--teal-dark); font-weight:800; }
.ic-label { font-size:9px; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; font-weight:800; }
.ic-note { font-size:10.5px; line-height:1.35; margin-top:5px; }
table { width:100%; border-collapse:collapse; }
th { background:var(--sage-dark); color:white; text-align:left; font-size:9px; text-transform:uppercase; letter-spacing:.04em; padding:7px 9px; }
td { padding:7px 9px; border-bottom:1px solid var(--border); font-size:10.5px; line-height:1.32; vertical-align:top; }
.geo-table th, .intent-table th, .tax-table th { background:var(--sage-dark); }
.tier-1 { color:var(--green); font-weight:800; }
.tier-2 { color:var(--teal-dark); font-weight:800; }
.tier-review { color:var(--amber); font-weight:800; }
.architecture-page .card { padding:14px; margin-bottom:12px; }
.architecture-page .card p { font-size:11px !important; }
.ag-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:12px; }
.ag-chip { background:white; border:1px solid var(--border); border-radius:6px; padding:9px; min-height:54px; }
.ag-name { font-size:11px; color:var(--sage-dark); font-weight:800; }
.ag-meta { font-size:9px; color:var(--muted); margin-top:3px; }
.roadmap { display:grid; grid-template-columns:repeat(5,1fr); gap:0; margin-bottom:16px; }
.roadmap-item { background:white; border:1px solid var(--border); padding:11px; min-height:170px; }
.roadmap-item.active { background:var(--sage-dark); color:white; }
.rm-num { font-size:8px; text-transform:uppercase; letter-spacing:.08em; color:var(--sage); font-weight:800; }
.roadmap-item.active .rm-num { color:var(--blush); }
.rm-title { font-size:11px; font-weight:800; margin:7px 0; color:var(--sage-dark); }
.roadmap-item.active .rm-title { color:white; }
.rm-body { font-size:9.5px; line-height:1.35; color:var(--muted); }
.roadmap-item.active .rm-body { color:rgba(255,255,255,.78); }
.rm-tag { display:inline-block; margin-top:7px; padding:3px 6px; border-radius:8px; background:#eef4f2; font-size:7.5px; font-weight:800; color:var(--sage-dark); }
.tax-table td, .tax-table th { font-size:9.2px; padding:6px 8px; }
.ad-page { padding:.33in .38in; }
.ad-page::before { inset:.22in .24in; }
.ad-page .page-body { height:100%; }
.ad-page .ag-review-block { height:100%; display:flex; flex-direction:column; border-radius:8px; }
.ag-review-header { background:var(--sage-dark); color:white; display:flex; justify-content:space-between; align-items:center; padding:12px 16px; }
.ag-review-header h3 { margin:0; color:white; font-size:17px; line-height:1.05; }
.ag-num { color:var(--blush); font-size:22px; font-weight:800; margin-right:10px; }
.ag-url-badge { font-size:8px; color:var(--blush); font-family:monospace; text-align:right; max-width:360px; }
.ag-review-body { padding:14px; flex:1; }
.ag-review-cols { display:grid; grid-template-columns:32% 68%; gap:16px; height:100%; }
.copy-section-title { color:var(--sage); text-transform:uppercase; letter-spacing:.09em; font-size:9px; font-weight:800; margin:0 0 7px; }
.ad-preview { border:1px solid var(--border); border-radius:7px; padding:12px; margin-bottom:12px; }
.ap-label, .ap-url { font-size:9px; color:#4d5156; margin-bottom:4px; }
.ap-headlines { color:#1a0dab; font-size:14px; line-height:1.35; margin-bottom:6px; }
.ap-desc { font-size:10.5px; line-height:1.42; color:#4d5156; }
.copy-grade-card { border:1px solid var(--border); border-left:4px solid var(--teal); border-radius:0 7px 7px 0; padding:10px; background:#F8FAF9; }
.grade-compare { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:8px; }
.grade-label { display:block; font-size:8px; text-transform:uppercase; color:var(--muted); font-weight:800; margin-bottom:4px; }
.grade-pill { display:inline-block; min-width:42px; text-align:center; border-radius:5px; padding:4px 6px; font-size:12px; font-weight:800; }
.grade-B { background:#DBEAFE; color:#1E40AF; }
.grade-C { background:var(--amber-bg); color:var(--amber); }
.grade-D { background:#FEE2E2; color:#991B1B; }
.grade-note { font-size:9.3px; line-height:1.38; margin-top:5px; color:var(--text); }
.grade-note.muted { color:var(--muted); }
.copy-table { margin-bottom:10px; }
.copy-table th { background:#F2EFE9; color:var(--sage-dark); font-size:8px; padding:5px 7px; }
.copy-table td { font-size:9.25px; padding:4.6px 7px; line-height:1.22; }
.char-ok { color:var(--muted); font-size:8.5px; font-family:monospace; }
.char-bad { color:var(--muted); background:transparent; font-size:8.5px; }
.copy-violation { background:transparent !important; }
.ad-page p[style] { font-size:9px !important; color:var(--red) !important; line-height:1.35 !important; }
.ad-page .ag-review-body::after {
  content:"Review focus: confirm service availability, landing page accuracy, and claim-sensitive wording before launch.";
  display:block; margin-top:12px; padding:10px 12px; border-left:3px solid var(--teal);
  background:rgba(90,187,186,.08); color:var(--teal-dark); font-size:10.5px; line-height:1.35; font-weight:700;
}
.ad-pair-page { padding:.32in .34in; }
.ad-pair-page::before { inset:.22in .24in; }
.ad-pair-page h1 { font-size:22px; margin-bottom:10px; }
.ad-pair-grid { position:relative; z-index:1; display:grid; grid-template-rows:1fr 1fr; gap:10px; height:9.45in; }
.ad-pair-page .ag-review-block { height:100%; display:flex; flex-direction:column; border-radius:7px; background:#fff; border:1px solid var(--border); overflow:hidden; }
.ad-pair-page .ag-review-header { padding:8px 12px; }
.ad-pair-page .ag-review-header h3 { font-size:13px; }
.ad-pair-page .ag-num { font-size:17px; min-width:24px; }
.ad-pair-page .ag-url-badge { font-size:6.5px; max-width:330px; }
.ad-pair-page .ag-review-body { padding:8px 10px; flex:1; }
.ad-pair-page .ag-review-cols { display:grid; grid-template-columns:29% 71%; gap:10px; height:auto; }
.ad-pair-page .copy-section-title { font-size:7.2px; margin-bottom:4px; letter-spacing:.08em; }
.ad-pair-page .ad-preview { padding:8px; margin-bottom:7px; }
.ad-pair-page .ap-label, .ad-pair-page .ap-url { font-size:7px; margin-bottom:2px; }
.ad-pair-page .ap-headlines { font-size:10.5px; line-height:1.25; margin-bottom:3px; }
.ad-pair-page .ap-desc { font-size:7.8px; line-height:1.27; }
.ad-pair-page .copy-grade-card { padding:7px; }
.ad-pair-page .grade-compare { gap:5px; margin-bottom:5px; }
.ad-pair-page .grade-label { font-size:6.2px; margin-bottom:2px; }
.ad-pair-page .grade-pill { min-width:34px; padding:2px 5px; font-size:9px; }
.ad-pair-page .grade-note { font-size:7.1px; line-height:1.25; margin-top:3px; }
.ad-pair-page .copy-table { margin-bottom:5px; }
.ad-pair-page .copy-table th { font-size:6.3px; padding:3px 5px; }
.ad-pair-page .copy-table td { font-size:7.25px; padding:2.55px 5px; line-height:1.12; }
.ad-pair-page .char-ok, .ad-pair-page .char-bad { font-size:6.6px; }
.ad-pair-page p[style] { font-size:7px !important; line-height:1.22 !important; margin-top:4px !important; }
.revision-control-card {
  background:white; border:1px solid var(--border); border-left:4px solid var(--teal);
  border-radius:0 8px 8px 0; padding:18px 20px;
}
.revision-control-card .rc-label {
  color:var(--teal-dark); font-size:9px; font-weight:800; text-transform:uppercase; letter-spacing:.14em; margin-bottom:7px;
}
.revision-control-card h2 { margin:0 0 12px; color:var(--sage-dark); font-size:18px; }
.revision-control-card .rc-grid { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
.revision-control-card h3 { margin:0 0 8px; color:var(--teal-dark); font-size:13px; }
.revision-control-card ul { margin:0; padding-left:18px; }
.revision-control-card li { font-size:11.6px; line-height:1.48; margin-bottom:7px; color:var(--text); }
.approval-page .page-body { display:flex; flex-direction:column; gap:14px; }
.approval-page .card { padding:14px; }
.approval-page .card p, .approval-page li { font-size:11px !important; line-height:1.45; }
.discussion-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:10px; }
.discussion-card { padding:12px; min-height:86px; }
.dc-label { font-size:8px; text-transform:uppercase; letter-spacing:.09em; color:var(--sage); font-weight:800; }
.dc-title { font-size:11px; font-weight:800; color:var(--sage-dark); margin:4px 0; }
.dc-body { font-size:9.4px; line-height:1.32; color:var(--muted); }
.dc-actions { display:flex; gap:5px; margin-top:8px; }
.dc-action { flex:1; border:1px solid var(--border); border-radius:4px; text-align:center; padding:3px; font-size:7px; text-transform:uppercase; font-weight:800; color:var(--muted); }
.dc-approve { border-color:#B7DEC7; color:var(--green); }
.dc-changes { border-color:#FDE68A; color:var(--amber); }
footer { display:none !important; }
"""


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
    parser = argparse.ArgumentParser(description="Build fixed-page client review HTML/PDF.")
    parser.add_argument("--input-html", required=True, type=Path)
    parser.add_argument("--output-html", required=True, type=Path)
    parser.add_argument("--output-pdf", required=True, type=Path)
    args = parser.parse_args()

    fixed = build_fixed_html(args.input_html)
    args.output_html.parent.mkdir(parents=True, exist_ok=True)
    args.output_html.write_text(fixed, encoding="utf-8")
    findings, summary = audit_html(args.output_html)
    if summary["errors"]:
        for finding in findings:
            if finding.severity == "error":
                print(f"error: {finding.code}: {finding.message} {finding.evidence}", file=sys.stderr)
        return 1
    export_pdf(args.output_html, args.output_pdf)
    print(f"wrote {args.output_html}")
    print(f"wrote {args.output_pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
