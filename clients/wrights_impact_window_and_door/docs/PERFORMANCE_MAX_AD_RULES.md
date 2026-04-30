# Performance Max Campaign Ad Rules & Requirements

## Overview

**Performance Max (PMAX) campaigns** use **ASSET GROUPS** and Google's AI to automatically optimize ad delivery across all Google networks. This document contains the complete rules and requirements for PMAX ad structure, validation, and optimization.

**File Pathway**: `campaigns/Wrights_Performance_Max_2026.csv` → PMAX campaigns only
**Critical Path**: PMAX → Asset Groups → Headlines (1-5) + Descriptions (1-5) + Images/Videos

## PMAX Campaign Structure Requirements

### Campaign-Level Settings (MANDATORY)
```csv
Campaign Type: Performance Max
Networks: Google search, Search Partners, Display Network, YouTube
Budget: $150-300 daily (based on service value)
Brand guidelines: Disabled
EU political ads: Doesn't have EU political ads
```

### Asset Group Structure (MANDATORY)
**Required Fields per Asset Group:**
- `Asset Group` (name, max 30 chars)
- `Final URL` (landing page)
- `Headlines` (1-5 headlines, 30 chars max each)
- `Descriptions` (1-5 descriptions, 90 chars max each)
- `Images/Videos` (optional but recommended)

## Headline Requirements (PMAX Specific)

### Character Limits & Technical Writing
- **Maximum**: 30 characters per headline
- **Optimal Range**: 22-29 characters (technical writing sweet spot)
- **Minimum**: 22 characters (no filler words)
- **Jam-Pack Value**: Every character must contribute to conversion

### Headline Categories (Strategic Framework)

#### Authority & Leadership Headlines
**Purpose**: Establish Florida market leadership
**Integration**: Combine with client requirements
**Examples**:
- "Florida's #1 Impact Protection"
- "Leading Florida Storm Defense"
- "Florida Impact Window Experts"

#### Service Excellence Headlines
**Purpose**: Highlight specific services with technical precision
**Integration**: Support client's 6 core value propositions
**Examples**:
- "Energy-Efficient Impact Windows"
- "Hurricane Impact Door Systems"
- "Lifetime Guaranteed Protection"

#### Regional Authority Headlines
**Purpose**: Demonstrate local expertise and coverage
**Integration**: Support "Impact Windows and Doors in FL" requirement
**Examples**:
- "Fort Myers Impact Protection"
- "Naples Storm Defense Systems"
- "Broward County Impact Experts"

#### Value Proposition Headlines
**Purpose**: Communicate specific benefits and savings
**Integration**: Support client's insurance, security, property value requirements
**Examples**:
- "Lower Insurance Rates Today"
- "Increase Home Security Now"
- "Improve Property Value Fast"

### Headline Validation Rules

#### Technical Writing Enforcement
- **No Filler Words**: "the", "a", "an", "or", "very", "really", "just"
- **No Em Dashes**: Avoid "—" and "–"
- **Value Density**: 22-29 character sweet spot for maximum impact
- **Client Requirements**: Intuitive inclusion of all 8 client requirements

#### Character Efficiency Rules
```python
# Optimal headline length validation
if len(headline) < 22:
    ERROR: "Too short - add value without filler words"
elif len(headline) > 29:
    WARNING: "Suboptimal - consider shortening for better value density"
elif len(headline) > 30:
    ERROR: "Violates Google Ads limit"
```

## Description Requirements (PMAX Specific)

### Character Limits & Technical Writing
- **Maximum**: 90 characters per description
- **Optimal Range**: 75-85 characters (technical writing sweet spot)
- **Minimum**: 75 characters (no filler words)
- **Jam-Pack Value**: Every character must contribute to conversion

### Description Categories (Strategic Framework)

#### Value Amplification Descriptions
**Purpose**: Amplify client's value propositions with measurable benefits
**Integration**: Support all 6 core client requirements
**Examples**:
- "Improve energy efficiency and lower utility bills by up to 40% with our impact windows"
- "Increase home security while reducing insurance rates through certified impact protection"

