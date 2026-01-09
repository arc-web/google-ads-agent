# Campaign Architecture Pathways - NO CONFUSION ALLOWED

## Critical Pathways Overview

This document provides **CRYSTAL CLEAR** pathways for each campaign type to eliminate confusion between Performance Max and Search campaign structures.

## 🚨 CRITICAL WARNING: DIFFERENT CAMPAIGN TYPES = DIFFERENT RULES

**Performance Max** and **Search** campaigns have **COMPLETELY DIFFERENT** structures, validation rules, and file pathways. **DO NOT MIX THEM UP**.

---

## Performance Max Campaigns (PMAX)

### File Pathway
```
campaigns/Wrights_Performance_Max_2026.csv
```

### Campaign Structure
```
CAMPAIGN (Performance Max)
├── Networks: Google search + Search Partners + Display + YouTube
├── Budget: $150-300 daily
├── Brand guidelines: Disabled
├── EU political ads: Doesn't have EU political ads
│
└── ASSET GROUPS (3-5 per campaign)
    ├── Asset Group Name (max 30 chars)
    ├── Final URL (required)
    ├── Headlines 1-5 (22-29 chars each, optimal)
    ├── Descriptions 1-5 (75-85 chars each, optimal)
    ├── Images (3-5 recommended)
    ├── Videos (1-2 optional)
    └── Geographic Targeting (Regional + City + ZIP)
```

### Validation Rules Applied
- ✅ **PERFORMANCE_MAX_AD_RULES.md**
- ✅ PMAX validation path in CSV validator
- ✅ Asset Group validation (not Ad Group)
- ✅ 3-5 headlines per asset group
- ✅ 2-5 descriptions per asset group

### Client Requirements Integration
- ✅ All 8 client requirements included across asset groups
- ✅ Intuitive integration within technical writing standards
- ✅ Florida positioning in regional asset groups
- ✅ PACE financing in financing-focused asset groups

---

## Search Campaigns (RSA)

### File Pathway
```
campaigns/Wrights_Service_NearMe_Only_2026.csv
```

### Campaign Structure
```
CAMPAIGN (Search)
├── Networks: Google search only
├── Search Partners: Disabled
├── Display Network: Disabled
├── Budget: $100-200 daily
│
└── AD GROUPS (5-20 per campaign)
    ├── Ad Group Name (max 30 chars)
    ├── Keywords (exact + phrase + broad match)
    ├── Negative Keywords (required)
    ├── Headlines 1-15 (22-29 chars each, optimal)
    ├── Descriptions 1-5 (75-85 chars each, optimal)
    ├── Final URL (required)
    └── Geographic Targeting (integrated in keywords)
```

### Validation Rules Applied
- ✅ **SEARCH_CAMPAIGN_AD_RULES.md**
- ✅ Search validation path in CSV validator
- ✅ Ad Group validation (not Asset Group)
- ✅ 8-12 headlines per ad group (RSA optimization)
- ✅ 3-5 descriptions per ad group

### Client Requirements Integration
- ✅ All 8 client requirements included across ad variations
- ✅ Intuitive integration within RSA headlines/descriptions
- ✅ Keyword integration with client requirements
- ✅ Geographic specificity with client positioning

---

## Campaign Type Detection & Routing

### How the System Knows Which Rules to Apply

```python
# Automatic campaign type detection
campaign_type = row.get("Campaign Type", "").strip()

if campaign_type == "Performance Max":
    # Apply PMAX rules from PERFORMANCE_MAX_AD_RULES.md
    validate_asset_groups()
    validate_pmax_assets()

elif campaign_type == "Search":
    # Apply Search rules from SEARCH_CAMPAIGN_AD_RULES.md
    validate_ad_groups()
    validate_search_rsa_assets()

else:
    # Error: Unknown campaign type
    raise ValidationError("Campaign type must be 'Performance Max' or 'Search'")
```

### File Naming Convention (MANDATORY)

#### Performance Max Files
- `Wrights_Performance_Max_2026.csv`
- `Wrights_Lee_County_PMAX_2026.csv`
- `Wrights_Broward_PMAX_2026.csv`

#### Search Campaign Files
- `Wrights_Service_NearMe_Only_2026.csv`
- `Wrights_Broward_Search_2026.csv`
- `Wrights_Lee_County_RSA_2026.csv`

---

