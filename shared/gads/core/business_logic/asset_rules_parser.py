"""
Google Ads Asset Rules Parser and Configuration System

This module parses and implements the Google Ads asset generation rules from XML
system prompts, providing a structured configuration system for automated asset
creation, validation, and optimization.

Key Features:
- XML parsing for asset generation rules
- CTR evaluation engine with weighted scoring
- Industry-specific modifiers and compliance rules
- Asset variant generation and optimization
- Policy compliance checking
- Winner promotion logic with performance tracking
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import re
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class AssetType(Enum):
    """Supported Google Ads asset types"""
    SITELINK = "sitelink"
    CALLOUT = "callout"
    STRUCTURED_SNIPPET = "structured_snippet"
    PRICE_ITEM = "price_item"
    PROMOTION = "promotion"
    CALL = "call"
    IMAGE = "image"
    LEAD_FORM = "lead_form"
    LOCATION = "location"
    APP = "app"


class ValidationSeverity(Enum):
    """Validation severity levels for asset rules"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IndustryType(Enum):
    """Industry types for asset rule modifiers"""
    ECOMMERCE = "E-commerce"
    SAAS = "SaaS"
    HEALTHCARE = "Healthcare"
    OTHER = "Other"


@dataclass
class GoogleAdsLimits:
    """Official Google Ads character limits - Technical Writing Standards"""
    # Headlines - Technical writing: jam-pack value, avoid filler words
    headline: int = 30  # Max 30 chars
    headline_min: int = 22  # Technical writing minimum (avoid filler words)
    headline_optimal_min: int = 22  # Optimal for value density
    headline_optimal_max: int = 29  # Optimal for value density

    # Long headlines (PMAX only)
    long_headline: int = 90  # Max 90 chars
    long_headline_min: int = 22  # Technical writing minimum

    # Descriptions - Technical writing: jam-pack value, avoid filler words
    description: int = 90  # Max 90 chars
    description_min: int = 75  # Technical writing minimum (avoid filler words)
    description_optimal_min: int = 75  # Optimal for value density
    description_optimal_max: int = 85  # Optimal for value density

    # Sitelinks
    sitelink_text: int = 25  # Max 25 chars for sitelink text
    sitelink_text_min: int = 15  # Recommended minimum
    sitelink_desc: int = 35  # Max 35 chars for sitelink description
    sitelink_desc_min: int = 20  # Recommended minimum

    # Callouts
    callout: int = 25  # Max 25 chars
    callout_min: int = 15  # Recommended minimum

    # Structured Snippets
    structured_snippet_header: int = 25  # Max 25 chars for header
    structured_snippet_header_min: int = 15  # Recommended minimum
    structured_snippet_value: int = 25  # Max 25 chars per value
    structured_snippet_value_min: int = 10  # Recommended minimum

    # Other
    price_header: int = 25
    price_desc: int = 25
    promotion_text: int = 20
    business_name: int = 25

    # Paths
    path1: int = 15  # Max 15 chars
    path2: int = 15  # Max 15 chars

    # Final URL
    final_url: int = 2048  # Max 2048 bytes


# Backward compatibility
CharLimits = GoogleAdsLimits


@dataclass
class CTREvaluationWeights:
    """CTR evaluation weights for scoring assets - Technical Writing Focus"""
    benefit: float = 0.30
    keyword_match: float = 0.25
    number: float = 0.20
    emotion: float = 0.15
    technical_writing: float = 0.10  # Formerly readability - now measures value density


@dataclass
class VariantGenerationConfig:
    """Configuration for asset variant generation"""
    default_n: int = 3
    strategy: str = "unique-angle"


@dataclass
class CTRBestPractice:
    """CTR best practice guideline"""
    guideline: str
    category: str = "general"


@dataclass
class IndustryModifier:
    """Industry-specific asset modifier"""
    industry: IndustryType
    modifiers: List[str] = field(default_factory=list)


@dataclass
class AssetInputs:
    """Input data for asset generation"""
    business_name: str = ""
    final_url: str = ""
    industry_vertical: str = ""
    core_offer: str = ""
    unique_selling_points: str = ""
    promo_details: str = ""
    locations: str = ""
    phone_number: str = ""
    compliance_notes: str = ""
    feed_source: str = ""
    rsa_headlines: List[str] = field(default_factory=list)
    rsa_descriptions: List[str] = field(default_factory=list)
    ad_language: str = "en"


