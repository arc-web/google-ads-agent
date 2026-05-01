# THLH Build Readiness

Date: 2026-05-01

## Decision

THLH is the active first client for the next account-build testing phase.

The current best staging artifact is:

- [THHL Search Services Editor Staging REV2](../../clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/THHL_Search_Services_Editor_Staging_REV2.csv)

REV2 repairs the short RSA headlines that blocked REV1 after the 2026-05-01 headline quality rule update. It is not a live-launch approval and does not activate API upload.

## Current Validation Result

Fresh structural validation before the headline quality rule update:

- active staging validator: pass
- `MasterValidator`: PASS, 0 issues
- `SearchMasterValidator`: success, 0 issues

Current validation after the REV2 headline repair:

- active staging validator: pass, 0 issues
- `MasterValidator`: PASS, 0 issues
- `SearchMasterValidator`: success, 0 issues
- headline repairs applied: 443 placements across 63 unique weak headlines
- all RSA headlines are now 25 to 30 characters
- all campaign network values are `Google search`

REV2 output shape:

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

- `THHL_Search_Services_Editor_Staging_REV2.csv`
- `THHL_Search_Services_Editor_Staging_REV2_review.md`
- `THHL_Search_Services_Editor_Staging_REV2_validation.json`
- `THHL_Search_Services_Editor_Staging_REV2_headline_repair_summary.json`
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

The staging file structure and RSA headline quality are now clean. The remaining work is packaging the current evidence into the canonical one-shot output contract.

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
- The current staging review authority is `THHL_Search_Services_Editor_Staging_REV2_review.md`.

## Next Work For THLH

Recommended next batch:

1. Create a THLH one-shot package folder without moving existing client data.
2. Copy or generate canonical aliases for the REV2 staging and review evidence.
3. Normalize existing THLH evidence into the one-shot filenames where the source is clear.
4. Generate missing evidence only from current client inputs.
5. Produce a current `human_review.md` tied to REV2, not the older broad service build.
6. Keep API upload off.

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
