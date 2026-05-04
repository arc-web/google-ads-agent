# Worktree Triage 2026-05-04

## Purpose

Resolve the dirty worktree after Search asset automation and client deliverable generation without deleting active client assets or mixing client deliverables into shared-tooling commits.

Sources:

- Repo process: `AGENTS.md`
- Client folder rules: `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`
- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en

## Preservation

- Active cleanup branch: `codex/client-deliverables-catchup-20260504`.
- Safety branch: `codex/safety-catchup-20260504_165926`.
- Safety tag: `safety/catchup-20260504_165926`.
- Safety stash: `stash@{0}`, message `safety catchup dirty state 20260504_165926`.

## Classification

| Bucket | Paths | Action | Reason |
| --- | --- | --- | --- |
| Shared report wording | `shared/presentation/build_new_campaign_report.py` | `commit_system` | Generic report language now handles regional targeting instead of implying national targeting by default. |
| Search-term email drafting | `shared/presentation/client_email_draft.py`, `tests/test_client_email_draft.py` | `commit_system` | Search-term and regional confirmation emails now use a review-oriented format without carrying generic rebuild confirmation copy. |
| Revision email generation | `shared/rebuild/account_pipeline.py` | `commit_system` | Replaces shared hard-coded client revision email text with notes derived from `client_feedback_classified.json`. |
| RSA service-logic gate | `shared/rebuild/rsa_headline_quality.py` | `commit_system` | Completes service-logic-aware headline generation so the audit accepts the new optional context and tests pass. |
| Service logic research helper | `shared/rebuild/service_logic_research.py` | `commit_system` | Generic website-backed service interpretation helper retained as shared rebuild tooling. |
| One-shot service-logic build integration | `shared/new_campaign/build_initial_search_campaign.py`, `shared/presentation/build_new_campaign_report.py`, `shared/rebuild/rsa_headline_quality.py`, `shared/rebuild/service_logic_research.py` | `commit_system` | Service logic research is now generated during one-shot builds, passed into RSA generation, audited in report output, and included in manifests. |
| Triage report | `docs/system_review/WORKTREE_TRIAGE_2026-05-04.md` | `commit_system` | Documents path-level disposition for the worktree cleanup. |
| EMorrison initial build | `clients/arc/emorrison_consulting/` | `commit_client_artifact` | Correct agency/client layout with validation anchors `run_manifest.json`, `validation_report.json`, `run_csv_validation_report.json`, and `human_review.md`. |
| NYC Mindful revision package | `clients/therappc/nyc_mindful_mental_health_counseling/build/2026-05-02_initial_search_build/` and `docs/client_hq/` | `commit_client_artifact` | Validated Rev1 package includes `client_feedback_classified.json`, `revision_decision_log.csv`, `human_review.md`, validated dated Rev1 CSV, HTML, PDF, and Client HQ artifacts. |
| NYC Mindful tracked original PDF | `clients/therappc/nyc_mindful_mental_health_counseling/build/2026-05-02_initial_search_build/Client_New_Campaign_Review.pdf` | `restore_tracked_artifact` | The tracked original PDF remains preserved because the replacement PDF is additive revision output, not a documented deletion. |
| Generated cache files | `__pycache__/`, `*.pyc`, `.DS_Store` | `purge_generated_noise` | Generated local runtime files are not active client assets or process documentation. |
| Duplicate Rev1 output | `nyc_mindful_mental_health_counseling_google_ads_editor_staging_rev1_20260504_080026.*` | `purge_generated_noise` | Duplicate later test output was removed because the committed Rev1 package uses the validated `20260504_071707` output. |
| Deferred client folders from earlier safety capture | `clients/NKPsych.com/`, `clients/skytherapies/`, THLH cross-client test output | `hold_for_owner_review` | Preserved in the safety stash and not committed in this cleanup branch because the current worktree no longer contains them as untracked files. |

## Validation Summary

- Full suite before final cleanup: `PYTHONPATH=/Users/home/ai/agents/ppc/google_ads_agent pytest -q`, 245 passed.
- Focused final check: `PYTHONPATH=/Users/home/ai/agents/ppc/google_ads_agent python3 -m py_compile shared/rebuild/service_logic_research.py && PYTHONPATH=/Users/home/ai/agents/ppc/google_ads_agent pytest -q tests/test_rsa_headline_quality.py tests/test_client_email_draft.py`, 12 passed.
- Final service-logic integration check: `PYTHONPATH=/Users/home/ai/agents/ppc/google_ads_agent pytest -q tests/test_rsa_headline_quality.py tests/test_new_campaign_report.py tests/test_account_pipeline.py tests/test_initial_search_campaign_builder.py tests/test_client_email_draft.py`, 25 passed.
- EMorrison validation anchors present: `run_manifest.json`, `validation_report.json`, `run_csv_validation_report.json`, `human_review.md`.
- NYC Mindful validation anchors present: `client_feedback_classified.json`, `revision_decision_log.csv`, `human_review.md`, `nyc_mindful_mental_health_counseling_google_ads_editor_staging_rev1_20260504_071707_validation.json`.
- Generated cache files were removed with path-specific cleanup only.

## Launch State

All Google Ads Editor CSV outputs in the committed client packages are staged for human review only. No live Google Ads upload or API mutation was performed.
