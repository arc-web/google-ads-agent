# Search Campaign Ad Rules & Requirements

## Overview

**Search campaigns** use **AD GROUPS** with manual keyword targeting and **Responsive Search Ads (RSA)**. This document contains the complete rules and requirements for Search campaign ad structure, validation, and optimization.

**File Pathway**: `campaigns/Wrights_Service_NearMe_Only_2026.csv` → Search campaigns only
**Critical Path**: Search → Ad Groups → Keywords → RSA Headlines (1-15) + Descriptions (1-5)

## Search Campaign Structure Requirements

### Campaign-Level Settings (MANDATORY)
```csv
Campaign Type: Search
Networks: Google search
Search Partners: Disabled
Display Network: Disabled
Budget: $100-200 daily (based on keyword competition)
Ad Schedule: Business hours + emergency availability
```

### Ad Group Structure (MANDATORY)
**Required Fields per Ad Group:**
- `Ad Group` (name, max 30 chars)
- `Keywords` (exact match, phrase match, broad match)
- `Headlines` (1-15 headlines, 30 chars max each)
- `Descriptions` (1-5 descriptions, 90 chars max each)
- `Final URL` (landing page)

## RSA Headline Requirements (Search Specific)

### Character Limits & Technical Writing
- **Maximum**: 30 characters per headline (Google Ads API limit)
- **Optimal Range**: 22-29 characters (technical writing sweet spot)
- **Minimum**: No minimum, but optimal for value density
- **RSA Flexibility**: Up to 3 headlines per ad group for AI optimization (Google API limit)

### Headline Categories (Strategic Framework)

#### Keyword-Focused Headlines
**Purpose**: Match search intent with technical precision
**Integration**: Direct keyword integration without filler
**Examples**:
- "Impact Windows Fort Myers"
- "Hurricane Doors Naples"
- "Energy Efficient Windows FL"
- "Impact Protection Broward"

#### Service + Location Headlines
**Purpose**: Combine client services with geographic targeting
**Integration**: Support "Impact Windows and Doors in FL" requirement
**Examples**:
- "Fort Myers Impact Windows"
- "Naples Hurricane Protection"
- "Broward Impact Door Systems"
- "Florida Energy Efficient Windows"

#### Value Proposition Headlines
**Purpose**: Include client requirements with search intent
**Integration**: Intuitive inclusion of core value propositions
**Examples**:
- "Lower Insurance Impact Windows"
- "Energy Efficient Home Security"
- "Property Value Impact Doors"
- "Safeguard Home Hurricane Protection"

### Headline Validation Rules

#### Technical Writing Enforcement
- **No Filler Words**: "the", "a", "an", "or", "very", "really", "just"
- **No Em Dashes**: Avoid "—" and "–"
- **Value Density**: 22-29 character sweet spot for maximum impact
- **Keyword Integration**: Headlines must include target keywords

#### Character Efficiency Rules
```python
# Optimal RSA headline length validation
if len(headline) < 22:
    ERROR: "Too short - add value without filler words"
elif len(headline) < 25:
    WARNING: "Below optimal - consider strengthening value density"
elif len(headline) > 29:
    WARNING: "Suboptimal - consider shortening for better value density"
elif len(headline) > 30:
    ERROR: "Violates Google Ads limit"
```

## RSA Description Requirements (Search Specific)

### Character Limits & Technical Writing
- **Maximum**: 90 characters per description (Google Ads API limit)
- **Optimal Range**: 75-85 characters (technical writing sweet spot)
- **Minimum**: No minimum, but optimal for value density
- **RSA Flexibility**: Up to 2 descriptions per ad group for AI optimization (Google API limit)

### Description Categories (Strategic Framework)

#### Conversion-Focused Descriptions
**Purpose**: Drive immediate action with client requirements
**Integration**: Include call-to-action with value propositions
**Examples**:
- "Get PACE financing: 100% coverage, no down payment, 12+ months deferred. Call now!"
- "Lower insurance rates with certified impact windows. Lifetime guarantee included."

