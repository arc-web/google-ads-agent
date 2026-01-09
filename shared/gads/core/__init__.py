"""
Google Ads Agent Core Module

Provides systematic Google Ads campaign management through API integration.
"""

from .google_ads_api_service import GoogleAdsAPIService
from .models import (
    GoogleAdsAccount, AccountAccessCheck, CampaignBudget,
    Campaign, CampaignCreationLog, AssetGroup, Asset,
    AdGroup, Keyword, Ad, SystematicExecution
)

__all__ = [
    'GoogleAdsAPIService',
    'GoogleAdsAccount',
    'AccountAccessCheck',
    'CampaignBudget',
    'Campaign',
    'CampaignCreationLog',
    'AssetGroup',
    'Asset',
    'AdGroup',
    'Keyword',
    'Ad',
    'SystematicExecution'
]
