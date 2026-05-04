# Report System Automation Audit

Date: 2026-05-04

## Purpose

This audit turns the latest report-build work into durable automation rules for
new campaign builds, inherited account rebuilds, and revision builds.

The report system has three client-facing report types:

- `Client_New_Campaign_Review`: used when there is no inherited Google Ads account.
- `Client_Rebuild_Review`: used when an inherited Google Ads account is rebuilt.
- `Client_Rebuild_Review_R1`: used after client feedback has been classified and approved.

HTML remains the editable source of truth. PDF remains the client-facing export.
Generated report artifacts stay in the client build folder.

Sources:

- [HTML/PDF Client Report Standard](../HTML_PDF_CLIENT_REPORT_STANDARD.md)
- [Presentation Build Instructions](../../presentations/docs/BUILD_INSTRUCTIONS.md)
- [Presentation Quality Gates](../../presentations/docs/QUALITY_GATES.md)
- [Google Ads Agent Process](../GOOGLE_ADS_AGENT_PROCESS.md)

## Latest Report Creation Lessons

Recent new-campaign report work exposed issues that must become automation
checks, not manual memory:

| Issue found | Resulting rule |
| --- | --- |
| Generic ad-copy page titles such as `Ad Copy Example 1 Of 8` were hard to review. | Ad-copy pages should use the service or ad group name as the page title. |
| Headline and description tables could look mismatched. | RSA headline and description tables need shared column sizing, spacing, and visual grammar. |
| A regional section split into a header-only page and a content page. | A section page with only a header is a failed report build. |
| Regional targeting only handled a simple NY/ZIP explanation. | Regional tables must support states, cities, ZIPs, exclusions, and long location lists. |
| A dense final approval page looked noisy and hard to scan. | Final approval pages should be compact. Detailed confirmation belongs at the end of each detailed section. |
| The word `client` appeared in reader-facing copy. | Reader-facing reports should speak directly to the person reviewing the report. |
| New campaign reports risk sounding like rebuild reports. | New campaign reports must not imply inherited account history. |

## Report Types

### `Client_New_Campaign_Review`

Used when:

- There is no inherited Google Ads account evidence.
- The system is building a new paused Google Ads Editor staging file from website, intake, and operator inputs.
- API upload is off.

Primary automation entrypoints:

- `presentations/tools/build_initial_search_campaign.py`
- `presentations/tools/build_new_campaign_report.py`
- `shared/new_campaign/build_initial_search_campaign.py`
- `shared/presentation/build_new_campaign_report.py`

Required outputs:

- paused Google Ads Editor staging CSV
- `website_scan.json`
- `service_catalog.json`
- `geo_strategy.json`
- `source_attribution.json`
- `campaign_taxonomy.csv`
- `rsa_copy_matrix.csv`
- `human_review.md`
- `Client_New_Campaign_Review.html`
- `Client_New_Campaign_Review.pdf`
- `client_email_draft.md`
- `validation_report.json`
- `new_campaign_visual_audit/`
- `run_manifest.json`

Core content:

- What website and intake sources support.
- What campaign structure is staged.
- Which ad groups, ad copy, regional targeting, and budget need confirmation.
- What validation passed before Google Ads Editor review.

Must not include:

- inherited account comparison language
- previous provider language
- live upload language
- Search partners language unless explicitly needed from client source material
- broad match, exact match, PMAX, or API activation language

### `Client_Rebuild_Review`

Used when:

- There is an inherited account export or prior structure to review.
- The system is rebuilding a paused Google Ads Editor staging file.
- The report needs to explain what was inherited, what changed, and why the new structure is better.

Primary automation entrypoints:

- `shared/rebuild/account_pipeline.py`
- `presentations/tools/build_review_doc.py`
- `presentations/tools/build_fixed_campaign_review.py`
- `shared/presentation/build_review_doc.py`

Required outputs:

- `account_snapshot.json`
- `account_audit.json`
- `source_attribution.json`
- `website_scan.json`
- `service_catalog.json`
- `landing_page_map.json`
- `geo_strategy.json`
- `campaign_taxonomy.csv`
- `rsa_copy_matrix.csv`
- `targeting_spec.json`
- `human_review.md`
- `Client_Rebuild_Review.html`
- `Client_Rebuild_Review.pdf`
- `client_email_draft.md`
- `validation_report.json`
- rendered visual audit directory
- `run_manifest.json`

Core content:

- What was inherited.
- What was rebuilt.
- Why the rebuild is clearer or safer.
- Which services, geos, budget, ad copy, and landing pages need confirmation.
- What remains paused for Google Ads Editor review.

