"""Deterministic Search asset planning for Google Ads Editor staging."""

from __future__ import annotations

import csv
import json
import re
import shutil
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol


SITELINK_TEXT_LIMIT = 25
SITELINK_DESCRIPTION_LIMIT = 35
SITELINK_MIN_TO_STAGE = 2
SITELINK_TARGET_MAX = 6
CALLOUT_TEXT_LIMIT = 25
STRUCTURED_SNIPPET_VALUE_LIMIT = 25
STRUCTURED_SNIPPET_MIN_VALUES = 3
STRUCTURED_SNIPPET_MAX_VALUES = 10
PRICE_MIN_ITEMS = 3
PRICE_TEXT_LIMIT = 25
PROMOTION_TARGET_LIMIT = 20
BUSINESS_NAME_LIMIT = 25
IMAGE_MIN_WIDTH = 300
IMAGE_MIN_HEIGHT = 300
LOGO_MIN_WIDTH = 128
LOGO_MIN_HEIGHT = 128

GENERIC_SITELINK_LABELS = {
    "about",
    "about us",
    "contact",
    "contact us",
    "home",
    "learn more",
    "services",
    "our services",
    "locations",
    "pricing",
}

GOOGLE_SOURCE_URLS = {
    "account_limits": "https://support.google.com/google-ads/answer/6372658?hl=en",
    "sitelink": "https://support.google.com/google-ads/answer/2375416?hl=en",
    "callout": "https://support.google.com/google-ads/answer/6079510?hl=en",
    "structured_snippet": "https://support.google.com/google-ads/answer/6280012?hl=en",
    "price": "https://support.google.com/google-ads/answer/7065415?hl=en",
    "promotion": "https://support.google.com/google-ads/answer/7367521?hl=en",
    "image": "https://support.google.com/google-ads/answer/9566341?hl=en",
    "business_information": "https://support.google.com/google-ads/answer/12497613?hl=en-GB",
    "business_information_requirements": "https://support.google.com/adspolicy/answer/12499303?hl=en",
    "location": "https://support.google.com/google-ads/answer/2404182?hl=en",
}

APPROVED_STRUCTURED_SNIPPET_HEADERS = {
    "Amenities",
    "Brands",
    "Courses",
    "Degree programs",
    "Destinations",
    "Featured hotels",
    "Insurance coverage",
    "Models",
    "Neighborhoods",
    "Services",
    "Shows",
    "Styles",
    "Types",
}


class SearchAdGroup(Protocol):
    name: str
    final_url: str
    keywords: list[str]
    headlines: list[str]
    descriptions: list[str]


@dataclass
class SitelinkAssetPlan:
    campaign: str
    ad_group: str
    link_text: str
    final_url: str
    description_1: str
    description_2: str
    source_url: str
    evidence_type: str = "landing_page"
    level: str = "ad_group"
    status: str = "Paused"


@dataclass
class CalloutAssetPlan:
    campaign: str
    callout_text: str
    source_url: str = ""
    evidence_type: str = "campaign_value"
    level: str = "campaign"
    ad_group: str = ""
    status: str = "Paused"


@dataclass
class StructuredSnippetAssetPlan:
    campaign: str
    header: str
    values: list[str]
    source_url: str = ""
    evidence_type: str = "service_catalog"
    level: str = "campaign"
    ad_group: str = ""
    status: str = "Paused"


@dataclass
class CallAssetPlan:
    campaign: str
    phone_number: str
    source_url: str
    country_code: str = "US"
    evidence_type: str = "website_phone"
    level: str = "campaign"
    ad_group: str = ""
    status: str = "Paused"


@dataclass
class PriceAssetPlan:
    campaign: str
    header: str
    description: str
    price: str
    final_url: str
    source_url: str
    currency: str = "USD"
    price_type: str = "Services"
    price_qualifier: str = "From"
    unit: str = "None"
    level: str = "campaign"
    ad_group: str = ""
    status: str = "Paused"


