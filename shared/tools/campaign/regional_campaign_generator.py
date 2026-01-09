#!/usr/bin/env python3
"""
Regional Campaign Generator for EvoRestore

Generates Google Ads CSV files with proper regional targeting based on website scraping
and client service areas.

Usage:
    python regional_campaign_generator.py --client evorestore --output campaigns.csv
"""

import argparse
import csv
import sys
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class RegionalCampaignGenerator:
    """Generates campaign CSVs with proper regional targeting"""

    def __init__(self, client_config: Dict[str, Any]):
        self.client_config = client_config
        self.service_areas = []

    def scrape_service_areas(self, website_url: str) -> List[str]:
        """
        Scrape website to identify service areas/cities
        Returns list of cities/regions for targeting
        """
        try:
            response = requests.get(website_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for common patterns in service area listings
            cities = []

            # Check navigation menus for city links
            nav_links = soup.find_all('a', href=True)
            for link in nav_links:
                href = link.get('href', '').lower()
                text = link.get_text().strip()

                # Look for city patterns in URLs and link text
                city_indicators = ['az', 'arizona']
                if any(indicator in href or indicator in text.lower() for indicator in city_indicators):
                    # Extract city names
                    if 'scottsdale' in text.lower() or 'scottsdale' in href:
                        cities.append('Scottsdale, AZ')
                    elif 'phoenix' in text.lower() or 'phoenix' in href:
                        cities.append('Phoenix, AZ')
                    elif 'mesa' in text.lower() or 'mesa' in href:
                        cities.append('Mesa, AZ')
                    elif 'chandler' in text.lower() or 'chandler' in href:
                        cities.append('Chandler, AZ')
                    elif 'tucson' in text.lower() or 'tucson' in href:
                        cities.append('Tucson, AZ')

            # Remove duplicates and return
            return list(set(cities))

        except Exception as e:
            print(f"Error scraping service areas: {e}")
            # Fallback to known service areas from config
            return self.client_config.get('known_service_areas', [])

    def create_campaign_csv(self, service_areas: List[str], output_path: str):
        """Create CSV with regional targeting for each service area"""

        # Define all possible field names that might be used
        all_fieldnames = [
            'Campaign', 'Campaign Type', 'Networks', 'Budget', 'Budget type',
            'EU political ads', 'Standard conversion goals', 'Customer acquisition', 'Languages',
            'Bid Strategy Type', 'Target CPA', 'Max CPC', 'Ad Schedule', 'Ad rotation',
            'Targeting method', 'Exclusion method', 'Brand guidelines', 'Final URL expansion',
            'Image enhancement', 'Image generation', 'Video enhancement', 'Campaign Status',
            'Location', 'Reach', 'Location groups', 'Radius', 'Unit', 'Bid Modifier'
        ]

        campaigns = []

        # Emergency Services Campaign (highest priority)
        emergency_campaign = {
            'Campaign': f"{self.client_config['name']} Emergency Services PMAX",
            'Campaign Type': 'Performance Max',
            'Networks': 'Google search;Search Partners',
            'Budget': '150.00',
            'Budget type': 'Daily',
            'EU political ads': "Doesn't have EU political ads",
            'Standard conversion goals': 'Account-level',
            'Customer acquisition': 'Bid equally',
            'Languages': 'en',
            'Bid Strategy Type': 'Maximize conversions',
            'Target CPA': '40.00',
            'Ad Schedule': '(Monday[00:00-23:59]);(Tuesday[00:00-23:59]);(Wednesday[00:00-23:59]);(Thursday[00:00-23:59]);(Friday[00:00-23:59]);(Saturday[00:00-23:59]);(Sunday[00:00-23:59])',
            'Ad rotation': 'Optimize for clicks',
            'Targeting method': 'Location of presence or Area of interest',
            'Exclusion method': 'Location of presence',
            'Brand guidelines': 'Disabled',
            'Final URL expansion': 'Enabled',
            'Image enhancement': 'Enabled',
            'Image generation': 'Disabled',
            'Video enhancement': 'Enabled',
            'Campaign Status': 'Enabled'
        }
        campaigns.append(emergency_campaign)

        # Add regional targeting rows for emergency services
        for city in service_areas:
            location_row = {
                'Campaign': f"{self.client_config['name']} Emergency Services PMAX",
                'Location': city,
                'Reach': '',
                'Location groups': '',
                'Radius': '25',
                'Unit': 'miles',
                'Bid Modifier': '0'
            }
            campaigns.append(location_row)

        # Add other service campaigns with regional targeting
        services = [
            ('Water Damage Restoration PMAX', '120.00'),
            ('Fire Damage Restoration PMAX', '100.00'),
            ('Mold Remediation Search', '80.00'),
            ('Storm Damage PMAX', '90.00')
        ]

        for service_name, budget in services:
            campaign = {
                'Campaign': f"{self.client_config['name']} {service_name}",
                'Campaign Type': 'Performance Max' if 'PMAX' in service_name else 'Search',
                'Networks': 'Google search;Search Partners',
                'Budget': budget,
                'Budget type': 'Daily',
                'EU political ads': "Doesn't have EU political ads",
                'Standard conversion goals': 'Account-level',
                'Customer acquisition': 'Bid equally',
                'Languages': 'en',
                'Bid Strategy Type': 'Maximize conversions' if 'PMAX' in service_name else 'Manual CPC',
                'Target CPA': '40.00' if 'PMAX' in service_name else '',
                'Max CPC': '2.50' if 'Search' in service_name else '',
                'Ad Schedule': '(Monday[00:00-23:59]);(Tuesday[00:00-23:59]);(Wednesday[00:00-23:59]);(Thursday[00:00-23:59]);(Friday[00:00-23:59]);(Saturday[00:00-23:59]);(Sunday[00:00-23:59])',
                'Ad rotation': 'Optimize for clicks',
                'Targeting method': 'Location of presence or Area of interest',
                'Exclusion method': 'Location of presence',
                'Brand guidelines': 'Disabled',
                'Final URL expansion': 'Enabled',
                'Image enhancement': 'Enabled',
                'Image generation': 'Disabled',
                'Video enhancement': 'Enabled',
                'Campaign Status': 'Enabled'
            }
            campaigns.append(campaign)

            # Add regional targeting for this campaign too
            for city in service_areas:
                location_row = {
                    'Campaign': f"{self.client_config['name']} {service_name}",
                    'Location': city,
                    'Reach': '',
                    'Location groups': '',
                    'Radius': '25',
                    'Unit': 'miles',
                    'Bid Modifier': '0'
                }
                campaigns.append(location_row)

        # Write to CSV with all possible fieldnames
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=all_fieldnames, extrasaction='ignore')
            writer.writeheader()
            for campaign in campaigns:
                # Fill missing fields with empty strings
                row = {field: campaign.get(field, '') for field in all_fieldnames}
                writer.writerow(row)

        print(f"✅ Generated campaign CSV with {len(service_areas)} service areas: {', '.join(service_areas)}")
        return len(campaigns)


