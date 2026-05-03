# Google_Ads_Agent Process

Date: 2026-04-28

## Goal

Given a Google Ads Editor export CSV, performance reports, and a client website, `Google_Ads_Agent` runs a repeatable rebuild process:

1. Ingest client onboarding and business constraints.
2. Audit the account.
3. Scan the website.
4. Ingest performance and analytics reports.
5. Normalize source attribution so old provider names stay out of generated work.
6. Build service, landing page, geo, keyword, and copy strategy.
7. Generate phrase-match Search campaign rebuilds.
8. Create RSA copy through quality gates.
9. Build targeting and bid adjustment specs.
10. Validate the output.
11. Produce a Google Ads Editor staging CSV.
12. Generate and prepare a client-facing campaign review document through deterministic presentation scripts.
13. Classify client revisions.
14. Regenerate approved revisions.
15. Hand off to launch readiness and client approval call.

Google Ads Editor is the staging environment. The automation stops before upload.

## Required Inputs

Minimum:

- Google Ads Editor account export CSV.
- Website URL.
- Client name.
- Agency or workspace name.
- Target market or service area if known.

Recommended:

- Search terms report.
- Location report.
- RSA asset report.
- Landing page performance report.
- Conversion action report.
- Client notes about priority services, exclusions, offers, licensing, capacity, and claims.
- Client onboarding questionnaire.
- Client revision feedback after the first review document.

## Client Directory

New active clients live here:

`clients/{agency}/{client}/`

Existing client folders that predate the agency/client layout remain active under:

`clients/{client_slug}/`

Keep existing client data actionable until the system is tested and the repo owner explicitly decides what, if anything, should be archived.

Use the template:

`templates/client_template/`

Create a new client with:

```bash
python3 shared/rebuild/scaffold_client.py \
  --agency AGENCY_SLUG \
  --client CLIENT_SLUG
```

After scaffolding, place exports and reports here:

- `campaigns/account_export.csv`
- `reports/performance_inputs/search_terms_report.csv`
- `reports/performance_inputs/location_report.csv`
- `reports/performance_inputs/rsa_asset_report.csv`
- `reports/performance_inputs/landing_page_report.csv`

## Output Contract

Each rebuild creates:

`clients/{agency}/{client}/build/{date}_account_rebuild/`

With:

- `account_audit.json`
- `account_snapshot.json`
- `source_attribution.json`
- `website_scan.json`
- `service_catalog.json`
- `landing_page_map.json`
- `geo_strategy.json`
- `search_term_analysis.csv`
- `keyword_expansion_candidates.csv`
- `negative_review_candidates.csv`
- `campaign_taxonomy.csv`
- `rsa_copy_matrix.csv`
- `targeting_spec.json`
- `human_review.md`
- `Client_Rebuild_Review.html`
- `Client_Rebuild_Review.pdf`
- `validation_report.json`
- `{client_slug}_google_ads_editor_staging_{YYYYMMDD_HHMMSS}.csv`
- `client_feedback_classified.json`
- `revision_decision_log.csv`
- `{client_slug}_google_ads_editor_staging_rev1_{YYYYMMDD_HHMMSS}.csv` when revisions are approved.

Generated Google Ads Editor CSV filenames must include the client slug and date/time. Do not overwrite a prior upload candidate with a generic `CURRENT` filename. Keep old dated CSVs in the build folder so operators can search by client and select the intended version in Google Ads Editor.

Provider-token validation helper:

```bash
python3 shared/rebuild/provider_token_validator.py \
  --token RevKey \
  --file clients/{agency}/{client}/build/{date}_account_rebuild/{client_slug}_google_ads_editor_staging_{YYYYMMDD_HHMMSS}.csv
```

Google Ads Editor staging validation helper:

```bash
python3 shared/rebuild/staging_validator.py \
  --csv clients/{agency}/{client}/build/{date}_account_rebuild/{client_slug}_google_ads_editor_staging_{YYYYMMDD_HHMMSS}.csv
```

## Pipeline

### 0. Ingest Client Onboarding

Read client-provided business truth before strategy generation.

Extract:

- Services currently available.
- Services to pause or exclude.
- Capacity by service.
- Priority growth services.
- Eligible ages.
- Insurance and billing language.
- Licensed states and telehealth constraints.
- Legal entity and verification timing.
- Approved claims and prohibited claims.

