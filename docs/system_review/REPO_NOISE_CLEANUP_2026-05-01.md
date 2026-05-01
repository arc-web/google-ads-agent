# Repo Noise Cleanup Review

Date: 2026-05-01

## Decision

Generated machine noise is not part of the Google Ads Agent system and should stay out of commits.

Keep ignoring:

- `.DS_Store`
- `__pycache__/`
- `*.pyc`

The scan found generated cache files across tests, shared modules, presentation wrappers, client build scripts, and API/MCP review material. None of those files were tracked by Git, so the cleanup removed local generated files only.

## What Was Removed Locally

The local cleanup removed generated files and directories matching:

- `.DS_Store`
- `.pytest_cache`
- `__pycache__`
- `*.pyc`

No client data, source code, documentation, templates, reports, credentials, or build artifacts were removed by this batch.

## What Stayed Unchanged

The `.gitignore` file already contains the required machine-noise patterns:

- `.DS_Store`
- `__pycache__/`
- `*.pyc`

The local `.gitignore` also has unrelated credential ignore edits. Those are not part of this batch and were left unstaged.

## Validation Added

The guard test verifies:

- machine-noise patterns remain ignored
- no generated noise paths are tracked by Git
- credential-related local edits are not required for this cleanup batch

## Sources

- [Script Cleanup Process](SCRIPT_CLEANUP_PROCESS_2026-05-01.md)
- [Google Ads Agent Process](../GOOGLE_ADS_AGENT_PROCESS.md)
