# Agent Tools

This directory contains agent-level tools for managing and processing client data across the platform.

## Directory Relationships

### Parent Dependencies
- **Agent Layer**: `../` (google_ads_agent)
  - Provides core Google Ads API integration and authentication
  - Supplies shared configuration and business logic
  - Offers cross-app communication infrastructure

### Child Components
- **`campaign/`**: Campaign management and generation tools
  - `campaign_plan.py` - Generates comprehensive campaign CSV exports
  - `rsa_campaign_generator.py` - Creates Responsive Search Ads campaigns
  - `search_themes_generator.py` - Builds search theme configurations
  - `sitelink_generator.py` - Generates sitelink extensions
  - `analyze_original_campaign.py` - Analyzes existing campaign performance

- **`website/`**: Website analysis and optimization tools
  - `website_content_analyzer.py` - Analyzes website content for campaigns
  - `performance_report_generator.py` - Generates performance reports

### Sibling Relationships
- **`config/`**: Provides configuration data consumed by tools
- **`gads/`**: Supplies core business logic and API integrations
- **`apps/`**: Consumes tool outputs for application workflows

### Data Flow Relationships
1. **Configuration Input**: Receives settings from `../config/` directory
2. **Client Data Input**: Processes data from `../../clients/my_expert_resume/` and other client directories
3. **API Integration**: Uses `../gads/core/` for Google Ads API access
4. **App Consumption**: Provides processed data to `../apps/` for workflow automation

### Cross-Agent Dependencies
- **Client Directories**: `../../../clients/my_expert_resume/`, `../../google_cloud_agent/`, etc.
  - Supplies client-specific data and requirements
  - Receives processed campaign outputs
- **Shared Resources**: `../../shared/`
  - Provides common utilities and dependencies
  - Enables cross-agent tool reuse

## File Dependencies
- **Core Logic**: Depends on `../gads/core/business_logic/` for API operations
- **Configuration**: Uses `../config/` for business rules and limits
- **Client Data**: Integrates with client-specific directories for data processing

## 📁 Tools Overview

### Campaign Management Tools
- **`campaign/campaign_plan.py`** - Generate comprehensive campaign CSV exports for Google Ads Editor
- **`campaign/rsa_campaign_generator.py`** - Generate Responsive Search Ads campaigns
- **`campaign/search_themes_generator.py`** - Generate search theme configurations for asset groups
- **`campaign/sitelink_generator.py`** - Generate sitelink extensions for campaigns

### Analysis & Research Tools
- **`campaign/analyze_original_campaign.py`** - Analyze existing campaign performance and structure
- **`website/website_content_analyzer.py`** - Analyze website content for campaign optimization

### Automation Scripts
- **`campaign/run_campaign_plan.sh`** - Automated campaign planning and execution pipeline

## 🎯 Tool Categories

**Client-Specific Tools**: Work with individual client data (MyExpertResume, etc.)
**Agent Infrastructure**: Core agent capabilities for data processing and management
**Automation Scripts**: Workflow automation for repetitive tasks

## 🚀 Usage

```bash
# Generate campaign plan for a client
python3 campaign/campaign_plan.py --client my_expert_resume

# Analyze existing campaigns
python3 campaign/analyze_original_campaign.py --input campaigns.csv

# Run automated campaign pipeline
./campaign/run_campaign_plan.sh
```

## 📊 Integration

These tools integrate with client directories in `../../../clients/my_expert_resume/`, `../../../clients/brain_based_emdr/`, etc., providing agent-level processing capabilities for client-specific data.

## Links
- **Parent Agent**: `../README.md` (agent documentation)
- **Configuration**: `../config/` (business rules and settings)
- **Core Logic**: `../gads/core/` (API integrations)
- **Client Data**: `../../../clients/` (all client-specific inputs)
- **Shared Resources**: `../../shared/` (common utilities)
