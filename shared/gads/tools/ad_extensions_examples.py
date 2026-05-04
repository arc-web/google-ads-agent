#!/usr/bin/env python3
"""
Ad Extensions Management System - Example Usage

This script demonstrates comprehensive usage of the Ad Extensions Management System
for creating, optimizing, and managing ad extensions in Google Ads campaigns.
"""

import json
import sys
import os
from typing import Dict, Any

# Add the gads directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ad_extensions_management_system import AdExtensionsManagementSystem, ExtensionType
from ad_extensions_integration import AdExtensionsCampaignIntegrator

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")

def print_json(data: dict, indent: int = 2):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=indent, ensure_ascii=False))

def demonstrate_basic_extension_creation():
    """Demonstrate basic extension creation"""
    print_section("1. BASIC EXTENSION CREATION")

    ext_system = AdExtensionsManagementSystem()

    # Business information
    business_info = {
        "name": "Example Services Company",
        "website": "https://example.com",
        "phone": "+1-555-123-4567",
        "country_code": "US",
        "type": "professional_services",
        "years_experience": 15,
        "certifications": ["Certified Resume Writer", "Professional Career Coach"],
        "address": {
            "line1": "123 Business St",
            "city": "Miami",
            "state": "FL",
            "zip": "33101"
        }
    }

    # Generate extensions for professional services
    extensions = ext_system.generate_campaign_extensions(
        business_type="professional_services",
        business_info=business_info,
        extension_types=["sitelink", "callout", "call", "structured_snippet"]
    )

    print(f"Generated extensions for {len(extensions)} types:")

    for ext_type, ext_list in extensions.items():
        print(f"\n{ext_type.upper()} EXTENSIONS ({len(ext_list)}):")
        for i, ext in enumerate(ext_list[:3], 1):  # Show first 3
            print(f"  {i}. {ext.name}")
            if hasattr(ext, 'text'):
                print(f"     Text: {ext.text}")
            if hasattr(ext, 'final_urls') and ext.final_urls:
                print(f"     URL: {ext.final_urls[0]}")
            if hasattr(ext, 'phone_number'):
                print(f"     Phone: {ext.phone_number}")

def demonstrate_extension_validation():
    """Demonstrate extension validation"""
    print_section("2. EXTENSION VALIDATION")

    ext_system = AdExtensionsManagementSystem()

    # Create sample extensions with issues
    from ad_extensions_management_system import SitelinkExtension, CalloutExtension

    extensions = {
        "sitelink": [
            SitelinkExtension(
                extension_type=ExtensionType.SITELINK,
                name="Valid Sitelink",
                text="Contact Us",
                final_urls=["https://example.com/contact"]
            ),
            SitelinkExtension(
                extension_type=ExtensionType.SITELINK,
                name="Invalid Sitelink",
                text="This sitelink text is way too long and exceeds the character limit",
                final_urls=[]  # Missing URL
            )
        ],
        "callout": [
            CalloutExtension(
                extension_type=ExtensionType.CALLOUT,
                name="Valid Callout",
                text="Free Consultation"
            ),
            CalloutExtension(
                extension_type=ExtensionType.CALLOUT,
                name="Invalid Callout",
                text="This callout text is also extremely long and will definitely exceed Google's character limits for callout extensions"
            )
        ]
    }

    # Validate extensions
    validation = ext_system.validate_extensions(extensions)

    print("Extension Validation Results:")
    print(f"Overall Valid: {validation['is_valid']}")
    print(f"Total Extensions: {validation['extension_count']}")

    if validation['errors']:
        print(f"\nErrors ({len(validation['errors'])}):")
        for error in validation['errors']:
            print(f"  ❌ {error}")

    if validation['warnings']:
        print(f"\nWarnings ({len(validation['warnings'])}):")
        for warning in validation['warnings']:
            print(f"  ⚠️  {warning}")

