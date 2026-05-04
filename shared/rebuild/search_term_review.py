"""Reusable search-term review grouping for client-facing automation."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Iterable


DEFAULT_REGION_TERMS = (
    "ajax",
    "barrie",
    "brampton",
    "downtown",
    "etobicoke",
    "hamilton",
    "kingston",
    "markham",
    "mississauga",
    "newmarket",
    "north york",
    "oakville",
    "ontario",
    "pickering",
    "richmond hill",
    "scarborough",
    "st catharines",
    "toronto",
    "vaughan",
)

EXCLUDE_INTENT_MARKERS = (
    "association",
    "clinic",
    "dietician",
    "dietitian",
    "doctor",
    "hospital",
    "injection",
    "medicine",
    "physio",
    "probiotic",
    "specialist",
)

OBSERVE_INTENT_MARKERS = (
    "how ",
    "is ",
    "what ",
    "when ",
    "which ",
    "why ",
    " vs ",
)


@dataclass(frozen=True)
class SearchTermDecision:
    search_term: str
    category: str
    client_action: str
    internal_action: str
    action_term: str
    negative_match_type: str
    negative_level: str
    matched_service: str
    matched_regions: list[str]
    unknown_regions: list[str]
    clicks: float
    impressions: float
    conversions: float
    reason: str


@dataclass(frozen=True)
class SearchTermQuestionGroup:
    group_id: str
    group_type: str
    title: str
    question: str
    terms: list[str] = field(default_factory=list)
    regions: list[str] = field(default_factory=list)
    services: list[str] = field(default_factory=list)
    default_action: str = "Review"


@dataclass(frozen=True)
class SearchTermReview:
    decisions: list[SearchTermDecision]
    question_groups: list[SearchTermQuestionGroup]

    def decision_rows(self) -> list[dict[str, object]]:
        return [asdict(decision) for decision in self.decisions]

    def question_group_rows(self) -> list[dict[str, object]]:
        return [
            {
                **asdict(group),
                "terms": "; ".join(group.terms),
                "regions": "; ".join(group.regions),
                "services": "; ".join(group.services),
            }
            for group in self.question_groups
        ]


def build_search_term_review(
    rows: list[dict[str, str]],
    *,
    service_terms: Iterable[str],
    approved_regions: Iterable[str],
    competitor_terms: Iterable[str] = (),
    candidate_regions: Iterable[str] = (),
    telehealth_regions: Iterable[str] = (),
    virtual_only: bool = False,
    physical_locations: Iterable[str] = (),
) -> SearchTermReview:
    services = normalize_unique(service_terms)
    competitors = normalize_unique(competitor_terms)
    approved = normalize_unique(region_name(region) for region in approved_regions)
    telehealth = normalize_unique(region_name(region) for region in telehealth_regions)
    regions = normalize_unique([*candidate_regions, *approved, *telehealth, *DEFAULT_REGION_TERMS])
    grouped = aggregate_terms(rows)
    decisions = [
        classify_search_term(
            term,
            metrics,
            services=services,
            competitors=competitors,
            approved_regions=approved,
            candidate_regions=regions,
            telehealth_regions=telehealth,
            virtual_only=virtual_only,
            physical_locations=normalize_unique(physical_locations),
        )
        for term, metrics in grouped.items()
        if not term.startswith("total:")
    ]
    decisions.sort(key=lambda item: (category_order(item.category), -item.conversions, -item.clicks, -item.impressions, item.search_term))
    return SearchTermReview(decisions=decisions, question_groups=build_question_groups(decisions))


def aggregate_terms(rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    grouped: dict[str, dict[str, float]] = {}
    for row in rows:
        term = normalize_text(row.get("Search term") or row.get("Search Term") or row.get("Query") or "")
        if not term:
            continue
        metrics = grouped.setdefault(term, {"clicks": 0.0, "impressions": 0.0, "conversions": 0.0})
        metrics["clicks"] += numeric_value(row.get("Clicks", ""))
        metrics["impressions"] += numeric_value(row.get("Impr.") or row.get("Impressions") or "")
        metrics["conversions"] += numeric_value(row.get("Conversions") or row.get("All conv.") or row.get("All conversions") or "")
    return grouped


def classify_search_term(
    term: str,
    metrics: dict[str, float],
    *,
    services: list[str],
    competitors: list[str],
    approved_regions: list[str],
    candidate_regions: list[str],
    telehealth_regions: list[str],
    virtual_only: bool,
    physical_locations: list[str],
) -> SearchTermDecision:
    matched_service = best_service_match(term, services)
    matched_regions = regions_in_term(term, candidate_regions)
    confirmed_regions = {*approved_regions, *telehealth_regions}
    unknown_regions = [region for region in matched_regions if region not in confirmed_regions]
    clicks = metrics["clicks"]
    impressions = metrics["impressions"]
    conversions = metrics["conversions"]
    lowered = term.lower()
    competitor = competitor_match(term, competitors)

    action_term = ""
    negative_match_type = ""
    negative_level = ""

    if competitor:
        category = "competitor_negative_candidate"
        client_action = "Do not ask the client to classify obvious competitor terms."
        internal_action = "Apply four-step pruning, then add the pruned competitor object as a campaign-level Negative Phrase unless an approved conquesting segment exists."
        action_term = competitor
        negative_match_type = "Negative Phrase"
        negative_level = "Campaign"
        reason = "Known competitor brand object matched the search term. Single-word components must be checked against service, city, brand, and protected terms before staging."
    elif is_exclude_intent(lowered):
        category = "exclude_recommendation"
        client_action = "No client question unless they want to override exclusions."
        internal_action = "Recommend exclusion review after single-word risk checks."
        reason = "Query appears to seek a provider, institution, procedure, supplement, or non-service intent. Do not negate a standalone word until service, city, and brand risk is checked."
    elif matched_service and virtual_only and matched_regions and not unknown_regions:
        category = "covered_service_observation"
        client_action = "Do not ask obvious virtual coverage questions."
        internal_action = "Keep observing unless performance increases."
        reason = "Virtual-only coverage is confirmed for this region."
    elif matched_service and unknown_regions:
        category = "unknown_region_confirmation"
        client_action = "Ask one grouped service-area question for the unknown regions."
        internal_action = "Do not create city ad groups until service area is confirmed."
        reason = regional_reason(unknown_regions, physical_locations, virtual_only)
    elif matched_service and conversions > 0:
        category = "focus_candidate"
        client_action = "Do not ask if service and region are already confirmed."
        internal_action = "Stage or recommend as a Focus keyword if it is not already covered."
        reason = "Conversion signal with confirmed service intent."
    elif matched_service and clicks >= 2:
        category = "focus_candidate"
        client_action = "Do not ask if service and region are already confirmed."
        internal_action = "Review for Focus addition if not already covered."
        reason = "Multiple clicks with confirmed service intent."
    elif matched_service:
        category = "covered_service_observation"
        client_action = "Do not ask obvious service-fit questions."
        internal_action = "Keep observing unless performance increases."
        reason = "The service appears to be known or website-supported."
    elif is_research_intent(lowered):
        category = "keep_observe"
        client_action = "Do not ask the client to classify low-risk research terms."
        internal_action = "Keep visible for trend monitoring."
        reason = "Informational query without enough waste signal to exclude."
    else:
        category = "unclear_intent_review"
        client_action = "Ask only if several similar unclear terms cluster together."
        internal_action = "Review internally before escalating to the client."
        reason = "Intent is not clearly mapped to a known service or exclusion."

    return SearchTermDecision(
        search_term=term,
        category=category,
        client_action=client_action,
        internal_action=internal_action,
        action_term=action_term,
        negative_match_type=negative_match_type,
        negative_level=negative_level,
        matched_service=matched_service,
        matched_regions=matched_regions,
        unknown_regions=unknown_regions,
        clicks=clicks,
        impressions=impressions,
        conversions=conversions,
        reason=reason,
    )


def build_question_groups(decisions: list[SearchTermDecision]) -> list[SearchTermQuestionGroup]:
    unknown_region_terms: list[SearchTermDecision] = []
    unclear_terms: list[SearchTermDecision] = []
    exclude_terms: list[SearchTermDecision] = []

    for decision in decisions:
        if decision.category == "unknown_region_confirmation":
            unknown_region_terms.append(decision)
        elif decision.category == "exclude_recommendation":
            exclude_terms.append(decision)
        elif decision.category == "unclear_intent_review" and (decision.clicks > 0 or decision.impressions >= 8):
            unclear_terms.append(decision)

    groups: list[SearchTermQuestionGroup] = []
    if unknown_region_terms:
        regions = sorted(set(
            display_region(region)
            for item in sorted(unknown_region_terms, key=lambda item: item.search_term)
            for region in item.unknown_regions
        ))
        services = normalize_unique(item.matched_service for item in unknown_region_terms if item.matched_service)
        terms = [
            item.search_term
            for item in sorted(unknown_region_terms, key=lambda item: (-item.conversions, -item.clicks, -item.impressions))[:8]
        ]
        groups.append(
            SearchTermQuestionGroup(
                group_id="regional_keyword_targeting",
                group_type="regional",
                title="Regional keyword targeting",
                question=(
                    "From the search term report, we picked up cities of interest for services. "
                    "Please confirm if you'd like to Focus, Keep, or Exclude keyword targeting for these cities. "
                    "This may also warrant building ad groups with unique ad copy for these cities."
                ),
                terms=dedupe_examples(terms),
                regions=regions,
                services=[title_case(service) for service in services],
                default_action="Discuss before building city-specific ad groups",
            )
        )

    if len(unclear_terms) >= 3:
        terms = [item.search_term for item in sorted(unclear_terms, key=lambda item: (-item.clicks, -item.impressions))[:10]]
        groups.append(
            SearchTermQuestionGroup(
                group_id="unclear_intent_cluster",
                group_type="service",
                title="Review unclear search intent cluster",
                question="These searches are not clearly tied to a confirmed service. Are any of these services you want us to pursue?",
                terms=dedupe_examples(terms),
                default_action="Review intent",
            )
        )

    if exclude_terms:
        terms = [item.search_term for item in sorted(exclude_terms, key=lambda item: (-item.clicks, -item.impressions))[:10]]
        groups.append(
            SearchTermQuestionGroup(
                group_id="exclude_recommendations",
                group_type="exclude",
                title="Review grouped exclusions",
                question="These look like non-fit searches, so we plan to keep them out unless you see a service we should support.",
                terms=dedupe_examples(terms),
                default_action="Exclude or continue excluding",
            )
        )

    return groups


def regional_reason(unknown_regions: list[str], physical_locations: list[str], virtual_only: bool) -> str:
    if virtual_only:
        return "Virtual service coverage is unclear for this region."
    if physical_locations:
        return "Service intent is clear, but this region is not confirmed against known physical locations or service area facts."
    return "Service intent is clear, but no physical-location or service-area fact confirms this region."


def dedupe_examples(terms: list[str], limit: int = 4) -> list[str]:
    output = []
    signatures = set()
    for term in terms:
        signature = re.sub(r"\b(therapy|therapist|counselling|counseling)\b", "", term.lower())
        signature = re.sub(r"\s+", " ", signature).strip()
        if signature in signatures:
            continue
        output.append(term)
        signatures.add(signature)
        if len(output) >= limit:
            break
    return output


def best_service_match(term: str, services: list[str]) -> str:
    term_tokens = meaningful_tokens(term)
    best = ""
    best_score = 0
    for service in services:
        service_tokens = meaningful_tokens(service)
        if not service_tokens:
            continue
        score = len(term_tokens & service_tokens)
        if normalize_text(service) in term or service in term:
            score += 3
        if score > best_score:
            best = service
            best_score = score
    return best if best_score > 0 else ""


def regions_in_term(term: str, regions: list[str]) -> list[str]:
    lowered = f" {term.lower()} "
    found = []
    for region in regions:
        if not region:
            continue
        pattern = rf"(?<![a-z0-9]){re.escape(region.lower())}(?![a-z0-9])"
        if re.search(pattern, lowered):
            found.append(region)
    return normalize_unique(found)


def is_exclude_intent(value: str) -> bool:
    return any(marker in value for marker in EXCLUDE_INTENT_MARKERS)


def is_research_intent(value: str) -> bool:
    return any(marker in f" {value}" for marker in OBSERVE_INTENT_MARKERS)


def competitor_match(term: str, competitors: list[str]) -> str:
    lowered = f" {term.lower()} "
    for competitor in sorted(competitors, key=lambda item: (-len(item), item)):
        if not competitor:
            continue
        pattern = rf"(?<![a-z0-9]){re.escape(competitor.lower())}(?![a-z0-9])"
        if re.search(pattern, lowered):
            return competitor
    return ""


def meaningful_tokens(value: str) -> set[str]:
    stop = {"and", "for", "near", "online", "services", "service", "support", "therapy", "the", "with"}
    return {token for token in re.split(r"\W+", value.lower()) if len(token) > 2 and token not in stop}


def numeric_value(value: object) -> float:
    text = str(value or "").replace(",", "").replace("%", "").strip()
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().strip('"').lower())


def normalize_unique(values: Iterable[str]) -> list[str]:
    output = []
    seen = set()
    for value in values:
        text = normalize_text(str(value))
        if text and text not in seen:
            output.append(text)
            seen.add(text)
    return output


def region_name(value: str) -> str:
    text = str(value or "").split("|", 1)[0]
    text = re.sub(r"\([^)]*\)", "", text)
    parts = [part.strip() for part in text.split(",") if part.strip()]
    if parts:
        return parts[0]
    return text.strip()


def title_case(value: str) -> str:
    return " ".join(part.capitalize() for part in value.split())


def display_region(value: str) -> str:
    if normalize_text(value) == "ontario":
        return "Ontario (province-wide)"
    return title_case(value)


def category_order(category: str) -> int:
    order = {
        "focus_candidate": 0,
        "unknown_region_confirmation": 1,
        "exclude_recommendation": 2,
        "unclear_intent_review": 3,
        "covered_service_observation": 4,
        "keep_observe": 5,
    }
    return order.get(category, 99)
