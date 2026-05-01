#!/usr/bin/env python3
"""
Ad Group Management System - Example Usage

This script demonstrates comprehensive usage of the Ad Group Management System
for creating, optimizing, and managing ad groups in Google Ads search campaigns.
"""

import json
import sys
import os
from typing import Dict, Any

# Add the gads directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ad_group_management_system import AdGroupManagementSystem
from ad_group_integration import AdGroupCampaignIntegrator

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")

def print_json(data: dict, indent: int = 2):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=indent, ensure_ascii=False))

def demonstrate_basic_ad_group_creation():
    """Demonstrate basic ad group creation"""
    print_section("1. BASIC AD GROUP CREATION")

    ag_system = AdGroupManagementSystem()

    # Create an optimized ad group for executive resume services
    ad_group = ag_system.create_optimized_ad_group(
        theme="Executive Resume Services",
        campaign_type="SEARCH",
        target_audience="executive_professionals",
        geo_targeting="National"
    )

    print("Created Ad Group Configuration:")
    print(f"Name: {ad_group['name']}")
    print(f"Type: {ad_group['type']}")
    print(f"Campaign Type: {ad_group['campaign_type']}")

    print(f"\nKeywords Generated: {len(ad_group['keywords'])}")
    print("Sample Keywords:")
    for kw in ad_group['keywords'][:5]:
        print(f"  • {kw['text']} ({kw['match_type']})")

    print(f"\nNegative Keywords: {len(ad_group['targeting']['negative_keywords'])}")
    print("Sample Negative Keywords:")
    for kw in ad_group['targeting']['negative_keywords'][:3]:
        print(f"  • {kw['text']} ({kw['match_type']})")

    print(f"\nOptimization Recommendations:")
    for rec in ad_group['optimization_recommendations'][:3]:
        print(f"  • {rec}")

    # Generate API JSON
    api_json = ag_system.generate_ad_group_json(ad_group)
    print(f"\nAPI JSON Preview:")
    print(json.dumps(api_json, indent=2)[:300] + "...")

def demonstrate_ad_group_validation():
    """Demonstrate ad group validation"""
    print_section("2. AD GROUP VALIDATION")

    ag_system = AdGroupManagementSystem()

    # Create a sample ad group configuration
    ad_group_config = {
        "name": "Test Ad Group",
        "type": "SEARCH_STANDARD",
        "settings": {
            "status": "ENABLED",
            "cpc_bid_micros": 500000  # $0.50
        },
        "keywords": [
            {"text": '"executive resume"', "match_type": "EXACT"},
            {"text": "resume writing", "match_type": "PHRASE"}
        ],
        "targeting": {
            "negative_keywords": [
                {"text": "free", "match_type": "EXACT"}
            ]
        }
    }

    # Validate the configuration
    validation = ag_system.validate_ad_group_config(ad_group_config)

    print("Validation Results:")
    print(f"Valid: {validation['is_valid']}")

    if validation['warnings']:
        print("Warnings:")
        for warning in validation['warnings']:
            print(f"  ⚠️  {warning}")

    if validation['errors']:
        print("Errors:")
        for error in validation['errors']:
            print(f"  ❌ {error}")

    if validation['recommendations']:
        print("Recommendations:")
        for rec in validation['recommendations']:
            print(f"  💡 {rec}")

