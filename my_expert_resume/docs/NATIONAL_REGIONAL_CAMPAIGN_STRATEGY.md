# National vs Regional Campaign Strategy - MyExpertResume

## Overview

Implemented a **two-campaign strategy** separating national and regional targeting:

1. **National Campaign** - Broad executive reach with NO regional keywords
2. **Regional Campaign** - Florida-focused with LOCAL keywords only

This approach optimizes bidding, targeting, and performance across different audience segments.

## Campaign Architecture

### National Campaign: "MyExpertResume National Executive"
**Target:** Broad national executive audience
**Budget:** $89.99 Daily (higher for national reach)
**Asset Groups:** 3 (Executive Core, Senior Executive, Career Advancement)
**Keywords:** National executive terms only (no cities/regions)

#### Asset Groups
1. **National - Executive Core** (10 search themes)
   - Executive Resume Writing Service
   - C-Suite Resume Writing Service
   - Leadership Resume Writing Service
   - VP Resume Writing Service
   - Director Resume Writing Service
   - Senior Management Resume Writing
   - Professional Resume Writing Service
   - Career Advancement Resume Service
   - Executive Career Coaching
   - Job Search Resume Service

2. **National - Senior Executive** (10 search themes)
   - Senior Executive Resume Writing
   - VP Level Resume Writing Service
   - Director Level Resume Services
   - Senior Management Resume Help
   - Executive Level Career Coaching
   - C-Level Resume Writing
   - Senior Leadership Resume Service
   - Executive Career Advancement
   - Senior Professional Resume Help
   - Management Level Resume Writing

3. **National - Career Advancement** (10 search themes)
   - Career Advancement Resume Service
   - Professional Development Resume
   - Job Search Resume Help
   - Career Transition Resume Writing
   - Executive Career Coaching
   - Professional Resume Optimization
   - Career Growth Resume Service
   - Job Advancement Resume Help
   - Professional Career Services
   - Executive Job Search Coaching

### Regional Campaign: "MyExpertResume Florida Executive"
**Target:** Florida local market
**Budget:** $59.99 Daily (regional focus)
**Asset Groups:** 2 (Executive Core, Career Services)
**Keywords:** Florida cities and regional terms only

#### Asset Groups
1. **Florida - Executive Core** (10 search themes)
   - Executive Resume Writing Service Fort Lauderdale
   - Executive Resume Writing Service Ft Lauderdale
   - Executive Resume Writing Service Miami
   - C-Suite Resume Writing Service Fort Lauderdale
   - Professional Resume Writing Service Florida
   - Career Coaching Fort Lauderdale
   - Executive Resume Service West Palm Beach
   - Resume Writing Service Tampa
   - C-Suite Resume Writing Orlando
   - Professional Resume Help Jacksonville

2. **Florida - Career Services** (10 search themes)
   - Resume Writing Fort Lauderdale
   - Career Coaching Miami Florida
   - Executive Resume Service Tampa
   - Professional Resume Help Orlando
   - Career Development Jacksonville
   - Resume Services West Palm Beach
   - Executive Career Help Fort Lauderdale
   - Professional Coaching Miami
   - Resume Writing Services Florida
   - Career Advancement Tampa

## Strategic Benefits

### Targeting Precision
**National Campaign:**
- Broad geographic reach across US
- Higher competition, higher CPC potential
- Catches national searchers and remote workers
- Brand awareness and top-of-funnel traffic

**Regional Campaign:**
- Local Florida market focus
- Lower competition, more efficient CPC
- Catches local searchers and in-person clients
- Higher conversion rates for local services

### Bidding Optimization
**Separate Budgets & Strategies:**
- National: Higher budget ($89.99) for broader reach
- Regional: Focused budget ($59.99) for efficiency
- Independent bidding strategies per campaign
- Geographic performance isolation

### Performance Tracking
**Campaign-Level Insights:**
- Compare national vs regional performance
- Optimize based on geographic conversion rates
- Adjust budgets based on market performance
- A/B test different approaches

## Technical Implementation

### Campaign Generation
```bash
# Generate National Campaign
python3 campaign_plan.py national

# Generate Florida Regional Campaign
python3 campaign_plan.py florida
```

### CSV Output
- **Complete Suite:** `MyExpertResume_Complete_Campaign_Suite_2025.csv` (contains both campaigns)

### Search Theme Strategy
**National Themes:** Pure service + industry combinations
**Regional Themes:** Service + industry + Florida location