@dataclass
class ValidationResult:
    """Result of asset validation"""
    is_valid: bool
    severity: ValidationSeverity
    message: str
    rule_name: str
    asset_type: Optional[AssetType] = None
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssetVariant:
    """Individual asset variant with scoring"""
    id: str
    asset_type: AssetType
    content: Dict[str, Any]
    ctr_score: float = 0.0
    is_valid: bool = True
    validation_results: List[ValidationResult] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    performance_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssetGenerationConfig:
    """Complete asset generation configuration"""
    version: str = "2025-07-08"
    updated: str = "2025-07-08"
    char_limits: CharLimits = field(default_factory=CharLimits)
    ctr_weights: CTREvaluationWeights = field(default_factory=CTREvaluationWeights)
    variant_generation: VariantGenerationConfig = field(default_factory=VariantGenerationConfig)
    debug_enabled: bool = False
    ctr_best_practices: List[CTRBestPractice] = field(default_factory=list)
    industry_modifiers: List[IndustryModifier] = field(default_factory=list)
    workflow_steps: List[Dict[str, Any]] = field(default_factory=list)
    output_schema: Dict[str, Any] = field(default_factory=dict)


class GoogleAdsAssetRulesParser:
    """
    Parser for Google Ads asset generation rules from XML system prompts

    This class parses the XML format and provides structured access to all
    configuration elements, rules, and workflow steps.
    """

    def __init__(self):
        self.config = AssetGenerationConfig()

    def parse_xml_string(self, xml_content: str) -> AssetGenerationConfig:
        """
        Parse XML string into structured configuration

        Args:
            xml_content: XML content as string

        Returns:
            AssetGenerationConfig: Parsed configuration
        """
        try:
            root = ET.fromstring(xml_content)

            # Parse version and updated date
            self.config.version = root.get('version', '2025-07-08')
            config_elem = root.find('config')
            if config_elem is not None:
                self.config.updated = config_elem.get('updated', '2025-07-08')

            # Parse character limits
            self._parse_char_limits(root)

            # Parse CTR weights
            self._parse_ctr_weights(root)

            # Parse variant generation config
            self._parse_variant_generation(root)

            # Parse debug setting
            self._parse_debug_config(root)

            # Parse CTR best practices
            self._parse_ctr_best_practices(root)

            # Parse industry modifiers
            self._parse_industry_modifiers(root)

            # Parse workflow steps
            self._parse_workflow_steps(root)

            # Parse output schema
            self._parse_output_schema(root)

            return self.config

        except ET.ParseError as e:
            logger.error(f"Failed to parse XML: {e}")
            raise ValueError(f"Invalid XML format: {e}")
        except Exception as e:
            logger.error(f"Error parsing asset rules: {e}")
            raise

    def parse_xml_file(self, file_path: str) -> AssetGenerationConfig:
        """
        Parse XML file into structured configuration

        Args:
            file_path: Path to XML file

        Returns:
            AssetGenerationConfig: Parsed configuration
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"XML file not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        return self.parse_xml_string(xml_content)

    def _parse_char_limits(self, root: ET.Element) -> None:
        """Parse character limits configuration"""
        char_limits_elem = root.find('.//char_limits')
        if char_limits_elem is not None:
            self.config.char_limits = CharLimits(
                headline=int(char_limits_elem.get('headline', '30')),
                headline_min=int(char_limits_elem.get('headline_min', '15')),
                description=int(char_limits_elem.get('description', '90')),
                description_min=int(char_limits_elem.get('description_min', '60')),
                sitelink=int(char_limits_elem.get('sitelink', '25')),
                sitelink_min=int(char_limits_elem.get('sitelink_min', '15')),
                sitelink_desc=int(char_limits_elem.get('sitelink_desc', '35')),
                sitelink_desc_min=int(char_limits_elem.get('sitelink_desc_min', '20')),
                callout=int(char_limits_elem.get('callout', '25')),
                callout_min=int(char_limits_elem.get('callout_min', '15')),
                structured_snippet_header=int(char_limits_elem.get('structured_snippet_header', '25')),
                structured_snippet_header_min=int(char_limits_elem.get('structured_snippet_header_min', '15')),
                structured_snippet_value=int(char_limits_elem.get('structured_snippet_value', '25')),
                structured_snippet_value_min=int(char_limits_elem.get('structured_snippet_value_min', '10')),
                price_header=int(char_limits_elem.get('price_header', '25')),
                price_desc=int(char_limits_elem.get('price_desc', '25')),
                promotion_text=int(char_limits_elem.get('promotion_text', '20')),
                business_name=int(char_limits_elem.get('business_name', '25'))
            )

    def _parse_ctr_weights(self, root: ET.Element) -> None:
        """Parse CTR evaluation weights"""
        ctr_weights_elem = root.find('.//ctr_weights')
        if ctr_weights_elem is not None:
            self.config.ctr_weights = CTREvaluationWeights(
                benefit=float(ctr_weights_elem.get('benefit', '0.30')),
                keyword_match=float(ctr_weights_elem.get('keyword_match', '0.25')),
                number=float(ctr_weights_elem.get('number', '0.20')),
                emotion=float(ctr_weights_elem.get('emotion', '0.15')),
                readability=float(ctr_weights_elem.get('readability', '0.10'))
            )

    def _parse_variant_generation(self, root: ET.Element) -> None:
        """Parse variant generation configuration"""
        variant_elem = root.find('.//variant_generation')
        if variant_elem is not None:
            self.config.variant_generation = VariantGenerationConfig(
                default_n=int(variant_elem.get('default_n', '3')),
                strategy=variant_elem.get('strategy', 'unique-angle')
            )

    def _parse_debug_config(self, root: ET.Element) -> None:
        """Parse debug configuration"""
        debug_elem = root.find('.//debug')
        if debug_elem is not None:
            self.config.debug_enabled = debug_elem.get('on', 'false').lower() == 'true'

    def _parse_ctr_best_practices(self, root: ET.Element) -> None:
        """Parse CTR best practices"""
        practices_elem = root.find('.//ctr_best_practices')
        if practices_elem is not None:
            for guideline_elem in practices_elem.findall('guideline'):
                practice = CTRBestPractice(
                    guideline=guideline_elem.text.strip() if guideline_elem.text else "",
                    category="general"
                )
                self.config.ctr_best_practices.append(practice)

    def _parse_industry_modifiers(self, root: ET.Element) -> None:
        """Parse industry-specific modifiers"""
        for if_block in root.findall('.//if_block'):
            condition = if_block.get('condition', '')
            industry = self._extract_industry_from_condition(condition)

            if industry:
                modifiers = []
                for modifier_elem in if_block.findall('modifier'):
                    if modifier_elem.text:
                        modifiers.append(modifier_elem.text.strip())

                industry_modifier = IndustryModifier(
                    industry=industry,
                    modifiers=modifiers
                )
                self.config.industry_modifiers.append(industry_modifier)

    def _parse_workflow_steps(self, root: ET.Element) -> None:
        """Parse workflow steps"""
        plan_elem = root.find('plan')
        if plan_elem is not None:
            for step_elem in plan_elem.findall('step'):
                step_data = {
                    'action_name': step_elem.find('action_name').text if step_elem.find('action_name') is not None else "",
                    'description': step_elem.find('description').text if step_elem.find('description') is not None else "",
                    'is_debug': False
                }

                # Check if this is a debug step
                if step_elem.find('emit_debug_log') is not None:
                    step_data['is_debug'] = True

                self.config.workflow_steps.append(step_data)

    def _parse_output_schema(self, root: ET.Element) -> None:
        """Parse output schema specification"""
        output_spec = root.find('output_specifications')
        if output_spec is not None:
            schema_elem = output_spec.find('schema')
            if schema_elem is not None:
                # Parse assets structure
                assets_elem = schema_elem.find('assets')
                if assets_elem is not None:
                    self.config.output_schema = self._parse_assets_schema(assets_elem)

    def _parse_assets_schema(self, assets_elem: ET.Element) -> Dict[str, Any]:
        """Parse assets schema structure"""
        schema = {}

        for asset_elem in assets_elem:
            asset_type = asset_elem.tag
            asset_config = {}

            # Parse attributes
            for attr_name, attr_value in asset_elem.items():
                asset_config[attr_name] = attr_value

            # Parse nested elements
            for child_elem in asset_elem:
                if child_elem.tag in ['text', 'desc1', 'desc2', 'header', 'values', 'price', 'desc', 'occasion', 'phone_number', 'src_prompt', 'alt_text', 'headline', 'cta', 'feedLink', 'store', 'link_text']:
                    asset_config[child_elem.tag] = child_elem.text or ""

            schema[asset_type] = asset_config

        return schema

    def _extract_industry_from_condition(self, condition: str) -> Optional[IndustryType]:
        """Extract industry type from condition string"""
        if 'E-commerce' in condition:
            return IndustryType.ECOMMERCE
        elif 'SaaS' in condition:
            return IndustryType.SAAS
        elif 'Healthcare' in condition:
            return IndustryType.HEALTHCARE
        return None

    def get_industry_modifiers(self, industry: IndustryType) -> List[str]:
        """Get modifiers for specific industry"""
        for modifier in self.config.industry_modifiers:
            if modifier.industry == industry:
                return modifier.modifiers
        return []

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'version': self.config.version,
            'updated': self.config.updated,
            'char_limits': {
                'headline': self.config.char_limits.headline,
                'headline_min': self.config.char_limits.headline_min,
                'description': self.config.char_limits.description,
                'description_min': self.config.char_limits.description_min,
                'sitelink': self.config.char_limits.sitelink,
                'sitelink_min': self.config.char_limits.sitelink_min,
                'sitelink_desc': self.config.char_limits.sitelink_desc,
                'sitelink_desc_min': self.config.char_limits.sitelink_desc_min,
                'callout': self.config.char_limits.callout,
                'callout_min': self.config.char_limits.callout_min,
                'structured_snippet_header': self.config.char_limits.structured_snippet_header,
                'structured_snippet_header_min': self.config.char_limits.structured_snippet_header_min,
                'structured_snippet_value': self.config.char_limits.structured_snippet_value,
                'structured_snippet_value_min': self.config.char_limits.structured_snippet_value_min,
                'price_header': self.config.char_limits.price_header,
                'price_desc': self.config.char_limits.price_desc,
                'promotion_text': self.config.char_limits.promotion_text,
                'business_name': self.config.char_limits.business_name
            },
            'ctr_weights': {
                'benefit': self.config.ctr_weights.benefit,
                'keyword_match': self.config.ctr_weights.keyword_match,
                'number': self.config.ctr_weights.number,
                'emotion': self.config.ctr_weights.emotion,
                'readability': self.config.ctr_weights.readability
            },
            'variant_generation': {
                'default_n': self.config.variant_generation.default_n,
                'strategy': self.config.variant_generation.strategy
            },
            'debug_enabled': self.config.debug_enabled,
            'ctr_best_practices': [
                {'guideline': p.guideline, 'category': p.category}
                for p in self.config.ctr_best_practices
            ],
            'industry_modifiers': [
                {'industry': m.industry.value, 'modifiers': m.modifiers}
                for m in self.config.industry_modifiers
            ],
            'workflow_steps': self.config.workflow_steps,
            'output_schema': self.config.output_schema
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GoogleAdsAssetRulesParser':
        """Create parser from dictionary"""
        parser = cls()
        parser.config = AssetGenerationConfig(
            version=data.get('version', '2025-07-08'),
            updated=data.get('updated', '2025-07-08'),
            char_limits=CharLimits(**data.get('char_limits', {})),
            ctr_weights=CTREvaluationWeights(**data.get('ctr_weights', {})),
            variant_generation=VariantGenerationConfig(**data.get('variant_generation', {})),
            debug_enabled=data.get('debug_enabled', False),
            ctr_best_practices=[
                CTRBestPractice(**p) for p in data.get('ctr_best_practices', [])
            ],
            industry_modifiers=[
                IndustryModifier(
                    industry=IndustryType(m['industry']),
                    modifiers=m['modifiers']
                ) for m in data.get('industry_modifiers', [])
            ],
            workflow_steps=data.get('workflow_steps', []),
            output_schema=data.get('output_schema', {})
        )
        return parser


# Convenience functions
def parse_asset_rules_xml(xml_content: str) -> AssetGenerationConfig:
    """Parse XML asset rules into configuration"""
    parser = GoogleAdsAssetRulesParser()
    return parser.parse_xml_string(xml_content)


def parse_asset_rules_file(file_path: str) -> AssetGenerationConfig:
    """Parse XML asset rules file into configuration"""
    parser = GoogleAdsAssetRulesParser()
    return parser.parse_xml_file(file_path)


# Export for easy importing
__all__ = [
    'GoogleAdsAssetRulesParser',
    'AssetGenerationConfig',
    'AssetInputs',
    'AssetVariant',
    'ValidationResult',
    'AssetType',
    'IndustryType',
    'ValidationSeverity',
    'CharLimits',
    'CTREvaluationWeights',
    'parse_asset_rules_xml',
    'parse_asset_rules_file'
]