def demonstrate_ad_group_optimization():
    """Demonstrate ad group optimization"""
    print_section("3. AD GROUP OPTIMIZATION")

    ag_system = AdGroupManagementSystem()

    # Sample ad group configuration
    ad_group_config = ag_system.create_optimized_ad_group(
        theme="Professional Resume Services",
        campaign_type="SEARCH"
    )

    # Sample performance data
    performance_data = {
        "impressions": 10000,
        "clicks": 150,
        "cost_micros": 7500000,  # $75.00
        "conversions": 3,
        "ctr": 1.5,
        "quality_score": 6,
        "search_terms_report": [
            {"text": "professional resume writer", "clicks": 50, "conversions": 2, "ctr": 3.0},
            {"text": "cheap resume service", "clicks": 30, "conversions": 0, "ctr": 0.5},
            {"text": "resume template free", "clicks": 20, "conversions": 0, "ctr": 0.3}
        ]
    }

    # Optimize the ad group
    optimization = ag_system.optimize_ad_group(ad_group_config, performance_data)

    print("Optimization Recommendations:")
    print(f"Priority Actions: {len(optimization.priority_actions)}")
    for action in optimization.priority_actions:
        print(f"  🎯 {action}")

    print(f"\nBid Adjustments: {len(optimization.bid_adjustments)}")
    for device, adjustment in optimization.bid_adjustments.items():
        print(f"  💰 {device}: {adjustment:+.0%}")

    print(f"\nNew Keywords to Add: {len(optimization.keyword_additions)}")
    for kw in optimization.keyword_additions[:3]:
        print(f"  ➕ {kw}")

    print(f"\nNegative Keywords to Add: {len(optimization.negative_keyword_additions)}")
    for kw in optimization.negative_keyword_additions[:3]:
        print(f"  🚫 {kw}")

def demonstrate_campaign_integration():
    """Demonstrate campaign integration"""
    print_section("4. CAMPAIGN INTEGRATION")

    integrator = AdGroupCampaignIntegrator()

    # Sample campaign configuration
    campaign_config = {
        "name": "MyExpertResume Executive Campaign",
        "type": "SEARCH",
        "objective": "conversions",
        "budget_micros": 50000000,  # $50 daily
        "bid_strategy_type": "Target CPA",
        "target_audience": "executive_professionals",
        "brand_business_name": "My Expert Resume",
        "asset_groups": [
            {"name": "Executive Core Services"},
            {"name": "Career Advancement"}
        ]
    }

    # Generate ad groups for the campaign
    ad_groups = integrator.generate_ad_groups_for_campaign(campaign_config)

    print(f"Generated {len(ad_groups)} Ad Groups for Campaign:")
    for i, ag in enumerate(ad_groups, 1):
        validation = ag.get('campaign_validation', {})
        status = "✅ Compatible" if validation.get('is_valid', True) else "⚠️  Review Needed"
        print(f"  {i}. {ag['name']} - {status}")
        if validation.get('warnings'):
            for warning in validation['warnings'][:1]:  # Show first warning
                print(f"     Warning: {warning}")

    # Export to CSV
    csv_content = integrator.export_ad_groups_to_csv(ad_groups, campaign_config['name'])
    print(f"\nGenerated CSV with {len(csv_content.split('\\n'))} lines")
    print("CSV Preview (first few lines):")
    lines = csv_content.split('\n')[:3]
    for line in lines:
        print(f"  {line}")

def demonstrate_performance_analysis():
    """Demonstrate performance analysis"""
    print_section("5. PERFORMANCE ANALYSIS")

    integrator = AdGroupCampaignIntegrator()

    # Sample ad groups
    ad_groups = [
        {
            "name": "Executive Resume Services - Exact",
            "type": "SEARCH_STANDARD",
            "keywords": [
                {"text": '"executive resume"', "match_type": "EXACT"},
                {"text": '"executive resume writing"', "match_type": "EXACT"}
            ]
        },
        {
            "name": "Professional Resume Services - Broad",
            "type": "SEARCH_STANDARD",
            "keywords": [
                {"text": "professional resume", "match_type": "BROAD"},
                {"text": "career resume", "match_type": "BROAD"}
            ]
        }
    ]

    # Sample performance data
    performance_data = {
        "ad_group_performance": {
            "Executive Resume Services - Exact": {
                "impressions": 5000,
                "clicks": 100,
                "cost_micros": 5000000,  # $50
                "conversions": 5,
                "ctr": 2.0,
                "cpa": 10.0
            },
            "Professional Resume Services - Broad": {
                "impressions": 8000,
                "clicks": 80,
                "cost_micros": 8000000,  # $80
                "conversions": 2,
                "ctr": 1.0,
                "cpa": 40.0
            }
        },
        "search_terms_report": [
            {"text": "executive resume writer", "conversions": 3, "cpa": 8.0},
            {"text": "professional resume service", "conversions": 1, "cpa": 25.0}
        ]
    }

    # Create performance dashboard
    dashboard = integrator.create_ad_group_performance_dashboard(ad_groups, performance_data)

    print("Performance Dashboard Summary:")
    print(f"Total Ad Groups: {dashboard['summary']['total_ad_groups']}")
    print(f"Active Ad Groups: {dashboard['summary']['active_ad_groups']}")
    print(f"Total Keywords: {dashboard['summary']['total_keywords']}")

    print("\nPerformance Metrics:")
    perf = dashboard['performance_summary']
    print(f"  Total Impressions: {perf['total_impressions']:,}")
    print(f"  Total Clicks: {perf['total_clicks']:,}")
    print(f"  Total Cost: ${perf['total_cost']:,.2f}")
    print(f"  Total Conversions: {perf['total_conversions']}")
    print(f"  Average CTR: {perf['average_ctr']}%")
    print(f"  Average CPA: ${perf['average_cpa']:.2f}")

    print("\nTop Performers:")
    for ag in dashboard['top_performers']:
        print(f"  🏆 {ag['name']}: {ag['conversions']} conversions @ ${ag['cpa']:.2f} CPA")

    print("\nUnderperformers:")
    for ag in dashboard['underperformers']:
        print(f"  📉 {ag['name']}: {ag['conversions']} conversions @ ${ag['cpa']:.2f} CPA")

    print("\nInsights:")
    for insight in dashboard['insights']:
        print(f"  💡 {insight}")

