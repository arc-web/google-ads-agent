# Shared GADS Business Logic

Most modules in this folder are salvage material.

## Active Files

- `google_ads_editor_exporter.py`

Active role:

- Search-only Google Ads Editor staging export
- UTF-16 tab-separated output
- validation through `shared/rebuild/staging_validator.py`
- PMAX and live API behavior blocked

## Salvage Files

The remaining modules contain useful ideas for later review:

- asset generation
- asset rules
- client audit and compliance
- client auth and isolation
- client context
- onboarding
- optimization
- reporting
- industry modifiers
- policy checks
- price assets

They are not active workflow authority yet.

## Current Safety Rules

- Shared onboarding must not auto-generate campaigns for one business type.
- Shared modules must not run live API mutations.
- Shared modules must not create client-specific defaults.
- Shared modules must not override the active Search phrase-only staging contract.
- Useful business-specific examples should move to docs or fixtures only when a later loop needs them.

## Activation Rule

Promote one module at a time. Each promotion needs:

- a clear active contract
- synthetic tests with no client fixture dependency
- validation through the active staging validator when output is a staging artifact
- documentation in `docs/system_review/`
