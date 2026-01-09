#!/usr/bin/env python3
"""
Ad Group Integration Module

This module integrates the Ad Group Management System with existing Google Ads
campaign planning and management workflows.
"""

import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add the gads directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from google_ads_reference_tool import GoogleAdsReferenceTool
from ad_group_management_system import AdGroupManagementSystem
from google_ads_agent.utils.logging_utils import get_logger

logger = get_logger('ad_group_integration')

class AdGroupCampaignIntegrator:
    """
    Integrates ad group management with campaign planning workflows.

    This class provides methods to automatically generate ad groups for campaigns,
    validate ad group configurations against campaign objectives, and optimize
    ad group performance within the context of overall campaign goals.
    """

    def __init__(self):
        """Initialize the ad group campaign integrator"""
        self.reference_tool = GoogleAdsReferenceTool()
        self.ag_system = AdGroupManagementSystem()

    def generate_ad_groups_for_campaign(self, campaign_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate optimized ad groups for a campaign based on its configuration.

        Args:
            campaign_config: Campaign configuration dictionary

        Returns:
            List of optimized ad group configurations
        """
        logger.info(f"Generating ad groups for campaign: {campaign_config.get('name', 'Unknown')}")

        ad_groups = []
        campaign_type = campaign_config.get('type', 'SEARCH')
        campaign_objective = campaign_config.get('objective', 'conversions')

        # Get campaign reference information
        campaign_ref = self.reference_tool.get_campaign_setup_info(f"{campaign_type.lower()} campaigns")

        # Extract key themes from campaign
        themes = self._extract_campaign_themes(campaign_config)

        # Generate ad groups for each theme
        for theme in themes:
            ad_group_config = self.ag_system.create_optimized_ad_group(
                theme=theme,
                campaign_type=campaign_type,
                target_audience=campaign_config.get('target_audience'),
                geo_targeting=campaign_config.get('geo_targeting'),
                budget_micros=campaign_config.get('budget_micros')
            )

            # Validate ad group against campaign objectives
            validation = self._validate_ad_group_against_campaign(ad_group_config, campaign_config)
            ad_group_config['campaign_validation'] = validation

            ad_groups.append(ad_group_config)

        # Add complementary ad groups based on campaign objective
        complementary_groups = self._generate_complementary_ad_groups(campaign_config, themes)
        ad_groups.extend(complementary_groups)

        return ad_groups

    def _extract_campaign_themes(self, campaign_config: Dict[str, Any]) -> List[str]:
        """Extract key themes from campaign configuration"""
        themes = []

        # From campaign name
        name = campaign_config.get('name', '').lower()
        if 'executive' in name or 'professional' in name:
            themes.append('Executive Resume Services')
        if 'resume' in name:
            themes.append('Resume Writing Services')
        if 'career' in name:
            themes.append('Career Development Services')

        # From asset groups (for Performance Max campaigns)
        asset_groups = campaign_config.get('asset_groups', [])
        for ag in asset_groups:
            if 'name' in ag:
                ag_name = ag['name'].lower()
                if 'executive' in ag_name:
                    themes.append('Executive Level Services')
                elif 'career' in ag_name:
                    themes.append('Career Advancement Services')

        # Default themes if none found
        if not themes:
            themes = ['Professional Services', 'Business Solutions', 'Expert Services']

        return list(set(themes))  # Remove duplicates

    def _validate_ad_group_against_campaign(self, ad_group_config: Dict[str, Any],
                                          campaign_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ad group configuration against campaign objectives"""
        validation = {
            "is_compatible": True,
            "warnings": [],
            "alignment_score": 0.8  # Default good alignment
        }

        campaign_type = campaign_config.get('type', 'SEARCH')
        ad_group_type = ad_group_config.get('type', 'SEARCH_STANDARD')

        # Check campaign type compatibility
        compatible_types = {
            'SEARCH': ['SEARCH_STANDARD', 'SEARCH_DYNAMIC'],
            'DISPLAY': ['DISPLAY_STANDARD'],
            'PERFORMANCE_MAX': ['SEARCH_STANDARD', 'DISPLAY_STANDARD'],
            'SHOPPING': ['SHOPPING_PRODUCT_ADS']
        }

        if campaign_type.upper() in compatible_types:
            if ad_group_type not in compatible_types[campaign_type.upper()]:
                validation["warnings"].append(
                    f"Ad group type {ad_group_type} may not be optimal for {campaign_type} campaigns"
                )
                validation["alignment_score"] -= 0.2

        # Check bidding strategy alignment
        campaign_bid_strategy = campaign_config.get('bid_strategy_type', '').lower()
        ad_group_settings = ad_group_config.get('settings', {})

        if 'target cpa' in campaign_bid_strategy and not ad_group_settings.get('target_cpa_micros'):
            validation["warnings"].append(
                "Campaign uses Target CPA but ad group doesn't have CPA targeting configured"
            )
            validation["alignment_score"] -= 0.1

        return validation

    def _generate_complementary_ad_groups(self, campaign_config: Dict[str, Any],
                                        existing_themes: List[str]) -> List[Dict[str, Any]]:
        """Generate complementary ad groups to fill coverage gaps"""
        complementary_groups = []
        campaign_type = campaign_config.get('type', 'SEARCH')

        # For search campaigns, add branded ad groups if not present
        if campaign_type.upper() == 'SEARCH':
            branded_terms = ['brand', 'company name', 'branded']
            has_branded = any(any(term in theme.lower() for term in branded_terms)
                             for theme in existing_themes)

            if not has_branded and campaign_config.get('brand_business_name'):
                branded_group = self.ag_system.create_optimized_ad_group(
                    theme=f"{campaign_config['brand_business_name']} Branded",
                    campaign_type=campaign_type,
                    target_audience='brand_searchers'
                )
                complementary_groups.append(branded_group)

        # Add competitor ad groups for competitive campaigns
        if campaign_config.get('competitive_industry'):
            competitor_group = self.ag_system.create_optimized_ad_group(
                theme='Competitor Comparison',
                campaign_type=campaign_type,
                target_audience='comparison_shoppers'
            )
            complementary_groups.append(competitor_group)

        return complementary_groups

    def optimize_campaign_ad_groups(self, campaign_config: Dict[str, Any],
                                  ad_groups: List[Dict[str, Any]],
                                  performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize ad groups within the context of overall campaign performance.

        Args:
            campaign_config: Campaign configuration
            ad_groups: List of ad group configurations
            performance_data: Campaign-level performance data

        Returns:
            Optimization recommendations for the campaign and ad groups
        """
        logger.info("Optimizing campaign ad groups")

        optimization_results = {
            "campaign_level_optimization": {},
            "ad_group_optimizations": [],
            "resource_allocation_recommendations": [],
            "new_ad_group_suggestions": []
        }

        # Analyze campaign-level performance
        campaign_performance = self._analyze_campaign_performance(performance_data)
        optimization_results["campaign_level_optimization"] = campaign_performance

        # Optimize individual ad groups
        for ad_group in ad_groups:
            ag_performance = performance_data.get('ad_group_performance', {}).get(ad_group['name'], {})
            ag_optimization = self.ag_system.optimize_ad_group(ad_group, ag_performance)
            optimization_results["ad_group_optimizations"].append({
                "ad_group_name": ad_group["name"],
                "optimization": ag_optimization
            })

        # Check for ad group gaps
        gaps = self._identify_ad_group_gaps(campaign_config, ad_groups, performance_data)
        optimization_results["new_ad_group_suggestions"] = gaps

        # Resource allocation recommendations
        allocation = self._recommend_resource_allocation(ad_groups, performance_data)
        optimization_results["resource_allocation_recommendations"] = allocation

        return optimization_results

    def _analyze_campaign_performance(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall campaign performance"""
        analysis = {
            "overall_health": "good",
            "key_insights": [],
            "recommendations": []
        }

        ctr = performance_data.get('ctr', 0)
        cpa = performance_data.get('cpa', 0)
        roas = performance_data.get('roas', 0)

        if ctr < 1.5:
            analysis["key_insights"].append("Low CTR across campaign indicates relevance issues")
            analysis["recommendations"].append("Review ad text and keyword relevance")
            analysis["overall_health"] = "needs_attention"

        if cpa > 100:
            analysis["key_insights"].append("CPA is above industry average")
            analysis["recommendations"].append("Consider bid adjustments or negative keywords")

        if roas < 2.0 and roas > 0:
            analysis["key_insights"].append("ROAS could be improved")
            analysis["recommendations"].append("Focus on high-converting keywords and audiences")

        return analysis

    def _identify_ad_group_gaps(self, campaign_config: Dict[str, Any],
                              ad_groups: List[Dict[str, Any]],
                              performance_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify gaps where new ad groups could improve performance"""
        gaps = []

        # Check for high-performing search terms not covered by existing ad groups
        search_terms = performance_data.get('search_terms_report', [])
        high_performing_terms = [
            term for term in search_terms
            if term.get('conversions', 0) > 5 and term.get('cpa', 0) < 50
        ]

        existing_keywords = set()
        for ag in ad_groups:
            for kw in ag.get('keywords', []):
                existing_keywords.add(kw['text'].strip('"').lower())

        uncovered_terms = [
            term for term in high_performing_terms
            if term['text'].lower() not in existing_keywords
        ]

        if uncovered_terms:
            gaps.append({
                "type": "high_performing_search_terms",
                "description": f"Found {len(uncovered_terms)} high-performing search terms not covered by existing ad groups",
                "suggested_terms": [term['text'] for term in uncovered_terms[:5]],
                "potential_impact": "high"
            })

        # Check for audience expansion opportunities
        if performance_data.get('audience_performance'):
            underperforming_audiences = [
                audience for audience in performance_data['audience_performance']
                if audience.get('ctr', 0) > 3.0 and audience.get('cpa', 0) < 30
            ]

            if underperforming_audiences:
                gaps.append({
                    "type": "audience_expansion",
                    "description": "Identified audiences with strong performance not fully targeted",
                    "suggested_audiences": [aud.get('name') for aud in underperforming_audiences[:3]]
                })

        return gaps

    def _recommend_resource_allocation(self, ad_groups: List[Dict[str, Any]],
                                    performance_data: Dict[str, Any]) -> List[str]:
        """Recommend how to allocate campaign budget across ad groups"""
        recommendations = []

        ag_performance = performance_data.get('ad_group_performance', {})

        # Identify top and bottom performing ad groups
        performing_groups = []
        for ag in ad_groups:
            perf = ag_performance.get(ag['name'], {})
            conversions = perf.get('conversions', 0)
            cost = perf.get('cost_micros', 0) / 1000000
            performing_groups.append({
                'name': ag['name'],
                'conversions': conversions,
                'cost': cost,
                'cpa': cost / conversions if conversions > 0 else float('inf')
            })

        # Sort by CPA (lowest first = best)
        performing_groups.sort(key=lambda x: x['cpa'])

        top_performers = [g for g in performing_groups if g['cpa'] < 50][:3]
        underperformers = [g for g in performing_groups if g['cpa'] > 100][-3:]

        if top_performers:
            recommendations.append(
                f"Allocate more budget to high-performing ad groups: {', '.join([g['name'] for g in top_performers])}"
            )

        if underperformers:
            recommendations.append(
                f"Consider pausing or optimizing underperforming ad groups: {', '.join([g['name'] for g in underperformers])}"
            )

        return recommendations

    def export_ad_groups_to_csv(self, ad_groups: List[Dict[str, Any]],
                               campaign_name: str) -> str:
        """
        Export ad groups to CSV format compatible with Google Ads Editor.

        Args:
            ad_groups: List of ad group configurations
            campaign_name: Name of the parent campaign

        Returns:
            CSV content as string
        """
        csv_lines = [
            "Campaign,Ad Group,Status,Type,Targeting,Keywords,Geographic Targeting,Networks,Bid Strategy Type,Bid Strategy Name,Target CPA,Max CPC,Enhanced CPC,Ad Schedule,Conversion Actions,Labels"
        ]

        for ag in ad_groups:
            settings = ag.get('settings', {})
            targeting = ag.get('targeting', {})

            # Format keywords
            keywords = ag.get('keywords', [])
            keyword_text = "; ".join([
                f"{kw['text']} ({kw['match_type']})" for kw in keywords[:10]  # Limit to 10 keywords
            ])

            # Format negative keywords
            negative_keywords = targeting.get('negative_keywords', [])
            if negative_keywords:
                neg_kw_text = "; ".join([
                    f"-{kw['text']} ({kw['match_type']})" for kw in negative_keywords[:5]
                ])
                keyword_text += f"; {neg_kw_text}"

            # Basic row data
            row = [
                campaign_name,  # Campaign
                ag["name"],  # Ad Group
                settings.get("status", "ENABLED"),  # Status
                ag.get("type", "SEARCH_STANDARD"),  # Type
                "Keywords",  # Targeting method
                keyword_text,  # Keywords
                "",  # Geographic Targeting (could be enhanced)
                "",  # Networks
                "Manual CPC",  # Bid Strategy Type
                "",  # Bid Strategy Name
                "",  # Target CPA
                str(settings.get("cpc_bid_micros", 500000) / 1000000),  # Max CPC in dollars
                "Enabled",  # Enhanced CPC
                "",  # Ad Schedule
                "",  # Conversion Actions
                "; ".join(settings.get("labels", []))  # Labels
            ]

            csv_lines.append(",".join(f'"{str(cell)}"' for cell in row))

        return "\n".join(csv_lines)

    def create_ad_group_performance_dashboard(self, ad_groups: List[Dict[str, Any]],
                                           performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a performance dashboard for ad groups.

        Args:
            ad_groups: List of ad group configurations
            performance_data: Performance metrics

        Returns:
            Dashboard data with summaries and insights
        """
        dashboard = {
            "summary": {
                "total_ad_groups": len(ad_groups),
                "active_ad_groups": sum(1 for ag in ad_groups if ag.get('settings', {}).get('status') == 'ENABLED'),
                "total_keywords": sum(len(ag.get('keywords', [])) for ag in ad_groups)
            },
            "performance_summary": {},
            "top_performers": [],
            "underperformers": [],
            "insights": []
        }

        ag_performance = performance_data.get('ad_group_performance', {})

        # Calculate performance summary
        total_impressions = sum(perf.get('impressions', 0) for perf in ag_performance.values())
        total_clicks = sum(perf.get('clicks', 0) for perf in ag_performance.values())
        total_cost = sum(perf.get('cost_micros', 0) for perf in ag_performance.values()) / 1000000
        total_conversions = sum(perf.get('conversions', 0) for perf in ag_performance.values())

        dashboard["performance_summary"] = {
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_cost": round(total_cost, 2),
            "total_conversions": total_conversions,
            "average_ctr": round((total_clicks / total_impressions * 100) if total_impressions > 0 else 0, 2),
            "average_cpa": round((total_cost / total_conversions) if total_conversions > 0 else 0, 2)
        }

        # Identify top and underperformers
        ag_perf_list = []
        for ag in ad_groups:
            perf = ag_performance.get(ag['name'], {})
            conversions = perf.get('conversions', 0)
            cost = perf.get('cost_micros', 0) / 1000000
            cpa = cost / conversions if conversions > 0 else float('inf')

            ag_perf_list.append({
                'name': ag['name'],
                'conversions': conversions,
                'cost': cost,
                'cpa': cpa,
                'clicks': perf.get('clicks', 0)
            })

        # Top performers (lowest CPA)
        top_performers = sorted([ag for ag in ag_perf_list if ag['cpa'] < float('inf')],
                               key=lambda x: x['cpa'])[:3]
        dashboard["top_performers"] = top_performers

        # Underperformers (highest CPA)
        underperformers = sorted([ag for ag in ag_perf_list if ag['cpa'] < float('inf')],
                               key=lambda x: x['cpa'], reverse=True)[:3]
        dashboard["underperformers"] = underperformers

        # Generate insights
        if dashboard["performance_summary"]["average_ctr"] < 1.5:
            dashboard["insights"].append("Overall CTR is below average - consider improving ad relevance")

        if dashboard["performance_summary"]["average_cpa"] > 100:
            dashboard["insights"].append("CPA is high - review bidding strategy and negative keywords")

        return dashboard