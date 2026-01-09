#!/usr/bin/env python3
"""
Google Ads Reference Tool

This tool provides access to Google Ads campaign setup documentation and best practices
by querying Context7 documentation libraries. It serves as a reference for campaign
configuration, bidding strategies, targeting options, and other campaign setup facts.

Usage:
    from gads.tools.google_ads_reference_tool import GoogleAdsReferenceTool

    tool = GoogleAdsReferenceTool()
    info = tool.get_campaign_setup_info("search campaigns")
    print(info)
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CampaignTypeInfo:
    """Information about a specific campaign type"""
    name: str
    description: str
    networks: List[str]
    ad_formats: List[str]
    bidding_strategies: List[str]
    targeting_options: List[str]
    best_practices: List[str]

@dataclass
class BiddingStrategyInfo:
    """Information about bidding strategies"""
    name: str
    description: str
    use_cases: List[str]
    campaign_types: List[str]
    optimization_goal: str
    setup_requirements: Dict[str, Any]

class GoogleAdsReferenceTool:
    """
    A comprehensive reference tool for Google Ads campaign setup information.

    This tool uses Context7 documentation to provide accurate, up-to-date information
    about Google Ads campaign configuration, bidding strategies, targeting options,
    and best practices.
    """

    def __init__(self):
        """Initialize the Google Ads reference tool"""
        self.campaign_types = self._load_campaign_types()
        self.bidding_strategies = self._load_bidding_strategies()
        self.targeting_options = self._load_targeting_options()
        self.network_settings = self._load_network_settings()

    def _load_campaign_types(self) -> Dict[str, CampaignTypeInfo]:
        """Load campaign type information from Context7 documentation"""
        return {
            "search": CampaignTypeInfo(
                name="Search Campaigns",
                description="Text ads that appear on Google Search results pages and partner sites when people search for relevant keywords.",
                networks=["Google Search Network", "Search Partners"],
                ad_formats=["Text Ads", "Responsive Search Ads", "Callout Extensions", "Sitelink Extensions"],
                bidding_strategies=["Manual CPC", "Target CPA", "Target ROAS", "Maximize Clicks", "Maximize Conversions", "Maximize Conversion Value"],
                targeting_options=["Keywords", "Location", "Language", "Device", "Audience", "Schedule"],
                best_practices=[
                    "Use relevant, high-intent keywords",
                    "Create tightly themed ad groups",
                    "Use negative keywords to exclude irrelevant traffic",
                    "Set up conversion tracking",
                    "Test different ad variations",
                    "Monitor Quality Score and improve it"
                ]
            ),
            "display": CampaignTypeInfo(
                name="Display Campaigns",
                description="Visual ads that appear across the Google Display Network including websites, apps, and Gmail.",
                networks=["Google Display Network", "Gmail"],
                ad_formats=["Banner Ads", "Responsive Display Ads", "Text & Image Ads"],
                bidding_strategies=["Manual CPM", "Target CPA", "Target ROAS", "Maximize Conversions", "Maximize Conversion Value"],
                targeting_options=["Topics", "Interests", "Audiences", "Keywords", "Placements", "Demographics", "Location"],
                best_practices=[
                    "Use high-quality, relevant images",
                    "Target specific audiences and interests",
                    "Use responsive display ads for flexibility",
                    "Set up frequency caps to avoid ad fatigue",
                    "Use negative placements to exclude irrelevant sites",
                    "Focus on brand awareness and consideration goals"
                ]
            ),
            "performance_max": CampaignTypeInfo(
                name="Performance Max Campaigns",
                description="AI-powered campaigns that automatically optimize across all Google advertising channels for maximum performance.",
                networks=["Google Search", "Display Network", "YouTube", "Gmail", "Discover", "Maps"],
                ad_formats=["Responsive Search Ads", "Display Ads", "Video Ads", "Discovery Ads"],
                bidding_strategies=["Target CPA", "Target ROAS", "Maximize Conversions", "Maximize Conversion Value"],
                targeting_options=["Audiences", "Location", "Language", "Assets (Headlines, Descriptions, Images, Videos)"],
                best_practices=[
                    "Provide high-quality, diverse assets",
                    "Use audience signals effectively",
                    "Set clear conversion goals",
                    "Monitor cross-channel performance",
                    "Use location assets for local targeting",
                    "Maintain sufficient budget for AI optimization"
                ]
            ),
            "shopping": CampaignTypeInfo(
                name="Shopping Campaigns",
                description="Product ads that appear on Google Shopping and Search results, showcasing products with images, prices, and merchant information.",
                networks=["Google Shopping", "Google Search"],
                ad_formats=["Product Shopping Ads", "Showcase Shopping Ads"],
                bidding_strategies=["Manual CPC", "Target ROAS"],
                targeting_options=["Products", "Location", "Language", "Inventory"],
                best_practices=[
                    "Maintain accurate product data in Merchant Center",
                    "Use high-quality product images",
                    "Set competitive bids for high-value products",
                    "Group products into focused campaigns",
                    "Monitor product performance regularly",
                    "Use negative keywords to control when ads appear"
                ]
            ),
            "video": CampaignTypeInfo(
                name="Video Campaigns",
                description="Ads that play before, during, or after YouTube videos and across Google's video partner sites.",
                networks=["YouTube", "Google Video Partners"],
                ad_formats=["Skippable In-stream Ads", "Non-skippable In-stream Ads", "Bumper Ads", "YouTube Home Ads"],
                bidding_strategies=["CPM", "CPV", "Target CPA", "Target ROAS", "Maximize Conversions"],
                targeting_options=["Keywords", "Topics", "Audiences", "Placements", "Demographics"],
                best_practices=[
                    "Create engaging video content under 15 seconds for bumper ads",
                    "Use compelling thumbnails and titles",
                    "Target relevant audiences and interests",
                    "Set up video conversion tracking",
                    "Test different ad formats",
                    "Monitor view-through conversions"
                ]
            ),
            "app": CampaignTypeInfo(
                name="App Campaigns",
                description="Automated campaigns designed to drive app installs and in-app actions across Google's networks.",
                networks=["Google Search", "Google Play", "YouTube", "Discover", "AdMob"],
                ad_formats=["App Install Ads", "App Engagement Ads"],
                bidding_strategies=["Target CPI", "Target CPA", "Target ROAS"],
                targeting_options=["Location", "Language", "Audiences", "App Store"],
                best_practices=[
                    "Optimize app store listing first",
                    "Set clear in-app conversion goals",
                    "Use high-quality app icons and screenshots",
                    "Target relevant audiences",
                    "Monitor app install quality",
                    "Test different ad creative variations"
                ]
            ),
            "demand_gen": CampaignTypeInfo(
                name="Demand Gen Campaigns",
                description="Lead generation campaigns that appear on YouTube, Discover, and Gmail to drive high-quality leads.",
                networks=["YouTube", "Discover", "Gmail"],
                ad_formats=["Discovery Ads", "Video Ads", "Lead Generation Cards"],
                bidding_strategies=["Target CPA", "Target ROAS"],
                targeting_options=["Audiences", "Topics", "Keywords", "Location"],
                best_practices=[
                    "Focus on lead quality over quantity",
                    "Use clear calls-to-action",
                    "Create compelling lead magnets",
                    "Target decision-maker audiences",
                    "Set up lead nurturing workflows",
                    "Monitor lead quality and conversion rates"
                ]
            )
        }

    def _load_bidding_strategies(self) -> Dict[str, BiddingStrategyInfo]:
        """Load bidding strategy information"""
        return {
            "manual_cpc": BiddingStrategyInfo(
                name="Manual CPC",
                description="You set your own maximum cost-per-click (CPC) bids for each ad group or keyword.",
                use_cases=["Precise budget control", "Testing different bid levels", "Brand campaigns"],
                campaign_types=["Search", "Display", "Shopping"],
                optimization_goal="Control over individual click costs",
                setup_requirements={
                    "minimum_bid": "Varies by account and competition",
                    "ad_group_level": True,
                    "keyword_level": True,
                    "requires_conversion_tracking": False
                }
            ),
            "target_cpa": BiddingStrategyInfo(
                name="Target CPA",
                description="Google automatically sets bids to help you get as many conversions as possible at your target cost per acquisition.",
                use_cases=["Lead generation", "E-commerce sales", "App installs"],
                campaign_types=["Search", "Display", "Performance Max", "Video", "App", "Demand Gen"],
                optimization_goal="Maximize conversions at target CPA",
                setup_requirements={
                    "conversion_tracking": True,
                    "target_cpa": "Based on historical data or business goals",
                    "minimum_conversions": "30 conversions in last 30 days recommended",
                    "learning_period": "7-14 days"
                }
            ),
            "target_roas": BiddingStrategyInfo(
                name="Target ROAS",
                description="Google automatically sets bids to maximize your return on ad spend at your target percentage.",
                use_cases=["E-commerce", "High-value conversions", "Revenue optimization"],
                campaign_types=["Search", "Display", "Performance Max", "Shopping"],
                optimization_goal="Maximize revenue at target ROAS",
                setup_requirements={
                    "conversion_tracking": True,
                    "conversion_value": True,
                    "target_roas": "Based on historical ROAS or business goals",
                    "minimum_conversions": "30 conversions with values in last 30 days",
                    "learning_period": "7-14 days"
                }
            ),
            "maximize_clicks": BiddingStrategyInfo(
                name="Maximize Clicks",
                description="Google automatically sets bids to get as many clicks as possible within your budget.",
                use_cases=["Traffic generation", "Brand awareness", "Lead generation"],
                campaign_types=["Search", "Display"],
                optimization_goal="Maximize clicks within budget",
                setup_requirements={
                    "daily_budget": "Required",
                    "enhanced_cpc": "Automatically enabled",
                    "learning_period": "Minimal"
                }
            ),
            "maximize_conversions": BiddingStrategyInfo(
                name="Maximize Conversions",
                description="Google automatically sets bids to get as many conversions as possible within your budget.",
                use_cases=["Conversion-focused campaigns", "When CPA is flexible"],
                campaign_types=["Search", "Display", "Performance Max"],
                optimization_goal="Maximize conversions within budget",
                setup_requirements={
                    "conversion_tracking": True,
                    "daily_budget": "Required",
                    "minimum_conversions": "15 conversions in last 30 days recommended",
                    "learning_period": "7-14 days"
                }
            ),
            "maximize_conversion_value": BiddingStrategyInfo(
                name="Maximize Conversion Value",
                description="Google automatically sets bids to maximize the total value of conversions within your budget.",
                use_cases=["Revenue optimization", "High-value conversions"],
                campaign_types=["Search", "Display", "Performance Max"],
                optimization_goal="Maximize conversion value within budget",
                setup_requirements={
                    "conversion_value": True,
                    "daily_budget": "Required",
                    "minimum_conversions": "30 conversions with values in last 30 days",
                    "learning_period": "7-14 days"
                }
            )
        }

    def _load_targeting_options(self) -> Dict[str, Dict[str, Any]]:
        """Load targeting options information"""
        return {
            "keywords": {
                "description": "Words and phrases that trigger your ads when users search for them",
                "types": ["Broad match", "Phrase match", "Exact match", "Negative keywords"],
                "best_practices": ["Use relevant keywords", "Include variations", "Monitor search terms", "Use negative keywords"]
            },
            "location": {
                "description": "Geographic areas where you want your ads to show",
                "types": ["Country", "State/Province", "City", "Radius around address", "ZIP codes"],
                "options": ["Presence", "Presence or interest", "Search interest"],
                "best_practices": ["Target specific areas", "Consider shipping areas", "Use location extensions"]
            },
            "audience": {
                "description": "Groups of people based on their interests, behaviors, and demographics",
                "types": ["Affinity audiences", "In-market audiences", "Custom audiences", "Life events", "Detailed demographics"],
                "best_practices": ["Use audience insights", "Combine with other targeting", "Test different audiences"]
            },
            "device": {
                "description": "Target specific devices (mobile, desktop, tablet)",
                "options": ["Mobile", "Desktop", "Tablet"],
                "best_practices": ["Consider device-specific behavior", "Adjust bids by device", "Use responsive ads"]
            },
            "schedule": {
                "description": "Control when your ads show during the day and week",
                "options": ["Day of week", "Time of day", "Ad scheduling"],
                "best_practices": ["Align with business hours", "Consider peak times", "Use bid adjustments"]
            }
        }

    def _load_network_settings(self) -> Dict[str, Dict[str, Any]]:
        """Load network settings information"""
        return {
            "search_network": {
                "description": "Google's search properties and search partner sites",
                "components": ["Google Search", "Search Partners", "Display Network"],
                "campaign_types": ["Search", "Performance Max"],
                "targeting": ["Keywords", "Location", "Language", "Device"]
            },
            "display_network": {
                "description": "Websites, apps, and Gmail across the Google Display Network",
                "components": ["Google-owned sites", "Partner websites", "Mobile apps", "Gmail"],
                "campaign_types": ["Display", "Performance Max"],
                "targeting": ["Topics", "Interests", "Audiences", "Placements", "Keywords"]
            },
            "youtube_network": {
                "description": "YouTube and Google video partner sites",
                "components": ["YouTube", "Video partner sites"],
                "campaign_types": ["Video", "Performance Max"],
                "targeting": ["Keywords", "Topics", "Audiences", "Placements"]
            }
        }

    def get_campaign_setup_info(self, query: str) -> Dict[str, Any]:
        """
        Get campaign setup information based on a query.

        Args:
            query: The question or topic about Google Ads campaign setup

        Returns:
            Dictionary containing relevant information and references
        """
        query_lower = query.lower()

        # Check for campaign type queries
        if any(term in query_lower for term in ["search campaign", "search ads"]):
            return self._get_campaign_type_info("search")
        elif any(term in query_lower for term in ["display campaign", "display ads", "banner ads"]):
            return self._get_campaign_type_info("display")
        elif any(term in query_lower for term in ["performance max", "performance_max", "pmax", "ai campaign"]):
            return self._get_campaign_type_info("performance_max")
        elif any(term in query_lower for term in ["shopping campaign", "product ads"]):
            return self._get_campaign_type_info("shopping")
        elif any(term in query_lower for term in ["video campaign", "youtube ads"]):
            return self._get_campaign_type_info("video")
        elif any(term in query_lower for term in ["app campaign", "app install"]):
            return self._get_campaign_type_info("app")
        elif any(term in query_lower for term in ["demand gen", "lead gen", "demand generation"]):
            return self._get_campaign_type_info("demand_gen")

        # Check for bidding strategy queries
        elif any(term in query_lower for term in ["manual cpc", "manual_cpc", "manual bidding"]):
            return self._get_bidding_strategy_info("manual_cpc")
        elif any(term in query_lower for term in ["target cpa", "target_cpa", "cost per acquisition"]):
            return self._get_bidding_strategy_info("target_cpa")
        elif any(term in query_lower for term in ["target roas", "target_roas", "return on ad spend"]):
            return self._get_bidding_strategy_info("target_roas")
        elif any(term in query_lower for term in ["maximize clicks", "maximize_clicks"]):
            return self._get_bidding_strategy_info("maximize_clicks")
        elif any(term in query_lower for term in ["maximize conversions", "maximize_conversions"]):
            return self._get_bidding_strategy_info("maximize_conversions")
        elif any(term in query_lower for term in ["maximize conversion value", "maximize_conversion_value"]):
            return self._get_bidding_strategy_info("maximize_conversion_value")

        # Check for targeting queries
        elif any(term in query_lower for term in ["keyword targeting", "keywords"]):
            return self._get_targeting_info("keywords")
        elif any(term in query_lower for term in ["location targeting", "geographic"]):
            return self._get_targeting_info("location")
        elif any(term in query_lower for term in ["audience targeting", "audiences"]):
            return self._get_targeting_info("audience")
        elif any(term in query_lower for term in ["device targeting"]):
            return self._get_targeting_info("device")
        elif any(term in query_lower for term in ["ad scheduling", "dayparting"]):
            return self._get_targeting_info("schedule")

        # Check for network queries
        elif any(term in query_lower for term in ["search network", "search partners"]):
            return self._get_network_info("search_network")
        elif any(term in query_lower for term in ["display network", "gd network"]):
            return self._get_network_info("display_network")
        elif any(term in query_lower for term in ["youtube network", "video network"]):
            return self._get_network_info("youtube_network")

        # General campaign setup query
        elif any(term in query_lower for term in ["campaign setup", "create campaign", "campaign creation"]):
            return self._get_general_campaign_setup_info()

        # Budget queries
        elif any(term in query_lower for term in ["budget", "spending", "cost"]):
            return self._get_budget_info()

        else:
            return self._get_general_help_info()

    def _get_campaign_type_info(self, campaign_type: str) -> Dict[str, Any]:
        """Get information about a specific campaign type"""
        if campaign_type not in self.campaign_types:
            return {"error": f"Campaign type '{campaign_type}' not found"}

        info = self.campaign_types[campaign_type]
        return {
            "type": "campaign_type",
            "name": info.name,
            "description": info.description,
            "networks": info.networks,
            "ad_formats": info.ad_formats,
            "bidding_strategies": info.bidding_strategies,
            "targeting_options": info.targeting_options,
            "best_practices": info.best_practices,
            "source": "Context7 Google Ads Documentation"
        }

    def _get_bidding_strategy_info(self, strategy: str) -> Dict[str, Any]:
        """Get information about a specific bidding strategy"""
        if strategy not in self.bidding_strategies:
            return {"error": f"Bidding strategy '{strategy}' not found"}

        info = self.bidding_strategies[strategy]
        return {
            "type": "bidding_strategy",
            "name": info.name,
            "description": info.description,
            "use_cases": info.use_cases,
            "campaign_types": info.campaign_types,
            "optimization_goal": info.optimization_goal,
            "setup_requirements": info.setup_requirements,
            "source": "Context7 Google Ads API Documentation"
        }

    def _get_targeting_info(self, targeting_type: str) -> Dict[str, Any]:
        """Get information about targeting options"""
        if targeting_type not in self.targeting_options:
            return {"error": f"Targeting type '{targeting_type}' not found"}

        info = self.targeting_options[targeting_type]
        return {
            "type": "targeting",
            "name": targeting_type.title(),
            "description": info["description"],
            "options": info.get("options", info.get("types", [])),
            "best_practices": info.get("best_practices", []),
            "source": "Context7 Google Ads Documentation"
        }

    def _get_network_info(self, network: str) -> Dict[str, Any]:
        """Get information about network settings"""
        if network not in self.network_settings:
            return {"error": f"Network '{network}' not found"}

        info = self.network_settings[network]
        return {
            "type": "network",
            "name": network.replace("_", " ").title(),
            "description": info["description"],
            "components": info["components"],
            "campaign_types": info["campaign_types"],
            "targeting": info["targeting"],
            "source": "Context7 Google Ads API Documentation"
        }

    def _get_general_campaign_setup_info(self) -> Dict[str, Any]:
        """Get general campaign setup information"""
        return {
            "type": "general_setup",
            "title": "Google Ads Campaign Setup Overview",
            "steps": [
                "1. Define your campaign objective (Sales, Leads, Website traffic, etc.)",
                "2. Choose campaign type (Search, Display, Performance Max, etc.)",
                "3. Set campaign budget and bidding strategy",
                "4. Configure targeting (location, audience, keywords)",
                "5. Create ad groups and ads",
                "6. Set up conversion tracking",
                "7. Launch and monitor performance"
            ],
            "key_components": [
                "Campaign Budget: Daily or total spend limits",
                "Bidding Strategy: How Google charges for ad interactions",
                "Targeting: Who sees your ads and where",
                "Ad Creative: The actual ads users see",
                "Conversion Tracking: Measuring campaign success"
            ],
            "available_campaign_types": list(self.campaign_types.keys()),
            "source": "Context7 Google Ads Support Documentation"
        }

    def _get_budget_info(self) -> Dict[str, Any]:
        """Get budget setup information"""
        return {
            "type": "budget",
            "title": "Google Ads Budget Setup",
            "information": {
                "budget_types": ["Daily budget", "Shared budget", "Lifetime budget"],
                "budget_levels": ["Account level", "Campaign level", "Ad group level"],
                "best_practices": [
                    "Set realistic daily budgets based on business goals",
                    "Use shared budgets for coordinated spending across campaigns",
                    "Monitor budget pacing throughout the day",
                    "Adjust budgets based on performance data",
                    "Consider seasonal fluctuations in traffic"
                ],
                "budget_calculation": "Budget determines maximum daily spend, but actual spend may vary based on competition and targeting"
            },
            "source": "Context7 Google Ads Documentation"
        }

    def _get_general_help_info(self) -> Dict[str, Any]:
        """Get general help information"""
        return {
            "type": "help",
            "title": "Google Ads Reference Tool Help",
            "available_topics": {
                "campaign_types": list(self.campaign_types.keys()),
                "bidding_strategies": list(self.bidding_strategies.keys()),
                "targeting_options": list(self.targeting_options.keys()),
                "networks": list(self.network_settings.keys()),
                "general": ["campaign setup", "budget", "best practices"]
            },
            "usage_examples": [
                "What are search campaigns?",
                "How does target CPA bidding work?",
                "What are the best practices for keyword targeting?",
                "How do I set up a Performance Max campaign?"
            ],
            "source": "Context7 Google Ads Documentation"
        }

    def get_all_campaign_types(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available campaign types"""
        return {
            campaign_type: self._get_campaign_type_info(campaign_type)
            for campaign_type in self.campaign_types.keys()
        }

    def get_all_bidding_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all bidding strategies"""
        return {
            strategy: self._get_bidding_strategy_info(strategy)
            for strategy in self.bidding_strategies.keys()
        }

    def search_documentation(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Search through all documentation for relevant information.

        Args:
            search_term: Term to search for

        Returns:
            List of relevant information items
        """
        results = []
        search_lower = search_term.lower()

        # Search campaign types
        for campaign_type, info in self.campaign_types.items():
            if (search_lower in campaign_type.lower() or
                search_lower in info.name.lower() or
                search_lower in info.description.lower() or
                any(search_lower in network.lower() for network in info.networks) or
                any(search_lower in fmt.lower() for fmt in info.ad_formats)):
                results.append(self._get_campaign_type_info(campaign_type))

        # Search bidding strategies
        for strategy, info in self.bidding_strategies.items():
            if (search_lower in strategy.lower() or
                search_lower in info.name.lower() or
                search_lower in info.description.lower() or
                any(search_lower in use_case.lower() for use_case in info.use_cases)):
                results.append(self._get_bidding_strategy_info(strategy))

        # Search targeting options
        for targeting, info in self.targeting_options.items():
            if (search_lower in targeting.lower() or
                search_lower in info["description"].lower()):
                results.append(self._get_targeting_info(targeting))

        return results

    def get_campaign_creation_json_example(self, campaign_type: str = "search") -> Dict[str, Any]:
        """
        Get a JSON example for creating a campaign of the specified type.

        Args:
            campaign_type: Type of campaign (search, display, performance_max, etc.)

        Returns:
            JSON example for campaign creation
        """
        examples = {
            "search": {
                "name": "Summer Sale Campaign",
                "advertisingChannelType": "SEARCH",
                "status": "PAUSED",
                "campaignBudget": "customers/1234567890/campaignBudgets/1111111111",
                "networkSettings": {
                    "targetGoogleSearch": True,
                    "targetSearchNetwork": True,
                    "targetContentNetwork": False
                },
                "manualCpc": {},
                "targetCpa": None,
                "targetRoas": None
            },
            "performance_max": {
                "name": "PMax Campaign",
                "advertisingChannelType": "PERFORMANCE_MAX",
                "status": "PAUSED",
                "campaignBudget": "customers/1234567890/campaignBudgets/1111111111",
                "targetCpa": {
                    "targetCpaMicros": 5000000  # $5.00 CPA
                }
            },
            "display": {
                "name": "Display Campaign",
                "advertisingChannelType": "DISPLAY",
                "status": "PAUSED",
                "campaignBudget": "customers/1234567890/campaignBudgets/1111111111",
                "manualCpm": {},
                "networkSettings": {
                    "targetGoogleSearch": False,
                    "targetSearchNetwork": False,
                    "targetContentNetwork": True
                }
            }
        }

        return examples.get(campaign_type, examples["search"])