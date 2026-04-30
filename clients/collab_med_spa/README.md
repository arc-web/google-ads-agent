# Collab Med Spa Campaign Management

This directory contains all Collab Med Spa campaign management files, organized for easy access and maintenance.

## 📁 Directory Structure

```
collab_med_spa/
├── campaigns/              # CSV exports for Google Ads Editor
│   ├── archive/            # Archived campaign CSVs
│   └── imports/            # Imported Google Ads Editor exports
├── docs/                   # Documentation and reports
├── assets/                 # Campaign assets (images, videos, etc.)
├── search_themes/          # Search theme configurations
├── collab_med_spa_client_config.yaml  # Client configuration
└── README.md              # This file

# Agent-level tools (../tools/)
├── campaign_plan.py        # Generate campaign CSVs
├── str_keyword_analyzer.py # Analyze Search Term Reports
├── map_keywords_to_campaigns.py # Map keywords to campaign structure
└── run_campaign_plan.sh   # Campaign planning script
```

## 🎯 Quick Access

### Current Campaign CSVs
- **Keywords to Add**: `campaigns/CollabMedSpa_Keywords_To_Add_2025.csv`
- **Mapped Keywords**: `campaigns/CollabMedSpa_Keywords_Mapped_2025.csv` ⭐ **Ready for Upload**

### Imported Campaign Structure
- **Google Ads Editor Export**: `campaigns/imports/CollabMedSpa.com++6_Campaigns+12_Ad groups+2025-12-23.csv`

### Search Themes
- **Asset Group Themes**: `search_themes/search_themes.csv`
- **PMAX Campaign Themes**: `search_themes/pmax_campaign_themes.md`

### Documentation
- **Analysis Report**: `docs/ANALYSIS_REPORT.md`
- **Implementation Guide**: `docs/CLIENT_SPECIFIC_IMPLEMENTATION.md`

### Campaign Planning
```bash
cd ../tools/
python3 str_keyword_analyzer.py
python3 map_keywords_to_campaigns.py
```

### View Campaign Summary
```bash
cd campaigns/
ls -la *.csv
```

## 📊 Campaign Overview

- **Campaign Types**: Search (TPPC campaigns)
- **Primary Services**: Facial Treatments, Dermal Fillers, Laser Hair Removal, Medical Spa Services
- **Website**: https://collabmedspa.com/
- **Primary Service Area**: Scottsdale, Phoenix, Mesa, Chandler, Tucson (AZ)
- **Account Status**: Live and Active

## 🚀 Google Ads Editor Import

1. Open Google Ads Editor
2. File → Import
3. Select CSV from `campaigns/` directory
4. Review and apply changes

## 📋 Campaign Structure

### Active Campaigns
1. **TPPC - Brand** - Brand awareness and direct searches
   - Ad Group: Brand - CollabMedSpa

2. **TPPC - General** - General service searches
   - Ad Group: Laser Hair Removal - General

3. **TPPC - Regional - Facials** - Facial treatment services
   - Ad Groups: Facials - Local, Facials - Scottsdale

4. **TPPC - Regional - Fillers** - Dermal filler services
   - Ad Groups: Fillers - Local, Fillers - Scottsdale

5. **TPPC - Regional - Laser** - Laser hair removal services
   - Ad Groups: Laser Hair Removal - General, Laser Hair Removal - Local, Laser Hair Removal - Scottsdale

6. **TPPC - Regional - Medspas** - General medical spa services
   - Ad Groups: Laser Hair Removal - General, Medspas - Local, Medspas - Scottsdale

## 🔧 Tools Available

### Campaign Tools (Agent Level - `../tools/`)
- `../tools/campaign/str_keyword_analyzer.py` - Analyze Search Term Reports
- `../tools/campaign/map_keywords_to_campaigns.py` - Map keywords to campaign structure
- `../tools/campaign/campaign_plan.py` - Generate campaign CSVs
- `../tools/campaign/rsa_campaign_generator.py` - Generate RSA campaigns
- `../tools/campaign/search_themes_generator.py` - Generate search themes
- `../tools/campaign/website_content_analyzer.py` - Analyze website content
- `../tools/campaign/analyze_original_campaign.py` - Analyze existing campaigns

### Documentation
- Campaign documentation in `docs/` directory
- Implementation guides and strategy documents
- Search Term Report analysis and keyword mapping reports

## 📈 Performance Notes

- Focus on Scottsdale and Phoenix metro area
- Emphasize professional medical spa services
- Trust signals and certifications important
- Before/after content crucial for aesthetic services
- Local "near me" searches prioritized
- Converting keywords prioritized with Exact match type

## 🎨 Industry-Specific Considerations

### Medical Spa Services
- Facial treatments (Hydrafacials, Microneedling, Dermaplaning)
- Dermal fillers (Lip fillers, Under eye fillers)
- Laser hair removal services
- Injectable treatments
- Professional aesthetic services

### Geographic Targeting
- Primary: Scottsdale, AZ (25-mile radius)
- Secondary: Phoenix, Mesa, Chandler, Tucson, AZ
- Local intent optimization
- Service area radius targeting

### Compliance Considerations
- Medical licensing requirements
- FDA-approved treatments only
- Professional certifications emphasized
- Trust signals and guarantees
- Before/after documentation