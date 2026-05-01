from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC = REPO_ROOT / "docs/system_review/SEARCH_PARTNER_HEADLINE_QUALITY_RULES_2026-05-01.md"
SUMMARY = (
    REPO_ROOT
    / "clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/"
    / "THHL_Search_Services_Editor_Staging_REV1_headline_quality_summary.json"
)
FAILURES = (
    REPO_ROOT
    / "clients/therappc/thinkhappylivehealthy/build/search_rebuild_test/"
    / "THHL_Search_Services_Editor_Staging_REV1_headline_quality_failures.csv"
)


def test_search_partner_and_headline_quality_doc_records_new_rules() -> None:
    text = DOC.read_text(encoding="utf-8")

    for phrase in [
        "Search partners are disabled 100 percent of the time",
        "RSA headlines under 25 characters fail quality review",
        "`Networks`: `Google search`",
        "`Ashburn Care`",
        "`Anxiety Counseling`",
    ]:
        assert phrase in text


def test_thlh_headline_quality_audit_records_current_failures() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    failures_text = FAILURES.read_text(encoding="utf-8")

    assert summary["status"] == "fail"
    assert summary["total_failures"] == 443
    assert summary["unique_failed_headlines"] == 63
    assert summary["rule"] == "headline_minimum_value"
    assert "Ashburn Care" in failures_text
    assert "Anxiety Counseling" in failures_text
