# One-Shot Google Ads Account Rebuild Automation Plan

Date: 2026-04-28

Client test case: ThinkHappyLiveHealthy

## Goal

Given a Google Ads Editor export CSV and a client website, run one repeatable automation that audits the account, scans the site, builds strategy, generates a new campaign structure, creates phrase-match keyword sets, writes RSAs, adds geo and demographic targeting, validates everything, and outputs a Google Ads Editor CSV for staging.

Google Ads Editor remains the staging environment. The automation should not post directly to Google Ads until the CSV is reviewed.

## Required Inputs

Minimum:

- Google Ads Editor account export CSV.
- Website URL.
- Client name.
- Target market or service area if known.

Recommended:

- Search terms report.
- Location report.
- RSA asset report.
- Landing page performance report.
- Conversion action report.
- Client notes about priority services, exclusions, offers, insurance, licensing, and capacity.

## Final Outputs

The automation should produce a folder like:

`clients/{agency}/{client}/build/{date}_account_rebuild/`

With:

- `account_audit.json`
- `website_scan.json`
- `service_catalog.json`
- `geo_strategy.json`
- `search_term_analysis.csv`
- `keyword_expansion_candidates.csv`
- `campaign_taxonomy.csv`
- `rsa_copy_matrix.csv`
- `targeting_spec.json`
- `human_review.md`
- `validation_report.json`
- `Google_Ads_Editor_Staging_CURRENT.csv`

## Pipeline

### 1. Ingest Account Export

Read the Google Ads Editor export.

Extract:

- Campaigns.
- Campaign settings.
- Ad groups.
- Keywords and match types.
- RSAs and assets.
- Final URLs.
- Locations.
- Radius targets.
- Demographics.
- Bid modifiers.
- Negatives.
- Budgets.
- Status fields.
- EU political ads field.

Normalize:

- Encoding.
- Header names.
- Row types.
- Campaign and ad group names.
- Keyword match type format.
- Location ID format where possible.

Output:

- `account_snapshot.json`
- `account_summary.md`

### 2. Ingest Performance Reports

Read search terms, location report, asset report, and landing page report.

Search terms:

- Classify service intent.
- Classify intent layer: General, Local, City, State.
- Mark converting terms for phrase keyword expansion.
- Mark high-impression non-converters for review.
- Mark competitor, provider name, coaching, out-of-market, and irrelevant terms for negative review.

Location report:

- Rank states, counties, cities, ZIPs, and radius performance.
- Identify core geos.
- Identify expansion geos.
- Identify reduce or exclude candidates.
- Add Google geo target IDs where available.

Asset report:

- Identify strongest old headlines and descriptions.
- Extract reusable language patterns.
- Reject weak or policy-risk language.

Output:

- `search_term_analysis.csv`
- `location_analysis.csv`
- `asset_performance_analysis.csv`

### 3. Scan Website

Crawl the client website.

Extract:

- Service pages.
- Page titles and H1s.
- Service categories.
- Locations.
- Appointment pages.
- Insurance and access claims.
- Staff credentials if visible.
- Compliance-sensitive claims.
- Landing page URLs for each service.

For THHL, this became:

- Psychiatry.
- Therapy categories.
- Specialty therapy modalities.
- Testing categories.
- Parent child services.
- Ashburn and Falls Church.

Output:

- `website_scan.json`
- `service_catalog.json`
- `landing_page_map.json`

### 4. Build Strategy

Generate campaign strategy from account data plus site data.

Decide:

- Which campaigns to rebuild first.
- Which services belong in the first campaign.
- Which ad groups should exist.
- Which geos are core versus expansion.
- Which audiences or demographics should be observed.
- Which terms should be reviewed as negatives.
- Which landing pages need review.

For this THHL test, the first campaign became:

`THHL - Search - Services - RevKey`

With ad group pattern:

- `Service - Audience/Category - General`
- `Service - Audience/Category - Local`
- `Service - Audience/Category - City`
- `Service - Audience/Category - State`

Output:

- `strategy.md`
- `campaign_taxonomy.csv`
- `human_review.md`

### 5. Build Keyword System

Generate phrase-match keywords only.

Do not use broad match.

Keyword sources:

- Core template root terms from service taxonomy.
- Singular and plural variants.
- Child, children, youth variants where relevant.
- High-performing search terms.
- Geo modifiers.
- City list.
- State list.

Intent-layer rules:

- General: no geo modifier.
- Local: `near me`, `near you`, or close-proximity variants.
- City: every target city, not only one.
- State: Virginia, VA, Northern Virginia, and approved state terms.

Keyword gates:

- Must map directly to a service.
- Must map to a relevant landing page.
- Must be phrase match.
- Must be title-cased for Editor readability.
- Must not be competitor, provider-name, coaching, or out-of-market unless human approved.
- Must not duplicate another keyword in the same ad group.

Output:

- `keyword_matrix.csv`
- `negative_review_candidates.csv`

### 6. Build RSA Copy System

Generate one RSA per ad group.

Each RSA:

- 15 headlines.
- 4 descriptions.
- Path 1.
- Path 2.
- Final URL.

Headline system:

- Build a pool of 25 to 40 candidate headlines per ad group.
- Score each headline.
- Keep the top 15.

Headline scoring should reward:

- Search term relevance.
- Service specificity.
- Intent layer match.
- City or state match.
- Client value prop.
- Appointment CTA.
- Licensed clinician or evaluator language.
- Telehealth and in-person access.
- Use of 20 to 30 characters where possible.

Headline gates:

- Max 30 characters.
- No one-word headlines.
- No bare labels like `Psychiatry` or `Therapy`.
- No broken truncation.
- No duplicate ideas.
- No unsupported claims.
- No sensitive-condition personalization.

Description system:

- Description 1: service fit.
- Description 2: process or value prop.
- Description 3: location/access.
- Description 4: CTA.

Description gates:

- Max 90 characters.
- Mention service or service category.
- Mention access, process, or value prop.
- No unsupported claims.
- No policy-risk language.

Output:

- `rsa_copy_matrix.csv`
- `rsa_copy_review.md`

### 7. Build Targeting

Generate targeting rows for Google Ads Editor.

Targets:

- Location rows.
- Location IDs where available.
- Radius rows where used.
- Bid modifiers.
- Demographic rows only when appropriate.

For healthcare and mental health:

- Keep demographics observational unless data and policy review support modifiers.
- Do not exclude sensitive groups in the first rebuild.
- Do not write copy that implies knowledge of a user’s condition or identity.

Output:

- `targeting_spec.json`
- `geo_targeting_review.md`

### 8. Assemble Editor CSV

Use the existing account export header as the base schema when possible.

Write:

- Campaign rows.
- Ad group rows.
- Keyword rows.
- RSA rows.
- Location rows.
- Radius rows.
- Optional demographic rows.
- Negative keyword rows after review.

Important fields:

- `Campaign Type`: `Search`
- `Networks`: `Google search`
- `EU political ads`: `Doesn't have EU political ads`
- `Broad match keywords`: `Off`
- `Targeting method`: `Location of presence`
- `Exclusion method`: `Location of presence`
- `Criterion Type`: `Phrase`
- `Keyword`: plain keyword text, not quotes or brackets
- `Location ID`: where available

Output:

- `Google_Ads_Editor_Staging_CURRENT.csv`

### 9. Validate

Run local validation before Editor import.

Hard validations:

- CSV encoding.
- Required headers.
- Campaign row present.
- EU political ads field populated.
- No broad match.
- Phrase keywords only.
- No missing final URLs.
- 15 RSA headlines.
- 4 RSA descriptions.
- Headline max 30 characters.
- Description max 90 characters.
- Path fields max 15 characters.
- No one-word headlines.
- No broken truncated headlines.
- No duplicate keywords in the same ad group.
- Location IDs where available.

Soft validations:

- Landing page fallback warnings.
- Low-evidence ad groups.
- High-risk terms for review.
- Demographic targeting review.
- Geo expansion review.

Output:

- `validation_report.json`
- `human_review.md`

### 10. Human Review

The automation should stop before upload.

Human reviews:

- Campaign names.
- Budgets.
- Geo bid modifiers.
- Search terms added.
- Negative candidates.
- Landing page fallbacks.
- RSAs by ad group.
- Any sensitive-category policy warnings.

The user imports the CSV into Google Ads Editor, checks warnings, makes changes, then decides whether to post.

## Agent Architecture

One-shot orchestrator:

- Coordinates all stages.
- Writes folder structure.
- Tracks source files.
- Produces final run report.

Account audit agent:

- Parses account export.
- Summarizes current state.

Website scan agent:

- Crawls site.
- Builds service and landing page catalog.

Strategy agent:

- Builds campaign plan, ad group taxonomy, targeting direction.

Keyword agent:

- Builds phrase-match keyword matrix.
- Uses search terms and inferred variants.

Copy agent:

- Generates and scores RSA assets.
- Uses account history and website language.

Targeting agent:

- Builds geo, radius, location ID, demographic, and bid modifier specs.

Validator agent:

- Runs schema, policy, and quality gates.

Review agent:

- Produces `human_review.md`.

## Minimal CLI

The practical command should look like:

```bash
python -m shared.rebuild.one_shot \
  --client thinkhappylivehealthy \
  --agency therappc \
  --website https://www.thinkhappylivehealthy.com/ \
  --account-export clients/therappc/thinkhappylivehealthy/campaigns/ThinkHappyLiveHealthy_export_2026-04-27.csv \
  --search-terms clients/therappc/thinkhappylivehealthy/reports/performance_inputs/search_terms_report_min_10_impressions_2026-04-28.csv \
  --location-report clients/therappc/thinkhappylivehealthy/reports/performance_inputs/location_report_2026-04-28.csv
```

Expected result:

```text
build/2026-04-28_account_rebuild/Google_Ads_Editor_Staging_CURRENT.csv
build/2026-04-28_account_rebuild/human_review.md
build/2026-04-28_account_rebuild/validation_report.json
```

## What We Learned From THHL

- Editor wants `Criterion Type: Phrase`, with plain keyword text.
- Editor needs `EU political ads` populated before location changes can post.
- Location names resolve better when `Location ID` is present.
- `General` ad groups still need strong ad copy.
- One-word headlines are unacceptable.
- City ad groups need all target city modifiers, not one city.
- Templates are necessary, but search term reports provide variation.
- High-impression terms should not automatically become keywords.
- Converting terms can graduate into phrase keywords after relevance review.

## Implementation Order

1. Move the THHL generator logic into shared modules.
2. Create reusable parsers for Google Ads Editor CSV and Google reports.
3. Create a generic service taxonomy builder from website scan and report evidence.
4. Create the keyword expansion engine.
5. Create the RSA copy pool and scoring engine.
6. Create targeting spec builder with geo target ID lookup.
7. Create Editor CSV assembler.
8. Create validator.
9. Create human review writer.
10. Wrap with one CLI command.

## References

- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor location import: https://support.google.com/google-ads/editor/answer/30573?hl=en
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en
- Google responsive search ads: https://support.google.com/google-ads/answer/7684791?hl=en-EN
- Google geo targets: https://developers.google.com/google-ads/api/data/geotargets
- Google Ads EU political advertising status: https://developers.google.com/google-ads/api/reference/rpc/v21/EuPoliticalAdvertisingStatusEnum.EuPoliticalAdvertisingStatus

