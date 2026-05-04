# Dirty Worktree Inventory

Date: 2026-05-05

Source workspace: `/Users/home/ai/agents/ppc/google_ads_agent`

Clean logo worktree: `/Users/home/ai/agents/ppc/google_ads_agent_logo_clean`

Logo PR: https://github.com/arc-web/google-ads-agent/pull/47

## Current Main Workspace State

Branch: `codex/search-asset-optimization-v2-logo`

Branch-local commits not in `origin/codex/no-blind-purge-guardrail`:

- `51d1875 Add client scaffold inventory and evidence`
- `34c75eb Update shared creative asset tooling`

Current dirty paths observed during cleanup:

- `AGENTS.md`
- `clients/client_directory_gap_report.csv`
- `clients/client_registry.csv`
- `docs/GOOGLE_ADS_AGENT_PROCESS.md`
- `docs/system_review/NEW_CAMPAIGN_REPORT_COMPONENT_MAP_2026-05-05.md`
- `shared/copy_engine/frameworks/ad_character_limits.yaml`
- `shared/copy_engine/search/copy_matrix.py`
- `shared/gads/core/search_campaigns/search_csv_generator.py`
- `shared/new_campaign/build_initial_search_campaign.py`
- `shared/presentation/build_new_campaign_report.py`
- `shared/presentation/report_quality_audit.py`
- `shared/rebuild/account_pipeline.py`
- `shared/rebuild/match_type_policy.py`
- `shared/rebuild/rsa_headline_quality.py`
- `shared/rebuild/staging_validator.py`
- `shared/validators/search/search_keyword_validator.py`
- `tests/test_new_campaign_report.py`
- `tests/test_staging_validator.py`

Ignored generated noise found:

- `.pytest_cache`
- `__pycache__/`
- `*.pyc`
- ignored `tasks/`

## Classification

### Leave Out Of Commits

- `AGENTS.md`: only a generated memory timestamp changed.
- `__pycache__/`, `.pytest_cache`, `*.pyc`: generated local test caches.

### Copy Quality And Validator Policy

Preserve in `codex/copy-quality-description-validation`:

- `shared/copy_engine/frameworks/ad_character_limits.yaml`
- `shared/copy_engine/search/copy_matrix.py`
- `shared/new_campaign/build_initial_search_campaign.py`
- `shared/rebuild/rsa_headline_quality.py`
- `shared/rebuild/staging_validator.py`
- `tests/test_staging_validator.py`

Related match-type validator work is coupled in the dirty validator files and should be preserved in a separate policy branch if split further.

### Match-Type Policy Preservation

Preserve in `codex/match-type-policy-sidecars`:

- `shared/rebuild/match_type_policy.py`
- `shared/rebuild/account_pipeline.py`
- `shared/rebuild/staging_validator.py`
- `shared/validators/search/search_keyword_validator.py`
- `shared/gads/core/search_campaigns/search_csv_generator.py`

Intent: keep new rebuilds phrase-first while allowing source-proven existing exact rows to be reviewed through sidecar artifacts.

### Client Registry Foundation

Preserve in `codex/client-registry-foundation`:

- `clients/client_directory_gap_report.csv`
- `clients/client_registry.csv`
- `shared/clients/`
- client registry tests
- client registry foundation docs

Intent: track client directory inventory without mixing it into asset or copy work.

### New Campaign Report Cleanup

Preserve in `codex/new-campaign-report-component-cleanup`:

- `docs/system_review/NEW_CAMPAIGN_REPORT_COMPONENT_MAP_2026-05-05.md`
- `shared/presentation/build_new_campaign_report.py`
- `shared/presentation/report_quality_audit.py`
- `tests/test_new_campaign_report.py`

Intent: keep internal service-logic cards out of client-facing ad-copy pages and tighten the campaign-structure page.

### Generated Client Build Evidence

Do not include in shared system PRs by default:

- `clients/arc/fdl_xibalba/build/2026-05-05_initial_search_build/`
- visual audit PNGs
- generated PDF and HTML outputs
- generated staged CSV files

If the client build must be preserved, create a separate client-specific evidence PR and document why it belongs in git.

## Cleanup Actions

1. Treat PR #47 as the clean business-logo implementation.
2. Preserve dirty source work by copying it into clean worktree branches.
3. Commit and push each clean branch independently.
4. Remove only generated cache noise from the main workspace.
5. Keep generated client build artifacts out of shared cleanup PRs unless explicitly approved.
6. After all preservation branches are pushed, the main dirty workspace can be reset only after explicit owner approval.

