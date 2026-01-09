#!/usr/bin/env python3
"""
Keyword Management System - Example Usage

This script demonstrates comprehensive usage of the Keyword Management System
for creating, optimizing, and managing keywords in Google Ads search campaigns.
"""

import json
import sys
import os
from typing import Dict, Any

# Add the gads directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from keyword_management_system import KeywordManagementSystem, KeywordCriterion, KeywordPerformance
from keyword_integration import KeywordCampaignIntegrator

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")

def print_json(data: dict, indent: int = 2):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=indent, ensure_ascii=False))

def demonstrate_basic_keyword_generation():
    """Demonstrate basic keyword generation"""
    print_section("1. BASIC KEYWORD GENERATION")

    kw_system = KeywordManagementSystem()

    # Generate keywords for executive resume services
    keywords = kw_system.generate_keywords_for_theme(
        theme="executive resume services",
        target_audience="executive_professionals",
        competition_level="high",
        keyword_count=20
    )

    print(f"Generated {len(keywords)} keywords for 'executive resume services':")

    # Group by match type
    by_match_type = {}
    for kw in keywords:
        mt = kw.match_type
        if mt not in by_match_type:
            by_match_type[mt] = []
        by_match_type[mt].append(kw.text)

    for match_type, kw_list in by_match_type.items():
        print(f"\n{match_type} Match ({len(kw_list)} keywords):")
        for kw in kw_list[:5]:  # Show first 5
            bid = f" - ${kw.bid_micros/1000000:.2f}" if kw.bid_micros else ""
            print(f"  • {kw}{bid}")

    # Generate API JSON
    api_json = kw_system.generate_keyword_json_for_api(keywords[:3], "customers/123/adGroups/456")
    print(f"\nAPI JSON Example (first 3 keywords):")
    print(json.dumps(api_json, indent=2))

def demonstrate_keyword_categorization():
    """Demonstrate keyword categorization"""
    print_section("2. KEYWORD CATEGORIZATION")

    kw_system = KeywordManagementSystem()

    # Create sample keywords
    sample_keywords = [
        KeywordCriterion(text='"executive resume"', match_type="EXACT", bid_micros=3000000),
        KeywordCriterion(text="resume writing service", match_type="PHRASE", bid_micros=1500000),
        KeywordCriterion(text="professional resume", match_type="BROAD", bid_micros=800000),
        KeywordCriterion(text="how to write resume", match_type="PHRASE", bid_micros=500000),
        KeywordCriterion(text="buy resume service", match_type="EXACT", bid_micros=4000000)
    ]

    # Categorize keywords
    categories = kw_system.categorize_keywords(sample_keywords)

    print("Keyword Categorization Results:")

    for category, keywords in categories.items():
        if keywords:  # Only show non-empty categories
            print(f"\n{category.replace('_', ' ').title()} ({len(keywords)} keywords):")
            for kw in keywords:
                print(f"  • {kw.text} ({kw.match_type})")

def demonstrate_keyword_optimization():
    """Demonstrate keyword optimization"""
    print_section("3. KEYWORD OPTIMIZATION")

    kw_system = KeywordManagementSystem()

    # Sample keywords with performance data
    keywords = [
        KeywordCriterion(text='"executive resume"', match_type="EXACT", bid_micros=3000000),
        KeywordCriterion(text="resume writing service", match_type="PHRASE", bid_micros=1500000),
        KeywordCriterion(text="cheap resume service", match_type="BROAD", bid_micros=800000)
    ]

    # Sample performance data
    performance_data = {
        '"executive resume"': KeywordPerformance(
            impressions=1000, clicks=50, cost_micros=150000000,  # $150
            conversions=5, ctr=5.0, quality_score=8
        ),
        "resume writing service": KeywordPerformance(
            impressions=2000, clicks=30, cost_micros=45000000,  # $45
            conversions=1, ctr=1.5, quality_score=6
        ),
        "cheap resume service": KeywordPerformance(
            impressions=500, clicks=25, cost_micros=20000000,  # $20
            conversions=0, ctr=5.0, quality_score=4
        )
    }

    # Optimize keywords
    optimization = kw_system.optimize_keyword_performance(keywords, performance_data)

    print("Keyword Optimization Recommendations:")
    print(f"Priority Actions ({len(optimization.priority_actions)}):")
    for action in optimization.priority_actions:
        print(f"  🎯 {action}")

    print(f"\nBid Adjustments ({len(optimization.bid_adjustments)}):")
    for keyword, adjustment in optimization.bid_adjustments.items():
        print(f"  💰 {keyword}: {adjustment:+.0%}")

    print(f"\nNegative Keywords to Add ({len(optimization.negative_keyword_additions)}):")
    for kw in optimization.negative_keyword_additions:
        print(f"  🚫 {kw}")

