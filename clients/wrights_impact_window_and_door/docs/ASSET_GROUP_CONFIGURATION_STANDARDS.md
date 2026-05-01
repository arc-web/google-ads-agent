
# ASSET GROUP CONFIGURATION STANDARDS - Wright's Search Campaigns

## REQUIRED ASSET GROUP COMPONENTS

### 1. Basic Information
- [ ] Asset Group Name: Follows naming conventions (≤30 chars)
- [ ] Campaign Association: Correct parent campaign
- [ ] Status: Disabled by default
- [ ] Type: Search (not display)

### 2. Geographic Targeting (REQUIRED)
- [ ] Target Type: ZIP codes
- [ ] City Specification: "City, FL - ZIP codes: ZIP1, ZIP2..."
- [ ] Coverage Verification: All service area ZIP codes included
- [ ] No Overlap: ZIP codes unique to this asset group

### 3. Bid Strategy Configuration (REQUIRED)
- [ ] Level: Asset group level (not campaign)
- [ ] Type: Based on data availability
  - Manual CPC: No conversion data
  - Maximize Conversions: 30+ conversions available
  - Target CPA: Good cost per lead established
  - Maximize Clicks: Optimal search terms identified
- [ ] Target CPA: Calculated as 10% above average CPL (when applicable)

### 4. Keywords (REQUIRED)
- [ ] Match Types: Broad match by default
- [ ] Structure: "service + local" format
- [ ] Examples: "impact windows fort myers near me"
- [ ] Volume: 10-20 keywords per asset group
- [ ] Relevance: Directly related to service offering

### 5. Negative Keywords (REQUIRED)
- [ ] Campaign Level: Broad negatives (free, DIY, etc.)
- [ ] Asset Group Level: Service-specific negatives
- [ ] Match Types: Exact [ ], Phrase " ", Broad
- [ ] Regular Updates: Weekly from search term reports

### 6. Ad Creative (REQUIRED)
- [ ] Headlines: 3 headlines, ≤30 chars each
- [ ] Descriptions: 2 descriptions, ≤90 chars each
- [ ] Call-to-Action: Clear next step
- [ ] Local Focus: City name included
- [ ] Service Specific: Matches asset group service

### 7. Ad Extensions (RECOMMENDED)
- [ ] Location Extensions: Business address
- [ ] Call Extensions: Primary phone number
- [ ] Sitelink Extensions: Service pages
- [ ] Callout Extensions: Key benefits

### 8. Conversion Tracking (REQUIRED for Conversion-Based Strategies)
- [ ] Actions Enabled: Website quotes, phone calls, appointments
- [ ] Attribution: Data-driven attribution
- [ ] Values Assigned: Based on service profitability
- [ ] Tracking Verified: Conversions appearing in reports

## CONFIGURATION VALIDATION CHECKLIST

### Pre-Upload Validation:
- [ ] All required components configured
- [ ] Character limits respected
- [ ] Bid strategies appropriate for data availability
- [ ] Geographic targeting accurate
- [ ] Keywords relevant and properly formatted
- [ ] Negative keywords applied
- [ ] Ad creative meets policy requirements

### Post-Upload Verification:
- [ ] Asset group created successfully
- [ ] Bid strategy applied correctly
- [ ] Geographic targeting active
- [ ] Keywords uploaded and active
- [ ] Ads approved and showing
- [ ] Extensions enabled and working

## ASSET GROUP LEVEL VS CAMPAIGN LEVEL

### Campaign Level Settings:
- Campaign Name and Status
- Budget (if applicable)
- Network Settings (Search only)
- Ad Scheduling (Business hours)
- Campaign-level negatives

### Asset Group Level Settings (REQUIRED):
- Geographic Targeting (ZIP codes)
- Bid Strategy and Targets
- Keywords and Negatives
- Ad Creative and Extensions
- Performance-specific optimizations

## CONFIGURATION STANDARDS BY BID STRATEGY

### Manual CPC Asset Groups:
- Max CPC: $2.00-$3.00 conservative
- Enhanced CPC: Disabled
- Focus: Data collection, not optimization

### Maximize Conversions Asset Groups:
- Conversion Actions: All enabled
- Attribution: Data-driven
- Focus: Conversion volume optimization

### Target CPA Asset Groups:
- Target CPA: 10% above average CPL
- Conversion Actions: Same as Maximize Conversions
- Focus: Cost control with conversion focus

### Maximize Clicks Asset Groups:
- Daily Budget: Based on conversion capacity
- Focus: Qualified traffic volume
- Prerequisites: Optimal search terms identified

## PERFORMANCE MONITORING SETUP

### Asset Group Level Tracking:
- Impressions, clicks, CTR
- CPC, conversions, CPA
- Geographic performance
- Search term discoveries
- Quality metrics

### Alert Configurations:
- CPA above target (Target CPA strategy)
- Conversion volume drops
- Geographic coverage issues
- Ad disapproval notifications

## MAINTENANCE PROCEDURES

### Weekly Maintenance:
- Review search term reports
- Update negative keywords
- Monitor performance metrics
- Check ad approval status

### Monthly Optimization:
- Recalculate Target CPA values
- Adjust bid strategies based on data
- Update ad creative performance
- Review geographic effectiveness

### Quarterly Reviews:
- Complete asset group audits
- Strategy progression evaluations
- Performance trend analysis
- Configuration optimization