def demonstrate_best_practices():
    """Demonstrate best practices retrieval"""
    print_section("6. BEST PRACTICES")

    ag_system = AdGroupManagementSystem()

    # Get best practices for search ad groups
    best_practices = ag_system.get_ad_group_best_practices("SEARCH_STANDARD")

    print("Ad Group Best Practices by Category:")

    for category, practices in best_practices.items():
        print(f"\n{category.title()}:")
        for practice in practices:
            print(f"  ✓ {practice}")

def demonstrate_template_usage():
    """Demonstrate template-based ad group creation"""
    print_section("7. TEMPLATE-BASED CREATION")

    ag_system = AdGroupManagementSystem()

    # Create ad group from executive services template
    exec_ad_group = ag_system.create_ad_group_from_template(
        "executive_services",
        customizations={
            "geo_targeting": "Florida",
            "budget_micros": 30000000  # $30 daily
        }
    )

    print("Executive Services Ad Group from Template:")
    print(f"Name: {exec_ad_group['name']}")
    print(f"Type: {exec_ad_group['type']}")
    print(f"Keywords: {len(exec_ad_group['keywords'])}")
    print(f"Settings: CPC Bid = ${exec_ad_group['settings'].cpc_bid_micros / 1000000:.2f}")

    # Create ad group from local services template
    local_ad_group = ag_system.create_ad_group_from_template("local_services")

    print("\nLocal Services Ad Group from Template:")
    print(f"Name: {local_ad_group['name']}")
    print(f"Type: {local_ad_group['type']}")
    print(f"Target Audience: {local_ad_group.get('target_audience', 'N/A')}")

def main():
    """Run all demonstrations"""
    print("🎯 AD GROUP MANAGEMENT SYSTEM - COMPREHENSIVE DEMO")
    print("=" * 70)
    print("This demo showcases the complete Ad Group Management System")
    print("for creating, optimizing, and managing Google Ads ad groups.")
    print("=" * 70)

    try:
        demonstrate_basic_ad_group_creation()
        demonstrate_ad_group_validation()
        demonstrate_ad_group_optimization()
        demonstrate_campaign_integration()
        demonstrate_performance_analysis()
        demonstrate_best_practices()
        demonstrate_template_usage()

        print_section("DEMO COMPLETE")
        print("✅ All Ad Group Management System features demonstrated successfully!")
        print("\nKey Capabilities:")
        print("• Automated ad group creation with best practices")
        print("• Configuration validation and optimization")
        print("• Campaign integration and CSV export")
        print("• Performance analysis and dashboard")
        print("• Template-based creation for common scenarios")
        print("• Best practices guidance and recommendations")

    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
