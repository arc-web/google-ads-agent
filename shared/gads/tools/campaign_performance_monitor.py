#!/usr/bin/env python3
"""
Campaign Performance Monitoring System

Tracks Quality Score, conversion rates, and other key performance indicators
as required by Context7 Google Ads documentation for campaign optimization.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for campaigns and ad groups"""
    campaign_name: str
    ad_group_name: Optional[str] = None
    date_range: str = "last_30_days"

    # Core metrics
    impressions: int = 0
    clicks: int = 0
    cost_micros: int = 0
    conversions: float = 0.0

    # Quality metrics
    quality_score: Optional[int] = None
    expected_ctr: Optional[float] = None
    ad_relevance: Optional[int] = None
    landing_page_experience: Optional[int] = None

    # Calculated metrics
    ctr: float = 0.0
    cpc: float = 0.0
    conversion_rate: float = 0.0
    cost_per_conversion: float = 0.0
    roas: float = 0.0

    # Context7 optimization thresholds
    optimization_score: int = 0  # 0-100 scale
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

@dataclass
class QualityScoreAnalysis:
    """Quality Score analysis and recommendations"""
    overall_score: int
    ad_relevance_score: int
    expected_ctr_score: int
    landing_page_score: int

    # Context7 recommendations
    improvement_actions: List[str]
    expected_impact: str
    priority_level: str  # 'high', 'medium', 'low'

