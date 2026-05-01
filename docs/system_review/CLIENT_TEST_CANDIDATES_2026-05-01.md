# Client Test Candidates

Date: 2026-05-01

## Purpose

Pick dry-run account-build candidates without moving, archiving, deleting, or reclassifying client data.

This review supports the active process in:

- [Google Ads Agent Process](../GOOGLE_ADS_AGENT_PROCESS.md)
- [Client Directory Scaffolding](../CLIENT_DIRECTORY_SCAFFOLDING.md)
- [Script Cleanup Process](SCRIPT_CLEANUP_PROCESS_2026-05-01.md)

## Selection Rules

- Keep all client data in place.
- Select candidates by completeness and test coverage.
- Use Google Ads Editor staging only.
- Keep API upload off.
- Keep Search phrase-only by default.
- Use PMAX-heavy clients only to prove inactive guards and salvage boundaries.

## Recommended Candidates

### 1. Current Search Staging Candidate

Client path:

- `clients/therappc/thinkhappylivehealthy/`

Primary evidence:

- `clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/THHL_Search_Services_Editor_Staging_REV1.csv`
- `clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/human_review.md`
- `clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/validation_report.json`
- `clients/therappc/thinkhappylivehealthy/reports/performance_inputs/search_terms_report_2026-04-28.csv`
- `clients/therappc/thinkhappylivehealthy/reports/performance_inputs/location_report_2026-04-28.csv`

Why this is the first dry-run candidate:

- It already has a current Search staging artifact.
- It has validation output and human review notes.
- It exercises the active phrase-only Search workflow.
- It includes real search term and location inputs.
- It has client feedback and revision evidence.

Use it to test:

- active campaign-builder path
- copy engine 15 headline and 4 description contract
- validator pass-through
- one-shot output contract shape
- report workflow later, if full output is tested

Do not use it to decide:

- PMAX activation
- API upload
- generic healthcare strategy without client facts

### 2. PMAX-Heavy Guard Candidate

Client path:

- `clients/evolution_restoration_and_renovation/`

Primary evidence:

- `clients/evolution_restoration_and_renovation/campaigns/EvoRestore_Complete_Campaign_Suite_2025.csv`
- `clients/evolution_restoration_and_renovation/search_themes/pmax_campaign_themes.md`
- `clients/evolution_restoration_and_renovation/search_themes/search_themes.csv`
- `clients/evolution_restoration_and_renovation/docs/ANALYSIS_REPORT.md`
- `clients/evolution_restoration_and_renovation/evorestore_client_config.yaml`

Why this is useful:

- It contains mixed PMAX and Search evidence.
- It is not the active Search staging model, which makes it useful for guard testing.
- It has service and market documentation.
- It can prove PMAX and Search-themes material stays salvage-only during Search rebuild testing.

Use it to test:

- PMAX inactive guards
- API-off boundaries
- old Search and PMAX inputs being read as evidence, not activated as workflow authority
- non-healthcare service-category handling

Do not use it to decide:

- that PMAX should be activated
- that old PMAX rows should become active Search output
- that legacy campaign naming should override current ARC naming

### 3. Simpler Raw Export Candidate

Client path:

- `clients/skytherapies/`

Primary evidence:

- `clients/skytherapies/campaigns/account_export_2026-04-29.csv`

Why this is useful:

- It is smaller than the old multi-folder client sets.
- It appears to be a raw Google Ads Editor style export.
- It includes live account evidence such as ad assets, URLs, approval statuses, and service pages.
- It is useful for testing scaffold defaults against a less prepared client folder.

Use it to test:

- ingesting a raw export into the active scaffold
- extracting service and URL evidence without assuming a completed build folder
- identifying missing search terms, location reports, onboarding, and client facts
- preventing the system from treating sparse client data as launch-ready

Do not use it to decide:

- launch readiness
- final copy claims
- healthcare compliance claims without client onboarding and website verification

## Deferred Candidates

These should stay available, but they are not the first three dry-run candidates:

- `clients/wrights_impact_window_and_door/`: valuable evidence, but very large and noisy. Better after the dry-run path is stable.
- `clients/wrights/`: useful older Search evidence, but overlaps with the larger Wrights material.
- `clients/collab_med_spa/`: useful med spa material, but less important than the current THLH Search staging candidate.
- `clients/my_expert_resume/`: useful national or regional structure evidence, but not needed before the first Search dry run.
- `clients/full_tilt_auto_body/` and `clients/fulltilt_autobody/`: useful PMAX and auto service evidence, but duplicate naming should be reviewed later.
- `clients/brain_based_emdr/`: likely useful healthcare evidence, but less complete than THLH for the current validated workflow.
- `clients/freedom_finance_campaigns/`: useful plan data, but does not appear to be in the current client scaffold shape.

## Recommended Dry-Run Order

1. THLH current Search staging candidate.
2. Sky Therapies simpler raw export candidate.
3. EvoRestore PMAX-heavy guard candidate.

This order tests the active path first, then a sparse real export, then a legacy mixed campaign set.

## Human Review Stops

Stop before:

- moving or archiving any client folder
- deleting old campaign evidence
- activating API upload
- activating PMAX
- changing default Search match type away from Phrase
- promoting a client-specific strategy into shared code
