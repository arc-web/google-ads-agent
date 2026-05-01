"""
Configuration loader for Google Ads campaign settings
Loads configuration from separate, well-organized YAML files
"""

import yaml
import os
from typing import Any
from pathlib import Path


ACTIVE_CAMPAIGN_TYPES = {"search"}
CAMPAIGN_TYPE_MAPPING = {
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
    "local_services": "local_campaigns",
}


class ConfigLoader:
    """Loads configuration from organized YAML files"""

    def __init__(self, config_dir: str | Path | None = None, *, allow_inactive_campaign_types: bool = False):
        self.config_dir = Path(config_dir or os.path.dirname(__file__))
        self.allow_inactive_campaign_types = allow_inactive_campaign_types

    def load_campaign_config(self, campaign_type: str = "search", bid_strategy: str = "default") -> dict[str, Any]:
        """
        Load campaign-specific configuration for a given campaign type and bid strategy.

        Args:
            campaign_type: Type of campaign (search, display, performance_max, shopping, video, app, discovery, local)
            bid_strategy: Specific bid strategy variant (default, manual_cpc, target_cpa, etc.)

        Returns:
            Dict containing campaign configuration for the specified type
        """
        normalized_type = self._normalize_campaign_type(campaign_type)
        if normalized_type not in ACTIVE_CAMPAIGN_TYPES and not self.allow_inactive_campaign_types:
            raise ValueError(
                f"Campaign type '{campaign_type}' is inactive. "
                "The active workflow is Search-first Google Ads Editor staging."
            )

        all_configs = self._load_yaml('campaign_defaults.yaml')

        if not all_configs:
            return {}

        config_key = CAMPAIGN_TYPE_MAPPING.get(normalized_type, "search_campaigns")
        campaign_configs = all_configs.get(config_key, {})

        # Get the specific bid strategy config, fallback to default
        config = campaign_configs.get(bid_strategy, campaign_configs.get("default", {}))

        # Merge with global settings
        config = dict(config)
        global_settings = all_configs.get("global_settings", {})
        merged_config = {**global_settings, **config}
        merged_config["active_workflow"] = all_configs.get("active_workflow", {})

        # Add geographic targeting
        geographic = all_configs.get("geographic", {})
        merged_config["geographic"] = geographic

        return merged_config

    def get_available_campaign_types(self) -> list[str]:
        """Get active campaign types by default."""
        if not self.allow_inactive_campaign_types:
            return sorted(ACTIVE_CAMPAIGN_TYPES)

        all_configs = self._load_yaml('campaign_defaults.yaml')
        if not all_configs:
            return []

        campaign_types = []
        for key in all_configs.keys():
            if key.endswith("_campaigns"):
                campaign_type = key.replace("_campaigns", "")
                campaign_types.append(campaign_type)

        return campaign_types

    def get_campaign_type_recommendations(self, business_goal: str) -> dict[str, Any]:
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
        recommendations = selection_rules.get(business_goal, {})
        if self.allow_inactive_campaign_types:
            return recommendations

        recommended_types = recommendations.get("recommended_types", [])
        return {
            **recommendations,
            "recommended_types": [
                campaign_type
                for campaign_type in recommended_types
                if self._normalize_campaign_type(campaign_type) in ACTIVE_CAMPAIGN_TYPES
            ],
        }

    def load_ad_limits(self) -> dict[str, Any]:
        """Load ad format limits configuration"""
        return self._load_yaml('ad_limits.yaml')

    def load_character_limits(self) -> dict[str, Any]:
        """Load character limits for all ad formats"""
        return self._load_yaml('ad_character_limits.yaml')

    def load_business_config(self) -> dict[str, Any]:
        """Load business-specific configuration"""
        return self._load_yaml('business_config.yaml')

    def load_all_config(self) -> dict[str, Any]:
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

    def _load_yaml(self, filename: str) -> dict[str, Any]:
        """Load a YAML file with error handling"""
        file_path = self.config_dir / filename

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"Warning: Config file not found: {file_path}")
            return {}
        except Exception as e:
            print(f"Warning: Could not load config {filename}: {e}")
            return {}

    def _normalize_campaign_type(self, campaign_type: str) -> str:
        return campaign_type.strip().lower().replace(" ", "_").replace("-", "_")


# Legacy function for backward compatibility
def load_campaign_config() -> dict[str, Any]:
    """Load all campaign configuration (legacy function)"""
    loader = ConfigLoader()
    return loader.load_all_config()
