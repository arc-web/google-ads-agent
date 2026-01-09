# Google Ads Reference Tool

A comprehensive reference tool for Google Ads campaign setup information, powered by Context7 documentation. This tool provides accurate, up-to-date information about campaign configuration, bidding strategies, targeting options, and best practices.

## Features

- **Campaign Types Reference**: Detailed information about Search, Display, Performance Max, Shopping, Video, App, and Demand Gen campaigns
- **Bidding Strategies Guide**: Complete setup information for all Google Ads bidding strategies
- **Targeting Options**: Comprehensive targeting configuration guidance
- **Network Settings**: Information about Google advertising networks
- **Budget Management**: Best practices for budget setup and management
- **JSON Examples**: Ready-to-use campaign creation examples
- **Search Functionality**: Find relevant information across all documentation

## Installation

The tool is part of the Google Ads agent codebase and requires no additional installation. It uses the existing Python environment.

## Usage

### Basic Usage

```python
from gads.tools.google_ads_reference_tool import GoogleAdsReferenceTool

# Initialize the tool
tool = GoogleAdsReferenceTool()

# Get information about a specific topic
search_info = tool.get_campaign_setup_info("search campaigns")
pmax_info = tool.get_campaign_setup_info("performance max")
bidding_info = tool.get_campaign_setup_info("target CPA")
```

### Available Query Topics

#### Campaign Types
- "search campaigns" or "search ads"
- "display campaigns" or "display ads"
- "performance max" or "pmax"
- "shopping campaigns" or "product ads"
- "video campaigns" or "youtube ads"
- "app campaigns" or "app install"
- "demand gen" or "lead generation"

#### Bidding Strategies
- "manual cpc" or "manual bidding"
- "target cpa" or "cost per acquisition"
- "target roas" or "return on ad spend"
- "maximize clicks"
- "maximize conversions"
- "maximize conversion value"

#### Targeting Options
- "keyword targeting" or "keywords"
- "location targeting" or "geographic"
- "audience targeting" or "audiences"
- "device targeting"
- "ad scheduling" or "dayparting"

#### Networks
- "search network"
- "display network"
- "youtube network"

#### General Topics
- "campaign setup" or "create campaign"
- "budget" or "spending"
- "help" (for usage information)

### Advanced Usage

```python
# Get all campaign types information
all_campaigns = tool.get_all_campaign_types()

# Get all bidding strategies
all_bidding = tool.get_all_bidding_strategies()

# Search across all documentation
results = tool.search_documentation("conversion tracking")

# Get JSON example for campaign creation
search_campaign_json = tool.get_campaign_creation_json_example("search")
pmax_campaign_json = tool.get_campaign_creation_json_example("performance_max")
```

## Response Format

All queries return structured dictionary responses with the following general format:

```python
{
    "type": "campaign_type|bidding_strategy|targeting|network|general_setup|budget|help",
    "name": "Display Name",
    "description": "Detailed description",
    "source": "Context7 Google Ads Documentation",
    # Additional fields specific to the query type
}
```

## Campaign Types Information

Each campaign type response includes:
- **name**: Official campaign type name
- **description**: What the campaign type does
- **networks**: Where ads can appear
- **ad_formats**: Available ad formats
- **bidding_strategies**: Compatible bidding strategies
- **targeting_options**: Available targeting methods
- **best_practices**: Recommended setup and management practices

## Bidding Strategies Information

Each bidding strategy response includes:
- **name**: Strategy name
- **description**: How the strategy works
- **use_cases**: When to use this strategy
- **campaign_types**: Compatible campaign types
- **optimization_goal**: What the strategy optimizes for
- **setup_requirements**: Prerequisites and configuration details

## Integration with Existing Workflows

The reference tool can be integrated into existing Google Ads workflows:

```python
# Example integration in campaign creation workflow
def create_campaign_with_reference(campaign_type, config):
    # Get reference information before setup
    reference = tool.get_campaign_setup_info(f"{campaign_type} campaigns")

    # Validate configuration against best practices
    validate_against_best_practices(config, reference["best_practices"])

    # Get appropriate bidding strategy info
    if config.get("bidding_strategy"):
        bidding_ref = tool.get_bidding_strategy_info(config["bidding_strategy"])
        validate_bidding_setup(config, bidding_ref)

    # Proceed with campaign creation
    return create_campaign(config)
```

## Data Sources

This tool uses information from:
- **Google Ads Support Documentation** (`/websites/support_google_google-ads`)
- **Google Ads API Documentation** (`/websites/developers_google_com-google-ads-api-docs`)

All information is sourced from official Google Ads documentation and kept current through Context7's documentation access.

## Error Handling

The tool provides helpful error messages for invalid queries:

```python
{
    "error": "Campaign type 'invalid_type' not found"
}
```

## Examples

See `example_usage.py` for complete usage examples and integration patterns.

## Contributing

When adding new campaign types, bidding strategies, or targeting options:
1. Update the corresponding `_load_*` method
2. Ensure data structure consistency
3. Add appropriate query terms to `get_campaign_setup_info`
4. Update this README with new capabilities