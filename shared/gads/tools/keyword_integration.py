#!/usr/bin/env python3
"""
Keyword Management Integration Module

This module integrates the Keyword Management System with existing Google Ads
campaign planning and ad group management workflows.
"""

import sys
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add the gads directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from keyword_management_system import KeywordManagementSystem, KeywordCriterion
from ad_group_management_system import AdGroupManagementSystem
from google_ads_agent.utils.logging_utils import get_logger

logger = get_logger('keyword_integration')

class KeywordCampaignIntegrator:
    """
    Integrates keyword management with campaign planning workflows.

    This class provides methods to automatically generate and optimize keywords
    for campaigns and ad groups, validate keyword configurations, and provide
    performance-based optimization recommendations.
    """

    def __init__(self):
        """Initialize the keyword campaign integrator"""
        self.kw_system = KeywordManagementSystem()
        self.ag_system = AdGroupManagementSystem()

    def generate_keywords_for_campaign(self, campaign_config: Dict[str, Any],
                                     ad_groups: List[Dict[str, Any]]) -> Dict[str, List[KeywordCriterion]]:
        """
        Generate comprehensive keyword sets for all ad groups in a campaign.

        Args:
            campaign_config: Campaign configuration
            ad_groups: List of ad group configurations

        Returns:
            Dictionary mapping ad group names to keyword lists
        """
        logger.info(f"Generating keywords for campaign with {len(ad_groups)} ad groups")

        campaign_keywords = {}

        for ad_group in ad_groups:
            ad_group_name = ad_group["name"]
            theme = self._extract_theme_from_ad_group(ad_group)

            # Generate keywords for this ad group
            keywords = self.kw_system.generate_keywords_for_theme(
                theme=theme,
                target_audience=campaign_config.get('target_audience'),
                competition_level=self._assess_campaign_competition(campaign_config),
                keyword_count=30  # Keywords per ad group
            )

            # Generate negative keywords
            negative_keywords = self.kw_system.generate_negative_keywords(
                theme=theme,
                positive_keywords=[kw.text for kw in keywords]
            )

            # Combine positive and negative keywords
            all_keywords = keywords + negative_keywords
            campaign_keywords[ad_group_name] = all_keywords

        return campaign_keywords

    def _extract_theme_from_ad_group(self, ad_group: Dict[str, Any]) -> str:
        """Extract theme from ad group configuration"""
        # Try to extract from ad group name
        name = ad_group.get("name", "").lower()

        # Look for theme indicators in name
        theme_indicators = {
            "executive": "executive resume services",
            "professional": "professional resume services",
            "career": "career development services",
            "resume": "resume writing services",
            "job": "job search assistance"
        }

        for indicator, theme in theme_indicators.items():
            if indicator in name:
                return theme

        # Fallback to a generic theme
        return "professional services"

    def _assess_campaign_competition(self, campaign_config: Dict[str, Any]) -> str:
        """Assess competition level for the campaign"""
        # Check budget as indicator of competition level
        budget = campaign_config.get('budget', 0)
        if budget > 100:  # High budget suggests high competition
            return "high"
        elif budget > 30:  # Medium budget
            return "medium"
        else:  # Low budget
            return "low"

    def validate_campaign_keywords(self, campaign_keywords: Dict[str, List[KeywordCriterion]],
                                 campaign_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate keyword configuration across the entire campaign.

        Args:
            campaign_keywords: Keywords organized by ad group
            campaign_config: Campaign configuration

        Returns:
            Validation results with issues and recommendations
        """
        validation = {
            "is_valid": True,
            "ad_group_validations": {},
            "campaign_level_issues": [],
            "recommendations": [],
            "keyword_distribution": {}
        }

        total_keywords = 0
        match_type_distribution = {"EXACT": 0, "PHRASE": 0, "BROAD": 0}

        # Validate each ad group
        for ad_group_name, keywords in campaign_keywords.items():
            ag_validation = self.kw_system.validate_keyword_criteria(keywords)
            validation["ad_group_validations"][ad_group_name] = ag_validation

            if not ag_validation["is_valid"]:
                validation["is_valid"] = False

            # Aggregate statistics
            total_keywords += len(keywords)
            for kw in keywords:
                if not kw.is_negative:  # Only count positive keywords
                    match_type_distribution[kw.match_type] += 1

        validation["keyword_distribution"] = {
            "total_keywords": total_keywords,
            "match_type_distribution": match_type_distribution,
            "ad_groups_covered": len(campaign_keywords)
        }

        # Campaign-level validation
        if match_type_distribution["EXACT"] < match_type_distribution["BROAD"] * 0.5:
            validation["campaign_level_issues"].append(
                "Campaign has more broad match than exact match keywords - consider adding more exact match terms"
            )

        if total_keywords < len(campaign_keywords) * 10:
            validation["recommendations"].append(
                "Consider adding more keywords per ad group for better coverage"
            )

        return validation

    def optimize_campaign_keywords(self, campaign_keywords: Dict[str, List[KeywordCriterion]],
                                 performance_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Optimize keywords across the entire campaign based on performance data.

        Args:
            campaign_keywords: Keywords organized by ad group
            performance_data: Performance data organized by ad group

        Returns:
            Optimization recommendations for the campaign
        """
        logger.info("Optimizing campaign keywords")

        optimization_results = {
            "ad_group_optimizations": {},
            "campaign_level_optimization": {},
            "resource_reallocation": [],
            "new_keyword_suggestions": [],
            "negative_keyword_additions": []
        }

        # Optimize each ad group
        for ad_group_name, keywords in campaign_keywords.items():
            ag_performance = performance_data.get(ad_group_name, {})

            # Convert performance data to KeywordPerformance objects
            kw_performance = {}
            for kw in keywords:
                if kw.text in ag_performance.get('keyword_performance', {}):
                    perf_data = ag_performance['keyword_performance'][kw.text]
                    kw_performance[kw.text] = perf_data

            # Get optimization recommendations
            ag_optimization = self.kw_system.optimize_keyword_performance(keywords, kw_performance)
            optimization_results["ad_group_optimizations"][ad_group_name] = ag_optimization

            # Aggregate campaign-level insights
            for action in ag_optimization.priority_actions:
                if "Low CTR" in action or "High CPA" in action:
                    optimization_results["campaign_level_optimization"].setdefault("performance_issues", []).append(action)

        # Campaign-level analysis
        self._analyze_campaign_level_optimization(campaign_keywords, performance_data, optimization_results)

        return optimization_results

    def _analyze_campaign_level_optimization(self, campaign_keywords: Dict[str, List[KeywordCriterion]],
                                           performance_data: Dict[str, Dict[str, Any]],
                                           optimization_results: Dict[str, Any]):
        """Analyze campaign-level optimization opportunities"""

        # Find top performing keywords across campaign
        top_performers = []
        for ad_group_name, keywords in campaign_keywords.items():
            ag_perf = performance_data.get(ad_group_name, {}).get('keyword_performance', {})
            for kw in keywords:
                perf = ag_perf.get(kw.text, {})
                conversions = perf.get('conversions', 0)
                if conversions > 0:
                    top_performers.append({
                        'keyword': kw.text,
                        'ad_group': ad_group_name,
                        'conversions': conversions,
                        'cpa': perf.get('cost_micros', 0) / 1000000 / conversions if conversions > 0 else float('inf')
                    })

        # Sort by CPA (lowest first)
        top_performers.sort(key=lambda x: x['cpa'])

        # Suggest expanding top performers to other ad groups
        if len(top_performers) > 5:
            optimization_results["new_keyword_suggestions"] = [
                {
                    "keyword": perf['keyword'],
                    "suggested_ad_groups": [ag for ag in campaign_keywords.keys() if ag != perf['ad_group']],
                    "reason": f"High performing keyword with ${perf['cpa']:.2f} CPA"
                }
                for perf in top_performers[:3]
            ]

    def balance_keyword_distribution(self, campaign_keywords: Dict[str, List[KeywordCriterion]]) -> Dict[str, Any]:
        """
        Analyze and provide recommendations for balancing keyword distribution across ad groups.

        Args:
            campaign_keywords: Keywords organized by ad group

        Returns:
            Balance analysis and recommendations
        """
        analysis = {
            "distribution": {},
            "imbalances": [],
            "recommendations": []
        }

        # Calculate distribution
        for ad_group_name, keywords in campaign_keywords.items():
            positive_keywords = [kw for kw in keywords if not kw.is_negative]
            negative_keywords = [kw for kw in keywords if kw.is_negative]

            analysis["distribution"][ad_group_name] = {
                "positive_keywords": len(positive_keywords),
                "negative_keywords": len(negative_keywords),
                "total_keywords": len(keywords),
                "match_type_breakdown": {}
            }

            # Match type breakdown
            match_types = {}
            for kw in positive_keywords:
                match_types[kw.match_type] = match_types.get(kw.match_type, 0) + 1
            analysis["distribution"][ad_group_name]["match_type_breakdown"] = match_types

        # Identify imbalances
        avg_keywords = sum(ag["positive_keywords"] for ag in analysis["distribution"].values()) / len(analysis["distribution"])

        for ag_name, dist in analysis["distribution"].items():
            if dist["positive_keywords"] < avg_keywords * 0.7:
                analysis["imbalances"].append(f"{ag_name} has significantly fewer keywords than average")
            elif dist["positive_keywords"] > avg_keywords * 1.5:
                analysis["imbalances"].append(f"{ag_name} has significantly more keywords than average")

        # Generate recommendations
        if analysis["imbalances"]:
            analysis["recommendations"].append("Balance keyword distribution across ad groups")
            analysis["recommendations"].append("Aim for 15-25 positive keywords per ad group")

        return analysis

    def export_keywords_to_campaign_csv(self, campaign_keywords: Dict[str, List[KeywordCriterion]],
                                       campaign_name: str) -> str:
        """
        Export all campaign keywords to a single CSV file.

        Args:
            campaign_keywords: Keywords organized by ad group
            campaign_name: Campaign name

        Returns:
            CSV content as string
        """
        csv_lines = [
            "Campaign,Ad Group,Keyword,Match Type,Criterion Type,Status,Bid Strategy Type,Max CPC,Labels"
        ]

        for ad_group_name, keywords in campaign_keywords.items():
            for keyword in keywords:
                # Determine criterion type
                criterion_type = "Negative keyword" if keyword.is_negative else "Keyword"

                # Format bid
                bid_str = f"${keyword.bid_micros/1000000:.2f}" if keyword.bid_micros else ""

                # Format labels
                labels_str = ";".join(keyword.labels) if keyword.labels else ""

                row = [
                    campaign_name,
                    ad_group_name,
                    keyword.text,
                    keyword.match_type.title(),
                    criterion_type,
                    keyword.status.title(),
                    "Manual CPC",
                    bid_str,
                    labels_str
                ]

                csv_lines.append(",".join(f'"{str(cell)}"' for cell in row))

        return "\n".join(csv_lines)

    def create_keyword_performance_dashboard(self, campaign_keywords: Dict[str, List[KeywordCriterion]],
                                           performance_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a comprehensive keyword performance dashboard.

        Args:
            campaign_keywords: Keywords organized by ad group
            performance_data: Performance data by ad group

        Returns:
            Performance dashboard with insights and metrics
        """
        dashboard = {
            "campaign_overview": {
                "total_ad_groups": len(campaign_keywords),
                "total_keywords": sum(len(kws) for kws in campaign_keywords.values()),
                "total_positive_keywords": 0,
                "total_negative_keywords": 0
            },
            "performance_summary": {},
            "top_performing_keywords": [],
            "underperforming_keywords": [],
            "ad_group_performance": {},
            "insights": [],
            "recommendations": []
        }

        # Calculate totals
        total_impressions = 0
        total_clicks = 0
        total_cost = 0
        total_conversions = 0

        for ad_group_name, keywords in campaign_keywords.items():
            positive_kws = [kw for kw in keywords if not kw.is_negative]
            negative_kws = [kw for kw in keywords if kw.is_negative]

            dashboard["campaign_overview"]["total_positive_keywords"] += len(positive_kws)
            dashboard["campaign_overview"]["total_negative_keywords"] += len(negative_kws)

            # Aggregate performance data
            ag_perf = performance_data.get(ad_group_name, {})
            total_impressions += ag_perf.get('total_impressions', 0)
            total_clicks += ag_perf.get('total_clicks', 0)
            total_cost += ag_perf.get('total_cost_micros', 0) / 1000000
            total_conversions += ag_perf.get('total_conversions', 0)

            # Ad group performance summary
            dashboard["ad_group_performance"][ad_group_name] = {
                "positive_keywords": len(positive_kws),
                "negative_keywords": len(negative_kws),
                "impressions": ag_perf.get('total_impressions', 0),
                "clicks": ag_perf.get('total_clicks', 0),
                "cost": ag_perf.get('total_cost_micros', 0) / 1000000,
                "conversions": ag_perf.get('total_conversions', 0)
            }

        # Overall performance summary
        dashboard["performance_summary"] = {
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_cost": round(total_cost, 2),
            "total_conversions": total_conversions,
            "average_ctr": round((total_clicks / total_impressions * 100) if total_impressions > 0 else 0, 2),
            "average_cpa": round((total_cost / total_conversions) if total_conversions > 0 else 0, 2),
            "average_cpc": round((total_cost / total_clicks) if total_clicks > 0 else 0, 2)
        }

        # Identify top and underperforming keywords across campaign
        all_keyword_performance = []
        for ad_group_name, ag_perf in performance_data.items():
            kw_perf = ag_perf.get('keyword_performance', {})
            for kw_text, perf in kw_perf.items():
                conversions = perf.get('conversions', 0)
                cost = perf.get('cost_micros', 0) / 1000000
                cpa = cost / conversions if conversions > 0 else float('inf')

                all_keyword_performance.append({
                    'keyword': kw_text,
                    'ad_group': ad_group_name,
                    'conversions': conversions,
                    'cost': cost,
                    'cpa': cpa,
                    'clicks': perf.get('clicks', 0),
                    'ctr': perf.get('ctr', 0)
                })

        # Top performers (lowest CPA)
        top_performers = sorted([kw for kw in all_keyword_performance if kw['cpa'] < float('inf') and kw['conversions'] > 0],
                               key=lambda x: x['cpa'])[:5]
        dashboard["top_performing_keywords"] = top_performers

        # Underperformers (high CPA or low CTR)
        underperformers = sorted([kw for kw in all_keyword_performance if kw['cpa'] > 100 or kw['ctr'] < 1.0],
                               key=lambda x: x['cpa'], reverse=True)[:5]
        dashboard["underperforming_keywords"] = underperformers

        # Generate insights
        perf_summary = dashboard["performance_summary"]
        if perf_summary["average_ctr"] < 1.5:
            dashboard["insights"].append("Campaign CTR is below average - review ad relevance and negative keywords")
            dashboard["recommendations"].append("Improve ad copy relevance and add more negative keywords")

        if perf_summary["average_cpa"] > 50:
            dashboard["insights"].append("CPA is above typical range - consider bid adjustments")
            dashboard["recommendations"].append("Review keyword bids and consider lowering bids on high-CPA terms")

        if len(dashboard["top_performing_keywords"]) > 0:
            dashboard["insights"].append(f"Found {len(dashboard['top_performing_keywords'])} high-performing keywords to expand")
            dashboard["recommendations"].append("Consider adding close variants of top-performing keywords")

        return dashboard

    def get_seasonal_keyword_strategy(self, campaign_keywords: Dict[str, List[KeywordCriterion]],
                                    season: str) -> Dict[str, Any]:
        """
        Develop seasonal keyword strategy for the campaign.

        Args:
            campaign_keywords: Current campaign keywords
            season: Season (winter, spring, summer, fall, holiday)

        Returns:
            Seasonal strategy recommendations
        """
        strategy = {
            "season": season,
            "bid_modifiers": {},
            "new_keywords": [],
            "paused_keywords": [],
            "recommendations": []
        }

        current_month = datetime.now().month

        # Apply seasonal modifiers
        for ad_group_name, keywords in campaign_keywords.items():
            for keyword in keywords:
                seasonal_modifier = self.kw_system.apply_seasonal_bid_modifiers([keyword], current_month)
                if keyword.text in seasonal_modifier:
                    strategy["bid_modifiers"][keyword.text] = seasonal_modifier[keyword.text]

        # Seasonal keyword suggestions
        seasonal_suggestions = {
            "holiday": ["gift", "holiday special", "year-end", "bonus"],
            "summer": ["outdoor", "vacation", "summer", "beach"],
            "back_to_school": ["student", "school", "college", "education"],
            "tax_season": ["tax", "refund", "financial planning"]
        }

        if season in seasonal_suggestions:
            strategy["new_keywords"] = seasonal_suggestions[season]
            strategy["recommendations"].append(f"Add seasonal keywords: {', '.join(seasonal_suggestions[season])}")

        return strategy