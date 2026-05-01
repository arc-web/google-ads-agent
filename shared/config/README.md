# Shared Configuration

This folder contains generic configuration for the active Google Ads Agent workflow.

## Active Role

The active workflow is Search-first Google Ads Editor staging.

Active configuration:

- `campaign_defaults.yaml`
- `business_config.yaml`
- `ad_limits.yaml`
- `ad_character_limits.yaml`
- `google_ads_config_loader.py`

The active config defaults must support:

- Search campaigns
- phrase-only keyword staging
- `Broad match keywords: Off`
- 15 RSA headlines
- 4 RSA descriptions
- UTF-16 tab-separated staging output
- manual human review before account changes

## Inactive Reference

PMAX, Display, Shopping, Video, App, Discovery, Local Services, API upload, and account mutation are not active defaults.

If a config mentions those areas, it is reference-only until a focused activation loop adds tests and updates the active process docs.

## Client Facts

Client names, services, brand terms, target audiences, business type, compliance facts, and campaign strategy belong under:

```text
clients/{agency}/{client}/
```

Do not put one client or one industry as the shared default.

## Loader Contract

By default, `ConfigLoader` returns active Search config only. It raises for inactive campaign types unless initialized with:

```python
ConfigLoader(allow_inactive_campaign_types=True)
```

That flag is for salvage review only. It does not activate non-Search workflows.

## Validation Contract

Generated staging artifacts must still pass:

```bash
python3 shared/rebuild/staging_validator.py --csv PATH_TO_STAGING_CSV
```
