# FullTiltAutobody.com Campaign Management

This directory contains all FullTiltAutobody.com campaign management files, organized for easy access and maintenance.

## 📁 Directory Structure

```
fulltilt_autobody/
├── campaigns/              # CSV exports for Google Ads Editor
│   ├── campaign_archive/   # Archived campaign CSVs
│   └── [active campaigns]  # Current launch-ready campaigns
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
- **🚀 Launch Ready PMAX**: `campaigns/FullTiltAutobody_Launch_Ready_PMAX.csv` *[ACTIVE]*
- **Production Campaign**: `campaigns/FullTiltAutobody_Production_Campaign.csv`
- **National PMAX Campaign**: `campaigns/FullTiltAutobody_National_PMAX_Campaign.csv`

### Archived Campaigns
- **Test Campaigns**: `campaigns/campaign_archive/` (old test versions)

### Search Themes
- **Asset Group Themes**: `search_themes/search_themes.csv`
- **PMAX Campaign Themes**: `search_themes/pmax_campaign_themes.md`

### Keyword Research
- **Industry Research**: `keyword_research/` (auto body, collision repair, paint services)
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

- **Campaign Name**: FullTilt Autobody National PMAX - Collision Repair Services
- **Type**: Performance Max
- **Budget**: $50.00 Daily (initial test budget)
- **Asset Groups**: Collision Repair (test) / Multiple Service-Specific (full)
- **Business**: FullTilt Autobody
- **Landing Page**: https://fulltiltAutobody.com/
- **Google Ads Account ID**: 934-508-6147

## 🚀 Google Ads Editor Import

1. Open Google Ads Editor
2. File → Import
3. Select CSV from `campaigns/` directory
4. Review and apply changes

## 📋 Asset Groups (Full Campaign)

1. Interests - Collision Repair Services (General targeting)
2. FullTilt - Service - Auto Body Repair | Search
3. FullTilt - Service - Collision Repair | Search
4. FullTilt - Service - Paint & Body Work | Search
5. FullTilt - Service - Frame Straightening | Search
6. FullTilt - Service - Insurance Claims | Search
7. FullTilt - Remarketing - Services
8. FullTilt - Course - Auto Repair | Search
9. FullTilt - Location - Local Repair Shops | Search
10. FullTilt - Emergency - Towing & Repair | Search
11. FullTilt - Service - Classic Car Restoration | Search
12. FullTilt - Service - Fleet Repair Services | Search
13. FullTilt - Service - Mobile Repair | Search
14. FullTilt - Warranty - Repair Guarantees | Search

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

- Collision repair asset group focuses on accident repair, insurance claims
- Service-specific groups target auto body repair service searches
- All campaigns use Performance Max with audience signals
- Emergency/towing services for urgent repair needs messaging used throughout

## 🎨 Industry-Specific Considerations

### Auto Body Repair Services
- Collision repair and restoration
- Paint and body work services
- Frame straightening and alignment
- Insurance claim processing
- Emergency towing services
- Classic car restoration
- Fleet repair services
- Mobile repair options

### Geographic Targeting
- National coverage with local intent
- Service area radius optimization
- Emergency service availability
- Local competition analysis

### Seasonal Considerations
- Higher demand after holidays/weekends
- Weather-related accident patterns
- Insurance claim processing timelines
- Fleet maintenance scheduling
