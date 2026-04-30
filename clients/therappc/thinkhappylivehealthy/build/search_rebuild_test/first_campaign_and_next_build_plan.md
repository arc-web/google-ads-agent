# THHL First Search Campaign Buildout And Next Campaign Plan

Date: 2026-04-28

## Source Reports

- Search terms source: `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/reports/performance_inputs/search_terms_report_2026-04-28.csv`
- Location source: `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/reports/performance_inputs/location_report_2026-04-28.csv`
- Organized search terms: `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/organized_search_terms_2026-04-28.csv`
- Organized locations: `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/organized_locations_2026-04-28.csv`

## What The Reports Say

- The search terms report is small but useful: after removing totals, it contains 39 usable search term rows.
- Child and family terms are being caught by old child psychiatry keywords, but several terms are better mapped by intent layer.
- `child behavioral therapist` and `child behavioral therapist near me` should move out of the old `Children's Psychiatry` ad group, but the ad group names should stay methodical rather than naming one-off search terms.
- ADHD terms split into two intents: child testing or assessment, and therapy or treatment.
- `adhd coach` and `adhd coach near me` spent heavily with weak CPA, so they should not be added to the first keyword build.
- The location report is too coarse for final ZIP-level buildout, but it gives enough to set first-pass campaign targeting and bid modifiers.

## Theme Summary From Converting Terms

- `adhd_treatment`: 6 terms, 68 clicks, 8.50 conversions, CPA $54.78
- `anxiety_treatment`: 4 terms, 13 clicks, 7.00 conversions, CPA $13.40
- `child_psychiatry_psychology`: 3 terms, 11 clicks, 5.00 conversions, CPA $15.55
- `child_adhd_testing`: 3 terms, 6 clicks, 4.00 conversions, CPA $8.63
- `psychiatric_np`: 3 terms, 12 clicks, 4.00 conversions, CPA $22.29
- `child_behavioral_therapy`: 2 terms, 6 clicks, 3.00 conversions, CPA $13.61
- `psychiatry_eval`: 1 terms, 1 clicks, 1.00 conversions, CPA $14.83

## First Campaign

Campaign name: `ARC - Search - Services - V1`

Purpose: rebuild the core service menu into one methodical Search campaign that uses phrase match only. No broad match. We can split ad groups into separate campaigns later after performance data shows which service and geo layers deserve their own budgets.

Campaign settings:

- Campaign type: Search
- Networks: Google Search only
- Search partners: off for initial test unless the client explicitly wants volume
- Match type: phrase only
- Location option: presence only
- Budget: start from current campaign budget, then split only after ad group and geo signal is stable

## Ad Groups And Seed Keywords

Correction: every service category in the first campaign should use the same delimiter pattern, not just the services that showed strongest in the search term report. The first build is intentionally broad inside one campaign so we can stage it in Google Ads Editor, review, and later split winning service lines into separate campaigns.

Campaign name: `ARC - Search - Services - V1`

Ad group naming pattern:

- `Service - Audience/Category - General`
- `Service - Audience/Category - Local`
- `Service - Audience/Category - City`
- `Service - Audience/Category - State`

Intent layer definitions:

- `General`: no explicit geo modifier, for example `child psychiatry`.
- `Local`: `near me` and close-proximity language only, for example `child psychiatry near me`.
- `City`: core city modifiers, starting with Ashburn and Falls Church, then expanding to cities proven by user-location data.
- `State`: state modifiers, starting with Virginia and VA terms. DC and Maryland state-level variants require licensing and client approval before buildout.

Match type rule:

- Generate phrase keywords only.
- Do not generate broad match.
- Each ad group gets only keywords matching its intent layer.

Full taxonomy artifacts:

- CSV: `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/service_ad_group_taxonomy_2026-04-28.csv`
- JSON: `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/service_ad_group_taxonomy_2026-04-28.json`

The current taxonomy contains 24 service categories and 96 planned ad groups.

### Psychiatry

- `Psychiatry - Children - General`
- `Psychiatry - Children - Local`
- `Psychiatry - Children - City`
- `Psychiatry - Children - State`
- `Psychiatry - Adult - General`
- `Psychiatry - Adult - Local`
- `Psychiatry - Adult - City`
- `Psychiatry - Adult - State`

