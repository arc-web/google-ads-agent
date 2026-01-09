
# BID STRATEGY CONFLICT PREVENTION - Wright's Search Campaigns

## BID STRATEGY LEVEL REQUIREMENTS

### Campaign Level:
- **Bid Strategy Type**: Must be set to "Manual CPC" at campaign level
- **Reason**: Allows asset group level control without conflicts
- **Setting**: All campaigns use Manual CPC at campaign level

### Asset Group Level:
- **Individual Control**: Each asset group has its own bid strategy
- **No Conflicts**: Campaign level doesn't override asset group settings
- **Supported Strategies**:
  - Manual CPC (no conversion data)
  - Maximize Conversions (conversion data available)
  - Target CPA (good cost per lead)
  - Maximize Clicks (optimal search terms)

## CONFLICT PREVENTION RULES

### Rule 1: Campaign Level Always Manual CPC
```
Campaign: wrights_lee_county_search
Bid Strategy: Manual CPC (campaign level)
├── Asset Group: windows_fm_search (Maximize Conversions)
├── Asset Group: doors_fm_search (Target CPA: $41.25)
└── Asset Group: hurricane_fm_search (Manual CPC: $2.50)
```

### Rule 2: Asset Group Strategies Independent
- Asset groups can have different strategies within same campaign
- No interaction between asset group strategies
- Each asset group optimized independently

### Rule 3: Strategy Progression Per Asset Group
- Move strategies based on THAT asset group's data
- Don't change all asset groups simultaneously
- Monitor each asset group performance individually

## CONFLICT DETECTION CHECKLIST

### Before Upload:
- [ ] Campaign bid strategy = Manual CPC
- [ ] Asset group strategies vary appropriately
- [ ] No duplicate Target CPA values across asset groups
- [ ] Conversion tracking enabled for conversion-based strategies

### After Upload:
- [ ] Verify campaign settings in Google Ads
- [ ] Check asset group strategy assignments
- [ ] Confirm no error messages about conflicts
- [ ] Test bid strategy functionality

## TROUBLESHOOTING CONFLICTS

### Symptom: "Bid strategy not compatible"
**Cause**: Wrong campaign level setting
**Fix**: Ensure campaign uses Manual CPC

### Symptom: "Asset group strategy ignored"
**Cause**: Campaign strategy overriding
**Fix**: Change campaign to Manual CPC

### Symptom: "Cannot set Target CPA"
**Cause**: Insufficient conversion data
**Fix**: Use Maximize Conversions first, then Target CPA

### Symptom: Multiple asset groups with same strategy
**Cause**: Not individualized by performance data
**Fix**: Set strategies based on each asset group's data
