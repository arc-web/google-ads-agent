# Google_Ads_Agent Master Instructions

This file is retained for compatibility with older scripts and docs. It no longer supersedes the repository process in `AGENTS.md`.

## Canonical Process

For Google Ads account rebuild work, follow the one-shot Google Ads Editor staging workflow:

- `docs/GOOGLE_ADS_AGENT_PROCESS.md`
- `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`

That workflow is the source of truth for audit, website scan, strategy, keyword expansion, RSA copy generation, targeting, validation, and human review. Client-specific folders are not process authorities.

## Non-Negotiable Rebuild Rules

- Google Ads Editor is the staging layer.
- Generated CSVs must be reviewed by a human before posting.
- Search rebuild keywords are phrase match only by default.
- Do not generate broad match.
- Do not generate exact match unless explicitly requested for a controlled test.
- Use plain keyword text with `Criterion Type` set to `Phrase`.
- Populate `EU political ads` on campaign rows.
- Use `Location ID` for location targets when available.
- Generate useful RSA copy, not one-word or bare-label headlines.
- Keep validation reports and human review files with every build.

## Communication Rules

- Never use em dashes.
- Always link to sources.
- When discussing platform requirements, cite Google documentation or the local process document.

## Reference Sources

- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en
- Google Ads Editor location import: https://support.google.com/google-ads/editor/answer/30573?hl=en
- Google responsive search ads: https://support.google.com/google-ads/answer/7684791?hl=en-EN
- Google geo targets: https://developers.google.com/google-ads/api/data/geotargets
- Google Ads EU political advertising status: https://developers.google.com/google-ads/api/reference/rpc/v21/EuPoliticalAdvertisingStatusEnum.EuPoliticalAdvertisingStatus
