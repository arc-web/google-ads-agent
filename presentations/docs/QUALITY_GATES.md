# Presentation Quality Gates

## Required Gates

A client-facing PDF is not deliverable until all gates pass.

## Gate 1: Static HTML Audit

Command:

```bash
python3 presentations/tools/report_quality_audit.py path/to/report.html
```

Must pass:

- `0 errors`.
- Warnings reviewed and documented.

## Gate 2: PDF Export

Command:

```bash
python3 presentations/tools/build_review_doc.py \
  --html path/to/report.html \
  --pdf path/to/report.pdf
```

Must pass:

- PDF exists.
- Page size is Letter unless explicitly configured otherwise.
- No browser headers or footers.

## Gate 3: Rendered Visual Audit

Command:

```bash
python3 presentations/tools/pdf_visual_audit.py \
  path/to/report.pdf \
  --pages-dir path/to/rendered_pages \
  --min-content-ratio 0.055
```

Must pass:

- `0 failures`.
- Every page has meaningful vertical span.
- No footer-only pages.
- No continuation-only pages.

## Gate 4: Manual Contact Sheet Review

Review every page as a thumbnail sheet.

Look for:

- Odd blank space.
- Clipped text.
- Tiny unreadable tables.
- Overgrown paragraphs.
- Broken visual hierarchy.
- Pages that do not explain why they exist.

## Gate 5: Client-Facing Language

Forbidden:

- Internal QA notes.
- Draft warnings.
- `Why this matters:`
- `Sweep highlights`
- Hype language.
- Em dashes.
- Unsupported service claims.
- Red exact-limit flags.

## Gate 6: Claim Scope

Confirm:

- Services are currently available.
- Age ranges are correct.
- Insurance language is approved.
- Location claims match actual service area.
- Landing pages match ad group intent.
- Old provider names are not repeated.
- ARC appears only where ownership or agency attribution is needed.

## Gate 7: Source Alignment

Every claim should map to at least one source:

- Client intake.
- Website.
- Google Ads account data.
- Analytics or reporting data.
- Approved client feedback.

## Current Known Thresholds

- Visual audit `--min-content-ratio`: `0.055` for fixed campaign review PDFs.
- Page size: US Letter.
- CSS page model: `8.5in x 11in`.
- CSS absolute length basis: `1in = 96px`.

## Sources

- W3C CSS absolute lengths: https://www.w3.org/TR/css-values-3/#absolute-lengths
- MDN page-break-inside: https://developer.mozilla.org/en-US/docs/Web/CSS/page-break-inside
