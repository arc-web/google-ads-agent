#!/usr/bin/env python3
"""Repo-local CSV workflow stage helpers."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


INITIAL_MARKERS = ("initial", "draft", "raw", "current", "rev")
ANALYZED_MARKERS = ("analyzed", "validated", "checked")
FINAL_MARKERS = ("final", "optimized", "complete", "approved")
VALID_STAGES = {"initial", "analyzed", "final"}


class CSVStageManager:
    """
    Manage staging CSV lifecycle without depending on an old client folder shape.

    Stage data is kept in filenames or sidecar metadata. CSV contents are never
    modified for stage tracking because row 1 must remain Google Ads Editor
    headers.
    """

    def __init__(self, base_path: str | Path = ".") -> None:
        self.base_path = Path(base_path)

    def get_csv_stage(self, csv_path: str | Path) -> str:
        """Determine the workflow stage from filename or sidecar metadata."""
        path = Path(csv_path)
        filename = path.stem.lower()

        metadata_stage = self._read_metadata_stage(path)
        if metadata_stage:
            return metadata_stage

        if any(self._has_marker(filename, marker) for marker in FINAL_MARKERS):
            return "final"
        if any(self._has_marker(filename, marker) for marker in ANALYZED_MARKERS):
            return "analyzed"
        if any(self._has_marker(filename, marker) for marker in INITIAL_MARKERS):
            return "initial"
        if "staging" in filename or "editor" in filename:
            return "initial"
        return "unknown"

    def mark_csv_stage(self, csv_path: str | Path, stage: str, reason: str = "") -> bool:
        """Write sidecar metadata for a CSV stage without changing CSV content."""
        if stage not in VALID_STAGES:
            return False

        path = Path(csv_path)
        if not path.exists():
            return False

        metadata_file = self._metadata_path(path)
        payload = {
            "stage": stage,
            "reason": reason,
            "csv_path": str(path),
            "timestamp": datetime.now().isoformat(),
        }
        metadata_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return True

    def should_trigger_validation(self, csv_path: str | Path) -> bool:
        """Return true for current, revision, draft, or unmarked staging CSVs."""
        return self.get_csv_stage(csv_path) in {"initial", "unknown"}

    def get_campaign_workflow_files(self, campaign_dir: str | Path) -> dict[str, str | None]:
        """Summarize CSV and report files below any workflow directory."""
        campaign_path = Path(campaign_dir)
        workflow_files: dict[str, str | None] = {
            "initial_csv": None,
            "analysis_report": None,
            "final_csv": None,
            "optimization_log": None,
        }

        if not campaign_path.exists():
            return workflow_files

        for file_path in sorted(campaign_path.rglob("*.csv")):
            stage = self.get_csv_stage(file_path)
            if stage == "final":
                workflow_files["final_csv"] = str(file_path)
            elif stage in {"initial", "unknown"} and workflow_files["initial_csv"] is None:
                workflow_files["initial_csv"] = str(file_path)

        for file_path in sorted(campaign_path.rglob("*.json")):
            name = file_path.name.lower()
            if "analysis" in name or "validation" in name:
                workflow_files["analysis_report"] = str(file_path)
                break

        for file_path in sorted(campaign_path.rglob("*.log")):
            if "optimization" in file_path.name.lower():
                workflow_files["optimization_log"] = str(file_path)
                break

        return workflow_files

    def create_analysis_feedback(self, csv_path: str, analysis_results: dict[str, Any]) -> dict[str, Any]:
        """Create generic feedback from a validation result."""
        report = analysis_results.get("validation_report", analysis_results)
        issues = report.get("issues", [])
        severities = Counter(issue.get("severity", "info") for issue in issues)
        return {
            "csv_path": csv_path,
            "timestamp": datetime.now().isoformat(),
            "stage": "analyzed",
            "overall_status": report.get("final_status", report.get("status", "UNKNOWN")),
            "critical_issues": severities.get("critical", 0) + severities.get("error", 0),
            "warnings": severities.get("warning", 0),
            "recommendations": [issue.get("message", "") for issue in issues[:10]],
            "optimization_suggestions": self._generate_optimization_suggestions(issues),
        }

    def save_feedback_to_campaign_builder(self, feedback: dict[str, Any], campaign_dir: str | Path) -> str:
        """Save validation feedback beside the workflow artifacts."""
        campaign_path = Path(campaign_dir)
        campaign_path.mkdir(parents=True, exist_ok=True)
        feedback_file = campaign_path / f"validation_feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        feedback_file.write_text(json.dumps(feedback, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return str(feedback_file)

    def monitor_new_campaigns_directory(self, client_dir: str | Path) -> list[str]:
        """Find CSVs needing validation below any supplied client or build directory."""
        client_path = Path(client_dir)
        if not client_path.exists():
            return []

        return [
            str(csv_file)
            for csv_file in sorted(client_path.rglob("*.csv"))
            if self.should_trigger_validation(csv_file)
        ]

    def get_workflow_status(self, campaign_dir: str | Path) -> dict[str, Any]:
        """Get current workflow status for any campaign or build directory."""
        workflow_files = self.get_campaign_workflow_files(campaign_dir)
        has_initial = workflow_files["initial_csv"] is not None
        has_analysis = workflow_files["analysis_report"] is not None
        has_final = workflow_files["final_csv"] is not None

        if not has_initial:
            next_action = "Create or locate a staging CSV"
        elif not has_analysis:
            next_action = "Run validation analysis"
        elif not has_final:
            next_action = "Review, revise, or mark final after approval"
        else:
            next_action = "Workflow complete"

        return {
            "directory": str(campaign_dir),
            "has_initial_csv": has_initial,
            "has_analysis_report": has_analysis,
            "has_final_csv": has_final,
            "workflow_complete": has_initial and has_analysis and has_final,
            "next_action": next_action,
            "files": workflow_files,
        }

    def _generate_optimization_suggestions(self, issues: list[dict[str, Any]]) -> list[str]:
        """Generate generic next-step suggestions from issue types."""
        issue_types = Counter(issue.get("issue_type") or issue.get("rule") or "unknown" for issue in issues)
        suggestions: list[str] = []
        if issue_types.get("missing_headers"):
            suggestions.append("Repair the staging CSV headers before importing.")
        if issue_types.get("disallowed_match_type"):
            suggestions.append("Convert Broad or Exact rows to the active phrase-only staging format.")
        if issue_types.get("location_id_preferred"):
            suggestions.append("Add Google Location ID values where available.")
        if issue_types.get("rsa_headline_required") or issue_types.get("rsa_description_required"):
            suggestions.append("Complete the RSA headline and description set.")
        return suggestions or ["Review validation issues before approving the staging CSV."]

    def _read_metadata_stage(self, path: Path) -> str | None:
        metadata_file = self._metadata_path(path)
        if not metadata_file.exists():
            return None

        try:
            payload = json.loads(metadata_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

        stage = str(payload.get("stage", "")).strip().lower()
        return stage if stage in VALID_STAGES else None

    @staticmethod
    def _metadata_path(path: Path) -> Path:
        return path.with_name(f"{path.stem}.stage.json")

    @staticmethod
    def _has_marker(filename: str, marker: str) -> bool:
        tokens = filename.replace("-", "_").split("_")
        return marker in tokens or any(token.startswith(marker) and marker == "rev" for token in tokens)


def mark_csv_final(csv_path: str, reason: str = "Approved final staging file") -> bool:
    """Mark a CSV as final without editing CSV contents."""
    return CSVStageManager().mark_csv_stage(csv_path, "final", reason)


def should_validate_csv(csv_path: str) -> bool:
    """Check if a CSV should be validated."""
    return CSVStageManager().should_trigger_validation(csv_path)


def get_csv_workflow_status(campaign_dir: str) -> dict[str, Any]:
    """Get workflow status for a directory."""
    return CSVStageManager().get_workflow_status(campaign_dir)
