# ThinkHappyLiveHealthy Search Campaign Rebuild Test Plan

Date: 2026-04-28

Client: ThinkHappyLiveHealthy

Website: https://www.thinkhappylivehealthy.com/

## Goal

Test the automation path by rebuilding one Search campaign into a Google Ads Editor-ready CSV. The CSV should be treated like a staging build: import into Google Ads Editor, inspect structure, resolve errors, then decide what is ready to upload.

This test should not rebuild the whole account. It should rebuild one campaign with campaign structure, ad groups, keywords, responsive search ads, geo targets, demographics, and bid adjustment rows.

## Source Inputs

- Manual campaign draft: `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/campaigns/THHL_Search_Campaign_2026-04-28.csv`
- Existing account export: `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/campaigns/ThinkHappyLiveHealthy_export_2026-04-27.csv`
- Copy review report: `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/reports/thinkhappylivehealthy_copy_review_2026-04-27.html`
- Google Ads Editor CSV import reference: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor location CSV import reference: https://support.google.com/google-ads/editor/answer/30573?hl=en
- Google Ads Editor CSV column reference: https://support.google.com/google-ads/editor/answer/57747?hl=en
- Google Ads location targeting reference: https://support.google.com/google-ads/answer/2453995?hl=en
- Google Ads demographic targeting reference: https://support.google.com/google-ads/answer/2580383?hl=en
- Google Ads personalized advertising policy reference: https://support.google.com/adspolicy/answer/143465?hl=en

## Current State

The manual THHL campaign draft contains:

- 1 Search campaign: `THHL - Search - RevKey`
- 9 ad groups
- 130 keyword rows
- 104 unique keywords
- 9 responsive search ad rows
- No location rows
- No radius rows
- No age rows
- No gender rows
- No household income rows
- No bid modifier rows

The existing THHL export contains:

- Location rows: 67
- Unique location targets: 29
- Age rows: 149
- Gender rows: 59
- Household income rows: 140
- Bid modifier rows: 30
- Targeting method: `Location of presence`
- Exclusion method: `Location of presence`

The rebuild should preserve the useful manual campaign work, then add targeting as importable account data.

## Test Campaign Scope

Rebuild only:

- Campaign: `THHL - Search - RevKey`
- Ad groups:
  - `Psychiatry`
  - `ADHD Testing`
  - `Adult Therapy`
  - `Autism Testing`
  - `Child Psychological Testing`
  - `Gifted Testing`
  - `Kindergarten Readiness Testing`
  - `Parent Child Services`
  - `Psychoeducational Evaluations`

Do not build Performance Max, display, remarketing, or additional Search campaigns in this first test.

## Targeting Integration Plan

Targeting should be written into the CSV as campaign-level rows where Google Ads Editor supports them. The strategy layer should produce a structured targeting spec, and the CSV builder should render that spec into Editor rows.

### Geo Layers

Tier 1, core local service areas:

- Falls Church, Virginia
- Ashburn, Virginia
- Loudoun County, Virginia
- Fairfax County, Virginia

Initial bid adjustment: `+20%`

Tier 2, nearby high-intent expansion:

- Leesburg, Virginia
- Sterling, Virginia
- Dulles, Virginia
- Reston, Virginia
- Vienna, Virginia
- Herndon, Virginia
- McLean, Virginia
- Arlington, Virginia
- Arlington County, Virginia
- Prince William County, Virginia

Initial bid adjustment: `+10%`

Tier 3, broader regional coverage:

- Virginia
- Maryland
- Washington, District of Columbia

Initial bid adjustment: `0%`

Radius layer:

- Reuse the existing export radius target `(15mi:38.964776:-77.521702)` as a first automation test row.
- Do not invent new coordinate targets until the automation can map and validate office or service-area coordinates.

Initial bid adjustment: `+10%`

### Demographic Layers

Demographics should be included as observation and bid adjustment rows, not hard exclusions.

Age:

- Keep all age groups eligible, including `Unknown`.
- Start priority age groups at `+10%` only where account data or client feedback supports it.
- Start non-priority age groups at `0%`.
- Do not exclude age groups in this first rebuild.

