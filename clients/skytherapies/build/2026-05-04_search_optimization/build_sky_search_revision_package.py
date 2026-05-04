#!/usr/bin/env python3
"""Build the Sky Therapies search-term and regional revision package."""

from __future__ import annotations

import csv
import html
import io
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from shared.presentation.build_fixed_campaign_review import fixed_css
from shared.presentation.build_review_doc import export_pdf
from shared.presentation.report_quality_audit import audit_html
from shared.rebuild.search_term_review import SearchTermReview, build_search_term_review


BUILD_DIR = Path(__file__).resolve().parent
CLIENT_DIR = ROOT / "clients" / "skytherapies"
EDITOR_EXPORT = CLIENT_DIR / "Skytherapies.ca++2_Campaigns+14_Ad groups+2026-05-04.csv"
SEARCH_TERMS = CLIENT_DIR / "reports" / "performance_inputs" / "search_terms_report_2026-05-04.csv"
LOCATIONS = CLIENT_DIR / "reports" / "performance_inputs" / "location_report_2026-05-04.csv"


@dataclass
class TermDecision:
    search_term: str
    decision: str
    recommended_action: str
    campaign: str
    ad_group: str
    suggested_ad_group: str
    clicks: float
    impressions: float
    cost: float
    conversions: float
    reason: str
    client_prompt: str


@dataclass
class LocationInsight:
    location: str
    campaign: str
    impressions: float
    interactions: float
    cost: float
    conversions: float
    recommendation: str
    bid_adjustment_review: str
    rationale: str


SERVICE_AD_GROUPS = {
    "emdr": "Therapy - EMDR",
    "eye movement": "Therapy - EMDR",
    "trauma": "Therapy - Trauma & PTSD",
    "ptsd": "Therapy - Trauma & PTSD",
    "somatic": "Therapy - Trauma & PTSD",
    "dbr": "Therapy - DBR",
    "deep brain": "Therapy - DBR",
    "pain reprocessing": "Therapy - Chronic Pain",
    "chronic pain": "Therapy - Chronic Pain",
    "fibromyalgia": "Therapy - Chronic Pain",
    "pain psychologist": "Therapy - Chronic Pain",
    "ibs": "Therapy - IBS & Gut Health",
    "gut": "Therapy - IBS & Gut Health",
    "hypnotherapy": "Therapy - IBS & Gut Health",
    "chronic illness": "Therapy - Chronic Illness",
    "illness": "Therapy - Chronic Illness",
}

EXCLUDE_PATTERNS = [
    "211",
    "ajax",
    "amani mental health",
    "axon pain clinic",
    "barrie",
    "bounce back",
    "canadian mental health association",
    "champagne drive",
    "clinic",
    "cortisone",
    "degroote",
    "dietician",
    "dietitian",
    "don mills",
    "dr khetani",
    "dr perelman",
    "dr rozen",
    "dry needling",
    "florastor",
    "hanna ratjen",
    "helpline",
    "hf care",
    "hospital",
    "injection",
    "interventional pain",
    "jacobs pain",
    "kingston",
    "kopi",
    "leslie street",
    "medicine",
    "mount sinai",
    "nerva",
    "neurofeedback",
    "ontario shores",
    "physio",
    "probiotic",
    "queensway",
    "rtms",
    "specialist",
    "st michael",
    "tapmi",
    "wasser",
    "york medical",
]

GEO_TERMS = [
    "toronto",
    "markham",
    "mississauga",
    "north york",
    "scarborough",
    "brampton",
    "vaughan",
    "richmond hill",
    "ontario",
]


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True).replace("\u2014", "-")


def num(value: object) -> float:
    text = str(value or "").replace(",", "").replace("%", "").replace(" --", "").strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def normalize_term(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().strip('"').lower())


def plain_keyword(value: str) -> str:
    text = re.sub(r"\s+", " ", value.strip().strip('"'))
    if text.startswith(("-", "[", '"')) or text.endswith(("]", '"')):
        raise ValueError(f"Keyword is not plain text: {value}")
    return text


def read_google_report(path: Path, header_prefix: str) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    header_index = next(index for index, line in enumerate(lines) if line.startswith(header_prefix))
    return [dict(row) for row in csv.DictReader(lines[header_index:])]


