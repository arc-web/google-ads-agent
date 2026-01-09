"""
Asset Generation Engine for Google Ads

This module implements the core asset generation workflow defined in the Google Ads Asset System Prompt XML.
It orchestrates the complete asset creation process following the exact workflow steps specified.

Workflow Steps:
1. generate_draft_assets - Produce initial text for every extension type
2. char_limit_check - Truncate lines at word boundary if they exceed limits
3. policy_check - Lint against Google Ads policies and rewrite automatically
4. ctr_eval - Score every line on the five criteria weighted in ctr_weights
5. variant_generation - Loop until N high-scoring variants exist per asset
6. deduplicate_vs_rsa - Compare against RSA headlines/descriptions
7. output_assets - Return final payload valid XML conforming to schema
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher

from asset_rules_parser import (
    AssetGenerationConfig,
    AssetInputs,
    AssetType,
    AssetVariant,
    ValidationResult,
    ValidationSeverity,
    IndustryType,
    parse_asset_rules_xml
)
from ctr_evaluation_engine import CTREvaluationEngine
from price_asset_builder import PriceAssetBuilder

logger = logging.getLogger(__name__)


@dataclass
class AssetGenerationResult:
    """Result of asset generation process"""
    assets: List[AssetVariant] = field(default_factory=list)
    workflow_log: List[Dict[str, Any]] = field(default_factory=list)
    debug_log: List[Dict[str, Any]] = field(default_factory=list)
    final_output_xml: Optional[str] = None
    generation_stats: Dict[str, Any] = field(default_factory=dict)


class PolicyComplianceChecker:
    """
    Google Ads Policy Compliance Checker

    Implements automatic linting and rewriting for Google Ads policies.
    """

    def __init__(self):
        # Google Ads policy violations that require rewriting
        self.policy_violations = {
            'superlatives': [
                'best', 'worst', 'greatest', 'finest', 'ultimate', 'perfect',
                'ideal', 'supreme', 'premier', 'top', 'leading', 'chief'
            ],
            'misrepresentation': [
                'guaranteed', 'promise', 'assured', 'certain', 'definite',
                'absolute', 'complete', 'total', 'full', '100%'
            ],
            'sensitive_events': [
                'emergency', 'urgent', 'crisis', 'critical', 'severe',
                'life-threatening', 'dangerous', 'hazardous'
            ],
            'trademarks': [],  # Would be populated with known trademark terms
            'restricted_health': [
                'cure', 'treat', 'heal', 'prevent', 'diagnose', 'medical advice'
            ]
        }

        # Replacement mappings for policy violations
        self.policy_replacements = {
            'guaranteed': 'helps',
            'promise': 'offer',
            'assured': 'available',
            'certain': 'likely',
            'perfect': 'excellent',
            'ideal': 'good',
            'best': 'quality',
            'leading': 'established',
            'cure': 'support',
            'treat': 'help',
            'heal': 'improve',
            'prevent': 'reduce risk of'
        }

    def check_and_rewrite(self, text: str, industry: IndustryType = IndustryType.OTHER) -> Tuple[str, List[ValidationResult]]:
        """
        Check text for policy violations and rewrite automatically

        Args:
            text: Text to check and potentially rewrite
            industry: Industry type for context-specific rules

        Returns:
            Tuple of (rewritten_text, validation_results)
        """
        rewritten_text = text
        violations = []

        # Check for policy violations
        for category, terms in self.policy_violations.items():
            for term in terms:
                if term.lower() in text.lower():
                    # Special handling for healthcare industry
                    if industry == IndustryType.HEALTHCARE and category == 'restricted_health':
                        violations.append(ValidationResult(
                            is_valid=False,
                            severity=ValidationSeverity.CRITICAL,
                            message=f"Healthcare content contains restricted term: '{term}'",
                            rule_name="healthcare_policy_violation"
                        ))
                        # Replace with compliant alternative
                        if term in self.policy_replacements:
                            rewritten_text = rewritten_text.replace(term, self.policy_replacements[term])
                    elif category in ['superlatives', 'misrepresentation']:
                        violations.append(ValidationResult(
                            is_valid=False,
                            severity=ValidationSeverity.ERROR,
                            message=f"Content contains {category} term: '{term}'",
                            rule_name="policy_violation",
                            suggestion=f"Replace with: {self.policy_replacements.get(term, 'more specific term')}"
                        ))
                        # Auto-replace
                        if term in self.policy_replacements:
                            rewritten_text = rewritten_text.replace(term, self.policy_replacements[term])

        return rewritten_text, violations


class IndustryModifiers:
    """
    Industry-specific content modifiers as defined in the XML rules
    """

    def __init__(self):
        self.modifiers = {
            IndustryType.ECOMMERCE: [
                "Highlight free shipping and easy returns in callouts",
                "Use 'Shop', 'View', or 'Buy' as sitelink verbs"
            ],
            IndustryType.SAAS: [
                "Emphasize free trials and demos",
                "Include 'No credit card' callout"
            ],
            IndustryType.HEALTHCARE: [
                "Add required disclaimers from compliance_notes",
                "Avoid superlatives disallowed by Google policy"
            ]
        }

    def get_modifiers(self, industry: IndustryType) -> List[str]:
        """Get modifiers for specific industry"""
        return self.modifiers.get(industry, [])

    def apply_modifiers(self, content: Dict[str, Any], industry: IndustryType,
                       compliance_notes: str = "") -> Dict[str, Any]:
        """Apply industry-specific modifications to content"""
        modified_content = content.copy()
        modifiers = self.get_modifiers(industry)

        for modifier in modifiers:
            if industry == IndustryType.HEALTHCARE:
                if "disclaimers" in modifier.lower() and compliance_notes:
                    # Add compliance notes to appropriate fields
                    if 'callout' in modified_content:
                        modified_content['callout'] = f"{modified_content['callout']} {compliance_notes}"
                    elif 'description' in modified_content:
                        modified_content['description'] = f"{modified_content['description']} {compliance_notes}"

        return modified_content


class AssetDeduplicationSystem:
    """
    Deduplication system that compares assets against RSA content using cosine similarity
    """

    def __init__(self, similarity_threshold: float = 0.75):
        self.similarity_threshold = similarity_threshold

    def check_similarity(self, asset_text: str, rsa_texts: List[str]) -> Tuple[bool, float, str]:
        """
        Check if asset text is too similar to existing RSA content

        Args:
            asset_text: New asset text to check
            rsa_texts: Existing RSA headlines and descriptions

        Returns:
            Tuple of (is_similar, similarity_score, most_similar_text)
        """
        if not rsa_texts:
            return False, 0.0, ""

        max_similarity = 0.0
        most_similar_text = ""

        for rsa_text in rsa_texts:
            similarity = self._calculate_similarity(asset_text, rsa_text)
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_text = rsa_text

        is_similar = max_similarity >= self.similarity_threshold
        return is_similar, max_similarity, most_similar_text

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using sequence matching"""
        # Normalize texts
        text1_norm = text1.lower().strip()
        text2_norm = text2.lower().strip()

        # Use sequence matcher for similarity
        matcher = SequenceMatcher(None, text1_norm, text2_norm)
        return matcher.ratio()

    def rewrite_for_uniqueness(self, asset_text: str, similar_text: str) -> str:
        """
        Rewrite asset text to add unique value when too similar to existing content

        Args:
            asset_text: Original asset text
            similar_text: Similar existing text

        Returns:
            Rewritten text with added unique value
        """
        # Simple strategy: add benefit-focused modifiers
        benefit_modifiers = [
            "Save Time With",
            "Discover",
            "Experience",
            "Get Started With",
            "Choose",
            "Select"
        ]

        # Find the main subject and add a modifier
        words = asset_text.split()
        if len(words) > 2:
            # Insert modifier after first 1-2 words
            insert_pos = min(2, len(words) // 2)
            modifier = benefit_modifiers[len(asset_text) % len(benefit_modifiers)]
            words.insert(insert_pos, modifier)
            return ' '.join(words)

        return asset_text


class AssetGenerationEngine:
    """
    Core asset generation engine implementing the workflow from the XML specification
    """

    def __init__(self, config: Optional[AssetGenerationConfig] = None):
        self.config = config or AssetGenerationConfig()
        self.ctr_engine = CTREvaluationEngine(self.config.ctr_weights)
        self.policy_checker = PolicyComplianceChecker()
        self.industry_modifiers = IndustryModifiers()
        self.deduplication_system = AssetDeduplicationSystem()

        # Initialize specialized builders
        self.price_builder = PriceAssetBuilder()

    def generate_assets(self, inputs: AssetInputs, debug: bool = False) -> AssetGenerationResult:
        """
        Execute the complete asset generation workflow

        Args:
            inputs: Asset generation inputs
            debug: Enable debug logging

        Returns:
            AssetGenerationResult with generated assets and logs
        """
        result = AssetGenerationResult()
        result.generation_stats = {
            'start_time': datetime.now(),
            'total_assets_generated': 0,
            'variants_created': 0,
            'policy_violations_fixed': 0,
            'duplicates_removed': 0
        }

        # Step 1: generate_draft_assets
        self._log_workflow_step(result, "generate_draft_assets", "Starting draft asset generation")
        draft_assets = self._generate_draft_assets(inputs)
        result.generation_stats['total_assets_generated'] = len(draft_assets)

        # Step 2-5: variant_generation loop (includes char_limit_check, policy_check, ctr_eval)
        self._log_workflow_step(result, "variant_generation", f"Generating {self.config.variant_generation.default_n} variants per asset")
        final_assets = self._generate_variants(draft_assets, inputs, result, debug)

        # Step 6: deduplicate_vs_rsa
        self._log_workflow_step(result, "deduplicate_vs_rsa", "Checking for duplicates against RSA content")
        final_assets = self._deduplicate_assets(final_assets, inputs, result)

        # Step 7: output_assets
        self._log_workflow_step(result, "output_assets", "Generating final XML output")
        result.final_output_xml = self._generate_output_xml(final_assets, inputs)

        result.assets = final_assets
        result.generation_stats['end_time'] = datetime.now()
        result.generation_stats['duration_seconds'] = (
            result.generation_stats['end_time'] - result.generation_stats['start_time']
        ).total_seconds()

        return result

    def _generate_draft_assets(self, inputs: AssetInputs) -> List[AssetVariant]:
        """Step 1: Generate initial draft assets for all extension types"""
        assets = []

        # Generate assets for each type defined in the output schema
        for asset_type_name, asset_schema in self.config.output_schema.items():
            try:
                asset_type = AssetType[asset_type_name.upper()]

                # Generate content based on asset type and inputs
                content = self._generate_asset_content(asset_type, inputs)

                # Apply industry modifiers
                industry = IndustryType(inputs.industry_vertical.upper()) if inputs.industry_vertical else IndustryType.OTHER
                content = self.industry_modifiers.apply_modifiers(content, industry, inputs.compliance_notes)

                # Create asset variant
                asset = AssetVariant(
                    id=f"draft_{asset_type_name}_{len(assets)}",
                    asset_type=asset_type,
                    content=content
                )

                assets.append(asset)

            except KeyError:
                logger.warning(f"Unknown asset type: {asset_type_name}")
                continue

        return assets

    def _generate_asset_content(self, asset_type: AssetType, inputs: AssetInputs) -> Dict[str, Any]:
        """Generate content for specific asset type based on inputs"""
        content = {}

        if asset_type == AssetType.SITELINK:
            content.update({
                'text': self._generate_sitelink_text(inputs),
                'desc1': self._generate_sitelink_desc1(inputs),
                'desc2': self._generate_sitelink_desc2(inputs)
            })
        elif asset_type == AssetType.CALLOUT:
            content['text'] = self._generate_callout_text(inputs)
        elif asset_type == AssetType.STRUCTURED_SNIPPET:
            content.update({
                'header': "Conditions Treated",
                'values': ["Back, neck, shoulder pain"]
            })
        elif asset_type == AssetType.PRICE_ITEM:
            content.update({
                'header': f"${inputs.core_offer.split('$')[1] if '$' in inputs.core_offer else inputs.core_offer} {inputs.business_name}",
                'price': inputs.core_offer.split('$')[1] if '$' in inputs.core_offer else inputs.core_offer,
                'desc': f"New patient special - {inputs.unique_selling_points}"
            })
        elif asset_type == AssetType.PROMOTION:
            content.update({
                'occasion': "New Patient Offer",
                'text': inputs.promo_details
            })
        elif asset_type == AssetType.CALL:
            content['phone_number'] = inputs.phone_number
        elif asset_type == AssetType.IMAGE:
            content.update({
                'src_prompt': f"Professional image of {inputs.business_name} healthcare services",
                'alt_text': f"{inputs.business_name} healthcare clinic"
            })
        elif asset_type == AssetType.LEAD_FORM:
            content.update({
                'headline': f"Claim Your {inputs.core_offer}",
                'cta': "Book Now"
            })
        elif asset_type == AssetType.LOCATION:
            content['feedLink'] = "GMB_LOCATION_ID"

        return content

    def _generate_sitelink_text(self, inputs: AssetInputs) -> str:
        """Generate sitelink text using CTR best practices"""
        base_text = f"Claim {inputs.core_offer}"
        if inputs.locations and inputs.locations.lower() != "nationwide":
            base_text = f"{inputs.locations.split(',')[0]} {base_text}"
        return self._truncate_to_limit(base_text, self.config.char_limits.sitelink)

    def _generate_sitelink_desc1(self, inputs: AssetInputs) -> str:
        """Generate sitelink description 1"""
        desc = f"Consult plus {inputs.unique_selling_points.split('•')[0].strip()}"
        return self._truncate_to_limit(desc, self.config.char_limits.sitelink_desc)

    def _generate_sitelink_desc2(self, inputs: AssetInputs) -> str:
        """Generate sitelink description 2"""
        if '$' in inputs.promo_details:
            desc = f"Save on first visit"
        else:
            desc = f"Limited spots available"
        return self._truncate_to_limit(desc, self.config.char_limits.sitelink_desc)

    def _generate_callout_text(self, inputs: AssetInputs) -> str:
        """Generate callout text"""
        callouts = [
            inputs.core_offer,
            "Doctor-Led Consultation",
            inputs.unique_selling_points.split('•')[0].strip() if '•' in inputs.unique_selling_points else inputs.unique_selling_points,
            "Non-Invasive Treatment",
            "Targets Root Cause",
            "15-Minute Sessions",
            "No Drugs, No Surgery",
            "2M Patients Trust Us",
            "Limited Spots Available"
        ]

        # Return first callout that fits
        for callout in callouts:
            if len(callout) <= self.config.char_limits.callout:
                return callout

        # Fallback: truncate first one
        return self._truncate_to_limit(callouts[0], self.config.char_limits.callout)

    def _generate_variants(self, draft_assets: List[AssetVariant], inputs: AssetInputs,
                          result: AssetGenerationResult, debug: bool) -> List[AssetVariant]:
        """Step 2-5: Generate variants with validation and scoring"""
        final_assets = []

        for draft_asset in draft_assets:
            variants = [draft_asset]  # Start with the draft

            # Generate additional variants if needed
            while len(variants) < self.config.variant_generation.default_n:
                variant = self._create_variant(draft_asset, inputs)
                if variant:
                    variants.append(variant)

            # Process each variant through the pipeline
            processed_variants = []
            for variant in variants:
                # Step 2: char_limit_check
                variant = self._apply_char_limits(variant)

                # Step 3: policy_check
                variant, policy_violations = self._apply_policy_check(variant, inputs)
                result.generation_stats['policy_violations_fixed'] += len(policy_violations)

                # Step 4: ctr_eval
                ctr_metrics = self.ctr_engine.evaluate_asset(variant, [inputs.business_name, inputs.core_offer])
                variant.ctr_score = ctr_metrics.score_breakdown.total_score

                # Only keep variants that pass minimum CTR threshold
                if variant.ctr_score >= 0.5:  # Minimum threshold
                    processed_variants.append(variant)

                if debug:
                    result.debug_log.append({
                        'step': 'variant_processing',
                        'asset_id': variant.id,
                        'ctr_score': variant.ctr_score,
                        'policy_violations': len(policy_violations)
                    })

            # Keep top variants by CTR score
            processed_variants.sort(key=lambda x: x.ctr_score, reverse=True)
            top_variants = processed_variants[:self.config.variant_generation.default_n]

            final_assets.extend(top_variants)
            result.generation_stats['variants_created'] += len(top_variants)

        return final_assets

    def _create_variant(self, base_asset: AssetVariant, inputs: AssetInputs) -> Optional[AssetVariant]:
        """Create a variant of the base asset with modifications"""
        import copy
        variant = copy.deepcopy(base_asset)
        variant.id = f"{base_asset.id}_v{len([v for v in [base_asset] if v.id.startswith(base_asset.id)]) + 1}"

        # Apply simple variations based on CTR best practices
        for key, value in variant.content.items():
            if isinstance(value, str):
                # Add action verbs at the beginning
                if not any(action_verb in value.lower() for action_verb in ['get', 'book', 'call', 'save', 'claim']):
                    action_verbs = ['Get', 'Book', 'Call', 'Save', 'Claim']
                    variant.content[key] = f"{action_verbs[len(value) % len(action_verbs)]} {value}"

                # Add numbers if beneficial
                if '$' not in value and len(value) < self._get_char_limit(base_asset.asset_type, key) - 5:
                    variant.content[key] = f"$49 {value}"

        return variant

    def _apply_char_limits(self, asset: AssetVariant) -> AssetVariant:
        """Step 2: Apply character limits by truncating/extending to fit optimal window"""
        for key, value in asset.content.items():
            if isinstance(value, str):
                max_limit = self._get_char_limit(asset.asset_type, key)
                min_limit = self._get_min_char_limit(asset.asset_type, key)

                if len(value) > max_limit:
                    # Truncate if too long
                    asset.content[key] = self._truncate_to_limit(value, max_limit)
                elif len(value) < min_limit:
                    # Try to extend if too short (for headlines/descriptions)
                    if key in ['headline', 'description']:
                        asset.content[key] = self._extend_to_minimum(value, min_limit, max_limit)

        return asset

    def _apply_policy_check(self, asset: AssetVariant, inputs: AssetInputs) -> Tuple[AssetVariant, List[ValidationResult]]:
        """Step 3: Apply policy compliance checking and auto-rewriting"""
        industry = IndustryType(inputs.industry_vertical.upper()) if inputs.industry_vertical else IndustryType.OTHER
        all_violations = []

        for key, value in asset.content.items():
            if isinstance(value, str):
                rewritten, violations = self.policy_checker.check_and_rewrite(value, industry)
                asset.content[key] = rewritten
                all_violations.extend(violations)

        return asset, all_violations

    def _deduplicate_assets(self, assets: List[AssetVariant], inputs: AssetInputs,
                           result: AssetGenerationResult) -> List[AssetVariant]:
        """Step 6: Deduplicate against RSA content"""
        if not inputs.rsa_headlines and not inputs.rsa_descriptions:
            return assets

        rsa_texts = inputs.rsa_headlines + inputs.rsa_descriptions
        deduplicated = []

        for asset in assets:
            asset_text = self.ctr_engine._extract_text_content(asset)
            is_similar, similarity, similar_text = self.deduplication_system.check_similarity(asset_text, rsa_texts)

            if is_similar:
                # Rewrite to add unique value
                new_text = self.deduplication_system.rewrite_for_uniqueness(asset_text, similar_text)

                # Update asset content (simplified - would need more sophisticated parsing in real implementation)
                if asset.asset_type == AssetType.SITELINK and 'text' in asset.content:
                    asset.content['text'] = new_text[:self.config.char_limits.sitelink]

                result.generation_stats['duplicates_removed'] += 1
            else:
                deduplicated.append(asset)

        return deduplicated

    def _generate_output_xml(self, assets: List[AssetVariant], inputs: AssetInputs) -> str:
        """Step 7: Generate final XML output conforming to schema"""
        root = ET.Element("assets")

        for asset in assets:
            asset_elem = ET.SubElement(root, asset.asset_type.value)

            # Add content as attributes or child elements based on schema
            for key, value in asset.content.items():
                if isinstance(value, str):
                    asset_elem.set(key, value)
                elif isinstance(value, list):
                    # Handle lists (like structured snippet values)
                    asset_elem.set(key, ', '.join(value))

        # Wrap in google_ads_assets element
        wrapper = ET.Element("google_ads_assets")
        wrapper.append(root)

        # Convert to string
        rough_string = ET.tostring(wrapper, encoding='unicode')
        return self._prettify_xml(rough_string)

    def _truncate_to_limit(self, text: str, max_length: int) -> str:
        """Truncate text at word boundary if it exceeds limit"""
        if len(text) <= max_length:
            return text

        truncated = text[:max_length]
        last_space = truncated.rfind(' ')

        if last_space > max_length * 0.8:  # If space is reasonably close to limit
            truncated = truncated[:last_space]

        return truncated.rstrip()

    def _get_char_limit(self, asset_type: AssetType, field: str) -> int:
        """Get character limit for specific asset type and field (Google Ads official limits)"""
        limits = {
            'sitelink': self.config.char_limits.sitelink_text,  # 25 chars
            'desc1': self.config.char_limits.sitelink_desc,     # 35 chars
            'desc2': self.config.char_limits.sitelink_desc,     # 35 chars
            'text': self.config.char_limits.callout,            # 25 chars
            'header': self.config.char_limits.structured_snippet_header,  # 25 chars
            'values': self.config.char_limits.structured_snippet_value,   # 25 chars
            'description': self.config.char_limits.description,  # 90 chars
            'headline': self.config.char_limits.headline,       # 30 chars
            'long_headline': self.config.char_limits.long_headline  # 90 chars
        }
        return limits.get(field, 25)  # Default fallback

    def _get_min_char_limit(self, asset_type: AssetType, field: str) -> int:
        """Get minimum character limit for specific asset type and field"""
        min_limits = {
            'sitelink': self.config.char_limits.sitelink_text_min,
            'desc1': self.config.char_limits.sitelink_desc_min,
            'desc2': self.config.char_limits.sitelink_desc_min,
            'text': self.config.char_limits.callout_min,
            'header': self.config.char_limits.structured_snippet_header_min,
            'values': self.config.char_limits.structured_snippet_value_min,
            'description': self.config.char_limits.description_min,
            'headline': self.config.char_limits.headline_min,
            'long_headline': self.config.char_limits.long_headline_min
        }
        return min_limits.get(field, 10)  # Default fallback

    def _extend_to_minimum(self, text: str, min_limit: int, max_limit: int) -> str:
        """Try to extend text to meet minimum character requirements with valuable content"""
        if len(text) >= min_limit:
            return text

        # Rotate through multiple extension strategies to find the best fit
        extensions_by_type = {
            'headline': {
                'executive': [
                    " For C-Suite Professionals", " - Expert Executive Writers", " Services",
                    " - Get Hired Faster", " - Career Advancement", " - Trusted Experts"
                ],
                'resume': [
                    " Writing Services", " - Professional Help", " For Job Seekers",
                    " - ATS-Optimized", " - Expert Writers", " - Get Results"
                ],
                'career': [
                    " Coaching Services", " - Expert Guidance", " Support",
                    " - Job Search Help", " - Career Success", " - Professional Coaching"
                ],
                'linkedin': [
                    " Profile Optimization", " - Professional Writing", " Services",
                    " - Stand Out Online", " - Recruiter-Ready", " - Expert Help"
                ]
            },
            'description': {
                'executive': [
                    " Trusted by C-suite professionals nationwide for executive career advancement.",
                    " Results-driven executive resume writing that gets you hired faster.",
                    " Connect with top executive recruiters and land your dream leadership role.",
                    " ATS-optimized executive resumes designed for senior-level positions.",
                    " Award-winning executive resume specialists with proven success rates."
                ],
                'resume': [
                    " Professional resume writing services that showcase your career achievements.",
                    " ATS-optimized resume creation for better job search results.",
                    " Expert resume writers with years of experience in career services.",
                    " Comprehensive resume packages designed to get you noticed by recruiters.",
                    " Quality resume writing that highlights your professional strengths."
                ],
                'career': [
                    " Expert career coaching and professional development services available.",
                    " Comprehensive job search assistance and career transition support.",
                    " Professional career guidance to help you achieve your goals.",
                    " Results-oriented career services with proven success methods.",
                    " Trusted career professionals helping job seekers nationwide."
                ],
                'linkedin': [
                    " Professional LinkedIn profile optimization for executive visibility.",
                    " Stand out in executive job searches with optimized LinkedIn profiles.",
                    " Increase profile views and attract top recruiters with expert optimization.",
                    " Professional LinkedIn writing services for career advancement.",
                    " LinkedIn profile enhancement that showcases your executive expertise."
                ]
            }
        }

        # Determine content type and category
        content_type = 'description' if len(text) > 30 else 'headline'
        category = 'executive'  # Default category

        text_lower = text.lower()
        for cat in extensions_by_type[content_type]:
            if any(keyword in text_lower for keyword in cat.split()):
                category = cat
                break

        # Try extensions in order of preference
        extensions = extensions_by_type[content_type].get(category, [])

        for ext in extensions:
            if content_type == 'headline':
                candidate = text + ext
            else:  # description
                candidate = text + ext

            if min_limit <= len(candidate) <= max_limit:
                return candidate

        # If no extensions work, try more aggressive shortening/extension
        if len(text) < min_limit:
            # For headlines, try different strategies
            if content_type == 'headline':
                fallback_extensions = [" Services", " - Expert Help", " Solutions"]
                for ext in fallback_extensions:
                    candidate = text + ext
                    if len(candidate) >= min_limit:
                        return candidate[:max_limit]  # Truncate if needed
            else:
                # For descriptions, try minimal extension
                candidate = text + " Contact us today to learn more."
                if len(candidate) >= min_limit:
                    return candidate[:max_limit]

        # If all else fails, return original text (will be caught by validation)
        return text

    def _log_workflow_step(self, result: AssetGenerationResult, step_name: str, message: str):
        """Log workflow step execution"""
        result.workflow_log.append({
            'step': step_name,
            'timestamp': datetime.now(),
            'message': message
        })

    def _prettify_xml(self, xml_string: str) -> str:
        """Pretty-print XML string"""
        import xml.dom.minidom
        dom = xml.dom.minidom.parseString(xml_string)
        return dom.toprettyxml(indent="  ")


# Convenience functions
def generate_google_ads_assets(xml_rules: str, inputs: AssetInputs, debug: bool = False) -> AssetGenerationResult:
    """Generate Google Ads assets using XML rules and inputs"""
    config = parse_asset_rules_xml(xml_rules)
    engine = AssetGenerationEngine(config)
    return engine.generate_assets(inputs, debug)


# Export for easy importing
__all__ = [
    'AssetGenerationEngine',
    'AssetGenerationResult',
    'PolicyComplianceChecker',
    'IndustryModifiers',
    'AssetDeduplicationSystem',
    'generate_google_ads_assets'
]
