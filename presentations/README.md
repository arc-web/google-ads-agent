# Presentations Subsystem

This directory is the dedicated workspace for client-facing presentation and report generation.

The campaign builder creates strategy, CSVs, and account structure. The presentation subsystem turns that work into client-readable artifacts that can be reviewed, approved, revised, and archived.

## Status

Current production path:

1. Build or prepare source HTML.
2. Convert source HTML into fixed-page client review HTML.
3. Export fixed HTML to PDF.
4. Run static HTML audit.
5. Run rendered PDF visual audit.
6. Inspect the page contact sheet before sending.

This directory is the human-facing operating surface for presentation builds. Use the commands and docs here first.

`shared/presentation/` remains only for import compatibility and reusable internals. Do not send people there for build instructions.

## Build Instructions

Read this first:

- `presentations/docs/BUILD_INSTRUCTIONS.md`

For the current Think Happy Live Healthy review, the editable HTML source and generated PDF live in the client build folder:

- `clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28_fixed.html`
- `clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28_fixed.pdf`

## Key Tools

- `presentations/tools/build_fixed_campaign_review.py`
- `presentations/tools/prepare_client_review_html.py`
- `presentations/tools/build_revision_review.py`
- `presentations/tools/build_review_doc.py`
- `presentations/tools/report_quality_audit.py`
- `presentations/tools/pdf_visual_audit.py`

## Main Guide

Read:

- `presentations/docs/BUILD_INSTRUCTIONS.md`
- `presentations/docs/DEVELOPER_GUIDE.md`

## Design Principles

- Fixed page geometry for client PDFs.
- Explicit page composition instead of uncontrolled browser flow.
- Every page should have a purpose, visual mass, and safe padding.
- Report content must be client-facing, not internal QA chatter.
- Static checks and rendered checks are both mandatory.

## Current Client Example

Working PDF:

- `clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28_fixed.pdf`

Rendered page audit:

- `clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/fixed_visual_audit/`

## Sources

- MDN page-break-inside: https://developer.mozilla.org/en-US/docs/Web/CSS/page-break-inside
- W3C CSS absolute lengths: https://www.w3.org/TR/css-values-3/#absolute-lengths
- Paged.js: https://github.com/pagedjs/pagedjs
- WeasyPrint: https://weasyprint.org/
