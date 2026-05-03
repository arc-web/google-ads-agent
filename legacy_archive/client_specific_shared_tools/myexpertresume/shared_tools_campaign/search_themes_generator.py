#!/usr/bin/env python3
"""
Search Themes Generator for MyExpertResume PMAX Campaigns

Generates comprehensive search themes following the structure:
1. Core themes: (industry) + (service)
2. Long-tail themes: (industry) + (service) + (region)

Creates 50 search themes per asset group with systematic coverage.
"""

from typing import List, Dict, Set
import json
from dataclasses import dataclass

@dataclass
class SearchThemeConfig:
    """Configuration for search theme generation"""
    industries: List[str]
    services: List[str]
    regions: List[str]
    max_themes_per_group: int = 10

class SearchThemesGenerator:
    """Generates comprehensive search themes for PMAX campaigns"""

    def __init__(self):
        self.config = SearchThemeConfig(
            industries=[
                "Executive", "C-Suite", "Leadership", "VP", "Director",
                "Senior Management", "Professional", "Career Advancement",
                "Job Search", "Management", "Corporate", "Business",
                "Entrepreneur", "Startup", "Fortune 500"
            ],
            services=[
                "Resume Writing Service", "Resume Writing", "Resume Services",
                "Career Coaching", "Resume Help", "CV Writing Service",
                "Professional Resume", "Executive Resume", "Career Services",
                "Job Search Help", "Career Advancement", "Resume Optimization"
            ],
            regions=[
                "Fort Lauderdale", "Ft Lauderdale", "Miami", "West Palm Beach",
                "Tampa", "Orlando", "Jacksonville", "Atlanta", "New York",
                "Chicago", "Dallas", "Houston", "Los Angeles", "San Francisco",
                "Boston", "Washington DC", "Philadelphia", "Detroit", "Cleveland",
                "Pittsburgh", "Baltimore", "Richmond", "Charlotte", "Nashville",
                "Memphis", "New Orleans", "Austin", "Denver", "Phoenix",
                "Las Vegas", "Seattle", "Portland", "Minneapolis", "Milwaukee",
                "Kansas City", "Omaha", "Oklahoma City", "Tulsa", "Albuquerque",
                "Salt Lake City", "Boise", "Spokane", "Tacoma", "Vancouver WA"
            ]
        )

    def generate_core_themes(self) -> List[str]:
        """Generate core themes: (industry) + (service)"""
        themes = []

        # Primary executive focus
        executive_services = [
            "Executive Resume Writing Service",
            "C-Suite Resume Writing Service",
            "Leadership Resume Writing Service",
            "VP Resume Writing Service",
            "Director Resume Writing Service",
            "Senior Management Resume Writing",
            "Executive Career Coaching",
            "Executive Job Search Help",
            "Executive Resume Optimization",
            "Executive CV Writing Service"
        ]
        themes.extend(executive_services)

        # Professional services
        professional_services = [
            "Professional Resume Writing Service",
            "Career Advancement Resume Service",
            "Corporate Resume Writing",
            "Business Resume Services",
            "Professional Career Coaching",
            "Job Search Resume Services",
            "Resume Writing Help",
            "Professional CV Services",
            "Career Development Services",
            "Executive Resume Help"
        ]
        themes.extend(professional_services)

        # Remove duplicates and limit to core set
        return list(set(themes))[:20]

    def generate_regional_themes(self) -> List[str]:
        """Generate regional themes: (industry) + (service) + (region)"""
        themes = []

        # Core combinations with regions
        core_combinations = [
            "Executive Resume Writing Service",
            "C-Suite Resume Writing Service",
            "Professional Resume Writing Service",
            "Leadership Resume Writing Service",
            "Career Coaching Service"
        ]

        # Florida focus (primary market)
        florida_regions = [
            "Fort Lauderdale", "Ft Lauderdale", "Miami", "West Palm Beach",
            "Tampa", "Orlando", "Jacksonville", "Tallahassee", "Sarasota",
            "Naples", "Key West", "St Petersburg", "Clearwater", "Gainesville"
        ]

        # Major US cities
        major_cities = [
            "New York", "Chicago", "Dallas", "Houston", "Los Angeles",
            "San Francisco", "Boston", "Washington DC", "Philadelphia",
            "Atlanta", "Phoenix", "Denver", "Seattle", "Portland"
        ]

        # Generate regional themes
        for service in core_combinations:
            # Florida regions (higher priority)
            for region in florida_regions[:8]:  # Limit to top Florida markets
                theme = f"{service} {region}"
                themes.append(theme)

            # Major cities (secondary priority)
            for region in major_cities[:6]:  # Limit to top national markets
                theme = f"{service} {region}"
                themes.append(theme)

        return themes[:30]  # Limit to 30 regional themes

    def generate_all_themes(self) -> Dict[str, List[str]]:
        """Generate complete set of 50 search themes organized by priority"""
        core_themes = self.generate_core_themes()
        regional_themes = self.generate_regional_themes()

        # Combine and organize by priority
        all_themes = {
            "core_exact_match": core_themes[:10],  # Most important - exact matches
            "core_expanded": core_themes[10:20],  # Secondary core
            "regional_primary": regional_themes[:15],  # Florida + major cities
            "regional_secondary": regional_themes[15:25],  # Additional regional
            "regional_tertiary": regional_themes[25:30]  # Long-tail regional
        }

        return all_themes

    def create_asset_group_theme_sets(self) -> List[Dict[str, List[str]]]:
        """Create multiple asset groups, each with 10 search themes"""
        all_themes = self.generate_all_themes()

        asset_groups = []

        # Asset Group 1: Core Executive Focus
        asset_groups.append({
            "name": "Executive_Core",
            "themes": all_themes["core_exact_match"] + all_themes["regional_primary"][:0]  # Just core for now
        })

        # Asset Group 2: C-Suite Focus
        asset_groups.append({
            "name": "C_Suite_Focus",
            "themes": [
                "C-Suite Resume Writing Service",
                "Executive Resume Writing Service",
                "CEO Resume Writing Service",
                "C-Suite Career Coaching",
                "Executive Leadership Resume",
                "Senior Executive Resume Service",
                "C-Level Resume Writing",
                "Executive CV Writing Service",
                "C-Suite Job Search Help",
                "Executive Career Advancement"
            ]
        })

        # Asset Group 3: Regional Florida Focus
        florida_themes = [
            "Executive Resume Writing Service Fort Lauderdale",
            "Executive Resume Writing Service Miami",
            "Professional Resume Writing Service Florida",
            "Career Coaching Fort Lauderdale",
            "Executive Resume Service West Palm Beach",
            "Resume Writing Service Tampa",
            "C-Suite Resume Writing Orlando",
            "Professional Resume Help Jacksonville",
            "Executive Career Coaching Miami",
            "Resume Services Fort Lauderdale"
        ]
        asset_groups.append({
            "name": "Florida_Regional",
            "themes": florida_themes
        })

        # Asset Group 4: National Executive Focus
        national_themes = [
            "Executive Resume Writing Service New York",
            "Executive Resume Writing Service Chicago",
            "C-Suite Resume Writing Service Atlanta",
            "Professional Resume Service Los Angeles",
            "Executive Career Coaching Boston",
            "Resume Writing Service Washington DC",
            "Leadership Resume Service Dallas",
            "Executive Resume Help Houston",
            "Professional Resume Writing San Francisco",
            "Career Coaching Service Philadelphia"
        ]
        asset_groups.append({
            "name": "National_Executive",
            "themes": national_themes
        })

        # Asset Group 5: Career Advancement Focus
        advancement_themes = [
            "Career Advancement Resume Service",
            "Professional Development Resume",
            "Job Search Resume Help",
            "Career Transition Resume Writing",
            "Executive Career Coaching",
            "Professional Resume Optimization",
            "Career Growth Resume Service",
            "Job Advancement Resume Help",
            "Professional Career Services",
            "Executive Job Search Coaching"
        ]
        asset_groups.append({
            "name": "Career_Advancement",
            "themes": advancement_themes
        })

        return asset_groups

    def export_for_campaign_plan(self) -> str:
        """Export themes in format ready for campaign_plan.py"""
        asset_groups = self.create_asset_group_theme_sets()

        output = []
        for i, ag in enumerate(asset_groups, 1):
            output.append(f"                # Asset Group {i}: {ag['name'].replace('_', ' ')}")
            output.append("                {")

            # Add themes
            output.append('                    "search_themes": [')
            for theme in ag['themes']:
                output.append(f'                        "{theme}",')
            output.append('                    ],')

            # Add other asset group fields (placeholder)
            output.append('                    # ... other asset group fields ...')
            output.append("                },")
            output.append("")

        return "\n".join(output)

