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
- treat old Search generators with Wright-specific copy, Exact/Broad defaults, and 3-headline/2-description output as stale drafts until rewritten against the active staging validator

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