def demonstrate_negative_keywords():
    """Demonstrate negative keyword generation"""
    print_section("4. NEGATIVE KEYWORD GENERATION")

    kw_system = KeywordManagementSystem()

    # Generate negative keywords for resume theme
    positive_keywords = ['"executive resume"', 'resume writing', 'professional resume']
    negative_keywords = kw_system.generate_negative_keywords(
        theme="executive resume services",
        positive_keywords=positive_keywords
    )

    print(f"Generated {len(negative_keywords)} negative keywords for resume theme:")

    for kw in negative_keywords:
        print(f"  • {kw.text} ({kw.match_type}) - Negative: {kw.is_negative}")

    # Simulate search terms report
    search_terms_report = [
        {"text": "free resume template", "ctr": 0.5, "clicks": 20},
        {"text": "resume pdf download", "ctr": 0.3, "clicks": 15},
        {"text": "cheap resume writing", "ctr": 0.8, "clicks": 10}
    ]

    # Generate negative keywords from search terms
    additional_negatives = kw_system.generate_negative_keywords(
        theme="resume services",
        positive_keywords=positive_keywords,
        search_terms_report=search_terms_report
    )

    print(f"\nAdditional negatives from search terms ({len(additional_negatives)}):")
    for kw in additional_negatives:
        if kw.text not in [nkw.text for nkw in negative_keywords]:  # Show only new ones
            print(f"  • {kw.text} ({kw.match_type})")

def demonstrate_keyword_validation():
    """Demonstrate keyword validation"""
    print_section("5. KEYWORD VALIDATION")

    kw_system = KeywordManagementSystem()

    # Create keywords with various issues
    test_keywords = [
        KeywordCriterion(text="this is a very long keyword that exceeds the eighty character limit in google ads and should be flagged as invalid", match_type="EXACT"),
        KeywordCriterion(text="normal keyword", match_type="INVALID"),
        KeywordCriterion(text='"exact keyword"', match_type="BROAD"),  # Broad with quotes
        KeywordCriterion(text="duplicate keyword", match_type="EXACT"),
        KeywordCriterion(text="duplicate keyword", match_type="PHRASE"),  # Duplicate
        KeywordCriterion(text="good keyword", match_type="EXACT", bid_micros=10000)  # Very low bid
    ]

    # Validate keywords
    validation = kw_system.validate_keyword_criteria(test_keywords)

    print("Keyword Validation Results:")
    print(f"Overall Valid: {validation['is_valid']}")
    print(f"Total Keywords: {validation['keyword_count']}")

    if validation['errors']:
        print(f"\nErrors ({len(validation['errors'])}):")
        for error in validation['errors']:
            print(f"  ❌ {error}")

    if validation['warnings']:
        print(f"\nWarnings ({len(validation['warnings'])}):")
        for warning in validation['warnings']:
            print(f"  ⚠️  {warning}")

