# AI Reasoning Gates

Date: 2026-04-28

## Purpose

`Google_Ads_Agent` should not use AI reasoning for every step. The efficient path is to use AI only where judgment is needed, then hand the result to deterministic scripts for build, validation, presentation preparation, and PDF export.

## AI Reasoning Required

Use AI reasoning for:

- Interpreting client intake, constraints, and contradictions.
- Mapping website evidence to campaign strategy.
- Deciding when historical account data is reliable versus weak.
- Creating or revising campaign architecture when client feedback introduces nuance.
- Generating first-pass ad copy candidates.
- Producing qualitative copy-grade notes when structured grader output is missing.
- Explaining tradeoffs for human review.

## Deterministic Script Required

Do not use AI reasoning for:

- Character limit enforcement.
- Removing violation language from client-facing reports.
- Blocking pending copy grades.
- Inserting already-computed copy grades.
- Applying section, subsection, and continuation-header rules.
- Running presentation quality audit.
- Exporting HTML to PDF.
- Checking for old provider tokens.
- Checking campaign naming patterns.
- Checking Google Ads Editor CSV schema.

These steps must be repeatable through scripts.

## Current Presentation Pipeline

1. Generate or update review HTML from structured campaign data.
2. Run `shared/presentation/prepare_client_review_html.py`.
3. Run `shared/presentation/report_quality_audit.py`.
4. Export PDF through `shared/presentation/build_review_doc.py`.
5. Render selected pages to PNG for visual QA.

Example:

```bash
python3 shared/presentation/prepare_client_review_html.py \
  --input-html clients/{agency}/{client}/build/{date}_account_rebuild/Client_Rebuild_Review.html \
  --output-html clients/{agency}/{client}/build/{date}_account_rebuild/Client_Rebuild_Review_prepared.html \
  --output-pdf clients/{agency}/{client}/build/{date}_account_rebuild/Client_Rebuild_Review_prepared.pdf
```

## Hard Client-Facing Blocks

The report quality audit fails if client-facing HTML includes:

- Draft violation copy such as `Red counts are over the character limit`.
- `flagged for rewrite`.
- `Run full sweep for grade`.
- `Why this matters:`.
- Em dashes.
- Pending copy-grade tags in rendered content.

If those appear, the issue is not a client-report revision. It is a generation or preparation pipeline failure.

## Sources

- Google responsive search ads: https://support.google.com/google-ads/answer/7684791?hl=en-EN
- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564?hl=en
- MDN break-inside reference: https://developer.mozilla.org/en-US/docs/Web/CSS/break-inside
- MDN break-after reference: https://developer.mozilla.org/en-US/docs/Web/CSS/break-after