@dataclass
class PromotionAssetPlan:
    campaign: str
    promotion_target: str
    final_url: str
    source_url: str
    promotion_text: str
    percent_off: str = ""
    money_amount_off: str = ""
    promotion_code: str = ""
    level: str = "campaign"
    ad_group: str = ""
    status: str = "Paused"


@dataclass
class BusinessNameAssetPlan:
    campaign: str
    business_name: str
    source_url: str
    level: str = "campaign"
    ad_group: str = ""
    status: str = "Paused"


@dataclass
class AssetCandidate:
    asset_type: str
    value: str
    source_url: str
    evidence_type: str
    status: str
    reason: str
    local_path: str = ""


@dataclass
class AssetEligibilityDecision:
    campaign: str
    ad_group: str
    asset_type: str
    qualified: bool
    reason: str


@dataclass
class SearchAssetPlan:
    sitelinks: list[SitelinkAssetPlan] = field(default_factory=list)
    callouts: list[CalloutAssetPlan] = field(default_factory=list)
    structured_snippets: list[StructuredSnippetAssetPlan] = field(default_factory=list)
    calls: list[CallAssetPlan] = field(default_factory=list)
    prices: list[PriceAssetPlan] = field(default_factory=list)
    promotions: list[PromotionAssetPlan] = field(default_factory=list)
    business_names: list[BusinessNameAssetPlan] = field(default_factory=list)
    candidate_assets: list[AssetCandidate] = field(default_factory=list)
    skipped_assets: list[AssetEligibilityDecision] = field(default_factory=list)
    eligibility: list[AssetEligibilityDecision] = field(default_factory=list)
    future_opportunities: list[str] = field(default_factory=list)
    evidence: dict[str, object] = field(default_factory=dict)
    official_rules: dict[str, object] = field(default_factory=dict)
    human_review_required: list[str] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        return {
            "sitelinks": len(self.sitelinks),
            "callouts": len(self.callouts),
            "structured_snippets": len(self.structured_snippets),
            "calls": len(self.calls),
            "prices": len(self.prices),
            "promotions": len(self.promotions),
            "business_names": len(self.business_names),
            "candidate_assets": len(self.candidate_assets),
            "skipped": len(self.skipped_assets),
        }

    def generated_assets(self) -> dict[str, object]:
        return {
            "sitelinks": [asdict(value) for value in self.sitelinks],
            "callouts": [asdict(value) for value in self.callouts],
            "structured_snippets": [asdict(value) for value in self.structured_snippets],
            "calls": [asdict(value) for value in self.calls],
            "prices": [asdict(value) for value in self.prices],
            "promotions": [asdict(value) for value in self.promotions],
            "business_names": [asdict(value) for value in self.business_names],
        }

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["generated_assets"] = self.generated_assets()
        payload["counts"] = self.counts()
        return payload


