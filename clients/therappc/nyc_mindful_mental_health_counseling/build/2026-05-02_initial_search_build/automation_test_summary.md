# Initial Campaign Automation Test Summary

Run timestamp: 2026-05-04 01:42:08 JST

Client: Mindful Mental Health Counseling

Website source: https://nycmindfulmentalhealthcounseling.com/

## Scope

This was a new campaign test, not a rebuild and not a revision workflow. There was no inherited Google Ads account export used as a source of performance evidence. The run used website evidence and the repo's active Search staging and client-report pipeline.

## Source Evidence Scanned

- Home page: confirms anxiety-focused online therapy, New York and New Jersey service area, individual therapy, group therapy, CBT, DBT, ACT, mindfulness, depression, OCD, social anxiety, panic, people pleasing, perfectionism, and phobias.
- Contact page: confirms appointment request CTA, phone contact, out-of-network insurance status, and superbill language.
- Group therapy page: confirms online group sessions, 15-minute intro calls, 90-minute group sessions, adult group language, pricing, and NY/NJ licensing eligibility.
- CBT page: confirms CBT-based therapy for anxiety, racing thoughts, young adults, college students, New York City, and New Jersey.
- DBT page: confirms DBT positioning and skills-based therapy support.

## Generated Artifacts

- `Google_Ads_Editor_Staging_CURRENT.csv`
- `validation_report.json`
- `run_csv_validation_report.json`
- `source_attribution.json`
- `website_scan.json`
- `service_catalog.json`
- `landing_page_map.json`
- `geo_strategy.json`
- `campaign_taxonomy.csv`
- `rsa_copy_matrix.csv`
- `human_review.md`
- `Client_New_Campaign_Review.html`
- `Client_New_Campaign_Review.pdf`
- `new_campaign_visual_audit/`

## Campaign Output

- Campaign: `ARC - Search - Anxiety Therapy - V1`
- Network: Google search only
- Match type: Phrase only
- Status: paused for Google Ads Editor review
- Locations: New York and New Jersey by location ID
- Ad groups: 8
- Phrase keywords: 56
- Negative phrase keywords: 10
- RSAs: 8
- RSA assets: 15 headlines and 4 descriptions per ad group

## Validation Results

- Staging validator: pass
- Independent CSV validator: pass
- Static HTML audit: 16 sections, 0 errors, 0 warnings
- Rendered PDF visual audit: 16 pages, 0 failures

## Errors And Friction Hit

- The new-campaign build works, but it is still executed through a client-specific script inside a generated build folder.
- The website scan artifacts are structured JSON, but the source gathering is not yet a reusable scanner plus fact extractor. It still depends on manually curated facts in the run script.
- The presentation instructions had a new-campaign build command, but the follow-up audit examples only showed the older THLH rebuild paths. That made the correct audit sequence less obvious.
- The sitemap was accessible and useful, but there is no repo-local command that turns the sitemap plus selected service pages into `website_scan.json`, `service_catalog.json`, and `source_attribution.json`.
- No live Google Ads Editor import was performed. Platform import warnings still need human review in Google Ads Editor before upload.

## What Worked

- The active Search CSV generator produced Google Ads Editor-compatible UTF-16 output.
- The generator enforced phrase match, Google search only, paused rows, location IDs, and `EU political ads`.
- Copy validation enforced 25 to 30 character RSA headlines and 90 character descriptions before writing the staging CSV.
- The report pipeline produced HTML first, exported PDF through Chrome headless, and generated rendered page images for inspection.
- Static and rendered audits passed after export.

## Recommended Improvements Started

- Updated `presentations/docs/BUILD_INSTRUCTIONS.md` with the new-campaign static HTML audit and rendered PDF audit commands.
- Captured this run summary in the client build folder so the automation gaps are tied to the generated artifacts.

## Recommended Next Improvements

- Promote the reusable part of `build_initial_search_campaign.py` into shared code while keeping the client file as a thin wrapper.
- Add a repo-local website scan command that accepts a website URL, sitemap URL, selected source pages, and output build directory.
- Add a fact extraction review step that distinguishes verified website facts, inferred strategy, and human-review-needed claims.
- Add a single initial-campaign command that runs scan, campaign plan, staging CSV generation, validation, HTML/PDF report export, static audit, and visual audit.
- Add a machine-readable run manifest with command versions, source URLs, validation results, and artifact checksums.
