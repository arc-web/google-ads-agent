# Stage 1 Approval: Protect The Current Agent

This stage identifies the current working `Google_Ads_Agent` system and separates it from older archive or salvage material.

## Plain-English Recommendation

Approve this batch as the current agent foundation.

This batch should be kept together because the files describe and support one working system:

- A clear process for rebuilding Google Ads accounts.
- A standard client folder layout.
- A template for new clients.
- HTML and PDF client report tooling.
- Copy generation, grading, and character-limit checks.
- Active client folders that contain current work and review evidence.

This stage does not decide the fate of older tools, old root-level clients, or the archive. Those belong to later stages.

## Keep As The Current Agent

### Core Instructions And Process

Keep:

- `AGENTS.md`
- `README.md`
- `docs/GOOGLE_ADS_AGENT_PROCESS.md`
- `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`
- `docs/SOURCE_ATTRIBUTION_AND_BRAND_RULES.md`
- `docs/ONBOARDING_INGESTION_AND_REVISION_WORKFLOW.md`
- `docs/HTML_PDF_CLIENT_REPORT_STANDARD.md`
- `docs/AI_REASONING_GATES.md`
- `docs/CLIENT_FACING_LANGUAGE_RULES.md`
- `docs/HUMAN_IN_THE_LOOP_REVIEW_STAGE.md`
- `docs/instruction_audit_2026-04-28.md`
- `docs/REPO_CONTENT_AUDIT_2026-04-30.md`

Why:

- These files agree that Google Ads Editor is the staging layer.
- They agree that active client work belongs under `clients/{agency}/{client}/`.
- They agree that reports are HTML first and PDF second.
- They keep provider names, source attribution, healthcare claims, and client-facing language rules explicit.

### Client Template

Keep:

- `templates/client_template/`

Why:

- This is how new clients should be created.
- It gives new clients a predictable home for exports, reports, intake notes, campaigns, and build outputs.
- It prevents future root-level client folder clutter.

### Active Rebuild Helpers

Keep:

- `shared/rebuild/scaffold_client.py`
- `shared/rebuild/provider_token_validator.py`
- `shared/rebuild/__init__.py`

Keep as legacy internal fallback, but not client-facing:

- `shared/rebuild/hitl_review_doc.py`

Why:

- `scaffold_client.py` creates new client folders from the template.
- `provider_token_validator.py` protects generated outputs from leaking previous provider names.
- `hitl_review_doc.py` clearly says it is not the branded client-facing report path, so it should not drive the current report workflow.

### Active Report Tools

Keep:

- `presentations/`
- `presentations/tools/`
- `shared/presentation/`

Why:

- `presentations/` is the human-facing place to find report instructions.
- `presentations/tools/` gives simple commands people can run.
- `shared/presentation/` holds the implementation those commands use.
- The flow is clear: client HTML source, prepared HTML, fixed-page HTML, Chrome-headless PDF, static audit, visual audit.

### Active Copy Tools

Keep:

- `shared/copy_engine/`

Why:

- This contains the current copy generation, grading, character-limit enforcement, and report-generation logic.
- It directly supports RSA headline and description quality.
- It records lessons from the THLH build, including model choice, JSON parsing, character limits, and page layout failures.

### Active Client Work

Keep:

- `clients/`
- `clients/therappc/thinkhappylivehealthy/`
- `clients/collab_med_spa/`

Why:

- Client folders are working memory, not clutter.
- THLH contains current account exports, reports, staging CSVs, validation outputs, feedback classification, revision logs, HTML/PDF reports, and visual audit artifacts.
- Collab Med Spa contains targeting and geo notes that may gain value over time.

## Exclude From This Stage

Do not include these in the Stage 1 approval batch:

- `legacy_archive/`
- `shared/gads/`
- `shared/tools/`
- `shared/validators/`
- `shared/config/`
- `mcp/`
- `docs/browser_automation/`
- `.DS_Store`
- `__pycache__/`
- `*.pyc`
- root-level one-off raw exports

Why:

- Archive review belongs to Stage 4.
- Salvage tooling belongs to Stage 3.
- Browser automation and MCP notes may still contain useful ideas, but they are not part of the current working agent path yet.
- Machine noise should not be committed.

## Approval Decision

Recommended decision:

Approve Stage 1 as the current `Google_Ads_Agent` foundation.

After approval, the next implementation step is to stage only this Stage 1 foundation as the first safe batch. No archive purge should happen in Stage 1.

## Sources

- Current repo instructions: `AGENTS.md`
- Current process: `docs/GOOGLE_ADS_AGENT_PROCESS.md`
- Client folder rule: `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`
- Report workflow: `presentations/docs/BUILD_INSTRUCTIONS.md`
- Report standard: `docs/HTML_PDF_CLIENT_REPORT_STANDARD.md`
- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en
