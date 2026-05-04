# {{CLIENT_DISPLAY_NAME}}

Client slug: `{{CLIENT_SLUG}}`

Agency slug: `{{AGENCY_SLUG}}`

Website: {{WEBSITE_URL}}

## Purpose

This directory is a `Google_Ads_Agent` client workspace. It is created from `templates/client_template/` and should follow the process in:

- `docs/GOOGLE_ADS_AGENT_PROCESS.md`
- `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`
- `docs/ONBOARDING_INGESTION_AND_REVISION_WORKFLOW.md`

## Required First Files

Add:

- `docs/client_hq/`
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
- `reports/performance_inputs/quality_score_report.csv`
- `reports/performance_inputs/auction_insights_report.csv`
- `reports/performance_inputs/recommendations_report.csv`
- `reports/performance_inputs/disapproval_report.csv`
- `reports/performance_inputs/audience_report.csv`

## Build Output

The one-shot rebuild should create:

- `build/{date}_account_rebuild/{{CLIENT_SLUG}}_google_ads_editor_staging_{YYYYMMDD_HHMMSS}.csv`
- `build/{date}_account_rebuild/Client_Rebuild_Review.html`
- `build/{date}_account_rebuild/Client_Rebuild_Review.pdf`
- `build/{date}_account_rebuild/client_email_draft.md`
- `build/{date}_account_rebuild/human_review.md`
- `build/{date}_account_rebuild/validation_report.json`
- `build/{date}_account_rebuild/conversion_tracking_audit.json`
- `build/{date}_account_rebuild/evidence_quality_report.json`
- `build/{date}_account_rebuild/optimization_cadence_plan.json`
- `build/{date}_account_rebuild/bid_strategy_recommendation.json`
- `build/{date}_account_rebuild/audience_mode_audit.json`
- `build/{date}_account_rebuild/recommendations_triage.csv`
- `build/{date}_account_rebuild/policy_disapproval_audit.json`
- `build/{date}_account_rebuild/launch_readiness_checklist.md`
- `build/{date}_account_rebuild/client_feedback_classified.json`
- `build/{date}_account_rebuild/revision_decision_log.csv`

Generated Google Ads Editor CSV filenames must include this client slug and a date/time stamp so upload candidates are searchable by client and version in Google Ads Editor.

Client-facing packages must include `client_email_draft.md`. The email should summarize the report, reference the attached PDF, and describe the staging file only as the campaign build or revised campaign.

Client HQ files live under `docs/client_hq/`. Store the original source document there, plus generated `client_hq.md` and `client_hq.json` when available. These facts are used before repeat website crawling for services, locations, contacts, delivery mode, and targeting constraints.

## Reference Sources

- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en
