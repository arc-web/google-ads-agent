# Repo Rescaffold Proposal

Status: DRAFT - awaiting senior team review
Date: 2026-04-28
Author: agent
Audience: senior team

## Problem

Current top-level layout uses generic developer-shorthand names. Hard to invoke. Hard to read. Pipeline stages live under `shared/` but are not named to match the stages. Client-facing reviewers and ops people open the repo and cannot tell where things are.

Today:

```
google_ads_agent/
├── AGENTS.md
├── clients/
├── docs/                           ← what is "docs"? process? user manual? api?
├── legacy_archive/                 ← long, awkward
├── shared/                         ← what is "shared"? everything is shared
│   ├── copy_engine/
│   │   └── editor/                 ← editor of what? the copy_engine?
│   │       ├── grader.py
│   │       ├── char_limit_enforcer.py
│   │       └── reporter.py
│   ├── presentation/               ← does not match the stage name "review document"
│   ├── rebuild/
│   ├── scripts/
│   ├── tools/
│   ├── utils/
│   └── validators/
└── templates/
```

Issues:

1. `docs/` and `shared/` are catch-all names. Future contributors do not know what belongs where.
2. Pipeline has 15 stages. Code is buried under `shared/` with names that do not match the stages. To find the copy grader you have to know it lives at `shared/copy_engine/editor/grader.py`.
3. `editor/` inside `copy_engine/` is meaningless - everything in copy_engine edits copy.
4. Module imports are long: `from shared.copy_engine.editor.char_limit_enforcer import ...`. Every keystroke costs.
5. CLI invocation is awkward: `python3 -m shared.presentation.build_review_doc`. A user looking for the review-doc tool will not guess that path.
6. `legacy_archive/` should be `archive/` or `_archive/` - consistent with common conventions.

## Proposed Layout

Stage-aligned, invocation-friendly, top-level reads like a table of contents.

```
google_ads_agent/
├── README.md
├── AGENTS.md                          (kept - canonical agent instructions)
├── playbook/                          (was docs/)
│   ├── PROCESS.md                     (was GOOGLE_ADS_AGENT_PROCESS.md)
│   ├── CLIENT_DIRECTORY.md            (was CLIENT_DIRECTORY_SCAFFOLDING.md)
│   ├── ONBOARDING.md
│   └── SOURCE_ATTRIBUTION.md
├── agent/                             (was shared/, renamed for invocation clarity)
│   ├── audit/                         stage 1, 2 - account + performance ingestion
│   ├── site_scan/                     stage 3 - website crawl
│   ├── strategy/                      stage 6 - service, geo, copy strategy
│   ├── keywords/                      stage 7 - phrase keyword matrix
│   ├── copy/                          stage 8 - RSA generation + grading + char limits
│   │   ├── grader.py                  (was copy_engine/editor/grader.py)
│   │   ├── char_limits.py             (was copy_engine/editor/char_limit_enforcer.py)
│   │   ├── headlines.py               (was copy_engine/search/headlines.py)
│   │   ├── descriptions.py            (was copy_engine/search/descriptions.py)
│   │   ├── extensions.py              (was copy_engine/search/extensions.py)
│   │   ├── orchestrator.py
│   │   ├── models.py
│   │   └── policy.py                  (was copy_engine/editor/evaluator.py)
│   ├── targeting/                     stage 9 - geo, radius, bids
│   ├── csv_build/                     stage 11 - assemble Google Ads Editor CSV
│   ├── review_doc/                    stage 12 - client-facing review HTML+PDF
│   │   ├── build.py                   (was presentation/build_review_doc.py)
│   │   ├── page_break_rules.css       (canonical)
│   │   ├── section_header.css         (canonical)
│   │   └── LESSONS_TO_TOOLS.md
│   ├── revisions/                     stage 13, 14 - feedback classification + regen
│   ├── validate/                      stage 10 - validation gates
│   └── handoff/                       stage 15 - human review file + launch readiness
├── clients/                           (unchanged - client work)
├── new_client/                        (was templates/, named for action)
│   ├── client_template/
│   └── scaffold.py                    (was shared/rebuild/scaffold_client.py)
└── archive/                           (was legacy_archive/)
```

