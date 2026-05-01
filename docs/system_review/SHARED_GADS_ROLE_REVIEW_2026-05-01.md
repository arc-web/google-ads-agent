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

### Active Generic Search Staging Helper

- `shared/gads/core/search_campaigns/search_csv_generator.py`

Role:

- generic helper for building Google Ads Editor Search staging TSVs
- writes active `Ad Group` and `Criterion Type` casing
- writes UTF-16 tab-separated output
- uses phrase-only keyword rows and negative phrase rows
- requires 15 RSA headlines and 4 RSA descriptions before writing ad rows
- validates written output with `shared/rebuild/staging_validator.py`

Compatibility decision:

- the old client-shaped `generate_campaign(...)` entry point now fails clearly instead of generating unsafe account-specific output
- older callers can still import `SearchCSVGenerator`, but must use the generic row-building methods

### Active Generic Search Exporter

- `shared/gads/core/business_logic/google_ads_editor_exporter.py`

Role:

- compatibility import path for older exporter references
- active only for Search staging output
- delegates row generation to `SearchCSVGenerator`
- writes UTF-16 tab-separated files through `save_csv(...)`
- validates exported files through `shared/rebuild/staging_validator.py`

Compatibility decision:

- Search export stays active when callers pass generic campaign, ad group, keyword, RSA, and location data
- PMAX, Display, Shopping, Video, and Discovery export fail clearly until those workflows are explicitly activated
- old content auto-correction behavior was removed because the current process should validate output, not silently rewrite source decisions

### Salvage For Search Editor Workflow

- keyword, ad group, and extension tools under `shared/gads/tools/`

Useful ideas:

- keyword and ad group organization
- extension planning
- Google Ads Editor export concepts

Do not activate yet because current findings show:

- old `Ad group` and `Criterion type` casing
- Exact and Broad match defaults
- old 3-headline and 2-description ad assumptions
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

## Search CSV Generator Cleanup Completed

`shared/gads/core/search_campaigns/search_csv_generator.py` has been rewritten from stale account-shaped salvage into a generic active staging helper.

What changed:

- removed old one-account copy, URL, geography, and keyword logic
- removed Broad and Exact output behavior from shared generation
- switched output to active Google Ads Editor staging columns
- added strict RSA asset requirements before ad rows are emitted
- added `write_and_validate(...)` so the generator proves its output through the active staging validator

What stayed out of scope:

- no API upload
- no PMAX activation
- no client-data deletion
- no business-specific campaign strategy moved into shared code

## Google Ads Editor Exporter Cleanup Completed

`shared/gads/core/business_logic/google_ads_editor_exporter.py` has been narrowed from a universal auto-correcting exporter into a Search-only staging exporter.

What changed:

- removed PMAX activation from the active exporter path
- removed silent text auto-correction during export
- removed UTF-8 BOM output in favor of UTF-16 tab-separated staging files
- preserved old import names for compatibility
- added validator-backed export and validation methods
- added synthetic tests proving Search output validates and PMAX remains inactive

What stayed out of scope:

- no API upload
- no PMAX generation
- no extension activation
- no client-specific campaign strategy moved into shared code

## Next Recommended Cleanup Batch

Continue with Search support tools under `shared/gads/tools/`.

Goal:

- classify keyword, ad group, ad extension, campaign planning, and reference tools as active helper, reference-only, salvage, or delete-later
- rewrite only reusable Search-safe pieces into active staging helpers
- keep PMAX, API upload, Broad, and Exact behavior inactive unless a later phase explicitly activates them

Do not edit PMAX or API tools in the same PR.
