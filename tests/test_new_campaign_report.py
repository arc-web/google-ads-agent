from __future__ import annotations

from pathlib import Path

from shared.presentation.build_new_campaign_report import build_html
from shared.presentation.report_quality_audit import audit_html


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = REPO_ROOT / "clients/therappc/nyc_mindful_mental_health_counseling/build/2026-05-02_initial_search_build"


def test_new_campaign_report_builds_client_facing_html(tmp_path: Path) -> None:
    html = build_html(
        client="Mindful Mental Health Counseling",
        date_label="May 2, 2026",
        staging_csv=BUILD_DIR / "Google_Ads_Editor_Staging_CURRENT.csv",
        website_scan_json=BUILD_DIR / "website_scan.json",
        service_catalog_json=BUILD_DIR / "service_catalog.json",
        geo_strategy_json=BUILD_DIR / "geo_strategy.json",
        source_attribution_json=BUILD_DIR / "source_attribution.json",
    )
    output = tmp_path / "Client_New_Campaign_Review.html"
    output.write_text(html, encoding="utf-8")

    findings, summary = audit_html(output)

    assert "New Campaign Review" in html
    assert "A Controlled New Search Campaign" in html
    assert "Client_New_Campaign_Review" not in html
    assert summary["errors"] == 0
    assert not [finding for finding in findings if finding.severity == "error"]
