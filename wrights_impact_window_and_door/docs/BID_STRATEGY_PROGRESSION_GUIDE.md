
# BID STRATEGY PROGRESSION GUIDE - Wright's Search Campaigns

## OVERVIEW

Wright's Search campaigns use data-driven bid strategy progression. Start with Manual CPC to gather data, progress to Maximize Conversions with conversion data, advance to Target CPA with good cost per lead, and finalize with Maximize Clicks once optimal search terms are identified.

## PHASE 1: MANUAL CPC (DATA GATHERING)

### When to Use Manual CPC
- **New Campaigns**: No conversion history available
- **New Keywords**: Untested search terms
- **Strategy Testing**: Before automation interference
- **Data Collection**: Need search term insights

### Manual CPC Settings
```
Bid Strategy Type: Manual CPC
Enhanced CPC: Disabled (critical - prevents automation)
Max CPC: $2.00-$3.00 (conservative starting bids)
Asset Group Level: Yes (never campaign level)
```

### Manual CPC Objectives
- **Search Term Discovery**: Gather actual search queries
- **Performance Baseline**: Establish keyword performance without automation
- **Negative Keyword Identification**: Find irrelevant search terms
- **Conversion Data Collection**: Build conversion history

### Manual CPC Duration
- **Minimum**: 30 days with active spend
- **Target**: 60-90 days for robust data
- **Maximum**: 120 days before strategy evaluation

### Transition Triggers to Maximize Conversions
- ✅ 30+ conversions in 30 days
- ✅ Keywords show proper service + local intent
- ✅ Conversion tracking accurate and verified
- ✅ Search term report shows relevant queries

## PHASE 2: MAXIMIZE CONVERSIONS (CONVERSION OPTIMIZATION)

### When to Use Maximize Conversions
- **Conversion Data Available**: Keywords show consistent conversions
- **Proper Strategy Alignment**: Keywords follow service + local structure
- **Volume Sufficient**: Enough conversions for algorithm learning
- **Quality Verified**: Conversions are qualified leads

### Maximize Conversions Settings
```
Bid Strategy Type: Maximize Conversions
Conversion Actions: Website quotes, phone calls, appointment bookings
Attribution Model: Data-driven attribution (preferred)
Asset Group Level: Yes (never campaign level)
```

### Maximize Conversions Benefits
- **Automated Optimization**: Algorithm finds optimal CPC bids
- **Conversion Focus**: Prioritizes actions over clicks
- **Scale Efficiency**: Handles high-volume campaigns
- **Performance Learning**: Improves with more data

### Maximize Conversions Duration
- **Minimum**: 30 days for algorithm learning
- **Target**: 60-90 days for optimization maturity
- **Monitoring**: Daily CPA and conversion volume checks

### Transition Triggers to Target CPA
- ✅ Good cost per lead established (<$60 CPL average)
- ✅ CPA stability (<20% variance over 30 days)
- ✅ Performance report shows reliable averages
- ✅ Asset group level data sufficient for CPA calculation

## PHASE 3: TARGET CPA (COST CONTROL)

### When to Use Target CPA
- **Established CPL**: Clear average cost per lead from data
- **Cost Control Needed**: Want to maintain CPA within specific range
- **Volume Predictable**: Consistent conversion flow
- **Budget Efficiency**: Need cost predictability

### Target CPA Calculation (Critical)
```
Formula: Target CPA = Average Cost Per Lead × 1.10
Example: If avg CPL = $40, then Target CPA = $44
Application: Asset group level only (never campaign level)
```

### Target CPA Settings
```
Bid Strategy Type: Target CPA
Target CPA: Calculated value (10% above average CPL)
Conversion Actions: Same as Maximize Conversions
Asset Group Level: Mandatory
```

### Target CPA Benefits
- **Cost Predictability**: Maintains CPA within target range
- **Volume Optimization**: Balances cost control with conversion volume
- **Granular Control**: Asset group level precision
- **Performance Stability**: Reduces CPA volatility

### Target CPA Monitoring
- **Daily**: CPA vs Target CPA variance
- **Weekly**: Conversion volume trends
- **Monthly**: Target CPA recalculation (10% above new averages)

### Transition Triggers to Maximize Clicks
- ✅ Optimal search terms identified from Manual CPC phase
- ✅ Negative keywords fully implemented
- ✅ Target CPA consistently achieved
- ✅ Performance stabilized with good ROAS

