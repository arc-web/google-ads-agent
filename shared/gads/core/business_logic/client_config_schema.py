"""
Client-Specific Configuration Schema and Validation

This module defines comprehensive client-specific configuration schemas that extend
the base ClientRecord with business rules, reporting templates, optimization settings,
and compliance requirements.

Designed for multi-tenant Google Ads management with strict client isolation.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
import json
import jsonschema
from pathlib import Path


class ClientStatus(Enum):
    """Client account status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ONBOARDING = "onboarding"
    OFFBOARDING = "offboarding"


class IndustryType(Enum):
    """Industry classifications for specialized handling"""
    ECOMMERCE = "ecommerce"
    B2B_SERVICES = "b2b_services"
    LOCAL_BUSINESS = "local_business"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    REAL_ESTATE = "real_estate"
    HOSPITALITY = "hospitality"
    EDUCATION = "education"
    NONPROFIT = "nonprofit"
    OTHER = "other"


class OptimizationStrategy(Enum):
    """Available optimization strategies"""
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    PERFORMANCE_MAX = "performance_max"


@dataclass
class ClientKPIs:
    """Client-specific Key Performance Indicators"""
    primary_metric: str = "conversions"  # conversions, revenue, leads, etc.
    secondary_metrics: List[str] = field(default_factory=lambda: ["cpc", "ctr", "roas"])
    target_values: Dict[str, float] = field(default_factory=dict)
    minimum_thresholds: Dict[str, float] = field(default_factory=dict)
    maximum_thresholds: Dict[str, float] = field(default_factory=dict)
    custom_kpis: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def validate_kpi_value(self, kpi_name: str, value: float) -> bool:
        """Validate if a KPI value meets client thresholds"""
        if kpi_name in self.minimum_thresholds:
            if value < self.minimum_thresholds[kpi_name]:
                return False
        if kpi_name in self.maximum_thresholds:
            if value > self.maximum_thresholds[kpi_name]:
                return False
        return True


@dataclass
class ReportingPreferences:
    """Client-specific reporting preferences"""
    frequency: str = "weekly"  # daily, weekly, biweekly, monthly
    format: str = "detailed"  # summary, detailed, executive
    delivery_method: List[str] = field(default_factory=lambda: ["email"])
    include_charts: bool = True
    include_raw_data: bool = False
    custom_sections: List[str] = field(default_factory=list)
    recipient_emails: List[str] = field(default_factory=list)
    scheduled_time: Optional[time] = None
    timezone: str = "America/New_York"


