from __future__ import annotations

from pathlib import Path

from shared.presentation.client_language_rules import audit_client_email_file, audit_client_email_text
from shared.presentation.report_quality_audit import audit_html


def test_report_language_audit_blocks_banned_phrases_and_em_dash(tmp_path: Path) -> None:
    html = tmp_path / "bad_report.html"
    html.write_text(
        """
<html><body>
<section class="section"><div class="section-header"><h1>Review</h1></div>
<p>Why this matters: this would unlock growth — fast.</p>
</section>
<div class="subsection-header">Detail</div>
<div class="continuation-header">More</div>
</body></html>
""",
        encoding="utf-8",
    )

    findings, summary = audit_html(html)

    assert summary["errors"] >= 2
    assert {finding.code for finding in findings} >= {
        "presentation.client_facing_draft_language",
        "presentation.em_dash",
    }


def test_email_language_audit_blocks_robotic_markdown_and_report_boilerplate() -> None:
    findings = audit_client_email_text(
        """
Subject: Search terms

**Search Term Questions**
The attached PDF summarizes the review.
No changes are being pushed live.
"""
    )

    codes = {finding.code for finding in findings}
    assert "email.markdown_clutter" in codes
    assert "email.robotic_or_report_boilerplate" in codes
    assert "email.search_term_boilerplate" in codes


def test_email_language_audit_blocks_em_dash() -> None:
    findings = audit_client_email_text("Hi Anna — quick note.")

    assert any(finding.code == "email.em_dash" for finding in findings)


def test_email_language_audit_file_summary(tmp_path: Path) -> None:
    email = tmp_path / "client_email_draft.md"
    email.write_text("No changes have been pushed live.", encoding="utf-8")

    findings, summary = audit_client_email_file(email)

    assert summary["errors"] == 1
    assert findings[0].code == "email.robotic_or_report_boilerplate"
