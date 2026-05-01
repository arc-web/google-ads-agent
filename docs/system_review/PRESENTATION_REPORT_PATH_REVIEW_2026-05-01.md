# Presentation Report Path Review

Date: 2026-05-01

## Decision

The presentation and report path is aligned enough for the account-build cleanup sequence.

Keep this split:

- `presentations/` is the human-facing operating surface.
- `presentations/tools/` contains commands that operators should run.
- `presentations/docs/` contains build instructions, quality gates, and developer guidance.
- `shared/presentation/` contains implementation modules and compatibility imports.
- generated HTML, PDF, previews, audits, and contact sheets stay inside `clients/{agency}/{client}/build/{date}_account_rebuild/`.

This batch does not move presentation code. The current wrappers already preserve the right operating surface while keeping the reusable implementation in `shared/presentation/`.

## Areas Reviewed

### Active Human-Facing Path

- `presentations/README.md`
- `presentations/docs/BUILD_INSTRUCTIONS.md`
- `presentations/docs/DEVELOPER_GUIDE.md`
- `presentations/docs/QUALITY_GATES.md`
- `presentations/tools/build_fixed_campaign_review.py`
- `presentations/tools/build_review_doc.py`
- `presentations/tools/build_revision_review.py`
- `presentations/tools/prepare_client_review_html.py`
- `presentations/tools/report_quality_audit.py`
- `presentations/tools/pdf_visual_audit.py`

Role:

- active path for client-facing report operation
- contains the commands a human should run
- owns the visible documentation for HTML-first PDF reporting

### Implementation And Compatibility Path

- `shared/presentation/build_fixed_campaign_review.py`
- `shared/presentation/build_review_doc.py`
- `shared/presentation/build_revision_review.py`
- `shared/presentation/prepare_client_review_html.py`
- `shared/presentation/report_quality_audit.py`
- `shared/presentation/pdf_visual_audit.py`
- `shared/presentation/page_break_rules.css`
- `shared/presentation/section_header.css`

Role:

- active implementation code
- compatibility import surface for older module paths
- not the place to send operators for build instructions

## What Stayed Active

The current HTML-first report flow remains active:

1. Build or prepare source HTML in the client build folder.
2. Convert source HTML into fixed-page client review HTML.
3. Export fixed HTML to PDF with Chrome headless.
4. Run static HTML audit.
5. Run rendered PDF visual audit.
6. Inspect rendered pages or contact sheet before sending.

This matches the existing presentation build instructions and keeps presentation validation after campaign-build validation.

## What Stayed Deferred

These items are useful, but they are not blockers before campaign-build dry-run testing:

- turning `shared/presentation/` into a new package layout
- replacing the current wrapper pattern with a single top-level command
- rebuilding the report engine around a structured presentation data model
- running full HTML and PDF visual QA for every dry-run candidate

Those belong after the campaign generator, validator, copy engine, client template, and test-candidate flow are stable.

## Safety Rules

- Do not place human-facing build instructions under `shared/presentation/`.
- Do not make DOCX, PPTX, or Markdown the canonical client-facing rebuild review source.
- Do not place generated report outputs in `presentations/`.
- Do not run presentation export as proof that campaign staging is valid.
- Do not skip the campaign staging validator because a report rendered cleanly.

## Validation Added

The guard test verifies:

- presentation docs identify `presentations/` and `presentations/tools/` as the human-facing surface
- presentation docs identify `shared/presentation/` as reusable implementation or compatibility code
- every wrapper in `presentations/tools/` imports from `shared.presentation`
- wrappers insert the repo root before importing shared modules

## Sources

- [Presentation Build Instructions](../../presentations/docs/BUILD_INSTRUCTIONS.md)
- [Presentation Developer Guide](../../presentations/docs/DEVELOPER_GUIDE.md)
- [Google Ads Agent Process](../GOOGLE_ADS_AGENT_PROCESS.md)
