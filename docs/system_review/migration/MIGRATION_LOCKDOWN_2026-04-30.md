# Google Ads Agent PPC Migration Lockdown

Temporary migration manifest. Delete this file after the repo owner confirms the workspace migration is complete and the git state is clean.

## Purpose

This file records the cleanup from the mistaken workspace path into the canonical PPC department repo.

- Wrong external workspace path: `/Users/home/ai/google_ads_agent`
- Canonical workspace root: `/Users/home/ai/agents/ppc/google_ads_agent`
- Temporary recovery folder removed by this pass: `legacy_archive/recovered_wrong_path_2026-04-30/google_ads_agent_wrong_path`

## Current Source of Truth

The active repo contract is `AGENTS.md` at the canonical workspace root. It says:

- Active client work belongs under `clients/{agency}/{client}/`.
- New clients come from `templates/client_template/`.
- Old root-level client folders belong under `legacy_archive/root_clients/`.
- Old planning documents that conflict with the current process belong under `legacy_archive/legacy_plans/`.
- Presentation build instructions belong under `presentations/`.

The current archive contract is `legacy_archive/README.md`. It defines these archive homes:

- `legacy_archive/root_clients/`
- `legacy_archive/legacy_plans/`
- `legacy_archive/client_examples/`

## What Happened

Work was accidentally done in `/Users/home/ai/google_ads_agent` instead of `/Users/home/ai/agents/ppc/google_ads_agent`.

That wrong external workspace was moved into this repo as a temporary recovery folder so it would not keep existing as a separate active workspace. The stale git worktree was pruned. After inspection, the recovery folder was not a valid permanent archive category because it duplicated established archive homes and contained generated cache noise plus a stale `.git` worktree pointer.

During final verification, `/Users/home/ai/google_ads_agent` existed again as a tiny stub containing only `AGENTS.md` memory context. That stub was also removed so the PPC department repo is the only Google Ads Agent workspace path.

## Recovery Decisions

| Recovered area | Decision | Reason |
|---|---|---|
| `.git` in recovery folder | Purged | Stale worktree pointer. The only active git root must be the canonical PPC repo. |
| `.pytest_cache`, `__pycache__`, `.DS_Store`, temporary cache files | Purged | Generated machine artifacts. Not source of truth. |
| Root client folders such as `brain_based_emdr`, `full_tilt_auto_body`, `wrights_impact_window_and_door` | Purged from recovery folder | Historical root clients already belong under `legacy_archive/root_clients/`. |
| Recovered process docs | Not blindly merged | Current process docs already live under `docs/` and `presentations/`. Any future migration should be reviewed file by file against `AGENTS.md`. |
| Recovered shared tooling | Not blindly merged | Active shared tooling already lives under `shared/`. Future merges must be deliberate and tested. |
| Recovered tests | Not blindly merged | Tests must match the current PPC repo layout before being reintroduced. |
| Temporary recovery folder | Purged | The manifest is enough migration evidence. No random recovered workspace should remain. |

## Final Intended Layout

- `clients/`: active client work and generated rebuilds.
- `docs/`: active repo process, standards, and operating rules.
- `presentations/`: active client-facing HTML and PDF report workflow.
- `shared/`: reusable tooling and implementation code.
- `templates/`: scaffold sources for new clients.
- `legacy_archive/root_clients/`: old root-level client examples.
- `legacy_archive/legacy_plans/`: old or superseded planning docs.
- `legacy_archive/client_examples/`: historical examples only.

## Follow-Up Before Deleting This Manifest

- Confirm `git status --short --untracked-files=all` is understandable.
- Confirm no second git root exists below this repo.
- Confirm `/Users/home/ai/google_ads_agent` does not exist.
- Confirm any useful recovered work has been intentionally migrated into the canonical layout.