#### Technical Benefit Descriptions
**Purpose**: Provide specific, measurable technical benefits
**Integration**: Support financing and guarantee requirements
**Examples**:
- "PACE financing: 100% coverage, no down payment, 12+ months deferred payments"
- "Lifetime manufacturer guarantee on all Florida impact windows and doors"

#### Trust & Authority Descriptions
**Purpose**: Build credibility with Florida market positioning
**Integration**: Support "50+ years" and "lifetime guarantee" positioning
**Examples**:
- "50+ years protecting Florida homes with lifetime guaranteed impact protection"
- "State-certified installation with professional measurements and custom solutions"

### Description Validation Rules

#### Technical Writing Enforcement
- **No Filler Words**: Comprehensive elimination of low-value words
- **No Em Dashes**: Use hyphens or restructure for clarity
- **Value Density**: 75-85 character sweet spot for maximum impact
- **Client Requirements**: Complete coverage of all 8 client requirements

#### Character Efficiency Rules
```python
# Optimal description length validation
if len(description) < 75:
    ERROR: "Too short - add value without filler words"
elif len(description) > 85:
    WARNING: "Suboptimal - consider shortening for better value density"
elif len(description) > 90:
    ERROR: "Violates Google Ads limit"
```

## Asset Group Optimization Rules

### Required Asset Group Structure
```csv
Asset Group: hurricane_protection_regional
Final URL: https://wrightsimpactwindowanddoor.com/hurricane-protection
Headlines: 3-5 headlines (22-29 chars each)
Descriptions: 2-5 descriptions (75-85 chars each)
Images: 3-5 high-quality images (1200x628 recommended)
Videos: 1-2 videos (15-30 seconds)
```

### Asset Group Naming Convention
**Required Format**: `[service_type]_[geographic_focus]`
**Examples**:
- `hurricane_protection_regional`
- `energy_efficiency_regional`
- `impact_windows_fort_myers`
- `impact_doors_naples`
- `financing_options_statewide`

### Geographic Targeting Integration
**Regional Asset Groups**:
- Must include county/state targeting
- Client requirements: "Impact Windows and Doors in FL"
- Geographic keywords in headlines and descriptions

**Local Asset Groups**:
- City-specific targeting with ZIP codes
- Local intent keywords: "near me", city names
- Localized client requirements integration

## PMAX-Specific Validation Rules

### Campaign-Level Validation
- [ ] Campaign Type = "Performance Max"
- [ ] Networks include Search, Display, YouTube
- [ ] Brand guidelines = "Disabled"
- [ ] EU political ads = "Doesn't have EU political ads"
- [ ] Budget ≥ $150 daily

### Asset Group Validation
- [ ] Asset Group name ≤ 30 characters
- [ ] Final URL present and functional
- [ ] At least 3 headlines (22-29 chars each)
- [ ] At least 2 descriptions (75-85 chars each)
- [ ] Client requirements intuitively included
- [ ] No filler words or em dashes

### Ad Copy Validation
- [ ] Headlines: 22-29 chars optimal (technical writing)
- [ ] Descriptions: 75-85 chars optimal (technical writing)
- [ ] Client requirements: 100% coverage across asset group
- [ ] Value density: Maximum impact per character
- [ ] Technical precision: No ambiguity or filler

## Performance Monitoring & Optimization

### Key Metrics to Track
- **Impression Share**: Target >70% across networks
- **Click-Through Rate**: Monitor by asset group
- **Conversion Rate**: Track by geographic targeting
- **Cost Per Acquisition**: Target <$100

### Optimization Rules
- **Asset Group Performance**: Remove underperforming asset groups
- **Geographic Expansion**: Scale high-performing regional targeting
- **Creative Testing**: A/B test headline and description variations
- **Client Requirement Coverage**: Ensure all requirements maintained during optimization

---

**File Pathway**: `campaigns/Wrights_Performance_Max_2026.csv`
**Validation Engine**: `comprehensive_csv_validator.py` (PMAX validation path)
**Client Requirements**: Must include all 8 requirements from `CLIENT_AD_COPY_REQUESTS.md`
**Technical Standards**: Follow `AD_COPY_BEST_PRACTICES.md` for optimization