## Naming Principles

1. Top-level dirs are nouns the user already knows: `playbook`, `agent`, `clients`, `new_client`, `archive`.
2. Subdirs under `agent/` are pipeline stage names. One stage = one directory.
3. No `editor/`, `tools/`, `utils/`, `scripts/`, `shared/`. These tell you nothing.
4. Module filenames are short. `char_limits.py`, not `char_limit_enforcer.py`. `policy.py`, not `evaluator.py`.
5. CLI invocation matches the stage: `python3 -m agent.review_doc.build`, `python3 -m agent.copy.grader`, `python3 -m agent.csv_build.assemble`.

## Mapping Table

| Old path | New path |
|----------|----------|
| `docs/` | `playbook/` |
| `docs/GOOGLE_ADS_AGENT_PROCESS.md` | `playbook/PROCESS.md` |
| `docs/CLIENT_DIRECTORY_SCAFFOLDING.md` | `playbook/CLIENT_DIRECTORY.md` |
| `shared/` | `agent/` |
| `shared/copy_engine/` | `agent/copy/` |
| `shared/copy_engine/editor/grader.py` | `agent/copy/grader.py` |
| `shared/copy_engine/editor/char_limit_enforcer.py` | `agent/copy/char_limits.py` |
| `shared/copy_engine/editor/evaluator.py` | `agent/copy/policy.py` |
| `shared/copy_engine/editor/reporter.py` | `agent/review_doc/copy_section.py` |
| `shared/copy_engine/search/headlines.py` | `agent/copy/headlines.py` |
| `shared/copy_engine/orchestrator.py` | `agent/copy/orchestrator.py` |
| `shared/presentation/` | `agent/review_doc/` |
| `shared/presentation/build_review_doc.py` | `agent/review_doc/build.py` |
| `shared/presentation/page_break_rules.css` | `agent/review_doc/page_break_rules.css` |
| `shared/presentation/section_header.css` | `agent/review_doc/section_header.css` |
| `shared/presentation/LESSONS_TO_TOOLS.md` | `agent/review_doc/LESSONS_TO_TOOLS.md` |
| `shared/rebuild/scaffold_client.py` | `new_client/scaffold.py` |
| `shared/comprehensive_csv_validator.py` | `agent/validate/csv.py` |
| `shared/run_csv_validation.py` | `agent/validate/run.py` |
| `shared/validators/` | `agent/validate/` |
| `shared/google_ads_workflow.py` | DELETE (already a deprecated stub) |
| `shared/MASTER_AI_AGENT_INSTRUCTIONS.md` | merge into `AGENTS.md` at root |
| `shared/scripts/` | move to `agent/{matching_stage}/` per script |
| `shared/tools/` | move to `agent/{matching_stage}/` per tool |
| `shared/utils/` | `agent/_lib/` (only true cross-stage helpers) |
| `templates/` | `new_client/` |
| `templates/client_template/` | `new_client/client_template/` |
| `legacy_archive/` | `archive/` |

## Pipeline to Directory Alignment

After rescaffold, every stage in `playbook/PROCESS.md` maps to one `agent/` subdirectory. Reading the process doc tells you exactly where the code lives.

```
Stage  1  Ingest Account Export        →  agent/audit/
Stage  2  Ingest Performance Reports   →  agent/audit/
Stage  3  Scan Website                 →  agent/site_scan/
Stage  4  Source Attribution Normalize →  agent/audit/source_attribution.py
Stage  5  Build Strategy               →  agent/strategy/
Stage  6  Build Keyword System         →  agent/keywords/
Stage  7  Build RSA Copy System        →  agent/copy/
Stage  8  Build Targeting              →  agent/targeting/
Stage  9  Validate                     →  agent/validate/
Stage 10  Assemble Google Ads CSV      →  agent/csv_build/
Stage 11  Generate Client Review Doc   →  agent/review_doc/
Stage 12  Classify Client Revisions    →  agent/revisions/
Stage 13  Regenerate Approved Revisions→  agent/revisions/
Stage 14  Hand Off to Launch Readiness →  agent/handoff/
```