## PHASE 4: MAXIMIZE CLICKS (SCALE OPTIMIZATION)

### When to Use Maximize Clicks
- **Search Terms Optimized**: Proper keywords identified and negative keywords applied
- **Performance Stable**: Consistent ROAS and conversion quality
- **Volume Focus**: Want to maximize qualified traffic volume
- **Budget Efficiency**: Can handle increased scale

### Maximize Clicks Settings
```
Bid Strategy Type: Maximize Clicks
Daily Budget: Based on conversion capacity × target CPA
Asset Group Level: Yes
```

### Maximize Clicks Benefits
- **Traffic Scale**: Maximizes qualified click volume
- **Cost Efficiency**: Lower CPC through volume optimization
- **Search Term Utilization**: Makes full use of optimized keyword set
- **Performance Stability**: Less volatile than conversion-focused bidding

### Maximize Clicks Management
- **Budget Setting**: Conversion capacity × target CPA × safety buffer
- **Performance Monitoring**: Click quality and conversion rate maintenance
- **Scale Optimization**: Gradual budget increases based on performance

## PROGRESSION TIMING GUIDELINES

### Typical Campaign Lifecycle
```
Days 1-90: Manual CPC (data gathering)
Days 91-180: Maximize Conversions (optimization learning)
Days 181-365: Target CPA (cost control and scale)
Day 366+: Maximize Clicks (volume optimization)
```

### Acceleration Opportunities
- **Fast Track**: Skip Manual CPC if rich conversion data exists
- **Slow Down**: Extend Manual CPC if search terms unclear
- **Reset**: Return to Manual CPC if performance degrades

### Performance-Based Acceleration
- **Excellent Data**: Move from Manual CPC to Target CPA in 45 days
- **Good Data**: Standard 90-day Manual CPC period
- **Poor Data**: Extend Manual CPC up to 120 days

## ASSET GROUP LEVEL IMPLEMENTATION

### Why Asset Group Level (Critical)
```
Campaign: wrights_lee_county_search
├── Asset Group: impact_windows_fort_myers_search (Target CPA: $44)
├── Asset Group: impact_doors_cape_coral_search (Maximize Conversions)
└── Asset Group: hurricane_protection_naples_search (Manual CPC: $2.50)
```

### Asset Group Strategy Benefits
- **Service Precision**: Different services have different economics
- **Geographic Variance**: Local market conditions affect performance
- **Granular Control**: Optimize each service + location combination
- **Performance Isolation**: Issues in one don't affect others

## MONITORING AND ALERTS

### Phase-Specific Monitoring
- **Manual CPC**: Search term report and keyword performance
- **Maximize Conversions**: CPA trends and conversion volume
- **Target CPA**: CPA vs target variance and budget efficiency
- **Maximize Clicks**: Click volume, CTR, and conversion quality

### Alert Triggers
- **CPA Deviation**: >25% from target (any phase)
- **Conversion Drop**: >30% decrease in volume
- **Budget Waste**: >20% over daily budget
- **Quality Decline**: Conversion rate drop >25%

### Monthly Strategy Reviews
- **Progress Assessment**: Is campaign ready for next phase?
- **Performance Validation**: Current phase delivering expected results?
- **Optimization Opportunities**: Adjustments within current phase?
- **Timeline Adjustments**: Accelerate or delay progression?

## TROUBLESHOOTING PROGRESSION ISSUES

### Stuck in Manual CPC
**Symptoms**: Poor conversion data, unclear search terms
**Solutions**:
- Increase Max CPC temporarily
- Expand keyword targeting
- Improve ad creative quality
- Check conversion tracking setup

### Maximize Conversions Instability
**Symptoms**: CPA volatility, inconsistent performance
**Solutions**:
- Return to Manual CPC temporarily
- Refine audience targeting
- Improve conversion quality
- Increase conversion volume minimum

### Target CPA Not Achieving Goals
**Symptoms**: Consistently above target CPA
**Solutions**:
- Increase Target CPA (+15%)
- Refine audience segments
- Add negative keywords
- Improve landing page quality

## CONCLUSION

Bid strategy progression follows a data-driven path from Manual CPC data gathering through automated optimization phases. Each phase builds on the previous, ensuring campaigns reach Maximize Clicks only after optimal search terms and cost structures are established.
