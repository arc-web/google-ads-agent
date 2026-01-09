"""
CTR Evaluation Engine for Google Ads Assets

This module implements the CTR (Click-Through Rate) evaluation engine that scores
asset variants based on weighted criteria including benefit focus, keyword matching,
numerical content, emotional appeal, and readability.

Key Features:
- Weighted scoring system based on configurable CTR weights
- Multi-criteria evaluation for different asset types
- Benefit-focused scoring algorithms
- Keyword match analysis
- Numerical content detection
- Emotional language assessment
- Readability scoring
- Performance tracking and optimization
"""

import re
import math
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
from collections import Counter

from asset_rules_parser import (
    CTREvaluationWeights,
    AssetType,
    AssetVariant,
    ValidationResult,
    ValidationSeverity
)

logger = logging.getLogger(__name__)


@dataclass
class CTRScoreBreakdown:
    """Detailed breakdown of CTR score components"""
    benefit_score: float = 0.0
    keyword_match_score: float = 0.0
    number_score: float = 0.0
    emotion_score: float = 0.0
    readability_score: float = 0.0
    total_score: float = 0.0
    weighted_components: Dict[str, float] = field(default_factory=dict)


@dataclass
class CTRMetrics:
    """CTR evaluation metrics for an asset"""
    score_breakdown: CTRScoreBreakdown = field(default_factory=CTRScoreBreakdown)
    keywords_found: List[str] = field(default_factory=list)
    numbers_found: List[str] = field(default_factory=list)
    benefit_words_found: List[str] = field(default_factory=list)
    emotion_words_found: List[str] = field(default_factory=list)
    readability_metrics: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)