Must not include:

- new-campaign wording that hides inherited account context
- old provider names in repeated report branding
- unsupported claims from stale account data
- live upload language

### `Client_Rebuild_Review_R1`

Used when:

- Client feedback has been classified.
- Approved revisions have been converted into a revised staging file.
- The report should replace the prior review for approval.

Primary automation entrypoints:

- `presentations/tools/build_revision_review.py`
- `shared/presentation/build_revision_review.py`
- `shared/rebuild/account_pipeline.py --mode revise`

Required outputs:

- `client_feedback_classified.json`
- `revision_decision_log.csv`
- revised staging CSV, such as `Google_Ads_Editor_Staging_REV1.csv`
- revised validation JSON
- `Client_Rebuild_Review_R1.html` or equivalent dated revision HTML
- `Client_Rebuild_Review_R1.pdf` or equivalent dated revision PDF
- rendered visual audit directory
- updated `client_email_draft.md`
- updated `run_manifest.json`

Core content:

- What feedback was received.
- Which changes were accepted.
- Which changes were rejected or deferred.
- What changed in the staged CSV.
- What still needs approval before launch.

Must not include:

- unclassified feedback as if it were approved
- client feedback that overrides campaign architecture without decision logging
- stale pre-revision copy as if it were current

## Section Contracts

Each report section should have a clear job. The automation should know what
inputs it needs, where the section appears, when it appears, and how it fails.

| Section | What | Why | Where | When | How | Failure conditions |
| --- | --- | --- | --- | --- | --- | --- |
| Cover | Identifies the report type, business, agency brand, date, and top metrics. | Sets context before details. | First page. | All report types. | Use report-specific title and metrics from staging or validation data. | Wrong report type, missing date, inherited-account wording in a new campaign report. |
| Overview | Shows the review path. | Helps non-technical readers know what they are approving. | After cover. | All report types. | Use 4 to 6 review steps based on report type. | Missing approval path, unclear report purpose, rebuild language in new campaign report. |
| Source Attribution | Explains what sources support the work. | Prevents unsupported claims. | Early or controlled source section. | Required for rebuilds and new builds, optional in short revision reports if lineage is already explicit. | Pull from `source_attribution.json`, account snapshot, website scan, and approved feedback. | Old provider names repeated outside allowed source context. |
| Campaign Structure | Shows the current build shape and future expansion logic. | Explains why campaigns and ad groups are organized this way. | Before ad group detail. | New builds and rebuilds. | Use actual campaign and ad group counts. Future splits must be labeled as future only. | Future campaigns shown as active, missing current staged structure. |
| Ad Groups | Lists services or intent groups being advertised. | Lets the reviewer confirm the services being promoted. | Before ad copy. | All Search build reports. | Table from staging CSV or campaign taxonomy. End with `Please confirm`. | Missing priority prompt, stale ad group names, too-dense tables without chunking. |
| Ad Copy | Shows representative RSA copy. | Lets the reviewer approve copy direction without dumping every variation. | After ad groups. | All Search build reports with RSAs. | Use service or ad group page titles, 15 headlines, 4 descriptions, and consistent table columns. End with `Please confirm`. | Split tables, generic titles, overlong assets, weak headline quality, unsupported claims. |
| Regional Targeting | Shows where ads are staged to run and what location details need confirmation. | Prevents accidental geo overreach. | After ad copy, before budget. | All build reports with location rows. | Table supports state, city, ZIP, radius, exclusion, and review-only rows. End with `Please confirm`. | Header-only page, missing locations, only one state covered when multiple states are staged. |
| Budget | Shows the monthly budget, daily average, optional CPC range, and pacing logic. | Lets the reviewer approve spend. | After regional targeting. | New builds and rebuilds when budget is known. | Use monthly budget as source of truth. Optional CPC range only when supplied. End with `Please confirm`. | Budget omitted, confusing chart, approval separated from budget details. |
| Revision Changes | Shows what changed after feedback. | Makes revision lineage clear. | Before revised ad examples. | Revision reports only. | Use classified feedback and decision log. | Unclassified feedback presented as approved, missing decision source. |
| Approval | Final compact checklist only. | Gives one final review checkpoint. | Last page. | All client-facing build reports. | Four compact tiles by default: ad groups, ads, regional targeting, budget. Keep notes out of the final page. | Dense paragraphs, giant summary typography, signature area unless explicitly requested, low-density footer-only page. |

## Automation Requirements

### Shared Report Contracts

