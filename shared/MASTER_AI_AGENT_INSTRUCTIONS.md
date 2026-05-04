# Google_Ads_Agent Master Instructions

This file is retained for compatibility with older scripts and docs. It no longer supersedes the repository process in `AGENTS.md`.

## Canonical Process

For Google Ads account rebuild work, follow the one-shot Google Ads Editor staging workflow:

- `docs/GOOGLE_ADS_AGENT_PROCESS.md`
- `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`

That workflow is the source of truth for audit, website scan, strategy, keyword expansion, RSA copy generation, targeting, validation, and human review. Client-specific folders are not process authorities.

## Active Contracts

- Client scaffolding: `python3 shared/rebuild/scaffold_client.py --agency AGENCY --client CLIENT`
- Campaign structure helper: `shared/tools/campaign/search_campaign_builder.py`
- Search staging generator: `shared/gads/core/search_campaigns/search_csv_generator.py`
- Google Ads Editor exporter: `shared/gads/core/business_logic/google_ads_editor_exporter.py`
- Validation authority: `python3 shared/rebuild/staging_validator.py --csv PATH_TO_STAGING_CSV`
- Legacy validator wrappers: `shared/comprehensive_csv_validator.py` and `shared/run_csv_validation.py`
- Human-facing report commands: `presentations/tools/`

Compatibility wrappers may keep old command names alive, but they must delegate to these active contracts or fail clearly. They must not silently generate PMAX, broad match, exact match, live upload, source CSV mutation, or client-specific shared defaults.

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
- Generate 15 RSA headlines and 4 descriptions when possible.
- Keep validation reports and human review files with every build.
- Keep Google Ads API upload off unless the user explicitly activates live automation.
- Keep PMAX, API/MCP, and external database scripts salvage-only until explicitly activated.
- Validation reads and reports. It must not auto-fix or rewrite source staging CSVs.
- Never purge, drop, archive, delete, or discard files, folders, stashes, branches, or artifacts blindly. Every removal needs a documented logical resolution.
- Client data, source inputs, reports, stashes, and generated artifacts must be preserved until an inventory confirms their resolution.

## Human Review Stops

Stop for explicit human approval before:

- activating Google Ads API upload or any live account mutation
- activating PMAX as part of the current workflow
- deleting, archiving, or moving client data
- dropping safety branches or stashes after cleanup inventory
- changing the default Search policy away from phrase-only
- promoting client-specific strategy into shared code
- choosing between two valid business strategies that current docs and tests cannot resolve

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
