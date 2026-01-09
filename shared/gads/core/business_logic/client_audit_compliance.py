"""
Client-Specific Audit and Compliance Tracking

This module provides comprehensive audit trails and compliance monitoring for
client-specific operations in Google Ads management. It ensures regulatory
compliance, data retention policies, and maintains detailed operation logs.

Key Features:
- Comprehensive audit trail logging
- Regulatory compliance monitoring
- Data retention policy enforcement
- Compliance violation detection
- Audit report generation
- Privacy and security compliance
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import hashlib
import re

from client_config_schema import (
    ClientSpecificConfig,
    ComplianceSettings,
    IndustryType
)
from client_context_manager import ClientOperation

logger = logging.getLogger(__name__)


class ComplianceViolationSeverity(Enum):
    """Compliance violation severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEventType(Enum):
    """Types of auditable events"""
    OPERATION_EXECUTED = "operation_executed"
    DATA_ACCESSED = "data_accessed"
    CONFIGURATION_CHANGED = "configuration_changed"
    CREDENTIALS_ACCESSED = "credentials_accessed"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SECURITY_EVENT = "security_event"
    DATA_RETENTION_ENFORCED = "data_retention_enforced"


@dataclass
class ComplianceViolation:
    """Represents a compliance violation"""
    violation_id: str
    client_id: str
    regulation: str
    severity: ComplianceViolationSeverity
    description: str
    detected_at: datetime
    operation_context: Optional[str] = None
    remediation_required: bool = True
    remediation_steps: List[str] = field(default_factory=list)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    def mark_resolved(self, notes: Optional[str] = None):
        """Mark violation as resolved"""
        self.resolved = True
        self.resolved_at = datetime.now()
        self.resolution_notes = notes


@dataclass
class AuditEvent:
    """Represents an auditable event"""
    event_id: str
    client_id: str
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str] = None
    operation_id: Optional[str] = None
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    compliance_checked: bool = False
    compliance_violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "client_id": self.client_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "operation_id": self.operation_id,
            "description": self.description,
            "metadata": self.metadata,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "compliance_checked": self.compliance_checked,
            "compliance_violations": self.compliance_violations
        }


@dataclass
class ComplianceReport:
    """Compliance status report for a client"""
    client_id: str
    report_date: datetime
    overall_compliant: bool
    regulations_checked: List[str] = field(default_factory=list)
    violations_found: List[ComplianceViolation] = field(default_factory=list)
    compliance_score: float = 0.0  # 0.0 to 1.0
    recommendations: List[str] = field(default_factory=list)
    next_review_date: Optional[datetime] = None

    def calculate_compliance_score(self):
        """Calculate overall compliance score"""
        if not self.regulations_checked:
            self.compliance_score = 0.0
            return

        total_regulations = len(self.regulations_checked)
        violations_by_severity = {
            ComplianceViolationSeverity.LOW: 0,
            ComplianceViolationSeverity.MEDIUM: 0,
            ComplianceViolationSeverity.HIGH: 0,
            ComplianceViolationSeverity.CRITICAL: 0
        }

        for violation in self.violations_found:
            violations_by_severity[violation.severity] += 1

        # Weight violations by severity
        penalty_weights = {
            ComplianceViolationSeverity.LOW: 0.1,
            ComplianceViolationSeverity.MEDIUM: 0.3,
            ComplianceViolationSeverity.HIGH: 0.6,
            ComplianceViolationSeverity.CRITICAL: 1.0
        }

        total_penalty = 0
        for severity, count in violations_by_severity.items():
            total_penalty += penalty_weights[severity] * count

        # Calculate score (1.0 = perfect compliance, 0.0 = severe violations)
        self.compliance_score = max(0.0, 1.0 - (total_penalty / total_regulations))


