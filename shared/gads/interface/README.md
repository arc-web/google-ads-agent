# Shared GADS Interface

This folder is salvage-only.

The Streamlit campaign management app is not part of the active Google Ads Agent workflow. It references live API service methods, so it must stay inactive until API automation is explicitly approved and tested.

Current active workflow:

- generate Google Ads Editor staging files
- validate staging files with `shared/rebuild/staging_validator.py`
- review manually before any account changes

Do not use this interface for live client work in the current phase.