def demonstrate_campaign_integration():
    """Demonstrate campaign integration"""
    print_section("6. CAMPAIGN INTEGRATION")

    integrator = KeywordCampaignIntegrator()

    # Sample campaign configuration
    campaign_config = {
        "name": "Executive Resume Services Campaign",
        "type": "SEARCH",
        "target_audience": "executive_professionals",
        "budget": 75.0
    }

    # Sample ad groups
    ad_groups = [
        {
            "name": "Executive Resume Services - Exact",
            "type": "SEARCH_STANDARD"
        },
        {
            "name": "Professional Resume Services - Broad",
            "type": "SEARCH_STANDARD"
        }
    ]

    # Generate keywords for the campaign
    campaign_keywords = integrator.generate_keywords_for_campaign(campaign_config, ad_groups)

    print(f"Generated keywords for {len(campaign_keywords)} ad groups:")

    for ad_group_name, keywords in campaign_keywords.items():
        positive_kws = [kw for kw in keywords if not kw.is_negative]
        negative_kws = [kw for kw in keywords if kw.is_negative]

        print(f"\n{ad_group_name}:")
        print(f"  • Positive keywords: {len(positive_kws)}")
        print(f"  • Negative keywords: {len(negative_kws)}")

        # Show sample positive keywords
        print("  • Sample positive keywords:")
        for kw in positive_kws[:3]:
            bid = f" (${kw.bid_micros/1000000:.2f})" if kw.bid_micros else ""
            print(f"    - {kw.text} ({kw.match_type}){bid}")

    # Validate campaign keywords
    validation = integrator.validate_campaign_keywords(campaign_keywords, campaign_config)

    print(f"\nCampaign Validation: {'✅ PASS' if validation['is_valid'] else '❌ ISSUES'}")
    print(f"Total Keywords: {validation['keyword_distribution']['total_keywords']}")

    if validation['campaign_level_issues']:
        print("Campaign Issues:")
        for issue in validation['campaign_level_issues']:
            print(f"  ⚠️  {issue}")

