
# WRIGHT'S IMPACT WINDOW AND DOOR - SEARCH CAMPAIGN STRATEGY

## EXECUTIVE SUMMARY

Focus exclusively on Search campaigns. Performance Max campaigns are deprecated. All future optimization efforts directed toward pure Search campaign management with strategic bid strategy progression.

## SEARCH CAMPAIGN REQUIREMENTS

### Campaign Structure (Non-Negotiable)
- **Network**: Search only (no search partners, no display network)
- **Status**: Disabled by default
- **Geographic Targeting**: Asset group level (ZIP code specific)
- **Ad Scheduling**: Business hours only (8AM-6PM Mon-Sat)

### Bid Strategy Progression (Data-Driven)

#### Phase 1: Manual CPC (No Conversion Data)
**When to Use**: New campaigns or keywords without conversion history
**Settings**:
```
Bid Strategy Type: Manual CPC
Enhanced CPC: Disabled
Max CPC: Based on keyword performance data or $2.00 default
```

**Goals**:
- Gather search term data without bid automation interference
- Establish baseline keyword performance
- Identify high-converting search terms

#### Phase 2: Maximize Conversions (Conversion Data Available)
**When to Use**: Keywords show conversions linked to proper strategy
**Settings**:
```
Bid Strategy Type: Maximize Conversions
Target CPA: Set at asset group level
Conversion Actions: Website quotes, phone calls, appointment bookings
```

**Requirements**:
- Minimum 30 conversions in last 30 days
- Keywords follow proper service + local strategy
- Conversion tracking properly implemented

#### Phase 3: Target CPA (Good Cost Per Lead)
**When to Use**: Established cost per lead from performance data
**Settings**:
```
Bid Strategy Type: Target CPA
Target CPA: 10% above average cost per lead from performance report
```

**Calculation Method**:
1. Analyze performance report for average cost per lead
2. Set Target CPA = Average CPL × 1.10 (10% above average)
3. Apply at asset group level for granular control

#### Phase 4: Maximize Clicks (Proper Search Terms Acquired)
**When to Use**: Manual CPC phase has identified optimal search terms
**Settings**:
```
Bid Strategy Type: Maximize Clicks
Daily Budget: Based on conversion volume capacity
```

**Transition Triggers**:
- Search term report shows proper keyword coverage
- Negative keywords properly implemented
- Campaign shows consistent performance

## ASSET GROUP LEVEL OPTIMIZATION

### Asset Group Structure (Required)
Each asset group represents one service in one city:
```
Asset Group Name: [service]_[city]_search
Examples:
- impact_windows_fort_myers_search
- impact_doors_cape_coral_search
- hurricane_protection_naples_search
```

### Bid Strategy Application (Asset Group Level)
**Critical Requirement**: Bid strategies applied at asset group level, not campaign level
```
Campaign: wrights_lee_county_search
├── Asset Group: impact_windows_fort_myers_search (Target CPA: $45)
├── Asset Group: impact_doors_cape_coral_search (Maximize Conversions)
└── Asset Group: hurricane_protection_naples_search (Manual CPC: $2.50)
```

### Geographic Targeting (Asset Group Level)
- **ZIP Code Specific**: Each asset group targets specific city ZIP codes
- **No Campaign-Level Geography**: All geographic control at asset group level
- **Local Precision**: Complete ZIP code coverage for each city

## KEYWORD MANAGEMENT PROTOCOL

### Search Term Acquisition (Manual CPC Phase)
**Objective**: Gather proper search terms without automation interference

**Settings During Manual CPC**:
- Enhanced CPC: Disabled
- Bid Strategy: Manual CPC only
- Max CPC: Conservative bids to gather data
- Negative Keywords: Implement as search terms appear

**Transition to Maximize Clicks**:
- Search term report shows proper coverage
- Negative keywords eliminate irrelevant terms
- Performance stabilizes with good ROAS

### Conversion-Linked Keywords (Maximize Conversions Phase)
**Requirements for Maximize Conversions**:
- Keywords must show conversions
- Keywords must follow service + local strategy
- Minimum conversion volume (30+ in 30 days)

**Conversion Actions to Track**:
1. Website quote form submissions
2. Phone calls from ads (call tracking required)
3. Appointment booking form completions
4. Email lead captures

