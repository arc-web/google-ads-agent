#!/usr/bin/env python3
"""
Example usage of the Google Ads Reference Tool

This script demonstrates various ways to use the Google Ads Reference Tool
to get campaign setup information from Context7 documentation.
"""

import json
import sys
import os

# Add the gads directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from google_ads_reference_tool import GoogleAdsReferenceTool

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_json(data: dict, indent: int = 2):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=indent, ensure_ascii=False))

def main():
    """Demonstrate the Google Ads Reference Tool"""
    print("Google Ads Reference Tool - Example Usage")
    print("=" * 60)

    # Initialize the tool
    tool = GoogleAdsReferenceTool()

    # Example 1: Campaign Types
    print_section("1. Campaign Types Information")

    campaign_types = ["search", "display", "performance_max", "shopping"]
    for campaign_type in campaign_types:
        print(f"\n--- {campaign_type.upper().replace('_', ' ')} CAMPAIGNS ---")
        info = tool.get_campaign_setup_info(f"{campaign_type} campaigns")
        if "error" not in info:
            print(f"Name: {info.get('name', 'N/A')}")
            print(f"Description: {info.get('description', 'N/A')[:100]}...")
            networks = info.get('networks', [])
            if networks:
                print(f"Networks: {', '.join(networks)}")
            ad_formats = info.get('ad_formats', [])
            if ad_formats:
                print(f"Ad Formats: {', '.join(ad_formats[:3])}")
            bidding_strategies = info.get('bidding_strategies', [])
            if bidding_strategies:
                print(f"Bidding Strategies: {', '.join(bidding_strategies[:3])}")
        else:
            print(f"Error: {info['error']}")

    # Example 2: Bidding Strategies
    print_section("2. Bidding Strategies Information")

    bidding_strategies = ["target_cpa", "target_roas", "manual_cpc"]
    for strategy in bidding_strategies:
        print(f"\n--- {strategy.upper().replace('_', ' ')} ---")
        info = tool.get_campaign_setup_info(strategy)
        if "error" not in info:
            print(f"Name: {info.get('name', 'N/A')}")
            print(f"Description: {info.get('description', 'N/A')[:100]}...")
            use_cases = info.get('use_cases', [])
            if use_cases:
                print(f"Use Cases: {', '.join(use_cases)}")
            campaign_types = info.get('campaign_types', [])
            if campaign_types:
                print(f"Campaign Types: {', '.join(campaign_types[:3])}")
        else:
            print(f"Error: {info['error']}")

    # Example 3: Targeting Options
    print_section("3. Targeting Options")

    targeting_options = ["keywords", "audience", "location"]
    for targeting in targeting_options:
        print(f"\n--- {targeting.upper()} TARGETING ---")
        info = tool.get_campaign_setup_info(f"{targeting} targeting")
        if "error" not in info:
            print(f"Description: {info['description']}")
            print(f"Options: {', '.join(info['options'])}")
        else:
            print(f"Error: {info['error']}")

    # Example 4: JSON Examples
    print_section("4. Campaign Creation JSON Examples")

    print("\n--- SEARCH CAMPAIGN JSON ---")
    search_json = tool.get_campaign_creation_json_example("search")
    print_json(search_json)

    print("\n--- PERFORMANCE MAX CAMPAIGN JSON ---")
    pmax_json = tool.get_campaign_creation_json_example("performance_max")
    print_json(pmax_json)

    # Example 5: Search Functionality
    print_section("5. Search Functionality")

    print("\n--- SEARCHING FOR 'CONVERSION' ---")
    search_results = tool.search_documentation("conversion")
    print(f"Found {len(search_results)} relevant results")
    for i, result in enumerate(search_results[:2]):  # Show first 2 results
        print(f"\nResult {i+1}: {result.get('name', 'Unknown')}")
        print(f"Type: {result.get('type', 'Unknown')}")
        if 'description' in result:
            print(f"Description: {result['description'][:150]}...")

    # Example 6: General Help
    print_section("6. General Help")

    help_info = tool.get_campaign_setup_info("help")
    print("Available Topics:")
    for category, topics in help_info.get("available_topics", {}).items():
        print(f"- {category.title()}: {', '.join(topics[:5])}")

    # Example 7: Budget Information
    print_section("7. Budget Setup Information")

    budget_info = tool.get_campaign_setup_info("budget")
    print("Budget Types:", ", ".join(budget_info.get("information", {}).get("budget_types", [])))
    print("Best Practices:")
    for practice in budget_info.get("information", {}).get("best_practices", [])[:3]:
        print(f"- {practice}")

    print_section("Demo Complete")
    print("The Google Ads Reference Tool provides comprehensive information")
    print("about campaign setup, bidding strategies, targeting, and best practices")
    print("based on official Google Ads documentation.")

if __name__ == "__main__":
    main()