@dataclass
class BusinessRules:
    """Client-specific business rules and constraints"""
    budget_limits: Dict[str, float] = field(default_factory=dict)  # campaign_type -> max_budget
    bid_limits: Dict[str, float] = field(default_factory=dict)  # min_bid, max_bid
    targeting_restrictions: Dict[str, List[str]] = field(default_factory=dict)
    keyword_restrictions: List[str] = field(default_factory=list)
    competitor_domains: List[str] = field(default_factory=list)
    brand_terms: List[str] = field(default_factory=list)
    seasonal_adjustments: Dict[str, Dict[str, float]] = field(default_factory=dict)
    conversion_actions: List[str] = field(default_factory=list)
    custom_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationSettings:
    """Client-specific optimization settings"""
    strategy: OptimizationStrategy = OptimizationStrategy.BALANCED
    automation_enabled: bool = True
    auto_budget_adjustment: bool = False
    auto_bid_adjustment: bool = True
    budget_reallocation_enabled: bool = True
    keyword_expansion_enabled: bool = True
    audience_expansion_enabled: bool = False
    ad_testing_enabled: bool = True
    performance_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "min_ctr": 1.0,
        "min_conversion_rate": 0.5,
        "max_cpc": 10.0
    })
    custom_optimization_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComplianceSettings:
    """Client-specific compliance and regulatory settings"""
    industry_regulations: List[str] = field(default_factory=list)
    data_retention_days: int = 2555  # 7 years default
    audit_trail_required: bool = True
    pii_handling_required: bool = True
    consent_management_required: bool = False
    google_certifications: List[str] = field(default_factory=list)  # Google Ads certifications
    custom_compliance_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClientSpecificConfig:
    """
    Comprehensive client-specific configuration extending base ClientRecord

    This schema provides all client-specific settings for isolated, multi-tenant
    Google Ads management with strict adherence to business requirements.
    """

    # Base client information (extends ClientRecord)
    client_id: str
    client_name: str
    industry: IndustryType = IndustryType.OTHER
    status: ClientStatus = ClientStatus.ACTIVE

    # Contact and account information
    primary_email: str
    cc_emails: List[str] = field(default_factory=list)
    google_ads_account_id: str
    account_manager: str
    team_members: List[Dict[str, str]] = field(default_factory=list)  # [{"name": "", "email": "", "role": ""}]

    # Business configuration
    kpis: ClientKPIs = field(default_factory=ClientKPIs)
    reporting: ReportingPreferences = field(default_factory=ReportingPreferences)
    business_rules: BusinessRules = field(default_factory=BusinessRules)
    optimization: OptimizationSettings = field(default_factory=OptimizationSettings)
    compliance: ComplianceSettings = field(default_factory=ComplianceSettings)

    # Communication preferences (extended)
    communication_preferences: Dict[str, Any] = field(default_factory=lambda: {
        "response_style": "professional",
        "technical_detail_level": "balanced",
        "include_performance_alerts": True,
        "include_budget_alerts": True,
        "cc_account_manager": True,
        "preferred_contact_times": ["09:00-17:00"],
        "emergency_contact": None
    })

    # Operational settings
    service_level_agreement: Dict[str, Any] = field(default_factory=lambda: {
        "response_time_hours": 24,
        "reporting_deadlines": "EOD_Friday",
        "maintenance_windows": ["Saturday_22:00-02:00"],
        "emergency_support": True
    })

    # Integration settings
    integrations: Dict[str, Any] = field(default_factory=lambda: {
        "crm_system": None,
        "analytics_platform": "google_analytics",
        "webhook_endpoints": [],
        "api_rate_limits": {"requests_per_hour": 1000}
    })

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    def validate_configuration(self) -> List[str]:
        """
        Validate the client configuration for completeness and consistency

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Required field validation
        required_fields = [
            "client_id", "client_name", "primary_email",
            "google_ads_account_id", "account_manager"
        ]

        for field in required_fields:
            if not getattr(self, field, None):
                errors.append(f"Required field '{field}' is missing or empty")

        # Email format validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if self.primary_email and not re.match(email_pattern, self.primary_email):
            errors.append(f"Invalid primary email format: {self.primary_email}")

        for email in self.cc_emails:
            if not re.match(email_pattern, email):
                errors.append(f"Invalid CC email format: {email}")

        # Business rules validation
        if self.business_rules.budget_limits:
            for campaign_type, limit in self.business_rules.budget_limits.items():
                if limit <= 0:
                    errors.append(f"Invalid budget limit for {campaign_type}: {limit}")

        # KPI validation
        if self.kpis.primary_metric not in ["conversions", "revenue", "leads", "impressions", "clicks"]:
            errors.append(f"Invalid primary KPI: {self.kpis.primary_metric}")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization"""
        result = {
            "client_id": self.client_id,
            "client_name": self.client_name,
            "industry": self.industry.value,
            "status": self.status.value,
            "primary_email": self.primary_email,
            "cc_emails": self.cc_emails,
            "google_ads_account_id": self.google_ads_account_id,
            "account_manager": self.account_manager,
            "team_members": self.team_members,
            "kpis": {
                "primary_metric": self.kpis.primary_metric,
                "secondary_metrics": self.kpis.secondary_metrics,
                "target_values": self.kpis.target_values,
                "minimum_thresholds": self.kpis.minimum_thresholds,
                "maximum_thresholds": self.kpis.maximum_thresholds,
                "custom_kpis": self.kpis.custom_kpis
            },
            "reporting": {
                "frequency": self.reporting.frequency,
                "format": self.reporting.format,
                "delivery_method": self.reporting.delivery_method,
                "include_charts": self.reporting.include_charts,
                "include_raw_data": self.reporting.include_raw_data,
                "custom_sections": self.reporting.custom_sections,
                "recipient_emails": self.reporting.recipient_emails,
                "scheduled_time": self.reporting.scheduled_time.isoformat() if self.reporting.scheduled_time else None,
                "timezone": self.reporting.timezone
            },
            "business_rules": {
                "budget_limits": self.business_rules.budget_limits,
                "bid_limits": self.business_rules.bid_limits,
                "targeting_restrictions": self.business_rules.targeting_restrictions,
                "keyword_restrictions": self.business_rules.keyword_restrictions,
                "competitor_domains": self.business_rules.competitor_domains,
                "brand_terms": self.business_rules.brand_terms,
                "seasonal_adjustments": self.business_rules.seasonal_adjustments,
                "conversion_actions": self.business_rules.conversion_actions,
                "custom_rules": self.business_rules.custom_rules
            },
            "optimization": {
                "strategy": self.optimization.strategy.value,
                "automation_enabled": self.optimization.automation_enabled,
                "auto_budget_adjustment": self.optimization.auto_budget_adjustment,
                "auto_bid_adjustment": self.optimization.auto_bid_adjustment,
                "budget_reallocation_enabled": self.optimization.budget_reallocation_enabled,
                "keyword_expansion_enabled": self.optimization.keyword_expansion_enabled,
                "audience_expansion_enabled": self.optimization.audience_expansion_enabled,
                "ad_testing_enabled": self.optimization.ad_testing_enabled,
                "performance_thresholds": self.optimization.performance_thresholds,
                "custom_optimization_rules": self.optimization.custom_optimization_rules
            },
            "compliance": {
                "industry_regulations": self.compliance.industry_regulations,
                "data_retention_days": self.compliance.data_retention_days,
                "audit_trail_required": self.compliance.audit_trail_required,
                "pii_handling_required": self.compliance.pii_handling_required,
                "consent_management_required": self.compliance.consent_management_required,
                "google_certifications": self.compliance.google_certifications,
                "custom_compliance_rules": self.compliance.custom_compliance_rules
            },
            "communication_preferences": self.communication_preferences,
            "service_level_agreement": self.service_level_agreement,
            "integrations": self.integrations,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "custom_fields": self.custom_fields
        }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClientSpecificConfig':
        """Create configuration from dictionary"""
        # Convert string enums back to enum objects
        data_copy = data.copy()

        if 'industry' in data_copy:
            data_copy['industry'] = IndustryType(data_copy['industry'])
        if 'status' in data_copy:
            data_copy['status'] = ClientStatus(data_copy['status'])

        # Convert nested objects
        if 'kpis' in data_copy:
            kpis_data = data_copy['kpis']
            data_copy['kpis'] = ClientKPIs(
                primary_metric=kpis_data.get('primary_metric', 'conversions'),
                secondary_metrics=kpis_data.get('secondary_metrics', []),
                target_values=kpis_data.get('target_values', {}),
                minimum_thresholds=kpis_data.get('minimum_thresholds', {}),
                maximum_thresholds=kpis_data.get('maximum_thresholds', {}),
                custom_kpis=kpis_data.get('custom_kpis', {})
            )

        if 'reporting' in data_copy:
            reporting_data = data_copy['reporting']
            scheduled_time = None
            if reporting_data.get('scheduled_time'):
                from datetime import time
                time_str = reporting_data['scheduled_time']
                if isinstance(time_str, str):
                    scheduled_time = time.fromisoformat(time_str)
            data_copy['reporting'] = ReportingPreferences(
                frequency=reporting_data.get('frequency', 'weekly'),
                format=reporting_data.get('format', 'detailed'),
                delivery_method=reporting_data.get('delivery_method', ['email']),
                include_charts=reporting_data.get('include_charts', True),
                include_raw_data=reporting_data.get('include_raw_data', False),
                custom_sections=reporting_data.get('custom_sections', []),
                recipient_emails=reporting_data.get('recipient_emails', []),
                scheduled_time=scheduled_time,
                timezone=reporting_data.get('timezone', 'America/New_York')
            )

        if 'business_rules' in data_copy:
            rules_data = data_copy['business_rules']
            data_copy['business_rules'] = BusinessRules(
                budget_limits=rules_data.get('budget_limits', {}),
                bid_limits=rules_data.get('bid_limits', {}),
                targeting_restrictions=rules_data.get('targeting_restrictions', {}),
                keyword_restrictions=rules_data.get('keyword_restrictions', []),
                competitor_domains=rules_data.get('competitor_domains', []),
                brand_terms=rules_data.get('brand_terms', []),
                seasonal_adjustments=rules_data.get('seasonal_adjustments', {}),
                conversion_actions=rules_data.get('conversion_actions', []),
                custom_rules=rules_data.get('custom_rules', {})
            )

        if 'optimization' in data_copy:
            opt_data = data_copy['optimization']
            data_copy['optimization'] = OptimizationSettings(
                strategy=OptimizationStrategy(opt_data.get('strategy', 'balanced')),
                automation_enabled=opt_data.get('automation_enabled', True),
                auto_budget_adjustment=opt_data.get('auto_budget_adjustment', False),
                auto_bid_adjustment=opt_data.get('auto_bid_adjustment', True),
                budget_reallocation_enabled=opt_data.get('budget_reallocation_enabled', True),
                keyword_expansion_enabled=opt_data.get('keyword_expansion_enabled', True),
                audience_expansion_enabled=opt_data.get('audience_expansion_enabled', False),
                ad_testing_enabled=opt_data.get('ad_testing_enabled', True),
                performance_thresholds=opt_data.get('performance_thresholds', {}),
                custom_optimization_rules=opt_data.get('custom_optimization_rules', {})
            )

        if 'compliance' in data_copy:
            comp_data = data_copy['compliance']
            data_copy['compliance'] = ComplianceSettings(
                industry_regulations=comp_data.get('industry_regulations', []),
                data_retention_days=comp_data.get('data_retention_days', 2555),
                audit_trail_required=comp_data.get('audit_trail_required', True),
                pii_handling_required=comp_data.get('pii_handling_required', True),
                consent_management_required=comp_data.get('consent_management_required', False),
                google_certifications=comp_data.get('google_certifications', []),
                custom_compliance_rules=comp_data.get('custom_compliance_rules', {})
            )

        # Convert datetime strings
        if 'created_at' in data_copy and isinstance(data_copy['created_at'], str):
            data_copy['created_at'] = datetime.fromisoformat(data_copy['created_at'])
        if 'updated_at' in data_copy and isinstance(data_copy['updated_at'], str):
            data_copy['updated_at'] = datetime.fromisoformat(data_copy['updated_at'])

        return cls(**data_copy)