def demonstrate_extension_optimization():
    """Demonstrate extension optimization"""
    print_section("3. EXTENSION OPTIMIZATION")

    ext_system = AdExtensionsManagementSystem()

    # Create sample extensions
    from ad_extensions_management_system import SitelinkExtension, CalloutExtension

    extensions = {
        "sitelink": [
            SitelinkExtension(
                extension_type=ExtensionType.SITELINK,
                name="High Performing Sitelink",
                text="Free Quote",
                final_urls=["https://example.com/quote"]
            ),
            SitelinkExtension(
                extension_type=ExtensionType.SITELINK,
                name="Low Performing Sitelink",
                text="About Us",
                final_urls=["https://example.com/about"]
            )
        ],
        "callout": [
            CalloutExtension(
                extension_type=ExtensionType.CALLOUT,
                name="Good Callout",
                text="Licensed & Insured"
            )
        ]
    }

    # Sample performance data
    performance_data = {
        "High Performing Sitelink": {
            "clicks": 150,
            "impressions": 5000,
            "cost_micros": 75000000,  # $75
            "conversions": 8
        },
        "Low Performing Sitelink": {
            "clicks": 5,
            "impressions": 2000,
            "cost_micros": 2500000,  # $2.50
            "conversions": 0
        },
        "Good Callout": {
            "clicks": 0,  # Callouts don't directly drive clicks
            "impressions": 8000,
            "ctr_impact": 0.15  # 15% CTR improvement
        }
    }

    # Optimize extensions
    optimization = ext_system.optimize_extensions_performance(extensions, performance_data)

    print("Extension Optimization Recommendations:")
    print(f"Priority Actions ({len(optimization.priority_actions)}):")
    for action in optimization.priority_actions:
        print(f"  🎯 {action}")

    print(f"\nNew Extension Suggestions ({len(optimization.new_extensions_suggestions)}):")
    for suggestion in optimization.new_extensions_suggestions:
        print(f"  ➕ {suggestion.get('suggestion', 'Additional extensions recommended')}")

def demonstrate_campaign_integration():
    """Demonstrate campaign integration"""
    print_section("4. CAMPAIGN INTEGRATION")

    integrator = AdExtensionsCampaignIntegrator()

    # Sample campaign configuration
    campaign_config = {
        "name": "Example Services Professional Services",
        "type": "SEARCH",
        "objective": "conversions",
        "brand_business_name": "Example Services Company",
        "website": "https://example.com",
        "phone": "+1-555-123-4567",
        "business_type": "professional_services",
        "years_experience": 15,
        "callouts": [
            "Certified Resume Writers",
            "15+ Years Experience",
            "100% Satisfaction Guarantee"
        ]
    }

    # Sample ad groups
    ad_groups = [
        {
            "name": "Executive Resume Services",
            "type": "SEARCH_STANDARD"
        },
        {
            "name": "Professional Resume Services",
            "type": "SEARCH_STANDARD"
        }
    ]

    # Generate extensions for the campaign
    extensions = integrator.generate_extensions_for_campaign(campaign_config, ad_groups)

    print(f"Generated extensions for campaign '{campaign_config['name']}':")

    for ext_type, ext_list in extensions.items():
        print(f"\n{ext_type.upper()} ({len(ext_list)} extensions):")
        for ext in ext_list[:2]:  # Show first 2 of each type
            print(f"  • {ext.name}")
            if hasattr(ext, 'text') and len(ext.text) < 30:
                print(f"    \"{ext.text}\"")
            elif hasattr(ext, 'phone_number'):
                print(f"    {ext.phone_number}")
            elif hasattr(ext, 'final_urls') and ext.final_urls:
                print(f"    {ext.final_urls[0]}")

    # Validate campaign extensions
    validation = integrator.validate_campaign_extensions(extensions, campaign_config)

    print(f"\nCampaign Validation: {'✅ PASS' if validation['is_valid'] else '❌ ISSUES'}")

    if validation.get('warnings'):
        print("Campaign Warnings:")
        for warning in validation['warnings']:
            print(f"  ⚠️  {warning}")

    if validation.get('errors'):
        print("Campaign Errors:")
        for error in validation['errors']:
            print(f"  ❌ {error}")

    if validation.get('recommendations'):
        print("Recommendations:")
        for rec in validation['recommendations'][:3]:
            print(f"  💡 {rec}")

