#!/usr/bin/env python3
"""Build the NKPsych search-term and regional targeting optimization package."""

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


BUILD_DIR = Path(__file__).resolve().parent
CLIENT_DIR = ROOT / "clients" / "NKPsych.com"
EDITOR_EXPORT = CLIENT_DIR / "campaigns" / "account_export.csv"
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
class NegativeCandidate:
    search_term: str
    criterion_type: str
    campaign: str
    ad_group: str
    clicks: float
    impressions: float
    cost: float
    conversions: float
    reason: str


@dataclass
class LocationInsight:
    location: str
    campaign: str
    clicks: float
    impressions: float
    cost: float
    conversions: float
    conversion_rate: float
    cost_per_conversion: float
    recommendation: str
    bid_adjustment_review: str
    rationale: str


HEADERS = [
    "Campaign",
    "Campaign Type",
    "Networks",
    "Budget",
    "Budget type",
    "EU political ads",
    "Broad match keywords",
    "Ad Group",
    "Criterion Type",
    "Keyword",
    "Final URL",
    "Location",
    "Location ID",
    "Ad type",
    "Status",
    *[f"Headline {index}" for index in range(1, 16)],
    *[f"Description {index}" for index in range(1, 5)],
    "Path 1",
    "Path 2",
    "Radius",
    "Bid Modifier",
    "Campaign Status",
    "Ad Group Status",
    "Approval Status",
    "Ad strength",
    "Comment",
]

SERVICE_AD_GROUPS = {
    "child therapy": "Child Therapy - Chicago",
    "child therapist": "Child Therapy - Chicago",
    "children": "Child Therapy - Chicago",
    "kids": "Child Therapy - Chicago",
    "couples": "Couples Therapy - Chicago",
    "family": "Family Therapy - Chicago",
    "emdr": "EMDR Therapy - Chicago",
    "edmr": "EMDR Therapy - Chicago",
    "ptsd": "Trauma Therapy - Chicago",
    "trauma": "Trauma Therapy - Chicago",
    "therapist": "Therapy - Chicago",
    "therapy": "Therapy - Chicago",
    "psychologist": "Psychology - Chicago",
}

EXCLUDE_PATTERNS = {
    "aba": "ABA or autism-center intent is outside the staged therapy focus.",
    "action behavior": "Competitor or institution name with no conversion signal.",
    "academy": "Competitor or institution name with no conversion signal.",
    "addiction counselor": "Addiction counseling is not confirmed as a supported focus.",
    "autism": "Autism-center intent is outside the staged therapy focus.",
    "blossom": "Competitor or institution name with no conversion signal.",
    "center for psychology": "Generic center-seeking query with weak fit.",
    "cst academy": "Competitor or institution name with no conversion signal.",
    "geriatric": "Geriatric psychology is not confirmed as a supported focus.",
    "local psychiatrist": "Psychiatry is not confirmed as a supported focus in this package.",
    "lurie": "Competitor or institution name with no conversion signal.",
    "marriage counselor": "Marriage counseling is not confirmed as a supported focus.",
    "neuro psychologist": "Neuropsychology is not confirmed as a supported focus.",
    "northwestern": "Competitor or institution name with no conversion signal.",
    "psychiatrist": "Psychiatry is not confirmed as a supported focus in this package.",
    "reunification": "Reunification therapy is not confirmed as a supported focus.",
    "sex therapist": "Sex therapy is not confirmed as a supported focus.",
    "stride autism": "Competitor or institution name with no conversion signal.",
}

REVIEW_PATTERNS = {
    "insurance": "Insurance language converted once, but coverage terms need client confirmation.",
    "polish": "Language-specific demand needs client confirmation before focus expansion.",
    "polski": "Language-specific demand needs client confirmation before focus expansion.",
    "right now": "Urgent wording converted once, but crisis-intent handling needs human review.",
}