# JSON Schema for validation
CLIENT_CONFIG_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["client_id", "client_name", "primary_email", "google_ads_account_id", "account_manager"],
    "properties": {
        "client_id": {"type": "string", "minLength": 1},
        "client_name": {"type": "string", "minLength": 1},
        "industry": {"enum": [e.value for e in IndustryType]},
        "status": {"enum": [e.value for e in ClientStatus]},
        "primary_email": {"type": "string", "format": "email"},
        "cc_emails": {
            "type": "array",
            "items": {"type": "string", "format": "email"}
        },
        "google_ads_account_id": {"type": "string", "pattern": "^\\d{3}-\\d{3}-\\d{4}$"},
        "account_manager": {"type": "string", "minLength": 1},
        "kpis": {
            "type": "object",
            "properties": {
                "primary_metric": {"enum": ["conversions", "revenue", "leads", "impressions", "clicks"]},
                "secondary_metrics": {"type": "array", "items": {"type": "string"}},
                "target_values": {"type": "object"},
                "minimum_thresholds": {"type": "object"},
                "maximum_thresholds": {"type": "object"},
                "custom_kpis": {"type": "object"}
            }
        },
        "reporting": {
            "type": "object",
            "properties": {
                "frequency": {"enum": ["daily", "weekly", "biweekly", "monthly"]},
                "format": {"enum": ["summary", "detailed", "executive"]},
                "delivery_method": {"type": "array", "items": {"type": "string"}},
                "include_charts": {"type": "boolean"},
                "include_raw_data": {"type": "boolean"},
                "custom_sections": {"type": "array", "items": {"type": "string"}},
                "recipient_emails": {"type": "array", "items": {"type": "string", "format": "email"}},
                "scheduled_time": {"type": "string", "pattern": "^\\d{2}:\\d{2}:\\d{2}$"},
                "timezone": {"type": "string"}
            }
        },
        "business_rules": {
            "type": "object",
            "properties": {
                "budget_limits": {"type": "object"},
                "bid_limits": {"type": "object"},
                "targeting_restrictions": {"type": "object"},
                "keyword_restrictions": {"type": "array", "items": {"type": "string"}},
                "competitor_domains": {"type": "array", "items": {"type": "string"}},
                "brand_terms": {"type": "array", "items": {"type": "string"}},
                "seasonal_adjustments": {"type": "object"},
                "conversion_actions": {"type": "array", "items": {"type": "string"}},
                "custom_rules": {"type": "object"}
            }
        },
        "optimization": {
            "type": "object",
            "properties": {
                "strategy": {"enum": [e.value for e in OptimizationStrategy]},
                "automation_enabled": {"type": "boolean"},
                "auto_budget_adjustment": {"type": "boolean"},
                "auto_bid_adjustment": {"type": "boolean"},
                "budget_reallocation_enabled": {"type": "boolean"},
                "keyword_expansion_enabled": {"type": "boolean"},
                "audience_expansion_enabled": {"type": "boolean"},
                "ad_testing_enabled": {"type": "boolean"},
                "performance_thresholds": {"type": "object"},
                "custom_optimization_rules": {"type": "object"}
            }
        },
        "compliance": {
            "type": "object",
            "properties": {
                "industry_regulations": {"type": "array", "items": {"type": "string"}},
                "data_retention_days": {"type": "integer", "minimum": 1},
                "audit_trail_required": {"type": "boolean"},
                "pii_handling_required": {"type": "boolean"},
                "consent_management_required": {"type": "boolean"},
                "custom_compliance_rules": {"type": "object"}
            }
        },
        "communication_preferences": {"type": "object"},
        "service_level_agreement": {"type": "object"},
        "integrations": {"type": "object"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
        "version": {"type": "string"},
        "custom_fields": {"type": "object"}
    }
}


