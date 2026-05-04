"""Google Ads Editor exporter for the active Search staging workflow.

This module keeps the older exporter import path available, but narrows active
behavior to Search staging files that can be validated by
``shared.rebuild.staging_validator``. PMAX and API upload remain salvage-only
until they get a separate activation phase.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from shared.gads.core.search_campaigns.search_csv_generator import SearchCSVGenerator
from shared.rebuild.staging_validator import validate_file


class CampaignType(Enum):
    """Campaign types known to the salvage exporter."""

    SEARCH = "Search"
    PERFORMANCE_MAX = "Performance Max"
    DISPLAY = "Display Network only"
    SHOPPING = "Shopping"
    VIDEO = "Video"
    DISCOVERY = "Discovery"


class BidStrategyType(Enum):
    """Bid strategy names preserved for compatibility with old imports."""

    MANUAL_CPC = "Manual CPC"
    MAXIMIZE_CLICKS = "Maximize clicks"
    MAXIMIZE_CONVERSIONS = "Maximize conversions"
    MAXIMIZE_CONVERSION_VALUE = "Maximize conversion value"
    TARGET_CPA = "Target CPA"
    TARGET_ROAS = "Target ROAS"


@dataclass
class CampaignData:
    """Minimal campaign data for Search staging export."""

    campaign: str
    budget: float = 0.0
    campaign_type: CampaignType = CampaignType.SEARCH
    networks: str = "Google search"
    budget_type: str = "Daily"
    eu_political_ads: str = "No"
    broad_match_keywords: str = "Off"
    campaign_status: str = "Paused"


@dataclass
class AdGroupData:
    """Minimal ad group data for Search staging export."""

    ad_group: str
    ad_group_status: str = "Paused"


@dataclass
class KeywordData:
    """Minimal keyword data for Search staging export."""

    keyword: str
    criterion_type: str = "Phrase"
    final_url: str = ""
    status: str = "Paused"


@dataclass
class ResponsiveSearchAdData:
    """RSA data required by the active Search staging validator."""

    final_url: str
    headlines: list[str] = field(default_factory=list)
    descriptions: list[str] = field(default_factory=list)
    path_1: str = ""
    path_2: str = ""
    status: str = "Paused"


@dataclass
class AssetGroupData:
    """Compatibility container for PMAX salvage imports."""

    asset_group: str
    headlines: list[str] = field(default_factory=list)
    descriptions: list[str] = field(default_factory=list)
    final_url: str = ""
    asset_group_status: str = "Paused"


@dataclass
class ExtensionData:
    """Compatibility container for extension salvage imports."""

    link_text: str = ""
    description_line_1: str = ""
    description_line_2: str = ""
    final_url: str = ""


@dataclass
class GoogleAdsEditorRow:
    """Compatibility row container for older callers."""

    campaign_data: CampaignData
    ad_group_data: AdGroupData | None = None
    keyword_data: KeywordData | None = None
    rsa_data: ResponsiveSearchAdData | None = None
    asset_group_data: AssetGroupData | None = None
    extension_data: ExtensionData | None = None


class GoogleAdsEditorExporter:
    """Export active Search campaigns through the Search staging generator."""

    CSV_HEADERS = SearchCSVGenerator.columns

    def export_campaigns(self, campaigns: list[dict[str, Any]]) -> str:
        """Export Search campaigns to active Google Ads Editor TSV content."""
        generator = SearchCSVGenerator()
        for campaign in campaigns:
            self._add_search_campaign(generator, campaign)
        return generator.to_tsv()

    def export_campaign(self, campaign: dict[str, Any]) -> str:
        """Export one Search campaign to active Google Ads Editor TSV content."""
        return self.export_campaigns([campaign])

    def save_csv(self, csv_content: str, filename: str | Path) -> Path:
        """Save Google Ads Editor staging output as UTF-16 tab-separated text."""
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(csv_content, encoding="utf-16")
        return output_path

    def export_and_validate(self, campaigns: list[dict[str, Any]], output_path: str | Path) -> dict[str, Any]:
        """Export campaigns, save the file, and return the active validation report."""
        csv_content = self.export_campaigns(campaigns)
        path = self.save_csv(csv_content, output_path)
        return validate_file(path)

    def validate_csv_data(self, csv_content: str) -> list[str]:
        """Validate TSV content through the active staging validator."""
        with tempfile.NamedTemporaryFile("w", encoding="utf-16", suffix=".csv", delete=False) as handle:
            handle.write(csv_content)
            temp_path = Path(handle.name)

        try:
            report = validate_file(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)

        return [
            f"{issue.get('severity', 'issue')}: {issue.get('message', '')}"
            for issue in report.get("issues", [])
        ]

    def validate_file(self, csv_path: str | Path) -> dict[str, Any]:
        """Validate an existing staging file through the active validator."""
        return validate_file(Path(csv_path))

    def _add_search_campaign(self, generator: SearchCSVGenerator, campaign: dict[str, Any]) -> None:
        campaign_type = self._campaign_type(campaign)
        if campaign_type != CampaignType.SEARCH:
            raise NotImplementedError(
                "Only Search staging export is active. PMAX, Display, Shopping, Video, "
                "and Discovery remain salvage-only until explicitly activated."
            )

        campaign_data = self._campaign_data(campaign)
        generator.add_campaign(
            campaign_data.campaign,
            campaign_data.budget,
            status=campaign_data.campaign_status,
            networks=campaign_data.networks,
            budget_type=campaign_data.budget_type,
            eu_political_ads=campaign_data.eu_political_ads,
            broad_match_keywords=campaign_data.broad_match_keywords,
        )

        for location in campaign.get("locations", []):
            location_name, location_id, radius, bid_modifier = self._location_parts(location)
            generator.add_location(
                campaign_data.campaign,
                location_name,
                location_id=location_id,
                radius=radius,
                bid_modifier=bid_modifier,
            )

        for ad_group in campaign.get("ad_groups", []):
            self._add_ad_group(generator, campaign_data.campaign, campaign, ad_group)

    def _add_ad_group(
        self,
        generator: SearchCSVGenerator,
        campaign_name: str,
        campaign: dict[str, Any],
        ad_group: dict[str, Any],
    ) -> None:
        ad_group_data = self._ad_group_data(ad_group)
        generator.add_ad_group(
            campaign_name,
            ad_group_data.ad_group,
            status=ad_group_data.ad_group_status,
        )

        default_final_url = str(ad_group.get("final_url") or campaign.get("final_url") or "")
        for keyword in ad_group.get("keywords", []):
            keyword_data = self._keyword_data(keyword, default_final_url)
            generator.add_keyword(
                campaign_name,
                ad_group_data.ad_group,
                keyword_data.keyword,
                final_url=keyword_data.final_url,
                criterion_type=keyword_data.criterion_type,
                status=keyword_data.status,
            )

        for rsa in self._rsa_items(ad_group):
            rsa_data = self._rsa_data(rsa, default_final_url)
            generator.add_rsa(
                campaign_name,
                ad_group_data.ad_group,
                rsa_data.final_url,
                headlines=rsa_data.headlines,
                descriptions=rsa_data.descriptions,
                path_1=rsa_data.path_1,
                path_2=rsa_data.path_2,
                status=rsa_data.status,
            )

    def _campaign_type(self, campaign: dict[str, Any]) -> CampaignType:
        raw_type = str(campaign.get("type") or campaign.get("campaign_type") or CampaignType.SEARCH.value)
        try:
            return CampaignType(raw_type)
        except ValueError as exc:
            raise ValueError(f"Unsupported campaign type: {raw_type}") from exc

    def _campaign_data(self, campaign: dict[str, Any]) -> CampaignData:
        name = str(campaign.get("name") or campaign.get("campaign") or "").strip()
        if not name:
            raise ValueError("Campaign name is required.")
        return CampaignData(
            campaign=name,
            budget=float(str(campaign.get("budget", 0)).replace(",", "")),
            campaign_type=self._campaign_type(campaign),
            networks=str(campaign.get("networks", "Google search")),
            budget_type=str(campaign.get("budget_type", "Daily")),
            eu_political_ads=str(campaign.get("eu_political_ads", "No")),
            broad_match_keywords=str(campaign.get("broad_match_keywords", "Off")),
            campaign_status=str(campaign.get("status", "Paused")),
        )

    def _ad_group_data(self, ad_group: dict[str, Any]) -> AdGroupData:
        name = str(ad_group.get("name") or ad_group.get("ad_group") or "").strip()
        if not name:
            raise ValueError("Ad group name is required.")
        return AdGroupData(ad_group=name, ad_group_status=str(ad_group.get("status", "Paused")))

    def _keyword_data(self, keyword: str | dict[str, Any], default_final_url: str) -> KeywordData:
        if isinstance(keyword, str):
            return KeywordData(keyword=keyword, final_url=default_final_url)

        text = str(keyword.get("text") or keyword.get("keyword") or "").strip()
        if not text:
            raise ValueError("Keyword text is required.")
        return KeywordData(
            keyword=text,
            criterion_type=str(keyword.get("criterion_type", "Phrase")),
            final_url=str(keyword.get("final_url") or default_final_url),
            status=str(keyword.get("status", "Paused")),
        )

    def _rsa_items(self, ad_group: dict[str, Any]) -> list[dict[str, Any]]:
        if "rsa" in ad_group:
            rsa = ad_group["rsa"]
            return rsa if isinstance(rsa, list) else [rsa]
        if "ads" in ad_group:
            return list(ad_group["ads"])
        return []

    def _rsa_data(self, rsa: dict[str, Any], default_final_url: str) -> ResponsiveSearchAdData:
        return ResponsiveSearchAdData(
            final_url=str(rsa.get("final_url") or default_final_url),
            headlines=[str(value) for value in rsa.get("headlines", [])],
            descriptions=[str(value) for value in rsa.get("descriptions", [])],
            path_1=str(rsa.get("path_1", "")),
            path_2=str(rsa.get("path_2", "")),
            status=str(rsa.get("status", "Paused")),
        )

    def _location_parts(self, location: str | dict[str, Any]) -> tuple[str, str, str, str]:
        if isinstance(location, str):
            return location, "", "", ""
        return (
            str(location.get("location") or location.get("name") or ""),
            str(location.get("location_id", "")),
            str(location.get("radius", "")),
            str(location.get("bid_modifier", "")),
        )


def export_campaigns_to_csv(campaigns: list[dict[str, Any]], output_path: str | Path | None = None) -> str:
    """Export Search campaigns to active Google Ads Editor TSV content."""
    exporter = GoogleAdsEditorExporter()
    csv_content = exporter.export_campaigns(campaigns)
    if output_path:
        exporter.save_csv(csv_content, output_path)
    return csv_content


def create_sample_search_campaign() -> dict[str, Any]:
    """Create a generic Search campaign example that validates."""
    return {
        "name": "Search - Services - V1",
        "type": "Search",
        "budget": 100.00,
        "final_url": "https://example.com/services",
        "locations": [{"location": "United States", "location_id": "2840"}],
        "ad_groups": [
            {
                "name": "Core Services",
                "keywords": ["service consultation"],
                "rsa": {
                    "headlines": [
                        "Get Clear Service Support",
                        "Book A Service Consult Today",
                        "Local Service Team Ready Now",
                        "Compare Your Service Options",
                        "Plan Your Next Service Step",
                        "Trusted Service Guidance Now",
                        "Fast Scheduling Support Today",
                        "Helpful Service Answers Today",
                        "Expert Service Support Team",
                        "Simple Online Service Booking",
                        "Focused Support For Goals",
                        "Quality Care Team Support",
                        "Request Service Details Today",
                        "Speak With A Service Team",
                        "Start With A Service Call",
                    ],
                    "descriptions": [
                        "Review service support options with clear local guidance and a focused team. Call Today.",
                        "Compare availability, budget, and service fit before choosing next steps. Book Today.",
                        "Schedule practical service guidance with an experienced team. Schedule Today.",
                        "Request service details, timing, and support options before review. Request Details.",
                    ],
                    "path_1": "services",
                    "path_2": "consult",
                },
            }
        ],
    }


def create_sample_pmax_campaign() -> dict[str, Any]:
    """Create a PMAX salvage example that is not active for export."""
    return {
        "name": "Sample PMAX Campaign",
        "type": "Performance Max",
        "budget": 100.00,
        "asset_groups": [{"name": "Sample Asset Group"}],
    }


__all__ = [
    "GoogleAdsEditorExporter",
    "GoogleAdsEditorRow",
    "CampaignData",
    "AssetGroupData",
    "AdGroupData",
    "KeywordData",
    "ResponsiveSearchAdData",
    "ExtensionData",
    "CampaignType",
    "BidStrategyType",
    "export_campaigns_to_csv",
    "create_sample_pmax_campaign",
    "create_sample_search_campaign",
]
