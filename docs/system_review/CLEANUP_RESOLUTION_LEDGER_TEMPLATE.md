# Cleanup Resolution Ledger Template

Date: YYYY-MM-DD

## Purpose

Use this ledger for catch-up, cleanup, migration, archive, purge, stash-drop, branch-drop, generated-artifact removal, or deletion-heavy work.

No file, folder, stash, branch, or artifact may be purged, dropped, archived, deleted, or discarded without a logical resolution.

Valid resolutions:

- `kept`
- `committed`
- `moved`
- `superseded`
- `archived`
- `generated-noise`
- `owner-approved purge`

## Sources

- Repo process: `AGENTS.md`
- Client folder rules: `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`
- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en

## Ledger

| Path Or Stash Item | Bucket | Resolution | Evidence Or Replacement Path | Validation Performed | Owner Approval |
| --- | --- | --- | --- | --- | --- |
| `example/path` | Example bucket | `kept` | `example/path` remains tracked or preserved | `python3 -m pytest` | Not required |

## Stash And Branch Closure

Before dropping any safety stash or branch, confirm:

- Every path or stash item has a ledger row.
- No unique needed file remains only in the stash or branch.
- Generated noise has been inventoried before purge.
- Any `owner-approved purge` row names the approval source.

## Final Status

- Worktree status:
- Remaining stashes:
- Remaining branches:
- PR or commit:
