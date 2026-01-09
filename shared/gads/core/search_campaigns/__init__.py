"""
Search Campaign Core Module

This module contains all logic specific to Google Ads Search campaigns.
Search campaigns use Ad Groups (not Asset Groups) and have different CSV structures,
validation rules, and bid strategies compared to PMAX campaigns.

Key Differences from PMAX:
- Uses Ad Groups instead of Asset Groups
- Different CSV column structure
- Manual CPC, Target CPA, Maximize Clicks bid strategies
- Search network only (no Display, no Search Partners)
- Text ads, not responsive search ads
- Keyword targeting instead of audience signals
"""

from .search_campaign_builder import SearchCampaignBuilder
from .search_csv_generator import SearchCSVGenerator
from .search_validator import SearchCampaignValidator

__all__ = [
    'SearchCampaignBuilder',
    'SearchCSVGenerator',
    'SearchCampaignValidator'
]