Client feedback is authoritative for business facts, capacity, compliance, and priorities. It is not automatically authoritative for campaign structure, keyword count, ad group count, or bidding mechanics.

Detailed workflow:

- `docs/ONBOARDING_INGESTION_AND_REVISION_WORKFLOW.md`

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
- Source provider names and legacy naming suffixes.
- Keyword match type format.
- Location ID format where possible.

Source attribution rule:

- Treat old provider names, legacy vendor suffixes, and imported campaign ownership markers as source metadata only.
- Do not use those tokens in generated campaign names, ad group names, keywords, RSA copy, display paths, final URLs, output filenames, or repeated document branding.
- Use `source_attribution.json` to preserve the detected source context.
- Follow `docs/SOURCE_ATTRIBUTION_AND_BRAND_RULES.md`.

### 2. Ingest Performance Reports

Search terms:

- Classify service intent.
- Classify intent layer: General, Local, City, State.
- Mark converting terms for phrase keyword expansion.
- Mark high-impression non-converters for review.
- Mark competitor, provider name, coaching, out-of-market, and irrelevant terms for negative review.

Location reports:

- Rank states, counties, cities, ZIPs, and radius performance.
- Identify core geos.
- Identify expansion geos.
- Identify reduce or exclude candidates.
- Add Google geo target IDs where available.

Asset reports:

- Identify strongest old headlines and descriptions.
- Extract reusable language patterns.
- Reject weak or policy-risk language.

### 3. Scan Website

Crawl the client website.

Extract:

- Service pages.
- Page titles and H1s.
- Service categories.
- Locations.
- Appointment pages.
- Insurance, access, and offer language.
- Staff credentials if visible.
- Compliance-sensitive claims.
- Landing page URLs for each service.

### 4. Build Strategy

Generate strategy from account data plus site data.

Decide:

- Which campaigns to rebuild first.
- Which services belong in the first build.
- Which ad groups should exist.
- Which geos are core versus expansion.
- Which audiences or demographics should be observed.
- Which terms should be reviewed as negatives.
- Which landing pages need review.

Default ad group pattern:

- `Service - Audience/Category - General`
- `Service - Audience/Category - Local`
- `Service - Audience/Category - City`
- `Service - Audience/Category - State`

Naming rules:

- Campaign names must use `ARC` as the ownership prefix when the name identifies who built or manages the structure.
- Default campaign pattern: `ARC - Search - {CampaignTheme} - V1`.
- Ad group names must communicate service, audience or category, and intent layer.
- Old provider names may not be appended as campaign suffixes.
- `Advertising Report Card` is the agency brand in client-facing review documents.
- Client names, services, website, and locations belong in ad-facing copy, URLs, landing page choices, and client review context.

### 5. Build Keyword System

Generate phrase-match keywords only.

Do not use broad match.

Do not use exact match unless the user explicitly requests a later controlled test.

Keyword sources:

- Core root terms from service taxonomy.
- Singular and plural variants.
- Audience variants where relevant.
- High-performing search terms.
- Geo modifiers.
- City list.
- State list.

Intent-layer rules:

- General: no geo modifier.
- Local: `near me`, `near you`, and close-proximity variants.
- City: every approved target city, not only one.
- State: approved state and regional terms.

Keyword gates:

- Must map directly to a service.
- Must map to a relevant landing page.
- Must be phrase match.
- Must be title-cased for Editor readability.
- Must not be competitor, provider-name, coaching, or out-of-market unless human approved.
- Must not duplicate another keyword in the same ad group.

### 6. Build RSA Copy System

Generate one RSA per ad group.

Each RSA should include:

- 15 headlines.
- 4 descriptions.
- Path 1.
- Path 2.
- Final URL.

Headline system:

- Build a candidate pool per ad group.
- Score each headline.
- Keep the top 15.

Headline gates:

- 25 to 30 characters whenever possible.
- Max 30 characters.
- No one-word headlines.
- No bare labels like `Psychiatry`, `Therapy`, `Service`, or equivalent generic category names.
- No short vague labels like `Ashburn Care`, `Anxiety Counseling`, or other low-value filler.
- No broken truncation.
- No duplicate ideas.
- No unsupported claims.
- No sensitive-condition personalization.

Description gates:

