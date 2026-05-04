"""Website-backed service interpretation for service-based Search ads."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


GENERIC_CONCEPTS = {
    "care",
    "clear",
    "compare",
    "confirm",
    "consult",
    "consulting",
    "details",
    "focused",
    "guidance",
    "help",
    "next",
    "options",
    "plan",
    "planning",
    "practical",
    "program",
    "request",
    "review",
    "service",
    "services",
    "start",
    "step",
    "support",
    "team",
    "today",
}


@dataclass(frozen=True)
class ServiceLogic:
    service: str
    buyer_type: str
    buyer: str
    end_user: str
    service_mechanism: str
    problem: str
    outcome: str
    proof_or_specifics: list[str]
    concept_tokens: list[str]
    source_urls: list[str]
    evidence_summary: str
    status: str = "pass"
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()


def tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", normalize(value))


def page_text(page: dict[str, Any]) -> str:
    parts = [str(page.get("title", ""))]
    parts.extend(str(heading) for heading in page.get("headings", []) or [])
    sample = str(page.get("text_sample", ""))
    if sample and "\ufffd" not in sample[:80]:
        parts.append(sample)
    return " ".join(parts)


def source_pages(source_attribution: dict[str, Any], website_scan: dict[str, Any]) -> list[dict[str, Any]]:
    pages = list(source_attribution.get("source_pages", []) or [])
    if pages:
        return pages
    evidence = website_scan.get("page_evidence", {})
    return [page for page in evidence.values() if isinstance(page, dict)]


def service_match_score(service: str, page: dict[str, Any]) -> int:
    service_tokens = {token for token in tokens(service) if len(token) > 2}
    if not service_tokens:
        return 0
    text = normalize(" ".join([str(page.get("url", "")), page_text(page)]))
    score = sum(2 for token in service_tokens if token in text)
    if normalize(service) in text:
        score += 6
    return score


def select_service_pages(service: str, pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored = [(service_match_score(service, page), page) for page in pages]
    return [page for score, page in sorted(scored, key=lambda item: item[0], reverse=True) if score > 0][:3]


def infer_buyer_type(service: str, evidence_text: str) -> str:
    lower = normalize(f"{service} {evidence_text}")
    b2b_score = sum(
        1
        for term in (
            "capacity",
            "clinical",
            "development",
            "employee",
            "employees",
            "integrated",
            "organization",
            "organizations",
            "staff",
            "team",
            "teams",
            "training",
            "workplace",
        )
        if term in lower
    )
    b2c_score = sum(
        1
        for term in ("affordable", "appointments", "counseling for you", "customer", "customers", "for you", "individual", "personal", "text")
        if term in lower
    )
    if b2b_score >= 2 and b2c_score >= 1:
        return "b2b2c"
    if b2b_score >= 2:
        return "b2b"
    if b2c_score >= 2:
        return "b2c"
    return "unclear"


def logic_for_service(service: str, matched_pages: list[dict[str, Any]]) -> ServiceLogic:
    evidence = " ".join(page_text(page) for page in matched_pages)
    lower = normalize(f"{service} {evidence}")
    service_lower = normalize(service)
    source_urls = [str(page.get("url", "")) for page in matched_pages if page.get("url")]
    specifics = [str(heading).strip() for page in matched_pages for heading in page.get("headings", []) or [] if str(heading).strip()]
    buyer_type = infer_buyer_type(service, evidence)
    issues: list[str] = []

    if "lay counselor" in service_lower:
        buyer_type = "b2b2c"
        buyer = "Organizations building mental health support capacity"
        end_user = "Community members, employees, or clients who need accessible counseling support"
        mechanism = "Training staff in lay counseling skills"
        problem = "Organizations need more accessible mental health support without relying only on licensed clinicians"
        outcome = "Expanded care access through trained lay counselor and care team support"
        concepts = ["academy", "access", "capacity", "care", "counseling", "counselor", "lay", "mental", "organization", "staff", "team", "training"]
    elif "employee mental health" in service_lower:
        buyer_type = "b2b2c" if buyer_type == "unclear" else buyer_type
        buyer = "Employers or individuals reviewing mental health support options"
        end_user = "Employees or people seeking affordable empathic counseling"
        mechanism = "Employee mental health support and counseling access"
        problem = "Workplaces and individuals need clearer access to mental health support"
        outcome = "Better employee wellbeing, fewer sick days, and easier counseling access"
        concepts = ["access", "counseling", "employee", "employer", "flourish", "health", "mental", "wellbeing", "workplace"]
    elif "integrated behavioral" in service_lower:
        buyer_type = "b2b"
        buyer = "Healthcare organizations and clinical teams"
        end_user = "Patients and care teams using integrated behavioral health workflows"
        mechanism = "Integrated behavioral health consulting"
        problem = "Care teams need behavioral health workflows that fit clinical operations"
        outcome = "More coordinated behavioral health support inside care delivery"
        concepts = ["behavioral", "care", "clinical", "consulting", "health", "integrated", "team", "workflow"]
    elif "communication" in service_lower:
        buyer_type = "b2b"
        buyer = "Organizations and care teams"
        end_user = "Staff and the people they support"
        mechanism = "Empathic communication training"
        problem = "Teams need communication skills for difficult care and support conversations"
        outcome = "More empathic, human-centered communication"
        concepts = ["care", "communication", "conversation", "empathic", "skills", "staff", "team", "training"]
    elif "trauma" in service_lower:
        buyer_type = "b2b"
        buyer = "Organizations and care teams"
        end_user = "People served by trauma-informed teams"
        mechanism = "Trauma-informed care training"
        problem = "Teams need safer support practices for people affected by trauma"
        outcome = "More trauma-informed care and support interactions"
        concepts = ["care", "informed", "safe", "staff", "support", "team", "training", "trauma"]
    elif "learning" in service_lower or "development" in service_lower:
        buyer_type = "b2b"
        buyer = "Organizations planning staff development"
        end_user = "Staff members and the communities they support"
        mechanism = "Learning and development programs"
        problem = "Organizations need practical training paths for care and support teams"
        outcome = "Stronger staff skills and clearer support practices"
        concepts = ["development", "learning", "program", "skills", "staff", "team", "training"]
    elif "clinical" in service_lower:
        buyer_type = "b2b"
        buyer = "Clinical leaders and healthcare teams"
        end_user = "Patients and care teams"
        mechanism = "Clinical support consulting"
        problem = "Clinical teams need practical support around care delivery"
        outcome = "Clearer clinical support practices"
        concepts = ["care", "clinical", "consulting", "support", "team", "workflow"]
    elif "human centered" in service_lower or "human-centered" in service.lower():
        buyer_type = "b2b"
        buyer = "Healthcare and service organizations"
        end_user = "People receiving care or support"
        mechanism = "Human-centered care consulting"
        problem = "Organizations need care models that stay centered on people"
        outcome = "More human-centered care delivery"
        concepts = ["care", "centered", "consulting", "healthcare", "human", "organization", "people"]
    else:
        if buyer_type == "unclear" and matched_pages and "services" in service_lower:
            buyer_type = "b2c"
        buyer = "Customers reviewing service options" if buyer_type == "b2c" else ""
        end_user = "Customers who need service support" if buyer_type == "b2c" else ""
        mechanism = f"{service} support" if buyer_type == "b2c" else ""
        problem = "Customers need clear service planning and next steps" if buyer_type == "b2c" else ""
        outcome = "Clearer service options and next steps" if buyer_type == "b2c" else ""
        concepts = [token for token in tokens(service) if token not in GENERIC_CONCEPTS and len(token) > 2]
        if buyer_type == "b2c":
            concepts.extend([token for token in tokens(service) if len(token) > 2])
            concepts.extend(["customer", "option", "planning", "service"])

    if not source_urls:
        issues.append("missing_service_source_page")
    if buyer_type == "unclear":
        issues.append("buyer_type_unclear")
    if len(concepts) < 3:
        issues.append("insufficient_concept_tokens")

    return ServiceLogic(
        service=service,
        buyer_type=buyer_type,
        buyer=buyer,
        end_user=end_user,
        service_mechanism=mechanism,
        problem=problem,
        outcome=outcome,
        proof_or_specifics=specifics[:6],
        concept_tokens=sorted(set(concepts)),
        source_urls=source_urls,
        evidence_summary="; ".join(specifics[:3]) or service,
        status="fail" if issues else "pass",
        issues=issues,
    )


def build_service_logic_research(
    *,
    services: list[str],
    website_scan: dict[str, Any],
    source_attribution: dict[str, Any],
) -> dict[str, Any]:
    pages = source_pages(source_attribution, website_scan)
    records = [logic_for_service(service, select_service_pages(service, pages)).to_dict() for service in services]
    failing = [record for record in records if record["status"] != "pass"]
    return {
        "status": "fail" if failing else "pass",
        "service_count": len(records),
        "failing_services": len(failing),
        "services": records,
    }


def write_service_logic_research(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def service_logic_by_name(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(record.get("service", "")): record for record in payload.get("services", [])}
