"""
PMAX Campaign Core Module

This module contains all logic specific to Google Ads Performance Max campaigns.
PMAX campaigns use Asset Groups (not Ad Groups) and have different CSV structures,
validation rules, and bid strategies compared to Search campaigns.

Key Differences from Search:
- Uses Asset Groups instead of Ad Groups
- Different CSV column structure
- Target ROAS, Maximize Conversion Value bid strategies
- Audience signals and asset-based targeting
- Responsive search ads, not text ads
- No keyword match types (uses search themes)

ARCHITECTURAL SEPARATION: This module is completely separate from Search campaigns.
"""

from .pmax_campaign_builder import PMAXCampaignBuilder
from .pmax_csv_generator import PMAXCSVGenerator
from .pmax_validator import PMAXCampaignValidator

__all__ = [
    'PMAXCampaignBuilder',
    'PMAXCSVGenerator',
    'PMAXCampaignValidator'
]