Add a shared report contract layer before expanding more report types. Minimum
contract fields:

- `report_type`
- `report_title`
- `source_artifacts`
- `section_ids`
- `approval_items`
- `quality_gates`
- `visual_audit_dir`
- `staging_csv`
- `validation_report`
- `client_email_draft`

The contract should not replace the HTML builders immediately. It should make
each builder declare what it is producing so tests can validate behavior.

### Manifest Updates

Every `run_manifest.json` should include:

- `report_type`
- `report_html`
- `report_pdf`
- `report_sections`
- `approval_items`
- `quality_gate_results`
- `visual_audit_dir`
- `client_email_draft`
- `live_upload: false`

This lets later automation decide whether a build is complete without scanning
folder names or guessing from file presence.

### Static Report Checks

Static checks should fail on:

- missing required section IDs for the report type
- forbidden words or phrases from client-facing language rules
- em dashes
- `Ad Copy Example` style generic titles
- `Search partners` unless explicitly present in approved source material
- new-campaign reports containing inherited account comparison language
- rebuild reports missing inherited account context
- revision reports missing feedback or decision lineage
- final approval page containing bulky explanatory paragraphs
- missing `Please confirm` prompt after ad groups, ad copy, regional targeting, or budget

### Rendered PDF Checks

Visual checks should fail on:

- blank pages
- header-only pages
- continuation-only pages
- footer-only pages
- text or meaningful elements clipped by page edges
- low-density final approval page unless it is intentionally compact and complete
- ad-copy tables split across pages

Automation should store rendered pages and a contact sheet in the build folder.

### Report Builder Entry Points

New build automation should:

- keep `Client_New_Campaign_Review` separate from rebuild reports
- build from structured source artifacts
- generate `client_email_draft.md`
- write a manifest with report fields
- run static and visual audits
- fail on report contract violations

Rebuild automation should:

- generate `Client_Rebuild_Review`
- include inherited account context from account snapshot and audit
- keep old provider names controlled to source attribution only
- run the same report contract, static, and visual gates

Revision automation should:

- generate `Client_Rebuild_Review_R1` or an equivalent dated revision deliverable
- require classified feedback and decision log
- validate revised staging output
- show accepted, rejected, and deferred changes
- run the same report contract, static, and visual gates

## Implementation Backlog

1. Add a shared report contract module under `shared/presentation/`.
2. Make new campaign report generation declare and validate the report contract.
3. Extend `run_manifest.json` for new campaign one-shot builds.
4. Add report contract tests for new campaign reports.
5. Add rebuild report contract support to `shared/rebuild/account_pipeline.py`.
6. Add revision report contract support to `build_revision_review.py`.
7. Expand `report_quality_audit.py` so it understands report type rules.
8. Expand `pdf_visual_audit.py` or add a wrapper so report-specific visual failures are explicit.
9. Add generated contact sheet requirements to build instructions.
10. Add end-to-end fixtures for one new campaign, one inherited rebuild, and one revision build.

## Test And Acceptance Criteria

Before any report is marked deliverable:

- `python3 -m pytest`
- `python3 -m compileall -q shared presentations tests`
- `python3 presentations/tools/report_quality_audit.py PATH_TO_HTML`
- `python3 presentations/tools/pdf_visual_audit.py PATH_TO_PDF --pages-dir PATH_TO_VISUAL_AUDIT --min-content-ratio 0.055`
- staging CSV validates with `shared/rebuild/staging_validator.py`
- generated manifest includes report type, report paths, visual audit path, approval items, and quality gates
- rendered pages or contact sheet are reviewed before sending

## Current Gaps

- New campaign automation is closest to the target state, but report contract data is not yet first-class.
- Rebuild automation currently reuses the new campaign report builder in places and needs clearer rebuild-specific report semantics.
- Revision automation exists, but it does not yet share a common report contract with new builds and rebuilds.
- Static audit catches some HTML issues, but it does not yet fully enforce report-type language, approval prompt placement, or compact final approval design.
- Visual audit catches low-density pages, but the report contract should also state why each page exists and which section it belongs to.
- Manifest output needs to become the machine-readable proof that report generation, validation, visual audit, and email drafting are complete.

## Working Defaults

- HTML remains source of truth.
- PDF remains client-facing deliverable.
- Reports stay under `clients/{agency}/{client}/build/...`.
- Human-facing commands stay under `presentations/tools/`.
- Reusable implementation stays under `shared/presentation/`.
- Google Ads Editor staging remains the active workflow.
- API upload remains off.
- New campaign, rebuild, and revision reports remain separate report types.