#### Benefit + Proof Descriptions
**Purpose**: Combine benefits with credibility
**Integration**: Support all 6 core client value propositions
**Examples**:
- "Improve energy efficiency by 40% while increasing home security. 50+ years experience."
- "Reduce noise and improve property value with Florida's impact protection specialists."

#### Local Authority Descriptions
**Purpose**: Establish local expertise with geographic relevance
**Integration**: Support regional positioning and local intent
**Examples**:
- "Fort Myers impact windows and doors with lifetime guarantee. Statewide service."
- "Naples hurricane protection experts. PACE financing available, no credit check required."

### Description Validation Rules

#### Technical Writing Enforcement
- **No Filler Words**: Comprehensive elimination of low-value words
- **No Em Dashes**: Use hyphens or restructure for clarity
- **Value Density**: 75-85 character sweet spot for maximum impact
- **Call-to-Action**: Must include clear next step

#### Character Efficiency Rules
```python
# Optimal RSA description length validation
if len(description) < 75:
    ERROR: "Too short - add value without filler words"
elif len(description) < 80:
    WARNING: "Below optimal - consider strengthening value density"
elif len(description) > 85:
    WARNING: "Suboptimal - consider shortening for better value density"
elif len(description) > 90:
    ERROR: "Violates Google Ads limit"
```

## Ad Group Optimization Rules

### Required Ad Group Structure
```csv
Ad Group: fort_myers_impact_windows
Keywords: "impact windows fort myers", "fort myers impact glass", "hurricane windows fort myers"
Headlines: 3 headlines (≤30 chars each, optimal 22-29)
Descriptions: 2 descriptions (≤90 chars each, optimal 75-85)
Final URL: https://wrightsimpactwindowanddoor.com/fort-myers-impact-windows
```

### Ad Group Naming Convention
**Required Format**: `[city]_[primary_service]_[modifier]`
**Examples**:
- `fort_myers_impact_windows`
- `naples_hurricane_protection`
- `broward_energy_efficiency`
- `cape_coral_impact_doors`
- `punta_gorda_commercial_windows`

### Keyword Targeting Structure
**Required Match Types**:
- **Exact Match**: `"impact windows fort myers"` (primary targeting)
- **Phrase Match**: `"fort myers impact windows"` (related searches)
- **Broad Match**: `fort myers impact windows` (discovery)

**Negative Keywords** (MANDATORY):
- DIY terms: "how to", "diy", "install"
- Competitors: specific competitor names
- Non-service: "jobs", "careers", "employment"

## Search Campaign Validation Rules

### Campaign-Level Validation
- [ ] Campaign Type = "Search"
- [ ] Networks = "Google search" only
- [ ] Search Partners = "Disabled"
- [ ] Display Network = "Disabled"
- [ ] Ad Schedule includes business hours

### Ad Group Validation
- [ ] Ad Group name ≤ 30 characters
- [ ] Keywords include exact, phrase, and broad match
- [ ] Negative keywords implemented
- [ ] Geographic targeting matches ad group name
- [ ] Final URL present and location-specific

### RSA Ad Copy Validation
- [ ] Headlines: 3 per ad group (≤30 chars each, optimal 22-29)
- [ ] Descriptions: 2 per ad group (≤90 chars each, optimal 75-85)
- [ ] Keywords integrated in headlines
- [ ] Client requirements covered across ad variations
- [ ] No filler words or em dashes

## RSA AI Optimization Rules

### Google's RSA Algorithm Optimization
**RSA Headline Selection Algorithm**:
- Google tests combinations of 3 headlines from your pool of 15
- Algorithm prioritizes relevance, performance history, and diversity
- Requires minimum 8 headlines for optimal AI performance
- Optimal: 12-15 headlines for maximum combination possibilities

