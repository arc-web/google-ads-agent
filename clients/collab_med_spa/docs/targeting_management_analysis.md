# CollabMedSpa Targeting Management Analysis

Source memo: [geo_targeting_strategy_collabmedspa.txt](/Users/home/ai/agents/ppc/google_ads_agent/clients/collab_med_spa/docs/geo_targeting_strategy_collabmedspa.txt)

Client config source: [collab_med_spa_client_config.yaml](/Users/home/ai/agents/ppc/google_ads_agent/collab_med_spa/collab_med_spa_client_config.yaml)

Current account export source: [CollabMedSpa.com import](/Users/home/ai/agents/ppc/google_ads_agent/collab_med_spa/campaigns/imports/CollabMedSpa.com++6_Campaigns+12_Ad groups+2025-12-23.csv)

Official platform sources:
- [Google Ads location targeting](https://support.google.com/google-ads/answer/2453995?hl=en)
- [Google Ads demographic targeting](https://support.google.com/google-ads/answer/2580383?hl=en)
- [Google Ads Editor location CSV import](https://support.google.com/google-ads/editor/answer/30573?hl=en)
- [Google Ads Editor CSV columns](https://support.google.com/google-ads/editor/answer/57747?hl=en)
- [Google Ads personalized advertising policy](https://support.google.com/adspolicy/answer/143465?hl=en)

## What The Memo Adds

The memo gives us a Scottsdale ZIP inventory and a demographic thesis:

- Primary ZIPs: 85250, 85251, 85253, 85254, 85255, 85257, 85258, 85259, 85260, 85262, 85266, 85268.
- P.O. Box ZIPs to avoid as positive geo targets unless account data proves value: 85252, 85261, 85267, 85269, 85271.
- Demographic thesis: Scottsdale is affluent, older than average, wellness-oriented, and suitable for premium med spa positioning.
- Messaging implication: emphasize premium aesthetic care, medical credibility, convenience, trust, and culturally inclusive language.

## Current Targeting Pattern In The Export

The existing Google Ads Editor export already uses a layered location structure:

- Campaigns: 6 Search campaigns.
- Location targeting rows: 117 rows, 26 unique location strings.
- Location setting: `Location of presence` for both targeting and exclusion method, which is the right default for local med spa intent.
- ZIP/city/neighborhood examples already present:
  - `85258, Arizona, United States`
  - `85259, Arizona, United States`
  - `85254, Arizona, United States`
  - `Central Scottsdale, Arizona, United States`
  - `McCormick Ranch, Arizona, United States`
  - `Paradise Valley, Arizona, United States`
- Radius examples:
  - `(3mi:33.530300:-111.836502)`
  - `(10mi:33.530300:-111.836502)`
- Demographic rows exist for age and gender:
  - Age: 18-24, 25-34, 35-44, 45-54, 55-64, 65-up, Unknown.
  - Gender: Female, Male, Unknown.
- Household income rows are not present in the current export.

## Recommended Location Layering Model

Use location as the primary targeting control because it is explicit, importable, and appropriate for a local service business.

### Tier 1: Core Revenue ZIPs

Use dedicated positive location rows for the highest-value Scottsdale ZIPs:

- 85251: Old Town Scottsdale
- 85254: North Scottsdale
- 85255: North Scottsdale
- 85258: McCormick Ranch
- 85259: East Scottsdale
- 85260: North Scottsdale
- 85266: North Scottsdale

These should receive the most careful budget monitoring and can support higher bid adjustments when conversion data confirms value.

### Tier 2: Adjacent Affluent ZIPs And Cities

Use as secondary targets with lower initial bids or shared campaign budgets:

- 85250: Central Scottsdale
- 85253: Paradise Valley
- 85257: South Scottsdale
- 85262: North Scottsdale
- 85268: Fountain Hills
- Paradise Valley, Arizona
- Carefree, Arizona
- Desert Ridge, Arizona

### Tier 3: Broad Metro Expansion

Keep broader Phoenix metro locations separated from Scottsdale intent campaigns:

- Phoenix
- Mesa
- Chandler
- Glendale
- Goodyear
- Peoria

These should not be mixed into the same ad groups as high-intent Scottsdale terms unless the campaign goal is explicitly expansion.

### Exclusions And Avoid List

Avoid adding P.O. Box ZIPs as positive targets by default:

- 85252
- 85261
- 85267
- 85269
- 85271

If they appear in exports or account performance data, treat them as review-required rather than auto-include.

## Demographic Strategy

Use demographics as a reporting and optimization layer, not as the primary targeting layer.

Recommended starting posture:

- Keep all age groups enabled, including Unknown.
- Keep all gender groups enabled, including Unknown.
- Add household income reporting rows if available for the campaign type and market, but start in observation or low-risk bid-adjustment mode.
- Do not use race, ethnicity, or inferred cultural background as targeting criteria. Use that information only for inclusive creative review.

The likely high-value segments for CollabMedSpa are:

- 35-44
- 45-54
- 55-64
- Female
- Higher household income ZIPs

Do not hard-exclude men, 25-34, 65-up, or Unknown until account data proves waste. Med spa services can convert outside the assumed persona.

## Policy Guardrails

CollabMedSpa promotes aesthetic and medical spa services, including Botox, fillers, laser hair removal, and injectable treatments. Google personalized ads policy treats health-related content, invasive medical procedures, cosmetic surgery, surgical procedures, and injections as sensitive categories.

Operational rules:

- Prefer Search intent plus location targeting over remarketing and custom audience tactics.
- Do not use customer match, remarketing lists, lookalike segments, or advertiser-curated sensitive audiences for treatment-specific campaigns.
- Predefined Google audiences, demographics, detailed demographics, and location targeting may be available, but should still be reviewed for policy risk before launch.
- Avoid ad copy that implies personal attributes, insecurities, or sensitive conditions.
- Keep creative broad and benefit-led, for example `Scottsdale Med Spa Services` rather than copy that implies the user has a specific body concern.

## CSV Requirements For Automation

Location targets should be generated as separate rows. Google Ads Editor expects each location on its own row with a `Location` column, and optional `Location ID` when available.

Required internal schema for targeting agents:

```json
{
  "campaign": "TPPC - Regional - Medspas",
  "ad_group": "",
  "targeting_type": "location",
  "location": "85258, Arizona, United States",
  "location_id": "",
  "layer": "tier_1_core_zip",
  "bid_modifier": 20,
  "status": "Enabled",
  "reason": "Core Scottsdale affluent ZIP from source memo and current export"
}
```

Demographic rows should be generated separately:

```json
{
  "campaign": "TPPC - Regional - Medspas",
  "ad_group": "Medspas - Scottsdale",
  "targeting_type": "age",
  "value": "45-54",
  "bid_modifier": 0,
  "status": "Enabled",
  "mode": "observe_first",
  "reason": "Likely high-value segment, but do not restrict without performance data"
}
```

## Automation Implications

Targeting should be built by a dedicated targeting agent with these gates:

1. Parse client memo and existing account export.
2. Classify target geos into Tier 1, Tier 2, Tier 3, and Avoid.
3. Compare against current account targets.
4. Propose additions, removals, and bid modifiers.
5. Flag policy risks for demographic or audience targeting.
6. Produce human-reviewable targeting changes.
7. Export only approved rows to the Google Ads Editor CSV consolidator.

The targeting agent should not directly post changes. Google Ads Editor remains the staging layer.

