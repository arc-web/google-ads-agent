# HTML/PDF Client Report Standard

Date: 2026-04-28

## Current Home

Presentation build instructions now live under:

- `presentations/docs/BUILD_INSTRUCTIONS.md`
- `presentations/docs/DEVELOPER_GUIDE.md`

This file remains as a process reference, but humans should run presentation builds from `presentations/tools/`.

## Purpose

Client-facing rebuild reviews are branded reports, not technical dumps. The canonical deliverable is a PDF designed from HTML.

The HTML file is the source of truth. The PDF is what gets sent to the client.

## Canonical Outputs

For a first review:

- `Client_Rebuild_Review.html`
- `Client_Rebuild_Review.pdf`

For a revision review:

- `Client_Rebuild_Review_R1.html`
- `Client_Rebuild_Review_R1.pdf`

For a new campaign review with no inherited ad account:

- `Client_New_Campaign_Review.html`
- `Client_New_Campaign_Review.pdf`

The revision review should replace the prior review for client approval. It should keep clear lineage:

- What the inherited account started with.
- What `Advertising Report Card` rebuilt.
- What changed after client feedback.
- What still needs approval before launch.

The new campaign review should not imply there was an inherited account. It should show:

- What the website and intake sources support.
- What new campaign structure was built.
- Which claims, services, geos, and budgets need approval.
- What passed validation before Google Ads Editor review.

## Non-Canonical Outputs

Do not use these as the primary client-facing rebuild review format:

- DOCX.
- Pandoc-generated Word files.
- PPTX.
- Plain Markdown.

These formats can be used for internal notes, but they do not preserve the branded report layout well enough for client delivery.

## Builder

Use the presentation tool wrapper:

```bash
python3 presentations/tools/build_review_doc.py \
  --html clients/{agency}/{client}/build/{date}_account_rebuild/Client_Rebuild_Review.html \
  --pdf clients/{agency}/{client}/build/{date}_account_rebuild/Client_Rebuild_Review.pdf
```

The builder wraps the Chrome headless export flags that produced the accepted review PDF.

For a new campaign report, use:

```bash
python3 presentations/tools/build_initial_search_campaign.py \
  --agency agency_slug \
  --client client_slug \
  --display-name "Client Name" \
  --website https://example.com/ \
  --build-date YYYY-MM-DD \
  --location "United States|2840" \
  --service "Core Services" \
  --monthly-budget 3000
```

The one-shot builder creates the staging CSV, source artifacts, report HTML/PDF, visual audit folder, and `run_manifest.json`. To rebuild only the report from existing artifacts, use:

```bash
python3 presentations/tools/build_new_campaign_report.py \
  --client "Client Name" \
  --date "Month D, YYYY" \
  --staging-csv clients/{agency}/{client}/build/{date}_initial_search_build/Google_Ads_Editor_Staging_CURRENT.csv \
  --website-scan-json clients/{agency}/{client}/build/{date}_initial_search_build/website_scan.json \
  --service-catalog-json clients/{agency}/{client}/build/{date}_initial_search_build/service_catalog.json \
  --geo-strategy-json clients/{agency}/{client}/build/{date}_initial_search_build/geo_strategy.json \
  --source-attribution-json clients/{agency}/{client}/build/{date}_initial_search_build/source_attribution.json \
  --monthly-budget 3000 \
  --output-html clients/{agency}/{client}/build/{date}_initial_search_build/Client_New_Campaign_Review.html \
  --output-pdf clients/{agency}/{client}/build/{date}_initial_search_build/Client_New_Campaign_Review.pdf \
  --visual-audit-dir clients/{agency}/{client}/build/{date}_initial_search_build/new_campaign_visual_audit
```

The report builder can also read a one-shot manifest:

```bash
python3 presentations/tools/build_new_campaign_report.py \
  --manifest-json clients/{agency}/{client}/build/{date}_initial_search_build/run_manifest.json
```

If there is an approved cost-per-click planning range, include:

```bash
  --cpc-low 8 \
  --cpc-high 18
```

## Page Geometry

The standard report target is US Letter. CSS print units are deterministic enough for this workflow: the W3C CSS Values specification defines `1in` as `96px`, so US Letter maps to `816px x 1056px` before renderer scaling. Chrome export runs with no browser margins, so the HTML template owns all page padding, gutters, and safe areas.

Design against this box:

- Page box: `8.5in x 11in`.
- CSS page box: `816px x 1056px`.
- Minimum safe padding inside designed panels: `24px`.
- Minimum distance from meaningful text to a page edge or large panel edge: `32px`.
- No repeated module may force a page break unless a deterministic page-fit check has measured the next module against remaining page height.

## Design Rules

- Build the report in HTML and CSS first.
- Design must be dynamic, variable, and intelligent. A report may have 5 pages or 50 pages, and every page still needs to look intentional.
- Use client website screenshots, colors, typography feel, and visual tone as inputs.
- Present `Advertising Report Card` as the agency behind the work.
- Use `ARC` only for ownership-level campaign names and labels.
- Keep client identity in the ads, URLs, landing pages, and report context.
- Keep previous provider names out of repeated headers, campaign names, ad group names, ad copy, filenames, and page branding.
- Use previous provider names only in a controlled source attribution or before-and-after context.
- Use section header blocks with visual weight.
- Use subsection header blocks when the next content group is substantial, variable in length, or likely to start a new page.
- Repeat compact continuation headers when a module continues on a later page.
- Put section intro text inside the section header block.
- Put subsection intro text inside the subsection header block.
- Use strategy cards, insight cards, decision cards, representative ad previews, and approval checklists.
- Do not include thousands of keywords or every RSA variation in the client report.
- Do not put `break-inside: avoid` on grid, flex, or tall containers.
- Use `break-inside: avoid` only on leaf cards, small headers that must stay with their body, and table rows.
- Do not put `break-before: page` or `page-break-before: always` on repeated modules such as ad-copy cards, strategy cards, or continuation headers.
- Forced page breaks are allowed only after measured chunking logic confirms the next rendered page will contain meaningful content.

