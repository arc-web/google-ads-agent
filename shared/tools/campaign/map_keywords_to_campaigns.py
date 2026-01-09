#!/usr/bin/env python3
"""
Map Keywords to Campaign Structure

Reads the Google Ads Editor CSV export and maps keywords from STR analysis
to the correct campaigns and ad groups, creating a new CSV ready for upload.

Usage:
    python map_keywords_to_campaigns.py --campaign-csv path/to/campaigns.csv --keywords-csv path/to/keywords.csv --output mapped_keywords.csv
"""

import csv
import argparse
import sys
from collections import defaultdict
from typing import Dict, List, Set, Tuple


def read_campaign_structure(campaign_csv_path: str) -> Dict[Tuple[str, str], Dict]:
    """
    Read campaign structure CSV and extract unique campaigns and ad groups
    Returns: {(campaign, ad_group): {metadata}}
    """
    campaigns = {}
    ad_groups = {}
    
    # Try different encodings
    encodings = ['utf-16-le', 'utf-16-be', 'utf-8-sig', 'utf-8', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(campaign_csv_path, 'r', encoding=encoding) as f:
                # Read first line to detect delimiter
                first_line = f.readline()
                delimiter = '\t' if '\t' in first_line else ','
                f.seek(0)
                
                reader = csv.DictReader(f, delimiter=delimiter)
                
                for row in reader:
                    campaign = row.get('Campaign', '').strip()
                    ad_group = row.get('Ad Group', '').strip()
                    
                    if not campaign or not ad_group:
                        continue
                    
                    key = (campaign, ad_group)
                    
                    # Store campaign-level info
                    if campaign not in campaigns:
                        campaigns[campaign] = {
                            'campaign_type': row.get('Campaign Type', '').strip(),
                            'budget': row.get('Budget', '').strip(),
                            'networks': row.get('Networks', '').strip(),
                        }
                    
                    # Store ad group info
                    if key not in ad_groups:
                        ad_groups[key] = {
                            'max_cpc': row.get('Max CPC', '').strip(),
                            'campaign': campaign,
                            'ad_group': ad_group,
                        }
                
                print(f"✅ Successfully read campaign structure with {encoding} encoding")
                print(f"   Found {len(campaigns)} campaigns and {len(ad_groups)} ad groups")
                break
                
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"⚠️  Error with {encoding}: {e}")
            continue
    
    return ad_groups, campaigns


