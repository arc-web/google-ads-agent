# Dry-Run Account Build Test

Date: 2026-05-01

## Decision

The cleaned system is ready for the next account-build testing phase.

This dry run generated a Google Ads Editor staging file for the THLH Search candidate through the active Search campaign builder. The output passed the active staging validator, `MasterValidator`, and `SearchMasterValidator` with 0 issues.

## Candidate Used

Selected candidate:

- `clients/therappc/thinkhappylivehealthy/`

Reason:

- current Search staging evidence exists
- client build folder already contains taxonomy, copy planning, targeting evidence, and validation reports
- healthcare-sensitive Search copy gives the cleaned path a realistic compliance check
- this candidate does not require PMAX, API upload, or live account mutation

## Generated Evidence

Dry-run folder:

- [THLH Dry-Run Account Build](../../clients/therappc/thinkhappylivehealthy/build/dry_run_account_build_2026-05-01/README.md)

Generated files:

- `Google_Ads_Editor_Staging_DRY_RUN.csv`
- `validation_report.json`
- `staging_validator_report.json`
- `master_validator_report.json`
- `search_master_validator_report.json`

## Output Shape

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

## Validation

Commands:

```bash
python3 shared/rebuild/staging_validator.py \
  --csv clients/therappc/thinkhappylivehealthy/build/dry_run_account_build_2026-05-01/Google_Ads_Editor_Staging_DRY_RUN.csv \
  --json-output clients/therappc/thinkhappylivehealthy/build/dry_run_account_build_2026-05-01/staging_validator_report.json

python3 -m pytest

python3 -m compileall -q shared tests
```

Validator results:

- active staging validator: pass
- `MasterValidator`: PASS, 0 issues
- `SearchMasterValidator`: success, 0 issues

## Boundaries Confirmed

- API upload remained off.
- PMAX remained inactive.
- Search remained phrase-only.
- Broad match remained off.
- Exact match was not generated.
- No client data was moved, archived, deleted, or reclassified.
- Generated staging output remains review-only until a human approves launch.

## What This Proves

The cleaned active path can now:

1. Accept real client candidate facts.
2. Generate Search-only campaign staging rows.
3. Write Google Ads Editor-compatible UTF-16 output.
4. Preserve the phrase-only match policy.
5. Validate through the current staging authority.

## What Remains Next

The next phase should expand from this small dry run into a fuller one-shot rebuild test:

- more ad groups from the selected candidate taxonomy
- copy engine-generated RSA assets instead of manually selected dry-run copy
- human review file generation
- validation output packaged with the build
- optional presentation/report flow only after the staging build remains clean

## Sources

- [Client Test Candidates](CLIENT_TEST_CANDIDATES_2026-05-01.md)
- [Script Cleanup Process](SCRIPT_CLEANUP_PROCESS_2026-05-01.md)
- [Google Ads Agent Process](../GOOGLE_ADS_AGENT_PROCESS.md)
- [Google Ads Editor CSV Import](https://support.google.com/google-ads/editor/answer/30564)
- [Google Ads Editor CSV Columns](https://support.google.com/google-ads/editor/answer/57747)
