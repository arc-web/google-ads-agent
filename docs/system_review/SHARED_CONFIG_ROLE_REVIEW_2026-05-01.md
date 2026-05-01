# Shared Config Role Review

Date: 2026-05-01

## Plain-English Decision

`shared/config/` is active only for generic Search staging defaults.

It must not define one client, one industry, one agency, PMAX activation, or API upload as the shared default.

## Active Role

Active files:

- `shared/config/campaign_defaults.yaml`
- `shared/config/business_config.yaml`
- `shared/config/ad_limits.yaml`
- `shared/config/ad_character_limits.yaml`
- `shared/config/google_ads_config_loader.py`

Active contract:

- Search-first Google Ads Editor staging
- phrase-only keywords
- Broad match off
- 15 RSA headlines
- 4 RSA descriptions
- UTF-16 tab-separated staging output
- manual review before account changes

## Cleanup Completed

What changed:

- replaced one-client business config with generic placeholders
- removed business-specific service defaults from shared config
- rewrote campaign defaults so Search is the only active default
- marked PMAX and other non-Search campaign types as inactive reference material
- made `ConfigLoader` reject inactive campaign types by default
- added tests for loader behavior and active config boundaries

What stayed reference-only:

- PMAX limits
- non-Search campaign-type guidance
- character limits for formats outside active Search staging

## Next Review Target

The next subsystem should be chosen by fresh inventory.

Good candidates:

- `shared/tools/`
- `shared/scripts/`
- `shared/comprehensive_csv_validator.py`
- old non-active presentation compatibility paths

Selection rule:

- prioritize folders that can silently generate, mutate, or validate workflow artifacts