def validate_client_config(config_dict: Dict[str, Any]) -> List[str]:
    """
    Validate client configuration against JSON schema

    Args:
        config_dict: Client configuration as dictionary

    Returns:
        List of validation error messages (empty if valid)
    """
    try:
        jsonschema.validate(config_dict, CLIENT_CONFIG_SCHEMA)
        return []
    except jsonschema.ValidationError as e:
        return [f"Schema validation error: {e.message}"]
    except Exception as e:
        return [f"Validation error: {str(e)}"]


def create_default_client_config(client_id: str, client_name: str,
                               primary_email: str, google_ads_account_id: str,
                               account_manager: str, industry: IndustryType = IndustryType.OTHER) -> ClientSpecificConfig:
    """
    Create a default client configuration with sensible defaults

    Args:
        client_id: Unique client identifier
        client_name: Client company/organization name
        primary_email: Primary contact email
        google_ads_account_id: Google Ads account ID (format: XXX-XXX-XXXX)
        account_manager: Account manager name
        industry: Client industry type

    Returns:
        ClientSpecificConfig with default settings
    """
    return ClientSpecificConfig(
        client_id=client_id,
        client_name=client_name,
        industry=industry,
        primary_email=primary_email,
        google_ads_account_id=google_ads_account_id,
        account_manager=account_manager
    )


# Export for easy importing
__all__ = [
    'ClientSpecificConfig',
    'ClientKPIs',
    'ReportingPreferences',
    'BusinessRules',
    'OptimizationSettings',
    'ComplianceSettings',
    'ClientStatus',
    'IndustryType',
    'OptimizationStrategy',
    'validate_client_config',
    'create_default_client_config',
    'CLIENT_CONFIG_SCHEMA'
]