class CTREvaluationEngine:
    """
    CTR Evaluation Engine for scoring Google Ads assets

    This engine evaluates assets based on multiple criteria that correlate
    with higher click-through rates in Google Ads.
    """

    def __init__(self, ctr_weights: Optional[CTREvaluationWeights] = None):
        self.weights = ctr_weights or CTREvaluationWeights()

        # Benefit-focused keywords that indicate value propositions
        self.benefit_keywords = {
            'free', 'save', 'discount', 'new', 'best', 'top', 'leading', 'expert',
            'professional', 'certified', 'award-winning', 'guaranteed', 'results',
            'effective', 'proven', 'trusted', 'reliable', 'quality', 'premium',
            'exclusive', 'limited', 'special', 'offer', 'deal', 'bargain', 'value',
            'inexpensive', 'affordable', 'economical', 'budget-friendly', 'cheap'
        }

        # Emotional trigger words
        self.emotion_words = {
            'amazing', 'incredible', 'fantastic', 'excellent', 'wonderful', 'great',
            'awesome', 'superb', 'outstanding', 'exceptional', 'spectacular', 'marvelous',
            'love', 'favorite', 'dream', 'perfect', 'ideal', 'ultimate', 'ultimate',
            'unbeatable', 'unmatched', 'unparalleled', 'extraordinary', 'phenomenal',
            'stunning', 'impressive', 'remarkable', 'astonishing', 'surprising', 'exciting'
        }

        # Action verbs that drive clicks
        self.action_verbs = {
            'get', 'buy', 'shop', 'order', 'call', 'contact', 'visit', 'book',
            'schedule', 'reserve', 'claim', 'download', 'learn', 'discover',
            'find', 'see', 'view', 'check', 'explore', 'start', 'begin', 'try'
        }

        # Words that indicate numbers or quantities
        self.number_indicators = {
            'percent', 'off', 'discount', 'save', '%', '$', 'free', 'new',
            'only', 'just', 'now', 'today', 'limited', 'available', 'spots'
        }

        # Technical writing quality indicators
        self.filler_words = {
            'the', 'a', 'an', 'or', 'and', 'but', 'so', 'very', 'really',
            'just', 'only', 'that', 'this', 'these', 'those', 'i', 'you',
            'it', 'they', 'we', 'he', 'she', 'them', 'their', 'its', 'our'
        }

        self.technical_writing_indicators = {
            'benefit_focused': ['save', 'protect', 'reduce', 'increase', 'improve', 'expert', 'professional'],
            'value_dense': ['premium', 'quality', 'certified', 'guaranteed', 'lifetime', 'professional'],
            'urgency_drivers': ['now', 'today', 'immediate', 'emergency', 'critical', 'limited']
        }

    def evaluate_asset(self, asset: AssetVariant, target_keywords: List[str] = None) -> CTRMetrics:
        """
        Evaluate a single asset variant for CTR potential

        Args:
            asset: Asset variant to evaluate
            target_keywords: Target keywords for relevance scoring

        Returns:
            CTRMetrics: Detailed evaluation metrics
        """
        metrics = CTRMetrics()

        # Extract text content from asset
        text_content = self._extract_text_content(asset)

        # Evaluate each component
        metrics.score_breakdown.benefit_score = self._evaluate_benefit_focus(text_content)
        metrics.score_breakdown.keyword_match_score = self._evaluate_keyword_match(text_content, target_keywords or [])
        metrics.score_breakdown.number_score = self._evaluate_numerical_content(text_content)
        metrics.score_breakdown.emotion_score = self._evaluate_emotional_appeal(text_content)

        # Technical writing quality (replaces readability for value density)
        metrics.score_breakdown.readability_score = self._evaluate_technical_writing_quality(text_content)

        # Calculate weighted total score (technical writing replaces readability)
        metrics.score_breakdown.total_score = self._calculate_weighted_score(metrics.score_breakdown)

        # Update weighted components for transparency (technical writing replaces readability)
        technical_writing_weight = getattr(self.weights, 'technical_writing', self.weights.readability)
        metrics.score_breakdown.weighted_components = {
            'benefit': metrics.score_breakdown.benefit_score * self.weights.benefit,
            'keyword_match': metrics.score_breakdown.keyword_match_score * self.weights.keyword_match,
            'number': metrics.score_breakdown.number_score * self.weights.number,
            'emotion': metrics.score_breakdown.emotion_score * self.weights.emotion,
            'technical_writing': metrics.score_breakdown.readability_score * technical_writing_weight  # Value density scoring
        }

        # Generate suggestions for improvement
        metrics.suggestions = self._generate_improvement_suggestions(metrics, text_content)

        return metrics

    def evaluate_asset_batch(self, assets: List[AssetVariant], target_keywords: List[str] = None) -> Dict[str, CTRMetrics]:
        """
        Evaluate multiple assets and return ranked results

        Args:
            assets: List of asset variants to evaluate
            target_keywords: Target keywords for relevance scoring

        Returns:
            Dict mapping asset IDs to their CTR metrics
        """
        results = {}

        for asset in assets:
            metrics = self.evaluate_asset(asset, target_keywords)
            results[asset.id] = metrics

            # Update asset with calculated score
            asset.ctr_score = metrics.score_breakdown.total_score

        return results

    def rank_assets_by_ctr(self, assets: List[AssetVariant], target_keywords: List[str] = None) -> List[AssetVariant]:
        """
        Rank assets by their CTR potential

        Args:
            assets: List of asset variants to rank
            target_keywords: Target keywords for relevance scoring

        Returns:
            List of assets sorted by CTR score (highest first)
        """
        # Evaluate all assets
        self.evaluate_asset_batch(assets, target_keywords)

        # Sort by CTR score descending
        return sorted(assets, key=lambda x: x.ctr_score, reverse=True)

    def get_top_performers(self, assets: List[AssetVariant], top_n: int = 3,
                          target_keywords: List[str] = None) -> List[AssetVariant]:
        """
        Get top N performing assets by CTR score

        Args:
            assets: List of asset variants
            top_n: Number of top performers to return
            target_keywords: Target keywords for relevance scoring

        Returns:
            List of top performing assets
        """
        ranked = self.rank_assets_by_ctr(assets, target_keywords)
        return ranked[:top_n]

    def _extract_text_content(self, asset: AssetVariant) -> str:
        """Extract all text content from an asset for evaluation"""
        content_parts = []

        if asset.asset_type == AssetType.SITELINK:
            content_parts.extend([
                asset.content.get('text', ''),
                asset.content.get('desc1', ''),
                asset.content.get('desc2', '')
            ])
        elif asset.asset_type == AssetType.CALLOUT:
            content_parts.append(asset.content.get('text', ''))
        elif asset.asset_type == AssetType.STRUCTURED_SNIPPET:
            content_parts.append(asset.content.get('header', ''))
            values = asset.content.get('values', [])
            if isinstance(values, list):
                content_parts.extend(values)
            else:
                content_parts.append(str(values))
        elif asset.asset_type == AssetType.PRICE_ITEM:
            content_parts.extend([
                asset.content.get('header', ''),
                asset.content.get('desc', '')
            ])
        elif asset.asset_type == AssetType.PROMOTION:
            content_parts.extend([
                asset.content.get('occasion', ''),
                asset.content.get('text', '')
            ])
        elif asset.asset_type == AssetType.LEAD_FORM:
            content_parts.extend([
                asset.content.get('headline', ''),
                asset.content.get('cta', '')
            ])
        else:
            # Generic fallback - extract all string values
            for value in asset.content.values():
                if isinstance(value, str):
                    content_parts.append(value)

        return ' '.join(content_parts).strip()

    def _evaluate_benefit_focus(self, text: str) -> float:
        """
        Evaluate how benefit-focused the text is (0.0 to 1.0)

        Looks for benefit keywords, action verbs, and value propositions
        """
        if not text:
            return 0.0

        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)

        # Count benefit keywords
        benefit_count = sum(1 for word in words if word in self.benefit_keywords)

        # Count action verbs
        action_count = sum(1 for word in words if word in self.action_verbs)

        # Look for value propositions (numbers + benefits)
        value_propositions = len(re.findall(r'\$?\d+.*(?:save|off|discount|free)', text_lower))

        # Calculate benefit density
        total_words = len(words)
        if total_words == 0:
            return 0.0

        benefit_density = (benefit_count + action_count + value_propositions) / total_words

        # Position bonus - benefits at the beginning are more impactful
        first_10_words = words[:10]
        front_loaded_benefits = sum(1 for word in first_10_words if word in self.benefit_keywords)

        position_bonus = front_loaded_benefits * 0.1

        # Cap at 1.0 and ensure reasonable scaling
        raw_score = min(1.0, benefit_density * 2.0 + position_bonus)

        return round(raw_score, 3)

    def _evaluate_keyword_match(self, text: str, target_keywords: List[str]) -> float:
        """
        Evaluate keyword relevance (0.0 to 1.0)

        Measures how well the text matches target keywords
        """
        if not text or not target_keywords:
            return 0.0

        text_lower = text.lower()
        matched_keywords = []

        for keyword in target_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in text_lower:
                matched_keywords.append(keyword)

        if not matched_keywords:
            return 0.0

        # Calculate match ratio
        match_ratio = len(matched_keywords) / len(target_keywords)

        # Bonus for exact matches at word boundaries
        exact_matches = 0
        for keyword in matched_keywords:
            if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', text_lower):
                exact_matches += 1

        exact_bonus = exact_matches / len(target_keywords) * 0.2

        return round(min(1.0, match_ratio + exact_bonus), 3)

    def _evaluate_numerical_content(self, text: str) -> float:
        """
        Evaluate presence of numbers and quantities (0.0 to 1.0)

        Numbers often improve CTR by providing specific value propositions
        """
        if not text:
            return 0.0

        # Find numbers (digits, prices, percentages)
        number_patterns = [
            r'\$?\d+(?:\.\d{2})?',  # Prices like $49.99 or 49
            r'\d+%',                # Percentages like 30%
            r'\d+-\d+',            # Ranges like 3-5
            r'\b\d+\b'             # Plain numbers
        ]

        numbers_found = []
        for pattern in number_patterns:
            matches = re.findall(pattern, text)
            numbers_found.extend(matches)

        # Remove duplicates
        numbers_found = list(set(numbers_found))

        if not numbers_found:
            return 0.0

        # Count number indicators (words that make numbers more impactful)
        text_lower = text.lower()
        indicator_count = sum(1 for indicator in self.number_indicators
                            if indicator in text_lower)

        # Score based on number of unique numbers + indicators
        base_score = min(1.0, len(numbers_found) * 0.3)
        indicator_bonus = min(0.3, indicator_count * 0.1)

        return round(base_score + indicator_bonus, 3)

    def _evaluate_emotional_appeal(self, text: str) -> float:
        """
        Evaluate emotional appeal and engagement (0.0 to 1.0)

        Looks for emotionally charged words and engagement triggers
        """
        if not text:
            return 0.0

        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)

        # Count emotional words
        emotion_count = sum(1 for word in words if word in self.emotion_words)

        # Look for emotional punctuation (!!!)
        exclamation_count = text.count('!')
        question_count = text.count('?')

        # Emotional punctuation bonus (but not too much)
        punctuation_score = min(0.2, (exclamation_count + question_count) * 0.05)

        # Calculate emotional density
        total_words = len(words)
        if total_words == 0:
            return 0.0

        emotion_density = emotion_count / total_words

        # Cap and scale appropriately
        raw_score = min(1.0, emotion_density * 3.0 + punctuation_score)

        return round(raw_score, 3)

    def _evaluate_readability(self, text: str) -> float:
        """
        Evaluate text readability and scannability (0.0 to 1.0)

        Measures factors that make text easy to read quickly
        """
        if not text:
            return 0.0

        # Basic readability metrics
        words = re.findall(r'\b\w+\b', text)
        total_words = len(words)

        if total_words == 0:
            return 0.0

        # Average word length (shorter words are more readable)
        avg_word_length = sum(len(word) for word in words) / total_words
        word_length_score = max(0.0, 1.0 - (avg_word_length - 4.0) * 0.1)  # Optimal ~4-5 chars

        # Sentence structure (look for natural breaks)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        avg_sentence_length = total_words / len(sentences) if sentences else total_words
        sentence_score = max(0.0, 1.0 - (avg_sentence_length - 8.0) * 0.05)  # Optimal ~8 words

        # Capitalization (proper case is more readable than ALL CAPS)
        all_caps_ratio = sum(1 for char in text if char.isupper()) / len(text) if text else 0
        caps_score = max(0.0, 1.0 - all_caps_ratio * 2.0)  # Penalize excessive caps

        # Combine readability factors
        readability_score = (word_length_score + sentence_score + caps_score) / 3.0

        return round(readability_score, 3)

    def _evaluate_technical_writing_quality(self, text: str) -> float:
        """
        Evaluate technical writing quality based on value density and lack of filler words

        Technical writing prioritizes:
        - High value density (information per character)
        - Elimination of filler words
        - Precision language
        - Benefit-focused communication

        Returns score from 0-1 where 1 is optimal technical writing
        """
        if not text:
            return 0.0

        words = text.lower().split()
        total_words = len(words)

        if total_words == 0:
            return 0.0

        # Count filler words (negative impact)
        filler_count = sum(1 for word in words if word in self.filler_words)
        filler_ratio = filler_count / total_words

        # Count technical writing indicators (positive impact)
        benefit_words = sum(1 for word in words if word in self.technical_writing_indicators['benefit_focused'])
        value_words = sum(1 for word in words if word in self.technical_writing_indicators['value_dense'])
        urgency_words = sum(1 for word in words if word in self.technical_writing_indicators['urgency_drivers'])

        positive_indicators = benefit_words + value_words + urgency_words
        positive_ratio = positive_indicators / total_words

        # Calculate value density (characters per word weighted by quality)
        avg_word_length = sum(len(word) for word in words) / total_words
        value_density_score = min(1.0, avg_word_length / 6.0)  # Optimal around 6 chars/word

        # Technical writing score combines multiple factors
        filler_penalty = max(0, 1.0 - (filler_ratio * 3))  # Heavy penalty for filler words
        positive_bonus = min(1.0, positive_ratio * 2)  # Bonus for quality indicators
        density_score = value_density_score

        # Weighted combination: 40% no filler, 40% positive indicators, 20% density
        technical_score = (filler_penalty * 0.4) + (positive_bonus * 0.4) + (density_score * 0.2)

        return min(1.0, max(0.0, technical_score))

    def _calculate_weighted_score(self, breakdown: CTRScoreBreakdown) -> float:
        """Calculate weighted total CTR score - Technical Writing Focus"""
        # Use technical_writing weight instead of readability for value density
        technical_writing_weight = getattr(self.weights, 'technical_writing', self.weights.readability)

        weighted_score = (
            breakdown.benefit_score * self.weights.benefit +
            breakdown.keyword_match_score * self.weights.keyword_match +
            breakdown.number_score * self.weights.number +
            breakdown.emotion_score * self.weights.emotion +
            breakdown.readability_score * technical_writing_weight  # Now measures technical writing quality
        )

        return round(weighted_score, 3)

    def _generate_improvement_suggestions(self, metrics: CTRMetrics, text: str) -> List[str]:
        """Generate suggestions for improving CTR score"""
        suggestions = []

        breakdown = metrics.score_breakdown

        # Benefit focus suggestions
        if breakdown.benefit_score < 0.6:
            suggestions.append("Add more benefit-focused words like 'save', 'free', 'best', 'results'")
            suggestions.append("Start with action verbs like 'Get', 'Book', 'Call', 'Save'")

        # Keyword match suggestions
        if breakdown.keyword_match_score < 0.5:
            suggestions.append("Include more target keywords naturally in the copy")

        # Number suggestions
        if breakdown.number_score < 0.4:
            suggestions.append("Add specific numbers, prices, or percentages to show value")

        # Emotion suggestions
        if breakdown.emotion_score < 0.3:
            suggestions.append("Consider adding emotionally engaging words like 'amazing', 'incredible', 'results'")

        # Readability suggestions
        if breakdown.readability_score < 0.7:
            suggestions.append("Use shorter words and break up long sentences")
            if text and text.isupper():
                suggestions.append("Avoid ALL CAPS - use title case instead")

        return suggestions


