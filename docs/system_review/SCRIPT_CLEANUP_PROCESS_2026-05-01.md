# Script Cleanup Process

Date: 2026-05-01

## Purpose

This is the repeatable process for cleaning up old scripts without deleting useful work too early.

The goal is to move faster with less human review after the pattern has been proven once.

## Process

### 1. Classify The Script

Label each script as one of:

- current active path
- compatibility wrapper for an old command
- salvage reference
- stale draft blocked by validation
- delete later only after replacement is tested and documented

Default rule:

- preserve the script until its useful behavior is migrated or proven obsolete

### 2. Identify The Active Contract

Before editing, name the contract the script must satisfy.

For Google Ads Editor staging scripts, the active contract is:

```bash
python3 shared/rebuild/staging_validator.py --csv PATH_TO_STAGING_CSV
```

The output must pass this validator before it is considered current.

For shared Python, the architecture boundary contract is:

```bash
python3 shared/rebuild/code_boundary_audit.py
```

Shared code should not hard-code one client, one agency, one brand, one local machine path, or one campaign.

### 3. Add An Operator Note

If a folder has confusing script names, add a short note in that folder explaining:

- which script is current
- which script is a compatibility path
- which output files are current
- which validator proves the output is acceptable

For THLH this note is:

- `clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/README.md`

### 4. Keep Client-Specific Logic Local

Client-specific decisions stay in the client script or client build folder.

Shared rules move into shared tools.

For THLH:

- local client revision decisions stay in `apply_round1_core_focus_revisions.py`
- the shared Google Ads Editor staging contract lives in `shared/rebuild/staging_validator.py`

Do not promote a client-specific Python file into the agent system until the reusable part has been extracted into shared code with client facts passed as inputs.

### 5. Wire The Shared Validator

After a script writes a staging CSV, run the shared validator.

If it fails:

- mark the script report as `fail`
- include the validator issues in the report
- do not pretend the script is current

If it passes:

- include the validator report in the generated JSON
- keep the generated CSV as reviewable staging output

### 6. Convert Old Entry Points Into Compatibility Wrappers

If an old script name is still referenced by notes or user memory, do not delete it immediately.

Instead:

- route it to the current generator
- preserve the old output filename if useful
- validate the compatibility output
- document that it is a compatibility wrapper

For THLH:

- `rebuild_thhl_search_campaign.py` now delegates to `generate_services_search_editor_csv.py`
- its legacy output `THHL_Search_Rebuild_Test_2026-04-28.csv` now passes the shared staging validator

### 7. Test Both Synthetic Rules And Real Artifacts

Use small tests for reusable rule behavior. Real client artifacts can be validated as workflow checks, but generic unit tests should not depend on one client folder.

Current validator tests:

```bash
python3 -m pytest
```

Expected result:

- 6 passed

### 8. Commit In Reviewable Batches

Use small commits:

- map roles before changing behavior
- add shared tool
- add tests
- wire one script area
- update generated evidence

This keeps cleanup reversible and easier to review.

## THLH Validator Status

The validator workflow is complete for the THLH staging scripts.

Completed:

- active validator exists in `shared/rebuild/staging_validator.py`
- validator is tested with synthetic rule cases
- validator is tested against real THLH REV1 output
- pytest is configured
- current REV1 script runs the validator
- older rebuild script is converted into a compatibility wrapper
- both THLH staging outputs pass the validator when run sequentially

Still useful later, but not blocking this validator phase:

- wire the shared validator into future non-THLH rebuild scripts as they are reviewed
- decide later which old `shared/validators/` files are duplicated after more scripts use the active validator
- add broader CI only when the repo has more active tests

## Shared GADS First Pass

The next cleanup area is `shared/gads/`.

First-pass lessons:

- do not activate the old `shared/gads/` generators just because they import
- classify the folder by role before rewriting code
- keep PMAX and API/MCP tooling salvage-only until explicitly activated
- make package imports safe before deeper analysis so optional dependencies do not block local tests
- treat old Search generators with one-account copy, Exact/Broad defaults, and 3-headline/2-description output as stale drafts until rewritten against the active staging validator