**RSA Description Selection Algorithm**:
- Google tests combinations of 2 descriptions from your pool of 5
- Algorithm considers length, relevance, and conversion potential
- Requires minimum 3 descriptions for optimal AI performance
- Optimal: 4-5 descriptions for maximum testing flexibility

### Headline Combination Optimization
**Service + Location Priority**:
- Combine service headlines with location headlines for relevance
- Example: "Impact Windows" + "Fort Myers" = "Impact Windows Fort Myers"
- Algorithm favors combinations with exact keyword matches

**Value + Trust Signal Combinations**:
- Pair value propositions with credibility signals
- Example: "Lower Insurance Rates" + "Lifetime Guarantee"
- Creates compelling benefit + proof combinations

### Path Optimization for RSA
**Display Path Requirements**:
- Path 1 + Path 2: Maximum 15 characters each
- Must be relevant to landing page content
- Should include location or service keywords
- Examples: "Fort Myers" | "Impact Windows"

**Path Validation Rules**:
```python
# Path length limits
path1_max_chars: 15
path2_max_chars: 15

# Path requirements
if not row.get("Path 1", "").strip():
    ERROR: "RSA requires Path 1 for display"
if len(row.get("Path 1", "")) > 15:
    ERROR: "Path 1 exceeds 15 character limit"
```

## RSA Keyword-Ad Relevance Rules

### Keyword Integration Validation
**Headline Keyword Matching**:
- At least 1 headline per ad group must contain exact keyword
- At least 2 headlines must contain keyword variations
- Headlines should match search query intent

**Example Validation**:
```python
# For keyword "impact windows fort myers"
required_headlines = [
    "Impact Windows Fort Myers",  # Exact match
    "Fort Myers Impact Glass",    # Variation
    "Hurricane Windows Fort Myers" # Related intent
]
```

### Ad Copy Relevance Scoring
**Keyword-Ad Copy Alignment**:
- Headlines must be relevant to keyword search intent
- Descriptions must address keyword-based user needs
- Landing page must match keyword expectations

## RSA Mobile Optimization Rules

### Mobile Screen Display Optimization
**Mobile Headline Limits**:
- Headlines may be truncated on mobile screens
- Optimal: 22-26 characters for mobile readability
- Avoid headlines longer than 25 chars for mobile

**Mobile Description Optimization**:
- Mobile users scan first 2 lines (approximately 70-80 chars)
- Place most important benefits in first 75 characters
- Include call-to-action within mobile-visible text

### Mobile User Behavior Rules
**Mobile-Specific Messaging**:
- Use "near me" and local intent keywords
- Include phone numbers prominently
- Optimize for tap-to-call actions
- Consider mobile landing page speed

## RSA Seasonal/Hurricane Rules

### Hurricane Season Optimization (June-November)
**Seasonal Messaging Priority**:
- Increase emergency preparedness messaging
- Emphasize storm protection benefits
- Highlight insurance discount urgency
- Use "hurricane ready" positioning

**Off-Season Optimization (December-May)**:
- Focus on energy efficiency benefits
- Emphasize property value increases
- Highlight noise reduction features
- Use "year-round protection" positioning

### Seasonal Keyword Integration
**Hurricane Season Keywords**:
- "hurricane protection", "storm ready", "emergency windows"
- "hurricane insurance discount", "storm shutters"
- "hurricane damage repair", "emergency installation"

**Off-Season Keywords**:
- "energy efficient windows", "utility bill savings"
- "property value increase", "home improvement"
- "noise reduction windows", "quiet windows"

## RSA A/B Testing Framework Rules

### Systematic Testing Protocol
**Test Group Structure**:
- Control Group: Original RSA combinations
- Test Group A: New headline variations
- Test Group B: New description combinations
- Test Group C: New path combinations

**Testing Timeline**:
- Run tests for minimum 7 days
- Require 100 conversions per variation
- Use statistical significance (95% confidence)
- Winner selection based on CPA and conversion rate

