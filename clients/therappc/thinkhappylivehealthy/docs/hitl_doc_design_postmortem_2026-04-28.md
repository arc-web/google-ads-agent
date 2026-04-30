# THHL Client-Facing Review Doc - Design Postmortem

Date: 2026-04-28
Client: Think Happy Live Healthy (therappc)
Deliverable: Branded HTML + PDF campaign review document for client approval call

This document captures every misstep made during the design pass on the THHL HITL document and the fix that resolved each one. It is preserved so future client rebuilds skip the same mistakes.

## Misstep Map

### 1. Grader corrupted JSON output

- What happened: First grader pass routed through `kimi-k2`. The model emitted literal tokens like `"suggestions":AITT"` mid-JSON, which broke the parser.
- Root cause: kimi-k2 produces structured-output tokens that are not strict JSON.
- Fix: Routed all grader calls to `google/gemini-2.5-flash` via `GRADER_MODEL` constant in `shared/copy_engine/editor/grader.py`. Added a list-unwrap step in `_parse_response` because gemini sometimes wraps a single result in a list.
- Lesson: Use `gemini-2.5-flash` for any JSON-structured output. Reserve `kimi-k2` for free-form generation.

### 2. Grader gave unfair scores to short-form headlines

- What happened: Geo headlines like "Ashburn VA" and credential headlines like "Board-Certified Psychiatry" graded poorly because the 7-sweep framework expected proof, CTAs, and emotion in every asset.
- Root cause: The 7-sweep framework was built for long-form copy and applied raw to 30-character headlines.
- Fix: Built a role-aware grading rubric in the SYSTEM_PROMPT. Each headline is classified into a role (keyword_match, geo, credential, benefit, question, cta, proof). Score 70 (neutral) on inapplicable dimensions. Exclude neutral dimensions from the weighted average. K-Readiness Testing tested at B/84 after the fix.
- Lesson: 7-sweep framework is not portable to ad assets without a role layer. Headlines and descriptions are graded against different bars.

### 3. Pandoc Word doc lost all branding

- What happened: First attempt at a portable deliverable was a `.docx` via pandoc. It rendered as plain black-on-white text with no brand colors, no card layouts, no callouts.
- Root cause: pandoc strips CSS-driven styling. It only preserves what Word/LibreOffice can natively render.
- Fix: Abandoned pandoc. Switched to HTML-first design.
- Lesson: Pandoc is for text content, not branded review documents. Never use it for client-facing material.

### 4. PowerPoint via pptxgenjs lost the same branding

- What happened: After the Word failure, tried `pptxgenjs`. Same outcome - generic slide layouts, no design fidelity.
- Root cause: PPTX is a layout-driven format. Web-style cards, gradients, CSS-driven spacing, and HTML structure do not map cleanly to slide objects.
- Fix: Abandoned PPTX. Stayed on HTML.
- Lesson: HTML + Chrome headless `--print-to-pdf` is the canonical path for branded review documents going forward.

### 5. Strategy cards rendered as prose paragraphs instead of itemized cards

- What happened: First pass on the methodology section turned itemized strategy points into flowing prose paragraphs. The user explicitly objected.
- Root cause: LLM defaults to prose when given list-shaped content without explicit structure rules.
- Fix: Rewrote the section as discrete `.strategy-card` elements with `sc-title` + `sc-body` + `sc-why` callout. Six cards in a 2-column grid.
- Lesson: Itemized inputs should produce itemized outputs. Cards beat paragraphs when items are independently meaningful.

### 6. Metric cards split mid-card across page breaks

- What happened: PDF page 2 ended with the top half of an insight card; page 3 started with the bottom half. Same for problem cards.
- Root cause: No `break-inside: avoid` on `.insight-card` or `.problem-card`.
- Fix: Added `break-inside: avoid` and `page-break-inside: avoid` to all leaf card classes.
- Lesson: Every visually self-contained card needs the break-inside rule.

### 7. Table rows split mid-row

- What happened: Taxonomy and intent layer tables had rows splitting across page boundaries.
- Root cause: No `tr { break-inside: avoid }` rule.
- Fix: Added `tr { break-inside: avoid; page-break-inside: avoid; }` globally.
- Lesson: Always apply break-inside to `tr`. Cheap rule, prevents a common bug.

### 8. Section title plus intro paragraph rendered alone, then blank space

- What happened: Several section pages showed only the title and one intro line, then a blank rest-of-page. The next section's content did not start until page +2.
- Root cause: Two compounding mistakes. (a) `break-inside: avoid` on grid containers like `.strategy-grid` caused the entire grid to defer to the next page when it could not fit on the remaining space. (b) The intro paragraph was a direct child of the section, so it was not glued to the deferred grid - it rendered orphan above the page break.
- Fix: Removed `break-inside: avoid` from all grid and flex containers. Only leaf cards keep that rule. Added `break-after: avoid` to `.section-header` so the entire header block (eyebrow + title + intro) glues to whatever follows.
- Lesson: Never apply `break-inside: avoid` to grid containers. Grids must be allowed to break between rows. Section intro paragraphs go inside the section header block, never as orphan `<p>` after the title.

