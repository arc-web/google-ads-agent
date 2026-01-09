#!/usr/bin/env python3
"""
Ad Group Management System for Google Ads Search Campaigns

This comprehensive system provides tools for managing ad groups in search campaigns,
including creation, configuration, optimization, and best practices based on
Google Ads documentation.

Usage:
    from gads.tools.ad_group_management_system import AdGroupManagementSystem

    ag_system = AdGroupManagementSystem()
    ad_group_config = ag_system.create_optimized_ad_group("Executive Resume Services", "search")
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AdGroupSettings:
    """Configuration settings for an ad group"""
    name: str
    status: str = "ENABLED"
    type: str = "SEARCH_STANDARD"
    cpc_bid_micros: Optional[int] = None
    target_cpa_micros: Optional[int] = None
    target_roas: Optional[float] = None
    effective_target_cpa_source: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    final_url_suffix: Optional[str] = None
    tracking_url_template: Optional[str] = None
    url_custom_parameters: List[Dict[str, str]] = field(default_factory=list)

@dataclass
class AdGroupTargeting:
    """Targeting settings for an ad group"""
    keywords: List[Dict[str, Any]] = field(default_factory=list)
    negative_keywords: List[Dict[str, Any]] = field(default_factory=list)
    audience_targeting: List[str] = field(default_factory=list)
    demographic_targeting: Dict[str, List[str]] = field(default_factory=dict)
    device_targeting: List[str] = field(default_factory=list)

@dataclass
class AdGroupPerformance:
    """Performance metrics and optimization data"""
    impressions: int = 0
    clicks: int = 0
    cost_micros: int = 0
    conversions: float = 0.0
    conversion_value_micros: int = 0
    ctr: float = 0.0
    cpc: float = 0.0
    cpa: float = 0.0
    roas: float = 0.0
    quality_score: Optional[int] = None
    ad_relevance: Optional[int] = None
    landing_page_experience: Optional[int] = None
    expected_ctr: Optional[int] = None

@dataclass
class AdGroupOptimization:
    """Optimization recommendations and actions"""
    bid_adjustments: Dict[str, float] = field(default_factory=dict)
    keyword_additions: List[str] = field(default_factory=list)
    keyword_removals: List[str] = field(default_factory=list)
    negative_keyword_additions: List[str] = field(default_factory=list)
    audience_expansions: List[str] = field(default_factory=list)
    ad_text_improvements: List[str] = field(default_factory=list)
    priority_actions: List[str] = field(default_factory=list)

class AdGroupManagementSystem:
    """
    Comprehensive ad group management system for Google Ads search campaigns.

    This system provides tools for creating, configuring, optimizing, and managing
    ad groups based on Google Ads best practices and API documentation.
    """

    def __init__(self):
        """Initialize the ad group management system"""
        self.ad_group_types = self._load_ad_group_types()
        self.bid_strategies = self._load_bid_strategies()
        self.optimization_rules = self._load_optimization_rules()
        self.naming_conventions = self._load_naming_conventions()

    def _load_ad_group_types(self) -> Dict[str, Dict[str, Any]]:
        """Load ad group type information"""
        return {
            "SEARCH_STANDARD": {
                "description": "Standard search ad group for text ads",
                "campaign_types": ["SEARCH"],
                "ad_formats": ["TEXT_AD", "RESPONSIVE_SEARCH_AD"],
                "features": ["keywords", "negative_keywords", "ad_schedules", "device_targeting"]
            },
            "SEARCH_DYNAMIC": {
                "description": "Dynamic search ad group for automated keyword targeting",
                "campaign_types": ["SEARCH"],
                "ad_formats": ["DYNAMIC_SEARCH_AD"],
                "features": ["dynamic_keyword_insertion", "website_content_targeting"]
            },
            "DISPLAY_STANDARD": {
                "description": "Standard display ad group for banner ads",
                "campaign_types": ["DISPLAY"],
                "ad_formats": ["BANNER_AD", "RESPONSIVE_DISPLAY_AD"],
                "features": ["topics", "interests", "placements", "demographics"]
            },
            "SHOPPING_PRODUCT_ADS": {
                "description": "Shopping ad group for product listings",
                "campaign_types": ["SHOPPING"],
                "ad_formats": ["PRODUCT_SHOPPING_AD"],
                "features": ["product_groups", "inventory_filters"]
            }
        }

    def _load_bid_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Load bidding strategy information for ad groups"""
        return {
            "manual_cpc": {
                "description": "Set your own maximum CPC bids",
                "ad_group_level": True,
                "keyword_level": True,
                "optimization_goal": "Control over individual click costs",
                "setup_requirements": ["cpc_bid_micros"],
                "best_for": ["Precise budget control", "Testing different bid levels", "Brand campaigns"]
            },
            "target_cpa": {
                "description": "Automatically set bids to help get conversions at target CPA",
                "ad_group_level": True,
                "keyword_level": False,
                "optimization_goal": "Maximize conversions at target CPA",
                "setup_requirements": ["target_cpa_micros", "conversion_tracking"],
                "best_for": ["Lead generation", "E-commerce sales", "App installs"]
            },
            "target_roas": {
                "description": "Automatically set bids to maximize revenue at target ROAS",
                "ad_group_level": True,
                "keyword_level": False,
                "optimization_goal": "Maximize revenue at target ROAS",
                "setup_requirements": ["target_roas", "conversion_value_tracking"],
                "best_for": ["E-commerce", "High-value conversions"]
            },
            "maximize_clicks": {
                "description": "Automatically set bids to get as many clicks as possible within budget",
                "ad_group_level": True,
                "keyword_level": False,
                "optimization_goal": "Maximize clicks within budget",
                "setup_requirements": ["campaign_budget"],
                "best_for": ["Traffic generation", "Brand awareness"]
            }
        }

    def _load_optimization_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load optimization rules for ad group performance"""
        return {
            "low_ctr": {
                "threshold": 1.0,
                "actions": ["improve_ad_text", "add_negative_keywords", "test_ad_variations"],
                "bid_adjustment": -0.2
            },
            "high_cpa": {
                "threshold": "target_cpa * 1.5",
                "actions": ["lower_bids", "add_negative_keywords", "improve_quality_score"],
                "bid_adjustment": -0.3
            },
            "low_quality_score": {
                "threshold": 3,
                "actions": ["improve_landing_page", "add_negative_keywords", "optimize_ad_text"],
                "priority": "high"
            },
            "high_conversions": {
                "threshold": "baseline + 20%",
                "actions": ["increase_bids", "expand_keywords", "test_new_ad_variations"],
                "bid_adjustment": 0.2
            }
        }

    def _load_naming_conventions(self) -> Dict[str, Dict[str, Any]]:
        """Load naming convention guidelines"""
        return {
            "structure": "{Campaign Type} - {Target Audience} - {Match Type} - {Geo Location}",
            "examples": [
                "Search - Executive Resume - Broad - National",
                "Search - C-Suite - Exact - Florida",
                "Search - Professional Services - Phrase - Miami"
            ],
            "best_practices": [
                "Use descriptive, searchable names",
                "Include targeting information",
                "Keep names under 128 characters",
                "Use consistent formatting",
                "Include match types for keyword-focused ad groups"
            ]
        }

    def create_optimized_ad_group(self,
                                 theme: str,
                                 campaign_type: str = "SEARCH",
                                 target_audience: str = None,
                                 geo_targeting: str = None,
                                 budget_micros: int = None) -> Dict[str, Any]:
        """
        Create an optimized ad group configuration based on best practices.

        Args:
            theme: The main theme/topic of the ad group
            campaign_type: Type of campaign (SEARCH, DISPLAY, etc.)
            target_audience: Target audience segment
            geo_targeting: Geographic targeting information
            budget_micros: Budget in micros for bid calculation

        Returns:
            Complete ad group configuration dictionary
        """
        logger.info(f"Creating optimized ad group for theme: {theme}")

        # Generate optimal name
        ad_group_name = self._generate_ad_group_name(theme, campaign_type, target_audience, geo_targeting)

        # Determine ad group type
        ad_group_type = self._determine_ad_group_type(campaign_type)

        # Create settings
        settings = self._create_optimized_settings(theme, campaign_type, budget_micros)

        # Generate initial keywords
        keywords = self._generate_initial_keywords(theme, target_audience)

        # Create targeting
        targeting = self._create_targeting_config(theme, target_audience, geo_targeting)

        return {
            "name": ad_group_name,
            "type": ad_group_type,
            "campaign_type": campaign_type,
            "settings": settings,
            "targeting": targeting,
            "keywords": keywords,
            "optimization_recommendations": self._get_initial_optimization_recommendations(),
            "performance_tracking": {},
            "created_at": datetime.now().isoformat(),
            "version": "1.0"
        }

    def _generate_ad_group_name(self, theme: str, campaign_type: str,
                              target_audience: str = None, geo_targeting: str = None) -> str:
        """Generate an optimized ad group name following best practices"""
        parts = []

        # Campaign type prefix
        if campaign_type.upper() == "SEARCH":
            parts.append("Search")
        elif campaign_type.upper() == "DISPLAY":
            parts.append("Display")
        else:
            parts.append(campaign_type.title())

        # Main theme
        theme_clean = theme.replace("-", " ").replace("_", " ").title()
        if len(theme_clean) > 30:
            theme_clean = theme_clean[:27] + "..."
        parts.append(theme_clean)

        # Target audience (if provided and different from theme)
        if target_audience and target_audience.lower() not in theme.lower():
            audience_clean = target_audience.replace("-", " ").replace("_", " ").title()
            if len(audience_clean) > 20:
                audience_clean = audience_clean[:17] + "..."
            parts.append(audience_clean)

        # Geographic targeting (if provided)
        if geo_targeting:
            geo_clean = geo_targeting.replace("-", " ").replace("_", " ").title()
            if len(geo_clean) > 15:
                geo_clean = geo_clean[:12] + "..."
            parts.append(geo_clean)

        name = " - ".join(parts)

        # Ensure name is within limits
        if len(name) > 128:
            name = name[:125] + "..."

        return name

    def _determine_ad_group_type(self, campaign_type: str) -> str:
        """Determine the appropriate ad group type for the campaign"""
        campaign_type = campaign_type.upper()

        if campaign_type == "SEARCH":
            return "SEARCH_STANDARD"
        elif campaign_type == "DISPLAY":
            return "DISPLAY_STANDARD"
        elif campaign_type == "SHOPPING":
            return "SHOPPING_PRODUCT_ADS"
        else:
            return "SEARCH_STANDARD"  # Default

    def _create_optimized_settings(self, theme: str, campaign_type: str,
                                 budget_micros: int = None) -> AdGroupSettings:
        """Create optimized settings for the ad group"""
        settings = AdGroupSettings(
            name="",  # Will be set by caller
            status="ENABLED",
            type=self._determine_ad_group_type(campaign_type)
        )

        # Set default CPC bid based on campaign type and theme
        if campaign_type.upper() == "SEARCH":
            # Base bid calculation (this would be refined based on historical data)
            base_bid_micros = 500000  # $0.50 base bid

            # Adjust for competitive themes
            competitive_keywords = ["resume", "lawyer", "insurance", "mortgage", "loan"]
            if any(kw in theme.lower() for kw in competitive_keywords):
                base_bid_micros = int(base_bid_micros * 1.5)  # Increase for competitive themes

            # Adjust for budget constraints
            if budget_micros and budget_micros < 10000000:  # Less than $10 daily budget
                base_bid_micros = int(base_bid_micros * 0.8)  # Conservative bidding

            settings.cpc_bid_micros = base_bid_micros

        return settings

    def _generate_initial_keywords(self, theme: str, target_audience: str = None) -> List[Dict[str, Any]]:
        """Generate initial keyword set for the ad group"""
        keywords = []

        # Core exact match keywords
        theme_words = theme.lower().split()
        exact_keywords = [
            f'"{theme}"',
            f'"{theme} services"',
            f'"{theme} help"'
        ]
        keywords.extend([{"text": kw, "match_type": "EXACT"} for kw in exact_keywords])

        # Phrase match keywords
        phrase_keywords = [
            f'"{theme}"',
            f'"{theme} services"',
            f'"{theme} help"',
            f'"{theme} assistance"'
        ]
        keywords.extend([{"text": kw, "match_type": "PHRASE"} for kw in phrase_keywords])

        # Broad match keywords (more conservative set)
        broad_keywords = [
            theme,
            f"{theme} services",
            f"{theme} help"
        ]
        keywords.extend([{"text": kw, "match_type": "BROAD"} for kw in broad_keywords])

        # Add audience-specific keywords if provided
        if target_audience and target_audience != theme:
            audience_keywords = [
                f'"{target_audience} {theme}"',
                f'"{target_audience}"',
                f'"{theme} for {target_audience}"'
            ]
            keywords.extend([{"text": kw, "match_type": "PHRASE"} for kw in audience_keywords])

        return keywords

    def _create_targeting_config(self, theme: str, target_audience: str = None,
                               geo_targeting: str = None) -> AdGroupTargeting:
        """Create targeting configuration for the ad group"""
        targeting = AdGroupTargeting()

        # Add negative keywords to improve relevance
        negative_keywords = [
            "free", "cheap", "template", "download", "pdf",
            "tutorial", "how to", "DIY", "make money"
        ]

        # Add theme-specific negative keywords
        if "resume" in theme.lower():
            negative_keywords.extend([
                "writing service", "template", "free resume",
                "resume builder", "job search site"
            ])

        targeting.negative_keywords = [
            {"text": kw, "match_type": "EXACT"} for kw in negative_keywords
        ]

        # Set demographic targeting for B2B services
        if target_audience and any(term in target_audience.lower() for term in
                                 ["executive", "professional", "business", "c-suite"]):
            targeting.demographic_targeting = {
                "age_ranges": ["35-44", "45-54", "55-64", "65_UP"],
                "genders": ["MALE", "FEMALE"],
                "household_incomes": ["TOP_25_PERCENT", "TOP_10_PERCENT", "TOP_5_PERCENT"]
            }

        return targeting

    def _get_initial_optimization_recommendations(self) -> List[str]:
        """Get initial optimization recommendations for new ad groups"""
        return [
            "Monitor Quality Score and landing page experience",
            "Add negative keywords to improve click-through rate",
            "Test different ad variations for better performance",
            "Set up conversion tracking to measure success",
            "Review search terms report weekly to find new keyword opportunities",
            "Optimize bids based on conversion performance, not just clicks"
        ]

    def optimize_ad_group(self, ad_group_config: Dict[str, Any],
                         performance_data: Dict[str, Any]) -> AdGroupOptimization:
        """
        Analyze ad group performance and provide optimization recommendations.

        Args:
            ad_group_config: Current ad group configuration
            performance_data: Performance metrics from Google Ads

        Returns:
            Optimization recommendations and actions
        """
        logger.info(f"Optimizing ad group: {ad_group_config.get('name', 'Unknown')}")

        optimization = AdGroupOptimization()

        # Analyze CTR
        ctr = performance_data.get('ctr', 0)
        if ctr < 1.0:
            optimization.priority_actions.append("Improve ad text relevance and calls-to-action")
            optimization.ad_text_improvements.append("Add more specific benefits and unique selling propositions")
            optimization.bid_adjustments["device_mobile"] = -0.2

        # Analyze CPA vs target
        cpa = performance_data.get('cpa', 0)
        target_cpa = ad_group_config.get('settings', {}).get('target_cpa_micros', 0) / 1000000
        if target_cpa > 0 and cpa > target_cpa * 1.5:
            optimization.priority_actions.append("Reduce bids or add negative keywords to improve CPA")
            optimization.bid_adjustments["overall"] = -0.3

        # Analyze Quality Score
        quality_score = performance_data.get('quality_score')
        if quality_score and quality_score < 4:
            optimization.priority_actions.append("Improve landing page experience and ad relevance")
            optimization.ad_text_improvements.append("Make ads more relevant to target keywords")

        # Keyword optimization
        search_terms = performance_data.get('search_terms_report', [])
        high_performing_terms = [term for term in search_terms if term.get('conversions', 0) > 0]
        low_performing_terms = [term for term in search_terms if term.get('ctr', 0) < 1.0 and term.get('clicks', 0) > 10]

        optimization.keyword_additions.extend([term['text'] for term in high_performing_terms[:5]])
        optimization.negative_keyword_additions.extend([term['text'] for term in low_performing_terms[:10]])

        return optimization

    def validate_ad_group_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate ad group configuration against best practices.

        Args:
            config: Ad group configuration to validate

        Returns:
            Validation results with warnings and recommendations
        """
        validation = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }

        # Check name
        name = config.get('name', '')
        if not name:
            validation["errors"].append("Ad group name is required")
            validation["is_valid"] = False
        elif len(name) > 128:
            validation["warnings"].append("Ad group name exceeds 128 character limit")

        # Check keywords
        keywords = config.get('keywords', [])
        if len(keywords) < 5:
            validation["warnings"].append("Consider adding more keywords for better coverage")

        exact_keywords = [k for k in keywords if k.get('match_type') == 'EXACT']
        if len(exact_keywords) < 2:
            validation["recommendations"].append("Add more exact match keywords for precise targeting")

        # Check bids
        settings = config.get('settings', {})
        if not settings.get('cpc_bid_micros') and not settings.get('target_cpa_micros'):
            validation["warnings"].append("No bidding strategy configured")

        # Check negative keywords
        targeting = config.get('targeting', {})
        negative_keywords = targeting.get('negative_keywords', [])
        if len(negative_keywords) < 5:
            validation["recommendations"].append("Add more negative keywords to improve relevance")

        return validation

    def generate_ad_group_json(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate JSON representation for Google Ads API ad group creation.

        Args:
            config: Ad group configuration

        Returns:
            JSON object for Google Ads API
        """
        settings = config.get('settings', {})

        ad_group_json = {
            "name": config["name"],
            "status": settings.get("status", "ENABLED"),
            "type": settings.get("type", "SEARCH_STANDARD")
        }

        # Add bidding information
        if settings.get("cpc_bid_micros"):
            ad_group_json["cpcBidMicros"] = settings["cpc_bid_micros"]
        if settings.get("target_cpa_micros"):
            ad_group_json["targetCpaMicros"] = settings["target_cpa_micros"]
        if settings.get("target_roas"):
            ad_group_json["targetRoas"] = settings["target_roas"]

        # Add labels
        if settings.get("labels"):
            ad_group_json["labels"] = settings["labels"]

        # Add URL parameters
        if settings.get("final_url_suffix"):
            ad_group_json["finalUrlSuffix"] = settings["final_url_suffix"]
        if settings.get("tracking_url_template"):
            ad_group_json["trackingUrlTemplate"] = settings["tracking_url_template"]
        if settings.get("url_custom_parameters"):
            ad_group_json["urlCustomParameters"] = settings["url_custom_parameters"]

        return ad_group_json

    def get_ad_group_best_practices(self, ad_group_type: str = "SEARCH_STANDARD") -> Dict[str, List[str]]:
        """
        Get best practices for ad group management.

        Args:
            ad_group_type: Type of ad group

        Returns:
            Dictionary of best practice categories
        """
        base_practices = {
            "naming": [
                "Use descriptive, keyword-rich names",
                "Include targeting information in the name",
                "Keep names under 128 characters",
                "Use consistent naming conventions across campaigns"
            ],
            "structure": [
                "Group tightly related keywords together",
                "Create separate ad groups for different match types",
                "Limit ad groups to 20-50 keywords",
                "Use single keyword ad groups for high-value terms"
            ],
            "bidding": [
                "Set appropriate bids based on competition and goals",
                "Use ad group level bids for testing",
                "Adjust bids based on performance data",
                "Consider quality score when setting bids"
            ],
            "optimization": [
                "Monitor quality score regularly",
                "Add negative keywords to improve CTR",
                "Test different ad variations",
                "Review search terms report weekly",
                "Optimize for conversion rate, not just clicks"
            ]
        }

        # Add type-specific practices
        if ad_group_type == "SEARCH_STANDARD":
            base_practices["keywords"] = [
                "Use mix of match types (exact, phrase, broad)",
                "Include long-tail keywords",
                "Add question-based keywords",
                "Use keyword variations and synonyms"
            ]
        elif ad_group_type == "DISPLAY_STANDARD":
            base_practices["targeting"] = [
                "Use topic targeting for broad reach",
                "Add interest categories for precision",
                "Include demographic targeting",
                "Use placement exclusions for irrelevant sites"
            ]

        return base_practices

    def create_ad_group_from_template(self, template_name: str,
                                    customizations: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create an ad group from a predefined template.

        Args:
            template_name: Name of the template to use
            customizations: Custom values to override template defaults

        Returns:
            Complete ad group configuration
        """
        templates = {
            "executive_services": {
                "theme": "Executive Resume Services",
                "campaign_type": "SEARCH",
                "target_audience": "executive_professionals",
                "competitive_bidding": True
            },
            "local_services": {
                "theme": "Professional Services",
                "campaign_type": "SEARCH",
                "geo_targeting": "local",
                "local_focus": True
            },
            "brand_awareness": {
                "theme": "Brand Awareness",
                "campaign_type": "DISPLAY",
                "target_audience": "general",
                "awareness_focus": True
            }
        }

        if template_name not in templates:
            raise ValueError(f"Template '{template_name}' not found")

        template = templates[template_name]

        # Apply customizations
        if customizations:
            template.update(customizations)

        return self.create_optimized_ad_group(**template)

    def get_ad_group_performance_analysis(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze ad group performance and provide insights.

        Args:
            performance_data: Performance metrics from Google Ads

        Returns:
            Performance analysis with insights and recommendations
        """
        analysis = {
            "overall_health": "unknown",
            "key_metrics": {},
            "insights": [],
            "recommendations": [],
            "alerts": []
        }

        # Calculate key metrics
        impressions = performance_data.get('impressions', 0)
        clicks = performance_data.get('clicks', 0)
        cost = performance_data.get('cost_micros', 0) / 1000000
        conversions = performance_data.get('conversions', 0)

        if impressions > 0:
            ctr = (clicks / impressions) * 100
            analysis["key_metrics"]["ctr"] = round(ctr, 2)

        if clicks > 0:
            cpc = cost / clicks
            analysis["key_metrics"]["cpc"] = round(cpc, 2)

        if conversions > 0:
            cpa = cost / conversions
            analysis["key_metrics"]["cpa"] = round(cpa, 2)

        # Determine overall health
        if ctr > 2.0 and cpa < 50:  # Example thresholds
            analysis["overall_health"] = "excellent"
        elif ctr > 1.0 and cpa < 100:
            analysis["overall_health"] = "good"
        elif ctr < 1.0 or cpa > 200:
            analysis["overall_health"] = "needs_attention"

        # Generate insights
        if ctr < 1.0:
            analysis["insights"].append("Low CTR indicates ad relevance issues")
            analysis["recommendations"].append("Improve ad text and add negative keywords")

        if cpa > 100:
            analysis["insights"].append("High CPA suggests bidding or targeting issues")
            analysis["recommendations"].append("Lower bids or refine targeting")

        return analysis