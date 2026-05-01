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

### Active Search Support Helper

- `shared/gads/tools/search_staging_support.py`

Role:

- generic Search-safe support helpers for ad group and keyword planning
- phrase-only keyword defaults
- negative phrase helper without leading-minus keyword notation
- exporter-compatible output dictionaries
- no API upload, PMAX, Broad, Exact, or client-specific behavior

Compatibility decision:

- older keyword, ad group, extension, and campaign-planning tools under `shared/gads/tools/` stay salvage-only until their useful behavior is migrated into tested helpers
- the active helper is intentionally small so it can be used by future cleanup loops without inheriting stale assumptions

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
- `PMAXCSVGenerator` keeps the import path stable but blocks CSV output

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

Safety decision:

- `GoogleAdsAPIService` imports offline without requiring `google.ads`
- live API methods raise `LiveGoogleAdsAutomationDisabled`
- parent MCP calls raise `LiveGoogleAdsAutomationDisabled`
- `gads_client_config.json` no longer points to a local parent-machine path
- integrations and interface folders are documented as salvage-only
- no live account mutation is active

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

## Search Support Tools Cleanup Completed

`shared/gads/tools/search_staging_support.py` has been added as the active Search-safe support surface for this folder.

What changed:

- added phrase-only keyword planning helpers
- added negative phrase planning without old leading-minus notation
- added generic ad group planning that feeds `GoogleAdsEditorExporter`
- added synthetic tests proving the helper exports through the active staging validator

What stayed salvage-only:

- old keyword management system
- old ad group management system
- old extension management system
- old campaign planning with reference tool
- PMAX examples and PMAX branches
- API/MCP dependencies and upload concepts

Reason:

- these older tools contain useful ideas, but still mix Broad, Exact, PMAX, API automation, auto-optimization, and account-shaped examples
- they should be mined in later focused loops rather than activated as-is

## API/MCP Salvage Quarantine Completed

API and MCP behavior has been made safe for local cleanup work without activating live account operations.

What changed:

- replaced the old live API service with an offline-safe salvage facade
- preserved the `GoogleAdsAPIService` import path
- blocked live budget, campaign, asset group, ad group, keyword, RSA, account-read, and parent MCP methods
- removed the hard-coded local parent MCP config path from `gads_client_config.json`
- documented integrations and interface folders as salvage-only
- added tests proving the API service imports offline and blocks live calls

What stayed out of scope:

- no Google Ads API upload
- no parent MCP execution
- no Streamlit interface activation
- no Airtable or GitHub integration activation

## PMAX Salvage Guard Completed

PMAX remains preserved but inactive.

What changed:

- kept `shared.gads.core.pmax_campaigns.PMAXCSVGenerator` importable
- converted PMAX CSV generation into an explicit inactive guard
- allowed PMAX reference data to be recorded for later review
- added tests proving PMAX cannot export through the active Search exporter
- added tests proving active Search staging still validates after the PMAX guard

What stayed out of scope:

- no PMAX activation
- no PMAX CSV output
- no asset generation
- no API upload

## Business Logic Salvage Boundaries Completed

Business-logic modules have been classified and one clear shared-code defect was removed.

What changed:

- added `shared/gads/core/business_logic/README.md`
- documented `google_ads_editor_exporter.py` as the only active business-logic module in this folder
- documented remaining business-logic modules as salvage until individually promoted
- removed automatic account-shaped campaign generation from onboarding
- retired the old resume-campaign generation hook with a clear inactive message
- added tests proving onboarding no longer contains account-shaped campaign generation

What stayed salvage-only:

- asset generation
- asset rules
- client audit and compliance
- client auth and isolation
- client context
- optimization
- reporting
- industry modifiers
- policy checks
- price assets

Reason:

- these modules contain useful ideas, but they still need focused review before becoming workflow authority
- shared business logic must not auto-create client campaigns before the active staging process has reviewed client facts

## Next Recommended Cleanup Batch

The planned `shared/gads/` pass is complete.

Recommended next repo loop:

- re-run a fresh inventory of `shared/gads/`
- decide whether to continue salvage promotion module-by-module or move to another subsystem
- keep using one PR per behavior group

Do not activate live API, PMAX, or client-specific shared defaults without a new explicit activation plan.
