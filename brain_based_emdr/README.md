# BrainBasedEMDR Campaign Management

This directory contains all BrainBasedEMDR.com campaign management files, organized for easy access and maintenance.

## 📁 Directory Structure

```
clients/brain_based_emdr/
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
- **Test Campaign**: `campaigns/BrainBasedEMDR_Test_Campaign_Suite_2025.csv`
- **Fixed Test Campaign**: `campaigns/BrainBasedEMDR_Fixed_Test_Campaign_Suite_2025.csv`
- **Complete Campaign**: `campaigns/BrainBasedEMDR_Complete_Campaign_Suite_2025.csv`

### Search Themes
- **Asset Group Themes**: `search_themes/search_themes.csv`
- **PMAX Campaign Themes**: `search_themes/pmax_campaign_themes.md`

### Keyword Research
- **Trauma Therapy Research**: `keyword_research/` (PTSD, trauma, anxiety treatment categories)
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

- **Campaign Name**: BrainBasedEMDR National Trauma Therapy
- **Type**: Performance Max
- **Budget**: $TBD Daily
- **Asset Groups**: Trauma Therapy Services (test) / Multiple Trauma Treatment Categories (full)
- **Business**: BrainBasedEMDR
- **Landing Page**: https://brainbasedemdr.com/
- **Ad Account ID**: 700-715-0568

## 🚀 Google Ads Editor Import

1. Open Google Ads Editor
2. File → Import
3. Select CSV from `campaigns/` directory
4. Review and apply changes

## 📋 Asset Groups (Full Campaign)

1. Interests - Trauma Recovery (General targeting)
2. EMDR Therapy Services | Search
3. PTSD Treatment | Search
4. Trauma Therapy Online | Search
5. Anxiety Treatment EMDR | Search
6. Eye Movement Desensitization | Search
7. Complex PTSD Therapy | Search
8. Childhood Trauma Recovery | Search
9. Military Trauma Treatment | Search
10. Sexual Trauma Therapy | Search
11. Grief Trauma Counseling | Search
12. Dissociation Treatment | Search
13. Flashbacks EMDR Therapy | Search
14. Nightmares Trauma Treatment | Search

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

- Trauma-focused asset groups target specific mental health conditions
- Industry-specific groups target EMDR therapy service searches
- All campaigns use Performance Max with audience signals
- Evidence-based messaging used throughout (research-backed claims)

## 🎯 Industry-Specific Considerations

### EMDR Therapy Services
- **Target Audience**: Individuals with trauma, PTSD, anxiety disorders
- **Service Type**: Evidence-based psychotherapy treatment
- **Key Differentiators**: Brain-based approach, eye movement technology
- **Geographic Focus**: National coverage with local service availability
- **Regulatory Compliance**: Mental health service advertising requirements

### Campaign Strategy
- Focus on trauma recovery and mental health treatment searches
- Emphasize evidence-based, research-supported treatment outcomes
- Target both acute trauma and complex PTSD cases
- Include both in-person and online therapy options
- Highlight specialized trauma treatment expertise