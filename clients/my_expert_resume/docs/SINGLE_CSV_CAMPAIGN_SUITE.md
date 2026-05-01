# Single CSV Campaign Suite - Complete MyExpertResume Setup

## Overview

The MyExpertResume campaign system now generates a **single comprehensive CSV** containing both national and regional campaigns with all their respective configurations, asset groups, search themes, and geographic targeting.

## Single CSV Benefits

### Unified Management
- **One file** contains all campaign configurations
- **Google Ads Editor** automatically creates both campaigns
- **No manual** campaign creation or CSV switching
- **Complete setup** in one import operation

### Comprehensive Coverage
- **2 Campaigns**: National + Florida Regional
- **5 Asset Groups**: 3 national + 2 regional
- **50 Search Themes**: Strategically distributed
- **7 Geographic Targets**: 1 national + 6 regional cities
- **100+ Rows**: Complete campaign structure

## CSV Structure

### Campaigns Included
1. **MyExpertResume National Executive**
   - Budget: $89.99 daily
   - Targeting: All 50 US states
   - Asset Groups: 3 (Executive Core, Senior Executive, Career Advancement)
   - Search Themes: 30 (national keywords only)

2. **MyExpertResume Florida Executive**
   - Budget: $59.99 daily
   - Targeting: 6 Florida cities (25-mile radius each)
   - Asset Groups: 2 (Executive Core, Career Services)
   - Search Themes: 20 (Florida keywords only)

### Geographic Targeting
- **National**: "United States" (covers all 50 states)
- **Florida Cities**:
  - Fort Lauderdale, FL, USA (25-mile radius)
  - Miami, FL, USA (25-mile radius)
  - West Palm Beach, FL, USA (25-mile radius)
  - Tampa, FL, USA (25-mile radius)
  - Orlando, FL, USA (25-mile radius)
  - Jacksonville, FL, USA (25-mile radius)

## File Specifications

### CSV Output
- **Filename**: `MyExpertResume_Complete_Campaign_Suite_2025.csv`
- **Total Rows**: 103
- **File Size**: 80,971 bytes
- **Format**: Google Ads Editor compatible

### Content Breakdown
```
Campaign Rows: 2 campaigns × base configuration
Asset Group Rows: 5 asset groups × detailed configuration
Extension Rows: Sitelinks, callouts, structured snippets
Search Theme Rows: 50 themes × individual entries
Geographic Rows: 7 locations × targeting configuration
```

## Generation Command

```bash
cd tools
python3 campaign_plan.py complete
```

This generates the complete campaign suite in one operation.

## Import Process

### Google Ads Editor Setup
1. **Open Google Ads Editor**
2. **File → Import**
3. **Select**: `MyExpertResume_Complete_Campaign_Suite_2025.csv`
4. **Google Ads automatically creates both campaigns**

### Campaign Separation
- **Campaign 1**: "MyExpertResume National Executive"
- **Campaign 2**: "MyExpertResume Florida Executive"
- **Automatic setup**: Budgets, targeting, and all configurations applied

## Quality Assurance

### Validation Performed
- ✅ **Character limits** enforced across all text
- ✅ **Auto-corrections** applied for compliance
- ✅ **Geographic targeting** properly formatted
- ✅ **Search themes** within limits per asset group
- ✅ **CSV structure** Google Ads Editor compatible

### Error Handling
- **Auto-expansion** for short headlines
- **Auto-truncation** for long content
- **Validation feedback** for any issues
- **Compliance guaranteed** before export

## Performance Optimization

### Budget Allocation
- **National Campaign**: 60% ($89.99) - Broad reach
- **Regional Campaign**: 40% ($59.99) - Conversion focus

### Targeting Strategy
- **National**: Broad executive audience, brand awareness
- **Regional**: Local Florida intent, higher conversion rates

## Usage Examples

### Generate Complete Suite
```bash
python3 campaign_plan.py complete
# Output: MyExpertResume_Complete_Campaign_Suite_2025.csv
```

### Generate Individual Campaigns (if needed)
```bash
python3 campaign_plan.py national   # National only
python3 campaign_plan.py florida    # Florida only
```

## Technical Implementation

### Campaign Data Structure
```python
campaigns = [
    {
        "name": "MyExpertResume National Executive",
        "budget": 89.99,
        "locations": [{"location": "United States"}],
        "asset_groups": [
            {"name": "National - Executive Core", "search_themes": [...]},
            # ... more asset groups
        ]
    },
    {
        "name": "MyExpertResume Florida Executive",
        "budget": 59.99,
        "locations": [
            {"location": "Fort Lauderdale, FL, USA", "radius": "25", "unit": "miles"},
            # ... 5 more Florida cities
        ],
        "asset_groups": [
            {"name": "Florida - Executive Core", "search_themes": [...]},
            # ... more asset groups
        ]
    }
]
```

### CSV Export Process
1. **Generate campaign data** for both campaigns
2. **Convert to CSV rows** with all extensions and targeting
3. **Combine into single file** with proper headers
4. **Validate compliance** before saving
5. **Export complete suite** ready for Google Ads

## Campaign Management

### Post-Import Setup
- **Review campaigns** in Google Ads interface
- **Verify geographic targeting** for each campaign
- **Check budget allocation** matches recommendations
- **Monitor performance** across both campaigns

### Optimization Strategy
- **Track metrics** separately for national vs regional
- **Adjust budgets** based on conversion performance
- **A/B test** different targeting approaches
- **Scale successful** campaign structures

## File Reference

**Complete CSV**: `campaigns/MyExpertResume_Complete_Campaign_Suite_2025.csv`
**Generator**: `tools/campaign_plan.py`
**Documentation**:
- `docs/SINGLE_CSV_CAMPAIGN_SUITE.md`
- `docs/NATIONAL_REGIONAL_CAMPAIGN_STRATEGY.md`
- `docs/GEOGRAPHIC_TARGETING_IMPLEMENTATION.md`

## Summary

The single CSV approach provides:
- **Unified setup** in one import operation
- **Complete coverage** of national + regional strategies
- **Proper geographic targeting** automatically configured
- **50 search themes** strategically distributed
- **Google Ads ready** with full validation

**One CSV, two complete campaigns, maximum efficiency!** 🎯📄🚀
