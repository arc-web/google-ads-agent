# Shared GADS Tools

This folder is mostly salvage material.

## Active Helper

- `search_staging_support.py`

Role:

- creates generic Search ad group and keyword plans
- defaults keywords to phrase match through `Criterion Type`
- supports negative phrase plans without leading-minus keyword text
- feeds `GoogleAdsEditorExporter`
- does not activate PMAX, API upload, Broad, Exact, or client-specific logic

## Salvage Material

The older keyword, ad group, extension, campaign planning, and example files remain here for review. They should not be treated as active workflow code until useful behavior is migrated into a tested helper and validated through:

```bash
python3 shared/rebuild/staging_validator.py --csv PATH_TO_STAGING_CSV
```

Known stale assumptions in the older files:

- Broad and Exact examples
- PMAX branches
- API or MCP automation concepts
- old optimization and auto-generation behavior
- account-shaped examples

## Current Rule

Use `search_staging_support.py` for reusable Search helper behavior. Treat every other file in this folder as reference or salvage unless a later cleanup loop promotes it with tests.
