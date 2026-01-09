# Configuration Directory

This directory contains all configuration files and settings for the Google Ads agent, providing structured, validated configuration management across the platform.

## Directory Relationships

### Parent Dependencies
- **Agent Layer**: `../` (google_ads_agent)
  - Provides runtime environment and execution context
  - Consumes configuration for business logic and API operations

### Child Components
- **`google_ads_config_loader.py`**: Main configuration loading and validation engine
  - Loads and validates all YAML configuration files
  - Provides type-safe configuration access to other components
  - Implements configuration caching and hot-reloading

- **`business_config.yaml`**: Client-specific business rules and brand guidelines
  - Defines prohibited keywords and required terms
  - Specifies content quality standards and compliance requirements
  - Contains brand voice and tone guidelines

- **`campaign_defaults.yaml`**: Campaign structure and bidding defaults
  - Defines default settings for all campaign types (Search, Display, PMAX, etc.)
  - Specifies bid strategies and budget recommendations
  - Contains geographic targeting and ad scheduling defaults

- **`ad_limits.yaml`**: Google Ads format limitations reference
  - Documents character limits for headlines, descriptions, paths
  - Defines format-specific constraints and requirements
  - Used for validation during ad creation

- **`ad_character_limits.yaml`**: Complete character limits and validation rules
  - Comprehensive reference for all Google Ads format limits
  - Includes validation rules and prohibited characters
  - Supports automated ad content validation

- **`core_agent_traits.yaml`**: Agent behavior and knowledge base
  - Defines absolute prohibitions (never provide timelines)
  - Specifies business type identification rules
  - Contains quality assurance checklists

### Sibling Relationships
- **`gads/core/`**: Consumes configuration for API operations and business logic
- **`apps/`**: Uses configuration for app-specific behavior and workflows
- **`tools/`**: References configuration for tool parameters and validation

### Configuration Flow Relationships
1. **Loading**: `google_ads_config_loader.py` loads and validates all YAML files
2. **Distribution**: Provides configuration to `../gads/core/` for business logic
3. **Application**: Supplies settings to `../apps/` for workflow execution
4. **Validation**: Used by `../tools/` for content and parameter validation

### Cross-Agent Dependencies
- **Shared Validation**: `../../shared/` may reference common validation rules
- **Client-Specific**: `../../../clients/my_expert_resume/` uses client-specific overrides
- **Platform Standards**: Aligns with platform-wide configuration patterns

## File Dependencies
- **Python Runtime**: Requires Python for `google_ads_config_loader.py` execution
- **YAML Parser**: Uses PyYAML for configuration file parsing
- **Path Resolution**: Depends on relative path resolution from agent root

## Usage

```python
from config.google_ads_config_loader import ConfigLoader

loader = ConfigLoader()

# Load campaign configuration
campaign_config = loader.load_campaign_config("search", "maximize_conversions")

# Load business rules
business_config = loader.load_business_config()

# Load ad limits
limits = loader.load_ad_limits()
```

## Configuration Hierarchy
1. **Platform Defaults**: Base settings for all Google Ads operations
2. **Campaign Specific**: Type and bid strategy specific overrides
3. **Client Specific**: Business rule and brand customizations
4. **Runtime Overrides**: Environment-specific modifications

## Validation Rules
- All configurations validated against JSON schemas
- Type checking and range validation implemented
- Cross-reference validation between related settings
- Hot-reloading supported for development

## Links
- **Parent Agent**: `../README.md` (agent documentation)
- **Consumer - Core Logic**: `../gads/core/` (uses configuration)
- **Consumer - Apps**: `../apps/` (workflow configuration)
- **Consumer - Tools**: `../tools/` (validation and parameters)
- **Client Overrides**: `../../../clients/my_expert_resume/config/` (client-specific settings)
