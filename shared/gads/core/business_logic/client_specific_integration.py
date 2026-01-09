"""
Client-Specific Integration and Implementation Guide

This module provides a comprehensive integration of all client-specific components
for Google Ads management. It demonstrates how to implement client-specific plans
with proper isolation, security, and compliance.

Key Features:
- Complete client lifecycle management
- Multi-tenant operation isolation
- Automated compliance and audit trails
- Client-specific optimization and reporting
- Secure credential management
- Business rule enforcement
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

# Import all client-specific components
from client_config_schema import (
    ClientSpecificConfig,
    ClientStatus,
    IndustryType,
    create_default_client_config
)
from client_context_manager import get_context_manager, ClientContext
from client_auth_router import get_auth_router
from google_ads_client_business_rules import validate_client_operation, BusinessRuleValidator
from client_reporting_engine import ClientReportingEngine, generate_client_report
from client_isolation_middleware import get_middleware_instance, client_operation
from client_onboarding_workflow import (
    ClientOnboardingWorkflow,
    ClientOnboardingData,
    start_client_onboarding,
    get_onboarding_status
)
from client_optimization_engine import (
    ClientOptimizationEngine,
    generate_client_optimization
)
from client_audit_compliance import (
    ClientAuditComplianceManager,
    create_client_compliance_audit,
    AuditEventType
)

logger = logging.getLogger(__name__)


class ClientSpecificPlatform:
    """
    Complete client-specific Google Ads management platform

    This class integrates all client-specific components to provide:
    - Secure multi-tenant operations
    - Client-specific business logic
    - Automated compliance and auditing
    - Intelligent optimization and reporting
    - Complete client lifecycle management
    """

    def __init__(self, config_storage_path: Optional[Path] = None,
                 credential_storage_path: Optional[Path] = None,
                 audit_storage_path: Optional[Path] = None):
        """
        Initialize the client-specific platform

        Args:
            config_storage_path: Path for client configurations
            credential_storage_path: Path for encrypted credentials
            audit_storage_path: Path for audit and compliance data
        """
        self.config_storage_path = config_storage_path or Path("./client_configs")
        self.credential_storage_path = credential_storage_path or Path("./client_credentials")
        self.audit_storage_path = audit_storage_path or Path("./client_audit_data")

        # Initialize core components
        self.context_manager = get_context_manager()
        self.auth_router = get_auth_router(self.credential_storage_path)
        self.middleware = get_middleware_instance()

        # Component registries
        self.reporting_engines: Dict[str, ClientReportingEngine] = {}
        self.business_validators: Dict[str, BusinessRuleValidator] = {}
        self.optimization_engines: Dict[str, ClientOptimizationEngine] = {}
        self.compliance_managers: Dict[str, ClientAuditComplianceManager] = {}

        # Workflow managers
        self.onboarding_workflows: Dict[str, ClientOnboardingWorkflow] = {}

        logger.info("Initialized Client-Specific Platform")

    async def onboard_new_client(self, client_id: str, onboarding_data: ClientOnboardingData) -> Dict[str, Any]:
        """
        Start the complete client onboarding process

        Args:
            client_id: Unique client identifier
            onboarding_data: Client onboarding information

        Returns:
            Onboarding status and tracking information
        """
        try:
            logger.info(f"Starting onboarding for client {client_id}")

            # Initialize onboarding workflow
            workflow = ClientOnboardingWorkflow()
            self.onboarding_workflows[client_id] = workflow

            # Start onboarding
            tracking_id = await workflow.start_onboarding(client_id, onboarding_data)

            # Begin information gathering step
            success = await workflow.continue_onboarding(client_id, onboarding_data)

            if success:
                # Get initial status
                status = workflow.get_onboarding_status(client_id)

                # Log audit event
                await self._log_client_event(
                    client_id,
                    AuditEventType.OPERATION_EXECUTED,
                    f"Client onboarding initiated for {onboarding_data.client_name}",
                    metadata={"onboarding_data": onboarding_data.__dict__}
                )

                return {
                    "success": True,
                    "client_id": client_id,
                    "status": status,
                    "message": f"Client {onboarding_data.client_name} onboarding started successfully"
                }
            else:
                return {
                    "success": False,
                    "client_id": client_id,
                    "error": "Failed to start client onboarding"
                }

        except Exception as e:
            logger.error(f"Error onboarding client {client_id}: {e}")
            return {
                "success": False,
                "client_id": client_id,
                "error": str(e)
            }

    async def activate_client_account(self, client_id: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete client activation with credentials and final setup

        Args:
            client_id: Client identifier
            credentials: Client service credentials

        Returns:
            Activation status
        """
        try:
            # Get onboarding workflow
            workflow = self.onboarding_workflows.get(client_id)
            if not workflow:
                return {"success": False, "error": "No active onboarding found"}

            # Continue with credential collection
            success = await workflow.continue_onboarding(client_id, credentials)
            if not success:
                return {"success": False, "error": "Credential collection failed"}

            # Continue with remaining steps
            for step in ["business_rules_established", "integrations_configured", "testing_completed", "activated"]:
                success = await workflow.continue_onboarding(client_id)
                if not success:
                    status = workflow.get_onboarding_status(client_id)
                    return {
                        "success": False,
                        "error": f"Failed at step: {status.get('current_step', 'unknown')}"
                    }

            # Initialize client components
            await self._initialize_client_components(client_id)

            # Log activation
            await self._log_client_event(
                client_id,
                AuditEventType.OPERATION_EXECUTED,
                "Client account activated successfully",
                metadata={"activation_timestamp": "now"}
            )

            return {
                "success": True,
                "client_id": client_id,
                "message": "Client account activated successfully",
                "status": "active"
            }

        except Exception as e:
            logger.error(f"Error activating client {client_id}: {e}")
            return {"success": False, "client_id": client_id, "error": str(e)}

    async def _initialize_client_components(self, client_id: str):
        """Initialize all client-specific components after activation"""
        context = self.context_manager.get_client_context(client_id)
        if not context:
            raise ValueError(f"Client context not found for {client_id}")

        # Initialize reporting engine
        self.reporting_engines[client_id] = ClientReportingEngine(context.config)

        # Initialize business validator
        self.business_validators[client_id] = BusinessRuleValidator(context.config)

        # Initialize optimization engine
        self.optimization_engines[client_id] = ClientOptimizationEngine(context.config)

        # Initialize compliance manager
        self.compliance_managers[client_id] = create_client_compliance_audit(context.config, self.audit_storage_path)

        logger.info(f"Initialized all components for client {client_id}")

    async def execute_client_operation(self, client_id: str, operation_type: str,
                                     operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an operation within client context with full security and compliance

        Args:
            client_id: Client identifier
            operation_type: Type of operation to execute
            operation_data: Operation parameters

        Returns:
            Operation result with compliance and audit information
        """
        # Create middleware request
        from client_isolation_middleware import MiddlewareRequest

        request = MiddlewareRequest(
            client_id=client_id,
            operation=operation_type,
            parameters=operation_data
        )

        # Execute with middleware protection
        async with self.middleware.client_operation_context(request) as response:
            if not response.success:
                return {
                    "success": False,
                    "client_id": client_id,
                    "operation": operation_type,
                    "error": response.error,
                    "validation_results": [r.to_dict() for r in response.validation_results]
                }

            try:
                # Route to appropriate handler based on operation type
                result = await self._route_client_operation(client_id, operation_type, operation_data)

                response.data = result
                response.success = True

                return {
                    "success": True,
                    "client_id": client_id,
                    "operation": operation_type,
                    "result": result,
                    "processing_time_ms": response.processing_time_ms
                }

            except Exception as e:
                logger.error(f"Operation execution failed for client {client_id}: {e}")
                response.success = False
                response.error = str(e)

                return {
                    "success": False,
                    "client_id": client_id,
                    "operation": operation_type,
                    "error": str(e)
                }

    async def _route_client_operation(self, client_id: str, operation_type: str,
                                    operation_data: Dict[str, Any]) -> Any:
        """Route operation to appropriate handler"""
        if operation_type == "generate_report":
            return await self._generate_client_report(client_id, operation_data)
        elif operation_type == "optimize_campaign":
            return await self._optimize_client_campaigns(client_id, operation_data)
        elif operation_type == "validate_operation":
            return await self._validate_client_operation(client_id, operation_type, operation_data)
        elif operation_type == "get_compliance_status":
            return await self._get_client_compliance_status(client_id)
        else:
            # Generic operation - would integrate with Google Ads API
            return {"message": f"Operation {operation_type} executed for client {client_id}"}

    async def _generate_client_report(self, client_id: str, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a client-specific report"""
        engine = self.reporting_engines.get(client_id)
        if not engine:
            raise ValueError(f"Reporting engine not initialized for client {client_id}")

        performance_data = report_data.get("performance_data", {})
        date_range = report_data.get("date_range", (None, None))

        report = engine.generate_report(performance_data, date_range)

        # Convert to JSON-serializable format
        return {
            "report_id": f"{client_id}_{report.report_date.strftime('%Y%m%d')}",
            "client_name": report.client_name,
            "kpis": {name: {
                "value": kpi.value,
                "status": kpi.status,
                "target": kpi.target
            } for name, kpi in report.kpis.items()},
            "recommendations": report.recommendations,
            "sections": [{
                "title": section.title,
                "insights": section.insights
            } for section in report.sections]
        }

    async def _optimize_client_campaigns(self, client_id: str, optimization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimization recommendations for client"""
        engine = self.optimization_engines.get(client_id)
        if not engine:
            raise ValueError(f"Optimization engine not initialized for client {client_id}")

        performance_data = optimization_data.get("performance_data", {})
        campaign_data = optimization_data.get("campaign_data", {})

        recommendation = engine.analyze_performance_and_optimize(performance_data, campaign_data)

        return {
            "recommendation_id": f"opt_{client_id}_{recommendation.generated_at.strftime('%Y%m%d_%H%M')}",
            "opportunities_count": len(recommendation.opportunities),
            "priority_score": recommendation.priority_score,
            "opportunities": [{
                "action": opp.action_type.value,
                "priority": opp.priority.value,
                "description": opp.description,
                "confidence": opp.confidence_score,
                "expected_impact": opp.expected_impact
            } for opp in recommendation.opportunities[:5]]  # Top 5 opportunities
        }

    async def _validate_client_operation(self, client_id: str, operation_type: str,
                                       operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an operation against client business rules"""
        validator = self.business_validators.get(client_id)
        if not validator:
            raise ValueError(f"Business validator not initialized for client {client_id}")

        is_valid, validation_results = validator.validate_operation_pre_execution(
            operation_type, operation_data
        )

        return {
            "valid": is_valid,
            "validation_results": [r.to_dict() for r in validation_results],
            "blocking_issues": len([r for r in validation_results if not r.is_valid and r.severity.name in ["ERROR", "CRITICAL"]])
        }

    async def _get_client_compliance_status(self, client_id: str) -> Dict[str, Any]:
        """Get client compliance status"""
        compliance_manager = self.compliance_managers.get(client_id)
        if not compliance_manager:
            raise ValueError(f"Compliance manager not initialized for client {client_id}")

        report = compliance_manager.generate_compliance_report()

        return {
            "compliant": report.overall_compliant,
            "compliance_score": report.compliance_score,
            "violations_count": len(report.violations_found),
            "regulations_checked": report.regulations_checked,
            "recommendations": report.recommendations
        }

    async def _log_client_event(self, client_id: str, event_type: AuditEventType,
                              description: str, metadata: Optional[Dict[str, Any]] = None):
        """Log an audit event for a client"""
        compliance_manager = self.compliance_managers.get(client_id)
        if compliance_manager:
            compliance_manager.log_audit_event(
                event_type=event_type,
                description=description,
                metadata=metadata
            )

    async def get_client_status(self, client_id: str) -> Dict[str, Any]:
        """Get comprehensive client status"""
        context = self.context_manager.get_client_context(client_id)
        if not context:
            return {"error": f"Client {client_id} not found"}

        # Get onboarding status if applicable
        onboarding_status = None
        if client_id in self.onboarding_workflows:
            workflow = self.onboarding_workflows[client_id]
            onboarding_status = workflow.get_onboarding_status(client_id)

        # Get compliance status
        compliance_status = await self._get_client_compliance_status(client_id)

        return {
            "client_id": client_id,
            "client_name": context.config.client_name,
            "status": context.config.status.value,
            "industry": context.config.industry.value,
            "onboarding_status": onboarding_status,
            "compliance_status": compliance_status,
            "last_active": context.last_accessed.isoformat(),
            "account_manager": context.config.account_manager
        }

    async def list_active_clients(self) -> List[Dict[str, Any]]:
        """List all active clients with their status"""
        client_summaries = []

        for client_info in self.context_manager.list_active_clients():
            client_id = client_info["client_id"]

            # Get additional status information
            try:
                full_status = await self.get_client_status(client_id)
                client_summaries.append(full_status)
            except Exception as e:
                logger.error(f"Error getting status for client {client_id}: {e}")
                client_summaries.append(client_info)

        return client_summaries


# Example usage functions demonstrating the platform capabilities

async def example_client_onboarding():
    """Example of complete client onboarding process"""
    platform = ClientSpecificPlatform()

    # Sample client data
    onboarding_data = ClientOnboardingData(
        client_name="TechCorp Solutions",
        primary_email="billing@techcorp.com",
        cc_emails=["admin@techcorp.com"],
        industry=IndustryType.B2B_SERVICES,
        company_size="51-200",
        primary_goal="leads",
        target_kpis={"conversion_rate": 3.0, "cpl": 25.0},
        assigned_account_manager="sarah.johnson@agency.com"
    )

    # Start onboarding
    result = await platform.onboard_new_client("techcorp_001", onboarding_data)
    print(f"Onboarding started: {result}")

    # In real implementation, credentials would be collected securely
    sample_credentials = {
        "google_ads": {
            "account_id": "123-456-7890",
            "client_id": "sample_client_id",
            "client_secret": "sample_secret",
            "refresh_token": "sample_refresh_token",
            "developer_token": "sample_dev_token"
        },
        "airtable": {
            "api_key": "sample_airtable_key",
            "base_id": "sample_base_id"
        }
    }

    # Complete activation
    activation_result = await platform.activate_client_account("techcorp_001", sample_credentials)
    print(f"Activation completed: {activation_result}")

    return platform

async def example_client_operations():
    """Example of client operations after onboarding"""
    platform = await example_client_onboarding()

    client_id = "techcorp_001"

    # Example operations
    operations = [
        {
            "type": "generate_report",
            "data": {
                "performance_data": {
                    "impressions": 50000,
                    "clicks": 1500,
                    "conversions": 45,
                    "cost": 2250.00
                },
                "date_range": ["2024-01-01", "2024-01-31"]
            }
        },
        {
            "type": "optimize_campaign",
            "data": {
                "performance_data": {"campaigns": []},
                "campaign_data": {"campaign_id": "campaign_123"}
            }
        },
        {
            "type": "get_compliance_status",
            "data": {}
        }
    ]

    for op in operations:
        result = await platform.execute_client_operation(client_id, op["type"], op["data"])
        print(f"Operation {op['type']}: {'SUCCESS' if result['success'] else 'FAILED'}")
        if result["success"]:
            print(f"Result: {result.get('result', {})}")

async def example_compliance_reporting():
    """Example of compliance monitoring and reporting"""
    platform = await example_client_onboarding()

    # Get compliance status for all clients
    clients = await platform.list_active_clients()

    for client in clients:
        client_id = client["client_id"]
        compliance = await platform.execute_client_operation(
            client_id, "get_compliance_status", {}
        )

        if compliance["success"]:
            status = compliance["result"]
            print(f"Client {client_id} compliance: {status['compliance_score']:.2f}/1.0")
            if not status["compliant"]:
                print(f"Violations: {status['violations_count']}")


# Main demonstration function
async def demonstrate_client_specific_platform():
    """Complete demonstration of the client-specific platform"""
    print("🚀 Client-Specific Google Ads Platform Demonstration")
    print("=" * 60)

    try:
        # Example 1: Client Onboarding
        print("\n📋 Example 1: Client Onboarding")
        platform = await example_client_onboarding()

        # Example 2: Client Operations
        print("\n⚙️  Example 2: Client Operations")
        await example_client_operations()

        # Example 3: Compliance Monitoring
        print("\n🔒 Example 3: Compliance Monitoring")
        await example_compliance_reporting()

        print("\n✅ Client-Specific Platform demonstration completed successfully!")

    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run demonstration
    asyncio.run(demonstrate_client_specific_platform())
