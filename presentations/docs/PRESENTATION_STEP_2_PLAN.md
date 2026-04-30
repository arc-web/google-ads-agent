# Presentation Step 2 Plan

## Objective

Build a reusable presentation engine for client-facing Google Ads reports.

The engine must support:

- Initial rebuild review.
- Revision review.
- Client approval package.
- Internal technical appendix.
- PDF export.
- Visual QA.
- Source attribution.
- Brand-aware layout.

## Phase 1: Stabilize Current Fixed Builder

Tasks:

- Keep `build_fixed_campaign_review.py` as the working production path.
- Add fixture tests with known bad HTML.
- Add a formal contact-sheet generator.
- Add screenshot comparison for key pages.
- Move client-specific rewrite rules into a JSON revision file.

Done when:

- A report can be regenerated from source HTML and revision JSON with no manual edits.
- Static and visual audits pass.
- The contact sheet is generated automatically.

## Phase 2: Data Model

Create structured schemas for:

- Report metadata.
- Client brand theme.
- Campaign summary.
- Before and after account state.
- Geo strategy.
- Ad group review modules.
- Copy grade summaries.
- Client feedback and revision decisions.
- Approval checklist.

Output should be JSON first, then HTML.

## Phase 3: Template System

Move HTML into templates:

- Cover page.
- Before and after page.
- Methodology page.
- Data evidence page.
- Architecture page.
- Roadmap page.
- Ad-copy two-up page.
- Single ad-copy plus revision-controls page.
- Approval page.

Use a real templating layer such as Jinja2.

## Phase 4: Page Planner

Build a planner that chooses page layouts based on:

- Count of ad groups.
- Count of headlines and descriptions.
- Presence of notes.
- Table height.
- Required approval blocks.
- Page density target.

The planner should output a page manifest before rendering.

## Phase 5: QA Expansion

Add gates:

- Static HTML audit.
- Rendered PDF density audit.
- Contact sheet generation.
- OCR text clipping check.
- Edge padding check.
- Page count expectation check.
- Forbidden client-facing phrase check.
- Unsupported claim check.

## Phase 6: Renderer Abstraction

Evaluate renderers behind one command:

- Chrome headless.
- Paged.js.
- WeasyPrint.
- Vivliostyle.

The system should record which renderer created the PDF and preserve render logs.

## Phase 7: Client Review Workflow

Add explicit lifecycle states:

- Draft internal.
- Client review.
- Client feedback received.
- Revision prepared.
- Approved for staging.
- Published to Google Ads Editor.
- Published live.

Every report should include a matching machine-readable approval state file.

## Sources

- Paged.js: https://github.com/pagedjs/pagedjs
- WeasyPrint: https://weasyprint.org/
- Vivliostyle: https://vivliostyle.org/
- MDN CSS fragmentation: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_fragmentation
