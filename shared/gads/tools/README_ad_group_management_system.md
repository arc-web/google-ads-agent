# Ad Group Management System for Google Ads Search Campaigns

A comprehensive system for managing ad groups in Google Ads search campaigns, built using Context7 documentation analysis. This system provides automated ad group creation, optimization, validation, and integration with existing campaign workflows.

## Overview

The Ad Group Management System automates the complex process of creating and managing ad groups in Google Ads search campaigns. Based on official Google Ads API documentation and best practices, it ensures ad groups are configured optimally for performance and compliance.

## Key Features

### 🔧 **Automated Ad Group Creation**
- Generate optimized ad groups based on themes and targeting
- Automatic keyword generation (exact, phrase, broad match)
- Intelligent negative keyword suggestions
- Bid strategy optimization based on campaign goals

### ✅ **Configuration Validation**
- Validate ad group settings against Google Ads policies
- Check compatibility with campaign objectives
- Identify configuration gaps and issues
- Provide actionable improvement recommendations

### 📊 **Performance Optimization**
- Analyze ad group performance metrics
- Generate optimization recommendations
- Suggest bid adjustments and keyword changes
- Identify high-performing search terms for expansion

### 🔗 **Campaign Integration**
- Seamless integration with existing campaign planning workflows
- Automatic ad group generation for campaigns
- CSV export for Google Ads Editor
- Performance dashboard and reporting

### 📋 **Best Practices Implementation**
- Ad group naming conventions
- Keyword organization strategies
- Bid management recommendations
- Quality Score optimization guidance

## Installation & Setup

The system is part of the Google Ads agent codebase and requires no additional installation. All dependencies are included in the existing environment.

```python
from gads.tools.ad_group_management_system import AdGroupManagementSystem
from gads.tools.ad_group_integration import AdGroupCampaignIntegrator
```

## Core Components

### 1. AdGroupManagementSystem
Main system for creating and managing individual ad groups.

### 2. AdGroupCampaignIntegrator
Integrates ad group management with campaign planning workflows.

### 3. Supporting Classes
- `AdGroupSettings`: Configuration settings for ad groups
- `AdGroupTargeting`: Targeting parameters and keywords
- `AdGroupPerformance`: Performance metrics and analysis
- `AdGroupOptimization`: Optimization recommendations

## Usage Examples

### Basic Ad Group Creation

```python
from gads.tools.ad_group_management_system import AdGroupManagementSystem

ag_system = AdGroupManagementSystem()

# Create an optimized ad group
ad_group = ag_system.create_optimized_ad_group(
    theme="Executive Resume Services",
    campaign_type="SEARCH",
    target_audience="executive_professionals",
    geo_targeting="National"
)

print(f"Created: {ad_group['name']}")
print(f"Keywords: {len(ad_group['keywords'])}")
```

### Campaign Integration

```python
from gads.tools.ad_group_integration import AdGroupCampaignIntegrator

integrator = AdGroupCampaignIntegrator()

# Generate ad groups for a campaign
campaign_config = {
    "name": "Executive Resume Campaign",
    "type": "SEARCH",
    "objective": "conversions",
    "target_audience": "executives"
}

ad_groups = integrator.generate_ad_groups_for_campaign(campaign_config)
print(f"Generated {len(ad_groups)} ad groups")
```

### Performance Optimization

```python
# Analyze and optimize ad group performance
performance_data = {
    "impressions": 10000,
    "clicks": 150,
    "cost_micros": 7500000,
    "conversions": 3
}

optimization = ag_system.optimize_ad_group(ad_group, performance_data)
print("Optimization recommendations:")
for action in optimization.priority_actions:
    print(f"• {action}")
```

### CSV Export

```python
# Export ad groups to Google Ads Editor CSV format
csv_content = integrator.export_ad_groups_to_csv(ad_groups, "Campaign Name")

# Save to file
with open("ad_groups.csv", "w") as f:
    f.write(csv_content)
```

## Ad Group Types Supported

### SEARCH_STANDARD
- Standard search ad groups for text ads
- Supports all match types (exact, phrase, broad)
- Manual CPC and automated bidding strategies
- Comprehensive targeting options

### SEARCH_DYNAMIC
- Dynamic search ads for automated keyword targeting
- Website content-based keyword expansion
- Reduced manual keyword management

### DISPLAY_STANDARD
- Display network ad groups for banner ads
- Topic, interest, and audience targeting
- Placement-based targeting

### SHOPPING_PRODUCT_ADS
- Product listing ad groups for shopping campaigns
- Product group organization
- Inventory-based targeting

## Configuration Parameters