def demonstrate_performance_dashboard():
    """Demonstrate performance dashboard"""
    print_section("5. PERFORMANCE DASHBOARD")

    integrator = AdExtensionsCampaignIntegrator()

    # Sample extensions
    from ad_extensions_management_system import SitelinkExtension, CalloutExtension, CallExtension

    extensions = {
        "sitelink": [
            SitelinkExtension(
                extension_type=ExtensionType.SITELINK,
                name="Services Sitelink",
                text="Our Services",
                final_urls=["https://example.com/services"]
            ),
            SitelinkExtension(
                extension_type=ExtensionType.SITELINK,
                name="Contact Sitelink",
                text="Contact Us",
                final_urls=["https://example.com/contact"]
            )
        ],
        "callout": [
            CalloutExtension(
                extension_type=ExtensionType.CALLOUT,
                name="Experience Callout",
                text="15+ Years Experience"
            )
        ],
        "call": [
            CallExtension(
                extension_type=ExtensionType.CALL,
                name="Business Phone",
                phone_number="+1-555-123-4567",
                call_tracking_enabled=True
            )
        ]
    }

    # Sample performance data
    performance_data = {
        "Services Sitelink": {
            "clicks": 120,
            "impressions": 4000,
            "cost_micros": 60000000,  # $60
            "conversions": 6
        },
        "Contact Sitelink": {
            "clicks": 45,
            "impressions": 3000,
            "cost_micros": 22500000,  # $22.50
            "conversions": 2
        },
        "Experience Callout": {
            "impressions": 6000,
            "ctr_impact": 0.12
        },
        "Business Phone": {
            "calls": 8,
            "cost_micros": 40000000,  # $40
            "conversions": 4
        }
    }

    # Create performance dashboard
    dashboard = integrator.ext_system.create_extension_performance_dashboard(extensions, performance_data)

    print("Extension Performance Dashboard:")
    print(f"Total Extensions: {dashboard['summary']['total_extensions']}")
    print(f"Active Extensions: {dashboard['summary']['active_extensions']}")
    print(f"Extension Types: {dashboard['summary']['extension_types']}")

    perf = dashboard.get('performance_summary', {})
    if perf:
        print("\nPerformance Summary:")
        print(f"  • Impressions: {perf.get('total_impressions', 0):,}")
        print(f"  • Clicks: {perf.get('total_clicks', 0):,}")
        print(f"  • Cost: ${perf.get('total_cost', 0):,.2f}")
        print(f"  • Conversions: {perf.get('total_conversions', 0)}")
        print(f"  • Avg CTR: {perf.get('average_ctr', 0):.2f}%")
        print(f"  • Avg CPA: ${perf.get('average_cpa', 0):.2f}")

    print("\nPerformance by Type:")
    for ext_type, type_perf in dashboard.get('performance_by_type', {}).items():
        if type_perf.get('total_clicks', 0) > 0:
            print(f"  • {ext_type.title()}: {type_perf['total_clicks']} clicks, {type_perf['active']} active")

    print(f"\nTop Performers ({len(dashboard.get('top_performers', []))}):")
    for perf in dashboard['top_performers'][:3]:
        print(f"  🏆 {perf['name']}: {perf['clicks']} clicks")

    print(f"\nInsights ({len(dashboard.get('insights', []))}):")
    for insight in dashboard.get('insights', [])[:3]:
        print(f"  💡 {insight}")

def demonstrate_csv_export():
    """Demonstrate CSV export"""
    print_section("6. CSV EXPORT")

    integrator = AdExtensionsCampaignIntegrator()

    # Sample campaign extensions
    from ad_extensions_management_system import SitelinkExtension, CalloutExtension

    extensions = {
        "sitelink": [
            SitelinkExtension(
                extension_type=ExtensionType.SITELINK,
                name="Services",
                text="Our Services",
                final_urls=["https://example.com/services"],
                status="ENABLED"
            )
        ],
        "callout": [
            CalloutExtension(
                extension_type=ExtensionType.CALLOUT,
                name="Experience",
                text="15+ Years Experience",
                status="ENABLED"
            )
        ]
    }

    campaign_config = {
        "name": "My Test Campaign"
    }

    # Export to CSV
    csv_content = integrator.export_extensions_to_campaign_csv(extensions, campaign_config)

    print("Generated CSV for Google Ads Editor:")
    print("=" * 50)
    lines = csv_content.split('\n')[:6]  # Show first 6 lines
    for line in lines:
        print(line)
    print("...")

    print(f"\nTotal CSV lines: {len(csv_content.split('\\n'))}")