- Max 90 characters.
- Mention service or service category.
- Mention access, process, value prop, or CTA.
- No unsupported claims.
- No policy-risk language.

### 7. Build Targeting

Generate targeting rows for Google Ads Editor.

Targets:

- Location rows.
- Location IDs where available.
- Radius rows where used.
- Bid modifiers.
- Demographic rows only when appropriate.

For sensitive verticals:

- Keep demographics observational unless data and policy review support modifiers.
- Do not exclude sensitive groups in the first rebuild.
- Do not write copy that implies knowledge of a user's condition, identity, or private attribute.

### 8. Assemble Google Ads Editor CSV

Use the account export header as the base schema when possible.

Required fields:

- `Campaign Type`: `Search`
- `Networks`: `Google search`
- `EU political ads`: populated with the account-appropriate value.
- `Broad match keywords`: `Off`
- `Targeting method`: `Location of presence`
- `Exclusion method`: `Location of presence`
- `Criterion Type`: `Phrase`
- `Keyword`: plain keyword text, not quotes or brackets.
- `Location ID`: present where available.

### 9. Generate Client-Facing Campaign Review PDF

After the staging CSV is final, generate a branded HTML review document and export it to PDF with Chrome headless. The PDF is the client-facing deliverable. The HTML is the editable source of truth for revisions. Internal validation runs in stage 10.

Do not generate a DOCX as the primary client-facing rebuild review. DOCX is an internal fallback format only and does not preserve the branded report design.

Inputs:

- Final staging CSV from stage 8.
- Search term and location performance findings from stage 2.
- Account export inventory from stage 1.
- Copy grades from the copy quality gate.
- Brand assets from `clients/{agency}/{client}/assets/` or screenshots from the website.
- Client profile from `clients/{agency}/{client}/config/client_profile.yaml`.

Outputs:

- `clients/{agency}/{client}/build/{date}_account_rebuild/Client_Rebuild_Review.html`
- `clients/{agency}/{client}/build/{date}_account_rebuild/Client_Rebuild_Review.pdf`

Required sections in order:

1. Cover with client name, website, date, status banner, and brand-inspired visual treatment.
2. Executive summary with key metrics and the client approval goal.
3. Before and after showing what changed and why.
4. Campaign architecture explaining the ad group naming system.
5. Keyword strategy with representative examples, not a full keyword dump.
6. Targeting strategy with core locations, expansion locations, and bid adjustment logic.
7. Future optimization plan explaining how campaigns can split over time.
8. Ad copy review with actual ad previews, headline lists, description lists, URLs, and paths.
9. Approval checklist with clear client decisions.
10. Sources and staging notes.

Brand and source attribution rules:

- The document should show `Advertising Report Card` as the prepared-by agency.
- Previous provider names may appear once in the before-and-after section or sources and staging notes when needed for context.
- Do not use previous provider names in page headers, campaign names, sample ad group names, filenames, or repeated body copy.

Hard rules - copy violations:

- Headlines must be at or under 30 characters at generation time. Any over-limit asset is a blocker, not a flag.
- Headlines under 25 characters fail quality review unless a human explicitly approves a rare exception.
- Descriptions must be at or under 90 characters at generation time.
- All violations are caught and replaced before this stage runs.

Hard rules - document layout:

- Do not include thousands of keywords or every ad variation.
- Use representative examples and client decision tables.
- Use major section headers for report landmarks and subsection headers for variable-length groups.
- Use continuation headers when a module spans pages.
- Do not rely on bare subtitles before large grids, long tables, or ad-copy blocks.
- Layout must be dynamic, variable, and intelligent based on account size, industry, and content density.
- No text or critical element can sit directly on a page edge, border, or accent rule.
- Keep tables readable with padding and wrapped text.
- Run `shared/presentation/report_quality_audit.py` before PDF export.
- Export the HTML to PDF and inspect the PDF before delivery.
- Fix text clipping, awkward page breaks, distorted screenshots, or cramped tables before sharing.
- Never use pandoc, Word, or PPTX as the canonical branded report path.

Generator entry point:

- `shared/presentation/build_review_doc.py`

Preparation entry point:

- `shared/presentation/prepare_client_review_html.py`

Detailed stage requirements:

- `docs/HUMAN_IN_THE_LOOP_REVIEW_STAGE.md`
- `docs/HTML_PDF_CLIENT_REPORT_STANDARD.md`
- `docs/AI_REASONING_GATES.md`