def read_keywords_csv(keywords_csv_path: str) -> List[Dict]:
    """Read keywords CSV from STR analysis"""
    keywords = []
    
    with open(keywords_csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            keywords.append({
                'campaign': row.get('Campaign', '').strip(),
                'ad_group': row.get('Ad Group', '').strip(),
                'keyword': row.get('Keyword', '').strip(),
                'criterion_type': row.get('Criterion Type', '').strip(),
            })
    
    return keywords


def map_keywords_to_structure(
    keywords: List[Dict],
    ad_groups: Dict[Tuple[str, str], Dict],
    campaigns: Dict[str, Dict]
) -> List[Dict]:
    """
    Map keywords to actual campaign structure, handling name variations
    """
    mapped_keywords = []
    unmapped = []
    
    # Create mapping from STR campaign/ad group names to actual names
    # Handle variations like "TPPC - Regional - Medspas" vs "TPPC - Regional - Medspas"
    campaign_mapping = {}
    ad_group_mapping = {}
    
    # Build mappings
    for (actual_campaign, actual_ad_group), metadata in ad_groups.items():
        # Normalize names for matching
        normalized_campaign = actual_campaign.lower().strip()
        normalized_ad_group = actual_ad_group.lower().strip()
        
        campaign_mapping[normalized_campaign] = actual_campaign
        ad_group_mapping[(normalized_campaign, normalized_ad_group)] = (actual_campaign, actual_ad_group)
    
    # Map keywords
    for kw in keywords:
        kw_campaign = kw['campaign'].strip()
        kw_ad_group = kw['ad_group'].strip()
        
        # Try exact match first
        key = (kw_campaign, kw_ad_group)
        if key in ad_groups:
            # Leave Max CPC empty to use ad group default bid strategy
            mapped_keywords.append({
                'Campaign': kw_campaign,
                'Ad Group': kw_ad_group,
                'Keyword': kw['keyword'],
                'Criterion Type': kw['criterion_type'],
                'Status': 'Enabled',
                'Max CPC': '',  # Empty to use ad group default
            })
        else:
            # Try normalized match
            normalized_campaign = kw_campaign.lower().strip()
            normalized_ad_group = kw_ad_group.lower().strip()
            normalized_key = (normalized_campaign, normalized_ad_group)
            
            if normalized_key in ad_group_mapping:
                actual_campaign, actual_ad_group = ad_group_mapping[normalized_key]
                actual_key = (actual_campaign, actual_ad_group)
                mapped_keywords.append({
                    'Campaign': actual_campaign,
                    'Ad Group': actual_ad_group,
                    'Keyword': kw['keyword'],
                    'Criterion Type': kw['criterion_type'],
                    'Status': 'Enabled',
                    'Max CPC': '',  # Empty to use ad group default
                })
            else:
                unmapped.append((kw_campaign, kw_ad_group, kw['keyword']))
    
    return mapped_keywords, unmapped


def generate_google_ads_editor_csv(
    mapped_keywords: List[Dict],
    output_path: str,
    ad_groups: Dict[Tuple[str, str], Dict]
):
    """Generate CSV in Google Ads Editor format"""
    
    # Get all fieldnames from a sample row structure
    # Google Ads Editor format requires specific columns
    fieldnames = [
        'Campaign',
        'Ad Group',
        'Keyword',
        'Criterion Type',
        'Status',
        'Max CPC',
        'Final URL',
        'Final mobile URL',
        'Tracking template',
        'Custom parameters',
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for kw in mapped_keywords:
            row = {
                'Campaign': kw['Campaign'],
                'Ad Group': kw['Ad Group'],
                'Keyword': kw['Keyword'],
                'Criterion Type': kw['Criterion Type'],
                'Status': kw.get('Status', 'Enabled'),
                'Max CPC': kw.get('Max CPC', ''),
                'Final URL': '',
                'Final mobile URL': '',
                'Tracking template': '',
                'Custom parameters': '',
            }
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(
        description='Map keywords from STR analysis to actual campaign structure'
    )
    parser.add_argument(
        '--campaign-csv',
        required=True,
        help='Path to Google Ads Editor campaign structure CSV'
    )
    parser.add_argument(
        '--keywords-csv',
        required=True,
        help='Path to keywords CSV from STR analysis'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output CSV file path'
    )
    
    args = parser.parse_args()
    
    print("📊 Reading campaign structure...")
    ad_groups, campaigns = read_campaign_structure(args.campaign_csv)
    
    if not ad_groups:
        print("❌ Error: Could not read campaign structure CSV")
        sys.exit(1)
    
    print("\n📋 Campaigns found:")
    for campaign in sorted(campaigns.keys()):
        print(f"  - {campaign}")
    
    print("\n📁 Ad Groups found:")
    for (campaign, ad_group) in sorted(ad_groups.keys()):
        print(f"  {campaign} > {ad_group}")
    
    print(f"\n🔍 Reading keywords from STR analysis...")
    keywords = read_keywords_csv(args.keywords_csv)
    print(f"   Found {len(keywords)} keywords to map")
    
    print(f"\n🔗 Mapping keywords to campaign structure...")
    mapped_keywords, unmapped = map_keywords_to_structure(keywords, ad_groups, campaigns)
    
    print(f"✅ Successfully mapped {len(mapped_keywords)} keywords")
    
    if unmapped:
        print(f"\n⚠️  {len(unmapped)} keywords could not be mapped:")
        for campaign, ad_group, keyword in unmapped[:10]:
            print(f"   {campaign} > {ad_group}: {keyword}")
        if len(unmapped) > 10:
            print(f"   ... and {len(unmapped) - 10} more")
    
    print(f"\n📝 Generating Google Ads Editor CSV...")
    generate_google_ads_editor_csv(mapped_keywords, args.output, ad_groups)
    
    print(f"✅ Success! Generated CSV with {len(mapped_keywords)} keywords")
    print(f"📁 File saved to: {args.output}")
    print("\n💡 Next steps:")
    print("   1. Review the mapped keywords CSV")
    print("   2. Import into Google Ads Editor")
    print("   3. Review and post changes to your account")


if __name__ == "__main__":
    main()