def demonstrate_performance_dashboard():
    """Demonstrate performance dashboard"""
    print_section("7. PERFORMANCE DASHBOARD")

    integrator = KeywordCampaignIntegrator()

    # Sample campaign keywords
    campaign_keywords = {
        "Executive Services": [
            KeywordCriterion(text='"executive resume"', match_type="EXACT", bid_micros=3000000),
            KeywordCriterion(text="resume writing", match_type="PHRASE", bid_micros=1500000)
        ],
        "Professional Services": [
            KeywordCriterion(text="professional resume", match_type="BROAD", bid_micros=800000),
            KeywordCriterion(text="career resume", match_type="PHRASE", bid_micros=1000000)
        ]
    }

    # Sample performance data
    performance_data = {
        "Executive Services": {
            "total_impressions": 5000,
            "total_clicks": 250,
            "total_cost_micros": 750000000,  # $750
            "total_conversions": 15,
            "keyword_performance": {
                '"executive resume"': {
                    "impressions": 3000, "clicks": 150, "cost_micros": 450000000,
                    "conversions": 10, "ctr": 5.0
                },
                "resume writing": {
                    "impressions": 2000, "clicks": 100, "cost_micros": 300000000,
                    "conversions": 5, "ctr": 5.0
                }
            }
        },
        "Professional Services": {
            "total_impressions": 3000,
            "total_clicks": 90,
            "total_cost_micros": 270000000,  # $270
            "total_conversions": 3,
            "keyword_performance": {
                "professional resume": {
                    "impressions": 2000, "clicks": 60, "cost_micros": 180000000,
                    "conversions": 2, "ctr": 3.0
                },
                "career resume": {
                    "impressions": 1000, "clicks": 30, "cost_micros": 90000000,
                    "conversions": 1, "ctr": 3.0
                }
            }
        }
    }

    # Create performance dashboard
    dashboard = integrator.create_keyword_performance_dashboard(campaign_keywords, performance_data)

    print("Campaign Performance Dashboard:")
    print(f"Total Ad Groups: {dashboard['campaign_overview']['total_ad_groups']}")
    print(f"Total Keywords: {dashboard['campaign_overview']['total_keywords']}")
    print(f"Positive Keywords: {dashboard['campaign_overview']['total_positive_keywords']}")
    print(f"Negative Keywords: {dashboard['campaign_overview']['total_negative_keywords']}")

    perf = dashboard['performance_summary']
    print("
Performance Summary:"    print(f"  • Impressions: {perf['total_impressions']:,}")
    print(f"  • Clicks: {perf['total_clicks']:,}")
    print(f"  • Cost: ${perf['total_cost']:,.2f}")
    print(f"  • Conversions: {perf['total_conversions']}")
    print(f"  • Avg CTR: {perf['average_ctr']}%")
    print(f"  • Avg CPA: ${perf['average_cpa']:.2f}")

    print(f"\nTop Performing Keywords ({len(dashboard['top_performing_keywords'])}):")
    for kw in dashboard['top_performing_keywords']:
        print(f"  🏆 {kw['keyword']}: {kw['conversions']} conv @ ${kw['cpa']:.2f} CPA")

    print(f"\nUnderperforming Keywords ({len(dashboard['underperforming_keywords'])}):")
    for kw in dashboard['underperforming_keywords']:
        print(f"  📉 {kw['keyword']}: {kw['conversions']} conv @ ${kw['cpa']:.2f} CPA")

    print("
Insights:"    for insight in dashboard['insights']:
        print(f"  💡 {insight}")

    print("
Recommendations:"    for rec in dashboard['recommendations']:
        print(f"  ✅ {rec}")

def demonstrate_csv_export():
    """Demonstrate CSV export"""
    print_section("8. CSV EXPORT")

    integrator = KeywordCampaignIntegrator()

    # Sample campaign keywords
    campaign_keywords = {
        "Executive Resume Services": [
            KeywordCriterion(text='"executive resume"', match_type="EXACT", bid_micros=3000000, status="ENABLED"),
            KeywordCriterion(text="resume writing service", match_type="PHRASE", bid_micros=1500000),
            KeywordCriterion(text="template", match_type="EXACT", is_negative=True)
        ]
    }

    # Export to CSV
    csv_content = integrator.export_keywords_to_campaign_csv(campaign_keywords, "My Campaign")

    print("Generated CSV for Google Ads Editor:")
    print("=" * 50)
    lines = csv_content.split('\n')[:5]  # Show first 5 lines
    for line in lines:
        print(line)
    print("...")

    print(f"\nTotal CSV lines: {len(csv_content.split('\\n'))}")

def demonstrate_best_practices():
    """Demonstrate best practices retrieval"""
    print_section("9. BEST PRACTICES")

    kw_system = KeywordManagementSystem()

    # Get general keyword best practices
    general_practices = kw_system.get_keyword_best_practices()

    print("Keyword Management Best Practices:")

    for category, practices in general_practices.items():
        print(f"\n{category.title()}:")
        for practice in practices:
            print(f"  ✓ {practice}")

    # Get match type specific practices
    exact_practices = kw_system.get_keyword_best_practices("EXACT")
    if "exact_match" in exact_practices:
        print("
Exact Match Specific Practices:"        for practice in exact_practices["exact_match"]:
            print(f"  🎯 {practice}")

def main():
    """Run all demonstrations"""
    print("🎯 KEYWORD MANAGEMENT SYSTEM - COMPREHENSIVE DEMO")
    print("=" * 70)
    print("This demo showcases the complete Keyword Management System")
    print("for creating, optimizing, and managing keywords in Google Ads.")
    print("=" * 70)

    try:
        demonstrate_basic_keyword_generation()
        demonstrate_keyword_categorization()
        demonstrate_keyword_optimization()
        demonstrate_negative_keywords()
        demonstrate_keyword_validation()
        demonstrate_campaign_integration()
        demonstrate_performance_dashboard()
        demonstrate_csv_export()
        demonstrate_best_practices()

        print_section("DEMO COMPLETE")
        print("✅ All Keyword Management System features demonstrated successfully!")
        print("\nKey Capabilities:")
        print("• Automated keyword generation with multiple match types")
        print("• Intelligent bid calculation based on competition")
        print("• Performance-based optimization recommendations")
        print("• Negative keyword generation and management")
        print("• Campaign-level integration and validation")
        print("• Comprehensive performance dashboards")
        print("• CSV export for Google Ads Editor")
        print("• Best practices guidance and compliance checking")

    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()