"""
shared.presentation

Stage 9 of the Google_Ads_Agent pipeline: build the client-facing
campaign review document (HTML + PDF) after the staging CSV is final.

Modules:
- build_review_doc: Chrome headless PDF export with canonical flags.

Static assets (copy or @import into review HTML):
- page_break_rules.css: page-break ruleset with the bug-prevention
  comments baked in. Single source of truth.
- section_header.css: section header block treatment + the required
  HTML structure (intro lives INSIDE the header block).

See:
- docs/GOOGLE_ADS_AGENT_PROCESS.md stage 9 for the spec.
- clients/therappc/thinkhappylivehealthy/docs/hitl_doc_design_postmortem_2026-04-28.md
  for every lesson encoded in these tools.
"""

from .build_review_doc import (
    CHROME_BIN,
    PDF_FLAGS,
    PDFBuildError,
    export_pdf,
)

__all__ = ["CHROME_BIN", "PDF_FLAGS", "PDFBuildError", "export_pdf"]