Current role review:

- `docs/system_review/SHARED_GADS_ROLE_REVIEW_2026-05-01.md`

## Shared GADS Search Generator Loop

First behavior cleanup:

- `shared/gads/core/search_campaigns/search_csv_generator.py`

Outcome:

- converted stale client-shaped generator code into a generic Search staging helper
- kept the import path and class name stable for compatibility
- retired the old `generate_campaign(...)` account-shaped path with a clear error
- made the helper write UTF-16 tab-separated output
- made the helper validate through `shared/rebuild/staging_validator.py`
- added synthetic tests with no client fixture dependency

Reusable lesson:

- when an old shared script contains business-specific strategy, do not try to generalize the strategy by guessing
- preserve useful mechanics, remove account-specific assumptions, and require callers to pass client facts explicitly
- if old behavior cannot be made safe without strategic choices, keep a compatibility surface that fails clearly instead of silently generating bad staging output

Earlier checks to add to future loops:

- scan target files for one-account names before editing
- scan for old Google Ads Editor column casing
- scan for Broad or Exact output paths
- scan for old 3-headline and 2-description ad output
- verify that any writer uses the active UTF-16 tab-separated artifact format
- confirm that the script delegates pass/fail authority to the active staging validator

## Shared GADS Editor Exporter Loop

Second behavior cleanup:

- `shared/gads/core/business_logic/google_ads_editor_exporter.py`

Outcome:

- narrowed the old universal exporter to active Search staging only
- preserved compatibility import names used by older scripts
- removed PMAX from the active export path
- removed silent auto-correction behavior from export
- made saved output UTF-16 tab-separated staging files
- made validation delegate to `shared/rebuild/staging_validator.py`
- added synthetic tests proving Search output passes and PMAX export remains inactive

Reusable lesson:

- exporters should not rewrite strategic ad content while exporting
- if content needs correction, that belongs in an explicit review or copy-generation step before export
- export code should create a file, validate it, and report issues without mutating the source strategy silently

Earlier checks to add to future loops:

- search for auto-correction methods before deciding a script is safe

## CSV Validation Authority Loop

Cleanup target:

- `shared/comprehensive_csv_validator.py`
- `shared/run_csv_validation.py`

Outcome:

- replaced the old mixed Search and PMAX comprehensive validator with a compatibility facade
- made the facade delegate to `shared.validators.MasterValidator`
- kept pass and fail authority centralized on `shared/rebuild/staging_validator.py`
- preserved the older module and CLI names for compatibility
- rejected `--fix`, `auto_fix=True`, and `--mark-final` instead of mutating CSVs or workflow state
- removed client-specific examples and old local path assumptions from the active runner
- added synthetic tests proving exact match still fails through the active staging validator
- added synthetic tests proving legacy auto-fix paths leave source CSV bytes unchanged

Reusable lesson:

- old validator entry points should be treated as compatibility surfaces, not independent rule engines
- validation can read, report, and fail, but it should not rewrite source staging artifacts
- stage changes, workflow feedback files, and campaign-builder feedback are separate workflow decisions, not validator authority

Earlier checks to add to future loops:

- search for `auto_fix`, `--fix`, and writer calls before trusting old validation scripts
- check CLI help examples for one-client names and old root path assumptions
- require wrappers to expose the active validator report so failures can be traced to the current staging contract

## Shared Scripts Quarantine Loop

Cleanup target:

- `shared/scripts/migrate_campaign_architecture.py`
- `shared/scripts/setup_mcp.sh`
- `shared/scripts/database/update-client-status.sql`
- tracked generated cache under `shared/scripts/__pycache__/`

Outcome:

