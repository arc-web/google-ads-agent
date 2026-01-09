"""
Price Asset Builder for Google Ads

This module implements specialized price asset generation following the Price Asset Build Guide.
It creates pricing ladders with proper localization, compliance validation, and CSV export
functionality for Google Ads price assets.

Key Features:
- Pricing tier management (Free Consult, Intro Visit, Standard)
- Geo-localization for headers
- Compliance and style validation
- CSV export in Google Ads format
- Integration with CTR evaluation engine
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging
import re
import csv
import io
from pathlib import Path

from asset_rules_parser import (
    AssetType,
    AssetVariant,
    ValidationResult,
    ValidationSeverity,
    IndustryType
)
from ctr_evaluation_engine import CTREvaluationEngine, CTRMetrics

logger = logging.getLogger(__name__)


@dataclass
class AccountInfo:
    """Account information for price asset generation"""
    clinic_name: str = ""
    location: str = ""
    address: str = ""
    phone: str = ""
    final_url: str = ""


@dataclass
class PricingTier:
    """Individual pricing tier in the ladder"""
    order: int
    header: str
    description: str
    price: float
    unit: str
    purpose: str
    localized_headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class PriceAssetStyle:
    """Style rules for price assets"""
    case: str = "Title"  # Title, UPPER, lower
    avoid_symbols: Set[str] = field(default_factory=lambda: {'!', '&', '$', '%'})
    avoid_caps: str = "ALL"
    avoid_punctuation: str = "DoublePunctuation"
    avoid_whitespace: str = "DoubleSpaces"
    allowed_bullets: Set[str] = field(default_factory=lambda: {'•'})
    allowed_plus: Set[str] = field(default_factory=lambda: {'+'})


@dataclass
class LocalizationRule:
    """Geo-localization rules for price assets"""
    geo_prefixes: List[str] = field(default_factory=lambda: ['Aurora', 'Nearby'])
    header_templates: List[str] = field(default_factory=list)
    max_header_length: int = 25


@dataclass
class ComplianceRules:
    """Compliance rules specific to price assets"""
    no_claims: Set[str] = field(default_factory=set)
    allowed_phrasing: Set[str] = field(default_factory=set)
    disclaimer_rules: List[str] = field(default_factory=list)


@dataclass
class PriceAssetConfig:
    """Complete price asset configuration"""
    account: AccountInfo = field(default_factory=AccountInfo)
    language: str = "en"
    currency: str = "USD"
    asset_type: str = "Services"
    price_qualifier: str = "From"
    status: str = "Enabled"
    source: str = "Advertiser"
    min_price: float = 1.00
    required_items: int = 3
    header_max_length: int = 25
    description_max_length: int = 25
    pricing_tiers: List[PricingTier] = field(default_factory=list)
    style_rules: PriceAssetStyle = field(default_factory=PriceAssetStyle)
    localization: LocalizationRule = field(default_factory=LocalizationRule)
    compliance: ComplianceRules = field(default_factory=ComplianceRules)
    copy_guidance: List[str] = field(default_factory=list)


@dataclass
class PriceAsset:
    """Generated price asset with all required fields"""
    campaign: str
    ad_group: str
    language: str
    asset_type: str
    price_qualifier: str
    currency: str
    headers: List[str]
    descriptions: List[str]
    prices: List[str]
    units: List[str]
    final_urls: List[str]
    validation_results: List[ValidationResult] = field(default_factory=list)
    ctr_metrics: Optional[CTRMetrics] = None


class PriceAssetBuilder:
    """
    Specialized builder for Google Ads price assets

    Follows the Price Asset Build Guide specifications for creating
    compliant, optimized price assets with proper pricing ladders.
    """

    def __init__(self, config: Optional[PriceAssetConfig] = None):
        self.config = config or PriceAssetConfig()
        self.ctr_engine = CTREvaluationEngine()

        # Initialize default pricing tiers if none provided
        if not self.config.pricing_tiers:
            self._initialize_default_pricing_tiers()

    def parse_price_guide_xml(self, xml_content: str) -> PriceAssetConfig:
        """
        Parse Price Asset Build Guide XML into configuration

        Args:
            xml_content: XML content as string

        Returns:
            PriceAssetConfig: Parsed configuration
        """
        try:
            root = ET.fromstring(xml_content)

            # Parse account information
            account_elem = root.find('Account')
            if account_elem is not None:
                self.config.account = AccountInfo(
                    clinic_name=account_elem.find('ClinicName').text if account_elem.find('ClinicName') is not None else "",
                    location=account_elem.find('Location').text if account_elem.find('Location') is not None else "",
                    address=account_elem.find('Address').text if account_elem.find('Address') is not None else "",
                    phone=account_elem.find('Phone').text if account_elem.find('Phone') is not None else "",
                    final_url=account_elem.find('FinalURL').text if account_elem.find('FinalURL') is not None else ""
                )

            # Parse basic settings
            self.config.language = root.find('Language').get('value', 'en') if root.find('Language') is not None else 'en'
            self.config.currency = root.find('Currency').get('value', 'USD') if root.find('Currency') is not None else 'USD'
            self.config.asset_type = root.find('Type').get('value', 'Services') if root.find('Type') is not None else 'Services'
            self.config.price_qualifier = root.find('PriceQualifier').get('value', 'From') if root.find('PriceQualifier') is not None else 'From'
            self.config.status = root.find('Status').get('value', 'Enabled') if root.find('Status') is not None else 'Enabled'
            self.config.source = root.find('Source').get('value', 'Advertiser') if root.find('Source') is not None else 'Advertiser'

            # Parse rules
            min_price_elem = root.find('.//MinPriceAllowed')
            if min_price_elem is not None:
                self.config.min_price = float(min_price_elem.get('value', '1.00'))

            required_elem = root.find('.//RequiredItems')
            if required_elem is not None:
                self.config.required_items = int(required_elem.get('count', '3'))

            # Parse length limits
            length_elem = root.find('.//LengthLimits')
            if length_elem is not None:
                header_elem = length_elem.find('Header')
                desc_elem = length_elem.find('Description')
                if header_elem is not None:
                    self.config.header_max_length = int(header_elem.get('max', '25'))
                if desc_elem is not None:
                    self.config.description_max_length = int(desc_elem.get('max', '25'))

            # Parse style rules
            self._parse_style_rules(root)

            # Parse strategy (pricing tiers)
            self._parse_pricing_strategy(root)

            # Parse localization rules
            self._parse_localization_rules(root)

            # Parse compliance rules
            self._parse_compliance_rules(root)

            # Parse copy guidance
            self._parse_copy_guidance(root)

            return self.config

        except ET.ParseError as e:
            logger.error(f"Failed to parse price guide XML: {e}")
            raise ValueError(f"Invalid XML format: {e}")

    def generate_price_assets(self, campaigns: List[str], ad_groups: List[str],
                            target_keywords: List[str] = None) -> List[PriceAsset]:
        """
        Generate price assets for specified campaigns and ad groups

        Args:
            campaigns: List of campaign names
            ad_groups: List of ad group names
            target_keywords: Keywords for CTR evaluation

        Returns:
            List of generated price assets
        """
        assets = []

        for campaign in campaigns:
            for ad_group in ad_groups:
                asset = self._generate_single_price_asset(campaign, ad_group, target_keywords)
                assets.append(asset)

        return assets

    def _generate_single_price_asset(self, campaign: str, ad_group: str,
                                   target_keywords: List[str] = None) -> PriceAsset:
        """Generate a single price asset with all required data"""
        asset = PriceAsset(
            campaign=campaign,
            ad_group=ad_group,
            language=self.config.language,
            asset_type=self.config.asset_type,
            price_qualifier=self.config.price_qualifier,
            currency=self.config.currency,
            headers=[],
            descriptions=[],
            prices=[],
            units=[],
            final_urls=[]
        )

        # Generate tier data
        for tier in self.config.pricing_tiers:
            # Apply localization if ad group contains geo terms
            header = self._localize_header(tier.header, ad_group)

            # Validate and truncate if needed
            header = self._apply_style_rules(header)
            header = self._truncate_to_limit(header, self.config.header_max_length)

            description = self._apply_style_rules(tier.description)
            description = self._truncate_to_limit(description, self.config.description_max_length)

            asset.headers.append(header)
            asset.descriptions.append(description)
            asset.prices.append(f"{tier.price:.2f}")
            asset.units.append(tier.unit)
            asset.final_urls.append(self.config.account.final_url)

        # Validate the asset
        asset.validation_results = self.validate_price_asset(asset)

        # Evaluate CTR potential
        asset_variant = self._convert_to_asset_variant(asset)
        asset.ctr_metrics = self.ctr_engine.evaluate_asset(asset_variant, target_keywords)

        return asset

    def _localize_header(self, base_header: str, ad_group: str) -> str:
        """Apply localization rules to headers based on ad group"""
        ad_group_lower = ad_group.lower()

        # Check for geo-specific ad groups
        for geo_prefix in self.config.localization.geo_prefixes:
            if geo_prefix.lower() in ad_group_lower:
                localized = f"{geo_prefix} {base_header}"
                # Check if it fits within limits
                if len(localized) <= self.config.header_max_length:
                    return localized

        return base_header

    def _apply_style_rules(self, text: str) -> str:
        """Apply style rules to text content"""
        # Apply case rules
        if self.config.style_rules.case == "Title":
            text = self._to_title_case(text)
        elif self.config.style_rules.case == "UPPER":
            text = text.upper()
        elif self.config.style_rules.case == "lower":
            text = text.lower()

        # Remove prohibited symbols
        for symbol in self.config.style_rules.avoid_symbols:
            text = text.replace(symbol, '')

        # Fix double punctuation
        if self.config.style_rules.avoid_punctuation == "DoublePunctuation":
            text = re.sub(r'([.!?])\1+', r'\1', text)

        # Fix double spaces
        if self.config.style_rules.avoid_whitespace == "DoubleSpaces":
            text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _to_title_case(self, text: str) -> str:
        """Convert text to title case, preserving common words"""
        # Common words to not capitalize
        common_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}

        words = text.split()
        if not words:
            return text

        # Capitalize first word
        result = [words[0].capitalize()]

        # Handle remaining words
        for word in words[1:]:
            if word.lower() not in common_words:
                result.append(word.capitalize())
            else:
                result.append(word.lower())

        return ' '.join(result)

    def _truncate_to_limit(self, text: str, max_length: int) -> str:
        """Truncate text to fit within character limit"""
        if len(text) <= max_length:
            return text

        # Try to truncate at word boundary
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')

        if last_space > max_length * 0.8:  # If space is reasonably close to limit
            truncated = truncated[:last_space]

        return truncated.rstrip()

    def validate_price_asset(self, asset: PriceAsset) -> List[ValidationResult]:
        """Validate a price asset against all rules"""
        results = []

        # Check required items count
        if len(asset.headers) != self.config.required_items:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"Asset must have exactly {self.config.required_items} pricing tiers",
                rule_name="required_items_count"
            ))

        # Validate each header and description
        for i, (header, description) in enumerate(zip(asset.headers, asset.descriptions)):
            # Header length check
            if len(header) > self.config.header_max_length:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Header {i+1} exceeds {self.config.header_max_length} characters",
                    rule_name="header_length_limit"
                ))

            # Description length check
            if len(description) > self.config.description_max_length:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Description {i+1} exceeds {self.config.description_max_length} characters",
                    rule_name="description_length_limit"
                ))

            # Compliance checks
            compliance_results = self._check_compliance(header + " " + description)
            results.extend(compliance_results)

            # Style rule checks
            style_results = self._check_style_compliance(header, f"header_{i+1}")
            results.extend(style_results)

            style_results = self._check_style_compliance(description, f"description_{i+1}")
            results.extend(style_results)

        # Price validation
        for i, price_str in enumerate(asset.prices):
            try:
                price = float(price_str)
                if price < self.config.min_price:
                    results.append(ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Price {i+1} (${price}) below minimum ${self.config.min_price}",
                        rule_name="minimum_price_limit"
                    ))
            except ValueError:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Price {i+1} is not a valid number: {price_str}",
                    rule_name="price_format"
                ))

        return results

    def _check_compliance(self, text: str) -> List[ValidationResult]:
        """Check text against compliance rules"""
        results = []
        text_lower = text.lower()

        # Check for prohibited claims
        for claim in self.config.compliance.no_claims:
            if claim.lower() in text_lower:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Text contains prohibited claim: '{claim}'",
                    rule_name="prohibited_claim"
                ))

        return results

    def _check_style_compliance(self, text: str, field_name: str) -> List[ValidationResult]:
        """Check text against style rules"""
        results = []

        # Check for prohibited symbols
        for symbol in self.config.style_rules.avoid_symbols:
            if symbol in text:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    message=f"Text contains prohibited symbol '{symbol}' in {field_name}",
                    rule_name="prohibited_symbol"
                ))

        # Check for double punctuation
        if re.search(r'([.!?])\1+', text):
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                message=f"Text contains double punctuation in {field_name}",
                rule_name="double_punctuation"
            ))

        # Check for double spaces
        if re.search(r'\s{2,}', text):
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                message=f"Text contains double spaces in {field_name}",
                rule_name="double_spaces"
            ))

        return results

    def export_to_csv(self, assets: List[PriceAsset], output_path: Optional[str] = None) -> str:
        """
        Export price assets to CSV format compatible with Google Ads

        Args:
            assets: List of price assets to export
            output_path: Optional file path to save CSV

        Returns:
            CSV content as string
        """
        output = io.StringIO()

        # CSV headers matching Google Ads format
        fieldnames = [
            'Campaign', 'Ad Group', 'Language', 'Type', 'Price qualifier', 'Currency'
        ]

        # Add dynamic headers, descriptions, prices, units, and URLs
        for i in range(self.config.required_items):
            fieldnames.extend([
                f'Header {i+1}', f'Description {i+1}', f'Price {i+1}', f'Unit {i+1}', f'Final URL {i+1}'
            ])

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        # Write each asset
        for asset in assets:
            row = {
                'Campaign': asset.campaign,
                'Ad Group': asset.ad_group,
                'Language': asset.language,
                'Type': asset.asset_type,
                'Price qualifier': asset.price_qualifier,
                'Currency': asset.currency
            }

            # Add tier data
            for i in range(len(asset.headers)):
                row[f'Header {i+1}'] = asset.headers[i]
                row[f'Description {i+1}'] = asset.descriptions[i]
                row[f'Price {i+1}'] = asset.prices[i]
                row[f'Unit {i+1}'] = asset.units[i]
                row[f'Final URL {i+1}'] = asset.final_urls[i]

            writer.writerow(row)

        csv_content = output.getvalue()
        output.close()

        # Save to file if path provided
        if output_path:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                f.write(csv_content)

        return csv_content

    def _convert_to_asset_variant(self, asset: PriceAsset) -> AssetVariant:
        """Convert price asset to AssetVariant for CTR evaluation"""
        content = {
            'headers': asset.headers,
            'descriptions': asset.descriptions,
            'prices': asset.prices,
            'type': asset.asset_type,
            'qualifier': asset.price_qualifier
        }

        return AssetVariant(
            id=f"{asset.campaign}_{asset.ad_group}_price",
            asset_type=AssetType.PRICE_ITEM,
            content=content,
            is_valid=len(asset.validation_results) == 0
        )

    def _initialize_default_pricing_tiers(self):
        """Initialize default pricing tiers if none provided"""
        self.config.pricing_tiers = [
            PricingTier(
                order=1,
                header="Free Phone Consult",
                description="Phone Call • No Charge",
                price=1.00,
                unit="Session",
                purpose="Lowest friction lead in for new patients."
            ),
            PricingTier(
                order=2,
                header="Intro Visit",
                description="Consult + Therapy",
                price=69.00,
                unit="Session",
                purpose="Main front end offer. Must match landing page headline and hero section."
            ),
            PricingTier(
                order=3,
                header="Standard Visit",
                description="Full Retail Price",
                price=150.00,
                unit="Session",
                purpose="Anchors value and shows savings vs standard care."
            )
        ]

    def _parse_style_rules(self, root: ET.Element):
        """Parse style rules from XML"""
        style_elem = root.find('.//Style')
        if style_elem is not None:
            case_elem = style_elem.find('Case')
            avoid_elem = style_elem.find('Avoid')
            allowed_elem = style_elem.find('Allowed')

            if case_elem is not None:
                self.config.style_rules.case = case_elem.text or "Title"

            if avoid_elem is not None:
                avoid_symbols = set()
                for symbol_elem in avoid_elem.findall('Symbol'):
                    if symbol_elem.text:
                        avoid_symbols.add(symbol_elem.text.strip())
                self.config.style_rules.avoid_symbols = avoid_symbols

                caps_elem = avoid_elem.find('Caps')
                if caps_elem is not None:
                    self.config.style_rules.avoid_caps = caps_elem.text or "ALL"

            if allowed_elem is not None:
                bullets = set()
                for bullet_elem in allowed_elem.findall('Bullet'):
                    if bullet_elem.text:
                        bullets.add(bullet_elem.text.strip())
                self.config.style_rules.allowed_bullets = bullets

    def _parse_pricing_strategy(self, root: ET.Element):
        """Parse pricing strategy and tiers from XML"""
        strategy_elem = root.find('Strategy')
        if strategy_elem is not None:
            ladder_elem = strategy_elem.find('Ladder')
            if ladder_elem is not None:
                tiers = []
                for tier_elem in ladder_elem.findall('Tier'):
                    tier = PricingTier(
                        order=int(tier_elem.get('order', '1')),
                        header=tier_elem.find('Header').text if tier_elem.find('Header') is not None else "",
                        description=tier_elem.find('Description').text if tier_elem.find('Description') is not None else "",
                        price=float(tier_elem.find('Price').text or '0.00'),
                        unit=tier_elem.find('Unit').text if tier_elem.find('Unit') is not None else "",
                        purpose=tier_elem.find('Purpose').text if tier_elem.find('Purpose') is not None else ""
                    )
                    tiers.append(tier)
                self.config.pricing_tiers = sorted(tiers, key=lambda x: x.order)

    def _parse_localization_rules(self, root: ET.Element):
        """Parse localization rules from XML"""
        localization_elem = root.find('.//Localization')
        if localization_elem is not None:
            rule_elem = localization_elem.find('Rule')
            if rule_elem is not None:
                # Extract geo prefixes from the rule text
                rule_text = rule_elem.text or ""
                prefixes = []
                for prefix in self.config.localization.geo_prefixes:
                    if prefix in rule_text:
                        prefixes.append(prefix)
                self.config.localization.geo_prefixes = prefixes

    def _parse_compliance_rules(self, root: ET.Element):
        """Parse compliance rules from XML"""
        compliance_elem = root.find('Compliance')
        if compliance_elem is not None:
            no_claims_elem = compliance_elem.find('NoClaims')
            if no_claims_elem is not None:
                no_claims = set()
                for claim_elem in no_claims_elem.findall('Claim'):
                    if claim_elem.text:
                        no_claims.add(claim_elem.text.strip())
                self.config.compliance.no_claims = no_claims

            allowed_elem = compliance_elem.find('AllowedPhrasing')
            if allowed_elem is not None:
                allowed_phrasing = set()
                for phrase_elem in allowed_elem.findall('Phrase'):
                    if phrase_elem.text:
                        allowed_phrasing.add(phrase_elem.text.strip())
                self.config.compliance.allowed_phrasing = allowed_phrasing

    def _parse_copy_guidance(self, root: ET.Element):
        """Parse copy guidance from XML"""
        guidance_elem = root.find('.//CopyGuidance')
        if guidance_elem is not None:
            guidance = []
            for item in guidance_elem:
                if item.text:
                    guidance.append(item.text.strip())
            self.config.copy_guidance = guidance


# Convenience functions
def create_price_asset_builder_from_xml(xml_content: str) -> PriceAssetBuilder:
    """Create price asset builder from XML guide"""
    builder = PriceAssetBuilder()
    builder.parse_price_guide_xml(xml_content)
    return builder


def generate_price_assets_csv(assets: List[PriceAsset], output_path: Optional[str] = None) -> str:
    """Generate CSV from price assets"""
    if not assets:
        return ""

    # Create a temporary builder to get the export method
    builder = PriceAssetBuilder()
    return builder.export_to_csv(assets, output_path)


# Export for easy importing
__all__ = [
    'PriceAssetBuilder',
    'PriceAssetConfig',
    'PriceAsset',
    'PricingTier',
    'AccountInfo',
    'create_price_asset_builder_from_xml',
    'generate_price_assets_csv'
]