## Header System

Use three levels, based on what might happen after pagination:

- `section-header`: major report landmarks. These can start a new page and should look like a designed page opener.
- `subsection-header`: content groups inside a major section. Use this whenever the following content may start a new page.
- `continuation-header`: compact repeated context for a module that continues on a later page.
- `section-subtitle`: small local labels only. Do not use this before large grids, tables, ad-copy blocks, or any variable-length content.

The good pattern is a full-width block with an eyebrow, title, optional intro, spacing, and a left accent. The bad pattern is a lone text heading with a small rule that looks detached when it lands at the top of a PDF page.

Continuation headers are not page makers. They are context labels. A continuation header must have visible module content immediately following it on the same rendered page. A page that contains only a continuation header and background is a failed build.

Top-level sections flow naturally by default. A short section should continue on the current page when space is available. Starting every section on a new page is forbidden because it creates low-density pages in variable-length reports.

## Dynamic Layout Rules

- Long sections must be chunked into reviewable groups with repeated subsection headers.
- If a grid, table, or ad-copy module breaks across pages, the next page needs a lean `continued` header.
- Ad copy review should not be one endless sequence of ad group blocks.
- Dense tables need pre-table summary cards or subsection headers.
- Large repeated structures need visual indexes, badges, or continuation labels.
- The generator should choose section density based on count, not use one static layout for every account.
- A healthcare local-services account, ecommerce account, legal account, and national B2B account should share the same report grammar but not the same section density.
- No text or meaningful element may sit directly on a border, accent rule, page edge, or container edge. Internal padding is required.
- A short module should share a page with neighboring content when space allows. One small ad group per page is a failure unless the module visually fills the page.
- The generator must prevent low-density pages by measuring rendered output, not just trusting CSS.
- Final approval checklists should use a compact print layout. A last page with only a few small cards and a footer is not acceptable unless it contains a deliberate closing summary.
- Footers must not create their own page. If a footer cannot stay with meaningful final content, suppress it in print or use a true running footer implementation.

## Content Rules

The client-facing report must answer:

- What did we inherit?
- What did we rebuild?
- Why is this structure better?
- Which services, geos, copy claims, and landing pages need client approval?
- What changed in each revision round?
- What happens before launch?

Representative examples are preferred over exhaustive dumps.

Client-facing language must follow:

- `docs/CLIENT_FACING_LANGUAGE_RULES.md`

Use direct, evidence-led wording for non-technical readers. Do not use em dashes, `Why this matters:`, hype phrases, placeholder QA language, or contrived model-style labels.

## Quality Gates

Before delivery:

- Export the HTML to PDF through `presentations/tools/build_review_doc.py`.
- Run `presentations/tools/report_quality_audit.py` against the HTML before export.
- Run `presentations/tools/pdf_visual_audit.py` against the rendered PDF after export.
- Inspect every PDF page visually.
- Confirm no text overlap, clipping, orphan section headers, blank pages, or split cards.
- Confirm all RSA headlines are 30 characters or fewer.
- Confirm all RSA descriptions are 90 characters or fewer.
- Confirm all claims are supported by client intake, website evidence, account data, or approved strategy notes.
- Confirm source attribution rules were followed.
- Confirm the report matches the current staged CSV and validation report.
- Confirm client-facing language passes the do-not-use list in `docs/CLIENT_FACING_LANGUAGE_RULES.md`.

Audit command:

```bash
python3 presentations/tools/report_quality_audit.py \
  clients/{agency}/{client}/build/{date}_account_rebuild/Client_Rebuild_Review.html
```

Rendered PDF audit command:

```bash
python3 presentations/tools/pdf_visual_audit.py \
  clients/{agency}/{client}/build/{date}_account_rebuild/Client_Rebuild_Review.pdf \
  --pages-dir clients/{agency}/{client}/build/{date}_account_rebuild/pdf_visual_audit
```

## Sources

- Presentation builder wrapper: `presentations/tools/build_review_doc.py`
- Presentation audit wrapper: `presentations/tools/report_quality_audit.py`
- Design postmortem: `clients/therappc/thinkhappylivehealthy/docs/hitl_doc_design_postmortem_2026-04-28.md`
- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en
- Google responsive search ads: https://support.google.com/google-ads/answer/7684791?hl=en-EN
- MDN break-inside reference: https://developer.mozilla.org/en-US/docs/Web/CSS/break-inside
- MDN break-after reference: https://developer.mozilla.org/en-US/docs/Web/CSS/break-after
- MDN page-break-inside reference: https://developer.mozilla.org/en-US/docs/Web/CSS/page-break-inside
- MDN content breaks guide: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_multicol_layout/Handling_content_breaks_in_multicol_layout
- W3C CSS Values absolute lengths: https://www.w3.org/TR/css-values-3/#absolute-lengths
- WeasyPrint: https://weasyprint.org/
- Paged.js: https://github.com/pagedjs/pagedjs
