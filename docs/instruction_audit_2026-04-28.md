# Instruction Audit For Google_Ads_Agent Process

Date: 2026-04-28

## Purpose

This audit removes conflicting process guidance and establishes `Google_Ads_Agent` as the repository standard.

Canonical process document:

- `docs/GOOGLE_ADS_AGENT_PROCESS.md`
- `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`

## Current Canonical Workflow

When given a Google Ads account export and website, the agent should:

1. Ingest the Google Ads Editor account export.
2. Ingest performance reports, including search terms, locations, RSA assets, landing pages, and conversions when available.
3. Scan the website for services, locations, landing pages, claims, and service taxonomy.
4. Build strategy from account evidence plus website evidence.
5. Generate campaign taxonomy and ad groups.
6. Generate phrase-match keywords only.
7. Generate one RSA per ad group with 15 headlines and 4 descriptions when possible.
8. Build geo, radius, demographic, and bid modifier specs.
9. Assemble a Google Ads Editor staging CSV.
10. Validate the CSV and produce a human review file.
11. Stop before upload so Google Ads Editor remains the staging layer.

## Non-Negotiable Rules

- Google Ads Editor is the staging environment.
- Do not post directly to Google Ads from this automation.
- Use phrase match only by default.
- Do not use broad match.
- Do not use exact match unless explicitly requested for a controlled later test.
- Use plain keyword text in `Keyword` with `Criterion Type` set to `Phrase`.
- Populate `EU political ads` on campaign rows.
- Use `Location ID` for location targets when available.
- City ad groups must include all approved target city modifiers.
- RSA headlines must be strong ad copy, not one-word labels or bare service names.
- Every build must include validation and human review artifacts.

## Files Updated In First Cleanup

- `AGENTS.md`
  - Replaced stale memory-context content with the canonical repository instructions.
  - Added required rebuild rules and source links.

- `shared/MASTER_AI_AGENT_INSTRUCTIONS.md`
  - Removed the old claim that it supersedes every other guideline.
  - Replaced it with compatibility guidance that points to the one-shot rebuild process.

- `shared/google_ads_workflow.py`
  - Marked the old workflow as legacy.
  - Removed its claim that it is the single entry point.
  - Updated visible command help to point to the one-shot rebuild process.
  - Changed the inline legacy generator match type from `Exact` to `Phrase`.

- `clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/analyze_search_location_reports.py`
  - Replaced stale phrase-and-exact rebuild guidance with phrase-only guidance.

- `clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/first_campaign_and_next_build_plan.md`
  - Replaced stale phrase-and-exact rebuild guidance with phrase-only guidance.

- `clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/THHL_Search_Services_Editor_Staging_review.md`
  - Updated keyword summary to phrase-only.

- `clients/therappc/thinkhappylivehealthy/docs/rsa_copy_generation_system.md`
  - Updated the automation path to say phrase keyword generation, not phrase-and-exact generation.

## Legacy Material Left In Place

Some older client-specific files still mention broad, exact, PMAX, or past upload-ready assumptions. They are historical client artifacts, not current repository-level instructions.

Examples include:

- `wrights_impact_window_and_door/docs/`
- `collab_med_spa/docs/`
- `evolution_restoration_and_renovation/docs/`
- `shared/gads/tools/`

If any of those older tools are reused in the new automation, they must be wrapped by the one-shot validator and forced through the canonical rules above.

## Second Cleanup

The second cleanup reduced process fragmentation further:

- Moved old root-level client folders into `legacy_archive/root_clients/`.
- Moved old root-level planning documents into `legacy_archive/legacy_plans/`.
- Moved the client-specific one-shot plan into `legacy_archive/client_examples/thinkhappylivehealthy/`.
- Added the client-agnostic process document at `docs/GOOGLE_ADS_AGENT_PROCESS.md`.
- Added client scaffolding instructions at `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`.
- Added `templates/client_template/`.
- Added `shared/rebuild/scaffold_client.py`.
- Replaced `shared/google_ads_workflow.py` with a disabled compatibility wrapper.

## Validation Performed

The audit searched repo instruction and workflow files for conflicting terms including:

- `single entry point`
- `master instruction`
- `phrase and exact`
- `exact match`
- `broad match`
- `upload-ready`
- `auto-fix`

Current repository-level guidance now points to the client-agnostic `Google_Ads_Agent` process.

## Reference Sources

- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en
- Google Ads Editor location import: https://support.google.com/google-ads/editor/answer/30573?hl=en
- Google responsive search ads: https://support.google.com/google-ads/answer/7684791?hl=en-EN
- Google geo targets: https://developers.google.com/google-ads/api/data/geotargets
- Google Ads EU political advertising status: https://developers.google.com/google-ads/api/reference/rpc/v21/EuPoliticalAdvertisingStatusEnum.EuPoliticalAdvertisingStatus
