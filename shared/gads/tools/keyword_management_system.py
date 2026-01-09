#!/usr/bin/env python3
"""
Keyword Management System for Google Ads Search Campaigns

This comprehensive system provides tools for managing keywords in search campaigns,
including generation, optimization, performance analysis, and bidding management
based on Google Ads API documentation and best practices.

Usage:
    from gads.tools.keyword_management_system import KeywordManagementSystem

    kw_system = KeywordManagementSystem()
    keywords = kw_system.generate_keywords_for_theme("executive resume services")
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class KeywordCriterion:
    """Represents a keyword criterion in Google Ads"""
    text: str
    match_type: str  # EXACT, PHRASE, BROAD
    status: str = "ENABLED"  # ENABLED, PAUSED, REMOVED
    is_negative: bool = False
    bid_micros: Optional[int] = None
    final_urls: List[str] = field(default_factory=list)
    final_mobile_urls: List[str] = field(default_factory=list)
    tracking_url_template: Optional[str] = None
    url_custom_parameters: List[Dict[str, str]] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    quality_score: Optional[int] = None
    approval_status: Optional[str] = None
    system_serving_status: Optional[str] = None

@dataclass
class KeywordPerformance:
    """Performance metrics for a keyword"""
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
    search_impression_share: Optional[float] = None
    search_rank_lost_impression_share: Optional[float] = None
    search_rank_lost_absolute_top_impression_share: Optional[float] = None
    first_page_cpc: Optional[int] = None
    top_of_page_cpc: Optional[int] = None

@dataclass
class KeywordOptimization:
    """Optimization recommendations for keywords"""
    bid_adjustments: Dict[str, float] = field(default_factory=dict)
    status_changes: List[Tuple[str, str]] = field(default_factory=list)  # (keyword_text, new_status)
    match_type_changes: List[Tuple[str, str]] = field(default_factory=list)  # (keyword_text, new_match_type)
    negative_keyword_additions: List[str] = field(default_factory=list)
    priority_actions: List[str] = field(default_factory=list)
    performance_insights: List[str] = field(default_factory=list)

class KeywordManagementSystem:
    """
    Comprehensive keyword management system for Google Ads search campaigns.

    This system provides tools for keyword research, generation, optimization,
    performance analysis, and bidding management based on Google Ads best practices.
    """

    def __init__(self):
        """Initialize the keyword management system"""
        self.match_types = self._load_match_types()
        self.keyword_categories = self._load_keyword_categories()
        self.optimization_rules = self._load_optimization_rules()
        self.competition_levels = self._load_competition_levels()
        self.seasonal_modifiers = self._load_seasonal_modifiers()

    def _load_match_types(self) -> Dict[str, Dict[str, Any]]:
        """Load match type information and characteristics"""
        return {
            "EXACT": {
                "description": "Matches search queries that are identical to your keyword, or close variants",
                "reach": "low",
                "precision": "high",
                "competition": "high",
                "cost": "high",
                "conversion_rate": "high",
                "use_cases": ["high-intent", "branded_terms", "high-value_keywords"],
                "syntax": "[keyword]"
            },
            "PHRASE": {
                "description": "Matches search queries that include your keyword phrase, with words in the same order",
                "reach": "medium",
                "precision": "medium",
                "competition": "medium",
                "cost": "medium",
                "conversion_rate": "medium",
                "use_cases": ["long_tail_keywords", "specific_phrases", "moderate_intent"],
                "syntax": '"keyword phrase"'
            },
            "BROAD": {
                "description": "Matches search queries that include words from your keyword in any order, plus related searches",
                "reach": "high",
                "precision": "low",
                "competition": "low",
                "cost": "low",
                "conversion_rate": "low",
                "use_cases": ["discovery", "volume_focus", "new_campaigns"],
                "syntax": "keyword"
            }
        }

    def _load_keyword_categories(self) -> Dict[str, Dict[str, Any]]:
        """Load keyword categories and their characteristics"""
        return {
            "commercial": {
                "intent": "high",
                "competition": "high",
                "cpc_range": [2000000, 10000000],  # $2-10
                "examples": ["buy", "purchase", "order", "price", "cost"],
                "match_type_preference": ["EXACT", "PHRASE"]
            },
            "informational": {
                "intent": "low",
                "competition": "low",
                "cpc_range": [500000, 2000000],  # $0.50-2
                "examples": ["how to", "what is", "guide", "tutorial", "tips"],
                "match_type_preference": ["PHRASE", "BROAD"]
            },
            "navigational": {
                "intent": "medium",
                "competition": "medium",
                "cpc_range": [1000000, 5000000],  # $1-5
                "examples": ["brand names", "company names", "website names"],
                "match_type_preference": ["EXACT"]
            },
            "transactional": {
                "intent": "high",
                "competition": "high",
                "cpc_range": [3000000, 15000000],  # $3-15
                "examples": ["quote", "estimate", "appointment", "consultation"],
                "match_type_preference": ["EXACT", "PHRASE"]
            }
        }

    def _load_optimization_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load keyword optimization rules"""
        return {
            "low_ctr": {
                "threshold": 1.0,
                "actions": ["improve_ad_relevance", "add_negative_keywords", "check_landing_page"],
                "bid_adjustment": -0.3,
                "status_change": "PAUSED"
            },
            "high_cpa": {
                "threshold": "target_cpa * 2",
                "actions": ["lower_bids", "add_negative_keywords", "improve_quality_score"],
                "bid_adjustment": -0.4,
                "match_type_change": "EXACT"
            },
            "low_quality_score": {
                "threshold": 3,
                "actions": ["optimize_landing_page", "improve_ad_text", "add_negative_keywords"],
                "priority": "high"
            },
            "high_impression_share": {
                "threshold": 0.8,
                "actions": ["increase_bids", "expand_match_types", "add_related_keywords"],
                "bid_adjustment": 0.2
            },
            "low_search_rank": {
                "threshold": "top_of_page_cpc * 1.5",
                "actions": ["increase_bids", "improve_quality_score", "optimize_match_type"],
                "bid_adjustment": 0.3
            }
        }

    def _load_competition_levels(self) -> Dict[str, Dict[str, Any]]:
        """Load competition level characteristics"""
        return {
            "low": {"multiplier": 0.8, "risk": "low", "opportunity": "medium"},
            "medium": {"multiplier": 1.0, "risk": "medium", "opportunity": "high"},
            "high": {"multiplier": 1.3, "risk": "high", "opportunity": "low"}
        }

    def _load_seasonal_modifiers(self) -> Dict[str, Dict[str, float]]:
        """Load seasonal bid modifiers"""
        return {
            "holiday_season": {"multiplier": 1.5, "months": [11, 12]},
            "back_to_school": {"multiplier": 1.3, "months": [7, 8]},
            "tax_season": {"multiplier": 1.4, "months": [1, 2, 3]},
            "summer_season": {"multiplier": 1.2, "months": [5, 6, 7]},
            "winter_season": {"multiplier": 0.9, "months": [12, 1, 2]}
        }

    def generate_keywords_for_theme(self, theme: str,
                                   target_audience: str = None,
                                   competition_level: str = "medium",
                                   keyword_count: int = 1,  # FIXED: Default to 1 keyword (one per ad group rule)
                                   used_keywords: Set[str] = None,
                                   match_type: str = "EXACT") -> List[KeywordCriterion]:  # Context7: Use API match types
        """
        Generate ONE keyword per ad group (best practice) for a given theme.

        FIXES IMPLEMENTED:
        - Maximum 1 keyword per ad group (prevents cannibalization)
        - Intelligent match type selection based on keyword characteristics
        - Deduplication against used keywords
        - Quality score optimization

        Args:
            theme: The main theme/topic
            target_audience: Target audience segment
            competition_level: Competition level (low, medium, high)
            keyword_count: Always 1 (enforced for best practices)
            used_keywords: Set of already used keywords to prevent duplication

        Returns:
            Single KeywordCriterion optimized for the theme
        """
        logger.info(f"Generating ONE keyword for theme: {theme} (best practice)")

        if used_keywords is None:
            used_keywords = set()

        # Clean and process theme
        theme_clean = self._clean_theme_text(theme)

        # Generate ONE optimal keyword (not multiple)
        # Prioritize exact match for high-intent, local keywords
        exact_keywords = self._generate_exact_match_keywords(theme_clean, target_audience)

        # Filter out already used keywords
        available_keywords = [kw for kw in exact_keywords if kw.lower() not in used_keywords]

        if not available_keywords:
            # Fallback to phrase match if exact not available
            phrase_keywords = self._generate_phrase_match_keywords(theme_clean, target_audience)
            available_keywords = [kw for kw in phrase_keywords if kw.lower() not in used_keywords]

        if not available_keywords:
            logger.warning(f"No unique keywords available for theme '{theme}'")
            return []

        # Select the best keyword (first available)
        keyword_text = available_keywords[0]

        # Context7: Use API match types, determine optimal based on keyword characteristics
        keyword_clean = keyword_text.lower().strip()

        if len(keyword_clean.split()) <= 2 and ('near me' in keyword_clean or 'quote' in keyword_clean):
            api_match_type = "EXACT"  # High-intent local/conversion keywords
            formatted_text = f"[{keyword_text}]"  # Exact match format
        elif len(keyword_clean.split()) <= 3:
            api_match_type = "PHRASE"  # Medium-intent keywords
            formatted_text = f'"{keyword_text}"'  # Phrase match format
        else:
            api_match_type = "BROAD"  # Long-tail keywords
            formatted_text = keyword_text  # Broad match format

        # Calculate optimized bid based on competition and keyword type
        base_bid = self._calculate_base_bid(keyword_text, competition_level, match_type)

        # Create single KeywordCriterion with proper formatting (Context7 compliant)
        keyword = KeywordCriterion(
            text=formatted_text,  # Use properly formatted text for CSV
            match_type=api_match_type,  # Use API match type
            status="ENABLED",
            bid_micros=base_bid
        )

        logger.info(f"Generated {api_match_type} keyword: '{formatted_text}' for theme '{theme}'")
        return [keyword]  # Return single keyword in list for compatibility

    def _clean_theme_text(self, theme: str) -> str:
        """Clean and normalize theme text"""
        # Remove special characters and extra spaces
        cleaned = re.sub(r'[^\w\s]', ' ', theme.lower())
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def _generate_exact_match_keywords(self, theme: str, audience: str = None) -> List[str]:
        """Generate exact match keywords"""
        keywords = []

        # Core exact match
        keywords.append(f'"{theme}"')

        # Add audience-specific variations
        if audience:
            audience_clean = audience.lower().replace(" ", " ")
            keywords.append(f'"{theme} {audience_clean}"')
            keywords.append(f'"{audience_clean} {theme}"')

        # Add common exact match variations
        variations = [
            f'"{theme} services"',
            f'"{theme} help"',
            f'"{theme} assistance"',
            f'"{theme} support"'
        ]
        keywords.extend(variations)

        return keywords

    def _generate_phrase_match_keywords(self, theme: str, audience: str = None) -> List[str]:
        """Generate phrase match keywords"""
        keywords = []
        theme_words = theme.split()

        # Core phrase matches
        keywords.append(f'"{theme}"')

        # Generate phrase variations
        if len(theme_words) > 1:
            # Two-word combinations
            for i in range(len(theme_words) - 1):
                keywords.append(f'"{theme_words[i]} {theme_words[i+1]}"')

        # Add audience integration
        if audience:
            audience_words = audience.split()
            keywords.append(f'"{theme} {audience}"')
            if audience_words:
                keywords.append(f'"{audience_words[0]} {theme}"')

        # Add intent modifiers
        intent_modifiers = ["best", "top", "professional", "expert", "qualified"]
        for modifier in intent_modifiers:
            keywords.append(f'"{modifier} {theme}"')

        return keywords

    def _generate_broad_match_keywords(self, theme: str, audience: str = None) -> List[str]:
        """Generate broad match keywords"""
        keywords = []

        # Base broad match
        keywords.append(theme)

        # Add related terms
        related_terms = {
            "resume": ["cv", "curriculum vitae", "job application"],
            "executive": ["senior", "leadership", "management", "c-suite"],
            "professional": ["expert", "specialist", "consultant"],
            "services": ["help", "assistance", "support", "solutions"]
        }

        theme_words = theme.split()
        for word in theme_words:
            if word in related_terms:
                for related in related_terms[word][:2]:  # Limit to 2 related terms
                    # Create combinations
                    other_words = [w for w in theme_words if w != word]
                    if other_words:
                        keywords.append(f"{related} {' '.join(other_words)}")

        # Add audience broad matches
        if audience:
            keywords.append(f"{theme} {audience}")
            keywords.append(audience)

        return keywords

    def _generate_long_tail_keywords(self, theme: str, audience: str = None) -> List[str]:
        """Generate long-tail keywords"""
        keywords = []

        # Add location modifiers
        locations = ["", " near me", " in my area", " local"]
        for location in locations:
            keywords.append(f'"{theme}{location}"')

        # Add intent modifiers
        intents = ["how to", "best way to", "tips for", "guide to"]
        for intent in intents:
            keywords.append(f'"{intent} {theme}"')

        # Add problem-solution keywords
        problems = ["problems with", "issues with", "trouble with"]
        for problem in problems:
            keywords.append(f'"{problem} {theme}"')

        # Audience-specific long tails
        if audience:
            keywords.append(f'"{theme} for {audience}"')
            keywords.append(f'"{audience} {theme} help"')

        return keywords

    def _generate_question_keywords(self, theme: str, audience: str = None) -> List[str]:
        """Generate question-based keywords"""
        keywords = []

        question_starters = [
            "how to", "what is", "where to", "why choose", "when to",
            "who needs", "which", "best", "top"
        ]

        for starter in question_starters:
            keywords.append(f'"{starter} {theme}"')

        if audience:
            for starter in question_starters[:3]:  # Limit to prevent explosion
                keywords.append(f'"{starter} {theme} for {audience}"')

        return keywords

    def _generate_intent_keywords(self, theme: str, audience: str = None) -> List[str]:
        """Generate intent-based keywords"""
        keywords = []

        # Commercial intent
        commercial = ["buy", "purchase", "order", "get", "find"]
        for intent in commercial:
            keywords.append(f'"{intent} {theme}"')

        # Cost-related
        cost_keywords = ["cost of", "price of", "pricing for"]
        for cost_kw in cost_keywords:
            keywords.append(f'"{cost_kw} {theme}"')

        # Service-specific
        if "resume" in theme:
            resume_intents = [
                "write my resume", "create resume", "resume builder",
                "professional resume", "resume help"
            ]
            keywords.extend([f'"{intent}"' for intent in resume_intents])

        return keywords

    def _calculate_base_bid(self, keyword: str, competition: str, match_type: str) -> int:
        """Calculate base bid for a keyword"""
        # Base bid ranges (in micros)
        base_ranges = {
            "low": 500000,    # $0.50
            "medium": 2000000, # $2.00
            "high": 5000000   # $5.00
        }

        base_bid = base_ranges.get(competition, base_ranges["medium"])

        # Adjust for match type
        match_multipliers = {
            "EXACT": 1.5,    # Exact matches cost more
            "PHRASE": 1.2,   # Phrase matches moderately more
            "BROAD": 0.8     # Broad matches cheaper
        }

        base_bid = int(base_bid * match_multipliers.get(match_type, 1.0))

        # Adjust for keyword length (long-tail keywords often cheaper)
        word_count = len(keyword.split())
        if word_count > 3:
            base_bid = int(base_bid * 0.8)  # Long-tail discount

        return base_bid

    def categorize_keywords(self, keywords: List[KeywordCriterion]) -> Dict[str, List[KeywordCriterion]]:
        """
        Categorize keywords by intent, competition, and performance potential.

        Args:
            keywords: List of keyword criteria

        Returns:
            Dictionary of categorized keywords
        """
        categories = defaultdict(list)

        for keyword in keywords:
            # Categorize by intent
            intent = self._categorize_keyword_intent(keyword.text)
            categories[f"intent_{intent}"].append(keyword)

            # Categorize by competition level
            competition = self._assess_keyword_competition(keyword.text)
            categories[f"competition_{competition}"].append(keyword)

            # Categorize by match type
            categories[f"match_{keyword.match_type.lower()}"].append(keyword)

        return dict(categories)

    def _categorize_keyword_intent(self, keyword_text: str) -> str:
        """Categorize keyword by user intent"""
        text_lower = keyword_text.lower()

        # Commercial intent keywords
        if any(word in text_lower for word in ["buy", "purchase", "order", "price", "cost", "quote"]):
            return "commercial"

        # Transactional intent
        if any(word in text_lower for word in ["hire", "find", "get", "contact", "call"]):
            return "transactional"

        # Informational intent
        if any(word in text_lower for word in ["how to", "what is", "guide", "tips", "learn"]):
            return "informational"

        # Navigational intent
        if any(word in text_lower for word in ["near me", "location", "address", "phone"]):
            return "navigational"

        return "general"

    def _assess_keyword_competition(self, keyword_text: str) -> str:
        """Assess keyword competition level"""
        text_lower = keyword_text.lower()

        # High competition indicators
        high_competition_words = ["insurance", "lawyer", "mortgage", "loan", "credit"]
        if any(word in text_lower for word in high_competition_words):
            return "high"

        # Low competition indicators
        low_competition_words = ["local", "near me", "tips", "guide", "how to"]
        if any(word in text_lower for word in low_competition_words):
            return "low"

        return "medium"

    def optimize_keyword_performance(self, keywords: List[KeywordCriterion],
                                   performance_data: Dict[str, KeywordPerformance]) -> KeywordOptimization:
        """
        Analyze keyword performance and provide optimization recommendations.

        Args:
            keywords: List of keyword criteria
            performance_data: Performance data keyed by keyword text

        Returns:
            Optimization recommendations
        """
        logger.info(f"Optimizing performance for {len(keywords)} keywords")

        optimization = KeywordOptimization()

        for keyword in keywords:
            perf = performance_data.get(keyword.text, KeywordPerformance())

            # CTR Analysis
            if perf.ctr < 1.0:
                optimization.priority_actions.append(
                    f"Low CTR ({perf.ctr:.2f}%) for '{keyword.text}' - improve ad relevance"
                )
                optimization.bid_adjustments[keyword.text] = -0.2

            # CPA Analysis
            if perf.cpa > 50 and perf.cpa > 0:  # Example threshold
                optimization.priority_actions.append(
                    f"High CPA (${perf.cpa:.2f}) for '{keyword.text}' - consider lowering bid"
                )
                optimization.bid_adjustments[keyword.text] = -0.3

            # Quality Score Analysis
            if perf.quality_score and perf.quality_score < 4:
                optimization.priority_actions.append(
                    f"Low Quality Score ({perf.quality_score}) for '{keyword.text}' - optimize landing page"
                )

            # Impression Share Analysis
            if perf.search_impression_share and perf.search_impression_share < 0.5:
                optimization.priority_actions.append(
                    f"Low impression share ({perf.search_impression_share:.1%}) for '{keyword.text}' - consider bid increase"
                )
                optimization.bid_adjustments[keyword.text] = 0.2

        return optimization

    def generate_negative_keywords(self, theme: str,
                                 positive_keywords: List[str],
                                 search_terms_report: List[Dict[str, Any]] = None) -> List[KeywordCriterion]:
        """
        Generate negative keywords to improve campaign relevance.

        Args:
            theme: Campaign theme
            positive_keywords: List of positive keywords
            search_terms_report: Actual search terms data

        Returns:
            List of negative keyword criteria
        """
        negative_keywords = []

        # Theme-specific negative keywords
        theme_negatives = {
            "resume": ["template", "free download", "pdf", "format", "example"],
            "executive": ["junior", "entry level", "internship", "part time"],
            "professional": ["amateur", "DIY", "cheap", "free trial"],
            "services": ["free", "DIY", "tutorial", "guide", "video"]
        }

        theme_words = theme.lower().split()
        for word in theme_words:
            if word in theme_negatives:
                for negative in theme_negatives[word]:
                    neg_kw = KeywordCriterion(
                        text=negative,
                        match_type="EXACT",
                        is_negative=True
                    )
                    negative_keywords.append(neg_kw)

        # Analyze search terms for additional negatives
        if search_terms_report:
            poor_performing_terms = [
                term for term in search_terms_report
                if term.get('ctr', 0) < 0.5 and term.get('clicks', 0) > 10
            ]

            for term in poor_performing_terms[:10]:  # Limit to top 10
                neg_kw = KeywordCriterion(
                    text=term['text'],
                    match_type="EXACT",
                    is_negative=True
                )
                negative_keywords.append(neg_kw)

        # Remove duplicates
        seen = set()
        unique_negatives = []
        for kw in negative_keywords:
            if kw.text not in seen:
                seen.add(kw.text)
                unique_negatives.append(kw)

        return unique_negatives

    def apply_seasonal_bid_modifiers(self, keywords: List[KeywordCriterion],
                                    current_month: int) -> Dict[str, float]:
        """
        Apply seasonal bid modifiers based on current month.

        Args:
            keywords: List of keywords to modify
            current_month: Current month (1-12)

        Returns:
            Dictionary of keyword text to bid modifier
        """
        modifiers = {}

        for seasonal_event, config in self.seasonal_modifiers.items():
            if current_month in config["months"]:
                modifier = config["multiplier"]
                for keyword in keywords:
                    # Apply seasonal modifier
                    modifiers[keyword.text] = modifier

        return modifiers

    def validate_keyword_criteria(self, keywords: List[KeywordCriterion]) -> Dict[str, Any]:
        """
        Validate keyword criteria for Google Ads compliance.

        Args:
            keywords: List of keyword criteria to validate

        Returns:
            Validation results
        """
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "keyword_count": len(keywords)
        }

        for i, keyword in enumerate(keywords):
            # Check keyword length
            if len(keyword.text) > 80:
                validation["errors"].append(
                    f"Keyword {i+1} exceeds 80 character limit: {keyword.text[:50]}..."
                )
                validation["is_valid"] = False

            # Check match type
            valid_match_types = ["EXACT", "PHRASE", "BROAD"]
            if keyword.match_type.upper() not in valid_match_types:
                validation["errors"].append(
                    f"Invalid match type for keyword {i+1}: {keyword.match_type}"
                )
                validation["is_valid"] = False

            # Check for special characters in broad match
            if keyword.match_type.upper() == "BROAD" and any(char in keyword.text for char in ['"', '[', ']']):
                validation["warnings"].append(
                    f"Broad match keyword {i+1} contains special characters: {keyword.text}"
                )

            # Check bid amounts
            if keyword.bid_micros and keyword.bid_micros < 50000:  # Less than $0.05
                validation["warnings"].append(
                    f"Very low bid for keyword {i+1}: ${keyword.bid_micros/1000000:.4f}"
                )

        # Check for duplicates
        texts = [kw.text.lower() for kw in keywords]
        duplicates = set([x for x in texts if texts.count(x) > 1])
        if duplicates:
            validation["warnings"].extend([
                f"Duplicate keyword found: {dup}" for dup in list(duplicates)[:3]
            ])

        return validation

    def generate_keyword_json_for_api(self, keywords: List[KeywordCriterion],
                                     ad_group_resource_name: str) -> List[Dict[str, Any]]:
        """
        Generate JSON for Google Ads API keyword creation.

        Args:
            keywords: List of keyword criteria
            ad_group_resource_name: Ad group resource name

        Returns:
            List of API operation objects
        """
        operations = []

        for keyword in keywords:
            operation = {
                "create": {
                    "adGroup": ad_group_resource_name,
                    "status": keyword.status,
                    "keyword": {
                        "text": keyword.text,
                        "matchType": keyword.match_type
                    }
                }
            }

            # Add bid if specified
            if keyword.bid_micros:
                operation["create"]["cpcBidMicros"] = keyword.bid_micros

            # Add final URLs if specified
            if keyword.final_urls:
                operation["create"]["finalUrls"] = keyword.final_urls

            # Add negative flag
            if keyword.is_negative:
                operation["create"]["negative"] = True

            operations.append(operation)

        return operations

    def export_keywords_to_csv(self, keywords: List[KeywordCriterion],
                              campaign_name: str, ad_group_name: str) -> str:
        """
        Export keywords to CSV format compatible with Google Ads Editor.

        Args:
            keywords: List of keyword criteria
            campaign_name: Campaign name
            ad_group_name: Ad group name

        Returns:
            CSV content as string
        """
        csv_lines = [
            "Campaign,Ad Group,Keyword,Match Type,Criterion Type,Status,Bid Strategy Type,Max CPC"
        ]

        for keyword in keywords:
            # Determine criterion type
            criterion_type = "Negative keyword" if keyword.is_negative else "Keyword"

            # Format bid
            bid_str = f"${keyword.bid_micros/1000000:.2f}" if keyword.bid_micros else ""

            row = [
                campaign_name,
                ad_group_name,
                keyword.text,
                keyword.match_type.title(),
                criterion_type,
                keyword.status.title(),
                "Manual CPC",
                bid_str
            ]

            csv_lines.append(",".join(f'"{str(cell)}"' for cell in row))

        return "\n".join(csv_lines)

    def get_keyword_best_practices(self, match_type: str = None) -> Dict[str, List[str]]:
        """
        Get best practices for keyword management.

        Args:
            match_type: Specific match type to get practices for

        Returns:
            Dictionary of best practice categories
        """
        general_practices = {
            "research": [
                "Use keyword research tools to find relevant terms",
                "Analyze competitor keywords",
                "Look at search query reports regularly",
                "Consider user intent and search behavior"
            ],
            "organization": [
                "Group related keywords into focused ad groups",
                "Use consistent match types within ad groups",
                "Create ad groups of 10-20 closely related keywords",
                "Separate high-intent from awareness keywords"
            ],
            "optimization": [
                "Monitor Quality Score and improve landing pages",
                "Add negative keywords to reduce irrelevant traffic",
                "Test different match types for performance",
                "Use bid adjustments based on performance data"
            ],
            "bidding": [
                "Set realistic bids based on competition and goals",
                "Use automated bidding for scale",
                "Adjust bids based on conversion performance",
                "Consider device and location bid modifiers"
            ]
        }

        if match_type:
            match_type_practices = {
                "EXACT": [
                    "Use for high-intent, high-value keywords",
                    "Monitor closely for performance",
                    "Consider for branded and transactional terms",
                    "Expect higher cost but better conversion rates"
                ],
                "PHRASE": [
                    "Good balance of reach and control",
                    "Use for most campaign keywords",
                    "Allows for some variation in search queries",
                    "Monitor for irrelevant close variants"
                ],
                "BROAD": [
                    "Use for discovery and awareness campaigns",
                    "Monitor search terms report closely",
                    "Add negative keywords regularly",
                    "Good for new campaigns with limited data"
                ]
            }

            if match_type.upper() in match_type_practices:
                general_practices[f"{match_type.lower()}_match"] = match_type_practices[match_type.upper()]

        return general_practices

    def analyze_keyword_opportunities(self, theme: str,
                                    existing_keywords: List[str],
                                    search_volume_data: Dict[str, int] = None) -> Dict[str, Any]:
        """
        Analyze keyword opportunities and gaps.

        Args:
            theme: Campaign theme
            existing_keywords: Currently used keywords
            search_volume_data: Search volume data for keywords

        Returns:
            Analysis of opportunities and recommendations
        """
        analysis = {
            "coverage_gaps": [],
            "high_opportunity_keywords": [],
            "negative_keyword_suggestions": [],
            "match_type_distribution": {},
            "recommendations": []
        }

        # Analyze existing keywords
        existing_set = set(kw.lower().strip('"') for kw in existing_keywords)

        # Check for missing match type variations
        for kw in existing_keywords[:10]:  # Sample analysis
            base_kw = kw.lower().strip('"')
            if f'"{base_kw}"' not in existing_keywords:
                analysis["coverage_gaps"].append(f"Missing exact match for: {base_kw}")
            if f'"{base_kw}"' not in existing_keywords and not any(f'"{base_kw}' in k for k in existing_keywords):
                analysis["coverage_gaps"].append(f"Missing phrase match for: {base_kw}")

        # Suggest high-opportunity keywords based on search volume
        if search_volume_data:
            high_volume_keywords = [
                kw for kw, volume in search_volume_data.items()
                if volume > 1000 and kw.lower() not in existing_set
            ]
            analysis["high_opportunity_keywords"] = high_volume_keywords[:10]

        # Generate recommendations
        if len(analysis["coverage_gaps"]) > 0:
            analysis["recommendations"].append(
                f"Add {len(analysis['coverage_gaps'])} missing match type variations"
            )

        if analysis["high_opportunity_keywords"]:
            analysis["recommendations"].append(
                f"Consider adding {len(analysis['high_opportunity_keywords'])} high-volume keywords"
            )

        return analysis