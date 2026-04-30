# Repo Content Audit, 2026-04-30

This is a plain-English map of what is active, what is historical, and what should happen next before committing the repo cleanup.

## Short Answer

The repo is not just a code repo. It is becoming a working memory system for `Google_Ads_Agent`.

Keep:

- Active process docs.
- Active client folders.
- Client source files, reports, builds, review artifacts, and revision logs.
- Tooling that directly supports the current rebuild path.
- Older tools that may be merged later, but only after review.

Do not treat the old archive as permanent storage. The archive should become a temporary review area. After useful ideas and evidence are either moved into active client folders or merged into active tooling, purge archive contents and leave one markdown record explaining what used to be there and why it was removed.

## Current Active System

These files define the current agent:

- `AGENTS.md`
- `README.md`
- `docs/GOOGLE_ADS_AGENT_PROCESS.md`
- `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`
- `docs/SOURCE_ATTRIBUTION_AND_BRAND_RULES.md`
- `docs/ONBOARDING_INGESTION_AND_REVISION_WORKFLOW.md`
- `docs/HTML_PDF_CLIENT_REPORT_STANDARD.md`
- `docs/AI_REASONING_GATES.md`
- `docs/CLIENT_FACING_LANGUAGE_RULES.md`
- `presentations/docs/BUILD_INSTRUCTIONS.md`

These are newer than the older root-client folders and are internally consistent:

- Active client work belongs under `clients/{agency}/{client}/`.
- New client folders come from `templates/client_template/`.
- Client-facing reports are HTML first, then PDF.
- Presentation commands live in `presentations/tools/`.
- Reusable report implementation lives in `shared/presentation/`.
- `shared/google_ads_workflow.py` is now a disabled compatibility wrapper, not the main path.

## Active Client Memory

Keep all active client folders and files.

Current active client areas:

- `clients/therappc/thinkhappylivehealthy/`
- `clients/collab_med_spa/`

The THLH folder is active because it contains current rebuild evidence:

- Account export and report inputs.
- Search rebuild working files.
- Current and revised Google Ads Editor staging CSVs.
- Validation files.
- Feedback classification.
- Revision decision logs.
- HTML and PDF client review artifacts.
- Visual audit images and contact sheets.

Some generated artifacts are bulky, but they are useful while the report and rebuild process is still being reviewed. Do not purge client build artifacts until the client work is clearly closed and the useful evidence has been summarized.

## Active Tooling

Keep and review:

- `shared/rebuild/`
- `shared/copy_engine/`
- `shared/presentation/`
- `presentations/tools/`
- `templates/client_template/`

These are current work from April 27 to April 30 and line up with the active process. The strongest current relationship is:

- `presentations/tools/` provides commands a human can run.
- `shared/presentation/` contains implementation used by those commands.
- `clients/{agency}/{client}/build/...` holds generated report artifacts.
- `shared/rebuild/scaffold_client.py` creates new client folders from the template.

## Salvage, Not Current Path

Review before keeping, merging, or deleting:

- `shared/gads/`
- `shared/tools/`
- `shared/validators/`
- `shared/config/`
- `mcp/`
- `docs/browser_automation/`

These areas are older or loosely connected. They contain useful ideas, but the content often references old local paths, MCP setup, old client examples, or older ways of building campaigns.

Do not blindly delete them yet. Also do not treat them as the current agent. The right cleanup is:

1. List the useful capabilities.
2. Map each useful capability to the current process stages.
3. Merge only what helps the active rebuild path.
4. Delete or archive the rest.

Examples of salvage candidates:

- Google Ads API or MCP access ideas.
- Existing validators that can be adapted to the current CSV output contract.
- Website scan helpers.
- Campaign analysis helpers.
- Client structure validators.

## Archive Status

Current archive areas:

- `legacy_archive/root_clients/`
- `legacy_archive/legacy_plans/`
- `legacy_archive/client_examples/`

The archive currently preserves old root-level client folders and planning documents. This was useful as a safety step, but it should not become a second repo inside the repo.

The old root-client folders are stale as operating instructions because they predate the current active process and live outside `clients/{agency}/{client}/`. They may still contain client history, examples, campaign ideas, and tool ideas worth reviewing.

Final archive target:

- Keep one markdown file, likely `legacy_archive/WHAT_WAS_ARCHIVED.md`.
- Remove old archive file trees after useful content has been reviewed or migrated.
- The markdown record should list old client folders, what they contained, and why they were not kept as active work.

## Obvious Trash

Do not commit:

- `.DS_Store`
- `__pycache__/`
- `*.pyc`
- Temporary cache folders.
- Stale worktree pointers or nested `.git` leftovers.

Usually do not commit unless intentionally needed:

- One-off raw exports sitting at repo root.
- Downloaded zip files that can be fetched again.
- DOCX render remnants for a report system that is now HTML/PDF first.

## Recommended Cleanup Order

1. Keep this branch as the cleanup branch.
2. Do not commit the broad staged cleanup yet.
3. Commit active process docs, active client folders, templates, and current report tooling first.
4. Review salvage tooling by capability, not by folder name.
5. Create `legacy_archive/WHAT_WAS_ARCHIVED.md`.
6. Migrate any useful archive lessons into current docs or tools.
7. Purge the archive trees after review.
8. Commit the archive purge separately so it is clear and reversible.

## Sources

- Local process: `AGENTS.md`
- Local process: `docs/GOOGLE_ADS_AGENT_PROCESS.md`
- Client folder rule: `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`
- Report workflow: `presentations/docs/BUILD_INSTRUCTIONS.md`
- Report standard: `docs/HTML_PDF_CLIENT_REPORT_STANDARD.md`
- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en
