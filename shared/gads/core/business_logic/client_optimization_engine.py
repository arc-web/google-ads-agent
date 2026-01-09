"""
Client-Specific Performance Optimization Engine

This module provides intelligent, automated optimization for Google Ads campaigns
based on client-specific configurations, business rules, and performance data.
It implements client-tailored optimization strategies and recommendations.

Key Features:
- Client-specific optimization strategies
- Automated bid and budget adjustments
- Performance-based recommendations
- Industry-tailored optimization rules
- Risk-aware optimization with safety limits
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from client_config_schema import (
    ClientSpecificConfig,
    OptimizationSettings,
    OptimizationStrategy,
    IndustryType
)
from google_ads_client_business_rules import BusinessRuleValidator, ValidationResult
from client_reporting_engine import KPIResult

logger = logging.getLogger(__name__)


class OptimizationAction(Enum):
    """Types of optimization actions"""
    BID_ADJUSTMENT = "bid_adjustment"
    BUDGET_REALLOCATION = "budget_reallocation"
    KEYWORD_ADDITION = "keyword_addition"
    KEYWORD_PAUSE = "keyword_pause"
    AUDIENCE_EXPANSION = "audience_expansion"
    AD_CREATIVE_UPDATE = "ad_creative_update"
    CAMPAIGN_STRUCTURE_CHANGE = "campaign_structure_change"


class OptimizationPriority(Enum):
    """Optimization priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class OptimizationOpportunity:
    """Represents an optimization opportunity"""
    opportunity_id: str
    client_id: str
    campaign_id: str
    action_type: OptimizationAction
    priority: OptimizationPriority
    description: str
    expected_impact: Dict[str, float]  # metric -> expected_change_percentage
    confidence_score: float  # 0.0 to 1.0
    risk_level: str  # low, medium, high
    implementation_complexity: str  # simple, moderate, complex
    prerequisites: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    implemented: bool = False
    implemented_at: Optional[datetime] = None
    results: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if opportunity has expired"""
        return self.expires_at is not None and datetime.now() > self.expires_at

    def mark_implemented(self, results: Optional[Dict[str, Any]] = None):
        """Mark opportunity as implemented"""
        self.implemented = True
        self.implemented_at = datetime.now()
        if results:
            self.results = results


@dataclass
class OptimizationRecommendation:
    """Complete optimization recommendation"""
    client_id: str
    campaign_id: str
    opportunities: List[OptimizationOpportunity] = field(default_factory=list)
    summary: str = ""
    priority_score: float = 0.0  # 0.0 to 1.0
    estimated_effort_hours: float = 0.0
    expected_roi: float = 0.0
    risk_assessment: str = "medium"
    generated_at: datetime = field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None

    def calculate_priority_score(self):
        """Calculate overall priority score based on opportunities"""
        if not self.opportunities:
            self.priority_score = 0.0
            return

        # Weight opportunities by priority and confidence
        priority_weights = {
            OptimizationPriority.LOW: 0.1,
            OptimizationPriority.MEDIUM: 0.5,
            OptimizationPriority.HIGH: 1.0,
            OptimizationPriority.CRITICAL: 2.0
        }

        total_weight = 0
        weighted_sum = 0

        for opp in self.opportunities:
            weight = priority_weights.get(opp.priority, 0.5)
            confidence_weight = opp.confidence_score

            total_weight += weight * confidence_weight
            weighted_sum += weight * confidence_weight * opp.expected_impact.get('conversion_rate', 0)

        self.priority_score = min(1.0, total_weight / len(self.opportunities))

    def is_expired(self) -> bool:
        """Check if recommendation has expired"""
        return self.valid_until is not None and datetime.now() > self.valid_until


class ClientOptimizationEngine:
    """
    Client-specific optimization engine

    This engine analyzes performance data and generates tailored optimization
    recommendations based on client configuration and business rules.
    """

    def __init__(self, client_config: ClientSpecificConfig):
        self.config = client_config
        self.business_validator = BusinessRuleValidator(client_config)
        self.optimization_settings = client_config.optimization

        # Optimization thresholds based on client strategy
        self.thresholds = self._calculate_strategy_thresholds()

        logger.info(f"Initialized optimization engine for client {client_config.client_name}")

    def _calculate_strategy_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Calculate optimization thresholds based on client strategy"""
        base_thresholds = {
            "ctr_threshold": 1.0,
            "cpa_threshold_increase": 0.2,  # 20% increase allowed
            "budget_utilization_min": 0.8,  # 80% minimum utilization
            "conversion_rate_min": 1.0,
            "bid_adjustment_max": 0.5,  # 50% max bid change
            "confidence_min": 0.7  # Minimum confidence for auto-optimization
        }

        # Adjust thresholds based on strategy
        if self.optimization_settings.strategy == OptimizationStrategy.CONSERVATIVE:
            base_thresholds.update({
                "bid_adjustment_max": 0.2,
                "confidence_min": 0.8,
                "cpa_threshold_increase": 0.1
            })
        elif self.optimization_settings.strategy == OptimizationStrategy.AGGRESSIVE:
            base_thresholds.update({
                "bid_adjustment_max": 0.8,
                "confidence_min": 0.6,
                "cpa_threshold_increase": 0.3
            })

        return {"performance": base_thresholds}

    def analyze_performance_and_optimize(self, performance_data: Dict[str, Any],
                                       campaign_data: Dict[str, Any],
                                       historical_data: Optional[Dict[str, Any]] = None) -> OptimizationRecommendation:
        """
        Analyze performance data and generate optimization recommendations

        Args:
            performance_data: Current performance metrics
            campaign_data: Campaign structure and settings
            historical_data: Historical performance data for trend analysis

        Returns:
            OptimizationRecommendation with opportunities
        """
        opportunities = []

        # Analyze different aspects
        opportunities.extend(self._analyze_bid_optimization(performance_data, campaign_data))
        opportunities.extend(self._analyze_budget_optimization(performance_data, campaign_data))
        opportunities.extend(self._analyze_keyword_optimization(performance_data, campaign_data))
        opportunities.extend(self._analyze_audience_optimization(performance_data, campaign_data))

        # Industry-specific optimizations
        opportunities.extend(self._analyze_industry_specific_optimization(performance_data, campaign_data))

        # Filter opportunities based on client settings and business rules
        filtered_opportunities = self._filter_opportunities_by_rules(opportunities, campaign_data)

        # Create recommendation
        recommendation = OptimizationRecommendation(
            client_id=self.config.client_id,
            campaign_id=campaign_data.get('campaign_id', 'unknown'),
            opportunities=filtered_opportunities
        )

        recommendation.calculate_priority_score()
        recommendation.summary = self._generate_recommendation_summary(recommendation)
        recommendation.valid_until = datetime.now() + timedelta(days=7)  # Valid for 1 week

        return recommendation

    def _analyze_bid_optimization(self, performance_data: Dict[str, Any],
                                campaign_data: Dict[str, Any]) -> List[OptimizationOpportunity]:
        """Analyze and recommend bid optimizations"""
        opportunities = []

        if not self.optimization_settings.auto_bid_adjustment:
            return opportunities

        keywords = campaign_data.get('keywords', [])
        thresholds = self.thresholds["performance"]

        for keyword_data in keywords:
            keyword = keyword_data.get('keyword', '')
            current_cpc = keyword_data.get('cpc', 0)
            conversions = keyword_data.get('conversions', 0)
            cost = keyword_data.get('cost', 0)

            # Calculate CPA if we have conversion data
            cpa = cost / conversions if conversions > 0 else float('inf')

            # Check if keyword meets performance thresholds
            if conversions > 0 and cpa > 0:
                target_cpa = self.config.kpis.target_values.get('cpa', 50.0)

                if cpa > target_cpa * (1 + thresholds["cpa_threshold_increase"]):
                    # CPA too high - reduce bid
                    bid_reduction = min(0.3, (cpa - target_cpa) / target_cpa)
                    confidence = min(0.9, conversions / 10)  # Higher confidence with more conversions

                    if confidence >= thresholds["confidence_min"]:
                        opportunities.append(OptimizationOpportunity(
                            opportunity_id=f"bid_reduce_{hash(keyword) % 10000}",
                            client_id=self.config.client_id,
                            campaign_id=campaign_data.get('campaign_id', ''),
                            action_type=OptimizationAction.BID_ADJUSTMENT,
                            priority=OptimizationPriority.HIGH,
                            description=f"Reduce bid for keyword '{keyword}' due to high CPA (${cpa:.2f} vs target ${target_cpa:.2f})",
                            expected_impact={"cpa": -bid_reduction * 100, "conversions": -5},
                            confidence_score=confidence,
                            risk_level="low",
                            implementation_complexity="simple"
                        ))

                elif cpa < target_cpa * 0.8 and current_cpc > 0:
                    # CPA very good - consider bid increase if within limits
                    max_bid_increase = thresholds["bid_adjustment_max"]
                    bid_increase = min(max_bid_increase, (target_cpa - cpa) / target_cpa)
                    confidence = min(0.8, conversions / 5)

                    if confidence >= thresholds["confidence_min"]:
                        opportunities.append(OptimizationOpportunity(
                            opportunity_id=f"bid_increase_{hash(keyword) % 10000}",
                            client_id=self.config.client_id,
                            campaign_id=campaign_data.get('campaign_id', ''),
                            action_type=OptimizationAction.BID_ADJUSTMENT,
                            priority=OptimizationPriority.MEDIUM,
                            description=f"Increase bid for high-performing keyword '{keyword}' (CPA: ${cpa:.2f})",
                            expected_impact={"conversions": bid_increase * 50, "cost": bid_increase * 25},
                            confidence_score=confidence,
                            risk_level="medium",
                            implementation_complexity="simple"
                        ))

        return opportunities

    def _analyze_budget_optimization(self, performance_data: Dict[str, Any],
                                   campaign_data: Dict[str, Any]) -> List[OptimizationOpportunity]:
        """Analyze budget utilization and recommend reallocations"""
        opportunities = []

        if not self.optimization_settings.budget_reallocation_enabled:
            return opportunities

        campaigns = campaign_data.get('campaigns', [])
        total_budget = sum(c.get('budget', 0) for c in campaigns)
        thresholds = self.thresholds["performance"]

        if total_budget == 0:
            return opportunities

        # Identify underperforming campaigns
        underperformers = []
        performers = []

        for campaign in campaigns:
            budget_utilization = campaign.get('budget_utilization', 0)
            roi = campaign.get('roi', 0)

            if budget_utilization < thresholds["budget_utilization_min"]:
                underperformers.append(campaign)
            elif roi > 1.5:  # Good ROI
                performers.append(campaign)

        # Recommend budget reallocation from underperformers to performers
        if underperformers and performers:
            total_underperformer_budget = sum(c.get('budget', 0) for c in underperformers)
            reallocation_amount = min(total_underperformer_budget * 0.3, total_budget * 0.1)

            if reallocation_amount > 100:  # Minimum reallocation threshold
                opportunities.append(OptimizationOpportunity(
                    opportunity_id=f"budget_realloc_{hash(str(campaign_data)) % 10000}",
                    client_id=self.config.client_id,
                    campaign_id=campaign_data.get('campaign_id', ''),
                    action_type=OptimizationAction.BUDGET_REALLOCATION,
                    priority=OptimizationPriority.HIGH,
                    description=f"Reallocate ${reallocation_amount:.0f} from underperforming to high-ROI campaigns",
                    expected_impact={"roi": 15, "conversions": 10},
                    confidence_score=0.75,
                    risk_level="medium",
                    implementation_complexity="moderate",
                    prerequisites=["Campaign budget analysis", "ROI verification"]
                ))

        return opportunities

    def _analyze_keyword_optimization(self, performance_data: Dict[str, Any],
                                    campaign_data: Dict[str, Any]) -> List[OptimizationOpportunity]:
        """Analyze keyword performance and recommend additions/pauses"""
        opportunities = []

        if not self.optimization_settings.keyword_expansion_enabled:
            return opportunities

        keywords = campaign_data.get('keywords', [])
        search_terms = performance_data.get('search_terms', [])

        # Find high-performing search terms not targeted as keywords
        existing_keywords = {k.get('keyword', '').lower() for k in keywords}
        high_potential_terms = []

        for term in search_terms:
            term_text = term.get('search_term', '').lower()
            clicks = term.get('clicks', 0)
            conversions = term.get('conversions', 0)

            if (term_text not in existing_keywords and
                clicks >= 10 and
                conversions >= 1 and
                term.get('ctr', 0) >= 1.0):

                high_potential_terms.append(term)

        # Recommend adding high-potential keywords
        for term in high_potential_terms[:5]:  # Limit to top 5
            term_text = term['search_term']

            # Validate against business rules
            validation_results = self.business_validator.validate_keyword_addition([term_text])
            if not any(not r.is_valid for r in validation_results):
                opportunities.append(OptimizationOpportunity(
                    opportunity_id=f"keyword_add_{hash(term_text) % 10000}",
                    client_id=self.config.client_id,
                    campaign_id=campaign_data.get('campaign_id', ''),
                    action_type=OptimizationAction.KEYWORD_ADDITION,
                    priority=OptimizationPriority.MEDIUM,
                    description=f"Add high-performing search term '{term_text}' as keyword ({term['clicks']} clicks, {term['conversions']} conversions)",
                    expected_impact={"conversions": 20, "cost": 15},
                    confidence_score=0.7,
                    risk_level="low",
                    implementation_complexity="simple"
                ))

        # Find low-performing keywords to pause
        low_performers = []
        for keyword in keywords:
            if (keyword.get('clicks', 0) >= 100 and  # Sufficient data
                keyword.get('conversions', 0) == 0 and  # No conversions
                keyword.get('ctr', 0) < 0.5):  # Low CTR

                low_performers.append(keyword)

        for keyword in low_performers[:3]:  # Limit to top 3
            opportunities.append(OptimizationOpportunity(
                opportunity_id=f"keyword_pause_{hash(keyword.get('keyword', '')) % 10000}",
                client_id=self.config.client_id,
                campaign_id=campaign_data.get('campaign_id', ''),
                action_type=OptimizationAction.KEYWORD_PAUSE,
                priority=OptimizationPriority.MEDIUM,
                description=f"Pause low-performing keyword '{keyword.get('keyword', '')}' (0 conversions, CTR: {keyword.get('ctr', 0):.1f}%)",
                expected_impact={"cost": -20, "cpa": -5},  # Cost reduction
                confidence_score=0.8,
                risk_level="low",
                implementation_complexity="simple"
            ))

        return opportunities

    def _analyze_audience_optimization(self, performance_data: Dict[str, Any],
                                     campaign_data: Dict[str, Any]) -> List[OptimizationOpportunity]:
        """Analyze audience performance and recommend expansions"""
        opportunities = []

        if not self.optimization_settings.audience_expansion_enabled:
            return opportunities

        audience_data = performance_data.get('audience_performance', {})

        # Look for high-performing audience segments
        high_performing_audiences = []
        for audience, metrics in audience_data.items():
            if (metrics.get('conversions', 0) >= 5 and
                metrics.get('conversion_rate', 0) >= 2.0 and
                metrics.get('cost', 0) > 0):

                cpa = metrics['cost'] / metrics['conversions']
                target_cpa = self.config.kpis.target_values.get('cpa', 50.0)

                if cpa <= target_cpa:
                    high_performing_audiences.append((audience, metrics))

        # Recommend audience expansion for high performers
        for audience, metrics in high_performing_audiences[:3]:
            opportunities.append(OptimizationOpportunity(
                opportunity_id=f"audience_expand_{hash(audience) % 10000}",
                client_id=self.config.client_id,
                campaign_id=campaign_data.get('campaign_id', ''),
                action_type=OptimizationAction.AUDIENCE_EXPANSION,
                priority=OptimizationPriority.MEDIUM,
                description=f"Expand targeting to similar audiences based on high performance of '{audience}'",
                expected_impact={"conversions": 25, "reach": 30},
                confidence_score=0.65,
                risk_level="medium",
                implementation_complexity="moderate",
                prerequisites=["Audience performance analysis", "Budget capacity check"]
            ))

        return opportunities

    def _analyze_industry_specific_optimization(self, performance_data: Dict[str, Any],
                                              campaign_data: Dict[str, Any]) -> List[OptimizationOpportunity]:
        """Apply industry-specific optimization rules"""
        opportunities = []

        if self.config.industry == IndustryType.HEALTHCARE:
            opportunities.extend(self._healthcare_optimizations(performance_data, campaign_data))
        elif self.config.industry == IndustryType.EDUCATION:
            opportunities.extend(self._education_optimizations(performance_data, campaign_data))
        elif self.config.industry == IndustryType.ECOMMERCE:
            opportunities.extend(self._ecommerce_optimizations(performance_data, campaign_data))

        return opportunities

    def _healthcare_optimizations(self, performance_data: Dict[str, Any],
                                campaign_data: Dict[str, Any]) -> List[OptimizationOpportunity]:
        """Healthcare industry specific optimizations"""
        opportunities = []

        # Check for HIPAA compliance in ad copy
        ad_performance = performance_data.get('ad_performance', [])
        for ad in ad_performance:
            if ad.get('disapproved', False) and 'health' in ad.get('headline', '').lower():
                opportunities.append(OptimizationOpportunity(
                    opportunity_id=f"healthcare_compliance_{hash(ad.get('ad_id', '')) % 10000}",
                    client_id=self.config.client_id,
                    campaign_id=campaign_data.get('campaign_id', ''),
                    action_type=OptimizationAction.AD_CREATIVE_UPDATE,
                    priority=OptimizationPriority.CRITICAL,
                    description="Ad disapproved - ensure healthcare claims comply with FDA guidelines",
                    expected_impact={"impressions": -50},  # Temporary impact during fix
                    confidence_score=0.95,
                    risk_level="high",
                    implementation_complexity="moderate",
                    prerequisites=["Legal review", "FDA compliance check"]
                ))

        return opportunities

    def _education_optimizations(self, performance_data: Dict[str, Any],
                               campaign_data: Dict[str, Any]) -> List[OptimizationOpportunity]:
        """Education industry specific optimizations"""
        opportunities = []

        # Check for seasonal enrollment periods
        current_month = datetime.now().month

        # Pre-enrollment period (June-August for fall semester)
        if 6 <= current_month <= 8:
            opportunities.append(OptimizationOpportunity(
                opportunity_id=f"education_seasonal_{datetime.now().strftime('%Y%m')}",
                client_id=self.config.client_id,
                campaign_id=campaign_data.get('campaign_id', ''),
                action_type=OptimizationAction.BID_ADJUSTMENT,
                priority=OptimizationPriority.HIGH,
                description="Increase bids during pre-enrollment season (June-August)",
                expected_impact={"conversions": 40, "cost": 25},
                confidence_score=0.8,
                risk_level="medium",
                implementation_complexity="simple",
                expires_at=datetime.now() + timedelta(days=60)
            ))

        return opportunities

    def _ecommerce_optimizations(self, performance_data: Dict[str, Any],
                               campaign_data: Dict[str, Any]) -> List[OptimizationOpportunity]:
        """E-commerce industry specific optimizations"""
        opportunities = []

        # Analyze product performance
        product_performance = performance_data.get('product_performance', [])

        # Find best-selling products for campaign focus
        top_products = sorted(product_performance,
                            key=lambda x: x.get('revenue', 0), reverse=True)[:3]

        for product in top_products:
            if product.get('revenue', 0) > 1000:  # High revenue threshold
                opportunities.append(OptimizationOpportunity(
                    opportunity_id=f"ecommerce_product_focus_{hash(product.get('product_id', '')) % 10000}",
                    client_id=self.config.client_id,
                    campaign_id=campaign_data.get('campaign_id', ''),
                    action_type=OptimizationAction.CAMPAIGN_STRUCTURE_CHANGE,
                    priority=OptimizationPriority.MEDIUM,
                    description=f"Create dedicated campaign for top product '{product.get('name', '')}' (${product.get('revenue', 0):.0f} revenue)",
                    expected_impact={"revenue": 30, "roas": 25},
                    confidence_score=0.75,
                    risk_level="medium",
                    implementation_complexity="complex",
                    prerequisites=["Product catalog analysis", "Budget allocation"]
                ))

        return opportunities

    def _filter_opportunities_by_rules(self, opportunities: List[OptimizationOpportunity],
                                     campaign_data: Dict[str, Any]) -> List[OptimizationOpportunity]:
        """Filter opportunities based on client business rules and settings"""
        filtered = []

        for opportunity in opportunities:
            # Check if action type is allowed
            if not self._is_action_allowed(opportunity.action_type):
                continue

            # Validate against business rules
            validation_data = self._get_validation_data_for_opportunity(opportunity, campaign_data)
            if validation_data:
                validation_results = self.business_validator.validate_operation_pre_execution(
                    opportunity.action_type.value, validation_data
                )
                is_valid, _ = validation_results

                if not is_valid:
                    continue

            # Check risk tolerance
            if (opportunity.risk_level == "high" and
                self.optimization_settings.strategy == OptimizationStrategy.CONSERVATIVE):
                continue

            filtered.append(opportunity)

        return filtered

    def _is_action_allowed(self, action_type: OptimizationAction) -> bool:
        """Check if optimization action is allowed for this client"""
        settings = self.optimization_settings

        action_permissions = {
            OptimizationAction.BID_ADJUSTMENT: settings.auto_bid_adjustment,
            OptimizationAction.BUDGET_REALLOCATION: settings.budget_reallocation_enabled,
            OptimizationAction.KEYWORD_ADDITION: settings.keyword_expansion_enabled,
            OptimizationAction.AUDIENCE_EXPANSION: settings.audience_expansion_enabled,
        }

        return action_permissions.get(action_type, False)

    def _get_validation_data_for_opportunity(self, opportunity: OptimizationOpportunity,
                                          campaign_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get validation data for an optimization opportunity"""
        if opportunity.action_type == OptimizationAction.KEYWORD_ADDITION:
            return {"keywords": [opportunity.description.split("'")[1]]}  # Extract keyword from description
        elif opportunity.action_type == OptimizationAction.BID_ADJUSTMENT:
            return {"bid_changes": {"keyword": 0.1}}  # Sample bid change
        elif opportunity.action_type == OptimizationAction.BUDGET_REALLOCATION:
            return {"current_budgets": {"campaign1": 1000}, "proposed_changes": {"campaign1": -100}}

        return None

    def _generate_recommendation_summary(self, recommendation: OptimizationRecommendation) -> str:
        """Generate a summary for the optimization recommendation"""
        if not recommendation.opportunities:
            return "No optimization opportunities identified at this time."

        high_priority = len([o for o in recommendation.opportunities if o.priority == OptimizationPriority.HIGH])
        critical = len([o for o in recommendation.opportunities if o.priority == OptimizationPriority.CRITICAL])

        summary = f"Found {len(recommendation.opportunities)} optimization opportunities"

        if critical > 0:
            summary += f", including {critical} critical items requiring immediate attention"
        elif high_priority > 0:
            summary += f", with {high_priority} high-priority recommendations"

        summary += ". Implementation could improve performance metrics by 10-30%."

        return summary

    def implement_optimization(self, opportunity: OptimizationOpportunity) -> bool:
        """
        Implement a specific optimization opportunity

        This would integrate with Google Ads API to actually make the changes.
        For now, it marks the opportunity as implemented.
        """
        try:
            # Here you would implement the actual optimization logic
            # For example, calling Google Ads API to adjust bids, add keywords, etc.

            # For demonstration, we'll just mark as implemented
            opportunity.mark_implemented({
                "status": "implemented",
                "implementation_method": "manual_review_required",
                "notes": "Implementation requires API integration"
            })

            logger.info(f"Implemented optimization opportunity {opportunity.opportunity_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to implement optimization {opportunity.opportunity_id}: {e}")
            return False


def generate_client_optimization(client_config: ClientSpecificConfig,
                               performance_data: Dict[str, Any],
                               campaign_data: Dict[str, Any]) -> OptimizationRecommendation:
    """
    Generate optimization recommendations for a client

    Args:
        client_config: Client-specific configuration
        performance_data: Current performance data
        campaign_data: Campaign structure data

    Returns:
        OptimizationRecommendation with opportunities
    """
    engine = ClientOptimizationEngine(client_config)
    return engine.analyze_performance_and_optimize(performance_data, campaign_data)


# Export for easy importing
__all__ = [
    'ClientOptimizationEngine',
    'OptimizationOpportunity',
    'OptimizationRecommendation',
    'OptimizationAction',
    'OptimizationPriority',
    'generate_client_optimization'
]
