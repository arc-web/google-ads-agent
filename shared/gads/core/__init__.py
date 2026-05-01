"""Google Ads Agent core salvage package.

Importing this package must stay lightweight. API clients and optional Google
Ads dependencies are loaded by the modules that need them, not by package import.
"""

__all__ = [
    "GoogleAdsAPIService",
    "GoogleAdsAccount",
    "AccountAccessCheck",
    "CampaignBudget",
    "Campaign",
    "CampaignCreationLog",
    "AssetGroup",
    "Asset",
    "AdGroup",
    "Keyword",
    "Ad",
    "SystematicExecution",
]


def __getattr__(name: str):
    if name == "GoogleAdsAPIService":
        from .google_ads_api_service import GoogleAdsAPIService

        return GoogleAdsAPIService

    if name in {
        "GoogleAdsAccount",
        "AccountAccessCheck",
        "CampaignBudget",
        "Campaign",
        "CampaignCreationLog",
        "AssetGroup",
        "Asset",
        "AdGroup",
        "Keyword",
        "Ad",
        "SystematicExecution",
    }:
        from . import models

        return getattr(models, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