def main():
    parser = argparse.ArgumentParser(description='Generate regional campaign CSVs')
    parser.add_argument('--client', required=True, help='Client name (e.g., evorestore)')
    parser.add_argument('--website', help='Client website URL')
    parser.add_argument('--output', required=True, help='Output CSV file path')
    parser.add_argument('--service-areas', nargs='*', help='Manual service areas (city, state)')

    args = parser.parse_args()

    # Client configurations
    client_configs = {
        'evorestore': {
            'name': 'EvoRestore',
            'website': 'https://evorestore.com/',
            'known_service_areas': ['Scottsdale, AZ', 'Phoenix, AZ', 'Mesa, AZ', 'Chandler, AZ', 'Tucson, AZ']
        }
    }

    if args.client not in client_configs:
        print(f"❌ Unknown client: {args.client}")
        sys.exit(1)

    config = client_configs[args.client]
    website_url = args.website or config['website']

    generator = RegionalCampaignGenerator(config)

    # Get service areas
    if args.service_areas:
        service_areas = args.service_areas
    else:
        print(f"🔍 Scraping service areas from {website_url}...")
        service_areas = generator.scrape_service_areas(website_url)

        if not service_areas:
            print("⚠️  No service areas found, using known areas from config")
            service_areas = config['known_service_areas']

    # Generate CSV
    print(f"📊 Generating campaigns for {len(service_areas)} service areas...")
    campaign_count = generator.create_campaign_csv(service_areas, args.output)

    print(f"✅ Success! Created {campaign_count} campaign entries in {args.output}")


if __name__ == "__main__":
    main()