class ClientAuditComplianceManager:
    """
    Client-specific audit and compliance management

    This class provides:
    - Comprehensive audit trail management
    - Regulatory compliance monitoring
    - Data retention policy enforcement
    - Compliance violation detection and reporting
    - Privacy and security compliance
    """

    def __init__(self, client_config: ClientSpecificConfig, storage_path: Optional[Path] = None):
        self.client_config = client_config
        self.client_id = client_config.client_id
        self.compliance_settings = client_config.compliance

        # Storage paths
        self.storage_path = storage_path or Path("./client_audit_data")
        self.audit_path = self.storage_path / self.client_id / "audit"
        self.compliance_path = self.storage_path / self.client_id / "compliance"
        self.audit_path.mkdir(parents=True, exist_ok=True)
        self.compliance_path.mkdir(parents=True, exist_ok=True)

        # In-memory caches
        self.audit_events: List[AuditEvent] = []
        self.compliance_violations: List[ComplianceViolation] = []

        # Load existing data
        self._load_audit_events()
        self._load_compliance_violations()

        logger.info(f"Initialized audit compliance manager for client {self.client_config.client_name}")

    def log_audit_event(self, event_type: AuditEventType, description: str,
                       metadata: Optional[Dict[str, Any]] = None,
                       user_id: Optional[str] = None,
                       operation_id: Optional[str] = None) -> str:
        """
        Log an auditable event

        Args:
            event_type: Type of event being logged
            description: Human-readable description
            metadata: Additional event metadata
            user_id: User performing the action
            operation_id: Associated operation ID

        Returns:
            Event ID for tracking
        """
        import secrets

        event_id = f"{self.client_id}_{event_type.value}_{secrets.token_hex(4)}_{int(datetime.now().timestamp())}"

        event = AuditEvent(
            event_id=event_id,
            client_id=self.client_id,
            event_type=event_type,
            timestamp=datetime.now(),
            user_id=user_id,
            operation_id=operation_id,
            description=description,
            metadata=metadata or {}
        )

        # Check compliance for the event
        violations = self._check_event_compliance(event)
        event.compliance_checked = True
        event.compliance_violations = [v.violation_id for v in violations]

        # Log any new violations
        for violation in violations:
            if violation not in self.compliance_violations:
                self.compliance_violations.append(violation)
                self._save_compliance_violation(violation)

        # Add to audit trail
        self.audit_events.append(event)

        # Maintain audit trail size (keep last 10,000 events)
        if len(self.audit_events) > 10000:
            self.audit_events.pop(0)

        # Save to disk
        self._save_audit_event(event)

        logger.info(f"Audit event logged: {event_type.value} - {description}")
        return event_id

    def _check_event_compliance(self, event: AuditEvent) -> List[ComplianceViolation]:
        """Check an event for compliance violations"""
        violations = []

        # Industry-specific compliance checks
        if self.client_config.industry == IndustryType.HEALTHCARE:
            violations.extend(self._check_healthcare_compliance(event))
        elif self.client_config.industry == IndustryType.FINANCE:
            violations.extend(self._check_finance_compliance(event))
        elif self.client_config.industry == IndustryType.EDUCATION:
            violations.extend(self._check_education_compliance(event))

        # General compliance checks
        violations.extend(self._check_general_compliance(event))

        return violations

    def _check_healthcare_compliance(self, event: AuditEvent) -> List[ComplianceViolation]:
        """Check healthcare-specific compliance (HIPAA, FDA regulations)"""
        violations = []

        # Check for PHI in metadata
        phi_indicators = ['medical', 'health', 'patient', 'diagnosis', 'treatment', 'medication']
        metadata_str = json.dumps(event.metadata).lower()

        if any(indicator in metadata_str for indicator in phi_indicators):
            # Check if event involves data access without proper safeguards
            if event.event_type in [AuditEventType.DATA_ACCESSED, AuditEventType.OPERATION_EXECUTED]:
                if not self._has_hipaa_safeguards(event):
                    violations.append(ComplianceViolation(
                        violation_id=f"hipaa_phi_{event.event_id}",
                        client_id=self.client_id,
                        regulation="HIPAA",
                        severity=ComplianceViolationSeverity.HIGH,
                        description="Potential Protected Health Information (PHI) accessed without HIPAA safeguards",
                        detected_at=datetime.now(),
                        operation_context=event.operation_id,
                        remediation_steps=[
                            "Implement HIPAA Business Associate Agreement",
                            "Apply PHI encryption and access controls",
                            "Conduct HIPAA training for personnel",
                            "Implement audit controls for PHI access"
                        ]
                    ))

        # Check for FDA-regulated claims
        if 'ad_content' in event.metadata:
            ad_content = event.metadata['ad_content'].lower()
            regulated_terms = ['cure', 'treat', 'prevent', 'relieve', 'heal']

            if any(term in ad_content for term in regulated_terms):
                violations.append(ComplianceViolation(
                    violation_id=f"fda_claims_{event.event_id}",
                    client_id=self.client_id,
                    regulation="FDA Advertising Regulations",
                    severity=ComplianceViolationSeverity.CRITICAL,
                    description="Ad content contains potential FDA-regulated health claims",
                    detected_at=datetime.now(),
                    operation_context=event.operation_id,
                    remediation_steps=[
                        "Review claims against FDA guidelines",
                        "Obtain competent and reliable scientific evidence",
                        "Consult with FDA regulatory expert",
                        "Modify ad content to avoid unsubstantiated claims"
                    ]
                ))

        return violations

    def _check_finance_compliance(self, event: AuditEvent) -> List[ComplianceViolation]:
        """Check finance industry compliance (SEC, FINRA, Google Ads policies)"""
        violations = []

        # Google Ads Finance Policies - Debt Services, MCA, Cash Advances
        violations.extend(self._check_google_ads_finance_policies(event))

        # Traditional Finance Compliance - Investment Advice, FINRA
        violations.extend(self._check_traditional_finance_compliance(event))

        return violations

    def _check_google_ads_finance_policies(self, event: AuditEvent) -> List[ComplianceViolation]:
        """Check Google Ads specific finance policies for debt services, MCA, etc."""
        violations = []
        metadata_str = json.dumps(event.metadata).lower()

        # Debt Settlement and Debt Management Services
        debt_service_terms = [
            'debt settlement', 'debt management', 'debt relief', 'debt consolidation',
            'debt reduction', 'settle debt', 'manage debt', 'consolidate debt'
        ]

        if any(term in metadata_str for term in debt_service_terms):
            # Google requires certification for debt services
            if not self._has_google_finance_certification():
                violations.append(ComplianceViolation(
                    violation_id=f"debt_services_certification_{event.event_id}",
                    client_id=self.client_id,
                    regulation="Google Ads Financial Services Certification",
                    severity=ComplianceViolationSeverity.CRITICAL,
                    description="Advertising debt settlement/management services requires Google certification",
                    detected_at=datetime.now(),
                    operation_context=event.operation_id,
                    remediation_steps=[
                        "Complete Google's Financial Services verification process",
                        "Be registered/licensed/approved by relevant regulatory authorities",
                        "Only advertise in approved countries (US, UK, Canada, etc.)",
                        "For US: Must be approved non-profit budget/credit counseling agency per 11 U.S. Code § 111"
                    ]
                ))

        # Merchant Cash Advances (MCA) and Cash Advances
        mca_terms = [
            'merchant cash advance', 'mca', 'cash advance', 'business cash advance',
            'merchant financing', 'business financing', 'working capital financing'
        ]

        if any(term in metadata_str for term in mca_terms):
            # MCA advertising has restrictions due to "cash advance" association with payday loans
            violations.append(ComplianceViolation(
                violation_id=f"mca_restrictions_{event.event_id}",
                client_id=self.client_id,
                regulation="Google Ads Financial Services Policy",
                severity=ComplianceViolationSeverity.HIGH,
                description="MCA advertising restricted due to 'cash advance' association with payday loans",
                detected_at=datetime.now(),
                operation_context=event.operation_id,
                remediation_steps=[
                    "Avoid using 'cash advance' terminology in ads",
                    "Use terms like 'merchant financing', 'business capital', 'working capital'",
                    "Ensure compliance with state lending laws",
                    "Consider alternative ad platforms if restrictions are too limiting"
                ]
            ))

        # Credit Repair Services - PROHIBITED by Google
        credit_repair_terms = [
            'credit repair', 'fix credit', 'improve credit score', 'credit restoration',
            'remove negative items', 'credit clean up', 'credit repair services'
        ]

        if any(term in metadata_str for term in credit_repair_terms):
            violations.append(ComplianceViolation(
                violation_id=f"credit_repair_prohibited_{event.event_id}",
                client_id=self.client_id,
                regulation="Google Ads Prohibited Content Policy",
                severity=ComplianceViolationSeverity.CRITICAL,
                description="Credit repair services advertising is prohibited by Google Ads",
                detected_at=datetime.now(),
                operation_context=event.operation_id,
                remediation_steps=[
                    "Remove all credit repair advertising",
                    "Focus on allowed financial services (debt management, etc.)",
                    "Consult Google Ads policy documentation for allowed services"
                ]
            ))

        # Debt Purchasing/Collection Advertising
        debt_purchasing_terms = [
            'debt purchasing', 'buy debt', 'purchase debt', 'debt collection',
            'collect debt', 'debt buyer', 'debt portfolio', 'charged-off debt'
        ]

        if any(term in metadata_str for term in debt_purchasing_terms):
            # Debt purchasing has specific restrictions
            violations.append(ComplianceViolation(
                violation_id=f"debt_purchasing_restrictions_{event.event_id}",
                client_id=self.client_id,
                regulation="Google Ads Financial Services Policy",
                severity=ComplianceViolationSeverity.HIGH,
                description="Debt purchasing advertising has restrictions and requires proper licensing",
                detected_at=datetime.now(),
                operation_context=event.operation_id,
                remediation_steps=[
                    "Ensure proper state licensing for debt collection",
                    "Avoid deceptive collection practices",
                    "Comply with FDCPA (Fair Debt Collection Practices Act)",
                    "Include clear business identification in ads"
                ]
            ))

        # Loan Modification and Foreclosure Prevention - RESTRICTED
        loan_mod_terms = [
            'loan modification', 'modify loan', 'foreclosure prevention', 'stop foreclosure',
            'save home', 'avoid foreclosure', 'loan workout', 'mortgage modification'
        ]

        if any(term in metadata_str for term in loan_mod_terms):
            violations.append(ComplianceViolation(
                violation_id=f"loan_modification_restricted_{event.event_id}",
                client_id=self.client_id,
                regulation="Google Ads Loan Modification Policy",
                severity=ComplianceViolationSeverity.CRITICAL,
                description="Loan modification advertising has strict restrictions",
                detected_at=datetime.now(),
                operation_context=event.operation_id,
                remediation_steps=[
                    "Cannot guarantee loan modification or foreclosure prevention",
                    "Cannot charge upfront fees (unless law firm)",
                    "Cannot request property title transfer",
                    "Cannot encourage bypassing lender",
                    "Must be properly licensed attorney or firm",
                    "Must comply with RESPA and state laws"
                ]
            ))

        # Payday Loans and High-Interest Lending
        payday_terms = [
            'payday loan', 'payday advance', 'quick cash', 'fast cash',
            'emergency cash', 'instant loan', 'same day loan'
        ]

        if any(term in metadata_str for term in payday_terms):
            violations.append(ComplianceViolation(
                violation_id=f"payday_loans_restricted_{event.event_id}",
                client_id=self.client_id,
                regulation="Google Ads Financial Products Policy",
                severity=ComplianceViolationSeverity.CRITICAL,
                description="Payday loans and high-interest lending heavily restricted or prohibited",
                detected_at=datetime.now(),
                operation_context=event.operation_id,
                remediation_steps=[
                    "Payday loans generally prohibited",
                    "Cannot emphasize speed/ease over terms",
                    "Must disclose all fees and APR prominently",
                    "May require state-specific licensing verification",
                    "Consider if business model violates Google's policies"
                ]
            ))

        # Cryptocurrency and Speculative Products
        crypto_terms = [
            'cryptocurrency', 'bitcoin', 'crypto', 'blockchain investment',
            'digital currency', 'crypto trading', 'nft', 'decentralized finance'
        ]

        if any(term in metadata_str for term in crypto_terms):
            if not self._has_crypto_certification():
                violations.append(ComplianceViolation(
                    violation_id=f"crypto_certification_{event.event_id}",
                    client_id=self.client_id,
                    regulation="Google Ads Cryptocurrency Policy",
                    severity=ComplianceViolationSeverity.HIGH,
                    description="Cryptocurrency advertising requires Google certification",
                    detected_at=datetime.now(),
                    operation_context=event.operation_id,
                    remediation_steps=[
                        "Complete Google certification for cryptocurrency services",
                        "Comply with local laws and industry standards",
                        "Only advertise approved crypto products",
                        "Include risk disclosures prominently"
                    ]
                ))

        return violations

    def _check_traditional_finance_compliance(self, event: AuditEvent) -> List[ComplianceViolation]:
        """Check traditional finance compliance (SEC, FINRA regulations)"""
        violations = []

        # Check for investment advice without proper licensing
        if event.event_type == AuditEventType.OPERATION_EXECUTED:
            metadata_str = json.dumps(event.metadata).lower()
            investment_terms = ['invest', 'return', 'guarantee', 'risk', 'portfolio', 'diversify']

            if any(term in metadata_str for term in investment_terms):
                # Check if client has FINRA licensing
                if 'finra' not in self.compliance_settings.industry_regulations:
                    violations.append(ComplianceViolation(
                        violation_id=f"finra_licensing_{event.event_id}",
                        client_id=self.client_id,
                        regulation="FINRA Licensing",
                        severity=ComplianceViolationSeverity.CRITICAL,
                        description="Potential investment advice provided without FINRA licensing",
                        detected_at=datetime.now(),
                        operation_context=event.operation_id,
                        remediation_steps=[
                            "Obtain appropriate FINRA licensing (Series 65)",
                            "Implement investment advisory disclaimers",
                            "Limit advice to general educational content",
                            "Consult with compliance attorney"
                        ]
                    ))

        return violations

    def _has_google_finance_certification(self) -> bool:
        """Check if client has Google Financial Services certification"""
        # Check if certification is listed in compliance settings
        certifications = self.compliance_settings.custom_compliance_rules.get('google_certifications', [])
        return 'financial_services' in certifications

    def _has_crypto_certification(self) -> bool:
        """Check if client has Google cryptocurrency certification"""
        certifications = self.compliance_settings.custom_compliance_rules.get('google_certifications', [])
        return 'cryptocurrency' in certifications

    def _check_education_compliance(self, event: AuditEvent) -> List[ComplianceViolation]:
        """Check education industry compliance (FERPA, COPPA)"""
        violations = []

        # Check for student data handling (FERPA)
        if event.event_type == AuditEventType.DATA_ACCESSED:
            metadata_str = json.dumps(event.metadata).lower()
            student_data_indicators = ['student', 'grade', 'academic', 'enrollment', 'transcript']

            if any(indicator in metadata_str for indicator in student_data_indicators):
                violations.append(ComplianceViolation(
                    violation_id=f"ferpa_student_data_{event.event_id}",
                    client_id=self.client_id,
                    regulation="FERPA",
                    severity=ComplianceViolationSeverity.HIGH,
                    description="Student educational records accessed - FERPA compliance required",
                    detected_at=datetime.now(),
                    operation_context=event.operation_id,
                    remediation_steps=[
                        "Obtain parental consent for student data collection",
                        "Implement FERPA-compliant data handling procedures",
                        "Limit student data to directory information only",
                        "Train staff on FERPA requirements"
                    ]
                ))

        # Check for COPPA compliance (under 13 targeting)
        if 'targeting' in event.metadata:
            targeting = event.metadata['targeting']
            if isinstance(targeting, dict) and 'age_range' in targeting:
                age_range = targeting['age_range']
                if '13-17' in str(age_range) or 'under 13' in str(age_range).lower():
                    violations.append(ComplianceViolation(
                        violation_id=f"coppa_age_targeting_{event.event_id}",
                        client_id=self.client_id,
                        regulation="COPPA",
                        severity=ComplianceViolationSeverity.CRITICAL,
                        description="Targeting children under 13 - COPPA compliance required",
                        detected_at=datetime.now(),
                        operation_context=event.operation_id,
                        remediation_steps=[
                            "Obtain verifiable parental consent",
                            "Implement COPPA-compliant privacy policy",
                            "Limit data collection from children",
                            "Provide parental access and deletion rights"
                        ]
                    ))

        return violations

    def _check_general_compliance(self, event: AuditEvent) -> List[ComplianceViolation]:
        """Check general compliance requirements"""
        violations = []

        # Check data retention compliance
        if event.event_type == AuditEventType.DATA_ACCESSED:
            # Verify data retention policies are being followed
            if self._exceeds_retention_period(event):
                violations.append(ComplianceViolation(
                    violation_id=f"retention_policy_{event.event_id}",
                    client_id=self.client_id,
                    regulation="Data Retention Policy",
                    severity=ComplianceViolationSeverity.MEDIUM,
                    description="Data accessed beyond configured retention period",
                    detected_at=datetime.now(),
                    operation_context=event.operation_id,
                    remediation_steps=[
                        "Implement automated data purging",
                        "Review data retention schedule",
                        "Archive historical data appropriately",
                        "Update retention policy documentation"
                    ]
                ))

        # Check for PII handling compliance
        if self.compliance_settings.pii_handling_required:
            if self._contains_pii(event.metadata):
                if not self._has_pii_protections(event):
                    violations.append(ComplianceViolation(
                        violation_id=f"pii_handling_{event.event_id}",
                        client_id=self.client_id,
                        regulation="PII Handling Requirements",
                        severity=ComplianceViolationSeverity.HIGH,
                        description="Personally Identifiable Information handled without required protections",
                        detected_at=datetime.now(),
                        operation_context=event.operation_id,
                        remediation_steps=[
                            "Implement PII encryption at rest and in transit",
                            "Apply data minimization principles",
                            "Conduct PII impact assessment",
                            "Implement access controls and audit logging"
                        ]
                    ))

        return violations

    def _has_hipaa_safeguards(self, event: AuditEvent) -> bool:
        """Check if HIPAA safeguards are in place for the event"""
        # This would check if proper HIPAA controls are implemented
        # For now, return False to trigger compliance checks
        return False

    def _exceeds_retention_period(self, event: AuditEvent) -> bool:
        """Check if data access exceeds retention period"""
        if 'data_age_days' in event.metadata:
            data_age = event.metadata['data_age_days']
            max_retention = self.compliance_settings.data_retention_days
            return data_age > max_retention
        return False

    def _contains_pii(self, metadata: Dict[str, Any]) -> bool:
        """Check if metadata contains personally identifiable information"""
        pii_indicators = ['email', 'phone', 'address', 'ssn', 'name', 'birthdate']
        metadata_str = json.dumps(metadata).lower()

        return any(indicator in metadata_str for indicator in pii_indicators)

    def _has_pii_protections(self, event: AuditEvent) -> bool:
        """Check if PII protections are in place"""
        # Check if encryption and access controls are mentioned in metadata
        metadata_str = json.dumps(event.metadata).lower()
        protection_indicators = ['encrypted', 'hashed', 'anonymized', 'access_control']

        return any(indicator in metadata_str for indicator in protection_indicators)

    def generate_compliance_report(self) -> ComplianceReport:
        """Generate a comprehensive compliance report"""
        report = ComplianceReport(
            client_id=self.client_id,
            report_date=datetime.now(),
            overall_compliant=True,
            regulations_checked=self.compliance_settings.industry_regulations.copy(),
            violations_found=self.compliance_violations.copy()
        )

        # Add general regulations
        general_regs = ["Data Retention", "PII Handling", "Audit Trail"]
        if self.compliance_settings.audit_trail_required:
            report.regulations_checked.extend(general_regs)

        # Check for unresolved violations
        unresolved_violations = [v for v in self.compliance_violations if not v.resolved]
        report.overall_compliant = len(unresolved_violations) == 0

        # Calculate compliance score
        report.calculate_compliance_score()

        # Generate recommendations
        report.recommendations = self._generate_compliance_recommendations(report)

        # Set next review date (quarterly)
        report.next_review_date = datetime.now() + timedelta(days=90)

        return report

    def _generate_compliance_recommendations(self, report: ComplianceReport) -> List[str]:
        """Generate compliance improvement recommendations"""
        recommendations = []

        if report.compliance_score < 0.8:
            recommendations.append("Conduct comprehensive compliance training for all staff")

        unresolved_critical = [v for v in report.violations_found
                             if not v.resolved and v.severity == ComplianceViolationSeverity.CRITICAL]

        if unresolved_critical:
            recommendations.append(f"Address {len(unresolved_critical)} critical compliance violations immediately")

        # Industry-specific recommendations
        if self.client_config.industry == IndustryType.HEALTHCARE:
            recommendations.extend([
                "Implement HIPAA Business Associate Agreement with all vendors",
                "Conduct annual HIPAA training for all personnel",
                "Establish PHI breach notification procedures"
            ])
        elif self.client_config.industry == IndustryType.FINANCE:
            recommendations.extend([
                "Obtain required FINRA licensing for investment advice",
                "Implement SEC advertising compliance procedures",
                "Establish complaint handling and resolution procedures"
            ])

        return recommendations

    def enforce_data_retention(self) -> Dict[str, Any]:
        """Enforce data retention policies by cleaning up old data"""
        retention_days = self.compliance_settings.data_retention_days
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        # Count events to be deleted
        old_events = [e for e in self.audit_events if e.timestamp < cutoff_date]
        events_deleted = len(old_events)

        # Remove old events
        self.audit_events = [e for e in self.audit_events if e.timestamp >= cutoff_date]

        # Log retention enforcement
        self.log_audit_event(
            AuditEventType.DATA_RETENTION_ENFORCED,
            f"Enforced data retention policy: deleted {events_deleted} audit events older than {retention_days} days",
            metadata={"events_deleted": events_deleted, "retention_days": retention_days}
        )

        return {
            "events_deleted": events_deleted,
            "retention_days": retention_days,
            "remaining_events": len(self.audit_events)
        }

    def get_audit_trail(self, start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       event_type: Optional[AuditEventType] = None,
                       limit: int = 1000) -> List[AuditEvent]:
        """Get filtered audit trail"""
        filtered_events = self.audit_events

        if start_date:
            filtered_events = [e for e in filtered_events if e.timestamp >= start_date]
        if end_date:
            filtered_events = [e for e in filtered_events if e.timestamp <= end_date]
        if event_type:
            filtered_events = [e for e in filtered_events if e.event_type == event_type]

        return filtered_events[-limit:] if limit > 0 else filtered_events

    def resolve_compliance_violation(self, violation_id: str, resolution_notes: str) -> bool:
        """Mark a compliance violation as resolved"""
        for violation in self.compliance_violations:
            if violation.violation_id == violation_id:
                violation.mark_resolved(resolution_notes)

                # Log resolution
                self.log_audit_event(
                    AuditEventType.COMPLIANCE_VIOLATION,
                    f"Compliance violation resolved: {violation.description}",
                    metadata={
                        "violation_id": violation_id,
                        "resolution_notes": resolution_notes
                    }
                )

                # Save updated violation
                self._save_compliance_violation(violation)
                return True

        return False

    def _save_audit_event(self, event: AuditEvent):
        """Save audit event to disk"""
        try:
            filename = f"audit_{event.timestamp.strftime('%Y%m%d')}.jsonl"
            filepath = self.audit_path / filename

            with open(filepath, 'a') as f:
                f.write(json.dumps(event.to_dict()) + '\n')

        except Exception as e:
            logger.error(f"Failed to save audit event {event.event_id}: {e}")

    def _save_compliance_violation(self, violation: ComplianceViolation):
        """Save compliance violation to disk"""
        try:
            filename = f"violations_{violation.detected_at.strftime('%Y%m')}.json"
            filepath = self.compliance_path / filename

            # Load existing violations for this month
            existing_violations = []
            if filepath.exists():
                with open(filepath, 'r') as f:
                    existing_violations = json.load(f)

            # Update or add violation
            violation_dict = {
                "violation_id": violation.violation_id,
                "client_id": violation.client_id,
                "regulation": violation.regulation,
                "severity": violation.severity.value,
                "description": violation.description,
                "detected_at": violation.detected_at.isoformat(),
                "operation_context": violation.operation_context,
                "remediation_required": violation.remediation_required,
                "remediation_steps": violation.remediation_steps,
                "resolved": violation.resolved,
                "resolved_at": violation.resolved_at.isoformat() if violation.resolved_at else None,
                "resolution_notes": violation.resolution_notes
            }

            # Find and update existing violation or add new one
            found = False
            for i, v in enumerate(existing_violations):
                if v["violation_id"] == violation.violation_id:
                    existing_violations[i] = violation_dict
                    found = True
                    break

            if not found:
                existing_violations.append(violation_dict)

            with open(filepath, 'w') as f:
                json.dump(existing_violations, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save compliance violation {violation.violation_id}: {e}")

    def _load_audit_events(self):
        """Load audit events from disk"""
        try:
            for jsonl_file in self.audit_path.glob("audit_*.jsonl"):
                with open(jsonl_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            event_data = json.loads(line.strip())
                            # Convert back to AuditEvent
                            event_data["event_type"] = AuditEventType(event_data["event_type"])
                            event_data["timestamp"] = datetime.fromisoformat(event_data["timestamp"])
                            self.audit_events.append(AuditEvent(**event_data))

            # Sort by timestamp
            self.audit_events.sort(key=lambda x: x.timestamp)

        except Exception as e:
            logger.error(f"Failed to load audit events: {e}")

    def _load_compliance_violations(self):
        """Load compliance violations from disk"""
        try:
            for json_file in self.compliance_path.glob("violations_*.json"):
                with open(json_file, 'r') as f:
                    violations_data = json.load(f)
                    for v_data in violations_data:
                        # Convert back to ComplianceViolation
                        v_data["severity"] = ComplianceViolationSeverity(v_data["severity"])
                        v_data["detected_at"] = datetime.fromisoformat(v_data["detected_at"])
                        if v_data.get("resolved_at"):
                            v_data["resolved_at"] = datetime.fromisoformat(v_data["resolved_at"])
                        self.compliance_violations.append(ComplianceViolation(**v_data))

        except Exception as e:
            logger.error(f"Failed to load compliance violations: {e}")


def create_client_compliance_audit(client_config: ClientSpecificConfig) -> ClientAuditComplianceManager:
    """
    Create a compliance and audit manager for a client

    Args:
        client_config: Client-specific configuration

    Returns:
        ClientAuditComplianceManager instance
    """
    return ClientAuditComplianceManager(client_config)


# Export for easy importing
__all__ = [
    'ClientAuditComplianceManager',
    'ComplianceViolation',
    'AuditEvent',
    'ComplianceReport',
    'ComplianceViolationSeverity',
    'AuditEventType',
    'create_client_compliance_audit'
]