def build_asset_research_matrix() -> list[dict[str, object]]:
    return [
        {
            "asset_type": "sitelink",
            "official_source": GOOGLE_SOURCE_URLS["sitelink"],
            "limits": {"link_text": 25, "description_line": 35, "preferred_count": 6, "minimum_to_show": 2},
            "editor_fields": ["Campaign", "Ad Group", "Link text", "Final URL", "Description line 1", "Description line 2"],
            "generation_rule": "Use user-intent labels, never bare sitemap labels. Require distinct final URLs and both description lines.",
        },
        {
            "asset_type": "callout",
            "official_source": GOOGLE_SOURCE_URLS["callout"],
            "limits": {"text": 25},
            "editor_fields": ["Campaign", "Ad Group", "Callout text"],
            "generation_rule": "Use confirmed value props that apply at the selected account branch.",
        },
        {
            "asset_type": "structured_snippet",
            "official_source": GOOGLE_SOURCE_URLS["structured_snippet"],
            "limits": {"values_min": 3, "values_max": 10, "value": 25},
            "editor_fields": ["Campaign", "Structured snippet header", "Structured snippet values"],
            "generation_rule": "Use approved headers. Prefer Services and service-area lists when evidence supports them.",
        },
        {
            "asset_type": "call",
            "official_source": "https://support.google.com/google-ads/answer/2454052?hl=en",
            "limits": {"phone_number": "must match website or client evidence"},
            "editor_fields": ["Campaign", "Phone number", "Country code"],
            "generation_rule": "Generate only when website evidence has one confirmed phone number.",
        },
        {
            "asset_type": "price",
            "official_source": GOOGLE_SOURCE_URLS["price"],
            "limits": {"items_min": 3, "header": 25, "description": 25},
            "editor_fields": ["Campaign", "Price type", "Price qualifier", "Currency", "Price header", "Price amount", "Final URL"],
            "generation_rule": "Generate only from explicit website prices. Skip if fewer than 3 price points are visible.",
        },
        {
            "asset_type": "promotion",
            "official_source": GOOGLE_SOURCE_URLS["promotion"],
            "limits": {"promotion_target": 20},
            "editor_fields": ["Campaign", "Promotion target", "Percent off", "Money amount off", "Promotion code", "Final URL"],
            "generation_rule": "Generate only when explicit promotion or sale evidence exists.",
        },
        {
            "asset_type": "image",
            "official_source": GOOGLE_SOURCE_URLS["image"],
            "limits": {"minimum_local_manifest_check": "300x300 with known file path"},
            "editor_fields": ["manifest only until Editor import/export is verified"],
            "generation_rule": "Copy only local image files with basic dimension evidence into the review import package.",
        },
        {
            "asset_type": "business_logo",
            "official_source": GOOGLE_SOURCE_URLS["business_information_requirements"],
            "limits": {"minimum_local_manifest_check": "128x128 with logo evidence"},
            "editor_fields": ["manifest only until Editor import/export is verified"],
            "generation_rule": "Require website logo evidence and flag approval depends on advertiser verification.",
        },
        {
            "asset_type": "business_name",
            "official_source": GOOGLE_SOURCE_URLS["business_information"],
            "limits": {"business_name": 25},
            "editor_fields": ["Campaign", "Business name"],
            "generation_rule": "Generate when inferred name fits limits. Human review must confirm legal or domain match.",
        },
        {
            "asset_type": "location",
            "official_source": GOOGLE_SOURCE_URLS["location"],
            "limits": {"gbp_link_required": True},
            "editor_fields": ["review task only"],
            "generation_rule": "Do not fake location assets. Create GBP linking review task when not confirmed.",
        },
    ]


def clean_asset_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9 &/.$%-]+", " ", value)).strip()


def fit_asset_text(value: str, limit: int) -> str:
    text = clean_asset_text(value)
    if len(text) <= limit:
        return text
    return text[:limit].rstrip(" ./-&")


def service_from_ad_group(ad_group_name: str) -> str:
    if " - " in ad_group_name:
        return ad_group_name.split(" - ", 1)[1].strip()
    return ad_group_name.strip()


def url_signature(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def normalize_url_for_compare(url: str) -> str:
    return url_signature(url).lower()


def unique_texts(values: list[str], limit: int, *, char_limit: int) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = fit_asset_text(value, char_limit)
        key = text.lower()
        if text and key not in seen:
            output.append(text)
            seen.add(key)
        if len(output) >= limit:
            break
    return output


def asset_evidence(website_scan: dict[str, object]) -> dict[str, list[dict[str, str]]]:
    facts = website_scan.get("extracted_facts", {})
    if isinstance(facts, dict):
        evidence = facts.get("asset_evidence", {})
        if isinstance(evidence, dict):
            return {key: value for key, value in evidence.items() if isinstance(value, list)}
    return {}


def first_source(items: list[dict[str, str]]) -> str:
    return items[0].get("source", "") if items else ""


def local_file_from_url(url: str) -> Path | None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme == "file":
        return Path(urllib.request.url2pathname(parsed.path))
    return None


def image_dimensions(candidate: dict[str, str]) -> tuple[int, int]:
    try:
        return int(candidate.get("width", "") or 0), int(candidate.get("height", "") or 0)
    except ValueError:
        return 0, 0


def is_allowed_media_file(path: Path) -> bool:
    return path.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}


