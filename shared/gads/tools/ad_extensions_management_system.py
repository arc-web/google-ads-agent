#!/usr/bin/env python3
"""
Ad Extensions Management System for Google Ads Search Campaigns

This comprehensive system provides tools for managing all types of ad extensions
in search campaigns, including creation, configuration, optimization, and performance
analysis based on Google Ads API documentation and best practices.

Usage:
    from gads.tools.ad_extensions_management_system import AdExtensionsManagementSystem

    ext_system = AdExtensionsManagementSystem()
    extensions = ext_system.generate_campaign_extensions("executive resume services")
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExtensionType(Enum):
    """Types of ad extensions supported"""
    SITELINK = "sitelink"
    CALLOUT = "callout"
    CALL = "call"
    LOCATION = "location"
    STRUCTURED_SNIPPET = "structured_snippet"
    PRICE = "price"
    PROMOTION = "promotion"
    APP = "app"
    REVIEW = "review"
    MESSAGE = "message"
    LEAD_FORM = "lead_form"

@dataclass
class ExtensionAsset:
    """Represents an ad extension asset - Context7: Account-level setup"""
    extension_type: ExtensionType
    name: str
    status: str = "ENABLED"  # ENABLED, PAUSED, REMOVED
    account_level: bool = True  # Context7: Extensions should be account-level
    campaign_associations: List[str] = field(default_factory=list)  # Which campaigns use this extension
    labels: List[str] = field(default_factory=list)
    performance_data: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[str] = None

@dataclass
class SitelinkExtension:
    """Sitelink extension configuration"""
    extension_type: ExtensionType = ExtensionType.SITELINK
    name: str = ""
    text: str = ""
    final_urls: List[str] = field(default_factory=list)
    status: str = "ENABLED"
    labels: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    performance_data: Dict[str, Any] = field(default_factory=dict)
    description1: Optional[str] = None
    description2: Optional[str] = None
    final_mobile_urls: Optional[List[str]] = None
    tracking_url_template: Optional[str] = None
    url_custom_parameters: List[Dict[str, str]] = field(default_factory=list)
    final_url_suffix: Optional[str] = None

@dataclass
class CalloutExtension:
    """Callout extension configuration"""
    extension_type: ExtensionType = ExtensionType.CALLOUT
    name: str = ""
    text: str = ""
    status: str = "ENABLED"
    labels: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    performance_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CallExtension:
    """Call extension configuration"""
    extension_type: ExtensionType = ExtensionType.CALL
    name: str = ""
    country_code: str = ""
    phone_number: str = ""
    status: str = "ENABLED"
    labels: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    performance_data: Dict[str, Any] = field(default_factory=dict)
    call_tracking_enabled: bool = False
    call_conversion_action: Optional[str] = None
    call_conversion_reporting_state: str = "DISABLED"

@dataclass
class LocationExtension:
    """Location extension configuration"""
    extension_type: ExtensionType = ExtensionType.LOCATION
    name: str = ""
    status: str = "ENABLED"
    labels: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    performance_data: Dict[str, Any] = field(default_factory=dict)
    business_name: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    country_code: Optional[str] = None
    phone_number: Optional[str] = None
    company_name: Optional[str] = None

@dataclass
class StructuredSnippetExtension:
    """Structured snippet extension configuration"""
    extension_type: ExtensionType = ExtensionType.STRUCTURED_SNIPPET
    name: str = ""
    header: str = ""
    values: List[str] = field(default_factory=list)
    status: str = "ENABLED"
    labels: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    performance_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PriceExtension:
    """Price extension configuration"""
    extension_type: ExtensionType = ExtensionType.PRICE
    name: str = ""
    type: str = ""  # SERVICES, CATEGORIES, BRANDS
    status: str = "ENABLED"
    labels: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    performance_data: Dict[str, Any] = field(default_factory=dict)
    price_qualifier: Optional[str] = None
    tracking_url_template: Optional[str] = None
    final_url_suffix: Optional[str] = None
    items: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class PromotionExtension:
    """Promotion extension configuration"""
    extension_type: ExtensionType = ExtensionType.PROMOTION
    name: str = ""
    promotion_method: str = ""  # PERCENT_OFF, MONEY_AMOUNT_OFF, BUY_ONE_GET_ONE_FREE
    status: str = "ENABLED"
    labels: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    performance_data: Dict[str, Any] = field(default_factory=dict)
    percent_off: Optional[int] = None
    money_amount_off: Optional[Dict[str, Any]] = None
    original_price: Optional[Dict[str, Any]] = None
    promotion_code: Optional[str] = None
    orders_over_amount: Optional[Dict[str, Any]] = None
    promotion_start_date: Optional[str] = None
    promotion_end_date: Optional[str] = None
    occasion: Optional[str] = None
    final_urls: List[str] = field(default_factory=list)
    final_mobile_urls: Optional[List[str]] = None
    tracking_url_template: Optional[str] = None

@dataclass
class AppExtension:
    """App extension configuration"""
    extension_type: ExtensionType = ExtensionType.APP
    name: str = ""
    app_id: str = ""
    app_store: str = ""  # GOOGLE_PLAY, APPLE_APP_STORE
    status: str = "ENABLED"
    labels: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    performance_data: Dict[str, Any] = field(default_factory=dict)
    app_link_text: str = "Install"
    final_urls: List[str] = field(default_factory=list)
    final_mobile_urls: Optional[List[str]] = None

@dataclass
class ReviewExtension:
    """Review extension configuration"""
    extension_type: ExtensionType = ExtensionType.REVIEW
    name: str = ""
    source_name: str = ""
    source_url: str = ""
    status: str = "ENABLED"
    labels: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    performance_data: Dict[str, Any] = field(default_factory=dict)
    source_image_url: Optional[str] = None
    review_text: Optional[str] = None
    review_rating: Optional[float] = None

@dataclass
class MessageExtension:
    """Message extension configuration"""
    extension_type: ExtensionType = ExtensionType.MESSAGE
    name: str = ""
    business_name: str = ""
    country_code: str = ""
    phone_number: str = ""
    status: str = "ENABLED"
    labels: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    performance_data: Dict[str, Any] = field(default_factory=dict)
    message_text: Optional[str] = None
    message_tracking_enabled: bool = False

@dataclass
class LeadFormExtension:
    """Lead form extension configuration"""
    extension_type: ExtensionType = ExtensionType.LEAD_FORM
    name: str = ""
    business_name: str = ""
    headline: str = ""
    description: str = ""
    privacy_policy_url: str = ""
    status: str = "ENABLED"
    labels: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    performance_data: Dict[str, Any] = field(default_factory=dict)
    post_submit_headline: Optional[str] = None
    post_submit_description: Optional[str] = None
    call_to_action_text: Optional[str] = None
    fields: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class ExtensionPerformance:
    """Performance metrics for ad extensions"""
    impressions: int = 0
    clicks: int = 0
    cost_micros: int = 0
    conversions: float = 0.0
    conversion_value_micros: int = 0
    ctr: float = 0.0
    cpc: float = 0.0
    cpa: float = 0.0
    roas: float = 0.0
    interaction_rate: float = 0.0
    average_cpc: float = 0.0

@dataclass
class ExtensionOptimization:
    """Optimization recommendations for extensions"""
    priority_actions: List[str] = field(default_factory=list)
    performance_insights: List[str] = field(default_factory=list)
    status_changes: List[Tuple[str, str]] = field(default_factory=list)
    new_extensions_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    content_improvements: List[str] = field(default_factory=list)

class AdExtensionsManagementSystem:
    """
    Comprehensive ad extensions management system for Google Ads search campaigns.

    This system provides tools for creating, configuring, optimizing, and managing
    all types of ad extensions based on Google Ads API documentation and best practices.
    """

    def __init__(self):
        """Initialize the ad extensions management system"""
        self.extension_templates = self._load_extension_templates()
        self.performance_thresholds = self._load_performance_thresholds()
        self.business_type_templates = self._load_business_type_templates()

    def _load_extension_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load extension templates for different scenarios"""
        return {
            "professional_services": {
                "sitelink": [
                    {"text": "Our Services", "url": "/services"},
                    {"text": "About Us", "url": "/about"},
                    {"text": "Contact", "url": "/contact"},
                    {"text": "Free Consultation", "url": "/consultation"}
                ],
                "callout": [
                    "Certified Professionals",
                    "15+ Years Experience",
                    "Licensed & Insured",
                    "Free Initial Consultation"
                ],
                "structured_snippet": {
                    "header": "Services",
                    "values": ["Consultation", "Strategy", "Implementation", "Support"]
                }
            },
            "ecommerce": {
                "sitelink": [
                    {"text": "Shop Now", "url": "/shop"},
                    {"text": "Free Shipping", "url": "/shipping"},
                    {"text": "Returns", "url": "/returns"},
                    {"text": "Track Order", "url": "/track"}
                ],
                "callout": [
                    "Free Shipping",
                    "30-Day Returns",
                    "Secure Checkout",
                    "24/7 Support"
                ],
                "promotion": {
                    "method": "PERCENT_OFF",
                    "percent_off": 10,
                    "description": "10% off your first order"
                }
            },
            "local_business": {
                "location": True,
                "call": True,
                "sitelink": [
                    {"text": "Directions", "url": "/directions"},
                    {"text": "Hours", "url": "/hours"},
                    {"text": "Reviews", "url": "/reviews"},
                    {"text": "Book Appointment", "url": "/book"}
                ],
                "callout": [
                    "Open 7 Days",
                    "Emergency Service",
                    "Licensed Technicians",
                    "Satisfaction Guaranteed"
                ]
            }
        }

    def _load_performance_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Load performance thresholds for extension optimization"""
        return {
            "sitelink": {
                "min_ctr": 0.5,
                "min_clicks": 10,
                "max_cpc_increase": 0.3
            },
            "callout": {
                "min_ctr_impact": 0.1,
                "min_impressions": 1000
            },
            "call": {
                "min_calls_per_week": 5,
                "max_cost_per_call": 5.0
            },
            "location": {
                "min_directions": 2,
                "min_calls": 3
            }
        }

    def _load_business_type_templates(self) -> Dict[str, List[str]]:
        """Load business type specific extension recommendations"""
        return {
            "professional_services": [
                "sitelink", "callout", "call", "structured_snippet", "review"
            ],
            "ecommerce": [
                "sitelink", "callout", "promotion", "price", "review"
            ],
            "local_business": [
                "location", "call", "sitelink", "callout", "message"
            ],
            "healthcare": [
                "call", "location", "sitelink", "review", "lead_form"
            ],
            "education": [
                "sitelink", "callout", "structured_snippet", "location", "app"
            ],
            "real_estate": [
                "location", "call", "sitelink", "lead_form", "price"
            ]
        }

    def generate_campaign_extensions(self, business_type: str,
                                   business_info: Dict[str, Any],
                                   extension_types: Optional[List[str]] = None) -> Dict[str, List[ExtensionAsset]]:
        """
        Generate a comprehensive set of ad extensions for a campaign.

        Args:
            business_type: Type of business (professional_services, ecommerce, etc.)
            business_info: Business information (name, phone, address, website, etc.)
            extension_types: Specific extension types to generate (optional)

        Returns:
            Dictionary of extension types with their configurations
        """
        logger.info(f"Generating extensions for {business_type}")

        extensions = {}

        # Determine which extensions to generate
        if not extension_types:
            extension_types = self.business_type_templates.get(business_type, ["sitelink", "callout"])

        # Generate each type of extension
        for ext_type in extension_types:
            if ext_type == "sitelink":
                extensions["sitelink"] = self._generate_sitelink_extensions(business_info)
            elif ext_type == "callout":
                extensions["callout"] = self._generate_callout_extensions(business_type, business_info)
            elif ext_type == "call":
                extensions["call"] = self._generate_call_extensions(business_info)
            elif ext_type == "location":
                extensions["location"] = self._generate_location_extensions(business_info)
            elif ext_type == "structured_snippet":
                extensions["structured_snippet"] = self._generate_structured_snippet_extensions(business_type)
            elif ext_type == "promotion":
                extensions["promotion"] = self._generate_promotion_extensions(business_info)
            elif ext_type == "app":
                extensions["app"] = self._generate_app_extensions(business_info)
            elif ext_type == "review":
                extensions["review"] = self._generate_review_extensions(business_info)
            elif ext_type == "message":
                extensions["message"] = self._generate_message_extensions(business_info)
            elif ext_type == "lead_form":
                extensions["lead_form"] = self._generate_lead_form_extensions(business_info)

        return extensions

    def _generate_sitelink_extensions(self, business_info: Dict[str, Any]) -> List[SitelinkExtension]:
        """Generate sitelink extensions"""
        sitelinks = []
        base_url = business_info.get("website", "https://example.com")

        # Get template based on business type
        business_type = business_info.get("type", "general")
        template = self.extension_templates.get(business_type, self.extension_templates["professional_services"])

        template_sitelinks = template.get("sitelink", [])

        for i, link_info in enumerate(template_sitelinks):
            sitelink = SitelinkExtension(
                extension_type=ExtensionType.SITELINK,
                name=f"Sitelink {i+1}",
                text=link_info["text"],
                final_urls=[f"{base_url}{link_info['url']}"],
                created_at=datetime.now().isoformat()
            )
            sitelinks.append(sitelink)

        # Add dynamic sitelinks based on business info
        if business_info.get("services"):
            for service in business_info["services"][:2]:  # Limit to 2
                sitelink = SitelinkExtension(
                    extension_type=ExtensionType.SITELINK,
                    name=f"Service: {service[:20]}",
                    text=service[:25],
                    final_urls=[f"{base_url}/services/{service.lower().replace(' ', '-')}"]
                )
                sitelinks.append(sitelink)

        return sitelinks[:6]  # Google allows up to 6 sitelinks per campaign

    def _generate_callout_extensions(self, business_type: str, business_info: Dict[str, Any]) -> List[CalloutExtension]:
        """Generate callout extensions"""
        callouts = []

        # Get template callouts
        template = self.extension_templates.get(business_type, self.extension_templates["professional_services"])
        template_callouts = template.get("callout", [])

        for i, text in enumerate(template_callouts):
            callout = CalloutExtension(
                extension_type=ExtensionType.CALLOUT,
                name=f"Callout {i+1}",
                text=text,
                created_at=datetime.now().isoformat()
            )
            callouts.append(callout)

        # Add business-specific callouts
        business_name = business_info.get("name", "")
        if "years" in business_info:
            years = business_info["years"]
            callout = CalloutExtension(
                extension_type=ExtensionType.CALLOUT,
                name="Experience Callout",
                text=f"{years}+ Years Experience",
                created_at=datetime.now().isoformat()
            )
            callouts.append(callout)

        if business_info.get("certifications"):
            for cert in business_info["certifications"][:2]:
                callout = CalloutExtension(
                    extension_type=ExtensionType.CALLOUT,
                    name=f"Cert: {cert[:15]}",
                    text=f"Certified {cert[:20]}",
                    created_at=datetime.now().isoformat()
                )
                callouts.append(callout)

        return callouts[:10]  # Google allows up to 10 callouts

    def _generate_call_extensions(self, business_info: Dict[str, Any]) -> List[CallExtension]:
        """Generate call extensions"""
        calls = []

        if business_info.get("phone"):
            call = CallExtension(
                extension_type=ExtensionType.CALL,
                name="Primary Phone",
                country_code=business_info.get("country_code", "US"),
                phone_number=business_info["phone"],
                call_tracking_enabled=True,
                created_at=datetime.now().isoformat()
            )
            calls.append(call)

        return calls

    def _generate_location_extensions(self, business_info: Dict[str, Any]) -> List[LocationExtension]:
        """Generate location extensions"""
        locations = []

        if business_info.get("address"):
            location = LocationExtension(
                extension_type=ExtensionType.LOCATION,
                name="Primary Location",
                business_name=business_info.get("name"),
                address_line_1=business_info["address"].get("line1"),
                address_line_2=business_info["address"].get("line2"),
                city=business_info["address"].get("city"),
                province=business_info["address"].get("state"),
                postal_code=business_info["address"].get("zip"),
                country_code=business_info.get("country_code", "US"),
                phone_number=business_info.get("phone"),
                created_at=datetime.now().isoformat()
            )
            locations.append(location)

        return locations

    def _generate_structured_snippet_extensions(self, business_type: str) -> List[StructuredSnippetExtension]:
        """Generate structured snippet extensions"""
        snippets = []

        # Get template
        template = self.extension_templates.get(business_type, self.extension_templates["professional_services"])
        template_snippet = template.get("structured_snippet")

        if template_snippet:
            snippet = StructuredSnippetExtension(
                extension_type=ExtensionType.STRUCTURED_SNIPPET,
                name="Services Snippet",
                header=template_snippet["header"],
                values=template_snippet["values"],
                created_at=datetime.now().isoformat()
            )
            snippets.append(snippet)

        return snippets

    def _generate_promotion_extensions(self, business_info: Dict[str, Any]) -> List[PromotionExtension]:
        """Generate promotion extensions"""
        promotions = []

        # Get template
        business_type = business_info.get("type", "general")
        template = self.extension_templates.get(business_type, {})
        template_promo = template.get("promotion")

        if template_promo:
            promotion = PromotionExtension(
                extension_type=ExtensionType.PROMOTION,
                name="Current Promotion",
                promotion_method=template_promo["method"],
                percent_off=template_promo.get("percent_off"),
                final_urls=[business_info.get("website", "https://example.com")],
                created_at=datetime.now().isoformat()
            )
            promotions.append(promotion)

        return promotions

    def _generate_app_extensions(self, business_info: Dict[str, Any]) -> List[AppExtension]:
        """Generate app extensions"""
        apps = []

        if business_info.get("app_id"):
            app = AppExtension(
                extension_type=ExtensionType.APP,
                name="Mobile App",
                app_id=business_info["app_id"],
                app_store=business_info.get("app_store", "GOOGLE_PLAY"),
                final_urls=[business_info.get("app_url", f"https://play.google.com/store/apps/details?id={business_info['app_id']}")],
                created_at=datetime.now().isoformat()
            )
            apps.append(app)

        return apps

    def _generate_review_extensions(self, business_info: Dict[str, Any]) -> List[ReviewExtension]:
        """Generate review extensions"""
        reviews = []

        if business_info.get("reviews"):
            for i, review in enumerate(business_info["reviews"][:2]):  # Max 2 reviews
                review_ext = ReviewExtension(
                    extension_type=ExtensionType.REVIEW,
                    name=f"Review {i+1}",
                    source_name=review.get("source", "Google Reviews"),
                    source_url=review.get("url", ""),
                    review_text=review.get("text", "")[:50],
                    review_rating=review.get("rating", 5.0),
                    created_at=datetime.now().isoformat()
                )
                reviews.append(review_ext)

        return reviews

    def _generate_message_extensions(self, business_info: Dict[str, Any]) -> List[MessageExtension]:
        """Generate message extensions"""
        messages = []

        if business_info.get("phone"):
            message = MessageExtension(
                extension_type=ExtensionType.MESSAGE,
                name="Text Message",
                business_name=business_info.get("name", ""),
                country_code=business_info.get("country_code", "US"),
                phone_number=business_info["phone"],
                message_text="Contact us for more information",
                message_tracking_enabled=True,
                created_at=datetime.now().isoformat()
            )
            messages.append(message)

        return messages

    def _generate_lead_form_extensions(self, business_info: Dict[str, Any]) -> List[LeadFormExtension]:
        """Generate lead form extensions"""
        lead_forms = []

        if business_info.get("lead_form_enabled"):
            lead_form = LeadFormExtension(
                extension_type=ExtensionType.LEAD_FORM,
                name="Contact Form",
                business_name=business_info.get("name", ""),
                headline="Get Your Free Consultation",
                description="Fill out the form below and we'll contact you within 24 hours",
                privacy_policy_url=f"{business_info.get('website', 'https://example.com')}/privacy",
                created_at=datetime.now().isoformat()
            )
            lead_forms.append(lead_form)

        return lead_forms

    def optimize_extensions_performance(self, extensions: Dict[str, List[ExtensionAsset]],
                                      performance_data: Dict[str, Dict[str, Any]]) -> ExtensionOptimization:
        """
        Analyze extension performance and provide optimization recommendations.

        Args:
            extensions: Extensions organized by type
            performance_data: Performance data for each extension

        Returns:
            Optimization recommendations
        """
        logger.info("Optimizing extension performance")

        optimization = ExtensionOptimization()

        # Analyze each extension type
        for ext_type, ext_list in extensions.items():
            for extension in ext_list:
                perf = performance_data.get(extension.name, {})

                if ext_type == "sitelink":
                    self._optimize_sitelink(extension, perf, optimization)
                elif ext_type == "callout":
                    self._optimize_callout(extension, perf, optimization)
                elif ext_type == "call":
                    self._optimize_call(extension, perf, optimization)
                elif ext_type == "location":
                    self._optimize_location(extension, perf, optimization)

        # Add general recommendations
        total_extensions = sum(len(ext_list) for ext_list in extensions.values())
        if total_extensions < 4:
            optimization.new_extensions_suggestions.append({
                "type": "missing_extensions",
                "suggestion": "Consider adding more extension types for better ad coverage"
            })

        return optimization

    def _optimize_sitelink(self, extension: SitelinkExtension, perf: Dict[str, Any],
                          optimization: ExtensionOptimization):
        """Optimize sitelink performance"""
        clicks = perf.get('clicks', 0)
        impressions = perf.get('impressions', 0)

        if impressions > 1000 and clicks < 10:
            optimization.priority_actions.append(
                f"Low-performing sitelink '{extension.text}' - consider pausing or improving text"
            )
            optimization.status_changes.append((extension.name, "PAUSED"))

        if clicks > 50:
            optimization.performance_insights.append(
                f"High-performing sitelink '{extension.text}' - consider creating similar extensions"
            )

    def _optimize_callout(self, extension: CalloutExtension, perf: Dict[str, Any],
                         optimization: ExtensionOptimization):
        """Optimize callout performance"""
        ctr_impact = perf.get('ctr_impact', 0)

        if ctr_impact < 0.05:
            optimization.content_improvements.append(
                f"Low-impact callout '{extension.text}' - consider more compelling text"
            )

    def _optimize_call(self, extension: CallExtension, perf: Dict[str, Any],
                      optimization: ExtensionOptimization):
        """Optimize call performance"""
        calls = perf.get('calls', 0)
        cost = perf.get('cost_micros', 0) / 1000000

        if calls > 0 and cost / calls > 10:
            optimization.priority_actions.append(
                f"High cost per call for '{extension.name}' - review call quality settings"
            )

    def _optimize_location(self, extension: LocationExtension, perf: Dict[str, Any],
                          optimization: ExtensionOptimization):
        """Optimize location performance"""
        directions = perf.get('directions_requested', 0)
        calls = perf.get('calls', 0)

        if directions < 1 and calls < 1:
            optimization.performance_insights.append(
                f"Location extension '{extension.name}' has low engagement - verify address accuracy"
            )

    def validate_extensions(self, extensions: Dict[str, List[ExtensionAsset]]) -> Dict[str, Any]:
        """
        Validate extension configurations for compliance and best practices.

        Args:
            extensions: Extensions to validate

        Returns:
            Validation results
        """
        validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "extension_count": sum(len(ext_list) for ext_list in extensions.values())
        }

        # Validate each extension type
        for ext_type, ext_list in extensions.items():
            if ext_type == "sitelink":
                self._validate_sitelinks(ext_list, validation)
            elif ext_type == "callout":
                self._validate_callouts(ext_list, validation)
            elif ext_type == "call":
                self._validate_calls(ext_list, validation)
            elif ext_type == "location":
                self._validate_locations(ext_list, validation)

        # Check for minimum extension coverage
        if validation["extension_count"] < 3:
            validation["warnings"].append("Consider adding more extensions for better ad coverage")

        return validation

    def _validate_sitelinks(self, sitelinks: List[SitelinkExtension], validation: Dict[str, Any]):
        """Validate sitelink extensions"""
        if len(sitelinks) > 6:
            validation["errors"].append("Too many sitelinks - Google allows maximum 6 per campaign")
            validation["is_valid"] = False

        for sitelink in sitelinks:
            if len(sitelink.text) > 25:
                validation["warnings"].append(f"Sitelink text '{sitelink.text[:20]}...' exceeds 25 characters")

            if not sitelink.final_urls:
                validation["errors"].append(f"Sitelink '{sitelink.text}' missing final URLs")
                validation["is_valid"] = False

    def _validate_callouts(self, callouts: List[CalloutExtension], validation: Dict[str, Any]):
        """Validate callout extensions"""
        if len(callouts) > 10:
            validation["errors"].append("Too many callouts - Google allows maximum 10 per campaign")
            validation["is_valid"] = False

        for callout in callouts:
            if len(callout.text) > 25:
                validation["warnings"].append(f"Callout text '{callout.text[:20]}...' exceeds 25 characters")

    def _validate_calls(self, calls: List[CallExtension], validation: Dict[str, Any]):
        """Validate call extensions"""
        for call in calls:
            if not call.phone_number:
                validation["errors"].append(f"Call extension '{call.name}' missing phone number")
                validation["is_valid"] = False

    def _validate_locations(self, locations: List[LocationExtension], validation: Dict[str, Any]):
        """Validate location extensions"""
        for location in locations:
            if not location.address_line_1 or not location.city:
                validation["warnings"].append(f"Location extension '{location.name}' missing complete address")

    def generate_extension_json_for_api(self, extensions: Dict[str, List[ExtensionAsset]]) -> List[Dict[str, Any]]:
        """
        Generate JSON for Google Ads API extension creation.

        Args:
            extensions: Extensions to convert to API format

        Returns:
            List of API operation objects
        """
        operations = []

        for ext_type, ext_list in extensions.items():
            for extension in ext_list:
                operation = {
                    "create": {
                        "extension_type": ext_type.upper(),
                        "status": extension.status
                    }
                }

                # Add type-specific fields
                if extension.extension_type == ExtensionType.SITELINK:
                    operation["create"]["sitelink_asset"] = {
                        "link_text": extension.text,
                        "final_urls": extension.final_urls,
                        "final_mobile_urls": extension.final_mobile_urls,
                        "tracking_url_template": extension.tracking_url_template,
                        "final_url_suffix": extension.final_url_suffix
                    }

                elif extension.extension_type == ExtensionType.CALLOUT:
                    operation["create"]["callout_asset"] = {
                        "callout_text": extension.text
                    }

                elif extension.extension_type == ExtensionType.CALL:
                    operation["create"]["call_asset"] = {
                        "country_code": extension.country_code,
                        "phone_number": extension.phone_number
                    }

                elif extension.extension_type == ExtensionType.STRUCTURED_SNIPPET:
                    operation["create"]["structured_snippet_asset"] = {
                        "header": extension.header,
                        "values": extension.values
                    }

                operations.append(operation)

        return operations

    def export_extensions_to_csv(self, extensions: Dict[str, List[ExtensionAsset]],
                               campaign_name: str) -> str:
        """
        Export extensions to CSV format compatible with Google Ads Editor.

        Args:
            extensions: Extensions to export
            campaign_name: Campaign name

        Returns:
            CSV content as string
        """
        csv_lines = [
            "Campaign,Extension Type,Status,Details"
        ]

        for ext_type, ext_list in extensions.items():
            for extension in ext_list:
                details = self._get_extension_details_for_csv(extension)
                row = [
                    campaign_name,
                    ext_type.title(),
                    extension.status.title(),
                    details
                ]
                csv_lines.append(",".join(f'"{str(cell)}"' for cell in row))

        return "\n".join(csv_lines)

    def _get_extension_details_for_csv(self, extension: Any) -> str:
        """Get extension details for CSV export"""
        if extension.extension_type == ExtensionType.SITELINK:
            return f"Text: {extension.text}, URL: {extension.final_urls[0] if extension.final_urls else ''}"
        elif extension.extension_type == ExtensionType.CALLOUT:
            return f"Text: {extension.text}"
        elif extension.extension_type == ExtensionType.CALL:
            return f"Phone: {extension.phone_number}"
        elif extension.extension_type == ExtensionType.LOCATION:
            address = f"{extension.city}, {extension.province}" if extension.city else "Address needed"
            return f"Business: {extension.business_name}, Address: {address}"
        else:
            return f"Name: {extension.name}"

    def create_extension_performance_dashboard(self, extensions: Dict[str, List[ExtensionAsset]],
                                            performance_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a performance dashboard for extensions.

        Args:
            extensions: Extensions by type
            performance_data: Performance data by extension

        Returns:
            Performance dashboard with insights
        """
        dashboard = {
            "summary": {
                "total_extensions": sum(len(ext_list) for ext_list in extensions.values()),
                "extension_types": len(extensions),
                "active_extensions": 0
            },
            "performance_by_type": {},
            "top_performers": [],
            "underperformers": [],
            "insights": [],
            "recommendations": []
        }

        # Calculate summary
        for ext_type, ext_list in extensions.items():
            active = sum(1 for ext in ext_list if ext.status == "ENABLED")
            dashboard["summary"]["active_extensions"] += active

            # Type performance
            type_perf = {
                "count": len(ext_list),
                "active": active,
                "total_clicks": 0,
                "total_impressions": 0,
                "total_cost": 0
            }

            for ext in ext_list:
                perf = performance_data.get(ext.name, {})
                type_perf["total_clicks"] += perf.get('clicks', 0)
                type_perf["total_impressions"] += perf.get('impressions', 0)
                type_perf["total_cost"] += perf.get('cost_micros', 0) / 1000000

            dashboard["performance_by_type"][ext_type] = type_perf

        # Identify top performers (by clicks)
        all_perf = []
        for ext_type, ext_list in extensions.items():
            for ext in ext_list:
                perf = performance_data.get(ext.name, {})
                clicks = perf.get('clicks', 0)
                all_perf.append({
                    'name': ext.name,
                    'type': ext_type,
                    'clicks': clicks,
                    'impressions': perf.get('impressions', 0),
                    'cost': perf.get('cost_micros', 0) / 1000000
                })

        # Top performers
        top_performers = sorted(all_perf, key=lambda x: x['clicks'], reverse=True)[:5]
        dashboard["top_performers"] = top_performers

        # Underperformers (low clicks relative to impressions)
        underperformers = [
            perf for perf in all_perf
            if perf['impressions'] > 1000 and perf['clicks'] < 10
        ][:5]
        dashboard["underperformers"] = underperformers

        # Generate insights
        total_clicks = sum(tp["total_clicks"] for tp in dashboard["performance_by_type"].values())
        if total_clicks < 100:
            dashboard["insights"].append("Low overall extension engagement - review extension relevance")

        # Type-specific insights
        sitelink_perf = dashboard["performance_by_type"].get("sitelink", {})
        if sitelink_perf.get("count", 0) > 0 and sitelink_perf.get("total_clicks", 0) < 50:
            dashboard["insights"].append("Sitelink extensions have low engagement - consider improving link text")

        return dashboard

    def get_extension_best_practices(self, extension_type: str = None) -> Dict[str, List[str]]:
        """
        Get best practices for extension management.

        Args:
            extension_type: Specific extension type (optional)

        Returns:
            Best practices organized by category
        """
        general_practices = {
            "creation": [
                "Create extensions that directly relate to your ad and landing page",
                "Use clear, compelling text that encourages action",
                "Include relevant details like pricing, guarantees, or unique features",
                "Test different variations to see what performs best"
            ],
            "optimization": [
                "Monitor extension performance regularly in your account",
                "Pause or remove extensions with consistently poor performance",
                "Update extension content to reflect current promotions or services",
                "Use extension reports to understand which extensions drive the most value"
            ],
            "placement": [
                "Extensions appear when they're predicted to improve performance",
                "Different extensions may show on different devices and networks",
                "Multiple extensions can appear together for comprehensive information",
                "Extension eligibility depends on ad approval and account status"
            ]
        }

        if extension_type:
            type_practices = {
                "sitelink": [
                    "Use descriptive text that clearly indicates destination",
                    "Ensure landing pages are relevant and load quickly",
                    "Create sitelinks for your most important pages or actions",
                    "Use consistent sitelink text across campaigns when possible"
                ],
                "callout": [
                    "Highlight unique selling points or key benefits",
                    "Keep text concise and focused on one key message",
                    "Use action-oriented language when appropriate",
                    "Update callouts regularly to reflect current offerings"
                ],
                "call": [
                    "Verify phone numbers are accurate and professional",
                    "Enable call tracking to measure effectiveness",
                    "Consider different call extensions for different locations",
                    "Set appropriate call conversion tracking settings"
                ],
                "location": [
                    "Ensure business information is accurate and up-to-date",
                    "Verify addresses are correct in Google My Business",
                    "Include relevant business details like hours or services",
                    "Use location extensions for local search campaigns"
                ]
            }

            if extension_type.lower() in type_practices:
                general_practices[f"{extension_type.lower()}_specific"] = type_practices[extension_type.lower()]

        return general_practices