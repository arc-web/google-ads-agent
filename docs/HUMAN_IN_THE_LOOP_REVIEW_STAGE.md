# Human-In-The-Loop Review Stage

Date: 2026-04-28

## Purpose

The human-in-the-loop review stage creates a client-facing approval document before any Google Ads Editor CSV is posted.

This document is not a technical dump. It explains what changed, why it changed, what the client should review, and what decisions are needed before launch.

## Audience

Primary audience:

- Client decision-makers.
- Account strategists.
- Media buyers who need approval before staging or posting.

Secondary audience:

- Internal implementation team.
- QA reviewer.

## Required Inputs

- Google Ads Editor staging CSV.
- Campaign taxonomy.
- Search term analysis.
- Location or geo strategy.
- RSA copy matrix.
- Validation report.
- Client website screenshots or brand samples.
- Client website URL.

## Required Outputs

Client-facing:

- `Client_Rebuild_Review.html`
- `Client_Rebuild_Review.pdf`

Internal:

- `human_review.md`
- `validation_report.json`
- Optional technical appendix.

## Document Structure

### 1. Cover

Include:

- Client name.
- Website URL.
- Prepared-by agency: `Advertising Report Card`.
- Report title.
- Review date.
- Short summary of what is ready for review.
- Brand-inspired color and image treatment from the client website.

### 2. Executive Summary

Show:

- What we started with.
- What we rebuilt.
- What is ready for Google Ads Editor staging.
- What requires approval.

Use concise bullets and 3 to 5 metrics.

### 3. Before And After

Explain the strategic improvement:

- Before: scattered campaign logic, weak ad group separation, inconsistent keywords, weak copy, unclear staging checks.
- After: service taxonomy, intent-layer ad groups, phrase-only keywords, geo targeting, RSA quality gates, validation, human review.

Avoid attacking prior work. Make the improvement clear and professional.

If a previous provider name appears in the source export, mention it only when needed to explain the starting point. Do not repeat it through the document.

### 4. Campaign Architecture

Show the ad group naming system:

- `Service - Audience/Category - General`
- `Service - Audience/Category - Local`
- `Service - Audience/Category - City`
- `Service - Audience/Category - State`

Explain:

- General captures core service searches.
- Local captures near-me behavior.
- City captures named-city intent.
- State captures state or regional modifiers.

Show examples only. Do not list every ad group if the build has dozens or hundreds.

### 5. Keyword Strategy

Show:

- Phrase match only.
- No broad match.
- No exact match unless separately approved later.
- Singular and plural variants.
- Service and audience variants.
- City and state variants.
- Search-term-informed expansions.

Include sample keywords per intent layer, not a full keyword dump.

### 6. Targeting Strategy

Show:

- Core locations.
- Expansion locations.
- Radius or regional targets.
- Bid adjustment approach.
- How future splits will be decided.

Use city, county, ZIP, and state layering where relevant.

### 7. Ad Copy Review

Show actual RSA examples:

- Rendered ad preview style.
- Headline list for review.
- Description list for review.
- Final URL and display paths.

Show 3 to 6 representative ad groups, not every ad group.

### 8. Future Optimization Plan

Explain how the campaign can split over time:

- Split by winning service category.
- Split by high-performing geography.
- Split high-volume near-me campaigns.
- Expand into ZIP-level campaigns only when data supports it.

### 9. Approval Checklist

Ask the client to approve or comment on:

- Service categories.
- Excluded services.
- Location coverage.
- Landing pages.
- Ad claims and copy.
- Budget and staging readiness.

### 10. Appendix

Keep appendix light:

- Validation summary.
- Data sources.
- Google Ads Editor staging notes.
- Source links.

## Design Standard

The review document should:

- Be designed in HTML first and exported to PDF through the canonical Chrome headless builder.
- Treat the HTML as the source of truth for future revision rounds.
- Be dynamic, variable, and intelligent. The layout must adapt to report size, section density, industry, and the amount of evidence.
- Present `Advertising Report Card` as the agency behind the work.
- Match the client brand loosely through color, typography feel, and selected screenshots.
- Stay highly readable.
- Avoid dense tables.
- Avoid thousands of keywords or full RSA dumps.
- Use callouts, summary cards, and short examples.
- Use substantial subsection headers before any variable-length content group that may start a PDF page.
- Use compact continued headers when cards, tables, ad-copy blocks, or repeated modules continue onto another page.
- Keep meaningful text away from borders, accent rules, and container edges with visible internal padding.
- Include one technical appendix at most.
- Keep client-facing content calm, clear, and approval-oriented.
- Keep previous provider names out of headers, repeated body sections, sample campaign names, sample ad group names, and filenames.
- Avoid pandoc, Word, DOCX, and PPTX as the branded client-facing report path.

## Quality Gates

Before delivery:

- Export the HTML to PDF.
- Run `shared/presentation/report_quality_audit.py` against the HTML before PDF export.
- Inspect every PDF page visually.
- Fix layout issues before sharing.
- Confirm no text overlaps or clips.
- Confirm tables have padding and readable line spacing.
- Confirm screenshots are not distorted.
- Confirm every claim in the document is supported by the CSV, reports, website, or local strategy doc.
- Confirm previous provider names appear only in approved source attribution context.
- Confirm the PDF was generated through `shared/presentation/build_review_doc.py`.

## Reference Sources

- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747?hl=en
- Google responsive search ads: https://support.google.com/google-ads/answer/7684791?hl=en-EN
- Google geo targets: https://developers.google.com/google-ads/api/data/geotargets
- Repo HTML/PDF report standard: `docs/HTML_PDF_CLIENT_REPORT_STANDARD.md`
- Canonical PDF builder: `shared/presentation/build_review_doc.py`
