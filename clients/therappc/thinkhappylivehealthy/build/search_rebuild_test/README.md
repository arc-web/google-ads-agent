# THHL Search Rebuild Test Operator Note

This folder contains both current staging scripts and older draft scripts from the THHL rebuild work.

## Current Paths

Use these first:

- `generate_services_search_editor_csv.py`
  - builds `THHL_Search_Services_Editor_Staging_CURRENT.csv`
  - current broad service build
  - passes the shared staging validator
- `apply_round1_core_focus_revisions.py`
  - builds `THHL_Search_Services_Editor_Staging_REV1.csv`
  - current client-feedback revision path
  - passes local validation and the shared staging validator

## Compatibility Path

- `rebuild_thhl_search_campaign.py`
  - older entry point kept so old notes and commands do not break
  - now delegates to the current service staging generator
  - writes the legacy-named `THHL_Search_Rebuild_Test_2026-04-28.csv`
  - must pass the shared staging validator before its report is accepted

## Do Not Use As Authority

Do not treat archived reports or older draft outputs as current unless they pass:

```bash
python3 shared/rebuild/staging_validator.py --csv PATH_TO_STAGING_CSV
```

The shared validator is the active Google Ads Editor staging contract for this repo.