# Convenience functions
def evaluate_asset_ctr(asset: AssetVariant, target_keywords: List[str] = None,
                      ctr_weights: CTREvaluationWeights = None) -> CTRMetrics:
    """Convenience function to evaluate a single asset"""
    engine = CTREvaluationEngine(ctr_weights)
    return engine.evaluate_asset(asset, target_keywords)


def rank_assets_by_ctr_potential(assets: List[AssetVariant], target_keywords: List[str] = None,
                                ctr_weights: CTREvaluationWeights = None) -> List[AssetVariant]:
    """Convenience function to rank assets by CTR potential"""
    engine = CTREvaluationEngine(ctr_weights)
    return engine.rank_assets_by_ctr(assets, target_keywords)


# Export for easy importing
__all__ = [
    'CTREvaluationEngine',
    'CTRScoreBreakdown',
    'CTRMetrics',
    'evaluate_asset_ctr',
    'rank_assets_by_ctr_potential',
    'evaluate_rsa_combination_performance',
    'evaluate_headline_performance',
    'evaluate_description_performance'
]


# RSA-Specific Evaluation Methods

def evaluate_rsa_combination_performance(headlines: List[str], descriptions: List[str],
                                       paths: Dict[str, str]) -> CTRMetrics:
    """Evaluate RSA combination performance for AI optimization"""
    engine = CTREvaluationEngine()

    # Combine all RSA text for evaluation
    all_text = ' '.join(headlines + descriptions + list(paths.values()))

    # Create mock CTR metrics for RSA combination
    metrics = CTRMetrics()
    metrics.expected_ctr = _calculate_rsa_ctr_potential(all_text, engine)
    metrics.quality_score = _calculate_rsa_quality_score(all_text, engine)
    metrics.competition_level = _assess_rsa_competition(headlines, descriptions)

    # Evaluate technical writing quality
    metrics.score_breakdown.readability_score = engine._evaluate_technical_writing_quality(all_text)
    metrics.score_breakdown.keyword_relevance = _calculate_rsa_keyword_relevance(headlines)
    metrics.score_breakdown.benefit_focus = engine._calculate_benefit_density(all_text)
    metrics.score_breakdown.urgency_drivers = engine._calculate_urgency_signals(all_text)

    # Calculate weighted score
    technical_writing_weight = getattr(engine.weights, 'technical_writing', engine.weights.readability)
    keyword_weight = getattr(engine.weights, 'keyword_relevance', 0.15)
    benefit_weight = getattr(engine.weights, 'benefit_focus', 0.20)
    urgency_weight = getattr(engine.weights, 'urgency_drivers', 0.15)

    metrics.score_breakdown.overall_score = (
        metrics.score_breakdown.readability_score * technical_writing_weight +
        metrics.score_breakdown.keyword_relevance * keyword_weight +
        metrics.score_breakdown.benefit_focus * benefit_weight +
        metrics.score_breakdown.urgency_drivers * urgency_weight
    )

    return metrics