### Ad Group Settings
```python
settings = {
    "name": "Ad Group Name",
    "status": "ENABLED",  # ENABLED, PAUSED, REMOVED
    "type": "SEARCH_STANDARD",
    "cpc_bid_micros": 500000,  # $0.50 CPC bid
    "target_cpa_micros": 10000000,  # $10 target CPA
    "labels": ["high-priority", "executive-focused"]
}
```

### Targeting Configuration
```python
targeting = {
    "keywords": [
        {"text": '"executive resume"', "match_type": "EXACT"},
        {"text": "resume writing", "match_type": "PHRASE"}
    ],
    "negative_keywords": [
        {"text": "free", "match_type": "EXACT"},
        {"text": "template", "match_type": "BROAD"}
    ],
    "audience_targeting": ["executives", "professionals"],
    "demographic_targeting": {
        "age_ranges": ["35-44", "45-54"],
        "household_incomes": ["TOP_25_PERCENT"]
    }
}
```

## Optimization Features

### Automatic Analysis
- CTR (Click-Through Rate) evaluation
- CPA (Cost Per Acquisition) monitoring
- Quality Score assessment
- Search term performance analysis

### Recommendations Generated
- Bid adjustments by device/audience
- Keyword additions and removals
- Negative keyword suggestions
- Ad text improvements
- Audience expansion opportunities

## Best Practices Implemented

### Naming Conventions
- `{Campaign Type} - {Target Audience} - {Match Type} - {Geo Location}`
- Examples: `"Search - Executive - Exact - National"`

### Structure Guidelines
- 20-50 keywords per ad group
- Group by tight themes
- Separate match types when beneficial
- Use single keyword ad groups for high-value terms

### Bidding Strategies
- Automatic bid recommendations based on goals
- Competitive analysis for bid setting
- Budget-aware bidding suggestions

## Integration with Existing Workflows

### Campaign Planning (`campaign_plan.py`)
```python
# Automatically generate ad groups for new campaigns
campaign_config = create_campaign_plan()
ad_groups = integrator.generate_ad_groups_for_campaign(campaign_config)
```

### CSV Export (`GoogleAdsEditorExporter`)
```python
# Export campaigns with integrated ad groups
combined_csv = exporter.export_campaigns([campaign_config], ad_groups)
```

### Performance Monitoring
```python
# Analyze campaign and ad group performance together
optimization = integrator.optimize_campaign_ad_groups(
    campaign_config, ad_groups, performance_data
)
```

## Data Sources

Based on official Google Ads documentation from Context7:

- **Google Ads API Documentation** (`/websites/developers_google_com-google-ads-api-docs`)
- **Google Ads Support Documentation** (`/websites/support_google_google-ads`)

## Validation & Compliance

- **Policy Compliance**: Checks against Google Ads policies
- **API Compatibility**: Ensures compatibility with Google Ads API
- **Best Practices**: Validates against industry best practices
- **Performance Standards**: Monitors against performance benchmarks

## Performance Dashboard

Generate comprehensive performance insights:

```python
dashboard = integrator.create_ad_group_performance_dashboard(ad_groups, performance_data)

print(f"Overall CTR: {dashboard['performance_summary']['average_ctr']}%")
print(f"Top Performer: {dashboard['top_performers'][0]['name']}")
```

## Templates & Presets

### Available Templates
- `executive_services`: For executive-focused campaigns
- `local_services`: For location-based services
- `brand_awareness`: For brand-focused campaigns

```python
# Use a template with customizations
ad_group = ag_system.create_ad_group_from_template(
    "executive_services",
    customizations={"geo_targeting": "Florida"}
)
```

## Error Handling & Logging

- Comprehensive error handling for API failures
- Detailed logging for debugging
- Validation error reporting
- Performance issue alerts

## File Structure

```
gads/tools/
├── ad_group_management_system.py      # Core ad group management
├── ad_group_integration.py            # Campaign integration
├── ad_group_examples.py               # Usage examples
├── README_ad_group_management_system.md # This documentation
```

## Running Examples

```bash
cd gads/tools
python3 ad_group_examples.py
```

This will demonstrate all features of the Ad Group Management System with sample data and configurations.

## Future Enhancements

- Machine learning-based bid optimization
- Automated A/B testing for ad variations
- Real-time performance monitoring
- Integration with Google Ads API for live updates
- Advanced audience targeting recommendations

## Contributing

When adding new features:
1. Update relevant documentation
2. Add validation tests
3. Include example usage
4. Test integration with existing workflows
5. Follow existing code patterns and naming conventions

## Support

For issues or questions:
1. Check the examples in `ad_group_examples.py`
2. Review the comprehensive documentation
3. Test with sample data first
4. Check Google Ads API documentation for reference

---

*This system is built using Context7 documentation analysis to ensure accuracy and compliance with current Google Ads best practices and API specifications.*