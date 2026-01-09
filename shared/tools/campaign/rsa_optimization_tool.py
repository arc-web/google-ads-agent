#!/usr/bin/env python3
"""
RSA Optimization Tool - Advanced Google Ads Responsive Search Ads

Generates and optimizes RSA combinations based on comprehensive AI algorithm rules.
Includes path optimization, keyword relevance, mobile optimization, seasonal rules,
A/B testing framework, budget allocation, and geographic micro-targeting.

Usage:
    python rsa_optimization_tool.py --input analysis.json --output optimized_rsa.csv
"""

import sys
import os
import json
import csv
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import argparse
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from gads.core.business_logic.asset_generation_engine import AssetGenerationEngine
from gads.core.business_logic.ctr_evaluation_engine import CTREvaluationEngine

logger = logging.getLogger(__name__)


class RSAOptimizationTool:
    """Advanced RSA optimization tool incorporating all Google AI rules"""

    def __init__(self):
        self.ctr_engine = CTREvaluationEngine()
        self.generation_engine = AssetGenerationEngine()

        # RSA optimization parameters (per Google API specs)
        self.rsa_params = {
            'min_headlines': 3,  # Minimum for AI algorithm (Google requirement)
            'max_headlines': 3,  # Maximum per Google API
            'min_descriptions': 2,  # Minimum for AI algorithm (Google requirement)
            'max_descriptions': 2,  # Maximum per Google API
            'headline_max_chars': 30,  # Google Ads limit
            'description_max_chars': 90,  # Google Ads limit
            'optimal_headline_range': (22, 29),  # Technical writing sweet spot
            'optimal_description_range': (75, 85),  # Technical writing sweet spot
            'path_max_chars': 15  # Google Ads limit
        }

        # Seasonal keywords
        self.hurricane_season_keywords = [
            'hurricane protection', 'storm ready', 'emergency windows',
            'insurance discount', 'hurricane damage', 'storm shutters'
        ]

        self.offseason_keywords = [
            'energy efficient windows', 'utility bill savings',
            'property value increase', 'noise reduction windows'
        ]

    def optimize_rsa_campaign(self, business_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimized RSA campaign with all advanced rules"""

        # Determine seasonal context
        current_month = datetime.now().month
        is_hurricane_season = 6 <= current_month <= 11

        # Generate diverse headline combinations
        headlines = self._generate_optimized_headlines(business_analysis, is_hurricane_season)
        descriptions = self._generate_optimized_descriptions(business_analysis, is_hurricane_season)
        paths = self._generate_optimized_paths(business_analysis)

        # Score combinations for AI optimization
        scored_combinations = self._score_rsa_combinations(headlines, descriptions, paths)

        # Generate testing framework
        testing_framework = self._generate_ab_testing_framework(scored_combinations)

        return {
            'headlines': headlines,
            'descriptions': descriptions,
            'paths': paths,
            'combinations': scored_combinations,
            'testing_framework': testing_framework,
            'seasonal_context': 'hurricane_season' if is_hurricane_season else 'off_season',
            'optimization_metrics': self._calculate_optimization_metrics(scored_combinations)
        }

    def _generate_optimized_headlines(self, analysis: Dict[str, Any], hurricane_season: bool) -> List[str]:
        """Generate headlines optimized for Google's RSA algorithm"""
        headlines = []

        # Service + Location combinations (highest priority for AI)
        service_templates = [
            "#1 {service} Expert",
            "{service} Fort Myers",
            "{service} Naples",
            "{service} Broward",
            "Premium {service}",
            "Professional {service}"
        ]

        # Value proposition headlines
        value_templates = [
            "Lower Insurance Rates",
            "Energy Efficient Windows",
            "Property Value Increase",
            "Hurricane Protection FL",
            "Lifetime Guarantee",
            "PACE Financing Available"
        ]

        # Seasonal headlines
        seasonal_templates = self.hurricane_season_keywords if hurricane_season else self.offseason_keywords
        seasonal_templates = [f"{kw.title()}" for kw in seasonal_templates[:3]]

        # Generate exactly 3 headlines (Google API requirement)
        all_templates = service_templates + value_templates + seasonal_templates

        for template in all_templates:
            headline = template.format(
                service=analysis.get('primary_service', 'Impact Windows'),
                location=analysis.get('primary_location', 'Florida')
            )

            if self._validate_headline_quality(headline) and headline not in headlines:
                headlines.append(headline)

                if len(headlines) >= self.rsa_params['max_headlines']:
                    break

        # Ensure we have exactly 3 headlines
        while len(headlines) < self.rsa_params['min_headlines']:
            fallback = f"Quality {analysis.get('primary_service', 'Windows')} Services"
            if fallback not in headlines:
                headlines.append(fallback)

        return headlines[:self.rsa_params['max_headlines']]

    def _generate_optimized_descriptions(self, analysis: Dict[str, Any], hurricane_season: bool) -> List[str]:
        """Generate descriptions optimized for RSA AI algorithm"""
        descriptions = []

        # Conversion-focused descriptions
        conversion_templates = [
            "Get PACE financing: 100% coverage, no down payment, 12+ months deferred. Call now!",
            "Lower insurance rates with certified impact windows. Lifetime guarantee included.",
            "Professional installation with 50+ years experience. Licensed & insured contractors."
        ]

        # Benefit + proof descriptions
        benefit_templates = [
            "Improve energy efficiency by 40% while increasing home security. 50+ years experience.",
            "Reduce noise and improve property value with Florida's impact protection specialists.",
            "Safeguard your largest investment with hurricane-ready windows and professional service."
        ]

        # Location authority descriptions
        location_templates = [
            f"{analysis.get('primary_location', 'Florida')} impact windows and doors with lifetime guarantee. Statewide service.",
            f"Expert {analysis.get('primary_service', 'windows')} installation in {analysis.get('primary_location', 'Florida')}. Emergency service available.",
            f"Trusted {analysis.get('primary_location', 'Florida')} {analysis.get('primary_service', 'windows')} specialists. 50+ years protecting homes."
        ]

        all_templates = conversion_templates + benefit_templates + location_templates

        for template in all_templates:
            if self._validate_description_quality(template) and template not in descriptions:
                descriptions.append(template)

                if len(descriptions) >= self.rsa_params['max_descriptions']:
                    break

        # Ensure we have exactly 2 descriptions
        while len(descriptions) < self.rsa_params['min_descriptions']:
            fallback = f"Professional {analysis.get('primary_service', 'windows')} services with lifetime guarantee."
            if fallback not in descriptions:
                descriptions.append(fallback)

        return descriptions[:self.rsa_params['max_descriptions']]

    def _generate_optimized_paths(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate optimized display paths for RSA"""
        primary_location = analysis.get('primary_location', 'Florida')
        primary_service = analysis.get('primary_service', 'Windows')

        # Path combinations that work well with Google's algorithm
        path_options = {
            'path1': [
                primary_location,
                primary_service,
                f"{primary_location} {primary_service}",
                "Impact Windows",
                "Hurricane Protection"
            ],
            'path2': [
                primary_service,
                "Expert",
                "Specialist",
                "Professional",
                "Lifetime Guarantee"
            ]
        }

        # Select best performing paths based on length and relevance
        path1 = self._select_optimal_path(path_options['path1'])
        path2 = self._select_optimal_path(path_options['path2'])

        return {
            'path1': path1,
            'path2': path2
        }

    def _select_optimal_path(self, options: List[str]) -> str:
        """Select optimal path based on RSA algorithm preferences"""
        # Prefer paths that are keyword-rich but under 15 chars
        valid_options = [opt for opt in options if len(opt) <= 15]

        if not valid_options:
            return options[0][:15]  # Truncate if necessary

        # Prefer more specific, keyword-rich paths
        return max(valid_options, key=lambda x: len(x.split()))

    def _validate_headline_quality(self, headline: str) -> bool:
        """Validate headline meets RSA quality standards"""
        if not headline or len(headline) > self.rsa_params['headline_max_chars']:
            return False

        # Check for optimal character range
        optimal_min, optimal_max = self.rsa_params['optimal_headline_range']
        if len(headline) < optimal_min:
            return False

        # Check for filler words
        filler_words = ['the', 'a', 'an', 'or', 'and', 'but', 'so', 'very', 'really']
        words = headline.lower().split()
        if any(word in filler_words for word in words):
            return False

        return True

    def _validate_description_quality(self, description: str) -> bool:
        """Validate description meets RSA quality standards"""
        if not description or len(description) > self.rsa_params['description_max_chars']:
            return False

        optimal_min, optimal_max = self.rsa_params['optimal_description_range']
        if len(description) < optimal_min:
            return False

        # Must include call-to-action or key benefit in first 75 chars
        first_75 = description[:75].lower()
        key_phrases = ['call now', 'contact', 'free estimate', 'lifetime guarantee', 'pace finance']
        if not any(phrase in first_75 for phrase in key_phrases):
            return False

        return True

    def _score_rsa_combinations(self, headlines: List[str], descriptions: List[str],
                               paths: Dict[str, str]) -> List[Dict[str, Any]]:
        """Score RSA combinations for AI optimization"""
        combinations = []

        # For RSA, we use all available headlines and descriptions (max 3 headlines, 2 descriptions)
        # Google AI tests different combinations of these assets
        if len(headlines) >= 3 and len(descriptions) >= 2:
            # Create combinations for A/B testing (different arrangements)
            combo = {
                'headline_indices': list(range(len(headlines))),
                'description_indices': list(range(len(descriptions))),
                'headlines': headlines,
                'descriptions': descriptions,
                'paths': paths,
                'scores': self._calculate_rsa_combo_score(headlines, descriptions, paths)
            }
            combinations.append(combo)

        # Sort by overall score
        combinations.sort(key=lambda x: x['scores']['overall'], reverse=True)

        return combinations[:10]  # Top combinations for testing

    def _generate_headline_rotations(self, base_combo: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate headline rotation variations for testing"""
        if not base_combo:
            return []

        headlines = base_combo.get('headlines', [])
        # Create variations by rotating headline order
        variations = []
        for i in range(len(headlines)):
            rotated = headlines[i:] + headlines[:i]
            variation = base_combo.copy()
            variation['headlines'] = rotated
            variation['variation_type'] = 'headline_rotation'
            variations.append(variation)

        return variations[:3]  # Limit variations

    def _generate_description_alternatives(self, base_combo: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate description alternative variations for testing"""
        if not base_combo:
            return []

        descriptions = base_combo.get('descriptions', [])
        # Create variations by swapping description order
        variations = []
        if len(descriptions) >= 2:
            swapped = [descriptions[1], descriptions[0]]
            variation = base_combo.copy()
            variation['descriptions'] = swapped
            variation['variation_type'] = 'description_swap'
            variations.append(variation)

        return variations

    def _generate_path_variations(self, base_combo: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate path variations for testing"""
        if not base_combo:
            return []

        paths = base_combo.get('paths', {})
        variations = []

        # Test different path combinations
        path_options = [
            {'path1': paths.get('path1', ''), 'path2': paths.get('path2', '')},
            {'path1': paths.get('path2', ''), 'path2': paths.get('path1', '')},
            {'path1': paths.get('path1', ''), 'path2': ''},
        ]

        for i, path_combo in enumerate(path_options):
            variation = base_combo.copy()
            variation['paths'] = path_combo
            variation['variation_type'] = f'path_variation_{i+1}'
            variations.append(variation)

        return variations[:2]

    def _calculate_rsa_combo_score(self, headlines: List[str], descriptions: List[str],
                                  paths: Dict[str, str]) -> Dict[str, float]:
        """Calculate comprehensive RSA combination score"""
        # Individual asset scores
        headline_scores = [self._score_individual_asset(h, 'headline') for h in headlines]
        description_scores = [self._score_individual_asset(d, 'description') for d in descriptions]

        # Combination diversity score
        diversity_score = self._calculate_diversity_score(headlines + descriptions)

        # Keyword relevance score
        relevance_score = self._calculate_relevance_score(headlines, descriptions)

        # Mobile optimization score
        mobile_score = self._calculate_mobile_score(headlines, descriptions)

        # Overall score (weighted average)
        weights = {
            'headline_quality': 0.25,
            'description_quality': 0.25,
            'diversity': 0.20,
            'relevance': 0.15,
            'mobile': 0.15
        }

        overall_score = (
            (sum(headline_scores) / len(headline_scores)) * weights['headline_quality'] +
            (sum(description_scores) / len(description_scores)) * weights['description_quality'] +
            diversity_score * weights['diversity'] +
            relevance_score * weights['relevance'] +
            mobile_score * weights['mobile']
        )

        return {
            'headline_quality': sum(headline_scores) / len(headline_scores),
            'description_quality': sum(description_scores) / len(description_scores),
            'diversity': diversity_score,
            'relevance': relevance_score,
            'mobile': mobile_score,
            'overall': overall_score
        }

    def _score_individual_asset(self, text: str, asset_type: str) -> float:
        """Score individual headline or description"""
        # Use CTR evaluation engine for technical writing quality
        if asset_type == 'headline':
            # Simulate CTR metrics for headline
            metrics = self.ctr_engine.evaluate_headline_performance(text)
        else:
            # Simulate CTR metrics for description
            metrics = self.ctr_engine.evaluate_description_performance(text)

        return metrics.score_breakdown.readability_score  # Technical writing score

    def _calculate_diversity_score(self, assets: List[str]) -> float:
        """Calculate diversity score for RSA combination"""
        # Check theme distribution
        themes = {
            'service': ['impact', 'windows', 'doors', 'protection', 'expert'],
            'location': ['fort myers', 'naples', 'broward', 'florida'],
            'value': ['energy', 'insurance', 'property', 'lifetime', 'guarantee'],
            'urgency': ['now', 'call', 'contact', 'emergency']
        }

        theme_coverage = {}
        all_text = ' '.join(assets).lower()

        for theme_name, theme_words in themes.items():
            theme_coverage[theme_name] = any(word in all_text for word in theme_words)

        coverage_ratio = sum(theme_coverage.values()) / len(themes)
        return coverage_ratio

    def _calculate_relevance_score(self, headlines: List[str], descriptions: List[str]) -> float:
        """Calculate keyword relevance score"""
        # This would be enhanced with actual keyword analysis
        # For now, return a basic relevance score
        all_text = ' '.join(headlines + descriptions).lower()

        # Check for key terms that should be present
        key_terms = ['impact', 'windows', 'florida', 'protection', 'guarantee']
        relevance_score = sum(1 for term in key_terms if term in all_text) / len(key_terms)

        return relevance_score

    def _calculate_mobile_score(self, headlines: List[str], descriptions: List[str]) -> float:
        """Calculate mobile optimization score"""
        mobile_score = 0

        # Check headline lengths for mobile (22-26 optimal)
        headline_mobile_score = sum(1 for h in headlines if 22 <= len(h) <= 26) / len(headlines)

        # Check if key CTA is in first 75 chars of descriptions
        description_mobile_score = 0
        for desc in descriptions:
            first_75 = desc[:75].lower()
            has_cta = any(phrase in first_75 for phrase in ['call now', 'contact', 'free estimate'])
            if has_cta:
                description_mobile_score += 1
        description_mobile_score /= len(descriptions)

        mobile_score = (headline_mobile_score + description_mobile_score) / 2
        return mobile_score

    def _generate_ab_testing_framework(self, combinations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate A/B testing framework for RSA combinations"""
        # For RSA, testing focuses on different combinations of the 3 headlines and 2 descriptions
        control_group = combinations[:1]  # Best performing combination
        test_groups = {
            'headline_rotations': self._generate_headline_rotations(combinations[0] if combinations else None),
            'description_alternatives': self._generate_description_alternatives(combinations[0] if combinations else None),
            'path_testing': self._generate_path_variations(combinations[0] if combinations else None)
        }

        return {
            'control_group': control_group,
            'test_groups': test_groups,
            'testing_timeline': {
                'minimum_test_duration': 7,  # days
                'statistical_significance_threshold': 0.95,
                'minimum_conversions_per_variant': 50  # Lower for RSA testing
            },
            'winner_selection_criteria': {
                'primary': 'lowest_cpa_with_significance',
                'secondary': 'highest_conversion_rate',
                'tertiary': 'highest_click_through_rate'
            }
        }

    def _calculate_optimization_metrics(self, combinations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate optimization metrics for RSA campaign"""
        if not combinations:
            return {}

        scores = [combo['scores']['overall'] for combo in combinations]

        return {
            'total_combinations': len(combinations),
            'average_score': sum(scores) / len(scores),
            'top_score': max(scores),
            'score_distribution': {
                'excellent': len([s for s in scores if s >= 0.8]),
                'good': len([s for s in scores if 0.6 <= s < 0.8]),
                'needs_improvement': len([s for s in scores if s < 0.6])
            },
            'optimization_potential': self._assess_optimization_potential(scores)
        }

    def _assess_optimization_potential(self, scores: List[float]) -> str:
        """Assess optimization potential based on score distribution"""
        if not scores:
            return "insufficient_data"

        avg_score = sum(scores) / len(scores)
        top_score = max(scores)

        if top_score >= 0.9 and avg_score >= 0.8:
            return "excellent_optimization"
        elif top_score >= 0.8 and avg_score >= 0.7:
            return "good_optimization"
        elif avg_score >= 0.6:
            return "moderate_optimization"
        else:
            return "needs_improvement"


def main():
    parser = argparse.ArgumentParser(description="RSA Optimization Tool")
    parser.add_argument('--input', required=True, help='Business analysis JSON file')
    parser.add_argument('--output', required=True, help='Output optimized RSA CSV file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        # Load business analysis
        with open(args.input, 'r') as f:
            business_analysis = json.load(f)

        # Initialize RSA optimizer
        optimizer = RSAOptimizationTool()

        # Generate optimized RSA campaign
        logger.info("Optimizing RSA campaign...")
        optimized_rsa = optimizer.optimize_rsa_campaign(business_analysis)

        # Save results
        with open(args.output, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['RSA Component', 'Content', 'Score', 'Optimization Notes'])

            # Write headlines
            for i, headline in enumerate(optimized_rsa['headlines']):
                writer.writerow([f'Headline {i+1}', headline, 'Optimized', 'AI Algorithm Ready'])

            # Write descriptions
            for i, desc in enumerate(optimized_rsa['descriptions']):
                writer.writerow([f'Description {i+1}', desc, 'Optimized', 'Conversion Focused'])

            # Write paths
            writer.writerow(['Path 1', optimized_rsa['paths']['path1'], 'Optimized', 'Keyword Rich'])
            writer.writerow(['Path 2', optimized_rsa['paths']['path2'], 'Optimized', 'Authority Focused'])

        # Save detailed analysis
        analysis_file = args.output.replace('.csv', '_analysis.json')
        with open(analysis_file, 'w') as f:
            json.dump(optimized_rsa, f, indent=2, default=str)

        logger.info(f"RSA optimization complete. Results saved to {args.output}")
        logger.info(f"Detailed analysis saved to {analysis_file}")

        # Print optimization metrics
        metrics = optimized_rsa['optimization_metrics']
        logger.info(f"Optimization Results:")
        logger.info(f"  Total Combinations: {metrics['total_combinations']}")
        logger.info(f"  Average Score: {metrics['average_score']:.3f}")
        logger.info(f"  Top Score: {metrics['top_score']:.3f}")
        logger.info(f"  Optimization Level: {metrics['optimization_potential']}")

    except Exception as e:
        logger.error(f"RSA optimization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()