def _calculate_rsa_ctr_potential(text: str, engine: CTREvaluationEngine) -> float:
    """Calculate CTR potential for RSA combination"""
    # Base CTR influenced by technical writing quality
    base_ctr = 0.025  # 2.5% baseline

    # Technical writing quality multiplier
    tech_quality = engine._evaluate_technical_writing_quality(text)
    quality_multiplier = 0.8 + (tech_quality * 0.4)  # 0.8 to 1.2 range

    # Keyword relevance multiplier
    words = text.lower().split()
    keyword_matches = sum(1 for word in words if word in engine.technical_writing_indicators.get('benefit_focused', []))
    relevance_multiplier = 0.9 + min(keyword_matches / 10, 0.2)  # Up to 20% bonus

    return base_ctr * quality_multiplier * relevance_multiplier


def _calculate_rsa_quality_score(text: str, engine: CTREvaluationEngine) -> int:
    """Calculate Google Quality Score estimate for RSA"""
    # Base QS of 5-10
    base_qs = 7

    # Technical writing quality adjustment
    tech_score = engine._evaluate_technical_writing_quality(text)
    qs_adjustment = int(tech_score * 2)  # 0-2 points

    # Keyword relevance adjustment
    words = text.lower().split()
    keyword_density = sum(1 for word in words if word in engine.technical_writing_indicators.get('benefit_focused', [])) / len(words)
    relevance_adjustment = int(keyword_density * 3)  # 0-3 points

    final_qs = min(base_qs + qs_adjustment + relevance_adjustment, 10)
    return max(final_qs, 1)