## Validation Engine Routing

### CSV Validator Pathways

#### PMAX Validation Path
```python
def validate_pmax_campaign():
    validate_campaign_level()      # PMAX campaign settings
    validate_asset_group_level()   # Asset groups (not ad groups)
    validate_pmax_assets()         # 5 headlines max, 5 descriptions max
    validate_client_requirements() # All 8 requirements included
```

#### Search Validation Path
```python
def validate_search_campaign():
    validate_campaign_level()      # Search campaign settings
    validate_ad_group_level()      # Ad groups (not asset groups)
    validate_search_rsa_assets()   # 15 headlines max, 5 descriptions max
    validate_client_requirements() # All 8 requirements included
```

### Error Prevention
- ❌ **Cannot mix Asset Groups and Ad Groups in same file**
- ❌ **Cannot apply PMAX rules to Search campaigns**
- ❌ **Cannot apply Search rules to PMAX campaigns**
- ✅ **Automatic routing based on Campaign Type column**

---

## Client Requirements Coverage Matrix

### Performance Max Coverage
| Client Requirement | Coverage Method | Validation |
|-------------------|----------------|------------|
| Improve Energy Efficiency | Energy asset group headlines | ✅ Required |
| Noise Reduction | Residential asset groups | ✅ Required |
| Increase Home Security | Security-focused asset groups | ✅ Required |
| Lower Insurance Rates | Insurance asset groups | ✅ Required |
| Improve Property Value | Value-focused asset groups | ✅ Required |
| safeguard your home | Protection asset groups | ✅ Required |
| Impact Windows and Doors in FL | Regional Florida asset groups | ✅ Required |
| PACE Finance Details | Financing asset groups | ✅ Required |

### Search Campaign Coverage
| Client Requirement | Coverage Method | Validation |
|-------------------|----------------|------------|
| Improve Energy Efficiency | Energy-focused ad groups | ✅ Required |
| Noise Reduction | Residential RSA variations | ✅ Required |
| Increase Home Security | Security ad group headlines | ✅ Required |
| Lower Insurance Rates | Insurance ad group descriptions | ✅ Required |
| Improve Property Value | Property value ad groups | ✅ Required |
| safeguard your home | Protection-focused keywords | ✅ Required |
| Impact Windows and Doors in FL | Florida geographic ad groups | ✅ Required |
| PACE Finance Details | Financing ad group descriptions | ✅ Required |

---

## Implementation Checklist

### For Performance Max Campaigns
- [ ] File named with "PMAX" or "Performance_Max"
- [ ] Campaign Type = "Performance Max"
- [ ] Uses Asset Groups (not Ad Groups)
- [ ] 3-5 headlines per asset group (22-29 chars each)
- [ ] 2-5 descriptions per asset group (75-85 chars each)
- [ ] Client requirements distributed across asset groups
- [ ] Follows PERFORMANCE_MAX_AD_RULES.md

### For Search Campaigns
- [ ] File named with "Search" or "RSA"
- [ ] Campaign Type = "Search"
- [ ] Uses Ad Groups (not Asset Groups)
- [ ] Keywords included for each ad group
- [ ] 8-12 headlines per ad group (22-29 chars each)
- [ ] 3-5 descriptions per ad group (75-85 chars each)
- [ ] Client requirements distributed across ad variations
- [ ] Follows SEARCH_CAMPAIGN_AD_RULES.md

---

## Troubleshooting Confusion

### If You See This Error:
```
"Performance Max campaigns require asset groups (not ad groups)"
```
**Solution**: You're trying to use Ad Groups in a PMAX campaign. Switch to Asset Groups.

### If You See This Error:
```
"Search campaigns require ad groups (not asset groups)"
```
**Solution**: You're trying to use Asset Groups in a Search campaign. Switch to Ad Groups.

### If You See This Error:
```
"Campaign type must be 'Performance Max' or 'Search'"
```
**Solution**: The Campaign Type column must contain exactly "Performance Max" or "Search".

---

**File Pathways Summary:**
- **PMAX**: `campaigns/*Performance_Max*.csv` → `PERFORMANCE_MAX_AD_RULES.md`
- **Search**: `campaigns/*Search*.csv` → `SEARCH_CAMPAIGN_AD_RULES.md`

**NO EXCEPTIONS. NO CONFUSION. FOLLOW THE PATHWAYS.**