# Presentation Build Instructions

This is the first place to look when building or revising a client-facing presentation report.

## Folder Responsibilities

- `presentations/`: build instructions, standards, examples, templates, and command wrappers.
- `presentations/tools/`: commands a human should run.
- `shared/presentation/`: reusable implementation details and compatibility imports.
- `clients/{agency}/{client}/build/{date}_account_rebuild/`: generated client-specific HTML, PDF, previews, audits, and contact sheets.

Generated client files stay with the client build. The instructions and commands stay here.

## Canonical Flow

1. Edit or generate the source HTML in the client build folder.
2. Prepare client-facing HTML if the source was generated from campaign data.
3. Convert the prepared HTML into fixed-page HTML.
4. Export fixed-page HTML to PDF with Chrome headless.
5. Run static HTML audit.
6. Run rendered PDF visual audit.
7. Inspect the rendered page images or contact sheet before sending.

## Think Happy Live Healthy Current Build

Editable source of truth:

```bash
clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28_fixed.html
```

Current PDF:

```bash
clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28_fixed.pdf
```

## Commands

From the repo root:

```bash
python3 presentations/tools/build_fixed_campaign_review.py \
  --input-html clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28_prepared.html \
  --output-html clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28_fixed.html \
  --output-pdf clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28_fixed.pdf
```

Export any finished HTML to PDF:

```bash
python3 presentations/tools/build_review_doc.py \
  --html clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28_fixed.html \
  --pdf clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28_fixed.pdf
```

Build a client-facing revisions review from structured feedback:

```bash
python3 presentations/tools/build_revision_review.py \
  --client "Think Happy Live Healthy" \
  --date "April 29, 2026" \
  --feedback-json clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/client_feedback_classified.json \
  --decision-log clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/revision_decision_log.csv \
  --validation-json clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/THHL_Search_Services_Editor_Staging_REV1_validation.json \
  --targeting-json clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/targeting_spec.json \
  --staging-csv clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/THHL_Search_Services_Editor_Staging_REV1.csv \
  --output-html clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_revisions_2026-04-29.html \
  --output-pdf clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_revisions_2026-04-29.pdf \
  --visual-audit-dir clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/revision_visual_audit
```

Build a client-facing new campaign review when there is no inherited ad account:

Run the full one-shot initial Search build:

```bash
python3 presentations/tools/build_initial_search_campaign.py \
  --agency therappc \
  --client client_slug \
  --display-name "Client Name" \
  --website https://example.com/ \
  --build-date 2026-05-04 \
  --location "United States|2840" \
  --service "Core Services" \
  --monthly-budget 3000
```

The one-shot command scans the site, writes reviewed source artifacts, builds a paused Google Ads Editor staging CSV, validates it, exports the HTML/PDF report, runs audits, and writes `run_manifest.json`.

Build only the client-facing new campaign review from existing artifacts:

```bash
python3 presentations/tools/build_new_campaign_report.py \
  --client "Mindful Mental Health Counseling" \
  --date "May 2, 2026" \
  --staging-csv clients/therappc/nyc_mindful_mental_health_counseling/build/2026-05-02_initial_search_build/Google_Ads_Editor_Staging_CURRENT.csv \
  --website-scan-json clients/therappc/nyc_mindful_mental_health_counseling/build/2026-05-02_initial_search_build/website_scan.json \
  --service-catalog-json clients/therappc/nyc_mindful_mental_health_counseling/build/2026-05-02_initial_search_build/service_catalog.json \
  --geo-strategy-json clients/therappc/nyc_mindful_mental_health_counseling/build/2026-05-02_initial_search_build/geo_strategy.json \
  --source-attribution-json clients/therappc/nyc_mindful_mental_health_counseling/build/2026-05-02_initial_search_build/source_attribution.json \
  --monthly-budget 3000 \
  --output-html clients/therappc/nyc_mindful_mental_health_counseling/build/2026-05-02_initial_search_build/Client_New_Campaign_Review.html \
  --output-pdf clients/therappc/nyc_mindful_mental_health_counseling/build/2026-05-02_initial_search_build/Client_New_Campaign_Review.pdf \
  --visual-audit-dir clients/therappc/nyc_mindful_mental_health_counseling/build/2026-05-02_initial_search_build/new_campaign_visual_audit
```

Optional CPC planning fields:

```bash
  --cpc-low 8 \
  --cpc-high 18
```

Build from a one-shot run manifest:

```bash
python3 presentations/tools/build_new_campaign_report.py \
  --manifest-json clients/{agency}/{client}/build/{date}_initial_search_build/run_manifest.json
```

Run static HTML audit:

```bash
python3 presentations/tools/report_quality_audit.py \
  clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28_fixed.html
```

Run static HTML audit for the new-campaign example:

```bash
python3 presentations/tools/report_quality_audit.py \
  clients/therappc/nyc_mindful_mental_health_counseling/build/2026-05-02_initial_search_build/Client_New_Campaign_Review.html
```

Run rendered PDF visual audit:

```bash
python3 presentations/tools/pdf_visual_audit.py \
  clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28_fixed.pdf \
  --pages-dir clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/fixed_visual_audit
```

Run rendered PDF visual audit for the new-campaign example:

```bash
python3 presentations/tools/pdf_visual_audit.py \
  clients/therappc/nyc_mindful_mental_health_counseling/build/2026-05-02_initial_search_build/Client_New_Campaign_Review.pdf \
  --pages-dir clients/therappc/nyc_mindful_mental_health_counseling/build/2026-05-02_initial_search_build/new_campaign_visual_audit
```

## Rules That Matter

- HTML is the editable source of truth.
- PDF is exported from HTML, not hand-edited.
- Use Chrome headless through `presentations/tools/build_review_doc.py`.
- Keep generated outputs in the client build folder.
- Keep presentation build instructions in `presentations/`.
- Do not use DOCX, PPTX, or Markdown as the client-facing rebuild review source.
- Use a new campaign review, not a rebuild review, when there is no inherited Google Ads account evidence.
- Do not use em dashes in client-facing reports.
- Do not include draft QA language in client-facing reports.
- Run both static and rendered audits before sending a PDF.

## Sources

- Google Ads Editor CSV import: https://support.google.com/google-ads/editor/answer/30564
- Google Ads Editor CSV columns: https://support.google.com/google-ads/editor/answer/57747
- Google responsive search ads: https://support.google.com/google-ads/answer/7684791
- MDN break-inside: https://developer.mozilla.org/en-US/docs/Web/CSS/break-inside
- W3C CSS absolute lengths: https://www.w3.org/TR/css-values-3/#absolute-lengths