## TARGET CPA CALCULATION METHODOLOGY

### Performance Report Analysis
**Data Sources**:
- Google Ads performance reports
- Asset group level conversion data
- Cost per lead by service and location

**Calculation Steps**:
1. **Gather Data**: Pull 30-90 day performance report
2. **Calculate Average CPL**: Total cost ÷ total leads
3. **Apply Buffer**: CPL × 1.10 (10% above average)
4. **Set Target CPA**: Apply buffer at asset group level

**Example Calculation**:
```
Asset Group: impact_windows_fort_myers_search
Total Cost (30 days): $4,500
Total Leads: 120
Average CPL: $4,500 ÷ 120 = $37.50
Target CPA: $37.50 × 1.10 = $41.25
Final Setting: Target CPA $41.25 at asset group level
```

### Asset Group Level Application
**Why Asset Group Level**:
- Different services have different conversion values
- Geographic variations affect cost per lead
- Granular control prevents campaign-level averaging

**Implementation**:
- Each asset group gets its own Target CPA
- Based on that specific service + location performance
- Updated monthly based on new performance data

## CAMPAIGN SETUP CHECKLIST

### Search Campaign Creation
- [ ] Campaign Type: Search
- [ ] Networks: Search (uncheck Search Partners, Display)
- [ ] Status: Disabled by default
- [ ] Bid Strategy: Manual CPC initially
- [ ] Budget: Conservative starting budget
- [ ] Ad Schedule: Business hours only

### Asset Group Setup
- [ ] Asset Group Level Geography: ZIP code specific
- [ ] Asset Group Level Bid Strategy: Based on conversion data availability
- [ ] Conversion Tracking: All actions properly set up
- [ ] Keywords: Service + local strategy implemented

### Performance Monitoring Setup
- [ ] Conversion tracking verification
- [ ] Search term report access
- [ ] Asset group level reporting enabled
- [ ] Automated alerts for CPA changes

## BID STRATEGY TRANSITION PROTOCOL

### From Manual CPC to Maximize Conversions
**Requirements Met**:
- ✅ 30+ conversions in 30 days
- ✅ Keywords follow proper strategy
- ✅ Conversion tracking accurate

**Transition Steps**:
1. Switch bid strategy to Maximize Conversions
2. Set Target CPA at asset group level
3. Monitor performance for 7 days
4. Adjust Target CPA if needed

### From Maximize Conversions to Target CPA
**Requirements Met**:
- ✅ Good cost per lead established
- ✅ Performance data shows reliable averages
- ✅ Asset group level data available

**Transition Steps**:
1. Calculate Target CPA (10% above average CPL)
2. Switch to Target CPA at asset group level
3. Monitor for 14 days
4. Refine based on actual performance

### From Target CPA to Maximize Clicks
**Requirements Met**:
- ✅ Proper search terms acquired
- ✅ Negative keywords optimized
- ✅ Performance stabilized

**Transition Steps**:
1. Switch to Maximize Clicks
2. Set daily budget based on conversion capacity
3. Monitor click volume and quality
4. Optimize budget allocation

## PERFORMANCE MONITORING REQUIREMENTS

### Daily Monitoring
- CPA by asset group
- Conversion volume by service/location
- Search term report for new terms
- Budget pacing

### Weekly Reviews
- Asset group performance comparison
- Search term quality assessment
- Conversion attribution accuracy
- Bid strategy effectiveness

### Monthly Optimization
- Target CPA recalculation (10% above new averages)
- Asset group budget reallocation
- Negative keyword expansion
- Performance trend analysis

## SEARCH PARTNERS & DISPLAY NETWORK (DISABLED)

### Why Disabled by Default
- **Search Focus**: Pure search intent only
- **Cost Control**: No wasted spend on display impressions
- **Performance Clarity**: Uncontaminated search data
- **Local Business Model**: Search dominant for local services

### Never Enable Settings
- Search Partners: Always unchecked
- Display Network: Always unchecked
- Shopping Campaigns: Separate if needed
- Video Network: Separate campaigns only

## CONCLUSION

Wright's Search campaign strategy focuses exclusively on Search network with strategic bid strategy progression based on data availability. Asset group level control ensures granular optimization while maintaining focus on local service business requirements.