def user_intent_sitelink_text(url: str, fallback: str) -> str:
    parsed = urllib.parse.urlparse(url)
    slug = parsed.path.rstrip("/").split("/")[-1]
    words = [word for word in re.split(r"[-_]+", slug) if word and not word.isdigit()]
    label = " ".join(word.title() for word in words) if words else fallback
    generic_key = label.lower().strip()
    if generic_key in GENERIC_SITELINK_LABELS:
        if "contact" in generic_key:
            label = "Speak To A Specialist"
        elif "pricing" in generic_key:
            label = "Compare Service Costs"
        elif "location" in generic_key:
            label = "Find Local Support"
        elif "about" in generic_key:
            label = "Meet The Care Team"
        else:
            label = f"Explore {fallback}"
    return fit_asset_text(label or fallback, SITELINK_TEXT_LIMIT)


class SearchAssetGenerator:
    """Plan staged Search assets from existing rebuild artifacts."""

    def generate(
        self,
        *,
        campaign: str,
        ad_groups: list[SearchAdGroup],
        service_catalog: dict[str, object],
        source_pages: list[str],
        website: str,
        website_scan: dict[str, object],
    ) -> SearchAssetPlan:
        plan = SearchAssetPlan(official_rules={"sources": GOOGLE_SOURCE_URLS, "matrix": build_asset_research_matrix()})
        evidence = asset_evidence(website_scan)
        plan.evidence = evidence
        source_urls = self._candidate_urls(source_pages, ad_groups, website)

        for ad_group in ad_groups:
            ad_group_campaign = str(getattr(ad_group, "campaign", campaign))
            sitelinks = self._plan_sitelinks_for_ad_group(
                campaign=ad_group_campaign,
                ad_group=ad_group,
                source_urls=source_urls,
                website=website,
            )
            if sitelinks:
                plan.sitelinks.extend(sitelinks)
                self._qualify(plan, ad_group_campaign, ad_group.name, "sitelink", "qualified_non_homepage_landing_page")
            else:
                self._skip(plan, ad_group_campaign, ad_group.name, "sitelink", "insufficient_distinct_urls")

        callouts = self._plan_campaign_callouts(campaign, website_scan, evidence)
        plan.callouts.extend(callouts)
        self._record_bool(plan, campaign, "", "callout", bool(callouts), "campaign_level_value_assets", "no_confirmed_callouts")

        snippets = self._plan_structured_snippets(campaign, service_catalog, evidence)
        plan.structured_snippets.extend(snippets)
        self._record_bool(plan, campaign, "", "structured_snippet", bool(snippets), "catalog_or_service_area_values", "insufficient_structured_snippet_values")

        calls = self._plan_calls(campaign, evidence)
        plan.calls.extend(calls)
        self._record_bool(plan, campaign, "", "call", bool(calls), "confirmed_matching_phone_number", "no_confirmed_phone_number")

        prices = self._plan_prices(campaign, evidence, website)
        plan.prices.extend(prices)
        self._record_bool(plan, campaign, "", "price", bool(prices), "explicit_website_pricing", "insufficient_explicit_pricing")

        promotions = self._plan_promotions(campaign, evidence, website)
        plan.promotions.extend(promotions)
        self._record_bool(plan, campaign, "", "promotion", bool(promotions), "explicit_website_promotion", "no_explicit_promotion")

        business_names = self._plan_business_names(campaign, evidence, website_scan, website)
        plan.business_names.extend(business_names)
        self._record_bool(plan, campaign, "", "business_name", bool(business_names), "business_name_fits_review_gate", "business_name_needs_verification")

        self._plan_media_candidates(plan, evidence)
        self._plan_location_review(plan, campaign, evidence)
        return plan

    def _qualify(self, plan: SearchAssetPlan, campaign: str, ad_group: str, asset_type: str, reason: str) -> None:
        plan.eligibility.append(AssetEligibilityDecision(campaign, ad_group, asset_type, True, reason))

    def _skip(self, plan: SearchAssetPlan, campaign: str, ad_group: str, asset_type: str, reason: str) -> None:
        decision = AssetEligibilityDecision(campaign, ad_group, asset_type, False, reason)
        plan.eligibility.append(decision)
        plan.skipped_assets.append(decision)

    def _record_bool(self, plan: SearchAssetPlan, campaign: str, ad_group: str, asset_type: str, ok: bool, good: str, bad: str) -> None:
        if ok:
            self._qualify(plan, campaign, ad_group, asset_type, good)
        else:
            self._skip(plan, campaign, ad_group, asset_type, bad)

    def _candidate_urls(self, source_pages: list[str], ad_groups: list[SearchAdGroup], website: str) -> list[str]:
        values = [website, *source_pages, *(ad_group.final_url for ad_group in ad_groups)]
        output: list[str] = []
        seen: set[str] = set()
        for value in values:
            if not value:
                continue
            key = normalize_url_for_compare(value)
            if key not in seen:
                output.append(value)
                seen.add(key)
        return output

    def _plan_sitelinks_for_ad_group(self, *, campaign: str, ad_group: SearchAdGroup, source_urls: list[str], website: str) -> list[SitelinkAssetPlan]:
        if not ad_group.final_url or normalize_url_for_compare(ad_group.final_url) == normalize_url_for_compare(website):
            return []

        service = service_from_ad_group(ad_group.name)
        candidates = [url for url in source_urls if normalize_url_for_compare(url) != normalize_url_for_compare(website)]
        if normalize_url_for_compare(ad_group.final_url) not in {normalize_url_for_compare(url) for url in candidates}:
            candidates.insert(0, ad_group.final_url)

        sitelinks: list[SitelinkAssetPlan] = []
        seen_texts: set[str] = set()
        for url in candidates:
            text = user_intent_sitelink_text(url, service)
            if text.lower() in seen_texts or text.lower() in GENERIC_SITELINK_LABELS:
                continue
            sitelinks.append(
                SitelinkAssetPlan(
                    campaign=campaign,
                    ad_group=ad_group.name,
                    link_text=text,
                    final_url=url,
                    source_url=url,
                    description_1=fit_asset_text(f"Review {text} options", SITELINK_DESCRIPTION_LIMIT),
                    description_2=fit_asset_text("Confirm fit before launch", SITELINK_DESCRIPTION_LIMIT),
                )
            )
            seen_texts.add(text.lower())
            if len(sitelinks) >= SITELINK_TARGET_MAX:
                break

        return sitelinks if len(sitelinks) >= SITELINK_MIN_TO_STAGE else []

    def _plan_campaign_callouts(self, campaign: str, website_scan: dict[str, object], evidence: dict[str, list[dict[str, str]]]) -> list[CalloutAssetPlan]:
        facts = website_scan.get("extracted_facts", {})
        seeds = ["Review Before Launch", "Google Search Only", "Paused For Review", "Service Fit Review"]
        if isinstance(facts, dict):
            for key in ("billing", "consultation"):
                value = str(facts.get(key, "")).strip()
                if value:
                    seeds.append(value)
        if evidence.get("phone_numbers"):
            seeds.append("Phone Consult Available")
        if evidence.get("pricing"):
            seeds.append("Transparent Pricing")
        values = unique_texts(seeds, 10, char_limit=CALLOUT_TEXT_LIMIT)
        return [CalloutAssetPlan(campaign=campaign, callout_text=value, source_url=first_source(evidence.get("phone_numbers", []))) for value in values]

    def _plan_structured_snippets(self, campaign: str, service_catalog: dict[str, object], evidence: dict[str, list[dict[str, str]]]) -> list[StructuredSnippetAssetPlan]:
        snippets: list[StructuredSnippetAssetPlan] = []
        raw_values = service_catalog.get("active_services_for_staging", [])
        if isinstance(raw_values, list):
            values = unique_texts([str(value) for value in raw_values], STRUCTURED_SNIPPET_MAX_VALUES, char_limit=STRUCTURED_SNIPPET_VALUE_LIMIT)
            if len(values) >= STRUCTURED_SNIPPET_MIN_VALUES:
                snippets.append(StructuredSnippetAssetPlan(campaign=campaign, header="Services", values=values, source_url=first_source(evidence.get("business_names", []))))
        area_values = unique_texts([item.get("value", "") for item in evidence.get("service_areas", [])], STRUCTURED_SNIPPET_MAX_VALUES, char_limit=STRUCTURED_SNIPPET_VALUE_LIMIT)
        if len(area_values) >= STRUCTURED_SNIPPET_MIN_VALUES:
            snippets.append(StructuredSnippetAssetPlan(campaign=campaign, header="Neighborhoods", values=area_values, source_url=first_source(evidence.get("service_areas", [])), evidence_type="service_area"))
        return snippets

    def _plan_calls(self, campaign: str, evidence: dict[str, list[dict[str, str]]]) -> list[CallAssetPlan]:
        phones = evidence.get("phone_numbers", [])
        values = {item.get("value", "") for item in phones if item.get("value", "")}
        if len(values) != 1:
            return []
        value = next(iter(values))
        return [CallAssetPlan(campaign=campaign, phone_number=value, source_url=first_source(phones))]

    def _plan_prices(self, campaign: str, evidence: dict[str, list[dict[str, str]]], website: str) -> list[PriceAssetPlan]:
        prices = evidence.get("pricing", [])
        if len(prices) < PRICE_MIN_ITEMS:
            return []
        output: list[PriceAssetPlan] = []
        for index, item in enumerate(prices[:8], start=1):
            output.append(
                PriceAssetPlan(
                    campaign=campaign,
                    header=fit_asset_text(f"Service {index}", PRICE_TEXT_LIMIT),
                    description=fit_asset_text("Website listed price", PRICE_TEXT_LIMIT),
                    price=item.get("value", ""),
                    final_url=item.get("source", "") or website,
                    source_url=item.get("source", "") or website,
                )
            )
        return output

    def _plan_promotions(self, campaign: str, evidence: dict[str, list[dict[str, str]]], website: str) -> list[PromotionAssetPlan]:
        promotions = evidence.get("promotions", [])
        if not promotions:
            return []
        selected: tuple[dict[str, str], str, str, str] | None = None
        for item in promotions:
            evidence_text = item.get("evidence", "")
            money = ""
            percent = ""
            if "$" in evidence_text:
                match = re.search(r"\$\s?\d+(?:\.\d{2})?", evidence_text)
                money = match.group(0).replace(" ", "") if match else ""
            match = re.search(r"\d{1,2}\s?%", evidence_text)
            if match:
                percent = match.group(0).replace(" ", "")
            code_match = re.search(r"\b(?:promo\s+code|code)\s+([A-Z0-9-]{3,20})\b", evidence_text, re.IGNORECASE)
            promotion_code = code_match.group(1).upper() if code_match else ""
            if money or percent or promotion_code:
                selected = (item, money, percent, promotion_code)
                break
        if not selected:
            return []
        item, money, percent, promotion_code = selected
        text = item.get("value", "Promotion")
        return [
            PromotionAssetPlan(
                campaign=campaign,
                promotion_target=fit_asset_text(text.title(), PROMOTION_TARGET_LIMIT),
                final_url=item.get("source", "") or website,
                source_url=item.get("source", "") or website,
                promotion_text=item.get("evidence", "")[:160],
                money_amount_off=money,
                percent_off=percent,
                promotion_code=promotion_code,
            )
        ]

    def _plan_business_names(self, campaign: str, evidence: dict[str, list[dict[str, str]]], website_scan: dict[str, object], website: str) -> list[BusinessNameAssetPlan]:
        names = evidence.get("business_names", [])
        value = names[0].get("value", "") if names else str(website_scan.get("website", ""))
        value = value.split("|")[0].strip()
        value = fit_asset_text(value, BUSINESS_NAME_LIMIT)
        if not value:
            return []
        return [BusinessNameAssetPlan(campaign=campaign, business_name=value, source_url=first_source(names) or website)]

    def _plan_media_candidates(self, plan: SearchAssetPlan, evidence: dict[str, list[dict[str, str]]]) -> None:
        for asset_type, candidates, min_width, min_height in (
            ("image", evidence.get("image_candidates", []), IMAGE_MIN_WIDTH, IMAGE_MIN_HEIGHT),
            ("business_logo", evidence.get("logo_candidates", []), LOGO_MIN_WIDTH, LOGO_MIN_HEIGHT),
        ):
            if not candidates:
                plan.human_review_required.append(f"{asset_type}: no website candidate found")
                self._skip(plan, "", "", asset_type, "no_candidate_found")
                continue
            for candidate in candidates:
                width, height = image_dimensions(candidate)
                path = local_file_from_url(candidate.get("url", ""))
                if not path or not path.exists() or not is_allowed_media_file(path):
                    plan.candidate_assets.append(AssetCandidate(asset_type, candidate.get("url", ""), candidate.get("source", ""), candidate.get("evidence_type", asset_type), "needs_review", "remote_or_missing_file"))
                    continue
                if path.suffix.lower() != ".svg" and (width < min_width or height < min_height):
                    plan.candidate_assets.append(AssetCandidate(asset_type, candidate.get("url", ""), candidate.get("source", ""), candidate.get("evidence_type", asset_type), "rejected", "missing_or_small_dimensions"))
                    continue
                plan.candidate_assets.append(AssetCandidate(asset_type, candidate.get("url", ""), candidate.get("source", ""), candidate.get("evidence_type", asset_type), "ready_for_import_package", "passed_local_manifest_checks"))
        plan.human_review_required.append("image_and_logo_assets_require_google_ads_editor_import_export_verification")

    def _plan_location_review(self, plan: SearchAssetPlan, campaign: str, evidence: dict[str, list[dict[str, str]]]) -> None:
        if evidence.get("gbp_mentions"):
            self._qualify(plan, campaign, "", "location", "possible_gbp_or_maps_evidence_review_required")
            plan.human_review_required.append("confirm_google_business_profile_linked_before_location_assets")
        else:
            self._skip(plan, campaign, "", "location", "gbp_linking_required")
            plan.human_review_required.append("gbp_linking_required")


