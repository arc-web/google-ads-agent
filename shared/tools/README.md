# Shared Tools

This folder contains shared helper tools. Only explicitly marked helpers are active.

## Active Campaign Tool

- `campaign/search_campaign_builder.py`

Role:

- builds generic Search campaign staging files
- uses phrase-only keyword rows
- requires 15 RSA headlines and 4 descriptions
- writes through `GoogleAdsEditorExporter`
- validates through `shared/rebuild/staging_validator.py`

## Salvage Campaign Tools

The older campaign scripts remain reference material until individually migrated.

Known stale assumptions in the older tools:

- PMAX output
- Broad or Exact recommendations
- one-client examples
- UTF-8 CSV export paths
- API or upload-oriented language
- auto-fix or auto-generation behavior

## Inactive Compatibility Paths

- `campaign/campaign_plan.py`
- `campaign/run_campaign_plan.sh`

These paths fail clearly instead of generating stale output.

## Current Rule

Use the active Search builder for reusable campaign generation. Do not treat older scripts in this folder as workflow authority until a later cleanup loop promotes them with tests.
