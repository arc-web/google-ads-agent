"""
Industry-Specific Modifiers for Google Ads Assets

This module implements industry-specific content modifications as defined in the
Google Ads Asset System Prompt XML. It applies specialized rules for E-commerce,
SaaS, and Healthcare industries to ensure optimal asset performance.

Based on the industry modifiers section in the XML specification.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from asset_rules_parser import IndustryType, AssetType

logger = logging.getLogger(__name__)


class ModifierType(Enum):
    """Types of industry modifiers"""
    CALLOUT_ADDITION = "callout_addition"
    VERB_MODIFICATION = "verb_modification"
    COMPLIANCE_ADDITION = "compliance_addition"
    SUPERLATIVE_REMOVAL = "superlative_removal"
    CONTENT_ENHANCEMENT = "content_enhancement"


@dataclass
class IndustryModifier:
    """Represents a single industry modifier rule"""
    modifier_type: ModifierType
    description: str
    applies_to: List[AssetType]
    condition: Optional[str] = None  # For conditional modifiers
    replacement_rules: Optional[Dict[str, str]] = None


class GoogleAdsIndustryModifiers:
    """
    Industry-specific modifier engine for Google Ads assets

    Applies specialized modifications based on industry vertical to optimize
    asset performance and ensure compliance.
    """

    def __init__(self):
        self._initialize_modifier_rules()

    def _initialize_modifier_rules(self):
        """Initialize industry-specific modifier rules"""

        # E-commerce modifiers
        self.ecommerce_modifiers = [
            IndustryModifier(
                modifier_type=ModifierType.CALLOUT_ADDITION,
                description="Highlight free shipping and easy returns in callouts",
                applies_to=[AssetType.CALLOUT],
                replacement_rules={
                    "add_callouts": ["Free Shipping", "Easy Returns", "Fast Delivery", "Secure Checkout"]
                }
            ),
            IndustryModifier(
                modifier_type=ModifierType.VERB_MODIFICATION,
                description="Use 'Shop', 'View', or 'Buy' as sitelink verbs",
                applies_to=[AssetType.SITELINK],
                replacement_rules={
                    "action_verbs": ["Shop", "Buy", "View", "Order", "Purchase"]
                }
            )
        ]

        # SaaS modifiers
        self.saas_modifiers = [
            IndustryModifier(
                modifier_type=ModifierType.CONTENT_ENHANCEMENT,
                description="Emphasize free trials and demos",
                applies_to=[AssetType.SITELINK, AssetType.CALLOUT],
                replacement_rules={
                    "enhance_content": ["Free Trial", "Demo Available", "Start Free", "Try It Free"]
                }
            ),
            IndustryModifier(
                modifier_type=ModifierType.CALLOUT_ADDITION,
                description="Include 'No credit card' callout",
                applies_to=[AssetType.CALLOUT],
                replacement_rules={
                    "add_callouts": ["No Credit Card Required", "Free Sign Up", "Easy Setup"]
                }
            )
        ]

        # Healthcare modifiers
        self.healthcare_modifiers = [
            IndustryModifier(
                modifier_type=ModifierType.COMPLIANCE_ADDITION,
                description="Add required disclaimers from compliance_notes",
                applies_to=[AssetType.CALLOUT, AssetType.SITELINK, AssetType.PROMOTION],
                replacement_rules={
                    "compliance_addition": "compliance_notes"
                }
            ),
            IndustryModifier(
                modifier_type=ModifierType.SUPERLATIVE_REMOVAL,
                description="Avoid superlatives disallowed by Google policy",
                applies_to=[AssetType.SITELINK, AssetType.CALLOUT, AssetType.STRUCTURED_SNIPPET],
                replacement_rules={
                    "remove_superlatives": ["best", "leading", "top", "premier", "ultimate", "perfect"]
                }
            )
        ]

        # Master modifier dictionary
        self.modifiers = {
            IndustryType.ECOMMERCE: self.ecommerce_modifiers,
            IndustryType.SAAS: self.saas_modifiers,
            IndustryType.HEALTHCARE: self.healthcare_modifiers
        }

    def apply_modifiers(self, asset_content: Dict[str, Any], asset_type: AssetType,
                       industry: IndustryType, compliance_notes: str = "") -> Dict[str, Any]:
        """
        Apply industry-specific modifiers to asset content

        Args:
            asset_content: Original asset content dictionary
            asset_type: Type of asset being modified
            industry: Industry vertical
            compliance_notes: Compliance notes for healthcare industry

        Returns:
            Modified asset content dictionary
        """
        if industry not in self.modifiers:
            return asset_content

        modified_content = asset_content.copy()
        industry_modifiers = self.modifiers[industry]

        for modifier in industry_modifiers:
            if asset_type in modifier.applies_to:
                modified_content = self._apply_single_modifier(
                    modified_content, modifier, compliance_notes
                )

        return modified_content

    def _apply_single_modifier(self, content: Dict[str, Any], modifier: IndustryModifier,
                             compliance_notes: str) -> Dict[str, Any]:
        """Apply a single industry modifier to content"""

        if modifier.modifier_type == ModifierType.CALLOUT_ADDITION:
            return self._apply_callout_addition(content, modifier)

        elif modifier.modifier_type == ModifierType.VERB_MODIFICATION:
            return self._apply_verb_modification(content, modifier)

        elif modifier.modifier_type == ModifierType.CONTENT_ENHANCEMENT:
            return self._apply_content_enhancement(content, modifier)

        elif modifier.modifier_type == ModifierType.COMPLIANCE_ADDITION:
            return self._apply_compliance_addition(content, modifier, compliance_notes)

        elif modifier.modifier_type == ModifierType.SUPERLATIVE_REMOVAL:
            return self._apply_superlative_removal(content, modifier)

        return content

    def _apply_callout_addition(self, content: Dict[str, Any], modifier: IndustryModifier) -> Dict[str, Any]:
        """Add industry-specific callouts to content"""
        if 'text' not in content:
            return content

        add_callouts = modifier.replacement_rules.get('add_callouts', [])
        if add_callouts:
            # Add the first relevant callout that fits character limits
            current_text = content['text']
            for callout in add_callouts:
                # Simple logic: if current text is short, append callout
                if len(current_text) + len(callout) + 2 <= 25:  # +2 for separator
                    content['text'] = f"{current_text} • {callout}"
                    break

        return content

    def _apply_verb_modification(self, content: Dict[str, Any], modifier: IndustryModifier) -> Dict[str, Any]:
        """Modify action verbs in sitelinks for industry optimization"""
        if 'text' not in content:
            return content

        action_verbs = modifier.replacement_rules.get('action_verbs', [])
        current_text = content['text']

        # Replace generic action verbs with industry-specific ones
        for verb in action_verbs:
            # Look for common action verbs to replace
            generic_verbs = ['Get', 'Book', 'Call', 'Save', 'Claim']
            for generic_verb in generic_verbs:
                if current_text.startswith(generic_verb):
                    new_text = current_text.replace(generic_verb, verb, 1)
                    if len(new_text) <= 25:  # Check character limit
                        content['text'] = new_text
                        return content

        return content

    def _apply_content_enhancement(self, content: Dict[str, Any], modifier: IndustryModifier) -> Dict[str, Any]:
        """Enhance content with industry-specific messaging"""
        enhance_content = modifier.replacement_rules.get('enhance_content', [])

        # Apply to sitelink text
        if 'text' in content and enhance_content:
            current_text = content['text']
            for enhancement in enhance_content:
                # Add enhancement if it fits
                if len(current_text) + len(enhancement) + 3 <= 25:  # +3 for " - "
                    content['text'] = f"{current_text} - {enhancement}"
                    break

        return content

    def _apply_compliance_addition(self, content: Dict[str, Any], modifier: IndustryModifier,
                                 compliance_notes: str) -> Dict[str, Any]:
        """Add compliance disclaimers to healthcare content"""
        if not compliance_notes:
            return content

        # Apply compliance notes to appropriate fields
        applicable_fields = ['text', 'description', 'desc1', 'desc2']

        for field in applicable_fields:
            if field in content and isinstance(content[field], str):
                # Check if we can add compliance notes without exceeding limits
                current_content = content[field]
                # For healthcare, compliance notes are often critical, so we might need to replace content
                if len(compliance_notes) <= len(current_content):
                    content[field] = compliance_notes
                else:
                    # Truncate compliance notes to fit
                    truncated_notes = compliance_notes[:len(current_content)]
                    content[field] = truncated_notes

        return content

    def _apply_superlative_removal(self, content: Dict[str, Any], modifier: IndustryModifier) -> Dict[str, Any]:
        """Remove superlatives from healthcare content to ensure compliance"""
        superlatives = modifier.replacement_rules.get('remove_superlatives', [])

        for field, value in content.items():
            if isinstance(value, str):
                modified_value = value
                for superlative in superlatives:
                    # Remove superlative words (case-insensitive)
                    pattern = r'\b' + re.escape(superlative) + r'\b'
                    modified_value = re.sub(pattern, '', modified_value, flags=re.IGNORECASE)

                # Clean up extra spaces
                modified_value = re.sub(r'\s+', ' ', modified_value).strip()
                content[field] = modified_value

        return content

    def get_modifier_summary(self, industry: IndustryType) -> List[str]:
        """Get a summary of modifiers for an industry"""
        if industry not in self.modifiers:
            return []

        return [modifier.description for modifier in self.modifiers[industry]]

    def validate_industry_content(self, content: Dict[str, Any], industry: IndustryType) -> List[str]:
        """
        Validate that content follows industry-specific best practices

        Args:
            content: Asset content to validate
            industry: Industry vertical

        Returns:
            List of validation warnings/suggestions
        """
        warnings = []

        if industry == IndustryType.ECOMMERCE:
            warnings.extend(self._validate_ecommerce_content(content))
        elif industry == IndustryType.SAAS:
            warnings.extend(self._validate_saas_content(content))
        elif industry == IndustryType.HEALTHCARE:
            warnings.extend(self._validate_healthcare_content(content))

        return warnings

    def _validate_ecommerce_content(self, content: Dict[str, Any]) -> List[str]:
        """Validate ecommerce-specific content"""
        warnings = []

        text_content = ' '.join(str(v) for v in content.values() if isinstance(v, str))

        if not any(term in text_content.lower() for term in ['shop', 'buy', 'purchase', 'order']):
            warnings.append("E-commerce content should include shopping action verbs")

        if not any(term in text_content.lower() for term in ['free shipping', 'returns', 'delivery']):
            warnings.append("Consider highlighting shipping and return benefits")

        return warnings

    def _validate_saas_content(self, content: Dict[str, Any]) -> List[str]:
        """Validate SaaS-specific content"""
        warnings = []

        text_content = ' '.join(str(v) for v in content.values() if isinstance(v, str))

        if not any(term in text_content.lower() for term in ['free', 'trial', 'demo', 'start']):
            warnings.append("SaaS content should emphasize free trials and getting started")

        return warnings

    def _validate_healthcare_content(self, content: Dict[str, Any]) -> List[str]:
        """Validate healthcare-specific content"""
        warnings = []

        text_content = ' '.join(str(v) for v in content.values() if isinstance(v, str))

        # Check for potentially problematic terms
        problematic_terms = ['cure', 'guaranteed', 'perfect', 'best', 'leading']
        for term in problematic_terms:
            if term in text_content.lower():
                warnings.append(f"Healthcare content contains potentially restricted term: '{term}'")

        return warnings


# Convenience functions
def apply_industry_modifiers(asset_content: Dict[str, Any], asset_type: AssetType,
                           industry: IndustryType, compliance_notes: str = "") -> Dict[str, Any]:
    """Apply industry modifiers to asset content"""
    modifier_engine = GoogleAdsIndustryModifiers()
    return modifier_engine.apply_modifiers(asset_content, asset_type, industry, compliance_notes)


def get_industry_modifier_summary(industry: IndustryType) -> List[str]:
    """Get summary of modifiers for an industry"""
    modifier_engine = GoogleAdsIndustryModifiers()
    return modifier_engine.get_modifier_summary(industry)


def validate_industry_content(content: Dict[str, Any], industry: IndustryType) -> List[str]:
    """Validate content against industry best practices"""
    modifier_engine = GoogleAdsIndustryModifiers()
    return modifier_engine.validate_industry_content(content, industry)


# Export for easy importing
__all__ = [
    'GoogleAdsIndustryModifiers',
    'ModifierType',
    'IndustryModifier',
    'apply_industry_modifiers',
    'get_industry_modifier_summary',
    'validate_industry_content'
]