def read_editor_export(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    content = path.read_text(encoding="utf-16")
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")
    fieldnames = list(reader.fieldnames or [])
    if "Location ID" not in fieldnames:
        insert_at = fieldnames.index("Location") if "Location" in fieldnames else len(fieldnames)
        fieldnames.insert(insert_at, "Location ID")
    rows = [dict(row) for row in reader]
    for row in rows:
        row.setdefault("Location ID", row.get("ID", ""))
    return fieldnames, rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]], *, delimiter: str = ",", encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=delimiter, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def suggested_ad_group(term: str, fallback: str) -> str:
    normalized = normalize_term(term)
    for marker, ad_group in SERVICE_AD_GROUPS.items():
        if marker in normalized:
            return ad_group
    return fallback


def classify_term(term: str, clicks: float, impressions: float, conversions: float, ad_group: str) -> tuple[str, str, str]:
    normalized = normalize_term(term)
    has_geo = any(geo in normalized for geo in GEO_TERMS)
    has_service = any(marker in normalized for marker in SERVICE_AD_GROUPS)

    if any(pattern in normalized for pattern in EXCLUDE_PATTERNS):
        return (
            "Exclude",
            "Do not stage yet",
            "Likely non-service, provider, institution, supplement, procedure, or clinic-seeking intent.",
        )

    if conversions > 0 and has_service:
        return (
            "Focus",
            "Add as phrase keyword",
            "Conversion signal plus clear therapy-service intent.",
        )

    if clicks >= 2 and has_service and "clinic" not in normalized and "specialist" not in normalized:
        return (
            "Focus",
            "Add as phrase keyword",
            "Multiple clicks with clear therapy-service intent and no obvious exclusion pattern.",
        )

    if has_geo and has_service:
        return (
            "Review",
            "Client to mark Focus, Keep, or Exclude",
            "Geo-modified service term. Confirm whether this city and service should become an active focus.",
        )

    if clicks > 0 and has_service:
        return (
            "Review",
            "Client to mark Focus, Keep, or Exclude",
            "Relevant service intent with early engagement, but not enough evidence to stage automatically.",
        )

    if "what " in normalized or "how " in normalized or "is " in normalized:
        return (
            "Keep",
            "Continue observing",
            "Informational therapy research query. Keep visible unless the client wants tighter pruning.",
        )

    return (
        "Keep",
        "Continue observing",
        "Low-risk exploratory query with no urgent action from this report.",
    )


def aggregate_search_terms(rows: list[dict[str, str]]) -> list[TermDecision]:
    grouped: dict[str, dict[str, object]] = {}
    for row in rows:
        raw_term = row.get("Search term", "").strip()
        term = normalize_term(raw_term)
        if not term or term.startswith("total:"):
            continue
        item = grouped.setdefault(
            term,
            {
                "search_term": term,
                "campaigns": defaultdict(float),
                "ad_groups": defaultdict(float),
                "clicks": 0.0,
                "impressions": 0.0,
                "cost": 0.0,
                "conversions": 0.0,
            },
        )
        clicks = num(row.get("Clicks"))
        item["clicks"] = float(item["clicks"]) + clicks
        item["impressions"] = float(item["impressions"]) + num(row.get("Impr."))
        item["cost"] = float(item["cost"]) + num(row.get("Cost"))
        item["conversions"] = float(item["conversions"]) + num(row.get("Conversions"))
        item["campaigns"][row.get("Campaign", "")] += clicks
        item["ad_groups"][row.get("Ad group", "")] += clicks

    decisions: list[TermDecision] = []
    for item in grouped.values():
        ad_group_scores = item["ad_groups"]
        campaign_scores = item["campaigns"]
        ad_group = max(ad_group_scores, key=ad_group_scores.get) if ad_group_scores else ""
        campaign = max(campaign_scores, key=campaign_scores.get) if campaign_scores else ""
        term = str(item["search_term"])
        clicks = float(item["clicks"])
        impressions = float(item["impressions"])
        cost = float(item["cost"])
        conversions = float(item["conversions"])
        decision, action, reason = classify_term(term, clicks, impressions, conversions, ad_group)
        decisions.append(
            TermDecision(
                search_term=term,
                decision=decision,
                recommended_action=action,
                campaign=campaign or "ARC - Search - Services",
                ad_group=ad_group,
                suggested_ad_group=suggested_ad_group(term, ad_group),
                clicks=clicks,
                impressions=impressions,
                cost=cost,
                conversions=conversions,
                reason=reason,
                client_prompt="Reply Focus, Keep, or Exclude.",
            )
        )

    return sorted(decisions, key=lambda item: (item.decision != "Focus", -item.conversions, -item.clicks, -item.impressions, item.search_term))