def demonstrate_api_json_generation():
    """Demonstrate API JSON generation"""
    print_section("7. API JSON GENERATION")

    ext_system = AdExtensionsManagementSystem()

    # Sample extensions
    from ad_extensions_management_system import SitelinkExtension, CalloutExtension

    extensions = {
        "sitelink": [
            SitelinkExtension(
                extension_type=ExtensionType.SITELINK,
                name="Services Link",
                text="Our Services",
                final_urls=["https://example.com/services"],
                status="ENABLED"
            )
        ],
        "callout": [
            CalloutExtension(
                extension_type=ExtensionType.CALLOUT,
                name="Experience Callout",
                text="15+ Years Experience",
                status="ENABLED"
            )
        ]
    }

    # Generate API JSON
    api_operations = ext_system.generate_extension_json_for_api(extensions)

    print("Generated Google Ads API Operations:")
    print(json.dumps(api_operations, indent=2))

def demonstrate_best_practices():
    """Demonstrate best practices retrieval"""
    print_section("8. BEST PRACTICES")

    ext_system = AdExtensionsManagementSystem()

    # Get general extension best practices
    general_practices = ext_system.get_extension_best_practices()

    print("Extension Management Best Practices:")

    for category, practices in general_practices.items():
        print(f"\n{category.title()}:")
        for practice in practices:
            print(f"  ✓ {practice}")

    # Get sitelink-specific practices
    sitelink_practices = ext_system.get_extension_best_practices("sitelink")

    if "sitelink_specific" in sitelink_practices:
        print("\nSitelink-Specific Practices:")
        for practice in sitelink_practices["sitelink_specific"]:
            print(f"  🔗 {practice}")

def demonstrate_extension_strategy():
    """Demonstrate extension strategy development"""
    print_section("9. EXTENSION STRATEGY")

    integrator = AdExtensionsCampaignIntegrator()

    # Sample campaign configurations
    campaigns = [
        {
            "name": "Search Campaign",
            "type": "SEARCH",
            "objective": "conversions"
        },
        {
            "name": "Performance Max Campaign",
            "type": "PERFORMANCE_MAX",
            "objective": "awareness"
        }
    ]

    for campaign in campaigns:
        print(f"\nStrategy for {campaign['name']}:")
        strategy = integrator.get_campaign_extension_strategy(campaign)

        print(f"  Campaign Type: {strategy['campaign_type']}")
        print(f"  Objective: {strategy['objective']}")
        print(f"  Recommended Extensions: {', '.join(strategy['recommended_extensions'][:4])}")
        print(f"  Priority Order: {', '.join(strategy['priority_order'][:4])}")

        if strategy.get('expected_impact'):
            print("  Expected Impact:")
            for ext, impact in list(strategy['expected_impact'].items())[:3]:
                print(f"    • {ext.title()}: {impact}")

def main():
    """Run all demonstrations"""
    print("🎯 AD EXTENSIONS MANAGEMENT SYSTEM - COMPREHENSIVE DEMO")
    print("=" * 70)
    print("This demo showcases the complete Ad Extensions Management System")
    print("for creating, optimizing, and managing ad extensions in Google Ads.")
    print("=" * 70)

    try:
        demonstrate_basic_extension_creation()
        demonstrate_extension_validation()
        demonstrate_extension_optimization()
        demonstrate_campaign_integration()
        demonstrate_performance_dashboard()
        demonstrate_csv_export()
        demonstrate_api_json_generation()
        demonstrate_best_practices()
        demonstrate_extension_strategy()

        print_section("DEMO COMPLETE")
        print("✅ All Ad Extensions Management System features demonstrated successfully!")
        print("\nKey Capabilities:")
        print("• Automated extension generation for different business types")
        print("• Extension validation and compliance checking")
        print("• Performance-based optimization recommendations")
        print("• Campaign integration with automatic extension selection")
        print("• Comprehensive performance dashboards and reporting")
        print("• CSV export for Google Ads Editor compatibility")
        print("• API JSON generation for programmatic management")
        print("• Best practices guidance and strategy development")

    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
