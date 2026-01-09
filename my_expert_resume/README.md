# MyExpertResume Campaign Management

This directory contains all MyExpertResume.com campaign management files, organized for easy access and maintenance.

## 📁 Directory Structure

```
clients/my_expert_resume/
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
- **Test Campaign**: `campaigns/MyExpertResume_Test_Campaign_Suite_2025.csv`
- **Fixed Test Campaign**: `campaigns/MyExpertResume_Fixed_Test_Campaign_Suite_2025.csv`
- **Complete Campaign**: `campaigns/MyExpertResume_Complete_Campaign_Suite_2025.csv`

### Search Themes
- **Asset Group Themes**: `search_themes/search_themes.csv`
- **PMAX Campaign Themes**: `search_themes/pmax_campaign_themes.md`

### Keyword Research
- **Industry Research**: `keyword_research/` (8 resume industries)
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

- **Campaign Name**: ARC PMAX TEST - Executive / ARC PMAX
- **Type**: Performance Max
- **Budget**: $41.89 Daily
- **Asset Groups**: Executive Resume Services (test) / 14 Industry-Specific (full)
- **Business**: My Expert Resume
- **Landing Page**: https://myexpertresume.com/

## 🚀 Google Ads Editor Import

1. Open Google Ads Editor
2. File → Import
3. Select CSV from `campaigns/` directory
4. Review and apply changes

## 📋 Asset Groups (Full Campaign)

1. Interests - All (General targeting)
2. ARC - Service - Resume Writing | Search
3. ARC - Service - Careers | Search
4. ARC - Remarketing - Services
5. ARC - Course - Resume | Search
6. ARC - Executive Resume | Search
7. ARC - Management Resume | Search
8. ARC - Technical Resume | Search
9. ARC - Medical Resume | Search
10. ARC - Federal Resume | Search
11. ARC - Military Resume | Search
12. ARC - Student Resume | Search
13. ARC - Professional Resume | Search
14. ARC - CV Resume | Search

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

- Executive asset group focuses on C-suite, CEO, VP searches
- Industry-specific groups target resume writing service searches
- All campaigns use Performance Max with audience signals
- 74% success rate messaging used throughout
