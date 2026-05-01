# EvoRestore Campaign Management

This directory contains all EvoRestore.com campaign management files, organized for easy access and maintenance.

## 📁 Directory Structure

```
clients/evolution_restoration_and_renovation/
├── campaigns/              # CSV exports for Google Ads Editor
├── docs/                   # Documentation and reports
├── assets/                 # Campaign assets (images, videos, etc.)
├── keyword_research/       # Keyword research and analysis
├── search_themes/          # Search theme configurations
└── README.md              # This file

# Agent-level tools (../tools/)
├── campaign_plan.py        # Generate campaign CSVs
├── rsa_campaign_generator.py # Generate RSA campaigns
├── search_themes_generator.py # Generate search themes
├── website_content_analyzer.py # Analyze website content
├── analyze_original_campaign.py # Analyze existing campaigns
└── run_campaign_plan.sh   # Campaign planning script
```

## 🎯 Quick Access

### Current Campaign CSVs
- **Emergency Services**: `campaigns/EvoRestore_Emergency_Services_2025.csv`
- **Water Damage**: `campaigns/EvoRestore_Water_Damage_2025.csv`
- **Fire Damage**: `campaigns/EvoRestore_Fire_Damage_2025.csv`
- **Complete Campaign**: `campaigns/EvoRestore_Complete_Campaign_Suite_2025.csv`

### Search Themes
- **Asset Group Themes**: `search_themes/search_themes.csv`
- **PMAX Campaign Themes**: `search_themes/pmax_campaign_themes.md`

### Keyword Research
- **Service Research**: `keyword_research/` (Emergency, Water, Fire, Mold services)
- **Comprehensive Report**: `keyword_research/comprehensive_report.json`

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

- **Campaign Types**: Performance Max, Search, Display
- **Primary Services**: Water Damage Restoration, Fire Damage Restoration, Emergency Services
- **Phone**: 271-353-8876
- **Website**: https://evorestore.com/
- **Budget**: TBD based on analysis

## 🚀 Google Ads Editor Import

1. Open Google Ads Editor
2. File → Import
3. Select CSV from `campaigns/` directory
4. Review and apply changes

## 📋 Asset Groups (Planned)

1. Emergency Water Damage Response
2. Fire & Smoke Damage Restoration
3. Mold Remediation Services
4. Storm Damage Cleanup
5. Commercial Property Restoration
6. Residential Restoration Services
7. Emergency Board-Up Services
8. Content Restoration & Cleaning

## 🔧 Tools Available

### Campaign Tools (Agent Level - `../tools/`)
- `../tools/campaign_plan.py` - Generate campaign CSVs
- `../tools/rsa_campaign_generator.py` - Generate RSA campaigns
- `../tools/search_themes_generator.py` - Generate search themes
- `../tools/website_content_analyzer.py` - Analyze website content
- `../tools/analyze_original_campaign.py` - Analyze existing campaigns
- `../tools/run_campaign_plan.sh` - Campaign planning script

### Keyword Research (Agent Level)
- `../advertools_keyword_research.py` - Run keyword research using advertools

### Documentation
- Campaign documentation in `docs/` directory
- Implementation guides and strategy documents

## 📈 Performance Notes

- Emergency response messaging takes priority
- Local service area targeting (state/city level)
- 24/7 emergency service positioning
- Trust signals and certifications emphasized
- Before/after photo assets crucial for conversion

## 🆘 Emergency Services Focus

EvoRestore specializes in emergency restoration services with rapid response times. Campaigns should emphasize:
- 24/7 availability
- Licensed & insured technicians
- Fast emergency response
- Professional restoration services
- Local service areas
