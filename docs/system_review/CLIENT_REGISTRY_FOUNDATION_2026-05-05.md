# Client Registry Foundation

Date: 2026-05-05

## Result

The client registry foundation reconciles read-only Supabase active end-client rows with local `clients/` directories.

Active end-client definition:

- `clients.status = active`
- `clients.relationship_type = client`
- `companies.company_type = client`

The generated registry files are:

- `clients/client_registry.csv`
- `clients/client_directory_gap_report.csv`

## FDL Resolution

`clients/arc/fdl_xibalba/` is the canonical local directory for the FDL account because it has the richer scaffold, website URL, and build artifacts.

No `clients/arc/fdlxibalba/` directory existed in the final implementation worktree, so no duplicate content needed migration or removal during this pass.

## Commands

```bash
python3 -m shared.clients.client_registry verify-api
python3 -m shared.clients.client_registry sync --output clients/client_registry.csv --gap-report clients/client_directory_gap_report.csv
python3 -m shared.clients.client_registry scaffold-missing --dry-run
```

These commands are read-only for Supabase and do not mutate Google Ads or Discord.

## Reference Sources

- Supabase REST API: https://supabase.com/docs/guides/api
- Google Ads Change Status: https://developers.google.com/google-ads/api/docs/change-status
- Google Ads Change Event: https://developers.google.com/google-ads/api/docs/change-event
