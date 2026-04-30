# Presentation System Developer Guide

Date: 2026-04-28

## Purpose

The presentation system is a first-class subsystem of the Google Ads Agent. It is not an add-on to campaign generation.

It exists to translate campaign strategy, account rebuilds, client feedback, revision notes, and launch decisions into polished client-facing PDFs. The PDF is the artifact the client understands, reviews, approves, and shares internally.

The output has to do three jobs:

- Communicate the strategy clearly to non-technical stakeholders.
- Show enough evidence to justify the rebuild.
- Create a controlled human-in-the-loop approval stage before launch.

## What Was Built

### Fixed-Page Campaign Review Builder

Human-facing command:

- `presentations/tools/build_fixed_campaign_review.py`

Implementation:

- `shared/presentation/build_fixed_campaign_review.py`

What it does:

- Reads prepared campaign review HTML.
- Parses sections with BeautifulSoup.
- Applies deterministic client-facing cleanup.
- Creates explicit Letter-sized `.pdf-page` sections.
- Groups ad review modules two per page.
- Adds a revision-control panel when an odd final ad group would otherwise leave empty space.
- Exports a fixed-page HTML file and PDF.

Why it exists:

The previous report relied on natural browser pagination. That caused orphan headers, blank pages, split modules, huge gaps, and footer-only pages. The fixed-page builder makes each PDF page an intentional unit.

### Chrome PDF Export Wrapper

Human-facing command:

- `presentations/tools/build_review_doc.py`

Implementation:

- `shared/presentation/build_review_doc.py`

What it does:

- Exports HTML to PDF through headless Chrome.
- Uses the known working flags:
  - `--headless=new`
  - `--print-to-pdf-no-header`
  - `--no-pdf-header-footer`
  - `--no-margins`
  - `--disable-gpu`
  - `--run-all-compositor-stages-before-draw`

Why it exists:

Chrome PDF export is sensitive to flags. Dropping one flag can introduce browser headers, margins, incomplete rendering, or unstable output.

### Static HTML Presentation Audit

Human-facing command:

- `presentations/tools/report_quality_audit.py`

Implementation:

- `shared/presentation/report_quality_audit.py`

What it checks:

- Top-level report sections exist.
- Required section-header and subsection-header patterns exist.
- Forbidden draft phrases are absent.
- Em dashes are absent.
- `force-page` classes are absent.
- Repeated modules do not force page breaks.
- Tall containers and grid containers do not use `break-inside: avoid`.
- Copy grade placeholders are not shown to clients.

Why it exists:

Static rules catch known generator failures before the PDF is rendered.

### Rendered PDF Visual Audit

Human-facing command:

- `presentations/tools/pdf_visual_audit.py`

Implementation:

- `shared/presentation/pdf_visual_audit.py`

What it does:

- Renders the PDF to PNG pages with `pdftoppm`.
- Measures content density.
- Measures vertical content span.
- Flags low-density or near-empty pages.
- Produces page images for manual QA.

Why it exists:

Valid HTML can still create a bad PDF. The visual audit checks the rendered output, not just the source.

### Client Review Preparation Stage

Human-facing command:

- `presentations/tools/prepare_client_review_html.py`

Implementation:

- `shared/presentation/prepare_client_review_html.py`

What it does:

- Removes draft QA language.
- Replaces pending copy grades with structured inherited and rebuilt grades.
- Removes unsafe forced page breaks.
- Removes client-facing over-limit warnings from the review.
- Normalizes exact 30-character headlines as valid.
- Exports prepared HTML and optionally a PDF.

Why it exists:

Generated report HTML can include internal notes that are useful during development but inappropriate for client delivery.

## Issues We Hit

### 1. Browser Flow Was Treated Like Page Design

Problem:

The original report was HTML content flowing into a PDF. Sections, grids, cards, and footers were left to browser pagination.

Observed failures:

- Large blank spaces below small modules.
- Section headers stranded at the bottom or top of pages.
- Footer pushed onto its own page.
- Ad group cards floating in the top half of a page.
- Continuation headers appearing without meaningful following content.

Fix:

Create `build_fixed_campaign_review.py` to generate explicit `.pdf-page` containers.

### 2. Forced Page Breaks Were Used Without Page-Fit Math

Problem:

Rules like `break-before: page` and `page-break-before: always` were applied to repeated modules and continuation headers.

Observed failures:

- Empty continuation pages.
- One small ad module per page.
- Short sections starting on new pages with weak density.

Fix:

The prep stage strips unsafe forced breaks. The static audit now rejects repeated modules that force page breaks.

### 3. `break-inside: avoid` Was Applied Too Broadly

Problem:

Tall containers and grid containers used `break-inside: avoid`, causing Chrome to move too much content to the next page.

Observed failures:

- Page gaps before grids.
- Orphan headers.
- Content deferring unnecessarily.

Fix:

The rule is now limited to leaf cards and table rows. It is forbidden on grids, flex containers, and tall repeated modules.

### 4. Internal Copy QA Leaked Into Client Output

Problem:

The report showed phrases like:

- `Red counts are over the character limit and flagged for rewrite.`
- `Sweep highlights:`
- At-limit warnings for valid 30-character headlines.

Observed failures:

- Client-facing pages looked like internal QA output.
- One sweep paragraph blew up the Kindergarten Readiness page.

Fix:

The fixed builder removes sweep notes and at-limit warnings. Exact 30-character headlines are treated as valid.

### 5. Client Feedback Was Not Fully Reflected

Problem:

Rejected or sensitive service claims stayed in the report.

Examples:

- Active EMDR copy despite no current capacity.
- Adult ADHD testing phrasing despite the service being through age 21.
- Standalone family therapy language despite parent-child support being the real service.

Fix:

The fixed builder applies deterministic cleanup for known client-feedback conflicts.

Long-term fix:

Move these cleanup rules out of the builder and into structured client revision data.

### 6. The Ad Copy Review Section Was Too Sparse

Problem:

One ad group per page created too much empty space.

Fix:

Ad review modules now render two per page. If one ad group remains, the page gets a revision-control panel.

## Tools We Emulated Or Evaluated

### Paged Media Tools

We did not fully adopt these tools yet, but their design model informs the next stage:

- Paged.js: browser-based paged media polyfill for HTML-to-PDF workflows.
- WeasyPrint: Python HTML/CSS to PDF renderer with paged media support.
- Vivliostyle: CSS typesetting and paged media publishing tool.

Current decision:

Use Chrome headless with fixed-page HTML for immediate reliability. Keep Paged.js, WeasyPrint, and Vivliostyle as candidates for a later renderer abstraction.

### Internal Tools Built

- Static HTML audit.
- Rendered PDF density audit.
- Fixed-page campaign review builder.
- Client review cleanup stage.
- Contact-sheet generation by local script during QA.

## Current Command Path

From repo root:

```bash
python3 presentations/tools/build_fixed_campaign_review.py \
  --input-html clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28_prepared.html \
  --output-html clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28_fixed.html \
  --output-pdf clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28_fixed.pdf
```

Audit:

```bash
python3 presentations/tools/report_quality_audit.py \
  clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28_fixed.html
```

Rendered visual audit:

```bash
python3 presentations/tools/pdf_visual_audit.py \
  clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28_fixed.pdf \
  --pages-dir clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/fixed_visual_audit \
  --min-content-ratio 0.055
```

## Required QA Standard

Every client PDF must pass:

- Static HTML audit: `0 errors`.
- Rendered PDF audit: `0 failures`.
- Manual contact sheet inspection.
- No internal QA phrases.
- No unsupported client claims.
- No footer-only pages.
- No continuation-only pages.
- No module clipped at the page edge.
- No text sitting on container edges without padding.
- No red character-count flags for valid assets.

## Presentation Step 2

Presentation Step 2 is the next development phase.

Goal:

Turn the current fixed-builder proof into a reusable presentation engine.

Required work:

1. Create a structured presentation data model.
2. Move client-specific cleanup rules into revision JSON.
3. Separate page templates from Python string templates.
4. Add a page planner that chooses layouts by content count and content height.
5. Add OCR or layout detection to catch clipped text and oversized font blocks.
6. Add contact-sheet generation as a first-class command.
7. Add a Playwright or browser screenshot QA pass for HTML before PDF export.
8. Add a renderer abstraction so Chrome, Paged.js, WeasyPrint, or Vivliostyle can be tested behind the same interface.
9. Add approval-state artifacts for client review cycles.
10. Add tests with deliberately bad reports to prove the audits fail.

## Proposed Directory Structure

```text
presentations/
  README.md
  docs/
    DEVELOPER_GUIDE.md
    PRESENTATION_STEP_2_PLAN.md
    QUALITY_GATES.md
  tools/
    build_fixed_campaign_review.py
    build_review_doc.py
    prepare_client_review_html.py
    report_quality_audit.py
    pdf_visual_audit.py
  templates/
    fixed_campaign_review/
      README.md
  examples/
    thinkhappylivehealthy/
      README.md
```

## Known Technical Debt

- `shared/presentation/build_fixed_campaign_review.py` still contains Python string-based HTML templates.
- Client-specific cleanup is currently embedded in the fixed builder.
- Visual audit uses density heuristics, not semantic layout understanding.
- Contact sheet generation was done through ad hoc local commands and needs its own tool.
- The fixed builder currently assumes the THHL report section IDs.
- Styling is not yet tokenized into a brand theme object.
- The audit allows hidden placeholder section headers to satisfy legacy checks.
- `shared/presentation` and `presentations` both exist. The current wrappers prevent breakage, but long-term ownership should move into `presentations`.

## Do Not Repeat

- Do not rely on natural browser pagination for client PDFs.
- Do not use forced page breaks on repeated modules.
- Do not use continuation headers as page starters.
- Do not put internal QA notes in the client report.
- Do not solve visual layout with one-off PDF edits.
- Do not treat the PDF as secondary to the campaign CSV.

## Sources

- MDN page-break-inside: https://developer.mozilla.org/en-US/docs/Web/CSS/page-break-inside
- MDN CSS fragmentation: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_fragmentation
- W3C CSS absolute lengths: https://www.w3.org/TR/css-values-3/#absolute-lengths
- Paged.js: https://github.com/pagedjs/pagedjs
- WeasyPrint: https://weasyprint.org/
- Vivliostyle: https://vivliostyle.org/
