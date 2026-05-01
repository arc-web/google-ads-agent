# Google_Ads_Agent

`Google_Ads_Agent` audits Google Ads accounts and client websites, then produces staged rebuild CSVs for Google Ads Editor.

## Start Here

Use these documents as the source of truth:

- `docs/GOOGLE_ADS_AGENT_PROCESS.md`
- `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`
- `docs/SOURCE_ATTRIBUTION_AND_BRAND_RULES.md`
- `docs/ONBOARDING_INGESTION_AND_REVISION_WORKFLOW.md`
- `docs/HTML_PDF_CLIENT_REPORT_STANDARD.md`
- `docs/AI_REASONING_GATES.md`
- `docs/CLIENT_FACING_LANGUAGE_RULES.md`
- `AGENTS.md`

## Active Work

Active client work lives under:

`clients/{agency}/{client}/`

Create a client scaffold with:

```bash
python3 shared/rebuild/scaffold_client.py \
  --agency AGENCY_SLUG \
  --client CLIENT_SLUG
```

Then add:

- `campaigns/account_export.csv`
- `reports/performance_inputs/search_terms_report.csv`
- `reports/performance_inputs/location_report.csv`
- `docs/intake.md`
- `docs/client_onboarding_questionnaire.md`
- `docs/client_revision_feedback_template.md`

## Canonical Rebuild Output

Each rebuild should produce:

- `Google_Ads_Editor_Staging_CURRENT.csv`
- `Client_Rebuild_Review.html`
- `Client_Rebuild_Review.pdf`
- `human_review.md`
- `validation_report.json`
- supporting audit, website, keyword, copy, and targeting files.
- classified client feedback and revision decision logs after client review.

Google Ads Editor is the staging environment. Do not post generated CSVs directly without human review.

Previous provider names from imported files are source attribution only. Do not bake them into new campaign names, ad groups, ad copy, or client-facing branding.

Use `ARC` for ownership-level campaign names and labels, for example `ARC - Search - Services - V1`. Keep client identity in the ads, landing pages, URLs, and review content.

## Legacy Archive

Old root-level client folders and older planning docs are in:

`legacy_archive/`

Do not use archive files as process instructions unless they are reviewed against the current `Google_Ads_Agent` process.

## Reference Sources

- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en
- Google Ads Editor location import: https://support.google.com/google-ads/editor/answer/30573?hl=en
- Google responsive search ads: https://support.google.com/google-ads/answer/7684791?hl=en-EN
