# New Campaign Report Component Map

Date: 2026-05-05

Source standards:

- [HTML/PDF Client Report Standard](../HTML_PDF_CLIENT_REPORT_STANDARD.md)
- [Report System Automation Audit](REPORT_SYSTEM_AUTOMATION_AUDIT_2026-05-04.md)

## Report Type

`Client_New_Campaign_Review` is used when a campaign is being staged for launch from source evidence, website facts, service priorities, and Google Ads Editor output. It must not imply there is inherited account history unless that history exists and the report type changes.

## Page Index

1. Cover: identifies the report, business, date, and review purpose.
2. Overview: previews what needs review before launch.
3. Campaign structure: shows the current launch shape and later expansion paths.
4. Ad groups: lists the services or intent groups staged for ads.
5. Ad copy pages: one ad group per page, with preview, headlines, descriptions, and a compact confirmation prompt.
6. Regional targeting: lists staged locations, city or ZIP review needs, and exclusions.
7. Budget pacing: explains monthly budget, daily average, and expected pacing.
8. Budget learning: explains why spend may shift as performance data becomes clearer.
9. Approval summary: compact final confirmation for ad groups, ads, regional targeting, and budget.

## Component Map

### Section Header

Purpose: orient the reader at the top of each page.

Rules:

- Use one strong title and one short explanatory sentence.
- Do not create header-only pages.
- Do not use internal QA language or placeholder labels.

### Central Diagram

Purpose: show one main structural idea on a page.

Rules:

- Use at most one major visual per page.
- For new campaign structure, show the active launch shape first.
- Future splits must be labeled as future options, not active launch campaigns.
- Keep the diagram short enough to leave room for the explanation strip.

### Explanation Strip

Purpose: explain the diagram without overloading the diagram itself.

Required campaign-structure notes:

- `Why start together`
- `What triggers a split`
- `What changes after split`

Rules:

- Exactly three notes for the campaign-structure page.
- Each note should answer one reader question.
- Do not turn the strip into a second diagram.

### Table

Purpose: make staged detail easy to scan and approve.

Rules:

- Tables should not split critical ad-copy content across pages.
- Regional targeting must support states, cities, ZIPs, exclusions, and long location lists.
- City and ZIP review items should use separate rows.

### Ad Preview

Purpose: show how the ad direction reads before the full asset table.

Rules:

- One ad group per ad-copy page.
- Show preview, headline table, description table, and a compact confirmation line.
- Do not render service-logic research cards on client-facing ad-copy pages.

### Confirm Strip

Purpose: make each section's review action clear.

Rules:

- Use compact spacing.
- Keep prompts direct, such as `Please confirm`.
- Do not allow a confirm strip to overflow onto a mostly blank page.

### Approval Summary

Purpose: give a final compact approval checklist.

Rules:

- Keep it short and elegant.
- Summarize only the core approval categories: ad groups, ads, regional targeting, and budget.
- Do not include dense notes that repeat the full report.

### Visual Audit Output

Purpose: prove the PDF rendered correctly after HTML generation.

Rules:

- Store page images in the build folder for visual review.
- Fail mostly blank pages, orphan headers, and orphan confirm strips.
- Review the campaign structure, ad copy, regional targeting, budget, and approval pages after each generator change.

## Style Rules

- HTML is the editable source of truth, PDF is exported from HTML.
- One page should carry one main job.
- Use one major visual per page at most.
- Do not put internal reasoning cards in client-facing pages.
- Do not show `Who this is for`, `What they are buying`, `Why it matters`, or `What to confirm` inside ad-copy pages.
- Do not create orphan confirm strips.
- Do not create header-only pages.
- Do not create mostly blank overflow pages.
- Do not use Search partners, broad match, exact match, PMAX, live upload, or API language in new campaign reports unless explicitly approved for that report.

## Automation Requirements

- `presentations/tools/report_quality_audit.py` must fail when service-logic cards render inside an ad-copy page.
- New campaign report tests must prove the campaign-structure page includes the three-note explanation strip.
- New campaign report tests must prove service-logic research remains internal.
- Visual audits must be run after regenerating any final client-facing PDF.