def location_insights(rows: list[dict[str, str]]) -> list[LocationInsight]:
    insights: list[LocationInsight] = []
    for row in rows:
        location = row.get("Location", "").strip()
        campaign = row.get("Campaign", "").strip()
        if not location or location.startswith("Total:"):
            continue
        impressions = num(row.get("Impr."))
        interactions = num(row.get("Interactions"))
        cost = num(row.get("Cost"))
        conversions = num(row.get("Conversions"))
        if impressions == 0 and interactions == 0 and cost == 0 and conversions == 0:
            recommendation = "No action"
            bid = "None"
            rationale = "No current activity in this report window."
        elif "Toronto" in location and campaign == "ARC - Search - Services":
            recommendation = "Core focus"
            bid = "Review modest positive modifier only after budget and CPA tolerance are confirmed."
            rationale = "Highest volume and 2 conversions, but CPA is materially higher than Markham."
        elif "Markham" in location and campaign == "ARC - Search - Services":
            recommendation = "Priority review"
            bid = "Review positive modifier or dedicated Markham service coverage."
            rationale = "1 conversion on lower spend makes Markham the strongest efficiency signal."
        elif any(city in location for city in ["Mississauga", "North York"]):
            recommendation = "Hold for review"
            bid = "No positive modifier yet."
            rationale = "Some interaction volume, but no conversion evidence in this window."
        elif any(city in location for city in ["Brampton", "Vaughan", "Richmond Hill"]):
            recommendation = "Scrutinize"
            bid = "No positive modifier. Consider reduction if weak trend continues."
            rationale = "Low interaction quality and no conversions."
        else:
            recommendation = "Observe"
            bid = "None"
            rationale = "Insufficient evidence for a targeting change."
        insights.append(
            LocationInsight(
                location=location,
                campaign=campaign,
                impressions=impressions,
                interactions=interactions,
                cost=cost,
                conversions=conversions,
                recommendation=recommendation,
                bid_adjustment_review=bid,
                rationale=rationale,
            )
        )
    return insights


