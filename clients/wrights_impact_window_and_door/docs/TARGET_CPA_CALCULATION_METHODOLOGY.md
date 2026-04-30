
# TARGET CPA CALCULATION METHODOLOGY - Wright's Impact Window and Door

## OVERVIEW

Target CPA (Cost Per Acquisition) settings must be calculated at the asset group level using performance report data. Target CPA = Average Cost Per Lead × 1.10 (10% above average).

## PERFORMANCE REPORT ANALYSIS PROCESS

### Step 1: Data Extraction from Performance Reports
**Required Data Points**:
- Total Cost (by asset group)
- Total Conversions/Leads (by asset group) 
- Date Range (minimum 30 days, preferred 90 days)
- Asset Group Level Breakdown

**Report Configuration**:
- Time Range: Last 90 days
- Group By: Asset Group
- Metrics: Cost, Conversions, Cost/Conversion
- Filters: Only active asset groups with conversion data

### Step 2: Cost Per Lead Calculation
**Formula**: Average CPL = Total Cost ÷ Total Leads

**Example Calculation**:
```
Asset Group: impact_windows_fort_myers_search
Time Period: Last 90 days
Total Cost: $13,500
Total Leads: 360
Average CPL: $13,500 ÷ 360 = $37.50
```

### Step 3: Target CPA Setting (10% Buffer)
**Formula**: Target CPA = Average CPL × 1.10

**Example Application**:
```
Average CPL: $37.50
Buffer: 37.50 × 0.10 = $3.75
Target CPA: $37.50 + $3.75 = $41.25
Final Setting: Target CPA $41.25 at asset group level
```

### Step 4: Asset Group Level Application
**Critical**: Apply Target CPA at asset group level, not campaign level

**Example Implementation**:
```
Campaign: wrights_lee_county_search
├── Asset Group: impact_windows_fort_myers_search
│   └── Target CPA: $41.25 (based on $37.50 avg × 1.10)
├── Asset Group: impact_doors_cape_coral_search  
│   └── Target CPA: $38.50 (based on $35.00 avg × 1.10)
└── Asset Group: hurricane_protection_naples_search
    └── Target CPA: $52.25 (based on $47.50 avg × 1.10)
```

## MONTHLY RECALCULATION PROCESS

### Trigger Events
- Monthly performance review (1st of each month)
- Significant performance changes (±25% CPA shift)
- New asset groups with 30+ conversions
- Seasonal demand pattern changes

### Recalculation Steps
1. **Pull Fresh Data**: 90-day performance report
2. **Calculate New Averages**: Update CPL for each asset group
3. **Apply 10% Buffer**: CPL × 1.10 for new Target CPA
4. **Update Settings**: Apply new Target CPA at asset group level
5. **Monitor Impact**: Track performance for 7-14 days post-change

## BID STRATEGY QUALIFICATION CRITERIA

### Requirements for Target CPA Implementation
- **Conversion Volume**: Minimum 30 conversions in 30 days
- **Data Stability**: 90-day performance history
- **CPL Consistency**: Standard deviation <25% of average
- **Asset Group Maturity**: Active for minimum 60 days

### Conversion Quality Standards
- **Lead Quality**: >70% qualified leads (phone calls or quotes)
- **Geographic Accuracy**: >80% leads from target ZIP codes
- **Service Alignment**: Leads match asset group service focus
- **Duplicate Removal**: No duplicate leads in calculation

## TARGET CPA RANGE GUIDELINES

### Service-Based CPA Ranges (Wright's Market)
```
Impact Windows: $35-55 per lead
Impact Doors: $30-50 per lead  
Hurricane Protection: $40-65 per lead
Energy Efficiency: $25-45 per lead
Commercial Solutions: $60-100 per lead
```

### Geographic CPA Modifiers
```
Fort Myers: Base rates (primary market)
Cape Coral: -10% (value market)
Naples: +15% (luxury market)
Fort Lauderdale: +5% (urban market)
Pompano Beach: Base rates
Hollywood: -5% (accessible market)
```

### Seasonal CPA Adjustments
```
Peak Season (Jun-Nov): +20% to Target CPA
Off-Season (Dec-May): -15% to Target CPA
```

## PERFORMANCE MONITORING REQUIREMENTS

### Daily Monitoring
- **CPA vs Target**: Compare actual CPA to Target CPA
- **Conversion Volume**: Ensure sufficient conversion flow
- **Budget Pacing**: Monitor spend vs. conversion capacity
- **Alert Triggers**: CPA > Target CPA × 1.25

### Weekly Reviews
- **Asset Group Performance**: CPA trends by service/location
- **Target CPA Effectiveness**: Conversion volume vs. cost control
- **Geographic Performance**: ZIP code level attribution
- **Bid Strategy Stability**: Minimize strategy changes

### Monthly Recalculation Reviews
- **CPL Trend Analysis**: Identify improving/worsening performance
- **Target CPA Adjustments**: Update based on new averages
- **Asset Group Optimization**: Reallocate budget based on performance
- **Strategy Effectiveness**: Evaluate Target CPA vs. Maximize Conversions

## TROUBLESHOOTING TARGET CPA ISSUES

### CPA Too High (Above Target)
**Diagnosis**:
- Competition increased in market
- Audience quality declined
- Geographic targeting too broad
- Creative performance degraded

**Solutions**:
- Increase Target CPA temporarily (+15%)
- Refine audience targeting
- Add negative keywords
- Improve ad creative quality

### CPA Too Low (Below Target × 0.8)
**Diagnosis**:
- Competition decreased
- Audience quality improved significantly
- Geographic targeting too narrow
- High-converting periods

**Solutions**:
- Decrease Target CPA (-10%)
- Expand audience targeting
- Increase geographic coverage
- Monitor for sustained performance

### Insufficient Conversion Volume
**Diagnosis**:
- Target CPA too aggressive (too low)
- Audience size too small
- Geographic coverage insufficient
- Creative not compelling enough

**Solutions**:
- Increase Target CPA (+20%)
- Expand audience segments
- Add more ZIP codes
- Test new creative variations

## BID STRATEGY TRANSITION PROTOCOLS

### From Maximize Conversions to Target CPA
**Requirements**:
- 90+ days of Maximize Conversions data
- Stable CPA performance (<20% variance)
- Clear average CPL established
- Asset group level data sufficient

**Transition Process**:
1. Calculate Target CPA (avg CPL × 1.10)
2. Switch to Target CPA strategy
3. Monitor for 14 days
4. Adjust Target CPA based on actual performance

### Target CPA Optimization
**Monthly Adjustments**:
- If CPA consistently below target: Decrease by 5-10%
- If CPA consistently above target: Increase by 10-15%
- If performance unstable: Return to Maximize Conversions temporarily

## CONCLUSION

Target CPA implementation requires precise calculation using performance report data with a 10% buffer above average cost per lead. Applied at asset group level for granular control, this strategy balances cost control with conversion volume for optimal Search campaign performance.
