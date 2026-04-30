# Collab Med Spa Client-Specific Implementation Guide

## Overview

This implementation provides a comprehensive, client-specific Google Ads management platform for Collab Med Spa, a professional medical spa specializing in facial treatments, dermal fillers, laser hair removal, and aesthetic services in the Scottsdale/Phoenix area.

## Client Profile

- **Company**: Collab Med Spa
- **Website**: https://collabmedspa.com/
- **Phone**: To be determined
- **Industry**: Medical Spa Services
- **Services**: Facial Treatments, Dermal Fillers, Laser Hair Removal, Microneedling, Hydrafacials, Dermaplaning, Botox & Injectable Treatments
- **Account Status**: Live and Active
- **Primary Service Area**: Scottsdale, Phoenix, Mesa, Chandler, Tucson (AZ)

## Campaign Strategy

### Primary Focus Areas
1. **Regional Medspas**: General medical spa services and wellness treatments
2. **Facials**: Hydrafacials, microneedling, dermaplaning treatments
3. **Fillers**: Dermal fillers, lip fillers, under eye fillers
4. **Laser**: Laser hair removal services
5. **Brand**: Direct brand searches and brand awareness

### Key Differentiators
- Professional medical spa services
- Licensed and certified practitioners
- Advanced aesthetic treatments
- Local expertise (Scottsdale/Phoenix metro area)
- Trust signals and certifications
- Before/after treatment documentation

## Keyword Management

### Search Term Report Analysis (December 16-22, 2025)

Successfully mapped **182 keywords** from STR analysis to the actual Google Ads campaign structure. All keywords are ready for upload via Google Ads Editor.

## Mapping Results

### ✅ All Keywords Mapped Successfully

- **Total Keywords:** 182
- **Successfully Mapped:** 182 (100%)
- **Unmapped:** 0

### Keywords by Campaign

| Campaign | Keywords | Ad Groups |
|----------|----------|-----------|
| TPPC - Regional - Medspas | 98 | Medspas - Local (37), Medspas - Scottsdale (61) |
| TPPC - Regional - Facials | 53 | Facials - Local (21), Facials - Scottsdale (32) |
| TPPC - Regional - Fillers | 17 | Fillers - Local (12), Fillers - Scottsdale (5) |
| TPPC - General | 12 | Laser Hair Removal - General (12) |
| TPPC - Brand | 1 | Brand - CollabMedSpa (1) |
| TPPC - Regional - Laser | 1 | Laser Hair Removal - Scottsdale (1) |

### Keywords by Ad Group

#### TPPC - Regional - Medspas
- **Medspas - Scottsdale:** 61 keywords
  - Focus: Scottsdale-specific spa searches, hotel spas, wellness spas
  - Examples: "scottsdale spa", "fountain hills med spa", "nordstrom spa scottsdale az"
  
- **Medspas - Local:** 37 keywords
  - Focus: Local "near me" searches, general spa terms
  - Examples: "local pedicures near me" (1 conversion), "medspa near me", "spa near me"

#### TPPC - Regional - Facials
- **Facials - Scottsdale:** 32 keywords
  - Focus: Scottsdale-specific facial searches, aesthetician searches
  - Examples: "facial scottsdale az", "facials scottsdale az" (1 conversion), "hydrafacial scottsdale"
  
- **Facials - Local:** 21 keywords
  - Focus: Dermaplaning, hydrafacials, microneedling variations
  - Examples: "dermaplaning", "hydrafacial near me", "microneedling near me"

#### TPPC - Regional - Fillers
- **Fillers - Local:** 12 keywords
  - Focus: Under eye filler, lip filler, chin filler variations
  - Examples: "filler specials near me" (2 conversions), "under eye filler", "lip filler"
  
- **Fillers - Scottsdale:** 5 keywords
  - Focus: Scottsdale-specific filler searches
  - Examples: "lip filler scottsdale", "the scottsdale injector"

#### TPPC - General
- **Laser Hair Removal - General:** 12 keywords
  - Focus: Laser hair removal variations, electrolysis
  - Examples: "candela laser hair removal", "brazilian laser hair removal", "electrolysis hair removal"

#### TPPC - Brand
- **Brand - CollabMedSpa:** 1 keyword
  - Focus: Brand variations with location
  - Example: "collab medspa scottsdale" (1 conversion)

#### TPPC - Regional - Laser
- **Laser Hair Removal - Scottsdale:** 1 keyword
  - Focus: Laseraway brand searches
  - Example: "laseraway scottsdale"

## Top Converting Keywords

These keywords already have conversions and are prioritized with **Exact match**:

1. **filler specials near me** - 2 conversions ($7.13)
   - Campaign: TPPC - Regional - Fillers
   - Ad Group: Fillers - Local
   - Match Type: Exact

2. **local pedicures near me** - 1 conversion ($8.22)
   - Campaign: TPPC - Regional - Medspas
   - Ad Group: Medspas - Local
   - Match Type: Exact

3. **collab medspa scottsdale** - 1 conversion ($1.66)
   - Campaign: TPPC - Brand
   - Ad Group: Brand - CollabMedSpa
   - Match Type: Exact

4. **facials scottsdale az** - 1 conversion ($4.39)
   - Campaign: TPPC - Regional - Facials
   - Ad Group: Facials - Scottsdale
   - Match Type: Exact

## CSV File Details

**File:** `campaigns/keywords_mapped_to_campaigns.csv`

### Format
- **Encoding:** UTF-8 with BOM (for Excel compatibility)
- **Delimiter:** Comma
- **Format:** Google Ads Editor compatible

### Columns
- Campaign
- Ad Group
- Keyword (plain text)
- Criterion Type (Exact or Phrase)
- Status (Enabled)
- Max CPC (empty - uses ad group default)
- Final URL (empty)
- Final mobile URL (empty)
- Tracking template (empty)
- Custom parameters (empty)

### Match Type Distribution
- **Exact Match:** 4 keywords (all converting keywords)
- **Phrase Match:** 178 keywords (all other search terms)

## Upload Instructions

1. **Open Google Ads Editor**
2. **Import CSV:**
   - File → Import
   - Select "CSV file"
   - Choose `keywords_mapped_to_campaigns.csv`
   - Click "Open"
3. **Review Changes:**
   - Editor will show preview of new keywords
   - Verify keywords are in correct ad groups
   - Check match types are appropriate
4. **Post Changes:**
   - Click "Post" to upload to account
   - Keywords will be added without overriding existing campaigns

## Notes

- ✅ All keywords mapped to correct campaigns and ad groups
- ✅ Campaign and ad group names match exactly with account structure
- ✅ Max CPC left empty to use ad group bid strategy defaults
- ✅ Keywords deduplicated (best performing version kept)
- ✅ Converting keywords prioritized with Exact match
- ✅ CSV format compatible with Google Ads Editor import
- ✅ Ready for upload without overriding existing campaigns

## Files Generated

1. **keywords_to_add.csv** - Initial keywords from STR analysis
2. **keywords_mapped_to_campaigns.csv** - Final mapped keywords ready for upload ⭐
3. **STR_KEYWORD_ANALYSIS.md** - Detailed STR analysis report
4. **KEYWORD_MAPPING_SUMMARY.md** - This file

## Next Steps

1. ✅ STR analysis complete
2. ✅ Campaign structure analyzed
3. ✅ Keywords mapped to correct ad groups
4. ⏳ Review CSV file
5. ⏳ Import into Google Ads Editor
6. ⏳ Monitor performance of new keywords
7. ⏳ Add negative keywords for irrelevant searches as needed
