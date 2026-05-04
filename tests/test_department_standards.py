from __future__ import annotations

import json
from pathlib import Path

from shared.rebuild.department_standards import (
    audit_audience_modes,
    audit_conversion_tracking,
    audit_policy_disapprovals,
    build_bid_strategy_recommendation,
    load_department_standards,
    triage_recommendations,
)


def test_conversion_report_parser_scans_google_metadata_rows(tmp_path: Path) -> None:
    path = tmp_path / "conversion_action_report.csv"
    path.write_text(
        "Conversion actions\n"
        "Apr 1, 2026 - Apr 30, 2026\n"
        "Conversion action,Category,Tracking status,Include in Conversions,Count,Value,Conversions\n"
        "Lead Form,Website,Recording,Yes,One,100,18\n",
        encoding="utf-8",
    )

    report = audit_conversion_tracking(path, load_department_standards())

    assert report["status"] == "pass"
    assert report["summary"]["recording_actions"] == 1
    assert report["summary"]["valued_actions"] == 1


def test_conversion_report_blocks_unverified_primary_actions(tmp_path: Path) -> None:
    path = tmp_path / "conversion_action_report.csv"
    path.write_text(
        "Conversion action,Category,Tracking status,Include in Conversions,Count,Value,Conversions\n"
        "Lead Form,Website,Unverified,Yes,One,0,0\n",
        encoding="utf-8",
    )

    report = audit_conversion_tracking(path, load_department_standards())

    assert report["status"] == "fail"
    assert {issue["rule"] for issue in report["issues"]} >= {"conversion_not_recording"}


def test_bid_strategy_recommendation_uses_training_thresholds(tmp_path: Path) -> None:
    path = tmp_path / "conversion_action_report.csv"
    path.write_text(
        "Conversion action,Tracking status,Conversions\n"
        "Lead Form,Recording,35\n",
        encoding="utf-8",
    )

    report = build_bid_strategy_recommendation(path, load_department_standards())

    assert report["recommended_strategy"] == "target_cpa"
    assert report["recommended_phase"] == "efficiency_optimization"


def test_recommendations_triage_dismisses_blocked_google_suggestions(tmp_path: Path) -> None:
    path = tmp_path / "recommendations_report.csv"
    path.write_text(
        "Recommendation,Campaign,Impact\n"
        "Use broad match for more reach,ARC - Search - Services - V1,8%\n"
        "Add missing assets,ARC - Search - Services - V1,2%\n",
        encoding="utf-8",
    )

    summary, rows = triage_recommendations(path, load_department_standards())

    assert summary["rows"] == 2
    assert [row["triage_action"] for row in rows] == ["dismiss_by_default", "review_for_acceptance"]


def test_audience_and_disapproval_audits_surface_launch_risks(tmp_path: Path) -> None:
    audience = tmp_path / "audience_report.csv"
    disapprovals = tmp_path / "disapproval_report.csv"
    audience.write_text("Campaign,Audience,Audience mode\nARC - Search - Services - V1,In-market,Targeting\n", encoding="utf-8")
    disapprovals.write_text("Campaign,Ad group,Status,Policy\nARC - Search - Services - V1,General,Disapproved,Destination mismatch\n", encoding="utf-8")

    audience_report = audit_audience_modes(audience, load_department_standards())
    policy_report = audit_policy_disapprovals(disapprovals, load_department_standards())

    assert audience_report["status"] == "review_required"
    assert policy_report["status"] == "fail"
    assert json.dumps(policy_report)
