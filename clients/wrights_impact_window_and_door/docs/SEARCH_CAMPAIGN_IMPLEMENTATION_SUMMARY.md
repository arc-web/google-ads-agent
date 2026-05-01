
# WRIGHT'S SEARCH CAMPAIGN IMPLEMENTATION SUMMARY

## EXECUTIVE SUMMARY

Complete shift from Performance Max to Search campaigns only. No search partners or display network. Asset group level bid strategies with data-driven progression from Manual CPC to Maximize Clicks.

## SEARCH CAMPAIGN STRUCTURE (FINAL)

### Campaign Configuration (Non-Negotiable)
- **Campaign Type**: Search only
- **Networks**: Search (uncheck Search Partners, Display Network)
- **Status**: Disabled by default
- **Ad Schedule**: Monday-Saturday 8AM-6PM
- **Geographic Targeting**: Asset group level only

### Asset Group Structure (Service + Local)
```
Campaign: wrights_lee_county_search
├── impact_windows_fort_myers_search
├── impact_doors_fort_myers_search
├── hurricane_protection_fort_myers_search
├── energy_efficiency_fort_myers_search
├── commercial_solutions_fort_myers_search
├── impact_windows_cape_coral_search
├── impact_doors_cape_coral_search
├── hurricane_protection_cape_coral_search
├── energy_efficiency_cape_coral_search
├── commercial_solutions_cape_coral_search
├── impact_windows_naples_search
├── impact_doors_naples_search
├── hurricane_protection_naples_search
├── energy_efficiency_naples_search
└── commercial_solutions_naples_search

Campaign: wrights_broward_county_search
├── impact_windows_fort_lauderdale_search
├── impact_doors_fort_lauderdale_search
├── hurricane_protection_fort_lauderdale_search
├── energy_efficiency_fort_lauderdale_search
├── commercial_solutions_fort_lauderdale_search
├── impact_windows_pompano_beach_search
├── impact_doors_pompano_beach_search
├── hurricane_protection_pompano_beach_search
├── energy_efficiency_pompano_beach_search
├── commercial_solutions_pompano_beach_search
├── impact_windows_hollywood_search
├── impact_doors_hollywood_search
├── hurricane_protection_hollywood_search
├── energy_efficiency_hollywood_search
└── commercial_solutions_hollywood_search
```

## BID STRATEGY IMPLEMENTATION BY DATA AVAILABILITY

### Phase 1: Manual CPC (No Conversion Data)
**Settings**:
```
Bid Strategy Type: Manual CPC
Enhanced CPC: Disabled
Max CPC: $2.00-$3.00
Applied At: Asset Group Level
Purpose: Gather search term data
```

**Example Implementation**:
```
Asset Group: impact_windows_fort_myers_search
Bid Strategy: Manual CPC
Max CPC: $2.00
Enhanced CPC: Disabled
```

### Phase 2: Maximize Conversions (Conversion Data Available)
**Requirements**: 30+ conversions, proper keyword strategy
**Settings**:
```
Bid Strategy Type: Maximize Conversions
Conversion Actions: Quotes, calls, appointments
Attribution: Data-driven
Applied At: Asset Group Level
```

**Example Implementation**:
```
Asset Group: impact_doors_fort_myers_search
Bid Strategy: Maximize Conversions
Conversion Actions: All tracked actions
```

### Phase 3: Target CPA (Good Cost Per Lead)
**Requirements**: Established average cost per lead
**Calculation**: Target CPA = Average CPL × 1.10 (10% above average)
**Settings**:
```
Bid Strategy Type: Target CPA
Target CPA: Calculated value at asset group level
Applied At: Asset Group Level Only
```

**Example Implementation**:
```
Asset Group: hurricane_protection_fort_myers_search
Bid Strategy: Target CPA
Target CPA: $41.25 (based on $37.50 avg × 1.10)
```

### Phase 4: Maximize Clicks (Optimal Search Terms)
**Requirements**: Proper search terms identified, negative keywords applied
**Settings**:
```
Bid Strategy Type: Maximize Clicks
Daily Budget: Based on conversion capacity
Applied At: Asset Group Level
```

**Example Implementation**:
```
Asset Group: energy_efficiency_fort_myers_search
Bid Strategy: Maximize Clicks
Daily Budget: Calculated based on performance
```

## TARGET CPA CALCULATION EXAMPLES

### Performance Report Data Analysis
**Source**: Google Ads performance reports (30-90 days)
**Required Columns**: Asset Group, Cost, Conversions, Cost/Conversion

### Calculation Examples
```
1. Impact Windows Fort Myers
   Total Cost: $4,500 | Total Leads: 120
   Average CPL: $4,500 ÷ 120 = $37.50
   Target CPA: $37.50 × 1.10 = $41.25

2. Impact Doors Cape Coral  
   Total Cost: $3,200 | Total Leads: 100
   Average CPL: $3,200 ÷ 100 = $32.00
   Target CPA: $32.00 × 1.10 = $35.20

3. Hurricane Protection Naples
   Total Cost: $7,125 | Total Leads: 135
   Average CPL: $7,125 ÷ 135 = $52.78
   Target CPA: $52.78 × 1.10 = $58.06
```

### Monthly Recalculation Process
1. Pull 90-day performance report
2. Calculate new average CPL per asset group
3. Apply 10% buffer (CPL × 1.10)
4. Update Target CPA at asset group level
5. Monitor performance for 7-14 days

## IMPLEMENTATION CHECKLIST

### Campaign Setup
- [ ] Campaign Type: Search
- [ ] Networks: Search only (no partners/display)
- [ ] Status: Disabled
- [ ] Budget: Conservative starting amount
- [ ] Ad Schedule: Business hours only

### Asset Group Setup
- [ ] Geographic targeting: ZIP code specific
- [ ] Bid strategy: Based on data availability
- [ ] Keywords: Service + local format
- [ ] Conversion tracking: All actions enabled

### Performance Monitoring
- [ ] Search term reports: Enabled
- [ ] Asset group reporting: Enabled
- [ ] Conversion tracking: Verified
- [ ] Automated alerts: Configured

## SEARCH NETWORK ONLY REQUIREMENTS

### Disabled by Default
- **Search Partners**: Always unchecked
- **Display Network**: Always unchecked
- **Shopping**: Separate campaigns if needed
- **Video**: Separate campaigns only

### Why Search Only
- **Intent Clarity**: Pure search intent
- **Cost Control**: No display waste
- **Performance Tracking**: Clean data
- **Local Business**: Search dominant

## BID STRATEGY TRANSITION TRIGGERS

### Manual CPC → Maximize Conversions
- ✅ 30+ conversions in 30 days
- ✅ Keywords follow service + local strategy
- ✅ Conversion tracking verified
- ✅ Search terms show proper intent

### Maximize Conversions → Target CPA
- ✅ Good cost per lead established
- ✅ CPA stability achieved
- ✅ Performance data shows reliable averages
- ✅ Asset group level data sufficient

### Target CPA → Maximize Clicks
- ✅ Optimal search terms identified
- ✅ Negative keywords implemented
- ✅ Performance stabilized
- ✅ ROAS consistently positive

## CONCLUSION

Wright's Search campaign implementation focuses exclusively on Search network with asset group level bid strategy progression. Manual CPC for data gathering, Maximize Conversions for optimization, Target CPA for cost control (10% above average CPL), and Maximize Clicks for scale - all applied at asset group level for granular control.