def make_focus_additions(decisions: list[TermDecision], editor_rows: list[dict[str, str]], fieldnames: list[str]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    existing_keywords = {
        normalize_term(row.get("Keyword", ""))
        for row in editor_rows
        if row.get("Criterion Type", "").strip().lower() == "phrase" and row.get("Keyword", "").strip()
    }
    additions: list[dict[str, str]] = []
    for decision in decisions:
        if decision.decision != "Focus":
            continue
        keyword = plain_keyword(decision.search_term)
        normalized = normalize_term(keyword)
        if normalized in existing_keywords:
            continue
        row = {field: "" for field in fieldnames}
        row.update(
            {
                "Campaign": decision.campaign or "ARC - Search - Services",
                "Ad Group": decision.suggested_ad_group,
                "Criterion Type": "Phrase",
                "Keyword": keyword,
                "Campaign Status": "Enabled",
                "Ad Group Status": "Enabled",
                "Status": "Paused",
                "Approval Status": "",
                "Comment": "STR Focus addition pending human review",
            }
        )
        additions.append(row)
        existing_keywords.add(normalized)
    return editor_rows + additions, additions


def render_metric(value: float, decimals: int = 0) -> str:
    if decimals:
        return f"{value:,.{decimals}f}"
    return f"{value:,.0f}"


def table(headers: list[str], rows: list[list[object]], class_name: str = "tax-table") -> str:
    head = "".join(f"<th>{esc(header)}</th>" for header in headers)
    body = "".join("<tr>" + "".join(f"<td>{esc(cell)}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<table class="{class_name}"><tr>{head}</tr>{body}</table>'


def decision_rows(decisions: list[TermDecision]) -> list[list[object]]:
    visible = [item for item in decisions if item.decision in {"Focus", "Review", "Exclude"}]
    visible = sorted(visible, key=lambda item: (item.decision != "Focus", item.decision != "Review", -item.conversions, -item.clicks, -item.impressions))[:55]
    return [
        [
            item.search_term,
            item.decision,
            item.suggested_ad_group,
            render_metric(item.clicks),
            render_metric(item.impressions),
            render_metric(item.conversions, 2),
            item.client_prompt,
        ]
        for item in visible
    ]


def regional_opportunities() -> list[dict[str, object]]:
    return [
        {
            "ad_group": "Toronto EMDR Therapy",
            "campaign": "ARC - Regional - Search",
            "status": "Client review",
            "keywords": ["emdr therapy toronto", "emdr therapist toronto", "best emdr therapist toronto"],
            "headlines": [
                "Toronto EMDR Therapy",
                "EMDR Support In Toronto",
                "Trauma Therapy Toronto",
                "Book EMDR Therapy Online",
                "Private EMDR Support",
                "Talk With A Trauma Therapist",
                "EMDR For Trauma Support",
                "Online Therapy In Ontario",
                "Support For PTSD Symptoms",
                "Care For Trauma Recovery",
                "Toronto Trauma Support",
                "EMDR Therapy Consult",
                "Start With A Consult",
                "Therapy That Fits You",
                "Sky Therapies Online",
            ],
            "descriptions": [
                "Online EMDR therapy for trauma support with Sky Therapies in Ontario.",
                "Private trauma-informed therapy for people seeking EMDR support in Toronto.",
                "Confirm Toronto focus before we move this regional ad group into staging.",
                "Client approval required before launch or budget shifts.",
            ],
        },
        {
            "ad_group": "Markham EMDR Therapy",
            "campaign": "ARC - Regional - Search",
            "status": "Priority review",
            "keywords": ["emdr therapy markham"],
            "headlines": [
                "Markham EMDR Therapy",
                "EMDR Support Markham",
                "Trauma Therapy Markham",
                "Book EMDR Therapy Online",
                "Private EMDR Support",
                "Start With A Consult",
                "Ontario EMDR Therapy",
                "Trauma-Informed Support",
                "Care For PTSD Symptoms",
                "Therapy For Trauma Help",
                "Sky Therapies Online",
                "EMDR Therapist Support",
                "Support For Trauma",
                "Online Therapy Ontario",
                "Focused EMDR Care",
            ],
            "descriptions": [
                "Markham produced a conversion signal, so this deserves client confirmation.",
                "Online EMDR and trauma therapy support for Ontario clients.",
                "Approve Markham as Focus if it is a preferred service area.",
                "We will keep this paused until client approval.",
            ],
        },
        {
            "ad_group": "Toronto Pain Reprocessing Therapy",
            "campaign": "ARC - Regional - Search",
            "status": "Client review",
            "keywords": ["pain reprocessing therapy toronto"],
            "headlines": [
                "Pain Reprocessing Toronto",
                "Chronic Pain Therapy",
                "Pain Support In Toronto",
                "Online Pain Therapy",
                "Support For Chronic Pain",
                "Mind-Body Pain Support",
                "Start With A Consult",
                "Therapy For Pain Stress",
                "Private Online Support",
                "Chronic Pain Counselling",
                "Pain Recovery Support",
                "Ontario Therapy Online",
                "Sky Therapies Support",
                "Talk Through Pain Stress",
                "Therapy That Fits You",
            ],
            "descriptions": [
                "Pain reprocessing searches show Toronto intent and should be confirmed by the client.",
                "Online therapy support for chronic pain, stress, and mind-body patterns.",
                "Approve as Focus only if this is a high-priority service line.",
                "No location bid shift is recommended until approved.",
            ],
        },
        {
            "ad_group": "Toronto Trauma Therapy",
            "campaign": "ARC - Regional - Search",
            "status": "Client review",
            "keywords": ["childhood trauma therapist toronto", "trauma centre toronto", "somatic therapy toronto"],
            "headlines": [
                "Toronto Trauma Therapy",
                "Trauma Support Online",
                "Childhood Trauma Support",
                "Private Therapy Online",
                "Talk With A Trauma Therapist",
                "Support For PTSD Symptoms",
                "Somatic Therapy Review",
                "Care For Trauma Recovery",
                "Start With A Consult",
                "Ontario Trauma Therapy",
                "Therapy That Fits You",
                "Sky Therapies Online",
                "Trauma-Informed Care",
                "Support With Next Steps",
                "Online Therapy Ontario",
            ],
            "descriptions": [
                "Toronto trauma searches are relevant, but service fit should be confirmed first.",
                "Online trauma-informed support for Ontario clients.",
                "Approve only the terms that match services Sky Therapies wants to prioritize.",
                "Held for client review before staging.",
            ],
        },
    ]


def grouped_question_rows(grouped_review: SearchTermReview) -> list[list[object]]:
    return [
        [
            group.title,
            group.question,
            "; ".join(group.terms[:6]),
            group.default_action,
        ]
        for group in grouped_review.question_groups
    ]


def build_html(decisions: list[TermDecision], locations: list[LocationInsight], additions: list[dict[str, str]], grouped_review: SearchTermReview) -> str:
    focus_count = sum(1 for item in decisions if item.decision == "Focus")
    review_count = sum(1 for item in decisions if item.decision == "Review")
    exclude_count = sum(1 for item in decisions if item.decision == "Exclude")
    keep_count = sum(1 for item in decisions if item.decision == "Keep")
    additions_count = len(additions)

    location_rows = [
        [
            item.location,
            item.campaign,
            render_metric(item.interactions),
            render_metric(item.conversions, 2),
            f"${item.cost:,.2f}",
            item.recommendation,
            item.bid_adjustment_review,
        ]
        for item in locations
        if item.recommendation != "No action"
    ]
    source_rows = [
        [
            "Search terms report",
            "clients/skytherapies/reports/performance_inputs/search_terms_report_2026-05-04.csv",
            "Search queries, match context, clicks, cost, and conversions.",
        ],
        [
            "Location report",
            "clients/skytherapies/reports/performance_inputs/location_report_2026-05-04.csv",
            "City and radius performance by campaign for regional recommendations.",
        ],
        [
            "Google Ads Editor export",
            "clients/skytherapies/Skytherapies.ca++2_Campaigns+14_Ad groups+2026-05-04.csv",
            "Current campaign, ad group, keyword, RSA, and targeting structure.",
        ],
        [
            "Focus additions delta",
            "paused_focus_keyword_additions.csv",
            "Only the new paused Phrase keyword additions from this review.",
        ],
        [
            "Full revised review export",
            "skytherapies_google_ads_editor_staging_rev1_20260504_optimization.tsv",
            "Current Sky export plus the paused Focus additions for review context.",
        ],
    ]

    opportunity_blocks = []
    for opportunity in regional_opportunities():
        keyword_text = ", ".join(opportunity["keywords"])
        headline_text = " | ".join(opportunity["headlines"][:6])
        desc_text = " ".join(opportunity["descriptions"][:2])
        opportunity_blocks.append(
            f"""
<div class="ag-review-block">
  <div class="ag-review-header">
    <div><span class="ag-num">{esc(opportunity["status"])}</span><h3>{esc(opportunity["ad_group"])}</h3></div>
    <div class="ag-url-badge">{esc(opportunity["campaign"])}</div>
  </div>
  <div class="ag-review-body">
    <div class="copy-section-title">Draft keywords</div>
    <p>{esc(keyword_text)}</p>
    <div class="copy-section-title">Draft headline direction</div>
    <p>{esc(headline_text)}</p>
    <div class="copy-section-title">Draft description direction</div>
    <p>{esc(desc_text)}</p>
  </div>
</div>
"""
        )

    grouped_rows = grouped_question_rows(grouped_review)
    body = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Sky Therapies Search Terms And Regional Focus Confirmation</title>
<style>
{fixed_css()}
.page-body p {{ font-size: 13px; line-height: 1.52; }}
.metric-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 18px 0; }}
.metric-card {{ border: 1px solid var(--line); padding: 14px; background: #fff; border-radius: 8px; }}
.metric-value {{ font-size: 28px; font-weight: 800; color: var(--sage-dark); }}
.metric-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }}
.source-list a {{ color: var(--teal-dark); }}
</style>
</head>
<body>
<section class="section pdf-page cover-page">
  <div class="section-header" aria-hidden="true"></div>
  <div class="subsection-header" aria-hidden="true"></div>
  <div class="cover-band">
    <div class="page-kicker">Search Optimization Review</div>
    <h1>Sky Therapies</h1>
    <p>Search terms and regional focus confirmation for the April 26, 2026 to May 2, 2026 report window.</p>
    <div class="cover-meta">
      <span><strong>Prepared by</strong> Advertising Report Card</span>
      <span><strong>Date</strong> 2026-05-04</span>
      <span><strong>Status</strong> Client confirmation needed</span>
      <span><strong>Staging</strong> Google Ads Editor only</span>
    </div>
  </div>
  <div class="cover-grid">
    <div><strong>What changed</strong><p>New search terms and location data show clear Toronto volume and Markham conversion quality.</p></div>
    <div><strong>What we staged</strong><p>Only obvious Focus keyword additions were added to a paused review CSV.</p></div>
    <div><strong>What we need</strong><p>Client confirmation on Focus, Keep, or Exclude for the review terms below.</p></div>
  </div>
</section>
<section class="section pdf-page">
  <div class="section-header" aria-hidden="true"></div>
  <div class="subsection-header" aria-hidden="true"></div>
  <div class="page-kicker">Search Terms And Regional Focus Confirmation</div>
  <h1>Client Decision Page</h1>
  <div class="page-body">
    <p>Please mark each term as <strong>Focus</strong>, <strong>Keep</strong>, or <strong>Exclude</strong>. Focus means we should actively build around it. Keep means we should continue observing it. Exclude means we should block or avoid it.</p>
    <p>We are not asking the client to confirm obvious combinations such as a known service in an approved city. The questions below are grouped around uncertainty, especially cities where service-area coverage is not confirmed.</p>
    {table(["Question group", "Client question", "Example searches", "Default action"], grouped_rows) if grouped_rows else "<p>No grouped client questions were needed after matching services and approved regions.</p>"}
    <div class="metric-grid">
      <div class="metric-card"><div class="metric-value">{focus_count}</div><div class="metric-label">Focus candidates</div></div>
      <div class="metric-card"><div class="metric-value">{review_count}</div><div class="metric-label">Needs client review</div></div>
      <div class="metric-card"><div class="metric-value">{exclude_count}</div><div class="metric-label">Exclude recommendations</div></div>
      <div class="metric-card"><div class="metric-value">{additions_count}</div><div class="metric-label">Paused additions staged</div></div>
    </div>
    {table(["Search term", "Draft", "Suggested ad group", "Clicks", "Impr.", "Conv.", "Client reply"], decision_rows(decisions))}
  </div>
</section>
<section class="section pdf-page">
  <div class="section-header" aria-hidden="true"></div>
  <div class="subsection-header" aria-hidden="true"></div>
  <div class="page-kicker">Regional Targeting</div>
  <h1>City Signals And Bid Review</h1>
  <div class="page-body">
    <p>Toronto is the volume center. Markham has the strongest efficiency signal. Mississauga and North York have engagement but no conversions. Brampton, Vaughan, and Richmond Hill should stay under scrutiny until more conversion evidence appears.</p>
    {table(["Location", "Campaign", "Interactions", "Conv.", "Cost", "Recommendation", "Bid review"], location_rows)}
    <p>No postal-code targeting is recommended from this report. We should only add postal codes if Sky Therapies confirms exact preferred service areas.</p>
  </div>
</section>
<section class="section pdf-page">
  <div class="section-header" aria-hidden="true"></div>
  <div class="subsection-header" aria-hidden="true"></div>
  <div class="page-kicker">Regional Ad Group Drafts</div>
  <h1>City-Specific Opportunities</h1>
  <div class="page-body">
    <p>These are review drafts, not live structure changes. They should become staged ad groups only after the client confirms each city and service line as Focus.</p>
    {''.join(opportunity_blocks)}
  </div>
</section>
<section class="section pdf-page">
  <div class="section-header" aria-hidden="true"></div>
  <div class="subsection-header" aria-hidden="true"></div>
  <div class="page-kicker">Sources</div>
  <h1>Source Files And Platform References</h1>
  <div class="page-body source-list">
    <p><strong>Source files:</strong> search_terms_report_2026-05-04.csv, location_report_2026-05-04.csv, and the Sky Therapies Google Ads Editor export dated 2026-05-04.</p>
    <ul>
      <li><a href="https://support.google.com/google-ads/editor/answer/30564?hl=en">Google Ads Editor CSV import</a></li>
      <li><a href="https://support.google.com/google-ads/editor/answer/57747?hl=en">Google Ads Editor CSV columns</a></li>
      <li><a href="https://support.google.com/google-ads/editor/answer/30573?hl=en">Google Ads Editor location import</a></li>
      <li><a href="https://support.google.com/google-ads/answer/2732132?hl=en">Google Ads bid adjustments</a></li>
      <li><a href="../../../../docs/GOOGLE_ADS_AGENT_PROCESS.md">Google Ads Agent process</a></li>
    </ul>
    {table(["Artifact", "Path", "Use"], source_rows)}
    <p><strong>Validation note:</strong> the full current Sky export contains pre-existing exact-match, negative-exact, and RSA copy-quality issues. The Focus additions delta is the clean upload candidate from this pass. The full revised export is retained for review context and should not be treated as launch-ready until the existing export issues are reconciled.</p>
    <p>The revised CSV is for Google Ads Editor review only. It is not a direct launch file and does not push changes to Google Ads.</p>
  </div>
</section>
</body>
</html>
"""
    return body


def write_client_email(decisions: list[TermDecision], locations: list[LocationInsight], grouped_review: SearchTermReview) -> None:
    lines = [
        "Subject: Sky Therapies search terms and city focus confirmation",
        "",
        "Hi [Client Name],",
        "",
        "We reviewed the latest search terms and location performance for Sky Therapies. A few terms are clear enough to stage for review, and a few need your call before we build around them.",
        "",
        "The main thing we need from you is how you want to handle the cities and a small set of unclear searches below.",
        "",
        "Please reply inline with Focus, Keep, or Exclude where noted.",
    ]
    if grouped_review.question_groups:
        section_labels = [
            ("service", "**Service Confirmations**"),
            ("regional", "**Regional Confirmations**"),
            ("exclude", "**Exclude Recommendations**"),
        ]
        for group_type, label in section_labels:
            groups = [group for group in grouped_review.question_groups if group.group_type == group_type]
            if not groups:
                continue
            lines.extend(["", label])
            for group in groups:
                lines.append("")
                if group.group_type == "regional":
                    lines.append(f"**{group.title}**")
                    lines.append(group.question)
                    lines.append("")
                    for region in group.regions:
                        lines.append(f"- {region}: [Focus / Keep / Exclude]")
                    lines.append("")
                    lines.append("If any city is unclear, mark it Discuss and we can talk through it.")
                    continue
                lines.append(f"**{group.title}:** {group.question} Example searches:")
                for term in group.terms[:3]:
                    lines.append(f"- {term}")
                lines.append(f"Suggested default: {group.default_action}")
    else:
        lines.append("- No service-area questions require client input from this search-term batch.")
    lines.extend(
        [
            "",
            "Regional notes for your confirmation:",
            "- Toronto has the most volume and 2 conversions, but CPA is higher than Markham.",
            "- Markham has 1 conversion at lower cost and looks like the strongest city to review as a priority.",
            "- Mississauga and North York have engagement but no conversions yet.",
            "- Brampton, Vaughan, and Richmond Hill should stay under scrutiny before we increase focus.",
            "",
            "Possible regional buildout:",
            "- City-specific ad groups and ad copy for approved Focus cities: [Approve / Discuss]",
            "",
            "Looking forward to your feedback on these. If you have any questions on how this process works, just reach out and we are happy to hop on a call and help.",
            "",
            "Thanks,",
            "[Your Name]",
        ]
    )
    (BUILD_DIR / "client_email_draft.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_human_review(decisions: list[TermDecision], locations: list[LocationInsight], additions: list[dict[str, str]]) -> None:
    focus_terms = [item.search_term for item in decisions if item.decision == "Focus"]
    review_terms = [item.search_term for item in decisions if item.decision == "Review"]
    exclude_terms = [item.search_term for item in decisions if item.decision == "Exclude"]
    lines = [
        "# Sky Therapies Search Optimization Human Review",
        "",
        "Date: 2026-05-04",
        "Source report window: April 26, 2026 to May 2, 2026",
        "",
        "## Staged",
        "",
        f"- Paused Focus keyword additions staged: {len(additions)}",
        "- Match type for additions: Phrase",
        "- Live Google Ads changes: none",
        "",
        "## Client Confirmation Needed",
        "",
        f"- Focus candidates found: {len(focus_terms)}",
        f"- Review candidates found: {len(review_terms)}",
        f"- Exclude recommendations found: {len(exclude_terms)}",
        "",
        "## Regional Findings",
        "",
        "- Toronto has the most volume and 2 conversions in ARC - Search - Services.",
        "- Markham has 1 conversion on lower spend and should be reviewed as a priority focus city.",
        "- Mississauga and North York have engagement but no conversions.",
        "- Brampton, Vaughan, and Richmond Hill should be scrutinized before increasing investment.",
        "- No postal-code targeting is recommended until the client confirms exact preferred service areas.",
        "",
        "## Sources",
        "",
        "- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en",
        "- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en",
        "- Google Ads Editor location import: https://support.google.com/google-ads/editor/answer/30573?hl=en",
        "- Google Ads bid adjustments: https://support.google.com/google-ads/answer/2732132?hl=en",
    ]
    (BUILD_DIR / "human_review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    fieldnames, editor_rows = read_editor_export(EDITOR_EXPORT)
    search_rows = read_google_report(SEARCH_TERMS, "Search term,")
    location_rows = read_google_report(LOCATIONS, "Location,")

    decisions = aggregate_search_terms(search_rows)
    insights = location_insights(location_rows)
    grouped_review = build_search_term_review(
        search_rows,
        service_terms=[
            "EMDR Therapy",
            "Trauma Therapy",
            "PTSD Therapy",
            "DBR Therapy",
            "Chronic Pain Therapy",
            "Pain Reprocessing Therapy",
            "IBS Therapy",
            "Gut Hypnotherapy",
            "Chronic Illness Therapy",
            "First Responder Therapy",
        ],
        approved_regions=["Toronto, Ontario, Canada"],
        candidate_regions=[item.location for item in insights],
    )
    revised_rows, additions = make_focus_additions(decisions, editor_rows, fieldnames)

    decisions_path = BUILD_DIR / "search_term_focus_keep_exclude_review.csv"
    write_csv(decisions_path, list(TermDecision.__dataclass_fields__.keys()), [asdict(item) for item in decisions])

    additions_path = BUILD_DIR / "paused_focus_keyword_additions.csv"
    write_csv(additions_path, fieldnames, additions, delimiter="\t", encoding="utf-16")

    regional_path = BUILD_DIR / "regional_targeting_analysis.csv"
    write_csv(regional_path, list(LocationInsight.__dataclass_fields__.keys()), [asdict(item) for item in insights])

    question_groups_path = BUILD_DIR / "search_term_client_question_groups.csv"
    write_csv(
        question_groups_path,
        ["group_id", "group_type", "title", "question", "terms", "regions", "services", "default_action"],
        grouped_review.question_group_rows(),
    )

    opportunities_path = BUILD_DIR / "regional_ad_group_opportunities.json"
    opportunities_path.write_text(json.dumps(regional_opportunities(), indent=2), encoding="utf-8")

    revised_csv = BUILD_DIR / "skytherapies_google_ads_editor_staging_rev1_20260504_optimization.tsv"
    write_csv(revised_csv, fieldnames, revised_rows, delimiter="\t", encoding="utf-16")

    write_client_email(decisions, insights, grouped_review)
    write_human_review(decisions, insights, additions)

    html_path = BUILD_DIR / "Sky_Therapies_Search_Terms_Regional_Focus_Confirmation.html"
    pdf_path = BUILD_DIR / "Sky_Therapies_Search_Terms_Regional_Focus_Confirmation.pdf"
    html_path.write_text(build_html(decisions, insights, additions, grouped_review), encoding="utf-8")
    export_pdf(html_path, pdf_path, timeout_seconds=90)

    findings, counts = audit_html(html_path)
    audit_payload = {
        "html": str(html_path),
        "counts": counts,
        "findings": [finding.__dict__ for finding in findings],
    }
    (BUILD_DIR / "report_static_audit.json").write_text(json.dumps(audit_payload, indent=2), encoding="utf-8")

    manifest = {
        "client": "skytherapies",
        "build_dir": str(BUILD_DIR),
        "source_files": {
            "editor_export": str(EDITOR_EXPORT),
            "search_terms": str(SEARCH_TERMS),
            "locations": str(LOCATIONS),
        },
        "outputs": {
            "decisions": str(decisions_path),
            "focus_additions": str(additions_path),
            "regional_analysis": str(regional_path),
            "search_term_client_question_groups": str(question_groups_path),
            "regional_opportunities": str(opportunities_path),
            "staging_csv": str(revised_csv),
            "html": str(html_path),
            "pdf": str(pdf_path),
            "email": str(BUILD_DIR / "client_email_draft.md"),
            "human_review": str(BUILD_DIR / "human_review.md"),
            "static_audit": str(BUILD_DIR / "report_static_audit.json"),
        },
        "counts": {
            "search_term_rows": len(search_rows),
            "unique_decisions": len(decisions),
            "focus_candidates": sum(1 for item in decisions if item.decision == "Focus"),
            "review_candidates": sum(1 for item in decisions if item.decision == "Review"),
            "exclude_recommendations": sum(1 for item in decisions if item.decision == "Exclude"),
            "keep_terms": sum(1 for item in decisions if item.decision == "Keep"),
            "paused_focus_additions": len(additions),
            "revised_staging_rows": len(revised_rows),
        },
    }
    (BUILD_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest["counts"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
