"""Shared client-facing report contracts.

This module defines the machine-readable shape that report builders should
declare before they write HTML, PDF, visual audits, and run manifests.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class ReportType(StrEnum):
    """Canonical report types for client-facing Google Ads reports."""

    NEW_CAMPAIGN = "new_campaign"
    REBUILD = "rebuild"
    REVISION = "revision"


@dataclass(frozen=True)
class ApprovalItem:
    """A compact final approval item."""

    key: str
    label: str
    summary: str


@dataclass(frozen=True)
class QualityGateResult:
    """One quality gate result to store in a manifest."""

    gate: str
    status: str
    command: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReportContract:
    """Machine-readable report contract shared by report builders."""

    report_type: ReportType
    report_title: str
    source_artifacts: dict[str, str]
    section_ids: list[str]
    approval_items: list[ApprovalItem]
    quality_gates: list[QualityGateResult]
    report_html: str
    report_pdf: str
    visual_audit_dir: str
    staging_csv: str
    validation_report: str
    client_email_draft: str = ""

    def manifest_fields(self) -> dict[str, Any]:
        """Return fields intended to be merged into run_manifest.json."""
        return {
            "report_type": self.report_type.value,
            "report_title": self.report_title,
            "source_artifacts": dict(self.source_artifacts),
            "report_html": self.report_html,
            "report_pdf": self.report_pdf,
            "report_sections": list(self.section_ids),
            "approval_items": [asdict(item) for item in self.approval_items],
            "quality_gate_results": [asdict(gate) for gate in self.quality_gates],
            "visual_audit_dir": self.visual_audit_dir,
            "staging_csv": self.staging_csv,
            "validation_report": self.validation_report,
            "client_email_draft": self.client_email_draft,
            "live_upload": False,
        }


REQUIRED_SECTIONS: dict[ReportType, tuple[str, ...]] = {
    ReportType.NEW_CAMPAIGN: (
        "cover",
        "overview",
        "campaign_structure",
        "ad_groups",
        "ad_copy",
        "regional_targeting",
        "budget",
        "approval",
    ),
    ReportType.REBUILD: (
        "cover",
        "overview",
        "source_attribution",
        "campaign_structure",
        "ad_groups",
        "ad_copy",
        "regional_targeting",
        "budget",
        "approval",
    ),
    ReportType.REVISION: (
        "cover",
        "overview",
        "revision_changes",
        "ad_groups",
        "ad_copy",
        "regional_targeting",
        "approval",
    ),
}

DEFAULT_APPROVAL_ITEMS: tuple[ApprovalItem, ...] = (
    ApprovalItem("ad_groups", "Ad groups", "Services or intent groups shown in this report"),
    ApprovalItem("ads", "Ads", "Ad copy direction shown in this report"),
    ApprovalItem("regional_targeting", "Regional targeting", "Locations shown in this report"),
    ApprovalItem("budget", "Budget", "Budget shown in this report"),
)

DEFAULT_QUALITY_GATES: tuple[QualityGateResult, ...] = (
    QualityGateResult("staging_validation", "pending"),
    QualityGateResult("static_html_audit", "pending"),
    QualityGateResult("pdf_visual_audit", "pending"),
    QualityGateResult("manual_contact_sheet_review", "pending"),
)


def build_report_contract(
    *,
    report_type: ReportType | str,
    report_title: str,
    source_artifacts: dict[str, str | Path],
    report_html: str | Path,
    report_pdf: str | Path,
    visual_audit_dir: str | Path,
    staging_csv: str | Path,
    validation_report: str | Path,
    client_email_draft: str | Path = "",
    section_ids: list[str] | None = None,
    approval_items: list[ApprovalItem] | None = None,
    quality_gates: list[QualityGateResult] | None = None,
) -> ReportContract:
    """Build and validate a report contract."""
    parsed_type = ReportType(report_type)
    contract = ReportContract(
        report_type=parsed_type,
        report_title=report_title,
        source_artifacts={key: str(value) for key, value in source_artifacts.items()},
        section_ids=section_ids or list(REQUIRED_SECTIONS[parsed_type]),
        approval_items=approval_items or list(DEFAULT_APPROVAL_ITEMS),
        quality_gates=quality_gates or list(DEFAULT_QUALITY_GATES),
        report_html=str(report_html),
        report_pdf=str(report_pdf),
        visual_audit_dir=str(visual_audit_dir),
        staging_csv=str(staging_csv),
        validation_report=str(validation_report),
        client_email_draft=str(client_email_draft),
    )
    validate_report_contract(contract)
    return contract


def validate_report_contract(contract: ReportContract) -> None:
    """Validate required contract fields before manifest export."""
    missing_sections = [
        section for section in REQUIRED_SECTIONS[contract.report_type] if section not in contract.section_ids
    ]
    if missing_sections:
        raise ValueError(f"Missing required report sections: {', '.join(missing_sections)}")

    if not contract.report_title.strip():
        raise ValueError("Report title is required.")
    if not contract.report_html.strip():
        raise ValueError("Report HTML path is required.")
    if not contract.report_pdf.strip():
        raise ValueError("Report PDF path is required.")
    if not contract.staging_csv.strip():
        raise ValueError("Staging CSV path is required.")
    if not contract.validation_report.strip():
        raise ValueError("Validation report path is required.")
    if not contract.visual_audit_dir.strip():
        raise ValueError("Visual audit directory is required.")

    approval_keys = {item.key for item in contract.approval_items}
    required_approval_keys = {"ad_groups", "ads", "regional_targeting"}
    if contract.report_type != ReportType.REVISION:
        required_approval_keys.add("budget")
    missing_approvals = sorted(required_approval_keys - approval_keys)
    if missing_approvals:
        raise ValueError(f"Missing approval items: {', '.join(missing_approvals)}")

    gate_names = {gate.gate for gate in contract.quality_gates}
    required_gates = {"staging_validation", "static_html_audit", "pdf_visual_audit"}
    missing_gates = sorted(required_gates - gate_names)
    if missing_gates:
        raise ValueError(f"Missing quality gates: {', '.join(missing_gates)}")
