"""
Client Onboarding Workflow Automation

This module provides comprehensive automation for client onboarding workflows,
including initial setup, configuration validation, credential collection,
and activation processes for new Google Ads clients.

Key Features:
- Multi-step onboarding workflow
- Automated validation and setup
- Credential collection automation
- Configuration initialization
- Progress tracking and notifications
- Rollback capabilities
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from client_config_schema import (
    ClientSpecificConfig,
    ClientStatus,
    IndustryType,
    create_default_client_config
)
from client_context_manager import get_context_manager
from client_auth_router import get_auth_router
from google_ads_client_business_rules import BusinessRuleValidator

logger = logging.getLogger(__name__)


class OnboardingStep(Enum):
    """Onboarding workflow steps"""
    INITIALIZED = "initialized"
    INFORMATION_GATHERED = "information_gathered"
    CONFIGURATION_VALIDATED = "configuration_validated"
    CREDENTIALS_COLLECTED = "credentials_collected"
    BUSINESS_RULES_ESTABLISHED = "business_rules_established"
    INTEGRATIONS_CONFIGURED = "integrations_configured"
    TESTING_COMPLETED = "testing_completed"
    ACTIVATED = "activated"


class OnboardingStatus(Enum):
    """Overall onboarding status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OnboardingProgress:
    """Tracks onboarding progress for a client"""
    client_id: str
    status: OnboardingStatus = OnboardingStatus.PENDING
    current_step: OnboardingStep = OnboardingStep.INITIALIZED
    completed_steps: List[OnboardingStep] = field(default_factory=list)
    failed_steps: List[Tuple[OnboardingStep, str]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    estimated_completion: Optional[datetime] = None
    assigned_agent: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    def mark_step_completed(self, step: OnboardingStep):
        """Mark a step as completed"""
        if step not in self.completed_steps:
            self.completed_steps.append(step)
        self.updated_at = datetime.now()

        # Update current step to next logical step
        step_order = list(OnboardingStep)
        current_index = step_order.index(step)
        if current_index + 1 < len(step_order):
            self.current_step = step_order[current_index + 1]

    def mark_step_failed(self, step: OnboardingStep, error: str):
        """Mark a step as failed"""
        self.failed_steps.append((step, error))
        self.status = OnboardingStatus.FAILED
        self.updated_at = datetime.now()
        logger.error(f"Onboarding step {step.value} failed for client {self.client_id}: {error}")

    def is_completed(self) -> bool:
        """Check if onboarding is completed"""
        return self.current_step == OnboardingStep.ACTIVATED and self.status == OnboardingStatus.COMPLETED

    def get_completion_percentage(self) -> float:
        """Get completion percentage"""
        total_steps = len(OnboardingStep)
        completed_count = len(self.completed_steps)
        return (completed_count / total_steps) * 100

    def add_note(self, note: str):
        """Add a progress note"""
        self.notes.append(f"{datetime.now().isoformat()}: {note}")
        self.updated_at = datetime.now()


@dataclass
class ClientOnboardingData:
    """Data collected during client onboarding"""
    # Basic client information
    client_name: str
    primary_email: str
    cc_emails: List[str] = field(default_factory=list)
    phone: Optional[str] = None
    website: Optional[str] = None

    # Business information
    industry: IndustryType = IndustryType.OTHER
    company_size: Optional[str] = None  # "1-10", "11-50", "51-200", "201-1000", "1000+"
    annual_revenue: Optional[str] = None
    target_market: Optional[str] = None

    # Google Ads information
    google_ads_account_id: str = ""
    current_ad_spend: Optional[str] = None  # "under_1k", "1k_5k", "5k_25k", "25k_100k", "over_100k"
    current_agency: Optional[str] = None

    # Goals and objectives
    primary_goal: str = "brand_awareness"  # conversions, leads, sales, brand_awareness, traffic
    secondary_goals: List[str] = field(default_factory=list)
    target_kpis: Dict[str, float] = field(default_factory=dict)

    # Operational preferences
    reporting_frequency: str = "weekly"
    communication_style: str = "professional"
    escalation_contacts: List[Dict[str, str]] = field(default_factory=list)

    # Account manager assignment
    assigned_account_manager: Optional[str] = None

    # Additional metadata
    referral_source: Optional[str] = None
    special_requirements: List[str] = field(default_factory=list)
    compliance_requirements: List[str] = field(default_factory=list)


class ClientOnboardingWorkflow:
    """
    Automated client onboarding workflow

    This workflow handles the complete process of setting up new clients
    with proper configuration, validation, and activation.
    """

    def __init__(self):
        self.context_manager = get_context_manager()
        self.auth_router = get_auth_router()

        # Onboarding progress tracking
        self.active_onboardings: Dict[str, OnboardingProgress] = {}

        # Workflow step handlers
        self.step_handlers = {
            OnboardingStep.INITIALIZED: self._handle_initialization,
            OnboardingStep.INFORMATION_GATHERED: self._handle_information_gathering,
            OnboardingStep.CONFIGURATION_VALIDATED: self._handle_configuration_validation,
            OnboardingStep.CREDENTIALS_COLLECTED: self._handle_credential_collection,
            OnboardingStep.BUSINESS_RULES_ESTABLISHED: self._handle_business_rules_setup,
            OnboardingStep.INTEGRATIONS_CONFIGURED: self._handle_integration_setup,
            OnboardingStep.TESTING_COMPLETED: self._handle_testing,
            OnboardingStep.ACTIVATED: self._handle_activation
        }

        logger.info("Initialized ClientOnboardingWorkflow")

    async def start_onboarding(self, client_id: str, initial_data: Optional[ClientOnboardingData] = None) -> str:
        """
        Start the onboarding process for a new client

        Args:
            client_id: Unique client identifier
            initial_data: Initial client data if available

        Returns:
            Onboarding tracking ID
        """
        if client_id in self.active_onboardings:
            raise ValueError(f"Onboarding already in progress for client {client_id}")

        # Create onboarding progress tracker
        progress = OnboardingProgress(client_id=client_id)
        self.active_onboardings[client_id] = progress

        # Start with initialization
        await self._execute_step(client_id, OnboardingStep.INITIALIZED, initial_data)

        logger.info(f"Started onboarding for client {client_id}")
        return client_id

    async def continue_onboarding(self, client_id: str, step_data: Any = None) -> bool:
        """
        Continue onboarding to the next step

        Args:
            client_id: Client identifier
            step_data: Data for the current step

        Returns:
            True if onboarding continued successfully
        """
        if client_id not in self.active_onboardings:
            raise ValueError(f"No active onboarding found for client {client_id}")

        progress = self.active_onboardings[client_id]

        if progress.is_completed():
            logger.info(f"Onboarding already completed for client {client_id}")
            return True

        if progress.status == OnboardingStatus.FAILED:
            raise ValueError(f"Onboarding failed for client {client_id}")

        # Execute current step
        success = await self._execute_step(client_id, progress.current_step, step_data)

        if success:
            progress.status = OnboardingStatus.IN_PROGRESS
            if progress.current_step == OnboardingStep.ACTIVATED:
                progress.status = OnboardingStatus.COMPLETED
        else:
            progress.status = OnboardingStatus.FAILED

        return success

    async def _execute_step(self, client_id: str, step: OnboardingStep, step_data: Any = None) -> bool:
        """
        Execute a specific onboarding step

        Args:
            client_id: Client identifier
            step: Step to execute
            step_data: Data for the step

        Returns:
            True if step completed successfully
        """
        progress = self.active_onboardings[client_id]

        try:
            logger.info(f"Executing onboarding step {step.value} for client {client_id}")

            # Get step handler
            handler = self.step_handlers.get(step)
            if not handler:
                raise ValueError(f"No handler found for step {step.value}")

            # Execute step
            success = await handler(client_id, step_data)

            if success:
                progress.mark_step_completed(step)
                progress.add_note(f"Completed step: {step.value}")
                logger.info(f"Successfully completed step {step.value} for client {client_id}")
            else:
                progress.mark_step_failed(step, "Step execution failed")
                logger.error(f"Failed to complete step {step.value} for client {client_id}")

            return success

        except Exception as e:
            error_msg = f"Step execution error: {str(e)}"
            progress.mark_step_failed(step, error_msg)
            logger.error(f"Error in step {step.value} for client {client_id}: {e}")
            return False

    async def _handle_initialization(self, client_id: str, data: Any = None) -> bool:
        """Handle onboarding initialization"""
        # Create initial client configuration
        initial_config = create_default_client_config(
            client_id=client_id,
            client_name=f"Client {client_id}",  # Placeholder, will be updated
            primary_email=f"contact@{client_id}.com",  # Placeholder
            google_ads_account_id="",  # Will be collected later
            account_manager="unassigned"  # Will be assigned later
        )

        # Set initial status
        initial_config.status = ClientStatus.ONBOARDING

        # Create client context
        context = self.context_manager.create_client_context(initial_config)

        # Initialize progress tracking
        progress = self.active_onboardings[client_id]
        progress.estimated_completion = datetime.now() + timedelta(days=7)  # 1 week estimate

        return True

    async def _handle_information_gathering(self, client_id: str, onboarding_data: ClientOnboardingData) -> bool:
        """Handle client information gathering"""
        if not isinstance(onboarding_data, ClientOnboardingData):
            raise ValueError("ClientOnboardingData required for information gathering step")

        # Update client configuration with gathered information
        context = self.context_manager.get_client_context(client_id)
        if not context:
            return False

        config = context.config

        # Update basic information
        config.client_name = onboarding_data.client_name
        config.primary_email = onboarding_data.primary_email
        config.cc_emails = onboarding_data.cc_emails
        config.industry = onboarding_data.industry

        # Generate MyExpertResume campaigns for resume clients
        # Check if this is a resume business (by name or industry)
        is_resume_business = (
            "resume" in onboarding_data.client_name.lower() or
            "cv" in onboarding_data.client_name.lower() or
            onboarding_data.industry == IndustryType.B2B_SERVICES
        )

        if is_resume_business:
            # Automatically generate MyExpertResume campaign suite for resume clients
            try:
                await self._generate_resume_campaigns(client_id, config)
                logger.info(f"Generated MyExpertResume campaign suite for client {client_id}")
            except Exception as e:
                logger.warning(f"Failed to generate campaigns for client {client_id}: {e}")
                # Don't fail onboarding if campaign generation fails

        # Set up initial KPIs based on goals
        if onboarding_data.primary_goal == "conversions":
            config.kpis.primary_metric = "conversions"
            config.kpis.target_values = {"conversion_rate": 3.0, "cpa": 50.0}
        elif onboarding_data.primary_goal == "leads":
            config.kpis.primary_metric = "conversions"
            config.kpis.target_values = {"conversion_rate": 2.5, "cpl": 25.0}

        # Set reporting preferences
        config.reporting.frequency = onboarding_data.reporting_frequency
        config.communication_preferences["communication_style"] = onboarding_data.communication_style

        # Assign account manager if provided
        if onboarding_data.assigned_account_manager:
            config.account_manager = onboarding_data.assigned_account_manager

        # Save updated configuration
        self.context_manager.save_client_config(config)

        return True

    async def _handle_configuration_validation(self, client_id: str, data: Any = None) -> bool:
        """Handle configuration validation"""
        context = self.context_manager.get_client_context(client_id)
        if not context:
            return False

        # Validate configuration
        validation_errors = context.config.validate_configuration()

        if validation_errors:
            logger.error(f"Configuration validation failed for client {client_id}: {validation_errors}")
            return False

        # Validate business rules
        validator = BusinessRuleValidator(context.config)
        # Test with sample campaign creation
        test_campaign = {
            "budget": 1000,
            "type": "search",
            "targeting": {"locations": ["United States"]}
        }

        results = validator.validate_campaign_creation(test_campaign)
        critical_errors = [r for r in results if not r.is_valid and r.severity.name == "CRITICAL"]

        if critical_errors:
            logger.error(f"Business rules validation failed for client {client_id}: {critical_errors}")
            return False

        return True

    async def _handle_credential_collection(self, client_id: str, credentials: Dict[str, Any]) -> bool:
        """Handle credential collection and storage"""
        # Store credentials securely
        for service, creds in credentials.items():
            success = await self.auth_router.store_client_credentials(client_id, service, creds)
            if not success:
                logger.error(f"Failed to store {service} credentials for client {client_id}")
                return False

        # Validate stored credentials
        for service in credentials.keys():
            is_valid, error = await self.auth_router.validate_credentials(client_id, service)
            if not is_valid:
                logger.error(f"Credential validation failed for {service}, client {client_id}: {error}")
                return False

        # Update client configuration with account ID if Google Ads credentials provided
        if "google_ads" in credentials:
            context = self.context_manager.get_client_context(client_id)
            if context and "account_id" in credentials["google_ads"]:
                context.config.google_ads_account_id = credentials["google_ads"]["account_id"]
                self.context_manager.save_client_config(context.config)

        return True

    async def _handle_business_rules_setup(self, client_id: str, rules_data: Dict[str, Any]) -> bool:
        """Handle business rules establishment"""
        context = self.context_manager.get_client_context(client_id)
        if not context:
            return False

        config = context.config

        # Apply business rules from onboarding data
        if "budget_limits" in rules_data:
            config.business_rules.budget_limits = rules_data["budget_limits"]

        if "targeting_restrictions" in rules_data:
            config.business_rules.targeting_restrictions = rules_data["targeting_restrictions"]

        if "keyword_restrictions" in rules_data:
            config.business_rules.keyword_restrictions = rules_data["keyword_restrictions"]

        # Set up industry-specific rules
        if config.industry == IndustryType.HEALTHCARE:
            config.business_rules.keyword_restrictions.extend([
                "treatment", "cure", "therapy", "medical advice"
            ])
            config.compliance.industry_regulations = ["HIPAA", "FDA Advertising Guidelines"]

        elif config.industry == IndustryType.FINANCE:
            config.business_rules.keyword_restrictions.extend([
                "guaranteed returns", "risk-free", "bankruptcy"
            ])
            config.compliance.industry_regulations = ["SEC Regulations", "FINRA Guidelines"]

        # Save updated configuration
        self.context_manager.save_client_config(config)

        return True

    async def _generate_resume_campaigns(self, client_id: str, config: ClientSpecificConfig):
        """Generate MyExpertResume campaign suite for resume services clients"""
        # Import the existing working campaign generation system
        import subprocess
        import os
        from pathlib import Path

        # Path to the existing campaign generation tool
        campaign_tool_path = Path(__file__).parent.parent.parent / "tools" / "campaign" / "campaign_plan.py"

        if not campaign_tool_path.exists():
            raise FileNotFoundError(f"Campaign generation tool not found: {campaign_tool_path}")

        # Run the existing campaign generation script
        # This will generate the CSV files in the campaigns directory
        try:
            result = subprocess.run(
                ["python3", str(campaign_tool_path)],
                cwd=campaign_tool_path.parent,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                raise RuntimeError(f"Campaign generation failed: {result.stderr}")

            logger.info(f"Campaign generation completed for client {client_id}")
            logger.debug(f"Campaign generation output: {result.stdout}")

            # Store campaign generation info in client config
            config.custom_fields["campaigns_generated"] = True
            config.custom_fields["campaign_generation_date"] = datetime.now().isoformat()
            config.custom_fields["generated_campaigns"] = [
                "MyExpertResume National Executive",
                "MyExpertResume Florida Executive"
            ]

            # Save the updated config
            self.context_manager.save_client_config(config)

        except subprocess.TimeoutExpired:
            raise RuntimeError("Campaign generation timed out")
        except Exception as e:
            logger.error(f"Error generating campaigns for client {client_id}: {e}")
            raise

    async def _handle_integration_setup(self, client_id: str, integration_data: Dict[str, Any]) -> bool:
        """Handle integration configuration"""
        context = self.context_manager.get_client_context(client_id)
        if not context:
            return False

        config = context.config

        # Configure integrations
        if "airtable" in integration_data:
            config.integrations["crm_system"] = "airtable"
            # Store Airtable credentials
            await self.auth_router.store_client_credentials(
                client_id, "airtable", integration_data["airtable"]
            )

        if "analytics" in integration_data:
            config.integrations["analytics_platform"] = integration_data["analytics"]

        if "webhooks" in integration_data:
            config.integrations["webhook_endpoints"] = integration_data["webhooks"]

        # Save updated configuration
        self.context_manager.save_client_config(config)

        return True

    async def _handle_testing(self, client_id: str, test_data: Any = None) -> bool:
        """Handle testing and validation"""
        context = self.context_manager.get_client_context(client_id)
        if not context:
            return False

        # Test credential access
        credentials_valid = True
        services_to_test = ["google_ads", "airtable"]

        for service in services_to_test:
            is_valid, error = await self.auth_router.validate_credentials(client_id, service)
            if not is_valid:
                logger.error(f"Testing failed: {service} credentials invalid for client {client_id}: {error}")
                credentials_valid = False

        if not credentials_valid:
            return False

        # Test configuration validation
        validation_errors = context.config.validate_configuration()
        if validation_errors:
            logger.error(f"Testing failed: Configuration validation errors for client {client_id}: {validation_errors}")
            return False

        return True

    async def _handle_activation(self, client_id: str, activation_data: Any = None) -> bool:
        """Handle final activation"""
        context = self.context_manager.get_client_context(client_id)
        if not context:
            return False

        # Update client status to active
        context.config.status = ClientStatus.ACTIVE
        context.config.updated_at = datetime.now()

        # Save final configuration
        self.context_manager.save_client_config(context.config)

        # Clean up onboarding progress
        if client_id in self.active_onboardings:
            progress = self.active_onboardings[client_id]
            progress.status = OnboardingStatus.COMPLETED
            progress.add_note("Client successfully activated")

        logger.info(f"Successfully activated client {client_id}")
        return True

    def get_onboarding_status(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get onboarding status for a client"""
        if client_id not in self.active_onboardings:
            return None

        progress = self.active_onboardings[client_id]

        return {
            "client_id": client_id,
            "status": progress.status.value,
            "current_step": progress.current_step.value,
            "completed_steps": [step.value for step in progress.completed_steps],
            "failed_steps": [(step.value, error) for step, error in progress.failed_steps],
            "completion_percentage": progress.get_completion_percentage(),
            "created_at": progress.created_at.isoformat(),
            "updated_at": progress.updated_at.isoformat(),
            "estimated_completion": progress.estimated_completion.isoformat() if progress.estimated_completion else None,
            "assigned_agent": progress.assigned_agent,
            "recent_notes": progress.notes[-5:]  # Last 5 notes
        }

    def list_active_onboardings(self) -> List[Dict[str, Any]]:
        """List all active onboarding processes"""
        return [
            self.get_onboarding_status(client_id)
            for client_id in self.active_onboardings.keys()
        ]

    async def cancel_onboarding(self, client_id: str, reason: str) -> bool:
        """Cancel an onboarding process"""
        if client_id not in self.active_onboardings:
            return False

        progress = self.active_onboardings[client_id]
        progress.status = OnboardingStatus.CANCELLED
        progress.add_note(f"Onboarding cancelled: {reason}")

        # Clean up resources
        self.context_manager.remove_client_context(client_id)

        logger.info(f"Cancelled onboarding for client {client_id}: {reason}")
        return True


# Convenience functions for easy access
async def start_client_onboarding(client_id: str, initial_data: Optional[ClientOnboardingData] = None) -> str:
    """Start onboarding for a new client"""
    workflow = ClientOnboardingWorkflow()
    return await workflow.start_onboarding(client_id, initial_data)

async def get_onboarding_status(client_id: str) -> Optional[Dict[str, Any]]:
    """Get onboarding status"""
    workflow = ClientOnboardingWorkflow()
    return workflow.get_onboarding_status(client_id)

# Export for easy importing
__all__ = [
    'ClientOnboardingWorkflow',
    'ClientOnboardingData',
    'OnboardingProgress',
    'OnboardingStep',
    'OnboardingStatus',
    'start_client_onboarding',
    'get_onboarding_status'
]
