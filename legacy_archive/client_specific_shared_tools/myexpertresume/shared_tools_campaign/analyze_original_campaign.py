#!/usr/bin/env python3
"""
Analyze the original Google Ads Editor CSV campaign structure
"""

import csv
from collections import defaultdict

def clean_text(text):
    """Clean encoding issues from text"""
    if not text:
        return ""
    return text.replace('\x00', '').strip()

def analyze_campaign():
    """Analyze the original campaign structure"""
    print("=== ORIGINAL CAMPAIGN ANALYSIS ===")
    print("=" * 50)

    # Read the CSV
    with open('MyExpertResume.com+ARC PMAX+23_Asset groups+2025-12-05.csv', 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f, delimiter='\t')
        headers = reader.fieldnames

        # Get campaign info from first data row
        first_row = next(reader)

        print("📊 CAMPAIGN OVERVIEW:")
        print(f"   Campaign Name: {clean_text(first_row.get('Campaign', ''))}")
        print(f"   Campaign Type: {clean_text(first_row.get('Campaign Type', ''))}")
        print(f"   Budget: ${first_row.get('Budget', '')} {clean_text(first_row.get('Budget type', ''))}")
        print(f"   Business Name: {clean_text(first_row.get('Brand business name', ''))}")
        print(f"   Brand Font: {clean_text(first_row.get('Brand font', ''))}")
        print(f"   Final URL: {clean_text(first_row.get('Final URL', ''))}")
        print(f"   Custom Parameters: {clean_text(first_row.get('Custom parameters', ''))}")
        print(f"   Networks: {clean_text(first_row.get('Networks', ''))}")
        print(f"   Bid Strategy: {clean_text(first_row.get('Bid Strategy Type', ''))}")
        print()

        # Reset file pointer to analyze asset groups
        f.seek(0)
        reader = csv.DictReader(f, delimiter='\t')
        next(reader)  # Skip header

        # Find Asset Group column index
        ag_col_idx = None
        for i, header in enumerate(headers):
            if 'Asset Group' in clean_text(header):
                ag_col_idx = i
                break

        print("🎯 ASSET GROUPS ANALYSIS:")
        print("-" * 30)

        asset_groups = defaultdict(int)
        total_rows = 0

        # Reset and read all rows
        f.seek(0)
        reader = csv.reader(f, delimiter='\t')
        next(reader)  # Skip header

        for row in reader:
            total_rows += 1
            if ag_col_idx is not None and len(row) > ag_col_idx:
                ag_name = clean_text(row[ag_col_idx])
                if ag_name:
                    asset_groups[ag_name] += 1

        print(f"   Total Rows: {total_rows}")
        print(f"   Unique Asset Groups: {len(asset_groups)}")
        print()

        print("📋 ASSET GROUP BREAKDOWN:")
        for ag_name, count in sorted(asset_groups.items()):
            print(f"   • {ag_name} ({count} rows)")

        print()
        print("🔍 KEY INSIGHTS:")
        print("-" * 20)
        print("   • Business: My Expert Resume (Resume writing & career coaching)")
        print("   • Campaign Type: Performance Max")
        print("   • Budget: $41.89 daily")
        print("   • Targeting: Interest-based + Remarketing")
        print("   • Services: Resume writing, LinkedIn optimization, Career coaching")
        print("   • Geographic Focus: USA-based (Fort Lauderdale, FL)")
        print("   • Brand Elements: Poppins font, professional messaging")

if __name__ == "__main__":
    analyze_campaign()
