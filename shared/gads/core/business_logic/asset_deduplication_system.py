"""
Asset Deduplication System for Google Ads

This module implements the deduplication system that compares new assets against
existing RSA (Responsive Search Ad) headlines and descriptions using cosine similarity,
as defined in step 6 of the Google Ads Asset System Prompt workflow.

If cosine_similarity ≥ 0.75, the system rewrites the asset to add new value.
"""

import re
import math
from typing import List, Tuple, Dict, Optional, Set
from collections import Counter
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    """Result of similarity comparison"""
    is_similar: bool
    similarity_score: float
    most_similar_text: str
    similarity_details: Dict[str, float]


class CosineSimilarityCalculator:
    """
    Cosine similarity calculator for text comparison

    Uses TF-IDF vectorization and cosine similarity to measure
    semantic similarity between texts.
    """

    def __init__(self):
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'you', 'your'
        }

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts

        Args:
            text1: First text to compare
            text2: Second text to compare

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Preprocess texts
        vec1 = self._text_to_vector(text1)
        vec2 = self._text_to_vector(text2)

        # Calculate cosine similarity
        return self._cosine_similarity(vec1, vec2)

    def _text_to_vector(self, text: str) -> Dict[str, float]:
        """Convert text to TF-IDF vector"""
        # Tokenize and clean
        words = self._tokenize_and_clean(text)

        # Calculate term frequencies
        word_counts = Counter(words)
        total_words = len(words)

        if total_words == 0:
            return {}

        # Simple TF calculation (could be enhanced with IDF)
        vector = {}
        for word, count in word_counts.items():
            tf = count / total_words
            # Apply simple IDF-like weighting for common words
            idf_weight = 1.0 if word not in self.stop_words else 0.5
            vector[word] = tf * idf_weight

        return vector

    def _tokenize_and_clean(self, text: str) -> List[str]:
        """Tokenize and clean text for vectorization"""
        # Convert to lowercase
        text = text.lower()

        # Remove punctuation and special characters
        text = re.sub(r'[^\w\s]', ' ', text)

        # Split into words
        words = text.split()

        # Remove stop words and short words
        filtered_words = [
            word for word in words
            if len(word) > 2 and word not in self.stop_words
        ]

        return filtered_words

    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two vectors"""
        # Get all unique words
        all_words = set(vec1.keys()) | set(vec2.keys())

        if not all_words:
            return 0.0

        # Calculate dot product
        dot_product = sum(vec1.get(word, 0.0) * vec2.get(word, 0.0) for word in all_words)

        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(val ** 2 for val in vec1.values()))
        magnitude2 = math.sqrt(sum(val ** 2 for val in vec2.values()))

        # Avoid division by zero
        if magnitude1 == 0.0 or magnitude2 == 0.0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)


class AssetDeduplicationSystem:
    """
    Deduplication system for Google Ads assets

    Compares new assets against existing RSA content and rewrites
    similar content to add unique value.
    """

    def __init__(self, similarity_threshold: float = 0.75):
        self.similarity_threshold = similarity_threshold
        self.similarity_calculator = CosineSimilarityCalculator()

        # Initialize rewrite strategies
        self._initialize_rewrite_strategies()

    def _initialize_rewrite_strategies(self):
        """Initialize strategies for rewriting similar content"""

        # Action verbs to add uniqueness
        self.action_verbs = [
            "Discover", "Experience", "Explore", "Find", "Get", "Learn",
            "See", "Start", "Try", "Choose", "Select", "Book", "Call"
        ]

        # Benefit modifiers
        self.benefit_modifiers = [
            "Now", "Today", "Fast", "Easy", "Simple", "Quick", "Best",
            "New", "Advanced", "Professional", "Expert", "Trusted"
        ]

        # Question-based openers
        self.question_starters = [
            "Need", "Looking for", "Want", "Ready for", "Searching for"
        ]

        # Location/time modifiers
        self.context_modifiers = [
            "Nearby", "Local", "Today", "Now", "Available", "Open"
        ]

    def check_asset_similarity(self, asset_text: str, rsa_texts: List[str]) -> SimilarityResult:
        """
        Check if asset text is too similar to existing RSA content

        Args:
            asset_text: New asset text to check
            rsa_texts: Existing RSA headlines and descriptions

        Returns:
            SimilarityResult with comparison details
        """
        if not rsa_texts:
            return SimilarityResult(
                is_similar=False,
                similarity_score=0.0,
                most_similar_text="",
                similarity_details={}
            )

        max_similarity = 0.0
        most_similar_text = ""
        similarity_details = {}

        for i, rsa_text in enumerate(rsa_texts):
            similarity = self.similarity_calculator.calculate_similarity(asset_text, rsa_text)
            similarity_details[f"rsa_text_{i}"] = similarity

            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_text = rsa_text

        is_similar = max_similarity >= self.similarity_threshold

        return SimilarityResult(
            is_similar=is_similar,
            similarity_score=max_similarity,
            most_similar_text=most_similar_text,
            similarity_details=similarity_details
        )

    def rewrite_similar_asset(self, asset_text: str, similar_text: str,
                            asset_type: str = "general", max_length: int = 30) -> str:
        """
        Rewrite asset text to add unique value when too similar

        Args:
            asset_text: Original asset text
            similar_text: Similar existing text
            asset_type: Type of asset (affects rewrite strategy)
            max_length: Maximum character length for the asset

        Returns:
            Rewritten text with added unique value
        """
        # Try different rewrite strategies
        rewritten_texts = []

        # Strategy 1: Add action verb at beginning
        rewritten_texts.extend(self._add_action_verb(asset_text, max_length))

        # Strategy 2: Add benefit modifier
        rewritten_texts.extend(self._add_benefit_modifier(asset_text, max_length))

        # Strategy 3: Add question starter
        rewritten_texts.extend(self._add_question_starter(asset_text, max_length))

        # Strategy 4: Add context modifier
        rewritten_texts.extend(self._add_context_modifier(asset_text, max_length))

        # Strategy 5: Rephrase with synonyms
        rewritten_texts.extend(self._rephrase_with_synonyms(asset_text, similar_text, max_length))

        # Filter out texts that are still too similar
        valid_rewrites = []
        for rewritten in rewritten_texts:
            similarity = self.similarity_calculator.calculate_similarity(rewritten, similar_text)
            if similarity < self.similarity_threshold:
                valid_rewrites.append((rewritten, similarity))

        if valid_rewrites:
            # Return the rewrite with lowest similarity to the original similar text
            valid_rewrites.sort(key=lambda x: x[1])  # Sort by similarity score
            return valid_rewrites[0][0]

        # Fallback: If no good rewrites found, truncate and modify original
        return self._fallback_rewrite(asset_text, max_length)

    def _add_action_verb(self, text: str, max_length: int) -> List[str]:
        """Add action verbs to make text more unique"""
        rewrites = []

        for verb in self.action_verbs:
            # Add verb at beginning if it fits
            new_text = f"{verb} {text}"
            if len(new_text) <= max_length:
                rewrites.append(new_text)

            # Try replacing existing action verbs
            words = text.split()
            if words:
                first_word = words[0]
                if first_word in ['Get', 'Book', 'Call', 'Find', 'See']:
                    new_text = text.replace(first_word, verb, 1)
                    if len(new_text) <= max_length:
                        rewrites.append(new_text)

        return rewrites

    def _add_benefit_modifier(self, text: str, max_length: int) -> List[str]:
        """Add benefit modifiers to enhance value proposition"""
        rewrites = []

        for modifier in self.benefit_modifiers:
            # Add at beginning
            new_text = f"{modifier} {text}"
            if len(new_text) <= max_length:
                rewrites.append(new_text)

            # Add at end if it makes sense
            if len(text) + len(modifier) + 1 <= max_length:
                new_text = f"{text} {modifier}"
                rewrites.append(new_text)

        return rewrites

    def _add_question_starter(self, text: str, max_length: int) -> List[str]:
        """Turn statement into question for uniqueness"""
        rewrites = []

        for starter in self.question_starters:
            # Create question format
            question = f"{starter} {text.lower()}?"
            if len(question) <= max_length:
                rewrites.append(question.capitalize())

        return rewrites

    def _add_context_modifier(self, text: str, max_length: int) -> List[str]:
        """Add context modifiers like location or time"""
        rewrites = []

        for modifier in self.context_modifiers:
            new_text = f"{modifier} {text}"
            if len(new_text) <= max_length:
                rewrites.append(new_text)

        return rewrites

    def _rephrase_with_synonyms(self, text: str, similar_text: str, max_length: int) -> List[str]:
        """Rephrase using synonyms to differentiate from similar text"""
        # Simple synonym mapping (could be expanded)
        synonyms = {
            'get': ['obtain', 'receive', 'acquire'],
            'book': ['schedule', 'reserve', 'appoint'],
            'call': ['contact', 'phone', 'reach'],
            'find': ['locate', 'discover', 'find'],
            'see': ['view', 'check', 'look'],
            'best': ['top', 'leading', 'premier'],
            'new': ['latest', 'recent', 'modern'],
            'free': ['complimentary', 'no-cost', 'gratuitous'],
            'easy': ['simple', 'straightforward', 'effortless']
        }

        rewrites = []
        words = text.split()

        # Try replacing words with synonyms
        for i, word in enumerate(words):
            word_lower = word.lower()
            if word_lower in synonyms:
                for synonym in synonyms[word_lower]:
                    new_words = words.copy()
                    new_words[i] = synonym if word.istitle() else synonym.lower()
                    new_text = ' '.join(new_words)

                    if len(new_text) <= max_length:
                        rewrites.append(new_text)

        return rewrites

    def _fallback_rewrite(self, text: str, max_length: int) -> str:
        """Fallback rewrite when other strategies fail"""
        # Simple fallback: add "Now" at beginning or truncate
        if len(f"Now {text}") <= max_length:
            return f"Now {text}"

        # If that doesn't work, just return truncated original
        return text[:max_length].rstrip()

    def deduplicate_asset_batch(self, assets: List[Dict[str, str]], rsa_texts: List[str],
                              asset_type: str = "general") -> Tuple[List[Dict[str, str]], int]:
        """
        Deduplicate a batch of assets against RSA content

        Args:
            assets: List of asset dictionaries
            rsa_texts: Existing RSA content
            asset_type: Type of assets for rewrite strategy

        Returns:
            Tuple of (deduplicated_assets, duplicates_removed_count)
        """
        deduplicated = []
        duplicates_removed = 0

        for asset in assets:
            # Extract text content from asset
            asset_text = self._extract_asset_text(asset)

            if asset_text:
                similarity_result = self.check_asset_similarity(asset_text, rsa_texts)

                if similarity_result.is_similar:
                    # Rewrite to add uniqueness
                    max_length = self._get_asset_max_length(asset_type, asset)
                    rewritten_text = self.rewrite_similar_asset(
                        asset_text, similarity_result.most_similar_text,
                        asset_type, max_length
                    )

                    # Update asset with rewritten text
                    updated_asset = asset.copy()
                    self._update_asset_text(updated_asset, rewritten_text)
                    deduplicated.append(updated_asset)
                    duplicates_removed += 1
                else:
                    deduplicated.append(asset)
            else:
                deduplicated.append(asset)

        return deduplicated, duplicates_removed

    def _extract_asset_text(self, asset: Dict[str, str]) -> str:
        """Extract text content from asset dictionary"""
        text_fields = ['text', 'headline', 'header', 'description', 'desc1', 'desc2']

        text_parts = []
        for field in text_fields:
            if field in asset and asset[field]:
                text_parts.append(asset[field])

        return ' '.join(text_parts).strip()

    def _update_asset_text(self, asset: Dict[str, str], new_text: str):
        """Update asset text field with rewritten content"""
        # Simple strategy: update the primary text field
        if 'text' in asset:
            asset['text'] = new_text
        elif 'headline' in asset:
            asset['headline'] = new_text
        elif 'header' in asset:
            asset['header'] = new_text

    def _get_asset_max_length(self, asset_type: str, asset: Dict[str, str]) -> int:
        """Get maximum length for asset type"""
        # Default limits based on Google Ads specifications
        limits = {
            'sitelink': 25,
            'callout': 25,
            'headline': 30,
            'description': 90,
            'general': 30
        }
        return limits.get(asset_type, 30)


# Convenience functions
def check_asset_similarity(asset_text: str, rsa_texts: List[str],
                         threshold: float = 0.75) -> SimilarityResult:
    """Check similarity between asset and RSA content"""
    system = AssetDeduplicationSystem(threshold)
    return system.check_asset_similarity(asset_text, rsa_texts)


def deduplicate_assets(assets: List[Dict[str, str]], rsa_texts: List[str],
                      asset_type: str = "general") -> Tuple[List[Dict[str, str]], int]:
    """Deduplicate assets against RSA content"""
    system = AssetDeduplicationSystem()
    return system.deduplicate_asset_batch(assets, rsa_texts, asset_type)


# Export for easy importing
__all__ = [
    'AssetDeduplicationSystem',
    'CosineSimilarityCalculator',
    'SimilarityResult',
    'check_asset_similarity',
    'deduplicate_assets'
]
