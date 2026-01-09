#!/usr/bin/env python3
"""
Performance Report Generator

CLI tool that generates client performance reports from Google Ads data
using the existing email template system.

Usage:
    python performance_report_generator.py <client_name> --start-date YYYY-MM-DD --end-date YYYY-MM-DD
    python performance_report_generator.py collabmedspa --start-date 2025-11-01 --end-date 2025-11-20
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path to import email_generator
sys.path.insert(0, str(Path(__file__).parent.parent / "email_templates"))
from email_generator import EmailTemplateGenerator


class PerformanceReportGenerator:
    """Generate performance reports for clients from Google Ads data."""

    def __init__(self, client_name: str):
        """
        Initialize the report generator.

        Args:
            client_name: Name of the client (directory name in client folder)
        """
        self.client_name = client_name
        self.base_path = Path(__file__).parent.parent.parent / "client" / client_name
        self.communication_path = self.base_path / "communication"
        self.profile_path = self.base_path / "profile.json"
        
        # Ensure communication directory exists
        self.communication_path.mkdir(parents=True, exist_ok=True)

    def load_client_profile(self) -> Dict[str, Any]:
        """
        Load client profile from profile.json.

        Returns:
            Dictionary containing client profile data
        """
        if not self.profile_path.exists():
            raise FileNotFoundError(
                f"Client profile not found: {self.profile_path}\n"
                f"Expected client directory: {self.base_path}"
            )

        with open(self.profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def fetch_google_ads_metrics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Fetch Google Ads metrics for the specified date range.

        NOTE: This is a placeholder implementation. In production, this would
        integrate with Google Ads API or MCP server to fetch real data.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            Dictionary containing Google Ads metrics
        """
        # TODO: Integrate with Google Ads API or MCP server
        # For now, return placeholder data structure
        return {
            "conversions": 0,
            "cost_per_conversion": 0.0,
            "clicks": 0,
            "clickthrough_rate": 0.0,
            "impressions": 0,
            "cost": 0.0,
            "campaigns": []
        }

    def generate_narrative(self, metrics: Dict[str, Any], profile: Dict[str, Any]) -> str:
        """
        Generate performance narrative from metrics.

        Args:
            metrics: Google Ads metrics dictionary
            profile: Client profile dictionary

        Returns:
            Narrative text describing performance
        """
        narrative_parts = []

        if metrics.get("conversions", 0) > 0:
            narrative_parts.append(
                f"Generated {metrics['conversions']} conversions during this period."
            )

        if metrics.get("cost_per_conversion", 0) > 0:
            narrative_parts.append(
                f"Average cost per conversion: ${metrics['cost_per_conversion']:.2f}."
            )

        if metrics.get("clickthrough_rate", 0) > 0:
            narrative_parts.append(
                f"Click-through rate: {metrics['clickthrough_rate']:.2f}%."
            )

        if not narrative_parts:
            narrative_parts.append(
                "Performance data will be populated when Google Ads integration is complete."
            )

        return " ".join(narrative_parts)

    def generate_email_data(
        self,
        profile: Dict[str, Any],
        metrics: Dict[str, Any],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Generate email template data from client profile and metrics.

        Args:
            profile: Client profile dictionary
            metrics: Google Ads metrics dictionary
            start_date: Start date string
            end_date: End date string

        Returns:
            Dictionary formatted for email template
        """
        # Format date range for display
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        date_range = f"{start_dt.strftime('%B %d').upper()} - {end_dt.strftime('%B %d').upper()}"

        # Get client name from profile
        client_name = profile.get("business_info", {}).get("business_name", self.client_name)
        if not client_name or client_name == "Unknown":
            client_name = self.client_name.replace("_", " ").title()

        # Build email data structure
        email_data = {
            "BRAND_NAME": "Google Ads",
            "CUSTOMER_ID": self.client_name,
            "DATE_RANGE": date_range,
            "CLIENT_NAME": client_name,
            "overview_metrics": {
                "METRIC_1_LABEL": "Conversions",
                "METRIC_1_VALUE": str(metrics.get("conversions", 0)),
                "METRIC_1_CHANGE": "vs previous period",
                "METRIC_1_DIRECTION": "positive" if metrics.get("conversions", 0) > 0 else "negative",
                "METRIC_2_LABEL": "Cost per conversion",
                "METRIC_2_VALUE": f"${metrics.get('cost_per_conversion', 0):.2f}",
                "METRIC_2_CHANGE": "vs previous period",
                "METRIC_2_DIRECTION": "positive" if metrics.get("cost_per_conversion", 0) > 0 else "negative",
                "METRIC_3_LABEL": "Clicks",
                "METRIC_3_VALUE": str(metrics.get("clicks", 0)),
                "METRIC_3_CHANGE": "vs previous period",
                "METRIC_3_DIRECTION": "positive" if metrics.get("clicks", 0) > 0 else "negative",
                "METRIC_4_LABEL": "Clickthrough rate",
                "METRIC_4_VALUE": f"{metrics.get('clickthrough_rate', 0):.2f}%",
                "METRIC_4_CHANGE": "vs previous period",
                "METRIC_4_DIRECTION": "positive" if metrics.get("clickthrough_rate", 0) > 0 else "negative"
            },
            "call_to_action": {
                "CTA_BADGE": "PERFORMANCE UPDATE",
                "CTA_HEADING": "Review Your Campaign Performance",
                "CTA_DESCRIPTION": "See detailed insights and recommendations in your full performance report.",
                "CTA_BUTTON_TEXT": "View Full Report",
                "CTA_LINK": f"mailto:?subject={client_name}%20Performance%20Report"
            },
            "campaign_summary": {
                "CAMPAIGN_NAME": f"{client_name} - Campaign Summary",
                "key_metrics": {
                    "KEY_METRIC_1_LABEL": "Conversions",
                    "KEY_METRIC_1_VALUE": str(metrics.get("conversions", 0)),
                    "KEY_METRIC_1_CHANGE": "vs previous",
                    "KEY_METRIC_1_DIRECTION": "positive" if metrics.get("conversions", 0) > 0 else "negative",
                    "KEY_METRIC_2_LABEL": "Cost per conversion",
                    "KEY_METRIC_2_VALUE": f"${metrics.get('cost_per_conversion', 0):.2f}",
                    "KEY_METRIC_2_CHANGE": "vs previous",
                    "KEY_METRIC_2_DIRECTION": "positive" if metrics.get("cost_per_conversion", 0) > 0 else "negative",
                    "KEY_METRIC_3_LABEL": "Cost",
                    "KEY_METRIC_3_VALUE": f"${metrics.get('cost', 0):.2f}",
                    "KEY_METRIC_3_CHANGE": "vs previous",
                    "KEY_METRIC_3_DIRECTION": "positive" if metrics.get("cost", 0) > 0 else "negative",
                    "KEY_METRIC_4_LABEL": "Clicks",
                    "KEY_METRIC_4_VALUE": str(metrics.get("clicks", 0)),
                    "KEY_METRIC_4_CHANGE": "vs previous",
                    "KEY_METRIC_4_DIRECTION": "positive" if metrics.get("clicks", 0) > 0 else "negative",
                    "KEY_METRIC_5_LABEL": "Clickthrough rate",
                    "KEY_METRIC_5_VALUE": f"{metrics.get('clickthrough_rate', 0):.2f}%",
                    "KEY_METRIC_5_CHANGE": "vs previous",
                    "KEY_METRIC_5_DIRECTION": "positive" if metrics.get("clickthrough_rate", 0) > 0 else "negative",
                    "KEY_METRIC_6_LABEL": "Impressions",
                    "KEY_METRIC_6_VALUE": str(metrics.get("impressions", 0)),
                    "KEY_METRIC_6_CHANGE": "vs previous",
                    "KEY_METRIC_6_DIRECTION": "positive" if metrics.get("impressions", 0) > 0 else "negative"
                },
                "optimization": {
                    "OPTIMIZATION_SCORE": "N/A",
                    "OPTIMIZATION_DESCRIPTION": "Connect Google Ads API to see optimization recommendations.",
                    "OPTIMIZATION_TIP_1": "Integrate Google Ads API +Real-time data",
                    "OPTIMIZATION_TIP_2": "Set up automated reporting +Weekly updates",
                    "OPTIMIZATION_BUTTON_TEXT": "View Recommendations",
                    "OPTIMIZATION_LINK": f"mailto:?subject={client_name}%20Optimization%20Recommendations",
                    "OPTIMIZATION_NOTE": "Performance data will be populated when Google Ads integration is complete."
                }
            },
            "footer": {
                "FULL_REPORT_LINK": f"mailto:?subject={client_name}%20Full%20Performance%20Report"
            }
        }

        return email_data

    def generate_email(self, email_data: Dict[str, Any]) -> str:
        """
        Generate HTML email from template data.

        Args:
            email_data: Dictionary containing email template variables

        Returns:
            HTML string
        """
        generator = EmailTemplateGenerator()
        return generator.generate(email_data)

    def save_report(self, html: str, json_data: Dict[str, Any], start_date: str, end_date: str):
        """
        Save generated report to client's communication folder.

        Args:
            html: Generated HTML email content
            json_data: JSON data used to generate the email
            start_date: Start date string
            end_date: End date string
        """
        # Generate filename with date range
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        date_suffix = f"{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}"

        # Save HTML
        html_path = self.communication_path / f"performance_report_{date_suffix}.html"
        generator = EmailTemplateGenerator()
        generator.save_html(html, str(html_path))

        # Save JSON data
        json_path = self.communication_path / f"performance_report_{date_suffix}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f"✓ Report generated successfully:")
        print(f"  HTML: {html_path}")
        print(f"  JSON: {json_path}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate client performance reports from Google Ads data"
    )
    parser.add_argument(
        "client_name",
        help="Client name (directory name in client folder)"
    )
    parser.add_argument(
        "--start-date",
        required=True,
        help="Start date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--end-date",
        required=True,
        help="End date in YYYY-MM-DD format"
    )

    args = parser.parse_args()

    # Validate date format
    try:
        datetime.strptime(args.start_date, "%Y-%m-%d")
        datetime.strptime(args.end_date, "%Y-%m-%d")
    except ValueError:
        print("Error: Dates must be in YYYY-MM-DD format")
        sys.exit(1)

    try:
        # Initialize generator
        generator = PerformanceReportGenerator(args.client_name)

        # Load client profile
        print(f"Loading client profile for {args.client_name}...")
        profile = generator.load_client_profile()

        # Fetch metrics (placeholder for now)
        print(f"Fetching Google Ads metrics from {args.start_date} to {args.end_date}...")
        print("  NOTE: Google Ads integration pending - using placeholder data")
        metrics = generator.fetch_google_ads_metrics(args.start_date, args.end_date)

        # Generate email data
        print("Generating email data...")
        email_data = generator.generate_email_data(profile, metrics, args.start_date, args.end_date)

        # Generate HTML email
        print("Generating HTML email...")
        html = generator.generate_email(email_data)

        # Save report
        generator.save_report(html, email_data, args.start_date, args.end_date)

        print("\n✓ Performance report generation complete!")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

