# Client Directory Scaffolding

Date: 2026-04-28

## Rule

New active client work should live under:

`clients/{agency}/{client}/`

Do not create new active client folders at the repository root.

Existing client folders that predate the agency/client layout remain active under:

`clients/{client_slug}/`

Do not archive or purge existing client folders until the overall system has been tested, the folder has been reviewed, and the repo owner explicitly approves the archive decision.

## Create A New Client

Use:

```bash
python3 shared/rebuild/scaffold_client.py \
  --agency AGENCY_SLUG \
  --client CLIENT_SLUG
```

Example:

```bash
python3 shared/rebuild/scaffold_client.py \
  --agency therappc \
  --client example_client
```

This creates:

```text
clients/{agency}/{client}/
  README.md
  assets/
  build/
    current/
  campaigns/
  config/
    client_profile.yaml
  docs/
    client_hq/
    intake.md
  reports/
    performance_inputs/
```

## Where Files Go

Account exports:

- `campaigns/account_export.csv`

Performance reports:

- `reports/performance_inputs/search_terms_report.csv`
- `reports/performance_inputs/location_report.csv`
- `reports/performance_inputs/rsa_asset_report.csv`
- `reports/performance_inputs/landing_page_report.csv`
- `reports/performance_inputs/conversion_action_report.csv`

Client notes:

- `docs/client_hq/`
- `docs/client_hq/client_hq.md`
- `docs/client_hq/client_hq.json`
- `docs/intake.md`
- `docs/client_onboarding_questionnaire.md`
- `docs/client_revision_feedback_template.md`

Current build:

- `build/current/`

Dated rebuilds:

- `build/{date}_account_rebuild/`

Generated Google Ads Editor CSV files:

- Must include the client slug and date/time in the filename.
- Use `{client_slug}_google_ads_editor_staging_{YYYYMMDD_HHMMSS}.csv` for initial/current staging.
- Use `{client_slug}_google_ads_editor_staging_rev1_{YYYYMMDD_HHMMSS}.csv` for approved revision staging.
- Do not overwrite upload candidates with generic `CURRENT` filenames. Keep dated versions searchable for Google Ads Editor import review.

## Required Intake Fields

Before generating a rebuild, fill in:

- Client display name.
- Website URL.
- Durable Client HQ facts in `docs/client_hq/` when available.
- Agency slug.
- Client slug.
- Primary market.
- Target cities.
- Target states or regions.
- Services to prioritize.
- Services to exclude.
- Claim, offer, licensing, and capacity notes.
- Any sensitive-category restrictions.
- Legal entity and advertiser verification timing.
- Client-approved insurance and billing language.
- Services with current capacity.
- Services to pause or exclude.

## Template Files

The reusable template lives here:

- `templates/client_template/README.md`
- `templates/client_template/config/client_profile.yaml`
- `templates/client_template/docs/intake.md`
- `templates/client_template/docs/client_onboarding_questionnaire.md`
- `templates/client_template/docs/client_revision_feedback_template.md`
- `templates/client_template/campaigns/account_export_template.csv`
- `templates/client_template/reports/performance_inputs/search_terms_report_template.csv`
- `templates/client_template/reports/performance_inputs/location_report_template.csv`

## Reference Sources

- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en
- Google Ads Editor location import: https://support.google.com/google-ads/editor/answer/30573?hl=en
