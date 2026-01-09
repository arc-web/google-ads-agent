"""
Google Ads Policy Compliance Checker

This module implements comprehensive policy compliance checking for Google Ads assets,
including automatic violation detection and rewriting according to Google Ads policies.

Based on the policy_check step in the Google Ads Asset System Prompt workflow.
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import re
import logging

from asset_rules_parser import IndustryType, ValidationResult, ValidationSeverity

logger = logging.getLogger(__name__)


class PolicyCategory(Enum):
    """Categories of Google Ads policy violations"""
    SUPERLATIVES = "superlatives"
    MISREPRESENTATION = "misrepresentation"
    SENSITIVE_EVENTS = "sensitive_events"
    TRADEMARKS = "trademarks"
    HEALTHCARE_RESTRICTED = "healthcare_restricted"
    ADULT_CONTENT = "adult_content"
    POLITICAL_CONTENT = "political_content"


@dataclass
class PolicyViolation:
    """Represents a policy violation with suggested fixes"""
    category: PolicyCategory
    term: str
    severity: ValidationSeverity
    suggestion: str
    replacement: Optional[str] = None


class GoogleAdsPolicyChecker:
    """
    Comprehensive Google Ads policy compliance checker

    Implements automatic detection and correction of policy violations
    according to Google's advertising policies.
    """

    def __init__(self):
        # Initialize policy violation databases
        self._initialize_policy_databases()

    def _initialize_policy_databases(self):
        """Initialize comprehensive policy violation databases"""

        # Superlatives that Google restricts
        self.superlatives = {
            'best', 'worst', 'greatest', 'finest', 'ultimate', 'perfect',
            'ideal', 'supreme', 'premier', 'top', 'leading', 'chief',
            'number one', 'number 1', '#1', 'first', 'only', 'unique'
        }

        # Misrepresentation terms
        self.misrepresentation = {
            'guaranteed', 'promise', 'assured', 'certain', 'definite',
            'absolute', 'complete', 'total', 'full', '100%', 'proven',
            'scientifically proven', 'clinically proven', 'doctor recommended'
        }

        # Sensitive events and emergency terms
        self.sensitive_events = {
            'emergency', 'urgent', 'crisis', 'critical', 'severe',
            'life-threatening', 'dangerous', 'hazardous', 'emergency room',
            'hospital', 'ambulance', 'paramedic'
        }

        # Healthcare-specific restricted terms
        self.healthcare_restricted = {
            'cure', 'cures', 'treat', 'treats', 'heal', 'heals',
            'prevent', 'prevents', 'diagnose', 'diagnoses', 'medical advice',
            'medical treatment', 'medical cure', 'miracle cure', 'instant cure',
            'permanent cure', 'complete cure', 'total cure'
        }

        # Trademark indicators (would be populated with actual trademarks)
        self.trademark_indicators = {
            '®', '™', 'brand', 'trademark', 'patented', 'patent'
        }

        # Adult content terms
        self.adult_content = {
            'adult', 'xxx', 'porn', 'sex', 'nude', 'naked', 'erotic',
            'sexual', 'intimate', 'escort', 'massage', 'sensual'
        }

        # Political content terms
        self.political_content = {
            'vote', 'election', 'candidate', 'political party', 'ballot',
            'campaign', 'politician', 'government', 'policy', 'law'
        }

        # Policy replacement suggestions
        self.policy_replacements = {
            # Superlatives
            'best': 'quality',
            'perfect': 'excellent',
            'ideal': 'good',
            'ultimate': 'advanced',
            'leading': 'established',
            'top': 'quality',
            'unique': 'special',

            # Misrepresentation
            'guaranteed': 'available',
            'guarantee': 'offer',
            'promise': 'offer',
            'assured': 'available',
            'certain': 'likely',
            'definite': 'available',
            'absolute': 'complete',
            '100%': 'comprehensive',
            'proven': 'effective',

            # Healthcare
            'cure': 'help manage',
            'cures': 'helps manage',
            'treat': 'help manage',
            'treats': 'helps manage',
            'heal': 'improve',
            'heals': 'improves',
            'prevent': 'reduce risk of',
            'prevents': 'helps reduce risk of',
            'diagnose': 'assess',
            'diagnoses': 'assesses',
            'medical advice': 'health information',
            'medical treatment': 'health services',
            'medical cure': 'health improvement',
            'miracle cure': 'significant improvement'
        }

    def check_compliance(self, text: str, industry: IndustryType = IndustryType.OTHER) -> List[ValidationResult]:
        """
        Check text for Google Ads policy violations

        Args:
            text: Text content to check
            industry: Industry type for context-specific rules

        Returns:
            List of validation results for policy violations
        """
        violations = []
        text_lower = text.lower()

        # Check all policy categories
        policy_checks = [
            (PolicyCategory.SUPERLATIVES, self.superlatives),
            (PolicyCategory.MISREPRESENTATION, self.misrepresentation),
            (PolicyCategory.SENSITIVE_EVENTS, self.sensitive_events),
            (PolicyCategory.ADULT_CONTENT, self.adult_content),
            (PolicyCategory.POLITICAL_CONTENT, self.political_content),
        ]

        # Add healthcare-specific checks
        if industry == IndustryType.HEALTHCARE:
            policy_checks.append((PolicyCategory.HEALTHCARE_RESTRICTED, self.healthcare_restricted))

        for category, terms in policy_checks:
            for term in terms:
                if term.lower() in text_lower:
                    severity = self._get_violation_severity(category, term, industry)
                    suggestion = self._get_violation_suggestion(category, term)

                    violation = ValidationResult(
                        is_valid=False,
                        severity=severity,
                        message=f"Policy violation: {category.value} term '{term}' found in content",
                        rule_name=f"policy_{category.value}",
                        suggestion=suggestion
                    )
                    violations.append(violation)

        # Check for trademark issues
        trademark_violations = self._check_trademark_violations(text)
        violations.extend(trademark_violations)

        return violations

    def auto_rewrite(self, text: str, industry: IndustryType = IndustryType.OTHER) -> Tuple[str, List[ValidationResult]]:
        """
        Automatically rewrite text to fix policy violations

        Args:
            text: Original text to rewrite
            industry: Industry type for context-specific rules

        Returns:
            Tuple of (rewritten_text, remaining_violations)
        """
        rewritten_text = text
        violations_found = []

        # Get all violations first
        violations = self.check_compliance(text, industry)

        # Apply automatic fixes
        words = re.findall(r'\b\w+\b', text)
        rewritten_words = []

        for word in words:
            word_lower = word.lower()
            replacement = self.policy_replacements.get(word_lower)

            if replacement:
                # Apply replacement (maintain original casing)
                if word.isupper():
                    replacement = replacement.upper()
                elif word.istitle():
                    replacement = replacement.capitalize()

                rewritten_words.append(replacement)
                violations_found.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    message=f"Auto-replaced policy violation: '{word}' → '{replacement}'",
                    rule_name="auto_policy_rewrite",
                    suggestion="Review auto-replacement for accuracy"
                ))
            else:
                rewritten_words.append(word)

        # Handle multi-word replacements
        rewritten_text = ' '.join(rewritten_words)

        # Fix spacing and punctuation
        rewritten_text = re.sub(r'\s+', ' ', rewritten_text)  # Multiple spaces
        rewritten_text = re.sub(r'\s+([.!?,])', r'\1', rewritten_text)  # Space before punctuation
        rewritten_text = rewritten_text.strip()

        return rewritten_text, violations_found

    def _get_violation_severity(self, category: PolicyCategory, term: str, industry: IndustryType) -> ValidationSeverity:
        """Determine severity level for a policy violation"""
        # Critical violations that will get ads disapproved
        critical_categories = [
            PolicyCategory.HEALTHCARE_RESTRICTED,
            PolicyCategory.ADULT_CONTENT,
            PolicyCategory.POLITICAL_CONTENT
        ]

        if category in critical_categories:
            return ValidationSeverity.CRITICAL

        # High severity for misrepresentation and sensitive events
        if category in [PolicyCategory.MISREPRESENTATION, PolicyCategory.SENSITIVE_EVENTS]:
            return ValidationSeverity.ERROR

        # Medium severity for superlatives
        return ValidationSeverity.WARNING

    def _get_violation_suggestion(self, category: PolicyCategory, term: str) -> str:
        """Get suggestion for fixing a policy violation"""
        replacement = self.policy_replacements.get(term.lower())

        if replacement:
            return f"Replace '{term}' with '{replacement}' or remove it"

        # Generic suggestions based on category
        suggestions = {
            PolicyCategory.SUPERLATIVES: f"Replace superlative '{term}' with specific, factual language",
            PolicyCategory.MISREPRESENTATION: f"Avoid exaggerated claims. Replace '{term}' with factual language",
            PolicyCategory.SENSITIVE_EVENTS: f"Avoid sensitive terms. Replace '{term}' with appropriate medical terminology",
            PolicyCategory.HEALTHCARE_RESTRICTED: f"Healthcare claims must be carefully worded. Replace '{term}' with compliant language",
            PolicyCategory.ADULT_CONTENT: f"Adult content is restricted. Remove or rephrase '{term}'",
            PolicyCategory.POLITICAL_CONTENT: f"Political content has restrictions. Remove or rephrase '{term}'"
        }

        return suggestions.get(category, f"Remove or rephrase the term '{term}' to comply with Google Ads policies")

    def _check_trademark_violations(self, text: str) -> List[ValidationResult]:
        """Check for potential trademark violations"""
        violations = []

        # Check for trademark symbols without proper usage
        if '®' in text or '™' in text:
            violations.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                message="Trademark symbols detected - ensure proper trademark usage and permissions",
                rule_name="trademark_symbol_usage",
                suggestion="Verify trademark ownership and proper usage rights"
            ))

        # Check for common trademark misuse patterns
        trademark_patterns = [
            r'\b(?:and|or|the)\s+(?:best|top|leading|premier)\b',
            r'\b(?:official|authorized|certified)\s+(?:dealer|provider|service)\b'
        ]

        for pattern in trademark_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    message="Potential trademark misuse pattern detected",
                    rule_name="trademark_misuse_pattern",
                    suggestion="Avoid implying exclusive rights or official status without proper authorization"
                ))
                break

        return violations

    def validate_final_content(self, text: str, industry: IndustryType = IndustryType.OTHER) -> bool:
        """
        Final validation to ensure content is policy-compliant

        Args:
            text: Final text content to validate
            industry: Industry type

        Returns:
            True if content passes all policy checks
        """
        violations = self.check_compliance(text, industry)

        # Only allow content with no critical or error violations
        critical_errors = [
            v for v in violations
            if v.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR]
        ]

        return len(critical_errors) == 0


# Convenience functions
def check_google_ads_compliance(text: str, industry: IndustryType = IndustryType.OTHER) -> List[ValidationResult]:
    """Check text for Google Ads policy compliance"""
    checker = GoogleAdsPolicyChecker()
    return checker.check_compliance(text, industry)


def auto_rewrite_for_compliance(text: str, industry: IndustryType = IndustryType.OTHER) -> Tuple[str, List[ValidationResult]]:
    """Auto-rewrite text to fix policy violations"""
    checker = GoogleAdsPolicyChecker()
    return checker.auto_rewrite(text, industry)


# Export for easy importing
__all__ = [
    'GoogleAdsPolicyChecker',
    'PolicyCategory',
    'PolicyViolation',
    'check_google_ads_compliance',
    'auto_rewrite_for_compliance'
]
