# DRY Refactor Plan

Date: 2026-05-05

Workspace reviewed: `/Users/home/ai/agents/ppc/google_ads_agent`

## Sources

- Repo process: [docs/GOOGLE_ADS_AGENT_PROCESS.md](../GOOGLE_ADS_AGENT_PROCESS.md)
- Client scaffolding: [docs/CLIENT_DIRECTORY_SCAFFOLDING.md](../CLIENT_DIRECTORY_SCAFFOLDING.md)
- Source attribution and brand rules: [docs/SOURCE_ATTRIBUTION_AND_BRAND_RULES.md](../SOURCE_ATTRIBUTION_AND_BRAND_RULES.md)
- HTML and PDF standard: [docs/HTML_PDF_CLIENT_REPORT_STANDARD.md](../HTML_PDF_CLIENT_REPORT_STANDARD.md)
- Presentation developer guide: [presentations/docs/DEVELOPER_GUIDE.md](../../presentations/docs/DEVELOPER_GUIDE.md)
- Google Ads Editor CSV import: [Google Ads Help](https://support.google.com/google-ads/editor/answer/30564?hl=en)
- Google Ads Editor CSV columns: [Google Ads Help](https://support.google.com/google-ads/editor/answer/57747?hl=en)
- Google responsive search ads: [Google Ads Help](https://support.google.com/google-ads/answer/7684791?hl=en-EN)
- Google geo targets: [Google Ads API docs](https://developers.google.com/google-ads/api/data/geotargets)
- Google Ads EU political advertising status: [Google Ads API docs](https://developers.google.com/google-ads/api/reference/rpc/v21/EuPoliticalAdvertisingStatusEnum.EuPoliticalAdvertisingStatus)

## Current Preservation State

The first refactor gate is preservation, not cleanup. These branches were split from `origin/codex/no-blind-purge-guardrail` so the current dirty workspace does not need to remain the only copy of the work:

- `codex/copy-quality-description-validation-ready`
- `codex/match-type-policy-sidecars-ready`
- `codex/client-registry-foundation-ready`
- `codex/new-campaign-report-component-cleanup-ready`

The logo work remains separate in PR #47:

- [https://github.com/arc-web/google-ads-agent/pull/47](https://github.com/arc-web/google-ads-agent/pull/47)

Generated Emerson Morrison report and asset output was preserved in local safety stashes, not committed into shared system branches.

## Refactor Goal

Make the codebase easier to change by moving repeated policy, column, validation, report, and staging behavior into one source of truth per concern while preserving every accepted behavior that currently protects Google Ads Editor staging, source attribution, client-facing reports, and human review.

This is a DRY refactor, not a redesign. The operating rule is:

1. Keep canonical process behavior intact.
2. Replace duplicated logic with shared helpers.
3. Keep compatibility wrappers where people already run commands.
4. Delete or archive only after replacement and tests prove there is no unique behavior left.

## Refactor Boundaries

Do not change these behavioral contracts during the first DRY pass:

- Google Ads Editor remains the staging layer.
- Search builds stay phrase-first.
- Search partners stay disabled.
- Broad match stays blocked.
- Existing exact match can be reviewed only when source-proven through sidecars.
- New exact tests require explicit approval.
- Campaign rows must populate `EU political ads`.
- RSA output should target 15 headlines and 4 descriptions.
- Client-facing reports stay HTML-first and PDF-exported through the presentation tools.
- Client facts remain inputs or client-local artifacts, not hard-coded in `shared/`.

## Main Duplication Zones

### 1. Presentation Wrappers

Observed files:

- `presentations/tools/build_new_campaign_report.py`
- `presentations/tools/build_review_doc.py`
- `presentations/tools/report_quality_audit.py`
- `presentations/tools/pdf_visual_audit.py`
- Matching implementation files under `shared/presentation/`

Current pattern:

- Human-facing command wrappers insert the repo root into `sys.path`, then call `shared.presentation.*`.
- This pattern is valid as an operator surface, but the wrapper boilerplate is repeated.

Refactor:

- Add one shared wrapper bootstrap helper, for example `presentations/tools/_bootstrap.py`.
- Keep each human-facing command path stable.
- Replace repeated `sys.path.insert` blocks with one helper import.
- Add a test that every `presentations/tools/*.py` wrapper points to an implementation under `shared/presentation/` or a documented exception.

Do not remove the wrappers. They are the documented operator interface.

### 2. Search CSV Columns And Editor Rules

Observed files:

- `shared/gads/core/search_campaigns/search_csv_generator.py`
- `shared/gads/core/business_logic/google_ads_editor_exporter.py`
- `shared/rebuild/staging_validator.py`
- `shared/validators/search/search_*_validator.py`
- `shared/tools/campaign/search_campaign_builder.py`

Current pattern:

- Required Google Ads Editor fields, RSA field counts, status values, Search network policy, and match-type expectations appear in more than one place.
- Some validators are newer active gates, while some older validators remain useful compatibility or salvage surfaces.

Refactor:

- Create `shared/gads/core/search_campaigns/search_editor_schema.py`.
- Move shared constants there:
  - Search staging column order
  - Required headers
  - RSA headline and description fields
  - Default Search network value
  - Allowed statuses
  - Default EU political ads value
  - Default broad match setting
- Import those constants from the generator, exporter, and validators.
- Keep behavior tests at the highest active surface:
  - `SearchCSVGenerator`
  - `GoogleAdsEditorExporter`
  - `shared.rebuild.staging_validator`
  - `SearchKeywordValidator`

Only delete duplicated constants after the imports land and the tests pass.

### 3. Match-Type Policy

Observed files:

- `shared/rebuild/match_type_policy.py`
- `shared/rebuild/staging_validator.py`
- `shared/validators/search/search_keyword_validator.py`
- `shared/gads/core/search_campaigns/search_csv_generator.py`
- `shared/rebuild/account_pipeline.py`

Current pattern:

- The new sidecar policy is the right direction, but it is now used by multiple layers.
- Some old validator text still talks about active values independently from the policy helper.

Refactor:

- Treat `shared/rebuild/match_type_policy.py` as the only match-type decision engine.
- Keep validators responsible for row context, issue formatting, and counts.
- Keep the generator responsible for writing new phrase rows, not for deciding preservation.
- Add tests that prove the same row receives the same match-type decision from both validator surfaces.

Deletion candidates after replacement:

- Local `ALLOWED_CRITERION_TYPES` style sets in generators or validators when they duplicate the policy helper.
- Old exact or broad validation branches that no longer call `evaluate_match_type`.

### 4. Copy Quality And RSA Policy

Observed files:

- `shared/copy_engine/search/copy_matrix.py`
- `shared/copy_engine/search/headlines.py`
- `shared/copy_engine/search/descriptions.py`
- `shared/rebuild/rsa_headline_quality.py`
- `shared/rebuild/staging_validator.py`
- `shared/copy_engine/frameworks/ad_character_limits.yaml`

Current pattern:

- Copy generation, copy grading, RSA headline quality, and staging validation each enforce overlapping character and quality expectations.

Refactor:

- Make `ad_character_limits.yaml` the data source for RSA and asset copy limits.
- Add a small loader such as `shared/copy_engine/limits.py`.
- Use it in copy generation, RSA quality audit, and staging validation.
- Separate three concerns:
  - generation candidates
  - qualitative copy grading
  - hard Google Ads Editor validation

Deletion candidates after replacement:

- Hard-coded headline and description length values outside the limit loader.
- Repeated generic phrase lists once they are moved to one client-facing language policy module.

### 5. Client Registry And Scaffolding

Observed files:

- `shared/clients/client_registry.py`
- `shared/clients/supabase_client_registry.py`
- `shared/rebuild/scaffold_client.py`
- `clients/client_registry.csv`
- `clients/client_directory_gap_report.csv`
- `templates/client_template/`

Current pattern:

- The registry foundation adds inventory without replacing scaffolding.
- Directory layout rules live in docs, tests, templates, and registry code.

Refactor:

- Keep `templates/client_template/` as the scaffold source.
- Make `shared/clients/client_registry.py` the read-only inventory surface.
- Add a normalization decision record field for each client folder:
  - active
  - needs normalization
  - superseded
  - owner-approved archive
- Do not move legacy client folders automatically.

Deletion candidates after replacement:

- Ad hoc client directory scan code outside the registry module.
- Duplicated client layout assertions once they delegate to one registry/scaffold helper.

### 6. Creative Asset And Website Discovery

Observed files:

- `shared/creative_assets/build_creative_asset_package.py`
- `shared/gads/core/search_campaigns/search_asset_generator.py`
- `shared/tools/website/website_scanner.py`
- `presentations/docs/CREATIVE_ASSET_PACKAGE.md`

Current pattern:

- Website image discovery, asset eligibility, local package creation, report output, and Google Ads Editor staging notes are close together.
- This is useful for preservation, but harder to maintain as video and logo support grow.

Refactor:

- Split into modules by concern:
  - `discover.py` for website evidence collection.
  - `eligibility.py` for Google asset shape and size checks.
  - `package.py` for local file outputs.
  - `report.py` for approval HTML and CSV artifacts.
- Keep `build_creative_asset_package.py` as the CLI orchestrator.
- Keep source URLs as evidence, not as direct Editor import targets.

Deletion candidates after replacement:

- Inline image eligibility checks duplicated between the creative package and Search asset generator.
- Repeated asset manifest row shaping once a typed manifest helper exists.

## Safe Cleanup Rules

Every removal must be classified before it happens:

- `kept`
- `committed`
- `moved`
- `superseded`
- `archived`
- `generated-noise`
- `owner-approved purge`

Immediate cleanup allowed:

- `__pycache__/`
- `.pytest_cache/`
- `*.pyc`

Cleanup that needs inventory first:

- old generated client reports
- visual audit PNG folders
- old one-off scripts under `shared/tools/campaign/`
- salvage material under `shared/gads/tools/`
- planning documents that conflict with the current process

No blind reset of the main dirty workspace should happen until every unique source file, generated artifact, stash, and branch has a documented resolution.

## Execution Order

### Phase 0: PR Sequencing

1. Merge or close PR #47 first because it is the clean logo implementation.
2. Open the four preservation branches as separate PRs.
3. Resolve overlap before merging:
   - copy quality and match-type both touch `staging_validator.py`
   - match-type and copy quality both need `copy_matrix.py` or a follow-up merge branch
   - report cleanup is mostly independent
   - client registry is mostly independent

### Phase 1: Schema Extraction

1. Add `shared/gads/core/search_campaigns/search_editor_schema.py`.
2. Move shared Google Ads Editor Search constants.
3. Update generator, exporter, rebuild validator, and Search validators.
4. Run targeted Search tests.

### Phase 2: Validator Unification

1. Keep `shared/rebuild/staging_validator.py` as the active end-to-end Search CSV gate.
2. Keep `shared/validators/search/*` as row-level or compatibility validators.
3. Route match type through `match_type_policy.py`.
4. Route campaign, keyword, RSA, location, budget, and schedule checks through common helpers where possible.

### Phase 3: Presentation Bootstrap Cleanup

1. Add one wrapper bootstrap helper.
2. Replace repeated wrapper root insertion code.
3. Add a wrapper contract test.
4. Leave human-facing command names unchanged.

### Phase 4: Copy Limits And Language Policy

1. Add `shared/copy_engine/limits.py`.
2. Use YAML limits in copy generation, RSA audits, and staging validation.
3. Move repeated client-facing forbidden phrases into one module.
4. Run copy, validator, and report quality tests.

### Phase 5: Creative Asset Modularization

1. Split discovery, eligibility, packaging, and reporting into separate modules.
2. Keep the CLI and output contract unchanged.
3. Run creative asset tests and a fixture package build.

### Phase 6: Candidate Deletion Review

1. Generate a deletion inventory with path, owner, replacement, tests, and resolution.
2. Move conflicted planning docs to `docs/system_review/` when they are not active process.
3. Delete only generated noise automatically.
4. Require owner approval for purging any client data, branch, stash, or unique artifact.

## Test Gates

Minimum gate after each phase:

```bash
python3 -m pytest tests/test_staging_validator.py
python3 -m pytest tests/test_search_keyword_validator.py
python3 -m pytest tests/test_shared_gads_search_csv_generator.py
python3 -m pytest tests/test_new_campaign_report.py
python3 -m pytest tests/test_creative_asset_package.py
python3 -m pytest tests/test_client_registry.py tests/test_supabase_client_registry.py
```

Full gate before deletion or merge:

```bash
python3 -m pytest
python3 shared/rebuild/code_boundary_audit.py
python3 shared/rebuild/git_hygiene_audit.py
```

## First Implementation Recommendation

Start with Phase 1, schema extraction. It has the best risk-to-value ratio because it removes repeated Editor column and policy constants without changing campaign strategy, client output, or the human review workflow.

The second implementation should be Phase 3, wrapper bootstrap cleanup, because it is low risk and reduces repeated command-surface boilerplate while preserving the `presentations/tools/` commands documented for operators.
