"""
Client-Specific Business Rules and Validation Logic

This module implements comprehensive business rule validation for client-specific
operations in Google Ads management. It enforces client constraints, validates
operations against business rules, and provides compliance checking.

Key Features:
- Budget and bid limit validation
- Keyword and targeting restrictions
- Industry-specific compliance rules
- Custom business rule enforcement
- Operation pre-validation
"""

import logging
import re
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, time
from dataclasses import dataclass
from enum import Enum

from client_config_schema import (
    ClientSpecificConfig,
    IndustryType,
    BusinessRules,
    OptimizationSettings
)

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    severity: ValidationSeverity
    message: str
    rule_name: str
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "severity": self.severity.value,
            "message": self.message,
            "rule_name": self.rule_name,
            "suggestion": self.suggestion,
            "metadata": self.metadata or {}
        }


class BusinessRuleValidator:
    """
    Validates operations against client-specific business rules

    This class provides comprehensive validation for:
    - Budget constraints
    - Bid limits
    - Keyword restrictions
    - Targeting limitations
    - Industry compliance
    - Custom business rules
    """

    def __init__(self, client_config: ClientSpecificConfig):
        self.config = client_config
        self.business_rules = client_config.business_rules
        self.industry = client_config.industry

    def validate_campaign_creation(self, campaign_data: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate campaign creation against business rules

        Args:
            campaign_data: Campaign creation parameters

        Returns:
            List of validation results
        """
        results = []

        # Budget validation
        budget = campaign_data.get('budget', 0)
        campaign_type = campaign_data.get('type', 'default')

        budget_result = self._validate_budget_limit(budget, campaign_type)
        if budget_result:
            results.append(budget_result)

        # Targeting validation
        targeting = campaign_data.get('targeting', {})
        targeting_results = self._validate_targeting_restrictions(targeting)
        results.extend(targeting_results)

        # Industry-specific validation
        industry_results = self._validate_industry_rules(campaign_data)
        results.extend(industry_results)

        # Custom rules
        custom_results = self._validate_custom_rules('campaign_creation', campaign_data)
        results.extend(custom_results)

        return results

    def validate_keyword_addition(self, keywords: List[str],
                                match_types: Optional[List[str]] = None) -> List[ValidationResult]:
        """
        Validate keyword additions against restrictions

        Args:
            keywords: List of keywords to validate
            match_types: Corresponding match types

        Returns:
            List of validation results
        """
        results = []

        restricted_keywords = set(self.business_rules.keyword_restrictions)
        brand_terms = set(self.business_rules.brand_terms)

        for i, keyword in enumerate(keywords):
            keyword_lower = keyword.lower()

            # Check restricted keywords
            if keyword_lower in restricted_keywords:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Keyword '{keyword}' is restricted for this client",
                    rule_name="keyword_restriction",
                    suggestion="Remove this keyword or contact account manager for approval"
                ))

            # Check brand terms (may require special handling)
            if keyword_lower in brand_terms:
                results.append(ValidationResult(
                    is_valid=True,  # Valid but flagged
                    severity=ValidationSeverity.WARNING,
                    message=f"Keyword '{keyword}' matches brand term - ensure proper usage",
                    rule_name="brand_term_warning"
                ))

            # Industry-specific keyword validation
            industry_result = self._validate_industry_keyword(keyword, match_types[i] if match_types else None)
            if industry_result:
                results.append(industry_result)

        return results

    def validate_bid_changes(self, bid_changes: Dict[str, float]) -> List[ValidationResult]:
        """
        Validate bid changes against limits

        Args:
            bid_changes: Dictionary of keyword/ad -> new bid amount

        Returns:
            List of validation results
        """
        results = []

        min_bid = self.business_rules.bid_limits.get('min_bid')
        max_bid = self.business_rules.bid_limits.get('max_bid')

        for target, new_bid in bid_changes.items():
            if min_bid and new_bid < min_bid:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Bid ${new_bid} for '{target}' below minimum ${min_bid}",
                    rule_name="minimum_bid_limit",
                    suggestion=f"Increase bid to at least ${min_bid}"
                ))

            if max_bid and new_bid > max_bid:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Bid ${new_bid} for '{target}' above maximum ${max_bid}",
                    rule_name="maximum_bid_limit",
                    suggestion=f"Reduce bid to maximum ${max_bid}"
                ))

        return results

    def validate_budget_reallocation(self, current_budgets: Dict[str, float],
                                   proposed_changes: Dict[str, float]) -> List[ValidationResult]:
        """
        Validate budget reallocation against constraints

        Args:
            current_budgets: Current campaign budgets
            proposed_changes: Proposed budget changes (+/- amounts)

        Returns:
            List of validation results
        """
        results = []

        for campaign, change in proposed_changes.items():
            new_budget = current_budgets.get(campaign, 0) + change

            if new_budget < 0:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Budget reallocation would result in negative budget for campaign '{campaign}'",
                    rule_name="budget_reallocation_negative",
                    suggestion="Reduce budget reduction amount"
                ))
                continue

            # Check campaign-specific budget limits
            campaign_type = campaign.split('_')[0] if '_' in campaign else 'default'
            budget_result = self._validate_budget_limit(new_budget, campaign_type)
            if budget_result and not budget_result.is_valid:
                results.append(budget_result)

        return results

    def validate_audience_expansion(self, audience_data: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate audience expansion against client restrictions

        Args:
            audience_data: Audience targeting parameters

        Returns:
            List of validation results
        """
        results = []

        targeting_restrictions = self.business_rules.targeting_restrictions

        # Check geographic restrictions
        if 'locations' in audience_data:
            restricted_locations = targeting_restrictions.get('locations', [])
            for location in audience_data['locations']:
                if location in restricted_locations:
                    results.append(ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Location '{location}' is restricted for this client",
                        rule_name="location_restriction"
                    ))

        # Check demographic restrictions
        if 'demographics' in audience_data:
            restricted_demographics = targeting_restrictions.get('demographics', [])
            for demo in audience_data['demographics']:
                if demo in restricted_demographics:
                    results.append(ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Demographic targeting '{demo}' is restricted for this client",
                        rule_name="demographic_restriction"
                    ))

        # Industry-specific audience validation
        if self.industry == IndustryType.HEALTHCARE:
            healthcare_results = self._validate_healthcare_audience(audience_data)
            results.extend(healthcare_results)

        return results

    def validate_conversion_tracking(self, conversion_data: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate conversion tracking setup against requirements

        Args:
            conversion_data: Conversion tracking parameters

        Returns:
            List of validation results
        """
        results = []

        required_conversions = set(self.business_rules.conversion_actions)

        if 'conversions' in conversion_data:
            configured_conversions = set(conversion_data['conversions'])
            missing_conversions = required_conversions - configured_conversions

            if missing_conversions:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Missing required conversion actions: {', '.join(missing_conversions)}",
                    rule_name="required_conversions",
                    suggestion="Set up the missing conversion actions"
                ))

        # Validate conversion values are reasonable
        if 'conversion_value' in conversion_data:
            value = conversion_data['conversion_value']
            if value < 0:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message="Conversion value cannot be negative",
                    rule_name="conversion_value_validation"
                ))

        return results

    def _validate_budget_limit(self, budget: float, campaign_type: str) -> Optional[ValidationResult]:
        """Validate budget against campaign type limits"""
        max_budget = self.business_rules.budget_limits.get(campaign_type)

        if max_budget and budget > max_budget:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"Budget ${budget} exceeds maximum ${max_budget} for {campaign_type} campaigns",
                rule_name="budget_limit_exceeded",
                suggestion=f"Reduce budget to ${max_budget} or less"
            )

        return None

    def _validate_targeting_restrictions(self, targeting: Dict[str, Any]) -> List[ValidationResult]:
        """Validate targeting against client restrictions"""
        results = []

        restrictions = self.business_rules.targeting_restrictions

        for restriction_type, restricted_items in restrictions.items():
            if restriction_type in targeting:
                target_items = set(targeting[restriction_type])
                restricted_set = set(restricted_items)
                forbidden_items = target_items.intersection(restricted_set)

                if forbidden_items:
                    results.append(ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Targeting restriction violated for {restriction_type}: {', '.join(forbidden_items)}",
                        rule_name=f"{restriction_type}_restriction"
                    ))

        return results

    def _validate_industry_rules(self, operation_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate operation against industry-specific rules"""
        results = []

        if self.industry == IndustryType.HEALTHCARE:
            results.extend(self._validate_healthcare_rules(operation_data))
        elif self.industry == IndustryType.FINANCE:
            results.extend(self._validate_finance_rules(operation_data))
        elif self.industry == IndustryType.EDUCATION:
            results.extend(self._validate_education_rules(operation_data))

        return results

    def _validate_healthcare_rules(self, operation_data: Dict[str, Any]) -> List[ValidationResult]:
        """Healthcare industry specific validations"""
        results = []

        # Check for HIPAA compliance keywords
        sensitive_keywords = ['medical', 'health', 'patient', 'diagnosis', 'treatment']
        text_content = ' '.join(str(v) for v in operation_data.values() if isinstance(v, str))

        for keyword in sensitive_keywords:
            if keyword.lower() in text_content.lower():
                results.append(ValidationResult(
                    is_valid=True,  # Valid but requires attention
                    severity=ValidationSeverity.WARNING,
                    message=f"Content contains healthcare-related term '{keyword}' - ensure HIPAA compliance",
                    rule_name="healthcare_compliance_check"
                ))

        return results

    def _validate_finance_rules(self, operation_data: Dict[str, Any]) -> List[ValidationResult]:
        """Finance industry specific validations based on Google Ads policies"""
        results = []

        text_content = ' '.join(str(v) for v in operation_data.values() if isinstance(v, str))
        text_lower = text_content.lower()

        # Google Ads PROHIBITED Content - Credit Repair
        prohibited_credit_terms = [
            'credit repair', 'fix credit', 'improve credit score', 'credit restoration',
            'remove negative items', 'credit clean up', 'credit repair services'
        ]

        for term in prohibited_credit_terms:
            if term.lower() in text_lower:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"PROHIBITED: Credit repair advertising '{term}' violates Google Ads policy",
                    rule_name="google_credit_repair_prohibited",
                    suggestion="Remove credit repair claims - Google prohibits all credit repair advertising"
                ))

        # Google Ads RESTRICTED Content - Debt Services (Require Certification)
        debt_service_terms = [
            'debt settlement', 'debt management', 'debt relief', 'debt consolidation',
            'settle debt', 'manage debt', 'consolidate debt', 'debt reduction'
        ]

        for term in debt_service_terms:
            if term.lower() in text_lower:
                results.append(ValidationResult(
                    is_valid=False,  # Requires certification
                    severity=ValidationSeverity.CRITICAL,
                    message=f"RESTRICTED: Debt services '{term}' require Google Financial Services certification",
                    rule_name="google_debt_services_certification_required",
                    suggestion="Complete Google certification and ensure compliance with local regulations"
                ))

        # Google Ads RESTRICTED Content - MCA/Cash Advances
        mca_restricted_terms = [
            'merchant cash advance', 'mca', 'cash advance', 'business cash advance'
        ]

        for term in mca_restricted_terms:
            if term.lower() in text_lower:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"RESTRICTED: MCA advertising '{term}' has limitations due to payday loan associations",
                    rule_name="google_mca_restrictions",
                    suggestion="Avoid 'cash advance' terminology; use 'merchant financing' or 'business capital'"
                ))

        # Google Ads RESTRICTED Content - Loan Modification
        loan_mod_restricted_terms = [
            'loan modification', 'modify loan', 'foreclosure prevention', 'stop foreclosure',
            'save home', 'avoid foreclosure', 'mortgage modification', 'loan workout'
        ]

        for term in loan_mod_restricted_terms:
            if term.lower() in text_lower:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"HEAVILY RESTRICTED: Loan modification '{term}' cannot guarantee results or charge upfront fees",
                    rule_name="google_loan_mod_restrictions",
                    suggestion="Cannot guarantee loan modification; cannot charge upfront fees unless attorney"
                ))

        # Google Ads RESTRICTED Content - Payday Loans
        payday_restricted_terms = [
            'payday loan', 'payday advance', 'quick cash', 'fast cash',
            'emergency cash', 'instant loan', 'same day loan'
        ]

        for term in payday_restricted_terms:
            if term.lower() in text_lower:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"HEAVILY RESTRICTED: Payday loans '{term}' are generally prohibited",
                    rule_name="google_payday_loan_restrictions",
                    suggestion="Payday loans generally prohibited; cannot emphasize speed over terms"
                ))

        # Google Ads RESTRICTED Content - Cryptocurrency
        crypto_restricted_terms = [
            'cryptocurrency', 'bitcoin', 'crypto', 'blockchain investment',
            'digital currency', 'crypto trading'
        ]

        for term in crypto_restricted_terms:
            if term.lower() in text_lower:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"RESTRICTED: Cryptocurrency '{term}' requires Google certification",
                    rule_name="google_crypto_certification_required",
                    suggestion="Complete Google certification for cryptocurrency advertising"
                ))

        # Debt Purchasing/Collection Restrictions
        debt_collection_terms = [
            'debt purchasing', 'buy debt', 'purchase debt', 'debt collection',
            'collect debt', 'debt buyer', 'debt portfolio', 'charged-off debt'
        ]

        for term in debt_collection_terms:
            if term.lower() in text_lower:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"RESTRICTED: Debt purchasing '{term}' requires proper licensing and FDCPA compliance",
                    rule_name="debt_collection_licensing_required",
                    suggestion="Ensure state debt collection licensing and FDCPA compliance"
                ))

        # Traditional Finance Regulation Checks
        regulated_terms = ['investment', 'return', 'guarantee', 'risk-free', 'deposit']
        for term in regulated_terms:
            if term.lower() in text_lower:
                results.append(ValidationResult(
                    is_valid=True,  # Valid but requires attention
                    severity=ValidationSeverity.WARNING,
                    message=f"REGULATED: Content contains term '{term}' - ensure SEC/FINRA compliance",
                    rule_name="finance_regulation_check"
                ))

        # Check for misleading financial claims
        misleading_terms = [
            'guaranteed results', '100% success', 'no risk', 'risk-free',
            'instant approval', 'pre-approved', 'easy approval'
        ]

        for term in misleading_terms:
            if term.lower() in text_lower:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"MISLEADING: Term '{term}' may violate Google's prohibition on deceptive claims",
                    rule_name="google_misleading_claims_prohibited",
                    suggestion="Remove exaggerated claims; focus on factual information"
                ))

        return results

    def _validate_education_rules(self, operation_data: Dict[str, Any]) -> List[ValidationResult]:
        """Education industry specific validations"""
        results = []

        # Age targeting restrictions for educational content
        if 'age_ranges' in operation_data.get('targeting', {}):
            age_ranges = operation_data['targeting']['age_ranges']
            for age_range in age_ranges:
                if '13-17' in age_range:
                    results.append(ValidationResult(
                        is_valid=True,  # Valid but flagged
                        severity=ValidationSeverity.WARNING,
                        message="Targeting 13-17 age range - ensure COPPA compliance",
                        rule_name="coppa_compliance_check"
                    ))

        return results

    def _validate_industry_keyword(self, keyword: str, match_type: Optional[str]) -> Optional[ValidationResult]:
        """Validate keyword against industry-specific rules"""
        # Broad match validation for certain industries
        if self.industry == IndustryType.HEALTHCARE and match_type == 'BROAD':
            return ValidationResult(
                is_valid=True,  # Valid but caution advised
                severity=ValidationSeverity.WARNING,
                message=f"Broad match keyword '{keyword}' in healthcare industry may trigger unwanted impressions",
                rule_name="healthcare_broad_match_warning",
                suggestion="Consider using phrase or exact match for better control"
            )

        return None

    def _validate_custom_rules(self, operation_type: str, operation_data: Dict[str, Any]) -> List[ValidationResult]:
        """Validate against custom business rules"""
        results = []

        custom_rules = self.business_rules.custom_rules
        if not custom_rules:
            return results

        # Apply custom validation logic
        for rule_name, rule_config in custom_rules.items():
            if rule_config.get('operation_type') == operation_type:
                rule_result = self._apply_custom_rule(rule_name, rule_config, operation_data)
                if rule_result:
                    results.append(rule_result)

        return results

    def _apply_custom_rule(self, rule_name: str, rule_config: Dict[str, Any],
                          operation_data: Dict[str, Any]) -> Optional[ValidationResult]:
        """Apply a custom validation rule"""
        try:
            rule_type = rule_config.get('type')
            field = rule_config.get('field')
            condition = rule_config.get('condition')
            value = rule_config.get('value')

            if field not in operation_data:
                return None

            actual_value = operation_data[field]

            if rule_type == 'range':
                min_val = condition.get('min')
                max_val = condition.get('max')
                if min_val is not None and actual_value < min_val:
                    return ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Custom rule '{rule_name}': {field} value {actual_value} below minimum {min_val}",
                        rule_name=f"custom_{rule_name}"
                    )
                if max_val is not None and actual_value > max_val:
                    return ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Custom rule '{rule_name}': {field} value {actual_value} above maximum {max_val}",
                        rule_name=f"custom_{rule_name}"
                    )

            elif rule_type == 'regex':
                if not re.match(condition, str(actual_value)):
                    return ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Custom rule '{rule_name}': {field} value '{actual_value}' does not match required pattern",
                        rule_name=f"custom_{rule_name}"
                    )

            elif rule_type == 'list':
                allowed_values = condition.get('allowed', [])
                if actual_value not in allowed_values:
                    return ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Custom rule '{rule_name}': {field} value '{actual_value}' not in allowed list",
                        rule_name=f"custom_{rule_name}",
                        suggestion=f"Allowed values: {', '.join(allowed_values)}"
                    )

        except Exception as e:
            logger.error(f"Error applying custom rule {rule_name}: {e}")

        return None

    def _validate_healthcare_audience(self, audience_data: Dict[str, Any]) -> List[ValidationResult]:
        """Healthcare-specific audience validation"""
        results = []

        # Healthcare may have restrictions on certain audience types
        restricted_audience_types = ['alcohol', 'gambling', 'adult_content']

        if 'interests' in audience_data:
            for interest in audience_data['interests']:
                if any(restricted in interest.lower() for restricted in restricted_audience_types):
                    results.append(ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Audience interest '{interest}' may not be suitable for healthcare industry",
                        rule_name="healthcare_audience_restriction"
                    ))

        return results

    def validate_operation_pre_execution(self, operation_type: str,
                                       operation_data: Dict[str, Any]) -> Tuple[bool, List[ValidationResult]]:
        """
        Comprehensive pre-execution validation for any operation

        Args:
            operation_type: Type of operation being validated
            operation_data: Operation parameters

        Returns:
            Tuple of (is_valid, validation_results)
        """
        all_results = []

        # Route to specific validation methods
        if operation_type == 'campaign_creation':
            all_results.extend(self.validate_campaign_creation(operation_data))
        elif operation_type == 'keyword_addition':
            keywords = operation_data.get('keywords', [])
            match_types = operation_data.get('match_types')
            all_results.extend(self.validate_keyword_addition(keywords, match_types))
        elif operation_type == 'bid_change':
            bid_changes = operation_data.get('bid_changes', {})
            all_results.extend(self.validate_bid_changes(bid_changes))
        elif operation_type == 'budget_reallocation':
            current_budgets = operation_data.get('current_budgets', {})
            proposed_changes = operation_data.get('proposed_changes', {})
            all_results.extend(self.validate_budget_reallocation(current_budgets, proposed_changes))
        elif operation_type == 'audience_expansion':
            all_results.extend(self.validate_audience_expansion(operation_data))
        elif operation_type == 'conversion_setup':
            all_results.extend(self.validate_conversion_tracking(operation_data))

        # Check if any critical errors exist
        has_critical_errors = any(
            result.severity == ValidationSeverity.CRITICAL and not result.is_valid
            for result in all_results
        )

        has_errors = any(
            result.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] and not result.is_valid
            for result in all_results
        )

        is_valid = not has_critical_errors  # Allow warnings but not critical errors

        return is_valid, all_results


def validate_client_operation(client_config: ClientSpecificConfig,
                            operation_type: str,
                            operation_data: Dict[str, Any]) -> Tuple[bool, List[ValidationResult]]:
    """
    Convenience function to validate any client operation

    Args:
        client_config: Client-specific configuration
        operation_type: Type of operation
        operation_data: Operation parameters

    Returns:
        Tuple of (is_valid, validation_results)
    """
    validator = BusinessRuleValidator(client_config)
    return validator.validate_operation_pre_execution(operation_type, operation_data)


# Export for easy importing
__all__ = [
    'BusinessRuleValidator',
    'ValidationResult',
    'ValidationSeverity',
    'validate_client_operation'
]
