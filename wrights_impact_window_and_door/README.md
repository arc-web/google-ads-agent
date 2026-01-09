# Wright's Impact Window and Door Campaign Management

This directory contains all Wright's Impact Window and Door campaign management files, organized for easy access and maintenance.

## 📁 Directory Structure

```
wrights_impact_window_and_door/
├── reports/                # Organized CSV data exports
│   ├── campaign_data/      # Campaign structure and configuration
│   │   ├── Wright's Impact Window & Door - Search++76_Campaigns+278_Ad groups+22_Asset groups+2026-01-07.csv
│   │   └── README.md       # Campaign data analysis guide
│   ├── performance_data/   # Time-series performance metrics
│   │   ├── Time_series_chart(2025.12.08-2026.01.05).csv
│   │   ├── Time_series_chart(2025.12.08-2026.01.06).csv
│   │   └── README.md       # Performance analysis guide
│   ├── asset_data/         # Creative asset performance
│   │   ├── Ad asset report.csv
│   │   ├── Asset groups report.csv
│   │   └── README.md       # Asset optimization guide
│   ├── location_data/      # Geographic performance data
│   │   ├── Location report.csv
│   │   └── README.md       # Geographic analysis guide
│   └── video_data/         # Video advertising metrics
│       ├── Video report.csv
│       └── README.md       # Video performance guide
├── docs/                   # Documentation and strategy guides
│   ├── CAMPAIGN_ARCHITECTURE_PATHWAYS.md # CRITICAL pathways - NO CONFUSION ⭐⭐
│   ├── AD_ACCOUNT_ANALYSIS.md          # Critical account review ⭐
│   ├── CLIENT_SPECIFIC_IMPLEMENTATION.md # Campaign strategy
│   ├── CLIENT_AD_COPY_REQUESTS.md      # MANDATORY client requirements ⭐
│   ├── PERFORMANCE_MAX_AD_RULES.md     # PMAX campaign rules ⭐
│   ├── SEARCH_CAMPAIGN_AD_RULES.md     # Search campaign rules ⭐
│   ├── AD_COPY_BEST_PRACTICES.md       # Strategic ad copy framework
│   ├── REGIONAL_STRATEGY.md            # Geographic targeting
│   ├── BUDGET_ALLOCATION.md            # Financial planning
│   └── CSV_ANALYSIS_STRATEGY.md        # Data analysis guide ⭐
├── assets/                 # Campaign assets (images, videos, etc.)
├── search_themes/          # Search theme configurations
├── wrights_impact_client_config.yaml   # Client configuration
└── README.md              # This file

# Agent-level tools (../tools/)
├── campaign_plan.py        # Generate campaign CSVs
├── str_keyword_analyzer.py # Analyze Search Term Reports
├── map_keywords_to_campaigns.py # Map keywords to campaign structure
├── rsa_campaign_generator.py # Generate RSA campaigns
├── search_themes_generator.py # Generate search themes
└── run_campaign_plan.sh   # Campaign planning script
```

## 🎯 Quick Access

### Current Campaign CSVs
- **Keywords to Add**: `campaigns/Wrights_Keywords_To_Add_2025.csv`
- **Mapped Keywords**: `campaigns/Wrights_Keywords_Mapped_2025.csv` ⭐ **Ready for Upload**

### Imported Campaign Structure
- **Google Ads Editor Export**: `campaigns/imports/WrightsImpactWindowAndDoor.com++Campaigns+AdGroups+2025-01-07.csv`

### Search Themes
- **Asset Group Themes**: `search_themes/search_themes.csv`
- **PMAX Campaign Themes**: `search_themes/pmax_campaign_themes.md`

### Documentation
- **Analysis Report**: `docs/ANALYSIS_REPORT.md`
- **Implementation Guide**: `docs/CLIENT_SPECIFIC_IMPLEMENTATION.md`
- **Regional Strategy**: `docs/REGIONAL_STRATEGY.md`
- **Budget Allocation**: `docs/BUDGET_ALLOCATION.md`
- **Account Analysis**: `docs/AD_ACCOUNT_ANALYSIS.md` ⭐ **Critical Review**
- **CSV Analysis Strategy**: `docs/CSV_ANALYSIS_STRATEGY.md` ⭐ **Data Analysis Guide**
- **CSV Validation Report**: `docs/CSV_VALIDATION_REPORT.md` ⭐ **Data Quality Assessment**

