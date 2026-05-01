# Shared GADS Role Review

Date: 2026-05-01

## Plain-English Decision

Keep `shared/gads/`.

Do not archive it.

Do not treat it as the active Google Ads Agent workflow yet.

This folder contains useful API, PMAX, reference, and campaign-planning ideas, but it still mixes old assumptions with the current Search-first Google Ads Editor staging process. The current active contract remains:

```bash
python3 shared/rebuild/staging_validator.py --csv PATH_TO_STAGING_CSV
```

## Current Role Map

### Active Reference For Now

- `shared/gads/tools/google_ads_reference_tool.py`
- related reference READMEs under `shared/gads/tools/`

Role:

- useful reference material for Google Ads concepts
- not a pass/fail authority for generated rebuilds

### Salvage For Search Editor Workflow

- `shared/gads/core/search_campaigns/search_csv_generator.py`
- `shared/gads/core/business_logic/google_ads_editor_exporter.py`
- keyword, ad group, and extension tools under `shared/gads/tools/`

Useful ideas:

- CSV generation structure
- keyword and ad group organization
- extension planning
- Google Ads Editor export concepts

Do not activate yet because current findings show:

- old `Ad group` and `Criterion type` casing
- Exact and Broad match defaults
- old 3-headline and 2-description ad assumptions
- one-client Wright Impact Windows copy and URL logic
- UTF-8-only writer paths in places where active artifacts are UTF-16 tab-separated files

### Salvage Only Until A PMAX Phase

- `shared/gads/core/pmax_campaigns/`
- PMAX examples and PMAX branches in shared tools

Role:

- reference only
- not active for Search rebuild generation

Reason:

- the current agent process is Search-first and phrase-only by default
- PMAX behavior needs a separate activation phase with its own tests and user approval

### API And MCP Salvage

- `shared/gads/core/google_ads_api_service.py`
- `shared/gads/core/gads_client_config.json`
- `shared/gads/integrations/`
- `shared/gads/interface/`

Role:

- future API/MCP reference
- not active staging workflow code

Risks found:

- hard-coded local parent MCP paths
- optional `google.ads` dependency should not break offline repo tooling
- config examples include external service assumptions

## First Cleanup Batch Completed

The package imports were made salvage-safe:

- `shared.gads.core` no longer eagerly imports `google.ads`
- `shared.gads.core.search_campaigns` no longer imports missing builder or validator modules
- `shared.gads.core.pmax_campaigns` no longer imports missing builder or validator modules

This does not activate the old generators. It only makes the folder safe to inspect and test as salvage material.

## Next Recommended Cleanup Batch

Start with `shared/gads/core/search_campaigns/search_csv_generator.py`.

Goal:

- convert it from Wright-specific, Exact/Broad, old text-ad output into either:
  - a compatibility wrapper that clearly points to the active staging workflow, or
  - a generic Search CSV generator that writes active Google Ads Editor staging format and passes `shared/rebuild/staging_validator.py`

Do not edit PMAX or API tools in the same PR.