def _assess_rsa_competition(headlines: List[str], descriptions: List[str]) -> str:
    """Assess competition level for RSA keywords"""
    # Analyze keyword competitiveness based on ad copy
    all_text = ' '.join(headlines + descriptions).lower()

    # High competition indicators
    high_competition_terms = ['insurance', 'hurricane', 'protection', 'guarantee', 'expert']
    high_competition_count = sum(1 for term in high_competition_terms if term in all_text)

    if high_competition_count >= 3:
        return "high"
    elif high_competition_count >= 2:
        return "medium"
    else:
        return "low"


def _calculate_rsa_keyword_relevance(headlines: List[str]) -> float:
    """Calculate keyword relevance score for RSA headlines"""
    # Check if headlines contain keyword variations
    keyword_themes = ['impact', 'windows', 'doors', 'florida', 'protection']

    relevance_scores = []
    for headline in headlines:
        headline_lower = headline.lower()
        matches = sum(1 for theme in keyword_themes if theme in headline_lower)
        relevance_scores.append(min(matches / len(keyword_themes), 1.0))

    return sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0


def evaluate_headline_performance(headline: str) -> CTRMetrics:
    """Evaluate individual headline performance"""
    engine = CTREvaluationEngine()

    metrics = CTRMetrics()
    metrics.expected_ctr = _calculate_rsa_ctr_potential(headline, engine) * 1.2  # Headlines typically have higher CTR
    metrics.quality_score = _calculate_rsa_quality_score(headline, engine)
    metrics.competition_level = "medium"  # Default for individual evaluation

    # Technical writing breakdown
    metrics.score_breakdown.readability_score = engine._evaluate_technical_writing_quality(headline)
    metrics.score_breakdown.keyword_relevance = _calculate_rsa_keyword_relevance([headline])
    metrics.score_breakdown.benefit_focus = engine._calculate_benefit_density(headline)
    metrics.score_breakdown.urgency_drivers = engine._calculate_urgency_signals(headline)

    # Calculate overall score
    metrics.score_breakdown.overall_score = (
        metrics.score_breakdown.readability_score * 0.4 +
        metrics.score_breakdown.keyword_relevance * 0.3 +
        metrics.score_breakdown.benefit_focus * 0.2 +
        metrics.score_breakdown.urgency_drivers * 0.1
    )

    return metrics


def evaluate_description_performance(description: str) -> CTRMetrics:
    """Evaluate individual description performance"""
    engine = CTREvaluationEngine()

    metrics = CTRMetrics()
    metrics.expected_ctr = _calculate_rsa_ctr_potential(description, engine) * 0.8  # Descriptions typically have lower CTR
    metrics.quality_score = _calculate_rsa_quality_score(description, engine)
    metrics.competition_level = "medium"

    # Technical writing breakdown
    metrics.score_breakdown.readability_score = engine._evaluate_technical_writing_quality(description)
    metrics.score_breakdown.keyword_relevance = 0.5  # Descriptions have moderate keyword relevance
    metrics.score_breakdown.benefit_focus = engine._calculate_benefit_density(description)
    metrics.score_breakdown.urgency_drivers = engine._calculate_urgency_signals(description)

    # Calculate overall score
    metrics.score_breakdown.overall_score = (
        metrics.score_breakdown.readability_score * 0.4 +
        metrics.score_breakdown.keyword_relevance * 0.2 +
        metrics.score_breakdown.benefit_focus * 0.25 +
        metrics.score_breakdown.urgency_drivers * 0.15
    )

    return metrics