### 9. Ad Copy Review and Human Review sections had blank pages

- What happened: PDF showed full blank pages between the title of the Ad Copy Review section and the first ad group block. Same on Human Review.
- Root cause: `.ag-review-block` (~400px tall) and `.card` (the checklist card was ~620px) had `break-inside: avoid`. When near a page boundary, the entire block deferred to the next page, leaving the title and intro orphaned with blank space below.
- Fix: Removed `.card` and `.ag-review-block` from the break-inside avoid list. Added `.ag-review-header` (small) so the header bar always sticks to the body of its block.
- Lesson: Tall containers (>~300px) cannot have `break-inside: avoid`. They must be allowed to break naturally. Apply the avoid rule only to the small leaf header that needs to stay with the body.

### 10. Section headers looked weak

- What happened: Section labels were plain 10px uppercase text. Section titles were 1.5em with a thin border-bottom. Looked like draft-quality typography.
- Root cause: No visual block treatment. Just stacked text elements.
- Fix: Wrapped each section's label, title, and intro in a `.section-header` block. Warm gradient background, 5px teal left-border accent, teal-dark eyebrow text, 1.65em sage-dark title. Intro text lives inside the block.
- Lesson: Section markers need visual mass to function as landmarks in a long document.

### 11. All 9 ad group blocks looked identical with no scannable landmark

- What happened: Sage-dark header bar was repeated 9 times. Hard to scan to a specific ad group when the document is 3+ pages of ad copy.
- Root cause: No per-block visual differentiation.
- Fix: Added a blush-colored 01-09 number badge to each `.ag-review-header`. Numbered badges become scan landmarks.
- Lesson: Repeated structures need a per-instance visual tag for fast scanning.

### 12. Headline H9 included in copy review while being 33 characters (over limit)

- What happened: Copy review section included "Skilled Psych Nurse Practitioners" (33 chars) flagged red. Five other violations were also present: Child Psych Testing H4 (31), Gifted H6 (32), K-Ready H4 (32), Psychoeducational D1 (92), Autism D1 (92). User flagged this as unacceptable - violations should not be in a client-facing document at all.
- Root cause: Generator did not enforce the 30-char hard cap before writing the CSV. Violations were caught later as flags rather than fixed at source.
- Fix: Replaced all 6 violations with under-limit equivalents in both the CSV and the HTML. New headlines: Psychiatry H9 "Psych Nurse Practitioners" (25), Child Psych Testing H4 "Child Psych Assessments" (23), Gifted H6 "NoVA Gifted Testing" (19), K-Ready H4 "School Readiness Near You" (25). D1 descriptions trimmed to 78 and 83 chars.
- Lesson: Hard 30-char and 90-char caps must be enforced at generation time, not at review time. A violation must be a generator error, not a flagged item in the client document.

### 13. Truncation bug "Psychoeducational Evaluation H"

- What happened: Generator produced "Psychoeducational Evaluation H" - a dangling H character at position 30. All four Psychoeducational layers had this broken headline.
- Root cause: `keyword_roots()` returns the singular form "Psychoeducational Evaluation". The replacement dict in `headline_phrase()` only mapped the plural "Psychoeducational Evaluations" to a shorter form. The singular hit `truncate(30)` and got cut mid-word.
- Fix: Added a singular key `"Psychoeducational Evaluation": "Learning Evaluation"` to the replacement dict.
- Lesson: When normalizing long service names, map both singular and plural forms in the replacement dict. truncate() is a last resort, never the primary way to fit a long phrase into 30 chars.

## Principles for Future Client Docs

- Design in HTML first. PDF via Chrome headless `--print-to-pdf`. Never pandoc, never pptxgenjs for branded review documents.
- `break-inside: avoid` belongs only on leaf cards and `tr`. Never on grid or flex containers. Never on tall card containers like `.card` or `.ag-review-block`.
- Section intro paragraphs go inside the section header block, never as orphan `<p>` after the title.
- All headlines must be enforced at 30 characters in the generator, not flagged at review time.
- Grader uses `gemini-2.5-flash` for JSON output. Role-aware scoring for short-form ad assets. Never raw 7-sweep on 30-char headlines.
- Repeated structures get per-instance visual tags (numbered badges) so the reader can scan to a specific item.
- Section header blocks need visual mass. Eyebrow + title + intro inside a styled container. Not three stacked `div` elements.

## Files Touched

- `clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/Client_Rebuild_Review.html` - canonical reference template
- `clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/Client_Rebuild_Review.pdf` - exported via `shared/presentation/build_review_doc.py`
- `/Users/home/ai/agents/ppc/google_ads_agent/shared/copy_engine/editor/grader.py` - role-aware grader rubric
- `/Users/home/ai/agents/ppc/google_ads_agent/clients/therappc/thinkhappylivehealthy/campaigns/THHL_Search_Campaign_2026-04-28.csv` - 6 violations fixed
- `/Users/home/ai/agents/ppc/google_ads_agent/docs/GOOGLE_ADS_AGENT_PROCESS.md` - stage 9 added for presentation generation
