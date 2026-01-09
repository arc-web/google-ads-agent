"""
Configuration loader for Google Ads campaign settings
Loads configuration from separate, well-organized YAML files
"""

import yaml
import os
from typing import Dict, Any
from pathlib import Path


class ConfigLoader:
    """Loads configuration from organized YAML files"""

    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir or os.path.dirname(__file__))

    def load_campaign_config(self, campaign_type: str = "search", bid_strategy: str = "default") -> Dict[str, Any]:
        """
        Load campaign-specific configuration for a given campaign type and bid strategy.

        Args:
            campaign_type: Type of campaign (search, display, performance_max, shopping, video, app, discovery, local)
            bid_strategy: Specific bid strategy variant (default, manual_cpc, target_cpa, etc.)

        Returns:
            Dict containing campaign configuration for the specified type
        """
        all_configs = self._load_yaml('campaign_defaults.yaml')

        if not all_configs:
            return {}

        # Map campaign type names to config keys
        type_mapping = {
            "search": "search_campaigns",
            "display": "display_campaigns",
            "performance_max": "performance_max_campaigns",
            "pmax": "performance_max_campaigns",
            "shopping": "shopping_campaigns",
            "video": "video_campaigns",
            "youtube": "video_campaigns",
            "app": "app_campaigns",
            "discovery": "discovery_campaigns",
            "local": "local_campaigns",
            "local_services": "local_campaigns"
        }

        config_key = type_mapping.get(campaign_type.lower(), "search_campaigns")
        campaign_configs = all_configs.get(config_key, {})

        # Get the specific bid strategy config, fallback to default
        config = campaign_configs.get(bid_strategy, campaign_configs.get("default", {}))

        # Merge with global settings
        global_settings = all_configs.get("global_settings", {})
        config.update(global_settings)

        # Add geographic targeting
        geographic = all_configs.get("geographic", {})
        config["geographic"] = geographic

        return config

    def get_available_campaign_types(self) -> List[str]:
        """Get list of all available campaign types"""
        all_configs = self._load_yaml('campaign_defaults.yaml')
        if not all_configs:
            return []

        campaign_types = []
        for key in all_configs.keys():
            if key.endswith("_campaigns"):
                campaign_type = key.replace("_campaigns", "")
                campaign_types.append(campaign_type)

        return campaign_types

    def get_campaign_type_recommendations(self, business_goal: str) -> Dict[str, Any]:
        """
        Get campaign type recommendations based on business goal.

        Args:
            business_goal: Business objective (brand_awareness, lead_generation, sales_conversion, etc.)

        Returns:
            Dict with recommended campaign types and settings
        """
        all_configs = self._load_yaml('campaign_defaults.yaml')
        if not all_configs:
            return {}

        selection_rules = all_configs.get("campaign_type_selection", {}).get("rules", {})
        return selection_rules.get(business_goal, {})

    def load_ad_limits(self) -> Dict[str, Any]:
        """Load ad format limits configuration"""
        return self._load_yaml('ad_limits.yaml')

    def load_character_limits(self) -> Dict[str, Any]:
        """Load character limits for all ad formats"""
        return self._load_yaml('ad_character_limits.yaml')

    def load_business_config(self) -> Dict[str, Any]:
        """Load business-specific configuration"""
        return self._load_yaml('business_config.yaml')

    def load_all_config(self) -> Dict[str, Any]:
        """Load all configuration files and merge them"""
        config = {}

        # Load each config file
        config_files = [
            ('campaign', self.load_campaign_config()),
            ('limits', self.load_ad_limits()),
            ('character_limits', self.load_character_limits()),
            ('business', self.load_business_config())
        ]

        # Merge configurations
        for key, data in config_files:
            if data:
                config[key] = data

        return config

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load a YAML file with error handling"""
        file_path = self.config_dir / filename

        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"Warning: Config file not found: {file_path}")
            return {}
        except Exception as e:
            print(f"Warning: Could not load config {filename}: {e}")
            return {}


# Legacy function for backward compatibility
def load_campaign_config() -> Dict[str, Any]:
    """Load all campaign configuration (legacy function)"""
    loader = ConfigLoader()
    return loader.load_all_config()
