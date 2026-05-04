from __future__ import annotations

import pytest

from shared.presentation.report_contract import (
    ApprovalItem,
    QualityGateResult,
    ReportType,
    build_report_contract,
)


def test_new_campaign_report_contract_manifest_fields() -> None:
    contract = build_report_contract(
        report_type=ReportType.NEW_CAMPAIGN,
        report_title="New Campaign Review",
        source_artifacts={
            "website_scan": "website_scan.json",
            "service_catalog": "service_catalog.json",
            "geo_strategy": "geo_strategy.json",
            "source_attribution": "source_attribution.json",
        },
        report_html="Client_New_Campaign_Review.html",
        report_pdf="Client_New_Campaign_Review.pdf",
        visual_audit_dir="new_campaign_visual_audit",
        staging_csv="staging.csv",
        validation_report="validation_report.json",
        client_email_draft="client_email_draft.md",
    )

    manifest = contract.manifest_fields()

    assert manifest["report_type"] == "new_campaign"
    assert manifest["live_upload"] is False
    assert "campaign_structure" in manifest["report_sections"]
    assert "revision_changes" not in manifest["report_sections"]
    assert {item["key"] for item in manifest["approval_items"]} == {
        "ad_groups",
        "ads",
        "regional_targeting",
        "budget",
    }
    assert {gate["gate"] for gate in manifest["quality_gate_results"]} >= {
        "staging_validation",
        "static_html_audit",
        "pdf_visual_audit",
    }


def test_rebuild_report_contract_requires_source_attribution() -> None:
    with pytest.raises(ValueError, match="source_attribution"):
        build_report_contract(
            report_type="rebuild",
            report_title="Rebuild Review",
            source_artifacts={"account_snapshot": "account_snapshot.json"},
            report_html="Client_Rebuild_Review.html",
            report_pdf="Client_Rebuild_Review.pdf",
            section_ids=[
                "cover",
                "overview",
                "campaign_structure",
                "ad_groups",
                "ad_copy",
                "regional_targeting",
                "budget",
                "approval",
            ],
            visual_audit_dir="client_review_visual_audit",
            staging_csv="staging.csv",
            validation_report="validation_report.json",
        )


def test_revision_report_contract_uses_revision_sections() -> None:
    contract = build_report_contract(
        report_type=ReportType.REVISION,
        report_title="Revision Review",
        source_artifacts={
            "client_feedback_classified": "client_feedback_classified.json",
            "revision_decision_log": "revision_decision_log.csv",
        },
        report_html="Client_Rebuild_Review_R1.html",
        report_pdf="Client_Rebuild_Review_R1.pdf",
        visual_audit_dir="revision_visual_audit",
        staging_csv="Google_Ads_Editor_Staging_REV1.csv",
        validation_report="Google_Ads_Editor_Staging_REV1_validation.json",
        approval_items=[
            ApprovalItem("ad_groups", "Ad groups", "Revised services shown in this report"),
            ApprovalItem("ads", "Ads", "Revised ad copy shown in this report"),
            ApprovalItem("regional_targeting", "Regional targeting", "Revised locations shown in this report"),
        ],
    )

    manifest = contract.manifest_fields()

    assert manifest["report_type"] == "revision"
    assert "revision_changes" in manifest["report_sections"]
    assert "budget" not in {item["key"] for item in manifest["approval_items"]}


def test_report_contract_rejects_missing_quality_gate() -> None:
    with pytest.raises(ValueError, match="pdf_visual_audit"):
        build_report_contract(
            report_type=ReportType.NEW_CAMPAIGN,
            report_title="New Campaign Review",
            source_artifacts={"website_scan": "website_scan.json"},
            report_html="Client_New_Campaign_Review.html",
            report_pdf="Client_New_Campaign_Review.pdf",
            visual_audit_dir="new_campaign_visual_audit",
            staging_csv="staging.csv",
            validation_report="validation_report.json",
            quality_gates=[
                QualityGateResult("staging_validation", "pass"),
                QualityGateResult("static_html_audit", "pass"),
            ],
        )
