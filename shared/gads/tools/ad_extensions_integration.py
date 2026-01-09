#!/usr/bin/env python3
"""
Ad Extensions Integration Module

This module integrates the Ad Extensions Management System with existing Google Ads
campaign planning and management workflows.
"""

import sys
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add the gads directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ad_extensions_management_system import AdExtensionsManagementSystem, ExtensionAsset, ExtensionType
import logging

logger = logging.getLogger('ad_extensions_integration')

class AdExtensionsCampaignIntegrator:
    """
    Integrates ad extensions management with campaign planning workflows.

    This class provides methods to automatically generate, validate, and optimize
    ad extensions for campaigns and ad groups based on business type and campaign goals.
    """

    def __init__(self):
        """Initialize the ad extensions campaign integrator"""
        self.ext_system = AdExtensionsManagementSystem()

    def generate_extensions_for_campaign(self, campaign_config: Dict[str, Any],
                                       ad_groups: List[Dict[str, Any]] = None) -> Dict[str, List[ExtensionAsset]]:
        """
        Generate comprehensive extensions for a campaign.

        Args:
            campaign_config: Campaign configuration
            ad_groups: List of ad group configurations (optional)

        Returns:
            Extensions organized by type
        """
        logger.info(f"Generating extensions for campaign: {campaign_config.get('name', 'Unknown')}")

        # Extract business information from campaign
        business_info = self._extract_business_info_from_campaign(campaign_config, ad_groups)

        # Determine business type
        business_type = self._determine_business_type(campaign_config, business_info)

        # Select appropriate extension types
        extension_types = self._select_extension_types(campaign_config, business_type)

        # Generate extensions
        extensions = self.ext_system.generate_campaign_extensions(
            business_type=business_type,
            business_info=business_info,
            extension_types=extension_types
        )

        return extensions

    def _extract_business_info_from_campaign(self, campaign_config: Dict[str, Any],
                                           ad_groups: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract business information from campaign configuration"""
        business_info = {
            "name": campaign_config.get("brand_business_name", ""),
            "website": campaign_config.get("website", ""),
            "phone": campaign_config.get("phone", ""),
            "type": campaign_config.get("business_type", "general"),
            "address": campaign_config.get("address", {}),
            "services": [],
            "certifications": [],
            "years_experience": campaign_config.get("years_experience"),
            "app_id": campaign_config.get("app_id"),
            "app_store": campaign_config.get("app_store"),
            "reviews": campaign_config.get("reviews", []),
            "lead_form_enabled": campaign_config.get("lead_form_enabled", False)
        }

        # Extract services from ad groups or campaign
        if ad_groups:
            for ag in ad_groups:
                ag_name = ag.get("name", "").lower()
                if "executive" in ag_name:
                    business_info["services"].append("Executive Resume Services")
                elif "professional" in ag_name:
                    business_info["services"].append("Professional Resume Services")
                elif "career" in ag_name:
                    business_info["services"].append("Career Development Services")

        # Extract from campaign callouts if available
        callouts = campaign_config.get("callouts", [])
        for callout in callouts:
            if "years" in callout.lower():
                business_info["certifications"].append("Experienced Professional")
            elif "certified" in callout.lower():
                business_info["certifications"].append("Certified")

        return business_info

    def _determine_business_type(self, campaign_config: Dict[str, Any], business_info: Dict[str, Any]) -> str:
        """Determine the business type from campaign information"""
        campaign_name = campaign_config.get("name", "").lower()
        business_name = business_info.get("name", "").lower()

        # Check for keywords indicating business type
        if any(word in campaign_name or word in business_name for word in ["resume", "cv", "career"]):
            return "professional_services"
        elif any(word in campaign_name for word in ["shop", "store", "ecommerce"]):
            return "ecommerce"
        elif any(word in campaign_name for word in ["restaurant", "food", "dining"]):
            return "local_business"
        elif any(word in campaign_name for word in ["doctor", "medical", "health"]):
            return "healthcare"
        elif any(word in campaign_name for word in ["school", "education", "training"]):
            return "education"
        elif any(word in campaign_name for word in ["real estate", "property", "homes"]):
            return "real_estate"
        else:
            return "professional_services"  # Default

    def _select_extension_types(self, campaign_config: Dict[str, Any], business_type: str) -> List[str]:
        """Select appropriate extension types for the campaign"""
        base_types = ["sitelink", "callout"]  # Always include these

        campaign_objective = campaign_config.get("objective", "").lower()
        campaign_type = campaign_config.get("type", "").lower()

        additional_types = []

        # Add call extensions for campaigns that likely need phone contact
        if business_type in ["professional_services", "local_business", "healthcare", "real_estate"]:
            additional_types.append("call")

        # Add location extensions for local businesses
        if business_type == "local_business" or campaign_config.get("location_targeting"):
            additional_types.append("location")

        # Add structured snippets for service-based businesses
        if business_type in ["professional_services", "education"]:
            additional_types.append("structured_snippet")

        # Add promotions for ecommerce
        if business_type == "ecommerce" or "promotion" in campaign_config:
            additional_types.append("promotion")

        # Add app extensions if app info is available
        if campaign_config.get("app_id"):
            additional_types.append("app")

        # Add review extensions if reviews are available
        if campaign_config.get("reviews"):
            additional_types.append("review")

        # Add message extensions for businesses that might use texting
        if business_type in ["local_business", "professional_services"]:
            additional_types.append("message")

        # Add lead forms for high-intent campaigns
        if campaign_objective in ["leads", "conversions"] or campaign_config.get("lead_form_enabled"):
            additional_types.append("lead_form")

        return base_types + additional_types

    def validate_campaign_extensions(self, extensions: Dict[str, List[ExtensionAsset]],
                                   campaign_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extensions for campaign compatibility and best practices.

        Args:
            extensions: Extensions to validate
            campaign_config: Campaign configuration

        Returns:
            Validation results
        """
        validation = self.ext_system.validate_extensions(extensions)

        # Add campaign-specific validation
        campaign_type = campaign_config.get("type", "").lower()

        # Search campaigns should have relevant extensions
        if campaign_type == "search":
            sitelinks = extensions.get("sitelink", [])
            callouts = extensions.get("callout", [])

            if len(sitelinks) == 0:
                validation["warnings"].append("Search campaigns benefit from sitelink extensions")

            if len(callouts) == 0:
                validation["warnings"].append("Consider adding callout extensions to search campaigns")

        # Performance Max campaigns work well with various extensions
        elif campaign_type == "performance_max":
            total_extensions = sum(len(ext_list) for ext_list in extensions.values())
            if total_extensions < 5:
                validation["recommendations"] = validation.get("recommendations", [])
                validation["recommendations"].append("Performance Max campaigns can use multiple extension types")

        # Check for business info consistency
        business_name = campaign_config.get("brand_business_name", "")
        if business_name:
            for ext_type, ext_list in extensions.items():
                for ext in ext_list:
                    if hasattr(ext, 'business_name') and ext.business_name != business_name:
                        validation["warnings"].append(
                            f"Extension '{ext.name}' business name doesn't match campaign brand name"
                        )

        return validation

    def optimize_campaign_extensions(self, extensions: Dict[str, List[ExtensionAsset]],
                                   performance_data: Dict[str, Dict[str, Any]],
                                   campaign_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize extensions for the entire campaign based on performance.

        Args:
            extensions: Campaign extensions
            performance_data: Performance data by extension
            campaign_config: Campaign configuration

        Returns:
            Optimization recommendations
        """
        logger.info("Optimizing campaign extensions")

        # Get base optimization from extension system
        optimization = self.ext_system.optimize_extensions_performance(extensions, performance_data)

        # Add campaign-specific optimization
        campaign_type = campaign_config.get("type", "").lower()
        campaign_objective = campaign_config.get("objective", "").lower()

        # Campaign type specific recommendations
        if campaign_type == "search":
            # Ensure search campaigns have click-worthy extensions
            sitelink_performance = self._analyze_extension_type_performance(extensions, performance_data, "sitelink")
            if sitelink_performance["avg_ctr"] < 0.5:
                optimization.priority_actions.append(
                    "Search campaign sitelinks have low CTR - consider more compelling link text"
                )

        elif campaign_type == "performance_max":
            # Performance Max can handle more extension variety
            total_extensions = sum(len(ext_list) for ext_list in extensions.values())
            if total_extensions < 8:
                optimization.new_extensions_suggestions.append({
                    "type": "performance_max_expansion",
                    "suggestion": "Consider adding more extension types for Performance Max optimization"
                })

        # Objective-specific recommendations
        if campaign_objective == "conversions":
            call_extensions = extensions.get("call", [])
            lead_forms = extensions.get("lead_form", [])

            if not call_extensions and not lead_forms:
                optimization.priority_actions.append(
                    "Conversion-focused campaign should consider call or lead form extensions"
                )

        elif campaign_objective in ["awareness", "consideration"]:
            callouts = extensions.get("callout", [])
            if len(callouts) < 5:
                optimization.new_extensions_suggestions.append({
                    "type": "awareness_callouts",
                    "suggestion": "Consider adding more callout extensions for awareness campaigns"
                })

        return optimization

    def _analyze_extension_type_performance(self, extensions: Dict[str, List[ExtensionAsset]],
                                          performance_data: Dict[str, Dict[str, Any]],
                                          extension_type: str) -> Dict[str, float]:
        """Analyze performance for a specific extension type"""
        ext_list = extensions.get(extension_type, [])
        if not ext_list:
            return {"avg_ctr": 0, "total_clicks": 0, "total_impressions": 0}

        total_clicks = 0
        total_impressions = 0

        for ext in ext_list:
            perf = performance_data.get(ext.name, {})
            total_clicks += perf.get('clicks', 0)
            total_impressions += perf.get('impressions', 0)

        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0

        return {
            "avg_ctr": avg_ctr,
            "total_clicks": total_clicks,
            "total_impressions": total_impressions
        }

    def balance_extensions_across_campaign(self, extensions: Dict[str, List[ExtensionAsset]],
                                         campaign_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze and recommend balancing extensions across campaign ad groups.

        Args:
            extensions: Campaign extensions
            campaign_config: Campaign configuration

        Returns:
            Balance analysis and recommendations
        """
        analysis = {
            "distribution": {},
            "imbalance_issues": [],
            "recommendations": []
        }

        # Count extensions by type
        for ext_type, ext_list in extensions.items():
            active_extensions = [ext for ext in ext_list if ext.status == "ENABLED"]
            analysis["distribution"][ext_type] = {
                "total": len(ext_list),
                "active": len(active_extensions)
            }

        # Check for imbalances
        total_extensions = sum(dist["active"] for dist in analysis["distribution"].values())

        # Too few extensions overall
        if total_extensions < 4:
            analysis["imbalance_issues"].append("Campaign has very few extensions - consider adding more types")
            analysis["recommendations"].append("Add at least 4-6 extensions for good campaign coverage")

        # Missing key extension types
        campaign_type = campaign_config.get("type", "").lower()
        if campaign_type == "search" and "sitelink" not in analysis["distribution"]:
            analysis["imbalance_issues"].append("Search campaigns should include sitelink extensions")
            analysis["recommendations"].append("Add sitelink extensions for better search campaign performance")

        # Too many of one type
        for ext_type, dist in analysis["distribution"].items():
            if dist["active"] > total_extensions * 0.6:  # More than 60% of extensions
                analysis["imbalance_issues"].append(f"Too many {ext_type} extensions relative to other types")
                analysis["recommendations"].append(f"Balance {ext_type} extensions with other extension types")

        return analysis

    def export_extensions_to_campaign_csv(self, extensions: Dict[str, List[ExtensionAsset]],
                                        campaign_config: Dict[str, Any]) -> str:
        """
        Export all campaign extensions to a single CSV file.

        Args:
            extensions: Extensions organized by type
            campaign_config: Campaign configuration

        Returns:
            CSV content as string
        """
        campaign_name = campaign_config.get("name", "Campaign")

        return self.ext_system.export_extensions_to_csv(extensions, campaign_name)

    def create_extension_performance_report(self, extensions: Dict[str, List[ExtensionAsset]],
                                          performance_data: Dict[str, Dict[str, Any]],
                                          campaign_config: Dict[str, Any]) -> str:
        """
        Create a comprehensive performance report for extensions.

        Args:
            extensions: Campaign extensions
            performance_data: Performance data
            campaign_config: Campaign configuration

        Returns:
            Formatted performance report
        """
        dashboard = self.ext_system.create_extension_performance_dashboard(extensions, performance_data)

        report_lines = [
            "=" * 60,
            "AD EXTENSIONS PERFORMANCE REPORT",
            "=" * 60,
            f"Campaign: {campaign_config.get('name', 'Unknown')}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "SUMMARY:",
            f"  • Total Extensions: {dashboard['summary']['total_extensions']}",
            f"  • Active Extensions: {dashboard['summary']['active_extensions']}",
            f"  • Extension Types: {dashboard['summary']['extension_types']}",
            ""
        ]

        # Performance summary
        perf = dashboard.get('performance_summary', {})
        if perf:
            report_lines.extend([
                "PERFORMANCE SUMMARY:",
                f"  • Total Impressions: {perf.get('total_impressions', 0):,}",
                f"  • Total Clicks: {perf.get('total_clicks', 0):,}",
                f"  • Total Cost: ${perf.get('total_cost', 0):,.2f}",
                f"  • Total Conversions: {perf.get('total_conversions', 0)}",
                f"  • Average CTR: {perf.get('average_ctr', 0):.2f}%",
                f"  • Average CPA: ${perf.get('average_cpa', 0):.2f}",
                ""
            ])

        # Top performers
        if dashboard.get('top_performers'):
            report_lines.append("TOP PERFORMING EXTENSIONS:")
            for i, perf in enumerate(dashboard['top_performers'][:5], 1):
                report_lines.append(f"  {i}. {perf['name']} - {perf['clicks']} clicks")
            report_lines.append("")

        # Underperformers
        if dashboard.get('underperformers'):
            report_lines.append("UNDERPERFORMING EXTENSIONS:")
            for i, perf in enumerate(dashboard['underperformers'][:5], 1):
                report_lines.append(f"  {i}. {perf['name']} - {perf['clicks']} clicks, {perf['impressions']} impressions")
            report_lines.append("")

        # Insights
        if dashboard.get('insights'):
            report_lines.append("KEY INSIGHTS:")
            for insight in dashboard['insights']:
                report_lines.append(f"  • {insight}")
            report_lines.append("")

        # Recommendations
        if dashboard.get('recommendations'):
            report_lines.append("RECOMMENDATIONS:")
            for rec in dashboard['recommendations']:
                report_lines.append(f"  • {rec}")
            report_lines.append("")

        report_lines.append("=" * 60)

        return "\n".join(report_lines)

    def get_campaign_extension_strategy(self, campaign_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Develop a comprehensive extension strategy for a campaign.

        Args:
            campaign_config: Campaign configuration

        Returns:
            Extension strategy with recommendations
        """
        strategy = {
            "campaign_type": campaign_config.get("type", "SEARCH"),
            "objective": campaign_config.get("objective", "conversions"),
            "recommended_extensions": [],
            "priority_order": [],
            "implementation_phases": [],
            "expected_impact": {}
        }

        campaign_type = campaign_config.get("type", "").lower()
        objective = campaign_config.get("objective", "").lower()

        # Base recommendations
        if campaign_type == "search":
            strategy["recommended_extensions"] = ["sitelink", "callout", "call", "structured_snippet"]
            strategy["priority_order"] = ["sitelink", "callout", "call", "structured_snippet"]
            strategy["expected_impact"] = {
                "sitelink": "10-20% CTR increase",
                "callout": "5-15% CTR increase",
                "call": "Direct conversions",
                "structured_snippet": "Improved relevance"
            }

        elif campaign_type == "performance_max":
            strategy["recommended_extensions"] = ["sitelink", "callout", "call", "location", "promotion", "app"]
            strategy["priority_order"] = ["sitelink", "callout", "location", "call", "promotion"]
            strategy["expected_impact"] = {
                "sitelink": "Cross-network performance",
                "callout": "Ad relevance boost",
                "location": "Local search improvement",
                "call": "Direct response channel",
                "promotion": "Conversion acceleration"
            }

        # Objective-specific adjustments
        if objective == "conversions":
            strategy["priority_order"] = ["call", "sitelink", "callout"] + [x for x in strategy["priority_order"] if x not in ["call", "sitelink", "callout"]]
            strategy["implementation_phases"] = [
                "Phase 1: Call and lead generation extensions",
                "Phase 2: Navigation and trust-building extensions",
                "Phase 3: Awareness and consideration extensions"
            ]

        elif objective in ["awareness", "consideration"]:
            strategy["implementation_phases"] = [
                "Phase 1: Brand and awareness extensions",
                "Phase 2: Engagement and interaction extensions",
                "Phase 3: Conversion and action extensions"
            ]

        return strategy

    def validate_extension_compatibility(self, extensions: Dict[str, List[ExtensionAsset]],
                                       campaign_config: Dict[str, Any],
                                       ad_groups: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate extension compatibility with campaign and ad group settings.

        Args:
            extensions: Extensions to validate
            campaign_config: Campaign configuration
            ad_groups: Ad group configurations

        Returns:
            Compatibility validation results
        """
        compatibility = {
            "is_compatible": True,
            "issues": [],
            "warnings": [],
            "recommendations": []
        }

        campaign_type = campaign_config.get("type", "").lower()

        # Check extension type compatibility with campaign type
        incompatible_combinations = {
            "search": [],  # All extensions work with search
            "display": ["call"],  # Call extensions don't work with display
            "shopping": ["call", "location", "structured_snippet"],  # Limited extensions for shopping
            "video": ["structured_snippet", "location"],  # Limited for video
            "app": ["location", "call"],  # Limited for app campaigns
        }

        incompatible_types = incompatible_combinations.get(campaign_type, [])
        for ext_type in extensions.keys():
            if ext_type in incompatible_types:
                compatibility["issues"].append(
                    f"{ext_type.title()} extensions are not compatible with {campaign_type.title()} campaigns"
                )
                compatibility["is_compatible"] = False

        # Check for business information requirements
        business_info_required = {
            "location": ["address"],
            "call": ["phone"],
            "app": ["app_id"],
            "review": ["reviews"]
        }

        for ext_type, required_fields in business_info_required.items():
            if ext_type in extensions:
                for field in required_fields:
                    if not campaign_config.get(field):
                        compatibility["warnings"].append(
                            f"{ext_type.title()} extensions require {field} information"
                        )

        # Check ad group compatibility
        if ad_groups:
            for ad_group in ad_groups:
                ag_type = ad_group.get("type", "").lower()
                if ag_type == "shopping_product_ads":
                    shopping_incompatible = ["call", "location", "structured_snippet"]
                    for ext_type in extensions.keys():
                        if ext_type in shopping_incompatible:
                            compatibility["issues"].append(
                                f"{ext_type.title()} extensions incompatible with shopping ad groups"
                            )
                            compatibility["is_compatible"] = False

        return compatibility