def main():
    generator = SearchThemesGenerator()

    print("🎯 SEARCH THEMES GENERATOR - MyExpertResume")
    print("=" * 50)

    # Generate all themes
    all_themes = generator.generate_all_themes()

    print(f"📊 THEME GENERATION SUMMARY:")
    for category, themes in all_themes.items():
        print(f"   {category}: {len(themes)} themes")

    total_themes = sum(len(themes) for themes in all_themes.values())
    print(f"   TOTAL: {total_themes} themes generated")
    print()

    # Create asset group sets
    asset_groups = generator.create_asset_group_theme_sets()

    print(f"🎯 ASSET GROUP CONFIGURATION ({len(asset_groups)} groups):")
    for i, ag in enumerate(asset_groups, 1):
        print(f"   Group {i}: {ag['name']} - {len(ag['themes'])} themes")

    print()
    print("📋 SAMPLE THEMES BY GROUP:")

    for i, ag in enumerate(asset_groups, 1):
        print(f"\n   {ag['name']} ({len(ag['themes'])} themes):")
        for theme in ag['themes'][:3]:  # Show first 3
            print(f"     • {theme}")
        if len(ag['themes']) > 3:
            print(f"     • ... and {len(ag['themes']) - 3} more")

    print()
    print("💡 THEME STRUCTURE:")
    print("   1. Core themes: (industry) + (service)")
    print("   2. Regional themes: (industry) + (service) + (region)")
    print("   3. Priority: Florida focus → National expansion")
    print()

    # Export format for campaign plan
    print("📄 CAMPAIGN PLAN INTEGRATION:")
    print("   Ready to integrate into campaign_plan.py")
    print("   Each asset group gets 10 optimized search themes")

if __name__ == "__main__":
    main()
