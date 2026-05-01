# Mindful Mental Health Counseling

Client slug: `nyc_mindful_mental_health_counseling`

Agency slug: `therappc`

Website: https://nycmindfulmentalhealthcounseling.com/

## Purpose

This directory is a `Google_Ads_Agent` client workspace. It is created from `templates/client_template/` and should follow the process in:

- `docs/GOOGLE_ADS_AGENT_PROCESS.md`
- `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`
- `docs/ONBOARDING_INGESTION_AND_REVISION_WORKFLOW.md`

## Required First Files

Add:

- `campaigns/account_export.csv`
- `reports/performance_inputs/search_terms_report.csv`
- `reports/performance_inputs/location_report.csv`
- `docs/intake.md`
- `docs/client_onboarding_questionnaire.md`
- `docs/client_revision_feedback_template.md`

Optional but recommended:

- `reports/performance_inputs/rsa_asset_report.csv`
- `reports/performance_inputs/landing_page_report.csv`
- `reports/performance_inputs/conversion_action_report.csv`

## Build Output

The one-shot rebuild should create:

- `build/{date}_account_rebuild/Google_Ads_Editor_Staging_CURRENT.csv`
- `build/{date}_account_rebuild/Client_Rebuild_Review.html`
- `build/{date}_account_rebuild/Client_Rebuild_Review.pdf`
- `build/{date}_account_rebuild/human_review.md`
- `build/{date}_account_rebuild/validation_report.json`
- `build/{date}_account_rebuild/client_feedback_classified.json`
- `build/{date}_account_rebuild/revision_decision_log.csv`

## Reference Sources

- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en
