"""Active Search campaign build helper for Google Ads Editor staging.

This is the active campaign-build surface under ``shared/tools/campaign``.
Older campaign scripts in this folder are salvage material unless they delegate
to this module or another tested Search staging helper.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from shared.gads.core.business_logic.google_ads_editor_exporter import GoogleAdsEditorExporter


@dataclass(frozen=True)
class SearchRSAAssets:
    """Responsive Search Ad assets for one ad group."""

    headlines: list[str]
    descriptions: list[str]
    final_url: str
    path_1: str = ""
    path_2: str = ""


@dataclass(frozen=True)
class SearchAdGroupBuild:
    """Ad group input for Search campaign staging."""

    name: str
    keywords: list[str]
    rsa: SearchRSAAssets
    final_url: str = ""


@dataclass(frozen=True)
class SearchCampaignBuild:
    """Search campaign input for active staging generation."""

    name: str
    budget: float
    ad_groups: list[SearchAdGroupBuild]
    locations: list[dict[str, str]] = field(default_factory=list)
    status: str = "Paused"
    networks: str = "Google search"
    budget_type: str = "Daily"
    eu_political_ads: str = "No"


def build_search_campaign_staging(
    campaign: SearchCampaignBuild,
    output_path: str | Path,
) -> dict[str, Any]:
    """Write and validate a Search campaign staging file."""
    exporter = GoogleAdsEditorExporter()
    report = exporter.export_and_validate([_to_exporter_campaign(campaign)], output_path)
    if report.get("status") != "pass":
        raise ValueError(f"Generated staging output failed validation: {report.get('issues', [])}")
    return report


def to_exporter_campaign(campaign: SearchCampaignBuild) -> dict[str, Any]:
    """Return exporter-compatible campaign data without writing a file."""
    return _to_exporter_campaign(campaign)


def _to_exporter_campaign(campaign: SearchCampaignBuild) -> dict[str, Any]:
    _validate_campaign(campaign)
    return {
        "name": campaign.name,
        "type": "Search",
        "budget": campaign.budget,
        "status": campaign.status,
        "networks": campaign.networks,
        "budget_type": campaign.budget_type,
        "eu_political_ads": campaign.eu_political_ads,
        "broad_match_keywords": "Off",
        "locations": campaign.locations,
        "ad_groups": [_to_exporter_ad_group(ad_group) for ad_group in campaign.ad_groups],
    }


def _to_exporter_ad_group(ad_group: SearchAdGroupBuild) -> dict[str, Any]:
    final_url = ad_group.final_url or ad_group.rsa.final_url
    return {
        "name": ad_group.name,
        "final_url": final_url,
        "keywords": [
            {
                "text": _plain_keyword(keyword),
                "criterion_type": "Phrase",
                "final_url": final_url,
                "status": "Paused",
            }
            for keyword in ad_group.keywords
        ],
        "rsa": {
            "final_url": ad_group.rsa.final_url,
            "headlines": ad_group.rsa.headlines,
            "descriptions": ad_group.rsa.descriptions,
            "path_1": ad_group.rsa.path_1,
            "path_2": ad_group.rsa.path_2,
            "status": "Paused",
        },
        "status": "Paused",
    }


def _validate_campaign(campaign: SearchCampaignBuild) -> None:
    if not campaign.name.strip():
        raise ValueError("Campaign name is required.")
    if campaign.budget <= 0:
        raise ValueError("Campaign budget must be greater than zero.")
    if not campaign.ad_groups:
        raise ValueError("At least one ad group is required.")
    for ad_group in campaign.ad_groups:
        _validate_ad_group(ad_group)


def _validate_ad_group(ad_group: SearchAdGroupBuild) -> None:
    if not ad_group.name.strip():
        raise ValueError("Ad group name is required.")
    if not ad_group.keywords:
        raise ValueError("At least one phrase keyword is required.")
    if len(ad_group.rsa.headlines) != 15:
        raise ValueError("Search RSA assets require exactly 15 headlines.")
    if len(ad_group.rsa.descriptions) != 4:
        raise ValueError("Search RSA assets require exactly 4 descriptions.")
    if not ad_group.rsa.final_url.strip():
        raise ValueError("RSA final URL is required.")
    for keyword in ad_group.keywords:
        _plain_keyword(keyword)


def _plain_keyword(keyword: str) -> str:
    value = keyword.strip()
    if not value:
        raise ValueError("Keyword text is required.")
    if value in {"Broad", "Exact", "BROAD", "EXACT"}:
        raise ValueError("Broad and Exact are inactive keyword types.")
    if value.startswith(('"', "[", "-")) or value.endswith(('"', "]")):
        raise ValueError("Keyword must be plain text. Match behavior belongs in Criterion Type.")
    return value


__all__ = [
    "SearchAdGroupBuild",
    "SearchCampaignBuild",
    "SearchRSAAssets",
    "build_search_campaign_staging",
    "to_exporter_campaign",
]
