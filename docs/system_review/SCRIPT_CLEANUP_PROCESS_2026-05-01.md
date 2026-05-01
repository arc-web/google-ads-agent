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