### CSV Data Reports
- **Campaign Data**: `reports/campaign_data/` - Account structure and configuration
- **Performance Data**: `reports/performance_data/` - Time-series metrics and trends
- **Asset Data**: `reports/asset_data/` - Creative performance and optimization
- **Location Data**: `reports/location_data/` - Geographic performance analysis
- **Video Data**: `reports/video_data/` - Video advertising metrics and engagement

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

- **Campaign Types**: Search (TPPC campaigns), Performance Max, Display
- **Primary Services**: Impact Windows, Impact Doors, Hurricane Protection, Energy-Efficient Solutions
- **Website**: https://wrightsimpactwindowanddoor.com/
- **Phone**: 561-588-7353
- **Primary Service Area**: Florida (West Palm Beach, Punta Gorda, statewide coverage)
- **Account Status**: New Client - Strategy Development Phase
- **Experience**: 50+ years in Florida impact window and door industry

## 🚀 Google Ads Editor Import

1. Open Google Ads Editor
2. File → Import
3. Select CSV from `campaigns/` directory
4. Review and apply changes

## 📋 Campaign Structure

### Active Campaigns (Planned)
1. **TPPC - Brand** - Brand awareness and direct searches
   - Ad Group: Brand - WrightsImpact

2. **TPPC - Hurricane Protection** - Storm preparedness and hurricane defense
   - Ad Groups: Hurricane Protection - General, Hurricane Protection - Local, Hurricane Protection - West Palm Beach

3. **TPPC - Impact Windows** - Energy-efficient window solutions
   - Ad Groups: Impact Windows - General, Impact Windows - Local, Impact Windows - Florida

4. **TPPC - Impact Doors** - Security and storm-resistant doors
   - Ad Groups: Impact Doors - General, Impact Doors - Local, Impact Doors - Florida

5. **TPPC - Commercial Solutions** - Condo and commercial property solutions
   - Ad Groups: Commercial - Condos, Commercial - Builders, Commercial - Multi-Unit

6. **TPPC - Financing** - Financing options and payment plans
   - Ad Group: Financing Options

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

- Focus on Florida statewide coverage with emphasis on hurricane-prone areas
- Emphasize 50+ years experience and lifetime guarantee
- Trust signals and certifications important for high-value purchases
- Before/after project photos crucial for conversion
- Local "near me" and "Florida" searches prioritized
- Financing options messaging to overcome price objections
- Commercial property manager and HOA decision-maker targeting

## 🏠 Industry-Specific Considerations

### Impact Window & Door Services
- Hurricane Protection: Storm-resistant windows and doors
- Energy Efficiency: Improved insulation and reduced utility costs
- Noise Reduction: Sound-dampening technology
- Security Enhancement: Reinforced construction and locking systems
- Property Value Increase: Curb appeal and insurance benefits
- Insurance Cost Reduction: Lower premiums through storm protection

### Geographic Targeting
- **Primary**: West Palm Beach, FL (corporate headquarters)
- **Secondary**: Punta Gorda, FL (regional office), statewide Florida coverage
- **High-Value Areas**: Coastal regions, hurricane zones, high-rise condos
- Local intent optimization: "near me", "West Palm Beach", "Florida"
- Service area radius targeting: 25-50 mile radius from offices

### Seasonal Considerations
- **Hurricane Season (June-November)**: Peak demand for impact products
- **Storm Preparedness**: Pre-season campaigns emphasizing readiness
- **Post-Storm Response**: Emergency replacement and repair services
- **Year-Round**: Energy efficiency and property improvement messaging

### Compliance Considerations
- **Building Codes**: Local hurricane code compliance
- **Insurance Requirements**: Approved products for insurance discounts
- **Contractor Licensing**: Licensed installation requirements
- **Warranty Regulations**: Lifetime guarantee legal compliance

### Target Audiences
1. **Homeowners**: Storm protection, energy savings, property value
2. **Property Managers**: Multi-unit properties, compliance requirements
3. **HOA Boards**: Community standards, insurance considerations
4. **Builders/Developers**: New construction impact solutions
5. **Commercial Property Owners**: Security and tenant satisfaction
6. **Insurance Agents**: Policyholder recommendations

### Competitive Advantages
- 50+ years Florida experience
- Lifetime manufacturer guarantee
- Multiple financing options (PACE, cash, unsecured)
- Statewide service coverage
- Custom measurements and professional installation
- Energy efficiency certifications
- Insurance-approved products

This strategic approach positions Wright's Impact Window and Door as Florida's premier impact window and door specialist, leveraging their extensive experience and comprehensive service offerings for maximum Google Ads performance.