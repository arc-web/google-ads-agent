# RSA Headline System Audit

Date: 2026-05-04

## Summary

The original EM Consulting staged CSV failed the new RSA headline quality audit across all 8 RSA rows. The failures were caused by the one-shot builder's old headline generator, which hard-sliced service-led headlines to 30 characters and then padded duplicate fallback headlines.

The repaired build now passes the shared RSA headline audit, staging validation, static HTML audit, and rendered PDF visual audit.

## Affected Paths

- `shared/new_campaign/build_initial_search_campaign.py`: replaced local headline slicing with the shared quality headline generator.
- `shared/rebuild/staging_validator.py`: now blocks duplicate, semantically repeated, broken, and low-value RSA headlines.
- `shared/presentation/build_new_campaign_report.py`: now blocks report/PDF export when headline quality fails.
- `shared/rebuild/rsa_headline_quality.py`: new shared audit and generation contract.

## Original Failure Patterns

- Broken truncation: `Help Fro`, `Appointm`, `Local Su`, `Next Ste`, `Integrated Behavioral Health C`.
- Exact duplicate headline sets: repeated service-only headlines in long-service ad groups.
- Semantic duplicate sets: many headlines repeated the same service root with only generic suffix changes.
- Missing validation coverage: the previous validator checked headline length but not broken words, repeated ideas, or filler patterns.

## Current EM Consulting Results

- Headline audit: pass.
- CSV validation: pass.
- Campaigns: 1.
- Ad groups: 8.
- Phrase keywords: 56.
- RSAs: 8.
- Negative phrase keywords: 3.
- PDF visual audit: pass, 17 rendered pages.

## Sources

- Google responsive search ads: https://support.google.com/google-ads/answer/7684791?hl=en-EN
- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