Note - stage numbering above is illustrative. Final numbers come from the process doc after rescaffold.

## Migration Plan

Two-pass migration. Each pass is a single PR.

### Pass 1 - Move and Rename

1. `git mv docs playbook`
2. `git mv shared agent`
3. `git mv templates new_client`
4. `git mv legacy_archive archive`
5. Inside `agent/copy/` flatten the `editor/` and `search/` subdirs.
6. Rename `char_limit_enforcer.py` → `char_limits.py`, `evaluator.py` → `policy.py`, `build_review_doc.py` → `build.py`, etc per mapping table.
7. Update every Python import to match.
8. Run all tests. Run `agent/review_doc/build.py` against the THHL HTML to confirm PDF still exports.

### Pass 2 - Process Doc + Cross-References

1. Update `playbook/PROCESS.md` to reference new paths.
2. Update `AGENTS.md` to point to `playbook/PROCESS.md`.
3. Merge `agent/MASTER_AI_AGENT_INSTRUCTIONS.md` into root `AGENTS.md`.
4. Update `clients/therappc/thinkhappylivehealthy/docs/hitl_doc_design_postmortem_2026-04-28.md` references.
5. Add a `playbook/REPO_LAYOUT.md` describing the new structure for future onboarders.

### Pass 3 - DELETE the rescaffold proposal

Delete `REPO_RESCAFFOLD_PROPOSAL.md` once rescaffold is complete. The proposal is not a permanent doc - it is a one-time RFC.

## Risks

1. Any external doc, README, or session memory that references `shared/...` paths will break. Mitigate with a `git grep -l "shared/"` sweep after migration.
2. Active client builds in `clients/{agency}/{client}/build/{date}_account_rebuild/` are unaffected - they only contain output files, no Python imports.
3. Memory entries from prior sessions reference old paths. They will become stale. Add a note in `AGENTS.md` that pre-2026-04-28 memory entries use the old layout.
4. `shared/copy_engine/orchestrator.py` is imported by code outside `shared/`. Need a full grep before pass 1.
5. PyPI-style packaging (`pyproject.toml` if present) will need its package paths updated.

## Open Decisions for Senior Review

1. `agent/` vs `pipeline/` vs `engine/` - all candidates. Picked `agent/` because the repo is `google_ads_agent` and every subdir is something the agent does.
2. Should `playbook/` instead be `process/`? Argument for `process/` - matches the doc title. Argument for `playbook/` - matches the user-facing nature of the docs (this is what we hand to ops people).
3. Inside `agent/copy/`, do we keep `orchestrator.py` or rename to `pipeline.py`? Pipeline is clearer.
4. Do we keep `archive/` or use `_archive/` (leading underscore = "ignore me" convention)? Lean toward `archive/` - leading underscore implies private/internal in Python and confuses ops.
5. Do `agent/audit/` stages 1, 2, 4 need separate subdirs (`audit/account/`, `audit/performance/`, `audit/source_attribution/`) or stay as flat modules inside `audit/`? Flat is simpler. Subdirs only if a stage has 3+ files.
6. CLI entry point - currently `python3 -m shared.presentation.build_review_doc`. After rescaffold, do we add a single top-level `gads` command (e.g. `gads review-doc`, `gads grade`, `gads scaffold`) and route to stage modules? Big quality-of-life win for ops people. Separate proposal if accepted.

## Decision Required

Approve, reject, or request changes. If approved, agent will execute pass 1 in a single commit and request review before pass 2.