### Performance-Based Optimization
**Winner Selection Criteria**:
- Primary: Lowest CPA with statistical significance
- Secondary: Highest conversion rate
- Tertiary: Highest click-through rate
- Must maintain client requirement inclusion

## RSA Budget Allocation Rules

### Performance-Based Budget Distribution
**High-Performing RSA Combinations**:
- Allocate 60% of budget to top 3 performing combinations
- Allocate 30% to next 5 performing combinations
- Allocate 10% to new testing combinations

**RSA Budget Optimization**:
- Daily budget adjustments based on performance
- Shift budget from underperforming to high-performing RSAs
- Maintain minimum budget for testing new combinations

### Geographic Budget Micro-Allocation
**City-Level Budget Rules**:
- Allocate budget proportional to search volume
- Increase budget for high-conversion cities
- Decrease budget for low-performing locations

## RSA Geographic Micro-Targeting Rules

### ZIP Code Level Targeting
**ZIP Code Validation Rules**:
```python
# ZIP code format validation
def validate_zip_code(zip_code: str) -> bool:
    import re
    return bool(re.match(r'^\d{5}(-\d{4})?$', zip_code))

# Geographic coverage validation
def validate_geographic_coverage(city: str, zip_codes: list) -> bool:
    # Ensure ZIP codes match city
    # Validate coverage completeness
    # Check for geographic gaps
    pass
```

**ZIP Code Optimization**:
- Target high-value ZIP codes with premium pricing
- Exclude low-opportunity ZIP codes
- Use ZIP-specific messaging for local relevance

### Neighborhood-Level Targeting
**Micro-Geographic Rules**:
- Identify high-intent neighborhoods
- Use neighborhood-specific keywords
- Target based on property values and hurricane risk
- Optimize for local competition levels

## RSA Competitor Avoidance Rules

### RSA Combination Diversity
**Avoid Cannibalization**:
- Ensure RSA combinations have different focuses
- Avoid duplicate messaging across combinations
- Create distinct value propositions per combination

**Competitive Differentiation**:
- Monitor competitor RSA combinations
- Differentiate with unique value propositions
- Avoid direct competition with own high-performing RSAs

### Deduplication Rules
**RSA Internal Deduplication**:
```python
def check_rsa_similarity(rsa1: dict, rsa2: dict) -> float:
    """Check similarity between two RSA combinations"""
    # Compare headline combinations
    # Compare description combinations
    # Return similarity score
    pass

# Deduplication threshold
MAX_SIMILARITY = 0.7  # 70% similar = too close
```

## Quality Score Optimization Rules

### RSA-Specific Quality Score Factors
**Expected CTR Optimization**:
- Target >5% CTR for primary keywords
- Monitor RSA combination performance
- Optimize based on Google's RSA insights

**Ad Relevance Enhancement**:
- Headlines must include keyword variations
- Descriptions must address user intent
- Landing pages must match ad messaging

### RSA Performance Monitoring
**RSA Insights Integration**:
- Track top-performing headline combinations
- Monitor description combination performance
- Identify best path combinations
- Optimize based on AI algorithm preferences

---

**File Pathway**: `campaigns/Wrights_Service_NearMe_Only_2026.csv`
**Validation Engine**: `comprehensive_csv_validator.py` (Enhanced with RSA-specific rules)
**Client Requirements**: Must include all 8 requirements from `CLIENT_AD_COPY_REQUESTS.md`
**RSA Optimization**: Follows Google's AI algorithm requirements for maximum performance

---

**File Pathway**: `campaigns/Wrights_Service_NearMe_Only_2026.csv`
**Validation Engine**: `comprehensive_csv_validator.py` (Search validation path)
**Client Requirements**: Must include all 8 requirements from `CLIENT_AD_COPY_REQUESTS.md`
**Technical Standards**: Follow `AD_COPY_BEST_PRACTICES.md` for optimization