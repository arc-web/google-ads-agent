# Dry-Run Account Build

Date: 2026-05-01

## Purpose

This folder proves the cleaned Search build path can generate a Google Ads Editor staging artifact for a selected client test candidate without using API upload or live account mutation.

Selected test candidate:

- `clients/therappc/thinkhappylivehealthy/`

Why this candidate:

- it has current Search staging evidence
- it has service taxonomy, RSA copy planning, targeting evidence, and prior validation reports
- it exercises healthcare-sensitive Search copy while keeping the active workflow phrase-only and staging-first

## Generated Files

- `Google_Ads_Editor_Staging_DRY_RUN.csv`
- `validation_report.json`
- `staging_validator_report.json`
- `master_validator_report.json`
- `search_master_validator_report.json`

## Result

The dry-run staging artifact passed:

- active staging validator: pass
- `MasterValidator`: PASS, 0 issues
- `SearchMasterValidator`: success, 0 issues

Artifact shape:

- campaign rows: 1
- location rows: 2
- ad group rows: 2
- keyword rows: 4
- RSA rows: 2
- encoding: UTF-16
- keyword criterion types: Phrase only
- Broad match keywords: Off
- location IDs present where available
- API upload fields: none

## Boundaries

- no API upload was run
- no live Google Ads account mutation was run
- no client data was moved, archived, deleted, or reclassified
- this is staging evidence only and still requires human review before any launch action

## Sources

- [Client Test Candidates](../../../../docs/system_review/CLIENT_TEST_CANDIDATES_2026-05-01.md)
- [Google Ads Agent Process](../../../../docs/GOOGLE_ADS_AGENT_PROCESS.md)
- [Google Ads Editor CSV Import](https://support.google.com/google-ads/editor/answer/30564)
- [Google Ads Editor CSV Columns](https://support.google.com/google-ads/editor/answer/57747)
