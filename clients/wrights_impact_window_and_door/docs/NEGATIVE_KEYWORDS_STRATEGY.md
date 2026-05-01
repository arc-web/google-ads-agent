
# NEGATIVE KEYWORDS STRATEGY - Wright's Search Campaigns

## WHY THIS IS CRITICAL
Without negative keywords, campaigns waste budget on irrelevant searches like "free", "DIY", "cheap", etc.

## CORE NEGATIVE KEYWORD LISTS

### 1. Intent-Based Negatives
```
free, cheap, discount, bargain, low cost, budget, economical
DIY, do it yourself, how to, tutorial, guide, instructions
repair, fix, broken, damaged, replace, maintenance
parts, supplies, materials, tools, equipment
```

### 2. Geographic Negatives (Non-Service Areas)
```
miami, dade county, palm beach, broward (if not targeting)
orlando, tampa, sarasota, naples (if not in those markets)
florida statewide, all florida, statewide
```

### 3. Service Exclusions
```
roofing, siding, gutters, soffit, fascia
painting, drywall, flooring, carpet, tile
plumbing, electrical, HVAC, heating, cooling
landscaping, pool, fencing, deck
```

### 4. Competitive/Brand Terms
```
competitor company names
generic terms that don't convert
"best prices", "lowest cost", "guarantee" (unless you offer)
```

## SEARCH TERM REPORT ANALYSIS PROCESS

### Weekly Review Process:
1. **Download Search Terms Report**: Last 7 days, all campaigns
2. **Filter for Irrelevant Terms**:
   - Clicks > 0 but conversions = 0
   - Impressions > 100 but CTR < 1%
   - Cost > $10 but no conversions
3. **Categorize Negative Keywords**:
   - Exact match negatives: [brackets]
   - Phrase match negatives: "quotes"
   - Broad match negatives: no modifiers
4. **Add to Campaign-Level Negative Keywords**

### Monthly Deep Analysis:
1. **Performance Review**: Terms with high spend, low conversion
2. **Trend Analysis**: New irrelevant terms appearing
3. **Competitive Research**: What competitors are showing for
4. **Seasonal Adjustments**: Hurricane-related irrelevant terms

## NEGATIVE KEYWORD MANAGEMENT RULES

### 1. Campaign-Level vs. Ad Group-Level
- **Campaign Level**: Broad negatives that apply everywhere
- **Ad Group Level**: Specific to that service/location

### 2. Match Type Selection
- **Exact Match [ ]**: For terms you NEVER want
- **Phrase Match " "**: For phrase variations
- **Broad Match**: Only for very specific cases

### 3. Regular Maintenance
- **Weekly**: Add 5-10 new negatives from search terms
- **Monthly**: Review and optimize negative list
- **Quarterly**: Audit for conflicts or over-blocking

## AUTOMATED NEGATIVE KEYWORD TOOLS

### Google Ads Scripts for Automation:
```javascript
// Automated negative keyword addition based on performance
function main() {
  var campaign = AdsApp.campaigns().get();
  // Add logic to automatically add negatives for terms with 0 conversions
}
```

### Performance-Based Rules:
- Auto-add negatives for terms with >$50 spend and 0 conversions
- Flag terms with CTR < 0.5% for manual review
- Alert on terms with high impressions but low relevance

## NEGATIVE KEYWORD TESTING
1. **Before/After Testing**: Measure performance impact
2. **A/B Testing**: Test negative keyword additions
3. **Recovery Testing**: Ensure you're not blocking good terms
4. **Competitive Impact**: Monitor if competitors pick up blocked terms

## COMMON MISTAKES TO AVOID
- **Over-Blocking**: Don't block terms that could convert
- **Under-Blocking**: Don't let irrelevant terms waste budget
- **Match Type Errors**: Wrong match type blocks/converts incorrectly
- **No Regular Updates**: Negative lists become outdated
