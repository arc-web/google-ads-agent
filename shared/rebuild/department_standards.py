#!/usr/bin/env python3
"""Department training standards and operational audit helpers."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STANDARDS_PATH = ROOT / "shared" / "config" / "department_standards.yaml"
REPORT_ENCODINGS = ("utf-16", "utf-8-sig", "utf-8", "latin-1")


@dataclass(frozen=True)
class DepartmentRule:
    id: str
    scope: str
    title: str
    action: str


def load_department_standards(path: Path = DEFAULT_STANDARDS_PATH) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    data["rules"] = [asdict(rule) for rule in load_rules(data)]
    return data


def load_rules(data: dict[str, Any]) -> list[DepartmentRule]:
    return [
        DepartmentRule(
            id=str(item.get("id", "")),
            scope=str(item.get("scope", "global")),
            title=str(item.get("title", "")),
            action=str(item.get("action", "")),
        )
        for item in data.get("rules", [])
    ]


def rules_by_scope(standards: dict[str, Any], scopes: Iterable[str]) -> list[dict[str, str]]:
    allowed = set(scopes)
    return [rule for rule in standards.get("rules", []) if rule.get("scope") in allowed]


def read_google_report(path: Path, required_headers: Iterable[str]) -> tuple[list[str], list[dict[str, str]], str]:
    """Read Google Ads UI exports that may include title and date metadata rows."""
    required = {header.lower() for header in required_headers}
    if not path.exists():
        return [], [], "missing"
    for encoding in REPORT_ENCODINGS:
        try:
            text = path.read_text(encoding=encoding)
        except UnicodeError:
            continue
        lines = text.splitlines()
        for index, line in enumerate(lines):
            delimiter = detect_delimiter("\n".join(lines[index : index + 20]))
            headers = [header.strip() for header in line.split(delimiter)]
            lowered = {header.lower() for header in headers}
            if required.issubset(lowered):
                reader = csv.DictReader(lines[index:], delimiter=delimiter)
                return list(reader.fieldnames or []), [clean_row(row) for row in reader], f"{encoding}:{delimiter_name(delimiter)}"
        delimiter = detect_delimiter(text)
        reader = csv.DictReader(lines, delimiter=delimiter)
        headers = list(reader.fieldnames or [])
        if required.issubset({header.lower() for header in headers}):
            return headers, [clean_row(row) for row in reader], f"{encoding}:{delimiter_name(delimiter)}"
    return [], [], "unreadable"


def clean_row(row: dict[str, str | None]) -> dict[str, str]:
    return {str(key or "").strip(): str(value or "").strip() for key, value in row.items() if key is not None}


def detect_delimiter(text: str) -> str:
    sample = "\n".join(line for line in text.splitlines()[:20] if line.strip())
    if not sample:
        return ","
    try:
        return csv.Sniffer().sniff(sample, delimiters="\t,").delimiter
    except csv.Error:
        first = sample.splitlines()[0]
        return "\t" if first.count("\t") > first.count(",") else ","


def delimiter_name(delimiter: str) -> str:
    return "tab" if delimiter == "\t" else "comma"


def numeric_value(value: object) -> float:
    try:
        return float(str(value or "").replace(",", "").replace("$", "").strip() or 0)
    except ValueError:
        return 0.0


def truthy_text(value: str) -> bool:
    return value.strip().lower() in {"yes", "true", "enabled", "included", "include", "recording", "active"}


def audit_conversion_tracking(report_path: Path, standards: dict[str, Any]) -> dict[str, Any]:
    headers, rows, encoding = read_google_report(report_path, ["Conversion action"])
    issues: list[dict[str, str]] = []
    primary_actions = []
    recording_actions = []
    included_actions = []
    valued_actions = []

    for row in rows:
        name = value_for(row, "Conversion action", "Conversion action name", "Name")
        if not name:
            continue
        category = value_for(row, "Category", "Conversion source", "Source")
        status = value_for(row, "Tracking status", "Status")
        include = value_for(row, "Include in Conversions", "Include in conversions", "Include")
        value = value_for(row, "Value", "Default value", "Conversion value")
        count = value_for(row, "Count", "Counting")
        action = {
            "name": name,
            "category": category,
            "status": status,
            "include_in_conversions": include,
            "count": count,
            "value": value,
        }
        primary_actions.append(action)
        if "recording" in status.lower() or "active" in status.lower():
            recording_actions.append(action)
        if truthy_text(include):
            included_actions.append(action)
        if numeric_value(value) > 0:
            valued_actions.append(action)
        if not status:
            issues.append({"rule": "conversion_status_missing", "severity": "warning", "message": f"{name} has no tracking status."})
        elif "unverified" in status.lower() or "inactive" in status.lower() or "no recent" in status.lower():
            issues.append({"rule": "conversion_not_recording", "severity": "error", "message": f"{name} is not confirmed recording."})
        if not count:
            issues.append({"rule": "conversion_count_missing", "severity": "warning", "message": f"{name} has no count setting in the export."})

    if encoding == "missing":
        issues.append({"rule": "conversion_report_missing", "severity": "warning", "message": "No conversion action report was available."})
    elif not primary_actions:
        issues.append({"rule": "conversion_actions_missing", "severity": "error", "message": "No conversion actions were found in the report."})
    elif not recording_actions:
        issues.append({"rule": "conversion_recording_missing", "severity": "error", "message": "No primary conversion action is confirmed recording."})

    return {
        "status": "fail" if any(issue["severity"] == "error" for issue in issues) else "pass" if primary_actions else "review_required",
        "source": str(report_path),
        "encoding": encoding,
        "rules_applied": rules_by_scope(standards, ["launch_readiness"]),
        "conversion_actions": primary_actions,
        "summary": {
            "actions": len(primary_actions),
            "recording_actions": len(recording_actions),
            "included_actions": len(included_actions),
            "valued_actions": len(valued_actions),
        },
        "issues": issues,
    }


def build_bid_strategy_recommendation(report_path: Path, standards: dict[str, Any]) -> dict[str, Any]:
    _headers, rows, encoding = read_google_report(report_path, ["Conversion action"])
    conversions_30d = sum(numeric_value(value_for(row, "Conversions", "All conv.", "All conversions")) for row in rows)
    thresholds = standards.get("bid_strategy_thresholds", {})
    if conversions_30d >= numeric_value(thresholds.get("target_roas", {}).get("min_conversions_30d")):
        strategy = "target_roas"
        phase = "scale"
    elif conversions_30d >= numeric_value(thresholds.get("target_cpa", {}).get("min_conversions_30d")):
        strategy = "target_cpa"
        phase = "efficiency_optimization"
    elif conversions_30d >= numeric_value(thresholds.get("maximize_conversions", {}).get("min_conversions_30d")):
        strategy = "maximize_conversions"
        phase = "conversion_accumulation"
    else:
        strategy = "manual_cpc"
        phase = "data_collection"
    details = thresholds.get(strategy, {})
    return {
        "status": "review_required",
        "source": str(report_path),
        "encoding": encoding,
        "conversions_30d": conversions_30d,
        "recommended_phase": phase,
        "recommended_strategy": strategy,
        "recommendation": details.get("recommendation", ""),
        "rules_applied": rules_by_scope(standards, ["optimization"]),
    }


def build_optimization_cadence_plan(standards: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "active_standard",
        "source_document": standards.get("source_document", ""),
        "cadence": standards.get("cadence", {}),
        "rules_applied": rules_by_scope(standards, ["optimization", "manual_sop"]),
    }


def audit_audience_modes(report_path: Path, standards: dict[str, Any]) -> dict[str, Any]:
    headers, rows, encoding = read_google_report(report_path, ["Campaign"])
    issues: list[dict[str, str]] = []
    audited = []
    for row in rows:
        campaign = value_for(row, "Campaign")
        mode = value_for(row, "Audience mode", "Targeting setting", "Audience targeting setting", "Targeting mode")
        audience = value_for(row, "Audience", "Audience segment")
        if not campaign or not mode:
            continue
        item = {"campaign": campaign, "audience": audience, "mode": mode}
        audited.append(item)
        if "target" in mode.lower() and "remarketing" not in campaign.lower():
            issues.append(
                {
                    "rule": "audience_targeting_requires_strategy",
                    "severity": "warning",
                    "message": f"{campaign} uses Targeting mode. Confirm this is intentional before launch.",
                }
            )
    if encoding == "missing":
        issues.append({"rule": "audience_report_missing", "severity": "warning", "message": "No audience mode report was available."})
    return {
        "status": "review_required" if issues else "pass",
        "source": str(report_path),
        "encoding": encoding,
        "headers": headers,
        "audiences": audited,
        "rules_applied": rules_by_scope(standards, ["launch_readiness"]),
        "issues": issues,
    }


def triage_recommendations(report_path: Path, standards: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    _headers, rows, encoding = read_google_report(report_path, ["Recommendation"])
    policy = standards.get("recommendation_policy", {})
    triaged: list[dict[str, str]] = []
    for row in rows:
        recommendation = value_for(row, "Recommendation", "Recommendation type", "Type")
        if not recommendation:
            continue
        action = classify_recommendation(recommendation, policy)
        triaged.append(
            {
                "recommendation": recommendation,
                "campaign": value_for(row, "Campaign"),
                "impact": value_for(row, "Impact", "Optimization score uplift"),
                "triage_action": action,
                "reason": recommendation_reason(action),
            }
        )
    summary = {
        "status": "review_required" if triaged else "missing" if encoding == "missing" else "pass",
        "source": str(report_path),
        "encoding": encoding,
        "rows": len(triaged),
        "rules_applied": rules_by_scope(standards, ["manual_sop"]),
    }
    return summary, triaged


def classify_recommendation(recommendation: str, policy: dict[str, Any]) -> str:
    lowered = recommendation.lower()
    for item in policy.get("dismiss_by_default", []):
        if item.lower() in lowered or any(token in lowered for token in ("auto-applied", "display expansion", "broad match")):
            return "dismiss_by_default"
    for item in policy.get("accept_review", []):
        if item.lower() in lowered:
            return "review_for_acceptance"
    for item in policy.get("evaluate_critically", []):
        if item.lower() in lowered:
            return "evaluate_against_account_data"
    return "manual_review"


def recommendation_reason(action: str) -> str:
    reasons = {
        "dismiss_by_default": "Department standard blocks this unless a senior operator overrides it.",
        "review_for_acceptance": "Potentially useful, but still needs account evidence review.",
        "evaluate_against_account_data": "Do not accept from the Recommendations tab alone.",
        "manual_review": "No deterministic rule matched this recommendation.",
    }
    return reasons.get(action, "Review manually.")


def audit_policy_disapprovals(report_path: Path, standards: dict[str, Any]) -> dict[str, Any]:
    _headers, rows, encoding = read_google_report(report_path, ["Status"])
    issues: list[dict[str, str]] = []
    disapproved = []
    for row in rows:
        status = value_for(row, "Status", "Policy status", "Approval status")
        if not status:
            continue
        if "disapproved" in status.lower() or "limited" in status.lower() or "suspended" in status.lower():
            item = {
                "campaign": value_for(row, "Campaign"),
                "ad_group": value_for(row, "Ad group", "Ad Group"),
                "status": status,
                "policy": value_for(row, "Policy", "Policy issue", "Disapproval reason"),
            }
            disapproved.append(item)
            issues.append({"rule": "policy_issue_present", "severity": "error", "message": f"{status}: {item['policy']}"})
    if encoding == "missing":
        issues.append({"rule": "disapproval_report_missing", "severity": "warning", "message": "No disapproval report was available."})
    return {
        "status": "fail" if any(issue["severity"] == "error" for issue in issues) else "pass" if encoding != "missing" else "review_required",
        "source": str(report_path),
        "encoding": encoding,
        "disapprovals": disapproved,
        "rules_applied": rules_by_scope(standards, ["manual_sop"]),
        "issues": issues,
    }


def build_evidence_quality_report(
    *,
    account_snapshot: dict[str, Any],
    search_terms_path: Path,
    location_report_path: Path,
    conversion_audit: dict[str, Any],
    landing_map: dict[str, Any],
) -> dict[str, Any]:
    labels = {
        "account_structure": "strong" if account_snapshot.get("rows", 0) else "not_tested",
        "search_terms": "strong" if search_terms_path.exists() and search_terms_path.stat().st_size > 80 else "weak",
        "location_performance": "directional" if location_report_path.exists() else "not_tested",
        "conversion_tracking": "strong" if conversion_audit.get("status") == "pass" else "weak",
        "landing_page_match": landing_evidence_label(landing_map),
    }
    return {
        "status": "review_required" if "weak" in labels.values() or "not_tested" in labels.values() else "pass",
        "labels": labels,
        "notes": [
            "Use strong evidence for build decisions.",
            "Treat weak or not-tested evidence as human review input, not automatic exclusion logic.",
        ],
    }


def landing_evidence_label(landing_map: dict[str, Any]) -> str:
    if not landing_map:
        return "not_tested"
    if any(evidence.get("status") in {"missing", "unreadable", "fallback_homepage"} for evidence in landing_map.values()):
        return "weak"
    if all(evidence.get("fit_score", 0) > 0 for evidence in landing_map.values()):
        return "strong"
    return "directional"


def write_recommendations_csv(path: Path, rows: list[dict[str, str]]) -> Path:
    fieldnames = ["recommendation", "campaign", "impact", "triage_action", "reason"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_launch_readiness_checklist(path: Path, artifacts: dict[str, Any]) -> Path:
    conversion_status = artifacts.get("conversion_tracking_audit", {}).get("status", "review_required")
    policy_status = artifacts.get("policy_disapproval_audit", {}).get("status", "review_required")
    audience_status = artifacts.get("audience_mode_audit", {}).get("status", "review_required")
    lines = [
        "# Launch Readiness Checklist",
        "",
        "- Staging CSV remains paused for Google Ads Editor review.",
        f"- Conversion tracking audit: `{conversion_status}`.",
        f"- Policy and disapproval audit: `{policy_status}`.",
        f"- Audience mode audit: `{audience_status}`.",
        "- Confirm Search campaigns use Google search only.",
        "- Confirm no Search campaign is opted into Display expansion.",
        "- Confirm budget, service priority, landing pages, and conversion goals before upload.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def value_for(row: dict[str, str], *names: str) -> str:
    lower_map = {key.lower(): value for key, value in row.items()}
    for name in names:
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    return ""


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
