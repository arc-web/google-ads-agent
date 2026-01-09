#!/usr/bin/env python3
"""
Google Ads CSV Validators Package

This package provides hierarchical validation of Google Ads CSVs across all client directories.
Validates in order: Account Settings → Campaign Settings → Asset Groups → Assets → Targeting.
"""

from .master_validator import MasterValidator
from .account_validator import AccountValidator
from .campaign_validator import CampaignValidator
from .asset_group_validator import AssetGroupValidator
from .asset_validator import AssetValidator
from .targeting_validator import TargetingValidator

__all__ = [
    'MasterValidator',
    'AccountValidator',
    'CampaignValidator',
    'AssetGroupValidator',
    'AssetValidator',
    'TargetingValidator'
]

__version__ = '1.0.0'