class CampaignPerformanceMonitor:
    """
    Monitors campaign performance and provides optimization recommendations
    based on Context7 Google Ads best practices.
    """

    def __init__(self):
        """Initialize performance monitoring system"""
        self.quality_thresholds = {
            'excellent': 8,
            'good': 6,
            'needs_improvement': 4,
            'poor': 1
        }

        self.performance_targets = {
            'min_ctr': 2.0,  # Minimum 2% CTR
            'max_cpc': 5.00,  # Maximum $5 CPC
            'min_conversion_rate': 1.0,  # Minimum 1% conversion rate
            'target_roas': 4.0  # Target 4:1 ROAS
        }

    def analyze_campaign_performance(self, campaign_data: Dict[str, Any]) -> PerformanceMetrics:
        """
        Analyze campaign performance against Context7 best practices.

        Args:
            campaign_data: Campaign performance data from Google Ads API

        Returns:
            PerformanceMetrics with analysis and recommendations
        """
        metrics = PerformanceMetrics(
            campaign_name=campaign_data.get('campaign_name', 'Unknown'),
            impressions=campaign_data.get('impressions', 0),
            clicks=campaign_data.get('clicks', 0),
            cost_micros=campaign_data.get('cost_micros', 0),
            conversions=campaign_data.get('conversions', 0.0)
        )

        # Calculate derived metrics
        self._calculate_derived_metrics(metrics)

        # Analyze Quality Score
        if 'quality_score' in campaign_data:
            quality_analysis = self._analyze_quality_score(campaign_data['quality_score'])
            metrics.quality_score = campaign_data['quality_score']
            metrics.optimization_score = self._calculate_optimization_score(metrics, quality_analysis)

        # Generate recommendations
        metrics.recommendations = self._generate_recommendations(metrics)
        metrics.issues = self._identify_performance_issues(metrics)

        return metrics

    def _calculate_derived_metrics(self, metrics: PerformanceMetrics):
        """Calculate CTR, CPC, conversion rate, etc."""
        if metrics.impressions > 0:
            metrics.ctr = (metrics.clicks / metrics.impressions) * 100

        if metrics.clicks > 0:
            metrics.cpc = (metrics.cost_micros / 1000000) / metrics.clicks
            metrics.conversion_rate = (metrics.conversions / metrics.clicks) * 100

        if metrics.conversions > 0:
            metrics.cost_per_conversion = (metrics.cost_micros / 1000000) / metrics.conversions

        if metrics.cost_micros > 0:
            revenue = metrics.conversions * self.performance_targets['target_roas'] * (metrics.cost_micros / 1000000)
            metrics.roas = revenue / (metrics.cost_micros / 1000000)

    def _analyze_quality_score(self, quality_score: int) -> QualityScoreAnalysis:
        """Analyze Quality Score components and provide improvement recommendations"""
        analysis = QualityScoreAnalysis(
            overall_score=quality_score,
            ad_relevance_score=quality_score,  # Simplified - would get from API
            expected_ctr_score=quality_score,
            landing_page_score=quality_score,
            improvement_actions=[],
            expected_impact="",
            priority_level=""
        )

        # Determine priority and recommendations based on score
        if quality_score >= self.quality_thresholds['excellent']:
            analysis.priority_level = 'low'
            analysis.expected_impact = "Already optimized"
        elif quality_score >= self.quality_thresholds['good']:
            analysis.priority_level = 'medium'
            analysis.improvement_actions = [
                "Improve ad copy relevance",
                "Test different landing pages",
                "Add negative keywords"
            ]
            analysis.expected_impact = "10-20% improvement possible"
        elif quality_score >= self.quality_thresholds['needs_improvement']:
            analysis.priority_level = 'high'
            analysis.improvement_actions = [
                "Complete rewrite of ad copy",
                "Optimize landing page for conversions",
                "Add more specific negative keywords",
                "Improve keyword targeting"
            ]
            analysis.expected_impact = "30-50% improvement possible"
        else:
            analysis.priority_level = 'critical'
            analysis.improvement_actions = [
                "Complete campaign restructure required",
                "Professional ad copy review",
                "Landing page optimization",
                "Comprehensive keyword audit"
            ]
            analysis.expected_impact = "50-100% improvement needed"

        return analysis

    def _calculate_optimization_score(self, metrics: PerformanceMetrics,
                                   quality_analysis: QualityScoreAnalysis) -> int:
        """Calculate overall optimization score (0-100)"""
        score = 0

        # Quality Score component (40% weight)
        if metrics.quality_score:
            score += (metrics.quality_score / 10) * 40

        # CTR component (20% weight)
        ctr_score = min(metrics.ctr / self.performance_targets['min_ctr'], 1) * 20
        score += ctr_score

        # Conversion rate component (20% weight)
        conv_score = min(metrics.conversion_rate / self.performance_targets['min_conversion_rate'], 1) * 20
        score += conv_score

        # CPC efficiency component (20% weight)
        cpc_efficiency = 1 - min(metrics.cpc / self.performance_targets['max_cpc'], 1)
        score += cpc_efficiency * 20

        return int(min(score, 100))

    def _generate_recommendations(self, metrics: PerformanceMetrics) -> List[str]:
        """Generate optimization recommendations based on Context7 best practices"""
        recommendations = []

        # CTR recommendations
        if metrics.ctr < self.performance_targets['min_ctr']:
            recommendations.append("Improve ad copy to increase CTR above 2%")

        # Quality Score recommendations
        if metrics.quality_score and metrics.quality_score < 6:
            recommendations.append("Focus on Quality Score improvement - keywords, ads, and landing pages")

        # CPC recommendations
        if metrics.cpc > self.performance_targets['max_cpc']:
            recommendations.append("Reduce CPC through better keyword targeting or bid adjustments")

        # Conversion recommendations
        if metrics.conversions == 0:
            recommendations.append("Set up conversion tracking to enable optimization")

        if metrics.conversion_rate < 1.0:
            recommendations.append("Optimize landing pages and conversion funnel")

        # Budget utilization
        if metrics.impressions < 1000:
            recommendations.append("Increase budget or expand targeting to get more impressions")

        return recommendations

    def _identify_performance_issues(self, metrics: PerformanceMetrics) -> List[str]:
        """Identify critical performance issues"""
        issues = []

        if metrics.impressions == 0:
            issues.append("No impressions - campaign may be paused or have targeting issues")

        if metrics.quality_score and metrics.quality_score <= 3:
            issues.append("Critical Quality Score issues - campaign at risk of disapproval")

        if metrics.ctr < 1.0:
            issues.append("Very low CTR - ad copy may not be relevant to keywords")

        if metrics.conversions == 0 and metrics.clicks > 100:
            issues.append("No conversions despite clicks - landing page or conversion tracking issues")

        return issues

    def generate_performance_report(self, campaign_metrics: List[PerformanceMetrics]) -> Dict[str, Any]:
        """
        Generate comprehensive performance report for multiple campaigns.

        Args:
            campaign_metrics: List of performance metrics for campaigns

        Returns:
            Comprehensive performance report
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_campaigns': len(campaign_metrics),
            'summary': {},
            'campaign_details': [],
            'optimization_priorities': []
        }

        if not campaign_metrics:
            return report

        # Calculate summary statistics
        total_impressions = sum(m.impressions for m in campaign_metrics)
        total_clicks = sum(m.clicks for m in campaign_metrics)
        total_cost = sum(m.cost_micros for m in campaign_metrics) / 1000000
        total_conversions = sum(m.conversions for m in campaign_metrics)

        report['summary'] = {
            'total_impressions': total_impressions,
            'total_clicks': total_clicks,
            'total_cost': total_cost,
            'total_conversions': total_conversions,
            'average_ctr': (total_clicks / total_impressions * 100) if total_impressions > 0 else 0,
            'average_cpc': (total_cost / total_clicks) if total_clicks > 0 else 0,
            'average_conversion_rate': (total_conversions / total_clicks * 100) if total_clicks > 0 else 0,
            'average_cost_per_conversion': (total_cost / total_conversions) if total_conversions > 0 else 0
        }

        # Campaign details
        for metrics in campaign_metrics:
            campaign_detail = {
                'campaign_name': metrics.campaign_name,
                'optimization_score': metrics.optimization_score,
                'quality_score': metrics.quality_score,
                'performance_metrics': {
                    'impressions': metrics.impressions,
                    'clicks': metrics.clicks,
                    'ctr': round(metrics.ctr, 2),
                    'cpc': round(metrics.cpc, 2),
                    'conversions': metrics.conversions,
                    'conversion_rate': round(metrics.conversion_rate, 2),
                    'cost_per_conversion': round(metrics.cost_per_conversion, 2)
                },
                'issues': metrics.issues,
                'recommendations': metrics.recommendations
            }
            report['campaign_details'].append(campaign_detail)

        # Generate optimization priorities
        high_priority = [m for m in campaign_metrics if m.optimization_score < 40]
        medium_priority = [m for m in campaign_metrics if 40 <= m.optimization_score < 70]
        low_priority = [m for m in campaign_metrics if m.optimization_score >= 70]

        report['optimization_priorities'] = {
            'high_priority': [m.campaign_name for m in high_priority],
            'medium_priority': [m.campaign_name for m in medium_priority],
            'low_priority': [m.campaign_name for m in low_priority]
        }

        return report

    def get_campaign_health_score(self, metrics: PerformanceMetrics) -> str:
        """
        Get overall campaign health assessment.

        Returns:
            Health status: 'excellent', 'good', 'needs_attention', 'critical'
        """
        if metrics.optimization_score >= 80:
            return 'excellent'
        elif metrics.optimization_score >= 60:
            return 'good'
        elif metrics.optimization_score >= 40:
            return 'needs_attention'
        else:
            return 'critical'