### 10. Validate

Hard validations:

- CSV encoding.
- Required headers.
- Campaign row present.
- EU political ads field populated.
- No broad match.
- No Search partners. Search campaigns must use `Google search` only.
- Phrase keywords only.
- No missing final URLs.
- 15 RSA headlines when possible.
- 4 RSA descriptions when possible.
- Headline max 30 characters.
- Headline minimum 25 characters unless a human approves a rare exception.
- Description max 90 characters.
- Path fields max 15 characters.
- No one-word headlines.
- No broken truncated headlines.
- No duplicate keywords in the same ad group.
- Location IDs where available.
- No blocked previous-provider tokens in generated campaign names, ad group names, keywords, RSA copy, display paths, final URLs, output filenames, or repeated document branding.

Initial provider-token validator:

- `shared/rebuild/provider_token_validator.py`

Soft validations:

- Landing page fallback warnings.
- Low-evidence ad groups.
- High-risk terms for review.
- Demographic targeting review.
- Geo expansion review.

### 11. Human Review

The automation stops before upload.

The human review stage must summarize:

- Campaign names.
- Budgets.
- Geo bid modifiers.
- Search terms added.
- Negative candidates.
- Landing page fallbacks.
- RSAs by ad group.
- Any policy warnings.
- Any assumptions that need client approval.

### 12. Revision Triage

After the client responds, classify each feedback item before editing the CSV.

Required classification:

- `business_fact`
- `capacity_constraint`
- `compliance_or_claim`
- `website_gap`
- `campaign_revision`
- `strategy_question`
- `tracking_or_measurement`
- `legal_or_verification`
- `client_preference`
- `expert_override_needed`

Revision rules:

- Apply business fact, capacity, and compliance corrections directly.
- Create website guidance when the campaign and website do not agree.
- Update the build engine when feedback exposes a reusable rule gap.
- Use one-off scripts only for narrow revisions that do not belong in the reusable engine.
- Do not let client preference override campaign architecture without a strategy decision.

Required outputs:

- `client_feedback_classified.json`
- `revision_decision_log.csv`
- `engine_rule_updates.md`
- `client_questions_for_call.md`
- `{client_slug}_google_ads_editor_staging_rev1_{YYYYMMDD_HHMMSS}.csv` when approved revisions are regenerated.

## Agent Architecture

- Orchestrator: coordinates stages and writes the build folder.
- Account audit agent: parses export and summarizes current state.
- Website scan agent: crawls site and builds service catalog.
- Strategy agent: creates campaign plan, ad group taxonomy, and targeting direction.
- Keyword agent: builds phrase-match keyword matrix.
- Copy agent: generates and scores RSA assets.
- Targeting agent: builds geo, radius, location ID, demographic, and bid modifier specs.
- Source attribution agent: preserves source provenance while stripping old provider tokens from generated naming and copy.
- Validator agent: runs schema, policy, and quality gates.
- Presentation agent: generates the client-facing campaign review HTML and PDF for stage 9.
- Review agent: produces `human_review.md`.
- Revision triage agent: classifies client feedback and decides whether it is a campaign change, website guidance item, engine update, or strategy discussion.
- Launch readiness agent: checks conversion tracking, verification timing, PHI handling, and final client approvals before posting.

## Reference Sources

- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en
- Google Ads Editor location import: https://support.google.com/google-ads/editor/answer/30573?hl=en
- Google responsive search ads: https://support.google.com/google-ads/answer/7684791?hl=en-EN
- Google geo targets: https://developers.google.com/google-ads/api/data/geotargets
- Google Ads EU political advertising status: https://developers.google.com/google-ads/api/reference/rpc/v21/EuPoliticalAdvertisingStatusEnum.EuPoliticalAdvertisingStatus
- Google Ads bid adjustments: https://support.google.com/google-ads/answer/2732132?hl=en
- Google Ads Editor location bid adjustments: https://support.google.com/google-ads/editor/answer/47629?hl=en
- Google Ads healthcare and medicines policy: https://support.google.com/adspolicy/answer/176031?hl=en
- Google Ads customer data policies: https://support.google.com/google-ads/answer/7475709?hl=en
- Google Analytics HIPAA guidance: https://support.google.com/analytics/answer/13297105?hl=en
