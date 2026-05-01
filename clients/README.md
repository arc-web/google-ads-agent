# Clients

Active client work belongs in this folder.

Pattern:

`clients/{agency}/{client}/`

Create a new client with:

```bash
python3 shared/rebuild/scaffold_client.py \
  --agency AGENCY_SLUG \
  --client CLIENT_SLUG
```

Required first files:

- `campaigns/account_export.csv`
- `reports/performance_inputs/search_terms_report.csv`
- `reports/performance_inputs/location_report.csv`
- `docs/intake.md`

Do not create new client folders at the repository root. Old root-level client folders are archived in `legacy_archive/root_clients/`.

Source of truth:

- `docs/GOOGLE_ADS_AGENT_PROCESS.md`
- `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`

Reference:

- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