- converted the architecture migration script into an audit-only compatibility command
- made legacy `--migrate` return a clear inactive-workflow error instead of creating directories or copying files
- converted MCP setup into an inactive notice that does not install packages, write credentials, edit config, or contact Google Ads
- converted the database status updater into a documentation-only SQL note with no executable statements
- removed the tracked Python cache file from the shared scripts folder
- added tests proving mutation modes are blocked and generated cache files are not tracked

Reusable lesson:

- setup, migration, and status scripts should default to inert audit behavior unless the current process explicitly activates them
- shell scripts are high risk because they can install tools, write credentials, and edit local app configuration outside the repo
- SQL files in shared folders can be dangerous even when they look like notes, so inactive SQL should contain comments only

Earlier checks to add to future loops:

- search scripts for `mkdir`, `curl`, `pip install`, `chmod`, `open(`, `write_text`, `shutil`, and SQL update statements
- run inactive scripts with their old mutation flags and assert they exit nonzero without creating files
- remove generated cache files from the touched script area as part of the same safety pass

## Workflow Instruction Alignment Loop

Cleanup target:

- `shared/google_ads_workflow.py`
- `shared/MASTER_AI_AGENT_INSTRUCTIONS.md`

Outcome:

- kept the legacy workflow entry point inactive
- made the wrapper point directly to the current scaffold and staging validation commands
- documented active contracts for campaign building, staging generation, export, validation, and reports
- made Search-first, phrase-only, Google Ads Editor staging, API-off boundaries explicit
- added human review stops for live mutation, PMAX activation, client data movement, match-type policy changes, and shared-code promotion
- added tests proving the legacy workflow wrapper and master instructions keep these contracts visible

Reusable lesson:

- instruction files need tests when they are part of the operating contract
- compatibility wrappers should say what to use now, not just say they are deprecated
- old master instruction files should defer to `AGENTS.md` and the canonical process while still blocking stale behavior

Earlier checks to add to future loops:

- scan instruction files for stale active verbs around API upload, PMAX, broad match, exact match, and auto-fix
- require old entry points to name the current command that replaced them
- test the visible operator message from disabled compatibility wrappers

## Copy Engine Search RSA Contract Loop

Cleanup target:

- `shared/copy_engine/context.py`
- `shared/copy_engine/editor/char_limit_enforcer.py`
- `shared/copy_engine/editor/reporter.py`
- `shared/copy_engine/search/headlines.py`
- `shared/copy_engine/orchestrator.py`

Outcome:

- removed client-specific defaults and comments from touched shared copy-engine paths
- made reporter output default to the repo root discovered from the module path instead of a local machine path
- made the orchestrator accept an injected copy client for offline tests
- changed Search headline generation to target 15 RSA headlines by default
- made generate mode request 15 headlines and 4 descriptions explicitly
- changed the build plan fallback from 12 headlines to the active 15 headline contract
- added an offline fake-client test proving copy generation can satisfy 15 headlines, 4 descriptions, and hard character limits

Reusable lesson:

- copy generation tests should not call external model providers
- shared copy paths can use client facts, but they must receive those facts as inputs
- report output paths should be repo-local or caller-provided, not hard-coded to one local machine

Earlier checks to add to future loops:

- scan copy code for one-client examples, local machine paths, and old 12-headline defaults
- test asset-count contracts with fake LLM clients before touching real client data
- keep model/provider credentials outside active unit tests

## Client Template Scaffold Loop

Cleanup target:

- `templates/client_template/`
- `shared/rebuild/scaffold_client.py`

Outcome:

- converted the campaign CSV template into a tab-separated active Search staging example
- added the full 15 RSA headline and 4 description columns to the template
- made the template use `Ad Group`, `Criterion Type: Phrase`, `Broad match keywords: Off`, and `EU political ads`
- added separate campaign, ad group, keyword, RSA, and location rows so the template passes the active staging validator
- made scaffold output materialize `*_template` files into active filenames such as `account_export.csv`
- added temp-directory scaffold tests so no real client folder is touched

Reusable lesson:

- client templates should be validated like generated artifacts, not treated as static documentation
- scaffolding tests should use temp directories and should prove existing client folders are protected from overwrite
- source templates can stay UTF-8 for placeholder replacement, but the active schema and validator contract must still match Google Ads Editor staging

Earlier checks to add to future loops:

- validate scaffolded template CSVs through `shared/rebuild/staging_validator.py`
- check template filenames match the README required first files
- keep template defaults Search-first, phrase-only, and API-off

## Client Test Candidate Review Loop

Cleanup target:

- `clients/` review only
- `docs/system_review/CLIENT_TEST_CANDIDATES_2026-05-01.md`

Outcome:

- selected THLH as the current Search staging dry-run candidate
- selected Sky Therapies as the simpler raw export candidate
- selected EvoRestore as the PMAX-heavy guard candidate
- documented why deferred clients stay available but are not first in line
- added tests proving the review covers the required categories and does not authorize moving, archiving, or deleting client data

Reusable lesson:

- client data review is not archive review
- choose test candidates by workflow coverage and evidence completeness
- PMAX-heavy clients are useful for guard testing, not PMAX activation

Earlier checks to add to future loops:

- separate active-path test candidates from guard-test candidates
- document why a client is deferred instead of silently ignoring it
- add explicit human stops before any client data movement
- check output encoding before preserving old save methods
- check whether a generic-looking exporter is quietly activating PMAX or API behavior
- preserve old import names only when the active behavior is explicit and tested

## Shared GADS Search Support Tools Loop

Third behavior cleanup:

- `shared/gads/tools/search_staging_support.py`

Outcome:

- added a small active helper for Search-safe support logic
- kept older keyword, ad group, extension, and planning tools salvage-only
- added phrase-only keyword plans
- added negative phrase plans without leading-minus notation
- added ad group plans that feed `GoogleAdsEditorExporter`
- added synthetic tests proving helper output validates through the active staging path

Reusable lesson:

- when a folder contains many stale tools, create one narrow active support surface instead of trying to clean every old script at once
- use old tools as a source of ideas, not as active behavior, until each assumption is tested
- make active helpers compose with the current generator and exporter so every new helper inherits the same validator contract

Earlier checks to add to future loops:

- inventory old tools for examples that teach useful concepts but contain inactive match types
- avoid importing legacy tools from the new active helper
- prove new support helpers can feed the active exporter and staging validator
- leave bulky salvage tools untouched until their behavior has a specific migration target

## Shared GADS API/MCP Salvage Loop

Fourth behavior cleanup:

- `shared/gads/core/google_ads_api_service.py`
- `shared/gads/core/gads_client_config.json`
- `shared/gads/integrations/README.md`
- `shared/gads/interface/README.md`

Outcome:

- kept API/MCP work salvage-only
- removed the hard-coded local parent MCP config path
- made the Google Ads API service importable without `google.ads`
- blocked live API and parent MCP calls with an explicit exception
- documented integrations and interface folders as inactive salvage
- added synthetic tests proving live operations cannot run accidentally

Reusable lesson:

- optional live-account dependencies must not block offline repo cleanup
- a future API activation phase should start by replacing the guard with tested read-only behavior before any mutation method is enabled
- config files should use environment placeholders instead of local machine paths

Earlier checks to add to future loops:

- scan for `mutate_` methods before treating an API file as reference-only
- scan config JSON for local filesystem paths
- test imports without optional external SDKs installed
- keep UI or integration folders inactive when they call guarded services

## Shared GADS PMAX Salvage Loop

Fifth behavior cleanup:

- `shared/gads/core/pmax_campaigns/pmax_csv_generator.py`
- `shared/gads/core/pmax_campaigns/__init__.py`

Outcome:

- kept PMAX imports stable
- preserved reference data containers for future review
- blocked PMAX CSV generation with an explicit inactive-workflow exception
- added tests proving PMAX cannot export through the active Search exporter
- added tests proving active Search staging still validates after PMAX guard changes

Reusable lesson:

- keeping salvage code does not mean letting it produce workflow artifacts
- inactive campaign types should fail clearly at the generation boundary
- activation requires a separate PR with new tests, docs, and user approval

Earlier checks to add to future loops:

- look for generators that can write files even when their workflow is not active
- keep import compatibility but block output when activation is not approved
- test that inactive workflow modules cannot leak into active Search staging

## Shared GADS Business Logic Loop

Sixth behavior cleanup:

- `shared/gads/core/business_logic/client_onboarding_workflow.py`
- `shared/gads/core/business_logic/README.md`

Outcome:

- documented the business-logic folder as active exporter plus salvage modules
- removed automatic account-shaped campaign generation from shared onboarding
- retired the old resume-campaign generation hook with a clear inactive message
- added tests proving onboarding no longer contains the account-shaped generator path

Reusable lesson:

- business-specific workflows should not run from shared onboarding
- shared onboarding should collect facts and mark campaign generation for manual review
- campaign generation belongs in the active staging workflow after client facts are reviewed

Earlier checks to add to future loops:

- search for business-specific names and service categories before promoting shared modules
- search for subprocess-based generator calls inside onboarding or automation modules
- treat asset, optimization, reporting, and policy modules as salvage until each gets its own active contract
- prefer explicit inactive hooks over hidden side effects

## Shared GADS Pass Summary

Completed loops:

- Search CSV generator
- Google Ads Editor exporter
- Search support tools
- API/MCP salvage quarantine
- PMAX salvage guard
- Business-logic salvage boundaries

Current active shared/gads surfaces:

- `shared/gads/core/search_campaigns/search_csv_generator.py`
- `shared/gads/core/business_logic/google_ads_editor_exporter.py`
- `shared/gads/tools/search_staging_support.py`

Current inactive salvage surfaces:

- old Search support tools
- API/MCP service and integrations
- PMAX generator
- business-logic modules other than the active exporter

## Shared Config Active Search Loop

Next subsystem after `shared/gads/`:

- `shared/config/`

Outcome:

- made shared campaign defaults Search-only for the active workflow
- removed one-client business defaults from shared config
- marked non-Search campaign types as salvage-only references
- made `ConfigLoader` reject inactive campaign types by default
- kept an explicit `allow_inactive_campaign_types=True` option for salvage review
- aligned generic ad limits with the active RSA contract of 15 headlines and 4 descriptions
- added tests covering loader behavior, generic business config, inactive campaign references, and ad limits

Reusable lesson:

- config files are behavior, not passive documentation
- stale defaults are as risky as stale code because they can silently shape future generated campaigns
- shared config should describe the active contract and require client facts to come from client folders

Earlier checks to add to future loops:

- scan configs for one-client service lists and brand defaults
- scan configs for non-active campaign type recommendations
- test loader defaults rather than only reading YAML by eye
- keep salvage access explicit so non-active configs cannot be loaded accidentally

## Shared Campaign Tools Search Builder Loop

Next subsystem after `shared/config/`:

- `shared/tools/campaign/`

Outcome:

- added `shared/tools/campaign/search_campaign_builder.py` as the active campaign-build helper
- made the active helper produce Search-only staging data
- required phrase keywords, 15 RSA headlines, and 4 descriptions
- routed output through `GoogleAdsEditorExporter` and the active staging validator
- retired `campaign_plan.py` and `run_campaign_plan.sh` as inactive compatibility paths
- documented older campaign tools as salvage-only until individually migrated
- added tests proving the active builder validates and stale keyword shapes are rejected

Reusable lesson:

- generation tools need active wrappers before old client-shaped scripts are mined for useful ideas
- executable legacy scripts should fail clearly rather than generate stale PMAX or client-specific artifacts
- campaign generation should validate immediately after writing staging output

Earlier checks to add to future loops:

- scan generator scripts for one-client examples before activating them
- block old shell runners that produce stale artifacts
- require active builders to produce validator-passing staging files in tests