### Therapies

- `Therapy - Anxiety - General`
- `Therapy - Anxiety - Local`
- `Therapy - Anxiety - City`
- `Therapy - Anxiety - State`
- `Therapy - ADHD - General`
- `Therapy - ADHD - Local`
- `Therapy - ADHD - City`
- `Therapy - ADHD - State`
- `Therapy - Autism - General`
- `Therapy - Autism - Local`
- `Therapy - Autism - City`
- `Therapy - Autism - State`
- `Therapy - Depression - General`
- `Therapy - Depression - Local`
- `Therapy - Depression - City`
- `Therapy - Depression - State`
- `Therapy - LGBTQIA+ - General`
- `Therapy - LGBTQIA+ - Local`
- `Therapy - LGBTQIA+ - City`
- `Therapy - LGBTQIA+ - State`
- `Therapy - Stress - General`
- `Therapy - Stress - Local`
- `Therapy - Stress - City`
- `Therapy - Stress - State`
- `Therapy - Grief And Loss - General`
- `Therapy - Grief And Loss - Local`
- `Therapy - Grief And Loss - City`
- `Therapy - Grief And Loss - State`
- `Therapy - Trauma - General`
- `Therapy - Trauma - Local`
- `Therapy - Trauma - City`
- `Therapy - Trauma - State`
- `Therapy - Postpartum Support - General`
- `Therapy - Postpartum Support - Local`
- `Therapy - Postpartum Support - City`
- `Therapy - Postpartum Support - State`
- `Therapy - Children - General`
- `Therapy - Children - Local`
- `Therapy - Children - City`
- `Therapy - Children - State`

### Specialty Therapy Modalities

- `Therapy - EMDR - General`
- `Therapy - EMDR - Local`
- `Therapy - EMDR - City`
- `Therapy - EMDR - State`
- `Therapy - CBT - General`
- `Therapy - CBT - Local`
- `Therapy - CBT - City`
- `Therapy - CBT - State`
- `Therapy - DBT - General`
- `Therapy - DBT - Local`
- `Therapy - DBT - City`
- `Therapy - DBT - State`
- `Therapy - Somatic - General`
- `Therapy - Somatic - Local`
- `Therapy - Somatic - City`
- `Therapy - Somatic - State`
- `Therapy - Mindfulness - General`
- `Therapy - Mindfulness - Local`
- `Therapy - Mindfulness - City`
- `Therapy - Mindfulness - State`

### Testing

- `Testing - Child Psychological - General`
- `Testing - Child Psychological - Local`
- `Testing - Child Psychological - City`
- `Testing - Child Psychological - State`
- `Testing - Psychoeducational - General`
- `Testing - Psychoeducational - Local`
- `Testing - Psychoeducational - City`
- `Testing - Psychoeducational - State`
- `Testing - Gifted - General`
- `Testing - Gifted - Local`
- `Testing - Gifted - City`
- `Testing - Gifted - State`
- `Testing - ADHD - General`
- `Testing - ADHD - Local`
- `Testing - ADHD - City`
- `Testing - ADHD - State`
- `Testing - Kindergarten Readiness - General`
- `Testing - Kindergarten Readiness - Local`
- `Testing - Kindergarten Readiness - City`
- `Testing - Kindergarten Readiness - State`
- `Testing - Autism - General`
- `Testing - Autism - Local`
- `Testing - Autism - City`
- `Testing - Autism - State`
- `Parent Child Services - Children - General`
- `Parent Child Services - Children - Local`
- `Parent Child Services - Children - City`
- `Parent Child Services - Children - State`

### Search-Term Evidence To Preserve

These terms came from the search terms report and should be mapped into the taxonomy above rather than becoming one-off ad group names:

- `child behavioral therapist` goes into `Therapy - Children - General`.
- `child behavioral therapist near me` goes into `Therapy - Children - Local`.
- `child and adolescent psychiatry` and `child psychiatry` go into `Psychiatry - Children - General`.
- `child psychiatry near me` goes into `Psychiatry - Children - Local`.
- `adhd kids assessment near me`, `children adhd testing near me`, and `adhd assessment for kids near me` go into `Testing - ADHD - Local` when the landing page is testing, or `Therapy - ADHD - Local` when the landing page is therapy.
- `adhd therapist` goes into `Therapy - ADHD - General`.
- `adhd therapist near me` goes into `Therapy - ADHD - Local`.
- `anxiety doctors near me` goes into `Therapy - Anxiety - Local` or a psychiatry medication-management ad group after human review.
- `pmhnps near me`, `psych np near me`, and `psychiatric nurse practitioner` go into `Psychiatry - Adult - Local` or `Psychiatry - Adult - General`.

### First Build Control Rule

The taxonomy should be complete, but the initial CSV can mark low-evidence ad groups as paused if needed. That lets Google Ads Editor act as staging while keeping the build system consistent. We should not drop ad groups from the taxonomy just because this small search term report does not yet have evidence for every service.

## First Campaign Geo Targeting

Use the current report for first-pass geo targeting, but request a ZIP or city-level user location report before deeper segmentation.

Operating states supported by current data:

- Virginia: strongest state-level signal in this report, 39 conversions, CPA $333.29.
- Washington, District of Columbia: 5 conversions, CPA $375.88.
- Maryland: 15 conversions, but CPA is weak at $717.59, so keep under review instead of broad first-build expansion.

Core counties supported by current data:

- Fairfax County, Virginia: 16 conversions, CPA $271.46.
- Loudoun County, Virginia: 13 conversions, CPA $137.48.
- Prince William County, Virginia: 4 conversions, CPA $300.80.

Core cities supported by current report:

- Arlington, Virginia appears directly, but has weak CPA in this report: 1 conversion at $1062.20 CPA.
- Manassas, Virginia appears directly, with 0 conversions and $203.04 spend, so reduce or review.

Core city candidates from the existing account export and service area:

- Ashburn, Virginia
- Falls Church, Virginia
- Leesburg, Virginia
- Sterling, Virginia
- Dulles, Virginia
- Reston, Virginia
- Arlington, Virginia
- Manassas, Virginia

The report helps, but it is not enough for final city and ZIP buildout because most winning signal is at state, county, or `Total: Other locations` level. The next geo report should be user location by city and ZIP.

Tier 1, bid up:

- `Fairfax County, Virginia, United States`: 16.0 conversions, CPA $271.46, modifier `20`
- `Loudoun County, Virginia, United States`: 13.0 conversions, CPA $137.48, modifier `20`

Tier 2, moderate bid up:

- `Virginia, United States`: 39.0 conversions, CPA $333.29, modifier `10`
- `Washington, District of Columbia, United States`: 5.0 conversions, CPA $375.88, modifier `10`
- `Prince William County, Virginia, United States`: 4.0 conversions, CPA $300.8, modifier `10`

Reduce or review:

- `Manassas, Virginia, United States`: 0.0 conversions, CPA $0.0, modifier `-25`

Specific geo recommendation:

- Keep Loudoun County and Fairfax County as core targets.
- Keep Prince William County and Washington DC as expansion targets.
- Avoid broad Maryland in the first clean rebuild because this report shows high cost and weak CPA.
- Do not overreact to `Total: Other locations` yet, because it is an aggregate bucket. Pull a finer user-location report so the winning cities or ZIPs can be targeted directly.

## Terms To Exclude Or Review

- Add `coach` as a negative concept for this first campaign unless the client sells coaching.
- Review competitor, provider-name, and institution terms before adding or excluding them.
- Review out-of-market city terms like Danville, Towson, and Fredericksburg before deciding if they should be excluded.
- Keep brand and phone searches out of this nonbrand campaign. Build a separate brand campaign if needed.

High-priority review terms:

- `uva child psychology`: action `human_review_negative_or_competitor`, 2.0 conversions, CPA $3.87
- `7032897560`: action `separate_brand_or_call_only`, 2.0 conversions, CPA $7.31
- `epic danville va`: action `human_review_negative`, 2.0 conversions, CPA $8.32
- `belgrade counseling clinic`: action `human_review_negative_or_competitor`, 2.0 conversions, CPA $8.39
- `esketamine`: action `separate_later`, 2.0 conversions, CPA $15.7
- `aislynn collier`: action `human_review_negative_or_competitor`, 2.0 conversions, CPA $62.91
- `blackbird health vienna`: action `human_review_negative_or_competitor`, 1.0 conversions, CPA $5.77
- `think happy live healthy ashburn`: action `separate_brand_or_call_only`, 1.0 conversions, CPA $14.21
- `psychological evaluation for child`: action `human_review`, 1.0 conversions, CPA $16.44
- `uva child and family psychiatry`: action `human_review_negative_or_competitor`, 1.0 conversions, CPA $22.1
- `child psychologist fredericksburg va`: action `human_review_negative`, 1.0 conversions, CPA $24.4
- `physiatrists near me`: action `human_review`, 1.0 conversions, CPA $36.83
- `champs dc mental health`: action `human_review_negative_or_competitor`, 1.0 conversions, CPA $41.68
- `child and adult psychiatry towson`: action `human_review_negative`, 1.0 conversions, CPA $45.37
- `ari yares`: action `human_review_negative_or_competitor`, 1.0 conversions, CPA $51.96
- `adhd coach near me`: action `negative_or_separate_low_priority`, 1.0 conversions, CPA $224.33

## Responsive Search Ad Direction

The RSA builder should use old high-CTR converting themes, but improve relevance by ad group:

- Put child behavioral therapy language only in `Therapy - Children - General` and `Therapy - Children - Local`.
- Put ADHD assessment and testing language in `Testing - ADHD - Local` and `Testing - ADHD - General`.
- Keep adult ADHD therapist and treatment language in adult ADHD ad groups.
- Keep `Psychiatric Nurse Practitioner`, `PMHNP`, and `Psych NP` together in adult psychiatry ad groups.
- Keep anxiety ad copy direct, but avoid implying the user has a personal medical condition.

Every RSA must pass headline and description character limits, landing page match, clinical specificity, and sensitive-category policy review before CSV assembly.

## Next Campaigns

Campaign 2: `ARC - Search - Child Testing - V1`

- Build around child psychological testing, psychoeducational evaluations, autism testing, gifted testing, and kindergarten readiness.
- Use only phrase keywords.
- Use landing pages specific to each testing service.

Campaign 3: `ARC - Search - Adult Therapy + Psychiatry - V1`

- Build around adult therapy, adult psych evaluations, anxiety treatment, depression treatment, and medication management.
- Separate therapy from medication management when enough volume exists.

Campaign 4: `ARC - Search - Brand - V1`

- Capture `think happy live healthy`, phone number searches, provider name searches if approved, and office-location brand variants.
- Keep budget controlled and do not let brand conversion CPA distort nonbrand planning.

Campaign 5: geo split campaigns after we get better location detail

- `ARC - Search - Loudoun/Ashburn - V1`
- `ARC - Search - Fairfax/Falls Church - V1`
- `ARC - Search - DC/Arlington - V1` only if CPA improves or strategic need is confirmed.
- Maryland should be split only after city or ZIP winners are identified.

## Data Needed Before Deeper Segmentation

- User location report by city and ZIP code.
- Search term report segmented by campaign, ad group, conversion action, and network.
- RSA asset report with impressions, CTR, conversion rate, and conversions by headline and description.
- Landing page performance by final URL.
- Client priority services and capacity constraints.

## Google Ads Limit Note

Google's account limit docs list 10,500 location targets per campaign and up to 500 proximity targets per campaign. That is not the blocker here yet. The practical blocker is clean reporting and campaign control, so we should split campaigns by service line and high-value geography before we hit hard platform limits.

Source: https://support.google.com/google-ads/answer/6372658?hl=en

## Build Sequence

1. Add the first campaign structure above to the rebuild harness.
2. Generate phrase keyword rows only.
3. Generate one RSA per ad group, then a second variant only after review.
4. Add Tier 1 and Tier 2 locations with bid modifiers.
5. Add negatives for coaching, brand leakage, and clear out-of-market terms after human review.
6. Import into Google Ads Editor as staging.
7. Fix Editor validation issues, then repeat for Campaign 2.