GEO_RESEARCH = [
    {
        "name": "Chicago",
        "location_id": "1016367",
        "type": "City",
        "priority": "Core",
        "bid_modifier_review": "Keep as core city target. Review budget and CPA before increasing.",
        "reason": "Only reported location in the attached window and the current Chicago row converted.",
    },
    {
        "name": "60616",
        "location_id": "9021721",
        "type": "Postal Code",
        "priority": "Priority review",
        "bid_modifier_review": "Review as a South Loop, Chinatown, and Near South focus layer.",
        "reason": "Closest ZIP-style focus around the visible Chicago service page signal.",
    },
    {
        "name": "60605",
        "location_id": "9021710",
        "type": "Postal Code",
        "priority": "Priority review",
        "bid_modifier_review": "Review as a Loop and South Loop layer.",
        "reason": "Dense central Chicago demand area near the 60616 focus.",
    },
    {
        "name": "60607",
        "location_id": "9021712",
        "type": "Postal Code",
        "priority": "Review",
        "bid_modifier_review": "Review as a West Loop and university-adjacent layer.",
        "reason": "Nearby city intent layer for therapy searches.",
    },
    {
        "name": "60608",
        "location_id": "9021713",
        "type": "Postal Code",
        "priority": "Review",
        "bid_modifier_review": "Review as a Pilsen and Bridgeport layer.",
        "reason": "Nearby Chicago ZIP with search-term neighborhood overlap.",
    },
    {
        "name": "60610",
        "location_id": "9021715",
        "type": "Postal Code",
        "priority": "Review",
        "bid_modifier_review": "Review as Near North and Old Town layer.",
        "reason": "Useful higher-density city layer for Chicago therapy demand.",
    },
    {
        "name": "60614",
        "location_id": "9021719",
        "type": "Postal Code",
        "priority": "Review",
        "bid_modifier_review": "Review as Lincoln Park layer.",
        "reason": "Chicago neighborhood layer to test city-specific copy and bidding.",
    },
    {
        "name": "60622",
        "location_id": "9021727",
        "type": "Postal Code",
        "priority": "Review",
        "bid_modifier_review": "Review as Wicker Park and Ukrainian Village layer.",
        "reason": "Chicago neighborhood layer to test city-specific copy and bidding.",
    },
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


def read_google_report(path: Path, header_name: str) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    header_index = next(index for index, row in enumerate(csv.reader(lines)) if row and row[0] == header_name)
    return [dict(row) for row in csv.DictReader(lines[header_index:])]


def read_editor_export(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    content = path.read_text(encoding="utf-16")
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")
    return list(reader.fieldnames or []), [dict(row) for row in reader]


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
    return fallback or "Therapy - Chicago"


def classify_term(term: str, clicks: float, impressions: float, cost: float, conversions: float, ad_group: str) -> tuple[str, str, str]:
    normalized = normalize_term(term)
    has_service = any(marker in normalized for marker in SERVICE_AD_GROUPS)
    has_geo = any(token in normalized for token in ("chicago", "near me", "close to me", "south loop", "pilsen", "lincoln park"))

    if normalized in {"therapist", "therapy", "psychologist", "psychologists", "therapists"}:
        return "Review", "Review before adding", "Broad head term has signal, but phrase expansion could open too much generic traffic."

    if "gay therapist" in normalized or "gay therapists" in normalized:
        return "Review", "Client to mark Focus, Keep, or Exclude", "Specialized therapy intent needs client confirmation before focus expansion."

    if "center" in normalized and conversions == 0:
        return "Review", "Review before adding", "Center-seeking wording may indicate competitor or institution intent."

    for pattern, reason in EXCLUDE_PATTERNS.items():
        if pattern in normalized and conversions == 0:
            return "Exclude", "Stage as negative phrase for review", reason

    for pattern, reason in REVIEW_PATTERNS.items():
        if pattern in normalized:
            return "Review", "Client to mark Focus, Keep, or Exclude", reason

    if conversions > 0 and has_service:
        return "Focus", "Add as paused phrase keyword", "Conversion signal plus clear therapy-service intent."

    if clicks >= 2 and cost >= 20 and conversions == 0 and not has_service:
        return "Review", "Review before excluding", "Spend without conversion, but intent needs human confirmation."

    if clicks >= 2 and has_service and "clinic" not in normalized:
        return "Focus", "Add as paused phrase keyword", "Multiple clicks with clear therapy-service intent."

    if has_geo and has_service:
        return "Review", "Review for city or ZIP focus", "Geo-modified service term should inform Chicago targeting."

    if any(marker in normalized for marker in ("what ", "how ", "is ", "can ")):
        return "Keep", "Continue observing", "Informational therapy research query without enough waste signal."

    if has_service:
        return "Keep", "Continue observing", "Service-fit query with low current volume."

    return "Keep", "Continue observing", "Low-risk exploratory query with no urgent action from this report."


def aggregate_search_terms(rows: list[dict[str, str]]) -> list[TermDecision]:
    grouped: dict[str, dict[str, object]] = {}
    for row in rows:
        term = normalize_term(row.get("Search term", ""))
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
        decision, action, reason = classify_term(term, clicks, impressions, cost, conversions, ad_group)
        decisions.append(
            TermDecision(
                search_term=term,
                decision=decision,
                recommended_action=action,
                campaign=campaign,
                ad_group=ad_group,
                suggested_ad_group=suggested_ad_group(term, ad_group),
                clicks=clicks,
                impressions=impressions,
                cost=cost,
                conversions=conversions,
                reason=reason,
                client_prompt="Reply Focus, Keep, Exclude, or Geo.",
            )
        )

    return sorted(decisions, key=lambda item: (item.decision != "Focus", item.decision != "Review", -item.conversions, -item.cost, item.search_term))


def negative_candidates(decisions: list[TermDecision]) -> list[NegativeCandidate]:
    candidates = []
    for item in decisions:
        if item.decision != "Exclude":
            continue
        candidates.append(
            NegativeCandidate(
                search_term=item.search_term,
                criterion_type="Negative Phrase",
                campaign=item.campaign,
                ad_group=item.ad_group,
                clicks=item.clicks,
                impressions=item.impressions,
                cost=item.cost,
                conversions=item.conversions,
                reason=item.reason,
            )
        )
    return candidates


def location_insights(rows: list[dict[str, str]]) -> list[LocationInsight]:
    insights = []
    for row in rows:
        location = row.get("Location", "").strip()
        if not location or location.startswith("Total:"):
            continue
        clicks = num(row.get("Clicks"))
        impressions = num(row.get("Impr."))
        cost = num(row.get("Cost"))
        conversions = num(row.get("Conversions"))
        conv_rate = num(row.get("Conv. rate"))
        cpa = num(row.get("Cost / conv."))
        if location.startswith("Chicago") and conversions > 0:
            recommendation = "Core focus"
            bid = "Keep Chicago as core. Review ZIP layering before changing bids."
            rationale = "Only active location in the attached report and it produced 13 conversions."
        else:
            recommendation = "No action"
            bid = "None"
            rationale = "No material activity in this report window."
        insights.append(
            LocationInsight(
                location=location,
                campaign=row.get("Campaign", "").strip(),
                clicks=clicks,
                impressions=impressions,
                cost=cost,
                conversions=conversions,
                conversion_rate=conv_rate,
                cost_per_conversion=cpa,
                recommendation=recommendation,
                bid_adjustment_review=bid,
                rationale=rationale,
            )
        )
    return insights


def existing_phrase_keywords(editor_rows: list[dict[str, str]]) -> set[str]:
    return {
        normalize_term(row.get("Keyword", ""))
        for row in editor_rows
        if row.get("Criterion Type", "").strip().lower() == "phrase" and row.get("Keyword", "").strip()
    }


def base_row() -> dict[str, str]:
    return {header: "" for header in HEADERS}


def make_staging_rows(decisions: list[TermDecision], negatives: list[NegativeCandidate], editor_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    campaign = "ARC - Search - Chicago Therapy - V1"
    landing_page = "https://www.nkpsych.com/location/chicago-il"
    rows: list[dict[str, str]] = []

    campaign_row = base_row()
    campaign_row.update(
        {
            "Campaign": campaign,
            "Campaign Type": "Search",
            "Networks": "Google search",
            "Budget": "25.00",
            "Budget type": "Daily",
            "EU political ads": "Doesn't have EU political ads",
            "Broad match keywords": "Off",
            "Status": "Paused",
            "Campaign Status": "Paused",
            "Comment": "Optimization review package. Human review required before launch.",
        }
    )
    rows.append(campaign_row)

    for geo in GEO_RESEARCH:
        if geo["priority"] not in {"Core", "Priority review"}:
            continue
        row = base_row()
        row.update(
            {
                "Campaign": campaign,
                "Location": f"{geo['name']}, Illinois, United States" if geo["type"] == "Postal Code" else "Chicago, Illinois, United States",
                "Location ID": geo["location_id"],
                "Status": "Paused",
                "Campaign Status": "Paused",
                "Comment": f"{geo['priority']} geo review. {geo['bid_modifier_review']}",
            }
        )
        rows.append(row)

    existing = existing_phrase_keywords(editor_rows)
    additions: list[dict[str, str]] = []
    focus_decisions = [item for item in decisions if item.decision == "Focus"]
    for item in focus_decisions:
        keyword = item.search_term
        normalized = normalize_term(keyword)
        if normalized in existing:
            continue
        row = base_row()
        row.update(
            {
                "Campaign": campaign,
                "Ad Group": item.suggested_ad_group,
                "Criterion Type": "Phrase",
                "Keyword": keyword,
                "Final URL": landing_page,
                "Status": "Paused",
                "Campaign Status": "Paused",
                "Ad Group Status": "Paused",
                "Comment": "Paused search-term Focus addition pending human review.",
            }
        )
        rows.append(row)
        additions.append(row)
        existing.add(normalized)

    for item in negatives[:25]:
        row = base_row()
        row.update(
            {
                "Campaign": campaign,
                "Criterion Type": "Negative Phrase",
                "Keyword": item.search_term,
                "Status": "Paused",
                "Campaign Status": "Paused",
                "Comment": "Paused negative review candidate from search-term cleanup.",
            }
        )
        rows.append(row)

    for ad_group in sorted({row["Ad Group"] for row in additions if row.get("Ad Group")}):
        ad_group_row = base_row()
        ad_group_row.update(
            {
                "Campaign": campaign,
                "Ad Group": ad_group,
                "Status": "Paused",
                "Campaign Status": "Paused",
                "Ad Group Status": "Paused",
                "Comment": "Paused ad group context for validator and review.",
            }
        )
        rows.append(ad_group_row)

        rsa = base_row()
        rsa.update(rsa_payload(campaign, ad_group, landing_page))
        rows.append(rsa)

    return rows, additions


def rsa_payload(campaign: str, ad_group: str, final_url: str) -> dict[str, str]:
    service = ad_group.replace(" - Chicago", "").replace("Therapy - ", "Therapy")
    headlines = [
        "Chicago Counseling Consult",
        "Private Therapy In Chicago",
        "Talk Through Stress Today",
        "Care For Stress And Anxiety",
        "Support For Child Anxiety",
        "Family Sessions In Chicago",
        "Couples Care Near Downtown",
        "Trauma EMDR Care In Chicago",
        "Licensed Clinical Guidance",
        "Schedule A Therapy Consult",
        "Local Care For Hard Weeks",
        "Clear Next Steps For Care",
        "Support That Fits Your Life",
        "NKPsych Chicago Clinicians",
        "Care Plans For Real Needs",
        "Start With A Private Call",
    ]
    descriptions = [
        "Schedule today to review focused Chicago care options for children and adults.",
        "Book today to discuss private therapy options, local availability, and fit.",
        "Book today to discuss anxiety, family stress, trauma support, and next steps in care.",
        "Call today for Chicago therapy guidance with a licensed team and clear scheduling.",
    ]
    row = base_row()
    row.update(
        {
            "Campaign": campaign,
            "Ad Group": ad_group,
            "Ad type": "Responsive search ad",
            "Final URL": final_url,
            "Status": "Paused",
            "Campaign Status": "Paused",
            "Ad Group Status": "Paused",
            "Approval Status": "",
            "Path 1": "therapy",
            "Path 2": "chicago",
            "Comment": f"Paused RSA context for {service} optimization review.",
        }
    )
    for index, headline in enumerate(headlines, start=1):
        row[f"Headline {index}"] = headline
    for index, description in enumerate(descriptions, start=1):
        row[f"Description {index}"] = description
    return row


def metric(value: float, decimals: int = 0) -> str:
    return f"{value:,.{decimals}f}" if decimals else f"{value:,.0f}"


def table(headers: list[str], rows: list[list[object]]) -> str:
    head = "".join(f"<th>{esc(header)}</th>" for header in headers)
    body = "".join("<tr>" + "".join(f"<td>{esc(cell)}</td>" for cell in row) + "</tr>" for row in rows)
    return f'<table class="tax-table"><tr>{head}</tr>{body}</table>'


def build_html(decisions: list[TermDecision], negatives: list[NegativeCandidate], insights: list[LocationInsight], additions: list[dict[str, str]]) -> str:
    focus = [item for item in decisions if item.decision == "Focus"]
    review = [item for item in decisions if item.decision == "Review"]
    keep = [item for item in decisions if item.decision == "Keep"]
    total_clicks = sum(item.clicks for item in decisions)
    total_cost = sum(item.cost for item in decisions)
    total_conversions = sum(item.conversions for item in decisions)
    location = insights[0] if insights else None

    focus_rows = [
        [item.search_term, item.suggested_ad_group, metric(item.clicks), f"${item.cost:,.2f}", metric(item.conversions, 2), item.reason]
        for item in focus[:18]
    ]
    review_rows = [
        [item.search_term, item.recommended_action, metric(item.clicks), f"${item.cost:,.2f}", metric(item.conversions, 2), item.reason]
        for item in review[:22]
    ]
    negative_rows = [
        [item.search_term, item.criterion_type, metric(item.clicks), f"${item.cost:,.2f}", item.reason]
        for item in negatives[:22]
    ]
    geo_rows = [
        [geo["name"], geo["location_id"], geo["type"], geo["priority"], geo["bid_modifier_review"], geo["reason"]]
        for geo in GEO_RESEARCH
    ]

    location_summary = ""
    if location:
        location_summary = (
            f"<p>The attached location report only shows {esc(location.location)} for April 3, 2026 to May 2, 2026. "
            f"It recorded {metric(location.clicks)} clicks, {metric(location.impressions)} impressions, "
            f"${location.cost:,.2f} cost, {metric(location.conversions, 2)} conversions, "
            f"{location.conversion_rate:.2f}% conversion rate, and ${location.cost_per_conversion:,.2f} cost per conversion.</p>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>NKPsych Search Terms And Regional Targeting Review</title>
<style>
{fixed_css()}
body {{ color: #172033; }}
.section-body p {{ font-size: 14px; line-height: 1.45; }}
.metric-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 18px 0; }}
.metric {{ border: 1px solid #d8dee8; padding: 12px; border-radius: 6px; background: #f8fafc; }}
.metric strong {{ display: block; font-size: 22px; color: #0f5132; }}
.source-list li {{ margin-bottom: 6px; }}
.subsection-header, .continuation-header {{ font-weight: 700; margin: 12px 0 6px; color: #26364f; }}
</style>
</head>
<body>
<main class="report">
<section class="section page">
<div class="section"><div class="section-header">A - Executive Readout</div><div class="section-body">
<h1>NKPsych Search Optimization Review</h1>
<p>This is a staged review package, not a live launch. The goal is to recover lost conversion rate by cleaning search terms and tightening Chicago targeting around verified demand.</p>
<div class="metric-grid">
<div class="metric"><span>Search term clicks</span><strong>{metric(total_clicks)}</strong></div>
<div class="metric"><span>Search term cost</span><strong>${total_cost:,.2f}</strong></div>
<div class="metric"><span>Search term conversions</span><strong>{metric(total_conversions, 2)}</strong></div>
<div class="metric"><span>Paused additions</span><strong>{len(additions)}</strong></div>
</div>
{location_summary}
<p>The highest historical conversion rate supplied for context was 20 percent. The attached search-term export currently shows {metric(total_conversions, 2)} conversions from {metric(total_clicks)} clicks, which supports cleanup before scaling budget.</p>
</div></div>
<div class="section"><div class="section-header">B - Focus Terms</div><div class="section-body">
<p>These terms have conversion signal or clear fit and were staged as paused phrase keyword additions only when not already present in the current phrase keyword set.</p>
<div class="subsection-header">Paused keyword additions</div>
{table(["Search term", "Suggested ad group", "Clicks", "Cost", "Conversions", "Reason"], focus_rows)}
</div></div>
</section>
<section class="section page">
<div class="section"><div class="section-header">C - Review And Cleanup</div><div class="section-body">
<p>These searches need human review because they either spend without enough proof, include sensitive wording, or need service-area confirmation.</p>
<div class="continuation-header">Search-term review context</div>
{table(["Search term", "Action", "Clicks", "Cost", "Conversions", "Reason"], review_rows)}
</div></div>
<div class="section"><div class="section-header">D - Negative Review Candidates</div><div class="section-body">
<p>These are staged as review candidates only. They should be checked before import so no valid therapy demand is accidentally blocked.</p>
{table(["Search term", "Type", "Clicks", "Cost", "Reason"], negative_rows)}
</div></div>
</section>
<section class="section page">
<div class="section"><div class="section-header">E - Chicago Geo Targeting</div><div class="section-body">
<p>The current location evidence is too broad. The package recommends keeping Chicago as the core target and reviewing ZIP layers around 60616 and nearby city intent areas before changing bids.</p>
<div class="subsection-header">Geo layers for review</div>
{table(["Geo", "Google ID", "Type", "Priority", "Bid review", "Reason"], geo_rows)}
</div></div>
<div class="section"><div class="section-header">F - Sources</div><div class="section-body">
<ul class="source-list">
<li><a href="https://developers.google.com/google-ads/api/data/geotargets">Google geo targets</a></li>
<li><a href="https://developers.google.com/google-ads/api/docs/targeting/location-targeting">Google Ads location targeting</a></li>
<li><a href="https://support.google.com/google-ads/editor/answer/30564?hl=en">Google Ads Editor CSV import</a></li>
<li><a href="https://www.nkpsych.com/location/chicago-il">NKPsych Chicago page</a></li>
<li><a href="https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Community-Areas-current-/cauq-8yn6/about">City of Chicago community areas data</a></li>
</ul>
</div></div>
</section>
</main>
</body>
</html>
"""


def write_human_review(decisions: list[TermDecision], negatives: list[NegativeCandidate], additions: list[dict[str, str]], insights: list[LocationInsight]) -> None:
    focus = sum(1 for item in decisions if item.decision == "Focus")
    review = sum(1 for item in decisions if item.decision == "Review")
    keep = sum(1 for item in decisions if item.decision == "Keep")
    lines = [
        "# NKPsych Search Optimization Human Review",
        "",
        "This package is staged for Google Ads Editor review only. Do not launch before human approval.",
        "",
        "## Performance Context",
        "",
        "- Search terms report window: April 3, 2026 to May 2, 2026.",
        f"- Search-term totals from parsed rows: {sum(item.clicks for item in decisions):.0f} clicks, ${sum(item.cost for item in decisions):.2f} cost, {sum(item.conversions for item in decisions):.2f} conversions.",
        "- User-supplied context: highest prior conversion rate was 20 percent, current rate is around 8 percent.",
        "",
        "## Outputs",
        "",
        f"- Focus decisions: {focus}.",
        f"- Review decisions: {review}.",
        f"- Keep decisions: {keep}.",
        f"- Negative review candidates: {len(negatives)}.",
        f"- Paused keyword additions staged: {len(additions)}.",
        "",
        "## Geo Notes",
        "",
        "- The attached location report only shows Chicago, Illinois, United States.",
        "- Google geo target IDs were sourced from Google's 2026-03-31 geo target CSV.",
        "- Keep Chicago as core, then review 60616 and nearby ZIP layers before changing bids.",
        "",
        "## Source Links",
        "",
        "- Google geo targets: https://developers.google.com/google-ads/api/data/geotargets",
        "- Google Ads location targeting: https://developers.google.com/google-ads/api/docs/targeting/location-targeting",
        "- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en",
        "- NKPsych Chicago page: https://www.nkpsych.com/location/chicago-il",
        "- City of Chicago community areas: https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Community-Areas-current-/cauq-8yn6/about",
    ]
    (BUILD_DIR / "human_review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    search_rows = read_google_report(SEARCH_TERMS, "Search term")
    location_rows = read_google_report(LOCATIONS, "Location")
    _, editor_rows = read_editor_export(EDITOR_EXPORT)

    decisions = aggregate_search_terms(search_rows)
    negatives = negative_candidates(decisions)
    insights = location_insights(location_rows)
    staging_rows, additions = make_staging_rows(decisions, negatives, editor_rows)

    decisions_path = BUILD_DIR / "search_term_focus_keep_exclude_review.csv"
    write_csv(decisions_path, list(TermDecision.__dataclass_fields__.keys()), [asdict(item) for item in decisions])

    negatives_path = BUILD_DIR / "negative_review_candidates.csv"
    write_csv(negatives_path, list(NegativeCandidate.__dataclass_fields__.keys()), [asdict(item) for item in negatives])

    additions_path = BUILD_DIR / "paused_focus_keyword_additions.csv"
    write_csv(additions_path, HEADERS, additions, delimiter="\t", encoding="utf-16")

    regional_path = BUILD_DIR / "regional_targeting_analysis.csv"
    write_csv(regional_path, list(LocationInsight.__dataclass_fields__.keys()), [asdict(item) for item in insights])

    research_payload = {
        "source": "https://developers.google.com/google-ads/api/data/geotargets",
        "google_geo_targets_version": "2026-03-31",
        "city_of_chicago_source": "https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Community-Areas-current-/cauq-8yn6/about",
        "nkpsych_chicago_source": "https://www.nkpsych.com/location/chicago-il",
        "targets": GEO_RESEARCH,
    }
    (BUILD_DIR / "regional_targeting_research.json").write_text(json.dumps(research_payload, indent=2), encoding="utf-8")

    staging_path = BUILD_DIR / "nkpsych_google_ads_editor_staging_rev1_20260504_optimization.csv"
    write_csv(staging_path, HEADERS, staging_rows, delimiter="\t", encoding="utf-16")

    write_human_review(decisions, negatives, additions, insights)

    html_path = BUILD_DIR / "NKPsych_Search_Terms_Regional_Targeting_Review.html"
    pdf_path = BUILD_DIR / "NKPsych_Search_Terms_Regional_Targeting_Review.pdf"
    html_path.write_text(build_html(decisions, negatives, insights, additions), encoding="utf-8")
    export_pdf(html_path, pdf_path, timeout_seconds=90)

    findings, counts = audit_html(html_path)
    static_audit_path = BUILD_DIR / "report_static_audit.json"
    static_audit_path.write_text(
        json.dumps({"html": str(html_path), "counts": counts, "findings": [finding.__dict__ for finding in findings]}, indent=2),
        encoding="utf-8",
    )

    manifest = {
        "client": "NKPsych",
        "build_dir": str(BUILD_DIR),
        "source_files": {
            "editor_export": str(EDITOR_EXPORT),
            "search_terms": str(SEARCH_TERMS),
            "locations": str(LOCATIONS),
        },
        "outputs": {
            "decisions": str(decisions_path),
            "negative_review_candidates": str(negatives_path),
            "focus_additions": str(additions_path),
            "regional_analysis": str(regional_path),
            "regional_research": str(BUILD_DIR / "regional_targeting_research.json"),
            "staging_csv": str(staging_path),
            "html": str(html_path),
            "pdf": str(pdf_path),
            "human_review": str(BUILD_DIR / "human_review.md"),
            "static_audit": str(static_audit_path),
        },
        "counts": {
            "search_term_rows": len(search_rows),
            "unique_decisions": len(decisions),
            "focus_candidates": sum(1 for item in decisions if item.decision == "Focus"),
            "review_candidates": sum(1 for item in decisions if item.decision == "Review"),
            "exclude_recommendations": len(negatives),
            "keep_terms": sum(1 for item in decisions if item.decision == "Keep"),
            "paused_focus_additions": len(additions),
            "staging_rows": len(staging_rows),
            "location_rows": len(location_rows),
        },
        "status": "staged_for_human_review",
    }
    (BUILD_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(json.dumps(manifest["counts"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