def write_asset_research_artifacts(build_dir: Path) -> dict[str, Path]:
    matrix = build_asset_research_matrix()
    json_path = build_dir / "ad_asset_research_matrix.json"
    md_path = build_dir / "ad_asset_research_matrix.md"
    json_path.write_text(json.dumps({"sources": GOOGLE_SOURCE_URLS, "matrix": matrix}, indent=2) + "\n", encoding="utf-8")
    lines = ["# Search Asset Research Matrix", ""]
    for row in matrix:
        lines.extend(
            [
                f"## {row['asset_type']}",
                "",
                f"- Source: {row['official_source']}",
                f"- Limits: `{json.dumps(row['limits'], sort_keys=True)}`",
                f"- Editor fields: `{', '.join(row['editor_fields'])}`",
                f"- Generation rule: {row['generation_rule']}",
                "",
            ]
        )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {"ad_asset_research_matrix_json": json_path, "ad_asset_research_matrix_md": md_path}


def write_media_import_package(build_dir: Path, plan: SearchAssetPlan) -> dict[str, Path]:
    package_dir = build_dir / "ad_asset_import_package"
    package_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = build_dir / "image_asset_manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["asset_type", "source_url", "local_path", "status", "reason", "evidence_type"])
        writer.writeheader()
        for candidate in plan.candidate_assets:
            local_path = ""
            if candidate.status == "ready_for_import_package":
                source_path = local_file_from_url(candidate.value)
                if source_path:
                    target = package_dir / f"{candidate.asset_type}_{source_path.name}"
                    shutil.copy2(source_path, target)
                    local_path = str(target)
                    candidate.local_path = local_path
            writer.writerow(
                {
                    "asset_type": candidate.asset_type,
                    "source_url": candidate.value,
                    "local_path": local_path,
                    "status": candidate.status,
                    "reason": candidate.reason,
                    "evidence_type": candidate.evidence_type,
                }
            )
    return {"ad_asset_import_package": package_dir, "image_asset_manifest": manifest_path}


