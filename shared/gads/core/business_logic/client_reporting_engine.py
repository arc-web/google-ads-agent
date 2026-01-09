"""
Client-Specific Reporting Engine and KPI Templates

This module provides customizable reporting templates and KPI calculations
tailored to each client's specific requirements and industry. It generates
reports that align with client-specific metrics and presentation preferences.

Key Features:
- Client-specific KPI calculations
- Custom reporting templates
- Industry-tailored metrics
- Automated report generation
- Performance insights and recommendations
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from client_config_schema import (
    ClientSpecificConfig,
    ClientKPIs,
    ReportingPreferences,
    IndustryType
)

logger = logging.getLogger(__name__)


class ReportFormat(Enum):
    """Supported report formats"""
    SUMMARY = "summary"
    DETAILED = "detailed"
    EXECUTIVE = "executive"
    CUSTOM = "custom"


class MetricCategory(Enum):
    """Categories of performance metrics"""
    PERFORMANCE = "performance"
    EFFICIENCY = "efficiency"
    FINANCIAL = "financial"
    CONVERSION = "conversion"
    AUDIENCE = "audience"


@dataclass
class MetricDefinition:
    """Definition of a performance metric"""
    name: str
    display_name: str
    category: MetricCategory
    calculation: str  # Formula or method to calculate
    unit: str
    description: str
    benchmark_range: Optional[Tuple[float, float]] = None  # (min, max) good range
    higher_is_better: bool = True
    industry_specific: bool = False


@dataclass
class KPIResult:
    """Result of a KPI calculation"""
    name: str
    value: float
    target: Optional[float] = None
    status: str = "normal"  # normal, above_target, below_target, critical
    trend: Optional[str] = None  # improving, declining, stable
    previous_value: Optional[float] = None
    change_percentage: Optional[float] = None

    def calculate_status(self):
        """Calculate KPI status based on target and value"""
        if self.target is None:
            self.status = "normal"
            return

        if self.target > 0:  # Higher values are better
            if self.value >= self.target * 1.1:  # 10% above target
                self.status = "above_target"
            elif self.value < self.target * 0.9:  # 10% below target
                self.status = "below_target"
            else:
                self.status = "on_target"
        else:  # Lower values are better (costs)
            if self.value <= abs(self.target) * 0.9:  # 10% below target
                self.status = "above_target"
            elif self.value > abs(self.target) * 1.1:  # 10% above target
                self.status = "below_target"
            else:
                self.status = "on_target"

        # Calculate trend if previous value available
        if self.previous_value is not None:
            change = ((self.value - self.previous_value) / abs(self.previous_value)) * 100
            self.change_percentage = change
            if change > 5:
                self.trend = "improving"
            elif change < -5:
                self.trend = "declining"
            else:
                self.trend = "stable"


@dataclass
class ReportSection:
    """A section within a report"""
    title: str
    content_type: str  # text, chart, table, metric
    data: Any
    priority: int = 1  # 1=high, 2=medium, 3=low
    insights: List[str] = field(default_factory=list)


@dataclass
class ClientReport:
    """Complete client report"""
    client_id: str
    client_name: str
    report_date: datetime
    date_range: Tuple[datetime, datetime]
    format: ReportFormat
    sections: List[ReportSection] = field(default_factory=list)
    kpis: Dict[str, KPIResult] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ClientReportingEngine:
    """
    Generates client-specific reports with tailored KPIs and insights

    This engine provides:
    - Client-specific KPI calculations
    - Industry-tailored reporting templates
    - Automated performance insights
    - Custom metric definitions
    - Report generation and formatting
    """

    def __init__(self, client_config: ClientSpecificConfig):
        self.config = client_config
        self.industry = client_config.industry
        self.kpi_config = client_config.kpis
        self.reporting_config = client_config.reporting

        # Initialize metric definitions
        self.metric_definitions = self._load_metric_definitions()

        # Load industry-specific templates
        self.templates = self._load_industry_templates()

    def _load_metric_definitions(self) -> Dict[str, MetricDefinition]:
        """Load standard and industry-specific metric definitions"""
        definitions = {
            # Standard Google Ads metrics
            "impressions": MetricDefinition(
                name="impressions",
                display_name="Impressions",
                category=MetricCategory.AUDIENCE,
                calculation="raw",
                unit="count",
                description="Number of times ads were shown"
            ),
            "clicks": MetricDefinition(
                name="clicks",
                display_name="Clicks",
                category=MetricCategory.PERFORMANCE,
                calculation="raw",
                unit="count",
                description="Number of clicks on ads"
            ),
            "ctr": MetricDefinition(
                name="ctr",
                display_name="Click-Through Rate",
                category=MetricCategory.PERFORMANCE,
                calculation="clicks/impressions*100",
                unit="percentage",
                description="Percentage of impressions that resulted in clicks",
                benchmark_range=(1.0, 3.0)
            ),
            "cpc": MetricDefinition(
                name="cpc",
                display_name="Cost Per Click",
                category=MetricCategory.FINANCIAL,
                calculation="cost/clicks",
                unit="currency",
                description="Average cost per click",
                higher_is_better=False
            ),
            "conversions": MetricDefinition(
                name="conversions",
                display_name="Conversions",
                category=MetricCategory.CONVERSION,
                calculation="raw",
                unit="count",
                description="Number of conversion actions completed"
            ),
            "conversion_rate": MetricDefinition(
                name="conversion_rate",
                display_name="Conversion Rate",
                category=MetricCategory.CONVERSION,
                calculation="conversions/clicks*100",
                unit="percentage",
                description="Percentage of clicks that resulted in conversions",
                benchmark_range=(2.0, 5.0)
            ),
            "cpa": MetricDefinition(
                name="cpa",
                display_name="Cost Per Acquisition",
                category=MetricCategory.FINANCIAL,
                calculation="cost/conversions",
                unit="currency",
                description="Average cost per conversion",
                higher_is_better=False
            ),
            "roas": MetricDefinition(
                name="roas",
                display_name="Return on Ad Spend",
                category=MetricCategory.FINANCIAL,
                calculation="conversion_value/cost",
                unit="ratio",
                description="Revenue generated per dollar spent on ads",
                benchmark_range=(3.0, 5.0)
            )
        }

        # Add industry-specific metrics
        if self.industry == IndustryType.HEALTHCARE:
            definitions.update({
                "patient_acquisition_cost": MetricDefinition(
                    name="patient_acquisition_cost",
                    display_name="Patient Acquisition Cost",
                    category=MetricCategory.FINANCIAL,
                    calculation="cost/conversions",
                    unit="currency",
                    description="Cost to acquire a new patient",
                    industry_specific=True,
                    higher_is_better=False
                )
            })
        elif self.industry == IndustryType.EDUCATION:
            definitions.update({
                "student_inquiry_rate": MetricDefinition(
                    name="student_inquiry_rate",
                    display_name="Student Inquiry Rate",
                    category=MetricCategory.CONVERSION,
                    calculation="inquiries/clicks*100",
                    unit="percentage",
                    description="Percentage of clicks resulting in student inquiries",
                    industry_specific=True,
                    benchmark_range=(1.0, 3.0)
                )
            })

        # Add custom KPIs from client config
        for custom_kpi_name, custom_kpi_config in self.kpi_config.custom_kpis.items():
            definitions[custom_kpi_name] = MetricDefinition(
                name=custom_kpi_name,
                display_name=custom_kpi_config.get('display_name', custom_kpi_name),
                category=MetricCategory(custom_kpi_config.get('category', 'performance')),
                calculation=custom_kpi_config.get('calculation', 'raw'),
                unit=custom_kpi_config.get('unit', 'count'),
                description=custom_kpi_config.get('description', ''),
                benchmark_range=custom_kpi_config.get('benchmark_range'),
                higher_is_better=custom_kpi_config.get('higher_is_better', True),
                industry_specific=True
            )

        return definitions

    def _load_industry_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load industry-specific report templates"""
        templates = {
            "ecommerce": {
                "primary_kpis": ["roas", "conversion_rate", "cpa"],
                "sections": ["performance_summary", "product_performance", "audience_insights"],
                "insights": [
                    "Focus on high-ROAS products",
                    "Optimize for mobile conversion rates",
                    "Consider retargeting campaigns"
                ]
            },
            "b2b_services": {
                "primary_kpis": ["conversion_rate", "cpl", "lead_quality"],
                "sections": ["lead_generation", "account_based_marketing", "content_performance"],
                "insights": [
                    "Prioritize decision-maker targeting",
                    "Focus on long-tail keywords",
                    "Implement lead nurturing workflows"
                ]
            },
            "healthcare": {
                "primary_kpis": ["patient_acquisition_cost", "conversion_rate", "appointment_rate"],
                "sections": ["patient_acquisition", "service_line_performance", "compliance_metrics"],
                "insights": [
                    "Ensure HIPAA compliance in messaging",
                    "Focus on local search optimization",
                    "Consider patient journey mapping"
                ]
            },
            "default": {
                "primary_kpis": ["ctr", "conversion_rate", "cpa"],
                "sections": ["performance_overview", "campaign_analysis", "recommendations"],
                "insights": [
                    "Monitor campaign performance regularly",
                    "Optimize for quality score improvements",
                    "Test different ad creatives"
                ]
            }
        }

        return templates

    def calculate_kpis(self, raw_data: Dict[str, Any],
                       previous_period_data: Optional[Dict[str, Any]] = None) -> Dict[str, KPIResult]:
        """
        Calculate KPIs based on raw performance data

        Args:
            raw_data: Raw Google Ads performance data
            previous_period_data: Data from previous period for trend analysis

        Returns:
            Dictionary of calculated KPI results
        """
        kpi_results = {}

        # Calculate standard metrics
        for metric_name, definition in self.metric_definitions.items():
            if metric_name in raw_data:
                value = raw_data[metric_name]
                target = self.kpi_config.target_values.get(metric_name)

                # Get previous value for trend
                previous_value = None
                if previous_period_data and metric_name in previous_period_data:
                    previous_value = previous_period_data[metric_name]

                kpi_result = KPIResult(
                    name=metric_name,
                    value=value,
                    target=target,
                    previous_value=previous_value
                )
                kpi_result.calculate_status()

                kpi_results[metric_name] = kpi_result

        # Calculate derived metrics
        if 'clicks' in raw_data and 'impressions' in raw_data and raw_data['impressions'] > 0:
            ctr_value = (raw_data['clicks'] / raw_data['impressions']) * 100
            kpi_results['ctr'] = KPIResult(
                name='ctr',
                value=ctr_value,
                target=self.kpi_config.target_values.get('ctr')
            )
            kpi_results['ctr'].calculate_status()

        if 'cost' in raw_data and 'clicks' in raw_data and raw_data['clicks'] > 0:
            cpc_value = raw_data['cost'] / raw_data['clicks']
            kpi_results['cpc'] = KPIResult(
                name='cpc',
                value=cpc_value,
                target=self.kpi_config.target_values.get('cpc')
            )
            kpi_results['cpc'].calculate_status()

        if 'conversions' in raw_data and 'clicks' in raw_data and raw_data['clicks'] > 0:
            conv_rate_value = (raw_data['conversions'] / raw_data['clicks']) * 100
            kpi_results['conversion_rate'] = KPIResult(
                name='conversion_rate',
                value=conv_rate_value,
                target=self.kpi_config.target_values.get('conversion_rate')
            )
            kpi_results['conversion_rate'].calculate_status()

        return kpi_results

    def generate_report(self, performance_data: Dict[str, Any],
                       date_range: Tuple[datetime, datetime],
                       previous_period_data: Optional[Dict[str, Any]] = None) -> ClientReport:
        """
        Generate a complete client report

        Args:
            performance_data: Raw performance data
            date_range: (start_date, end_date) for the report
            previous_period_data: Previous period data for comparisons

        Returns:
            Complete client report
        """
        # Calculate KPIs
        kpis = self.calculate_kpis(performance_data, previous_period_data)

        # Create report
        report = ClientReport(
            client_id=self.config.client_id,
            client_name=self.config.client_name,
            report_date=datetime.now(),
            date_range=date_range,
            format=ReportFormat(self.reporting_config.format)
        )

        # Add KPIs to report
        report.kpis = kpis

        # Generate report sections based on template
        template = self.templates.get(self.industry.value.lower(),
                                    self.templates["default"])

        # Add performance summary section
        report.sections.append(self._generate_performance_summary(kpis))

        # Add industry-specific sections
        for section_name in template["sections"]:
            section = self._generate_section(section_name, performance_data, kpis)
            if section:
                report.sections.append(section)

        # Add recommendations
        report.recommendations = self._generate_recommendations(kpis, template)

        # Add metadata
        report.metadata = {
            "industry": self.industry.value,
            "account_manager": self.config.account_manager,
            "report_format": self.reporting_config.format,
            "kpi_targets_configured": len(self.kpi_config.target_values),
            "custom_kpis": list(self.kpi_config.custom_kpis.keys())
        }

        return report

    def _generate_performance_summary(self, kpis: Dict[str, KPIResult]) -> ReportSection:
        """Generate performance summary section"""
        summary_data = {
            "total_kpis": len(kpis),
            "on_target_kpis": len([k for k in kpis.values() if k.status == "on_target"]),
            "above_target_kpis": len([k for k in kpis.values() if k.status == "above_target"]),
            "below_target_kpis": len([k for k in kpis.values() if k.status == "below_target"]),
            "improving_kpis": len([k for k in kpis.values() if k.trend == "improving"]),
            "declining_kpis": len([k for k in kpis.values() if k.trend == "declining"])
        }

        insights = []
        if summary_data["below_target_kpis"] > 0:
            insights.append(f"{summary_data['below_target_kpis']} KPIs are below target - optimization needed")
        if summary_data["improving_kpis"] > 0:
            insights.append(f"{summary_data['improving_kpis']} KPIs showing improvement")

        return ReportSection(
            title="Performance Summary",
            content_type="summary",
            data=summary_data,
            insights=insights
        )

    def _generate_section(self, section_name: str, performance_data: Dict[str, Any],
                         kpis: Dict[str, KPIResult]) -> Optional[ReportSection]:
        """Generate a specific report section"""

        if section_name == "performance_overview":
            return ReportSection(
                title="Performance Overview",
                content_type="metrics_table",
                data={
                    "primary_kpis": {name: kpi.value for name, kpi in kpis.items()
                                   if name in self.kpi_config.primary_metric or
                                      name in self.kpi_config.secondary_metrics[:3]},
                    "trends": {name: kpi.trend for name, kpi in kpis.items() if kpi.trend}
                }
            )

        elif section_name == "campaign_analysis":
            # Mock campaign breakdown
            return ReportSection(
                title="Campaign Analysis",
                content_type="table",
                data={
                    "campaigns": performance_data.get("campaigns", []),
                    "top_performing": "Based on ROAS",
                    "needs_attention": "Based on CPA"
                }
            )

        elif section_name == "audience_insights":
            return ReportSection(
                title="Audience Insights",
                content_type="chart",
                data={
                    "demographics": performance_data.get("audience_demographics", {}),
                    "interests": performance_data.get("audience_interests", []),
                    "recommendations": ["Expand to similar interests", "Test lookalike audiences"]
                }
            )

        return None

    def _generate_recommendations(self, kpis: Dict[str, KPIResult],
                                template: Dict[str, Any]) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = template.get("insights", []).copy()

        # Add KPI-specific recommendations
        for name, kpi in kpis.items():
            if kpi.status == "below_target":
                metric_def = self.metric_definitions.get(name)
                if metric_def:
                    if name == "ctr":
                        recommendations.append("Improve ad relevance and targeting to increase CTR")
                    elif name == "cpa":
                        recommendations.append("Review bidding strategy and negative keywords to reduce CPA")
                    elif name == "conversion_rate":
                        recommendations.append("Optimize landing pages and call-to-action for better conversion rates")

            if kpi.trend == "declining":
                recommendations.append(f"Address declining {name} trend immediately")

        # Add industry-specific recommendations
        if self.industry == IndustryType.HEALTHCARE:
            recommendations.extend([
                "Ensure all ad content complies with healthcare advertising regulations",
                "Consider implementing patient acquisition cost tracking"
            ])
        elif self.industry == IndustryType.EDUCATION:
            recommendations.extend([
                "Focus on academic calendar timing for campaigns",
                "Target parents and students with relevant messaging"
            ])

        return list(set(recommendations))  # Remove duplicates

    def export_report(self, report: ClientReport, format_type: str = "json") -> str:
        """
        Export report in specified format

        Args:
            report: Client report to export
            format_type: Export format (json, html, pdf)

        Returns:
            Formatted report content
        """
        if format_type == "json":
            return self._export_json(report)
        elif format_type == "html":
            return self._export_html(report)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    def _export_json(self, report: ClientReport) -> str:
        """Export report as JSON"""
        report_data = {
            "client_id": report.client_id,
            "client_name": report.client_name,
            "report_date": report.report_date.isoformat(),
            "date_range": [d.isoformat() for d in report.date_range],
            "format": report.format.value,
            "kpis": {name: {
                "value": kpi.value,
                "target": kpi.target,
                "status": kpi.status,
                "trend": kpi.trend,
                "change_percentage": kpi.change_percentage
            } for name, kpi in report.kpis.items()},
            "sections": [{
                "title": section.title,
                "content_type": section.content_type,
                "data": section.data,
                "insights": section.insights
            } for section in report.sections],
            "recommendations": report.recommendations,
            "metadata": report.metadata
        }
        return json.dumps(report_data, indent=2)

    def _export_html(self, report: ClientReport) -> str:
        """Export report as HTML"""
        html = f"""
        <html>
        <head>
            <title>Performance Report - {report.client_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .kpi {{ display: inline-block; margin: 10px; padding: 15px; background: #e8f4fd; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .recommendations {{ background: #fff3cd; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Performance Report</h1>
                <h2>{report.client_name}</h2>
                <p>Report Date: {report.report_date.strftime('%Y-%m-%d')}</p>
                <p>Period: {report.date_range[0].strftime('%Y-%m-%d')} to {report.date_range[1].strftime('%Y-%m-%d')}</p>
            </div>

            <div class="section">
                <h3>Key Performance Indicators</h3>
                {"".join(f'<div class="kpi"><strong>{name}</strong><br/>{kpi.value:.2f}<br/><small>{kpi.status}</small></div>'
                        for name, kpi in report.kpis.items())}
            </div>

            {"".join(f'<div class="section"><h3>{section.title}</h3><p>{section.insights[0] if section.insights else "No insights available"}</p></div>'
                    for section in report.sections)}

            <div class="recommendations">
                <h3>Recommendations</h3>
                <ul>
                    {"".join(f"<li>{rec}</li>" for rec in report.recommendations)}
                </ul>
            </div>
        </body>
        </html>
        """
        return html


def generate_client_report(client_config: ClientSpecificConfig,
                          performance_data: Dict[str, Any],
                          date_range: Tuple[datetime, datetime],
                          previous_period_data: Optional[Dict[str, Any]] = None) -> ClientReport:
    """
    Convenience function to generate a client report

    Args:
        client_config: Client-specific configuration
        performance_data: Raw performance data
        date_range: Date range for the report
        previous_period_data: Previous period data for comparisons

    Returns:
        Complete client report
    """
    engine = ClientReportingEngine(client_config)
    return engine.generate_report(performance_data, date_range, previous_period_data)


# Export for easy importing
__all__ = [
    'ClientReportingEngine',
    'ClientReport',
    'ReportSection',
    'KPIResult',
    'MetricDefinition',
    'ReportFormat',
    'MetricCategory',
    'generate_client_report'
]
