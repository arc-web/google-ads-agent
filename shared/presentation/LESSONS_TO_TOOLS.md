# Lessons to Tools

Every misstep from the THHL HITL document build (2026-04-28) is encoded here as a tool, file, or hard rule. Future client rebuilds use the tools - they do not re-discover the lesson.

| # | Misstep | Tool / Rule | Path |
|---|---------|-------------|------|
| 1 | kimi-k2 corrupted JSON output | Grader hardcoded to `gemini-2.5-flash` via `GRADER_MODEL` constant | `shared/copy_engine/editor/grader.py` |
| 2 | 7-sweep raw on 30-char headlines | Role-aware SYSTEM_PROMPT (geo / credential / keyword_match etc) with neutral-70 scoring on inapplicable dimensions | `shared/copy_engine/editor/grader.py` |
| 3 | pandoc Word export lost branding | Process doc forbids pandoc for client docs. HTML+Chrome only | `docs/GOOGLE_ADS_AGENT_PROCESS.md` stage 9 |
| 4 | pptxgenjs same outcome | Same rule | `docs/GOOGLE_ADS_AGENT_PROCESS.md` stage 9 |
| 5 | Strategy items rendered as prose | Process doc spec lists `.strategy-card` with sc-title + sc-body + sc-why as the required pattern | `docs/GOOGLE_ADS_AGENT_PROCESS.md` stage 9 |
| 6 | Cards split mid-card | `break-inside: avoid` rule for leaf cards in canonical CSS | `shared/presentation/page_break_rules.css` |
| 7 | Table rows split mid-row | `tr { break-inside: avoid }` in canonical CSS | `shared/presentation/page_break_rules.css` |
| 8 | Section title + intro orphan, blank below | Forbidden-rules comment block in canonical CSS. Section header HTML pattern requires intro INSIDE `.section-header` | `shared/presentation/page_break_rules.css`, `shared/presentation/section_header.css` |
| 9 | Tall card containers deferred = blank pages | `.card` and `.ag-review-block` explicitly listed as forbidden in canonical CSS | `shared/presentation/page_break_rules.css` |
| 10 | Section headers visually weak | Section header block: gradient bg, 5px teal left-border, eyebrow+title+intro in one container | `shared/presentation/section_header.css` |
| 11 | 9 ad group blocks looked identical | Process doc requires numbered badge (01-N) on each `.ag-review-header` | `docs/GOOGLE_ADS_AGENT_PROCESS.md` stage 9 |
| 12 | Char-limit violations shipped to client doc | `CharLimitError` raised at generation. `assert_rsa_clean()` is hard gate before CSV write | `shared/copy_engine/editor/char_limit_enforcer.py` |
| 13 | Truncation bug "Psychoeducational Evaluation H" | Singular + plural forms both mapped in `headline_phrase()` replacement dict. Unit test pattern | `shared/copy_engine/search/headlines.py` |
| - | Chrome PDF flag set easy to forget | Single function `export_pdf()` wraps the 6 required flags | `shared/presentation/build_review_doc.py` |
| - | PDF rebuild iteration loop wasted time | One canonical CSS file means new docs do not re-discover page-break bugs | `shared/presentation/page_break_rules.css` |

## How to use

For a new client review document:

```python
from shared.presentation import export_pdf
from shared.copy_engine.editor.char_limit_enforcer import assert_rsa_clean

# Before writing any RSA to CSV:
assert_rsa_clean(headlines, descriptions, path1, path2)

# After the review HTML is final:
export_pdf(
    html_path="clients/AGENCY/CLIENT/build/DATE_account_rebuild/Client_Rebuild_Review.html",
    pdf_path="clients/AGENCY/CLIENT/build/DATE_account_rebuild/Client_Rebuild_Review.pdf",
    mirror_desktop=True,
)
```

In the HTML `<style>` block, paste the contents of:

- `shared/presentation/page_break_rules.css`
- `shared/presentation/section_header.css`

Or `@import` them if the HTML is served from a path that can resolve relative URLs.

## Reference template

The canonical reference for what a finished stage 9 deliverable looks like:

`clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/Client_Rebuild_Review.html`

Naming convention: every client-facing deliverable in `build/{date}_account_rebuild/` uses Pascal_Snake_Case (`Client_Rebuild_Review.html`, `Google_Ads_Editor_Staging_CURRENT.csv`). Internal artifacts use `snake_case.json` / `snake_case.csv`. See output contract in `docs/GOOGLE_ADS_AGENT_PROCESS.md`.

Mirror to Desktop is opt-in (`--mirror-desktop` flag). Default off - canonical lives in repo, Desktop stays clean.