def write_asset_artifacts(build_dir: Path, plan: SearchAssetPlan) -> dict[str, Path]:
    matrix_paths = write_asset_research_artifacts(build_dir)
    media_paths = write_media_import_package(build_dir, plan)
    json_path = build_dir / "ad_asset_plan.json"
    matrix_path = build_dir / "ad_asset_matrix.csv"
    json_path.write_text(json.dumps(plan.to_dict(), indent=2) + "\n", encoding="utf-8")

    with matrix_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "asset_type",
                "level",
                "campaign",
                "ad_group",
                "source_url",
                "evidence_type",
                "text",
                "final_url",
                "description_1",
                "description_2",
                "header",
                "values",
                "status",
                "skip_reason",
                "google_source_url",
            ],
        )
        writer.writeheader()
        for sitelink in plan.sitelinks:
            writer.writerow({"asset_type": "sitelink", "level": sitelink.level, "campaign": sitelink.campaign, "ad_group": sitelink.ad_group, "source_url": sitelink.source_url, "evidence_type": sitelink.evidence_type, "text": sitelink.link_text, "final_url": sitelink.final_url, "description_1": sitelink.description_1, "description_2": sitelink.description_2, "status": sitelink.status, "google_source_url": GOOGLE_SOURCE_URLS["sitelink"]})
        for callout in plan.callouts:
            writer.writerow({"asset_type": "callout", "level": callout.level, "campaign": callout.campaign, "ad_group": callout.ad_group, "source_url": callout.source_url, "evidence_type": callout.evidence_type, "text": callout.callout_text, "status": callout.status, "google_source_url": GOOGLE_SOURCE_URLS["callout"]})
        for snippet in plan.structured_snippets:
            writer.writerow({"asset_type": "structured_snippet", "level": snippet.level, "campaign": snippet.campaign, "ad_group": snippet.ad_group, "source_url": snippet.source_url, "evidence_type": snippet.evidence_type, "header": snippet.header, "values": ";".join(snippet.values), "status": snippet.status, "google_source_url": GOOGLE_SOURCE_URLS["structured_snippet"]})
        for call in plan.calls:
            writer.writerow({"asset_type": "call", "level": call.level, "campaign": call.campaign, "ad_group": call.ad_group, "source_url": call.source_url, "evidence_type": call.evidence_type, "text": call.phone_number, "status": call.status})
        for price in plan.prices:
            writer.writerow({"asset_type": "price", "level": price.level, "campaign": price.campaign, "ad_group": price.ad_group, "source_url": price.source_url, "evidence_type": "website_pricing", "text": f"{price.header}: {price.price}", "final_url": price.final_url, "description_1": price.description, "status": price.status, "google_source_url": GOOGLE_SOURCE_URLS["price"]})
        for promotion in plan.promotions:
            writer.writerow({"asset_type": "promotion", "level": promotion.level, "campaign": promotion.campaign, "ad_group": promotion.ad_group, "source_url": promotion.source_url, "evidence_type": "website_promotion", "text": promotion.promotion_target, "final_url": promotion.final_url, "description_1": promotion.promotion_text[:35], "status": promotion.status, "google_source_url": GOOGLE_SOURCE_URLS["promotion"]})
        for business_name in plan.business_names:
            writer.writerow({"asset_type": "business_name", "level": business_name.level, "campaign": business_name.campaign, "source_url": business_name.source_url, "evidence_type": "business_name", "text": business_name.business_name, "status": business_name.status, "google_source_url": GOOGLE_SOURCE_URLS["business_information"]})
        for skipped in plan.skipped_assets:
            writer.writerow({"asset_type": skipped.asset_type, "level": "", "campaign": skipped.campaign, "ad_group": skipped.ad_group, "status": "skipped", "skip_reason": skipped.reason})

    return {"ad_asset_plan": json_path, "ad_asset_matrix": matrix_path, **matrix_paths, **media_paths}
