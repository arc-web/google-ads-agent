#!/usr/bin/env python3
"""
Search Term Report (STR) Keyword Analyzer

Analyzes Google Ads Search Term Reports to identify keywords that should be added
to ad groups. Filters for search terms marked as "None" (not yet added) and creates
a CSV file ready for Google Ads Editor upload.

Usage:
    python str_keyword_analyzer.py --str-file path/to/str.csv --output keywords_to_add.csv
"""

import csv
import argparse
import sys
from collections import defaultdict
from typing import Dict, List, Tuple


class STRKeywordAnalyzer:
    """Analyzes STR data to identify keywords to add"""

    def __init__(self):
        self.keywords_to_add = defaultdict(list)  # (campaign, ad_group) -> [keywords]
        self.conversion_keywords = []  # Keywords with conversions

    def analyze_str_file(self, str_file_path: str) -> Dict:
        """Analyze STR file and identify keywords to add"""
        
        results = {
            'total_rows': 0,
            'none_rows': 0,
            'converting_keywords': [],
            'keywords_by_ad_group': defaultdict(list),
            'summary': {}
        }

        with open(str_file_path, 'r', encoding='utf-8-sig') as f:
            # Skip first two header rows
            next(f)  # Skip "ARC - Accounts - STR (Last 7 Days)"
            next(f)  # Skip date row
            
            reader = csv.DictReader(f)
            
            for row in reader:
                results['total_rows'] += 1
                
                # Skip empty rows
                if not row.get('Campaign') or not row.get('Search term'):
                    continue
                
                added_excluded = row.get('Added/Excluded', '').strip()
                
                # Focus on "None" - search terms that triggered but weren't added
                if added_excluded == 'None':
                    results['none_rows'] += 1
                    
                    campaign = row.get('Campaign', '').strip()
                    ad_group = row.get('Ad group', '').strip()
                    search_term = row.get('Search term', '').strip().lower()
                    search_keyword = row.get('Search keyword', '').strip()
                    match_type = row.get('Search keyword match type', '').strip()
                    
                    # Get performance metrics
                    try:
                        clicks = int(row.get('Clicks', '0') or '0')
                        cost = float(row.get('Cost', '0') or '0')
                        conversions = float(row.get('All conv.', '0') or '0')
                        ctr = float(row.get('CTR', '0%').replace('%', '') or '0')
                    except (ValueError, AttributeError):
                        clicks = 0
                        cost = 0.0
                        conversions = 0.0
                        ctr = 0.0
                    
                    # Skip if no search term
                    if not search_term:
                        continue
                    
                    # Determine appropriate match type
                    # Use phrase match for most, exact match for high-converting terms
                    recommended_match = 'Phrase'
                    if conversions > 0 and clicks > 0:
                        recommended_match = 'Exact'  # High-value converting terms
                    elif 'near me' in search_term or 'scottsdale' in search_term:
                        recommended_match = 'Phrase'  # Location-based
                    else:
                        recommended_match = 'Phrase'
                    
                    keyword_data = {
                        'search_term': search_term,
                        'campaign': campaign,
                        'ad_group': ad_group,
                        'original_keyword': search_keyword,
                        'original_match_type': match_type,
                        'recommended_match': recommended_match,
                        'clicks': clicks,
                        'cost': cost,
                        'conversions': conversions,
                        'ctr': ctr
                    }
                    
                    key = (campaign, ad_group)
                    results['keywords_by_ad_group'][key].append(keyword_data)
                    
                    if conversions > 0:
                        results['converting_keywords'].append(keyword_data)
        
        # Generate summary
        results['summary'] = {
            'total_ad_groups': len(results['keywords_by_ad_group']),
            'total_keywords_to_add': sum(len(kwds) for kwds in results['keywords_by_ad_group'].values()),
            'converting_keywords_count': len(results['converting_keywords'])
        }
        
        return results

    def generate_keyword_csv(self, analysis_results: Dict, output_path: str):
        """
        Generate CSV file with keywords to add in CORRECTED Google Ads Editor format

        CRITICAL FIX: Keywords are placed in Ad Group rows, not separate rows.
        This matches the official Google Ads Editor CSV specification.
        """
        from collections import defaultdict

        # Group keywords by ad group to avoid duplicates
        ad_group_keywords = defaultdict(list)

        for (campaign, ad_group), keywords in analysis_results['keywords_by_ad_group'].items():
            # Deduplicate keywords and prioritize converting ones
            keyword_map = {}  # search_term -> best keyword_data

            for kw_data in keywords:
                search_term = kw_data['search_term']

                # If we've seen this term, keep the one with conversions or more clicks
                if search_term in keyword_map:
                    existing = keyword_map[search_term]
                    # Prefer keyword with conversions
                    if kw_data['conversions'] > existing['conversions']:
                        keyword_map[search_term] = kw_data
                        # If converting, prefer Exact match
                        if kw_data['conversions'] > 0:
                            kw_data['recommended_match'] = 'Exact'
                    # Or prefer keyword with more clicks
                    elif kw_data['conversions'] == existing['conversions'] and kw_data['clicks'] > existing['clicks']:
                        keyword_map[search_term] = kw_data
                else:
                    keyword_map[search_term] = kw_data

            # Store deduplicated keywords for this ad group
            ad_group_keywords[(campaign, ad_group)] = list(keyword_map.values())

        # Google Ads Editor format: Keywords in Ad Group rows (not separate rows)
        rows = []

        for (campaign, ad_group), keywords in ad_group_keywords.items():
            # CORRECTED: Create Ad Group rows with keywords included
            # Each ad group gets one row with keyword data
            if keywords:
                # Use the best performing keyword for this ad group
                best_keyword = max(keywords, key=lambda k: (k['conversions'], k['clicks']))

                # Determine match type
                match_type = best_keyword['recommended_match']
                if match_type == 'Exact':
                    criterion_type = 'Exact'
                elif match_type == 'Phrase':
                    criterion_type = 'Phrase'
                else:
                    criterion_type = 'Broad'

                # CORRECTED FORMAT: Keyword in Ad Group row (Google Ads Editor spec)
                row = {
                    'Campaign': campaign,
                    'Ad Group': ad_group,
                    'Status': 'Enabled',  # Ad groups with keywords are enabled
                    'Campaign Type': 'Search',  # Required for Google Ads Editor
                    'Sub Type': 'Standard',  # Required for Google Ads Editor
                    'Networks': 'Search',  # Required for Google Ads Editor
                    'Search Partners': 'Disabled',  # Required for Google Ads Editor
                    'Display Network': 'Disabled',  # Required for Google Ads Editor
                    'Targeting': 'Geographic + Keyword',  # Required for Google Ads Editor
                    'Ad Schedule': 'Monday-Saturday 8AM-6PM',
                    'Budget': '',  # Leave empty - managed at campaign level
                    'Labels': f'{campaign.split()[-1]} County|STR Added',  # Dynamic labels
                    'Campaign Bid Strategy Type': '',  # Use campaign default
                    'Ad Group Bid Strategy Type': 'Manual CPC',  # Default for new keywords
                    'Ad Group Bid Strategy Name': 'Manual CPC - STR Keywords',
                    'Target CPA': '',
                    'Max CPC': '3.00',  # Conservative default
                    'Enhanced CPC': 'Disabled',
                    'EU Political Content': 'Disabled',  # Required for Google Ads Editor
                    'Keyword': best_keyword['search_term'],  # KEYWORD IN AD GROUP ROW
                    'Criterion Type': criterion_type,  # Match type in same row
                    'Final URL': '',  # Leave empty for manual entry
                    'Geographic Targeting': '',  # Leave empty for ad group targeting
                    'City Targeting': '',  # Leave empty for ad group targeting
                    'ZIP Code Targeting': '',  # Leave empty for ad group targeting
                    'Regional Targeting': '',  # Leave empty for ad group targeting
                    'Service Category': '',
                    'Priority Level': 'Medium',
                    'Conversion Actions': 'Website Quotes + Phone Calls',
                    'Ad Group Labels': f'STR Added|{best_keyword["conversions"]} conv'
                }

                rows.append(row)

        # Write CSV with corrected fieldnames
        fieldnames = [
            'Campaign', 'Ad Group', 'Status', 'Campaign Type', 'Sub Type', 'Networks',
            'Search Partners', 'Display Network', 'Targeting', 'Ad Schedule', 'Budget',
            'Labels', 'Campaign Bid Strategy Type', 'Ad Group Bid Strategy Type',
            'Ad Group Bid Strategy Name', 'Target CPA', 'Max CPC', 'Enhanced CPC',
            'EU Political Content', 'Keyword', 'Criterion Type', 'Final URL',
            'Geographic Targeting', 'City Targeting', 'ZIP Code Targeting',
            'Regional Targeting', 'Service Category', 'Priority Level',
            'Conversion Actions', 'Ad Group Labels'
        ]

        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return len(rows)

    def print_analysis_summary(self, analysis_results: Dict):
        """Print summary of analysis"""
        
        print("\n" + "="*70)
        print("SEARCH TERM REPORT ANALYSIS SUMMARY")
        print("="*70)
        print(f"Total rows analyzed: {analysis_results['total_rows']}")
        print(f"Search terms not yet added (None): {analysis_results['none_rows']}")
        print(f"Ad groups with new keywords: {analysis_results['summary']['total_ad_groups']}")
        print(f"Total keywords to add: {analysis_results['summary']['total_keywords_to_add']}")
        print(f"Keywords with conversions: {analysis_results['summary']['converting_keywords_count']}")
        
        print("\n" + "-"*70)
        print("TOP CONVERTING KEYWORDS TO ADD:")
        print("-"*70)
        
        # Sort by conversions, then by clicks
        converting = sorted(
            analysis_results['converting_keywords'],
            key=lambda x: (x['conversions'], x['clicks']),
            reverse=True
        )
        
        for i, kw in enumerate(converting[:10], 1):
            print(f"{i}. {kw['search_term']}")
            print(f"   Campaign: {kw['campaign']} | Ad Group: {kw['ad_group']}")
            print(f"   Conversions: {kw['conversions']} | Clicks: {kw['clicks']} | Cost: ${kw['cost']:.2f}")
            print()
        
        print("\n" + "-"*70)
        print("KEYWORDS BY AD GROUP:")
        print("-"*70)
        
        for (campaign, ad_group), keywords in sorted(analysis_results['keywords_by_ad_group'].items()):
            print(f"\n{campaign} > {ad_group}: {len(keywords)} keywords")
            # Show first 5 keywords
            for kw in keywords[:5]:
                match_indicator = "🔴 EXACT" if kw['recommended_match'] == 'Exact' else "🟡 PHRASE"
                conv_indicator = f" ({kw['conversions']} conv)" if kw['conversions'] > 0 else ""
                print(f"  {match_indicator} {kw['search_term']}{conv_indicator}")
            if len(keywords) > 5:
                print(f"  ... and {len(keywords) - 5} more")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze STR file and generate keywords CSV for Google Ads Editor'
    )
    parser.add_argument(
        '--str-file',
        required=True,
        help='Path to Search Term Report CSV file'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Output CSV file path for keywords'
    )
    parser.add_argument(
        '--min-clicks',
        type=int,
        default=0,
        help='Minimum clicks to include keyword (default: 0)'
    )
    parser.add_argument(
        '--min-conversions',
        type=float,
        default=0.0,
        help='Minimum conversions to include keyword (default: 0.0)'
    )
    
    args = parser.parse_args()
    
    analyzer = STRKeywordAnalyzer()
    
    print(f"📊 Analyzing STR file: {args.str_file}")
    analysis_results = analyzer.analyze_str_file(args.str_file)
    
    # Filter keywords based on criteria
    if args.min_clicks > 0 or args.min_conversions > 0:
        filtered_keywords = defaultdict(list)
        for (campaign, ad_group), keywords in analysis_results['keywords_by_ad_group'].items():
            for kw in keywords:
                if kw['clicks'] >= args.min_clicks and kw['conversions'] >= args.min_conversions:
                    filtered_keywords[(campaign, ad_group)].append(kw)
        analysis_results['keywords_by_ad_group'] = filtered_keywords
        analysis_results['summary']['total_keywords_to_add'] = sum(
            len(kwds) for kwds in filtered_keywords.values()
        )
    
    # Print summary
    analyzer.print_analysis_summary(analysis_results)
    
    # Generate CSV
    print(f"\n📝 Generating keyword CSV: {args.output}")
    keyword_count = analyzer.generate_keyword_csv(analysis_results, args.output)
    
    print(f"\n✅ Success! Generated CSV with {keyword_count} keywords")
    print(f"📁 File saved to: {args.output}")
    print("\n💡 Next steps:")
    print("   1. Review the keywords in the CSV")
    print("   2. Import into Google Ads Editor")
    print("   3. Review and post changes to your account")


if __name__ == "__main__":
    main()
