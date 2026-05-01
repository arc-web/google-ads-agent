# Stage 2 Approval: Protect Client Memory

This stage reviews active client work as client memory, not as random files.

## Plain-English Recommendation

Approve the active client memory already protected in Stage 1.

No additional client files need to be committed in Stage 2. The remaining uncommitted client files are machine noise, a superseded DOCX draft, a rendered preview of that DOCX draft, and a downloadable Google geo-target zip.

## Current Active Client Memory

Keep:

- `clients/README.md`
- `clients/therappc/thinkhappylivehealthy/`
- `clients/collab_med_spa/`

Why:

- Client folders are working memory.
- They preserve source inputs, decisions, generated outputs, client feedback, validation evidence, and report review artifacts.
- This is where the agent learns from real rebuilds over time.

## Think Happy Live Healthy

Status: active client memory.

Keep the committed THLH files because they include:

- Original account export.
- Search and location performance inputs.
- Search rebuild scripts and working analysis files.
- Current and revised Google Ads Editor staging CSVs.
- Validation files and human review notes.
- Client feedback classification and revision decision log.
- HTML and PDF campaign review reports.
- Rendered visual audit images and contact sheets.
- Postmortem notes that explain what the report system learned.

Important reasoning:

- The THLH files are not clutter while the system is still learning from them.
- They show the actual path from account data to staged CSV to client-facing review report.
- They are useful evidence for future clients and future tooling.

## Collab Med Spa

Status: active client memory, early stage.

Keep the committed Collab Med Spa docs because they include:

- Geo and targeting notes.
- Market-specific targeting constraints.
- Healthcare and sensitive-category targeting reminders.

Important reasoning:

- The folder is small.
- The notes may become useful when this client enters a fuller rebuild cycle.
- There is no obvious duplicate or machine-generated clutter in the committed Collab Med Spa files.

## Leave Out Of Client Memory

Do not commit:

- `clients/.DS_Store`
- `clients/therappc/thinkhappylivehealthy/build/.DS_Store`
- `clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/.DS_Store`
- `clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/Client_Rebuild_Review_DRAFT.docx`
- `clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/review_doc_render/`
- `clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/geotargets-2026-03-31.csv.zip`

Why:

- `.DS_Store` files are macOS machine noise.
- The DOCX draft and its rendered preview are from the abandoned DOCX-era report path.
- The current report standard is HTML first and PDF second.
- The geotarget zip is a downloaded source package that can be fetched again from Google if needed.

## Stage 2 Decision

Recommended decision:

Approve Stage 2 with no new client-memory commit.

Next implementation step:

- Stage 3 should review older shared tooling for salvage:
  - `shared/gads/`
  - `shared/tools/`
  - `shared/validators/`
  - `shared/config/`
  - `mcp/`
  - `docs/browser_automation/`

Noise cleanup should wait until Stage 5 so it happens in one deliberate cleanup batch.

## Sources

- Current repo instructions: `AGENTS.md`
- Current process: `docs/GOOGLE_ADS_AGENT_PROCESS.md`
- Client folder rule: `docs/CLIENT_DIRECTORY_SCAFFOLDING.md`
- Report workflow: `presentations/docs/BUILD_INSTRUCTIONS.md`
- Report standard: `docs/HTML_PDF_CLIENT_REPORT_STANDARD.md`
- Google Ads geo target source: https://developers.google.com/google-ads/api/data/geotargets
