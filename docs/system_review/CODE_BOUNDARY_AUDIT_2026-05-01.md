# Code Boundary Audit

Date: 2026-05-01

## Plain-English Finding

The concern is valid.

Some Python files are written around one client, one business type, or one local machine path. That is acceptable only inside `clients/` as a temporary run artifact or wrapper. It is not acceptable inside shared system code.

The problem did not start with the validator itself. The active validator in `shared/rebuild/staging_validator.py` is generic. The problem showed up when THLH client scripts were treated like normal workflow code and when the audit exposed older shared modules with hard-coded client assumptions.

## Boundary Rule

The repo rule is now:

- shared Python must not hard-code a client, agency, brand, absolute local path, or one-off campaign
- client-specific Python under `clients/` is allowed only as a run artifact, migration wrapper, or temporary workflow
- reusable behavior must be promoted into shared code before it becomes part of the agent system

This rule is now written into `AGENTS.md`.

## Audit Command

```bash
python3 shared/rebuild/code_boundary_audit.py \
  --json-output docs/system_review/code_boundary_audit_2026-05-01.json
```

Current result:

- status: `fail`
- scanned shared/tool Python files: 133
- findings: 182

The JSON evidence is here:

- `docs/system_review/code_boundary_audit_2026-05-01.json`

## Highest-Risk Shared Areas

These shared files have the most client-specific findings:

- `shared/gads/core/search_campaigns/search_csv_generator.py`
- `shared/tools/website/website_scanner.py`
- `shared/tools/campaign/campaign_plan.py`
- `shared/validators/search/text_ad_validator.py`
- `shared/copy_engine/orchestrator.py`
- `shared/comprehensive_csv_validator.py`
- `shared/gads/core/business_logic/client_onboarding_workflow.py`
- `shared/gads/tools/ad_extensions_examples.py`
- `shared/presentation/build_review_doc.py`
- `shared/run_csv_validation.py`
- `shared/tools/campaign/website_content_analyzer.py`

## What I Introduced That Needed Correction

I incorrectly added a generic validator test that depended directly on the THLH client artifact.

That is now corrected:

- `tests/test_staging_validator.py` uses generic synthetic fixtures only
- THLH artifact validation remains a client workflow check, not a shared validator unit test

## What Is Still Client-Specific By Design

These THLH Python files still exist under `clients/therappc/thinkhappylivehealthy/`:

- `analyze_keyword_variations.py`
- `analyze_search_location_reports.py`
- `generate_services_search_editor_csv.py`
- `apply_round1_core_focus_revisions.py`
- `rebuild_thhl_search_campaign.py`

They are not global system code.

Current role:

- client run artifacts
- evidence of what should be generalized
- wrappers around shared validation where already wired

They should not be copied as templates for other clients.

## Required Cleanup Process From Here

For each validator or script family:

1. Open a separate PR-sized batch.
2. Classify each Python file as active shared code, client artifact, compatibility wrapper, salvage reference, or stale draft.
3. Move reusable logic into shared code with client facts passed in as inputs.
4. Add or update tests before activation.
5. Run `python3 -m pytest`.
6. Run `python3 shared/rebuild/code_boundary_audit.py`.
7. Run any domain validator, such as `shared/rebuild/staging_validator.py`, against real outputs.
8. Commit only after the code, tests, docs, and generated evidence agree.

## PR Policy Going Forward

Use a separate PR for each validator or script-family cleanup.

Recommended PR sequence:

1. `shared/rebuild/staging_validator.py` and its tests.
2. `shared/validators/search/search_keyword_validator.py` salvage or replacement.
3. `shared/validators/search/search_campaign_validator.py` salvage or replacement.
4. `shared/validators/search/search_location_validator.py` salvage or replacement.
5. `shared/validators/search/search_text_ad_validator.py` salvage or replacement.
6. `shared/validators/account_validator.py` and orchestration cleanup.
7. Only then move to `shared/gads/` and `shared/tools/`.

This keeps each PR reviewable and prevents a large cleanup from hiding regressions.
