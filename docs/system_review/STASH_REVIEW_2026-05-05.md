# Safety Stash Review 2026-05-05

## Purpose

Review `stash@{0}` from `safety catchup dirty state 20260504_165926` and recover useful artifacts without applying the stash wholesale.

Sources:

- Repo process: `AGENTS.md`
- Client folder rules: `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`
- Git stash reference: https://git-scm.com/docs/git-stash

## Recovered

| Bucket | Paths | Reason |
| --- | --- | --- |
| NKPsych optimization package | `clients/NKPsych.com/build/2026-05-04_search_optimization/` | Search optimization package has `manifest.json`, passing `staging_validation_report.json`, passing `report_static_audit.json`, passing `pdf_visual_audit.json`, HTML, PDF, human review, and staged Google Ads Editor CSV. |
| NKPsych source and profile inputs | `clients/NKPsych.com/campaigns/`, `clients/NKPsych.com/config/`, `clients/NKPsych.com/docs/`, `clients/NKPsych.com/reports/performance_inputs/` | Required by the recovered manifest and needed to preserve source context for the optimization package. |
| THLH Client HQ | `clients/therappc/thinkhappylivehealthy/docs/client_hq/` | Active client data asset was present only in the stash and missing from the branch. |
| YouTube and embed scanning support | `shared/tools/website/website_scanner.py`, `shared/creative_assets/build_creative_asset_package.py` | Small generic scanner and creative package support for embedded video discovery. |

## Left In Stash

| Bucket | Reason |
| --- | --- |
| Sky Therapies optimization output | Main staging validation failed with disallowed match types, unsupported negative exact rows, short RSA headlines, and missing/short descriptions. Keep in stash until repaired or regenerated. |
| NKPsych creative image test bundle | Validation reported zero approved assets and zero campaign-ready assets. Keep out of the main branch until it becomes an approved creative package. |
| EMorrison duplicate artifacts | Already committed in the client deliverables branch. |
| NYCMindful duplicate visual screenshots and renamed PDF | Current committed branch keeps the tracked original PDF plus additive revision outputs. |
| THLH cross-client Sky export | Cross-client leakage under THLH build test path. Do not recover. |

## Validation

- NKPsych staged CSV validation: pass.
- NKPsych report static audit: 0 errors, 0 warnings.
- NKPsych PDF visual audit: 0 failures.
- Focused shared tests: `PYTHONPATH=/Users/home/ai/agents/ppc/google_ads_agent pytest -q tests/test_website_scanner.py tests/test_creative_asset_package.py`, 5 passed.

## Stash State

Keep `stash@{0}` after this recovery because it still contains Sky Therapies failed staging output and deferred creative/media artifacts that were intentionally not committed.
