# Wrights Campaign Management

This directory contains all Wrights campaign management files, organized for easy access and maintenance.

## 📁 Directory Structure

```
wrights/
├── campaigns/              # CSV exports for Google Ads Editor
│   ├── archive/            # Archived campaign CSVs
│   └── imports/            # Imported Google Ads Editor exports
├── docs/                   # Documentation and reports
├── assets/                 # Campaign assets (images, videos, etc.)
├── search_themes/          # Search theme configurations
├── wrights_client_config.yaml  # Client configuration
└── README.md              # This file

# Agent-level tools (../tools/)
├── campaign_plan.py        # Generate campaign CSVs
└── run_campaign_plan.sh   # Campaign planning script
```

## 🎯 Quick Access

### Current Campaign CSVs
- Check `campaigns/` directory for available CSV files

### Search Themes
- **Asset Group Themes**: `search_themes/search_themes.csv`
- **PMAX Campaign Themes**: `search_themes/pmax_campaign_themes.md`

### Documentation
- Analysis reports in `docs/` directory

### Campaign Planning
```bash
cd ../tools/
python3 campaign_plan.py
```

### View Campaign Summary
```bash
cd campaigns/
ls -la *.csv
```

## 📊 Campaign Overview

- **Client**: Wrights
- **Website**: To be determined
- **Industry**: To be determined
- **Account Status**: To be determined

## 🚀 Google Ads Editor Import

1. Open Google Ads Editor
2. File → Import
3. Select CSV from `campaigns/` directory
4. Review and apply changes

## 🔧 Tools Available

### Campaign Tools (Agent Level - `../tools/`)
- `../tools/campaign/campaign_plan.py` - Generate campaign CSVs
- `../tools/campaign/rsa_campaign_generator.py` - Generate RSA campaigns
- `../tools/campaign/search_themes_generator.py` - Generate search themes
- `../tools/campaign/website_content_analyzer.py` - Analyze website content

### Documentation
- Campaign documentation in `docs/` directory
- Implementation guides and strategy documents

## 📈 Performance Notes

- Add campaign performance notes here
