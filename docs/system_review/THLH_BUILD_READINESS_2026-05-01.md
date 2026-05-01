# THLH Build Readiness

Date: 2026-05-01

## Decision

THLH is the active first client for the next account-build testing phase.

The current best staging artifact is:

- [THHL Search Services Editor Staging REV1](../../clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/THHL_Search_Services_Editor_Staging_REV1.csv)

This file was previously staging-clean under the structural rules. After the 2026-05-01 headline quality rule update, it is now blocked for copy repair before package assembly. It is not a live-launch approval and does not activate API upload.

## Current Validation Result

Fresh structural validation before the headline quality rule update:

- active staging validator: pass
- `MasterValidator`: PASS, 0 issues
- `SearchMasterValidator`: success, 0 issues

Current validation after the headline quality rule update:

- active staging validator: fail
- failure type: `headline_minimum_value`
- failed headline count: 443
- reason: short low-value RSA headlines under 25 characters now fail quality review

REV1 output shape:

- rows: 470
- campaigns: 4
- ad groups: 49
- Phrase keyword rows: 295
- Negative Phrase keyword rows: 20
- RSA rows: 49
- location rows: 49
- bid modifier rows: 53
- radius rows: 4
- API upload fields: none

Campaigns:

- `ARC - Search - Adult Therapy - V1`
- `ARC - Search - Brand - V1`
- `ARC - Search - Psychiatry - V1`
- `ARC - Search - Testing - V1`

## Why THLH Is First

THLH is the first client because it has:

- current Search staging output
- client feedback and revision decisions
- search term evidence
- location evidence
- taxonomy evidence
- RSA copy planning
- validation reports
- client-facing report artifacts
- a successful smaller dry-run artifact

This makes it the best client for proving the cleaned system can move from staging generation into a fuller one-shot build package.

## Current Usable Assets

Usable now as source evidence:

- `THHL_Search_Services_Editor_Staging_REV1.csv`
- `THHL_Search_Services_Editor_Staging_REV1_review.md`
- `THHL_Search_Services_Editor_Staging_REV1_validation.json`
- `client_feedback_classified.json`
- `revision_decision_log.csv`
- `targeting_spec.json`
- `rsa_copy_blueprint.json`
- `service_ad_group_taxonomy_2026-04-28.csv`
- `organized_search_terms_2026-04-28.csv`
- `organized_locations_2026-04-28.csv`
- `Client_Rebuild_Review.html`
- `Client_Rebuild_Review.pdf`

## Current Gaps Before A Complete One-Shot Package

The staging file structure is strong, but RSA headline quality must be repaired before the one-shot output contract is packaged.

Missing or not yet normalized to canonical filenames:

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
- `Google_Ads_Editor_Staging_CURRENT.csv`
- `Google_Ads_Editor_Staging_REV1.csv`

Important note:

- Some equivalent evidence exists under THLH-specific names, but it has not been normalized into the one-shot output contract.
- The older `human_review.md` describes an earlier broad service build and should not be treated as the current REV1 review authority.
- The current REV1 review authority is `THHL_Search_Services_Editor_Staging_REV1_review.md`.

## Next Work For THLH

Recommended next batch:

1. Audit all REV1 RSA headlines that fail `headline_minimum_value`.
2. Rewrite weak short headlines such as `Ashburn Care` and `Anxiety Counseling`.
3. Re-run staging validation, `MasterValidator`, and `SearchMasterValidator`.
4. Create a THLH one-shot package folder without moving existing client data.
5. Copy or generate canonical aliases for the repaired staging and review evidence.
6. Normalize existing THLH evidence into the one-shot filenames where the source is clear.
7. Generate missing evidence only from current client inputs.
8. Produce a current `human_review.md` tied to the repaired REV1, not the older broad service build.
9. Keep API upload off.

## Human Review Stops

Stop before:

- changing match policy away from Phrase
- activating PMAX
- activating API upload or live mutation
- deleting, archiving, or moving client data
- replacing client feedback decisions with shared assumptions

## Sources

- [Client Test Candidates](CLIENT_TEST_CANDIDATES_2026-05-01.md)
- [Dry-Run Account Build Test](DRY_RUN_ACCOUNT_BUILD_TEST_2026-05-01.md)
- [Google Ads Agent Process](../GOOGLE_ADS_AGENT_PROCESS.md)
- [Google Ads Editor CSV Import](https://support.google.com/google-ads/editor/answer/30564)
- [Google Ads Editor CSV Columns](https://support.google.com/google-ads/editor/answer/57747)