## Content Strategy Differences

### Headlines & Copy
**National Campaign:**
- Broad appeal headlines
- National service positioning
- "Executive Resume Writing Service"
- "Professional Career Services"

**Regional Campaign:**
- Local market headlines
- Florida-specific positioning
- "Executive Resume Writing Fort Lauderdale"
- "Florida Career Coaching Services"

### Callouts & Extensions
**National:**
- "Executive Resume Service"
- "C-Suite Resume Writing"
- "National Coverage"
- "Professional Career Help"

**Regional:**
- "Fort Lauderdale Resume Service"
- "Miami Executive Resume"
- "Florida Career Coaching"
- "Local Professional Help"

## Performance Expectations

### National Campaign Metrics
- **Broader Reach:** Higher impressions, wider audience
- **Higher CPC:** More competitive national market
- **Brand Awareness:** Top-of-funnel traffic
- **Lead Quality:** Mix of national and serious job seekers

### Regional Campaign Metrics
- **Higher CTR:** More relevant local targeting
- **Lower CPC:** Less competition in local market
- **Higher Conversions:** Local intent, easier follow-up
- **Geographic Focus:** Florida market dominance

## Budget Allocation Strategy

### Recommended Split
- **National: 60%** ($89.99) - Broad reach foundation
- **Regional: 40%** ($59.99) - High-conversion local focus

### Performance-Based Adjustment
- Monitor conversion rates by campaign
- Shift budget to higher-performing campaign
- Scale winning strategies
- Geographic expansion opportunities

## Implementation Workflow

### Campaign Setup
1. **Create National Campaign** in Google Ads
2. **Create Florida Regional Campaign** in Google Ads
3. **Import National CSV** into national campaign
4. **Import Regional CSV** into Florida campaign
5. **Set Geographic Targeting:**
   - National: United States
   - Regional: Florida (radius around major cities)

### Performance Monitoring
1. **Weekly Review:** Compare campaign performance
2. **Geographic Analysis:** Track conversion by location
3. **Budget Optimization:** Shift based on ROI
4. **Content Testing:** A/B test headlines and themes

## Future Expansion

### Additional Regional Campaigns
- **Texas Campaign:** Dallas, Houston, Austin focus
- **California Campaign:** Los Angeles, San Francisco focus
- **Northeast Campaign:** New York, Boston focus

### Dynamic Campaign Creation
```bash
# Future regional campaigns
python3 campaign_plan.py texas
python3 campaign_plan.py california
python3 campaign_plan.py northeast
```

## Quality Assurance

### Validation Checks
- ✅ **No regional keywords** in national campaign
- ✅ **Only Florida keywords** in regional campaign
- ✅ **Proper budget allocation** between campaigns
- ✅ **Google Ads compliance** for both campaigns
- ✅ **Auto-correction applied** to both CSVs

### Performance Validation
- ✅ **Campaign separation** working correctly
- ✅ **Geographic targeting** properly configured
- ✅ **Budget distribution** optimized
- ✅ **Search theme relevance** maintained

## Results Summary

### ✅ Successfully Implemented
- **2 Separate Campaigns:** National + Regional strategy
- **30 Search Themes:** 10 per national asset group
- **20 Search Themes:** 10 per regional asset group
- **Geographic Precision:** National vs local targeting
- **Budget Optimization:** Independent campaign management

### 📊 Campaign Scale
- **National Campaign:** 3 asset groups, 58 rows, $89.99 budget
- **Regional Campaign:** 2 asset groups, 39 rows, $59.99 budget
- **Total Themes:** 50 search themes across both campaigns
- **Geographic Coverage:** National + Florida local markets

### 🎯 Strategic Advantages
- **Optimized Targeting:** Separate strategies for different audiences
- **Budget Efficiency:** Independent optimization per market
- **Performance Tracking:** Clear geographic performance insights
- **Scalability:** Easy expansion to additional regions

## File References

**National Campaign CSV:** `campaigns/MyExpertResume_National_Executive_Campaign_2025.csv`
**Regional Campaign CSV:** `campaigns/MyExpertResume_Florida_Executive_Campaign_2025.csv`
**Generator Script:** `tools/campaign_plan.py`
**Usage:** `python3 campaign_plan.py [national|florida]`

The national vs regional campaign strategy provides maximum flexibility and optimization for different market segments while maintaining precise geographic targeting and budget efficiency.