Gender:

- Keep `Female`, `Male`, and `Unknown` eligible.
- Start at `0%` unless account data supports a modifier.
- Do not exclude gender groups in this first rebuild.

Household income:

- Keep all household income groups eligible, including `Unknown`.
- Start at `0%` for this test unless the current account data clearly supports a modifier.
- Do not exclude household income groups in this first rebuild.

Healthcare and mental health advertising can touch sensitive categories. The automation should avoid copy or targeting logic that implies knowledge of a person’s health, mental health, disability, or other sensitive condition. Demographics may be used as campaign controls where allowed, but the quality gate should flag any hard exclusion or personalized phrasing that creates policy risk.

## Automation Flow

1. Ingest source files.
   - Parse the manual campaign draft.
   - Parse the current account export.
   - Normalize encodings, headers, campaign names, ad group names, and row types.

2. Build client context.
   - Pull website and report-card findings into `client_context.json`.
   - Record services, locations, offer constraints, brand voice, and policy notes.

3. Build targeting spec.
   - Create `targeting_spec.json`.
   - Include geo layers, demographic rows, radius rows, targeting method, exclusion method, and proposed bid modifiers.
   - Mark every bid adjustment as `initial`, `data_backed`, or `needs_human_review`.

4. Run copy quality gates.
   - Check headlines and descriptions for character limits.
   - Check clarity, specificity, service match, location relevance, landing page match, and policy risk.
   - Score or reject assets before CSV assembly.

5. Assemble Editor CSV.
   - Preserve the manual campaign's campaign, ad group, keyword, and RSA structure.
   - Add location rows.
   - Add radius rows.
   - Add demographic rows.
   - Add bid modifier values where supported.
   - Preserve `Location of presence` for targeting and exclusion method.

6. Validate output.
   - Validate required columns.
   - Validate row types.
   - Validate character limits.
   - Validate duplicate keywords and duplicate ads.
   - Validate that no sensitive demographic exclusions were introduced.
   - Validate that the CSV can be imported into Google Ads Editor.

7. Human review.
   - Generate a review HTML or Markdown file.
   - Highlight changed copy, geo targets, bid modifiers, demographic assumptions, and validation warnings.
   - Require approval before broader account buildout.

## Proposed Output Files

- `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/client_context.json`
- `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/targeting_spec.json`
- `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/THHL_Search_Rebuild_Test_2026-04-28.csv`
- `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/validation_report.json`
- `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/human_review.md`

## Agent Roles For The Later Multi-Agent Build

Context agent:

- Reads website, report card, account export, and client notes.
- Produces `client_context.json`.

Targeting agent:

- Produces `targeting_spec.json`.
- Converts regional strategy into explicit location, ZIP, city, radius, demographic, and bid adjustment rows.

Copy gate agent:

- Reviews headlines and descriptions.
- Applies character limits, policy checks, service fit, local relevance, and plain-English scoring.

Campaign assembler agent:

- Converts approved strategy, copy, keywords, and targeting into a Google Ads Editor CSV.

Validator agent:

- Checks schema, duplicate risk, character limits, missing targeting, unsupported bid modifiers, and policy warnings.

Human review coordinator:

- Summarizes choices and flags assumptions.
- Collects approval or edits before upload.

## Pass Criteria

The test passes when:

- The output CSV imports into Google Ads Editor without column or encoding errors.
- The CSV contains exactly one campaign.
- The CSV contains the 9 expected ad groups.
- The CSV contains the expected keyword and RSA rows from the manual draft.
- The CSV includes location or radius targeting rows.
- The CSV includes demographic rows or a documented reason for omitting them.
- Bid modifiers are present where supported and intentionally blank where unsupported.
- No demographic group is excluded.
- No ad copy implies knowledge of a sensitive personal condition.
- A human review file explains all bid adjustment assumptions.

## Recommended Next Step

Build the first implementation as a small script, not a full agent swarm:

- Input: manual campaign CSV, current export CSV, and a static targeting spec.
- Output: one Editor CSV plus validation report.
- After the CSV imports cleanly into Google Ads Editor, split the work into the agent roles above.

