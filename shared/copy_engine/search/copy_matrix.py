"""Search RSA copy matrix generation and deterministic quality gates."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from shared.rebuild.rsa_headline_quality import audit_rsa_headlines, generate_quality_headlines


HEADLINE_MIN = 25
HEADLINE_MAX = 30
DESCRIPTION_MIN = 75
DESCRIPTION_MAX = 90
PATH_MAX = 15

POLICY_RISK_TERMS = {
    "guarantee",
    "guaranteed",
    "cure",
    "cures",
    "diagnose",
    "diagnosis",
    "treat",
    "treats",
    "treatment",
}

FILLER_SUFFIXES = [
    " Support",
    " Options",
    " Today",
    " Near You",
    " Appointments",
    " Care",
]

RESTAURANT_CTAS = ["Book Your Reservation", "Reserve Your Table", "Check Availability", "Book A Tasting Menu"]
B2B_CTAS = ["Request Details", "Review Program Fit", "Plan Next Steps", "Schedule A Review"]
CONSULTATIVE_CTAS = ["Schedule Today", "Request Details", "Confirm Fit", "Book A Consultation"]
LOCAL_SERVICE_CTAS = ["Call Us Today", "Request A Quote", "Schedule Service", "Compare Options"]
DEFAULT_CTAS = ["Request Details", "Confirm Fit", "Plan Next Steps", "Schedule Today"]
VALUE_PROP_TERMS = {
    "available",
    "availability",
    "budget",
    "care",
    "clear",
    "compare",
    "confirm",
    "consult",
    "details",
    "experienced",
    "fit",
    "focused",
    "guidance",
    "licensed",
    "local",
    "options",
    "planning",
    "practical",
    "private",
    "process",
    "review",
    "schedule",
    "support",
    "team",
    "access",
    "coordinated",
    "skills",
    "training",
    "wellbeing",
}
GENERIC_DESCRIPTION_PHRASES = {
    "account import",
    "campaign approval",
    "implementation needs",
    "launch readiness",
    "service fit",
}
GENERIC_DESCRIPTION_TERMS = {
    "account",
    "approval",
    "before",
    "budget",
    "campaign",
    "compare",
    "confirm",
    "details",
    "fit",
    "implementation",
    "import",
    "launch",
    "needs",
    "options",
    "readiness",
    "request",
    "review",
    "schedule",
    "scope",
    "service",
    "stakeholders",
    "support",
    "timing",
    "today",
}
DELIVERY_CLAIM_PATTERNS = {
    "virtual": re.compile(r"\b(virtual|online|telehealth|remote)\b", re.IGNORECASE),
    "in_person": re.compile(r"\b(in-person|in person|office visit|on-site|onsite)\b", re.IGNORECASE),
    "24_7": re.compile(r"\b(24/7|24 hours|after hours|answering service)\b", re.IGNORECASE),
}
INCOMPLETE_TRAILING_WORDS = {"and", "for", "through", "to", "via", "with"}


@dataclass(frozen=True)
class CopyConstraints:
    approved_claims: list[str] = field(default_factory=list)
    blocked_claims: list[str] = field(default_factory=list)
    services_with_capacity: list[str] = field(default_factory=list)
    services_excluded: list[str] = field(default_factory=list)
    insurance_language: str = ""
    age_eligibility: dict[str, str] = field(default_factory=dict)
    geo_constraints: dict[str, Any] = field(default_factory=dict)
    legal_or_verification_notes: list[str] = field(default_factory=list)
    approved_ctas: list[str] = field(default_factory=list)
    blocked_ctas: list[str] = field(default_factory=list)
    approved_superlatives: list[str] = field(default_factory=list)
    delivery_modes: list[str] = field(default_factory=list)
    availability_claims: list[str] = field(default_factory=list)
    landing_page_fallback_allowed: bool = False

    @classmethod
    def from_file(cls, path: Path) -> "CopyConstraints":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            approved_claims=list(data.get("approved_claims", [])),
            blocked_claims=list(data.get("blocked_claims", [])),
            services_with_capacity=list(data.get("services_with_capacity", [])),
            services_excluded=list(data.get("services_excluded", [])),
            insurance_language=str(data.get("insurance_language", "")),
            age_eligibility=dict(data.get("age_eligibility", {})),
            geo_constraints=dict(data.get("geo_constraints", {})),
            legal_or_verification_notes=list(data.get("legal_or_verification_notes", [])),
            approved_ctas=list(data.get("approved_ctas", [])),
            blocked_ctas=list(data.get("blocked_ctas", [])),
            approved_superlatives=list(data.get("approved_superlatives", [])),
            delivery_modes=list(data.get("delivery_modes", [])),
            availability_claims=list(data.get("availability_claims", [])),
            landing_page_fallback_allowed=bool(data.get("landing_page_fallback_allowed", False)),
        )


@dataclass(frozen=True)
class CopyCandidate:
    campaign: str
    ad_group: str
    asset_type: str
    slot: int
    text: str
    chars: int
    role: str
    source: str
    grade: str
    status: str
    issues: list[str]


@dataclass(frozen=True)
class RsaCopyBundle:
    campaign: str
    ad_group: str
    headlines: list[str]
    descriptions: list[str]
    candidates: list[CopyCandidate]


def clean_words(value: str) -> str:
    replacements = {
        "treatment": "support",
        "treatments": "support",
        "treat": "support",
        "treats": "support",
        "diagnose": "evaluate",
        "diagnosis": "evaluation",
        "cure": "support",
        "guaranteed": "available",
        "guarantee": "available",
    }
    cleaned = value
    for source, replacement in replacements.items():
        cleaned = re.sub(rf"\b{re.escape(source)}\b", replacement, cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9 &/+.-]+", " ", cleaned)).strip()


def title_words(value: str) -> str:
    acronyms = {
        "adhd": "ADHD",
        "cbt": "CBT",
        "dbt": "DBT",
        "emdr": "EMDR",
        "lgbtq": "LGBTQ",
        "lgbtqia": "LGBTQIA",
        "va": "VA",
        "dc": "DC",
        "bcbs": "BCBS",
        "iep": "IEP",
    }
    small = {"and", "or", "for", "of", "the", "to", "in", "with"}
    words: list[str] = []
    for index, word in enumerate(clean_words(value).replace("-", " - ").split()):
        lower = word.lower()
        if lower == "-":
            words.append("-")
        elif lower in acronyms:
            words.append(acronyms[lower])
        elif index > 0 and lower in small:
            words.append(lower)
        else:
            words.append(lower.capitalize())
    return " ".join(words).replace(" - ", "-")


def path_part(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "", title_words(value))
    return cleaned[:PATH_MAX] or "Services"


def fit_headline(value: str) -> str:
    text = title_words(value)
    for suffix in FILLER_SUFFIXES:
        if HEADLINE_MIN <= len(text) <= HEADLINE_MAX:
            return text
        if len(text) < HEADLINE_MIN:
            text = f"{text}{suffix}"
    if len(text) < HEADLINE_MIN:
        text = f"{text} Support Options"
    if len(text) > HEADLINE_MAX:
        text = truncate_to_word(text, HEADLINE_MAX).rstrip(" -/&")
    while len(text) < HEADLINE_MIN:
        text = f"{text} Care"
        if len(text) > HEADLINE_MAX:
            text = truncate_to_word(text, HEADLINE_MAX).rstrip(" -/&")
            break
    return text


def fit_description(value: str) -> str:
    text = clean_words(value).replace("!", ".")
    if len(text) <= DESCRIPTION_MAX:
        return text
    return trim_incomplete_tail(text[:DESCRIPTION_MAX].rstrip(" ,;")) + "."


def append_cta(value: str, cta: str) -> str:
    text = clean_words(value).rstrip(".")
    cta = clean_words(cta).rstrip(".")
    if cta.lower() in text.lower():
        return fit_description(text)
    joined = f"{text}. {cta}."
    if len(joined) <= DESCRIPTION_MAX:
        return joined
    remaining = DESCRIPTION_MAX - len(f". {cta}.")
    return f"{trim_incomplete_tail(truncate_to_word(text, remaining))}. {cta}."


def truncate_to_word(value: str, limit: int) -> str:
    text = value[:limit].rstrip(" ,;")
    if " " in text and len(value) > limit:
        text = text.rsplit(" ", 1)[0].rstrip(" ,;")
    return text


def trim_incomplete_tail(value: str) -> str:
    words = value.rstrip(" ,;.").split()
    while words and words[-1].lower() in INCOMPLETE_TRAILING_WORDS:
        words.pop()
    return " ".join(words) if words else value.rstrip(" ,;.")


def description_ctas(constraints: CopyConstraints, source_evidence: dict[str, Any] | None = None) -> list[str]:
    blocked = {cta.lower() for cta in constraints.blocked_ctas}
    candidates = constraints.approved_ctas or contextual_ctas(source_evidence or {})
    output = [cta for cta in candidates if cta and cta.lower() not in blocked]
    return output or [cta for cta in DEFAULT_CTAS if cta.lower() not in blocked] or ["Request Details"]


def contextual_ctas(source_evidence: dict[str, Any]) -> list[str]:
    service_logic = source_evidence.get("service_logic", {})
    buyer_type = str(service_logic.get("buyer_type", "") if isinstance(service_logic, dict) else "").lower()
    concept_text = " ".join(str(token) for token in (service_logic.get("concept_tokens", []) if isinstance(service_logic, dict) else [])).lower()
    mechanism = str(service_logic.get("service_mechanism", "") if isinstance(service_logic, dict) else "").lower()
    combined = " ".join([concept_text, mechanism])

    if any(term in combined for term in ("chef", "dining", "dinner", "food", "menu", "pairing", "reservation", "restaurant", "tasting", "wine")):
        return RESTAURANT_CTAS
    if buyer_type in {"b2b", "b2b2c"} or any(term in combined for term in ("academy", "development", "organization", "staff", "team", "training", "workplace")):
        return B2B_CTAS
    if any(term in combined for term in ("behavioral", "care", "clinical", "consulting", "counseling", "health", "therapy")):
        return CONSULTATIVE_CTAS
    if any(term in combined for term in ("repair", "restoration", "renovation", "local service")):
        return LOCAL_SERVICE_CTAS
    return DEFAULT_CTAS


def keyword_roots(service: str) -> list[str]:
    base = clean_words(service).lower()
    roots = [
        base,
        f"{base} services",
        f"{base} near me",
        f"{base} consultation",
        f"{base} appointments",
    ]
    seen: set[str] = set()
    output: list[str] = []
    for root in roots:
        if root and root not in seen:
            output.append(title_words(root))
            seen.add(root)
    return output


def build_rsa_copy(
    *,
    campaign: str,
    ad_group: str,
    service: str,
    client_name: str,
    geo: list[str],
    keywords: list[str],
    constraints: CopyConstraints,
    source_evidence: dict[str, Any] | None = None,
) -> RsaCopyBundle:
    """Build passed RSA copy and retain rejected candidate records."""
    geo_label = first_geo_label(geo)
    service_label = title_words(service)
    keyword = title_words(keywords[0] if keywords else service)
    source_evidence = source_evidence or {}
    landing_claims = source_evidence.get("landing_page_claims", [])
    service_logic = source_evidence.get("service_logic", {})
    allowed_delivery = allowed_delivery_claims(constraints, source_evidence)
    ctas = description_ctas(constraints, source_evidence)
    candidates: list[CopyCandidate] = []

    headline_specs = [
        (f"Review {keyword} Fit", "keyword_match"),
        (f"Top {keyword}", "soft_superlative"),
        (f"{service_label} Near You", "keyword_match"),
        (f"{service_label} Appointments", "cta"),
        (f"Book {service_label} Today", "cta"),
        (f"{geo_label} {service_label}", "geo"),
        (f"Local {service_label} Support", "geo"),
        (f"Clear {service_label} Next Steps", "benefit"),
        (f"Support That Fits Your Goals", "benefit"),
        (f"Compare {service_label} Options", "benefit"),
        (f"Trusted {service_label} Team", "credential"),
        (f"Experienced Service Support", "credential"),
        (f"Is {service_label} Right For You?", "question"),
        (f"Need {service_label} Help?", "question"),
        (f"Request {service_label} Details", "cta"),
        (client_name, "brand"),
        (f"{client_name} Service Team", "brand"),
        ("Appointments Available Today", "cta"),
        ("Start With A Focused Consult", "cta"),
    ]

    passed_headlines: list[str] = []
    seen: set[str] = set()
    for raw, role in headline_specs:
        text = fit_headline(raw)
        if text.lower() in seen:
            continue
        seen.add(text.lower())
        candidate = evaluate_candidate(
            campaign=campaign,
            ad_group=ad_group,
            asset_type="headline",
            slot=len(passed_headlines) + 1,
            text=text,
            role=role,
            source="copy_engine",
            constraints=constraints,
            source_evidence=source_evidence,
        )
        candidates.append(candidate)
        if candidate.status == "pass":
            partial_audit = audit_rsa_headlines(
                ad_group=ad_group,
                service_label=service_label,
                client_name=client_name,
                headlines=[*passed_headlines, text],
            )
            blocking = [issue for issue in partial_audit.issues if issue.rule != "headline_count"]
            if blocking:
                continue
            passed_headlines.append(text)
        if len(passed_headlines) == 15:
            break

    for text in generate_quality_headlines(client_name=client_name, service_label=service_label, ad_group=ad_group):
        if len(passed_headlines) == 15:
            break
        if text.lower() in seen:
            continue
        candidate = evaluate_candidate(
            campaign=campaign,
            ad_group=ad_group,
            asset_type="headline",
            slot=len(passed_headlines) + 1,
            text=text,
            role="fallback",
            source="quality_headline_generator",
            constraints=constraints,
            source_evidence=source_evidence,
        )
        candidates.append(candidate)
        seen.add(text.lower())
        if candidate.status != "pass":
            continue
        partial_audit = audit_rsa_headlines(
            ad_group=ad_group,
            service_label=service_label,
            client_name=client_name,
            headlines=[*passed_headlines, text],
        )
        blocking = [issue for issue in partial_audit.issues if issue.rule != "headline_count"]
        if blocking:
            continue
        passed_headlines.append(text)

    while len(passed_headlines) < 15:
        fallback = fit_headline(f"{service_label} Support {len(passed_headlines) + 1}")
        candidate = evaluate_candidate(
            campaign=campaign,
            ad_group=ad_group,
            asset_type="headline",
            slot=len(passed_headlines) + 1,
            text=fallback,
            role="fallback",
            source="copy_engine_fallback",
            constraints=constraints,
            source_evidence=source_evidence,
        )
        candidates.append(candidate)
        if candidate.status != "pass":
            raise ValueError(f"Could not generate passing headline for {ad_group}: {candidate.issues}")
        passed_headlines.append(fallback)
    enforce_headline_mix(ad_group, candidates, passed_headlines)

    value_prop = first_value_prop(landing_claims) or service_logic_value_prop(service_logic) or "clear next steps and practical support"
    delivery_line = delivery_description_fragment(allowed_delivery)
    mechanism = service_logic_mechanism(service_logic) or f"{service_label.lower()} support"
    outcome = service_logic_outcome(service_logic) or value_prop
    description_specs = service_description_specs(
        keyword=keyword,
        client_name=client_name,
        value_prop=value_prop,
        delivery_line=delivery_line,
        mechanism=mechanism,
        outcome=outcome,
        service_logic=service_logic,
        ctas=ctas,
        insurance_language=constraints.insurance_language,
    )
    passed_descriptions: list[str] = []
    for raw, role in description_specs:
        text = fit_description(raw)
        candidate = evaluate_candidate(
            campaign=campaign,
            ad_group=ad_group,
            asset_type="description",
            slot=len(passed_descriptions) + 1,
            text=text,
            role=role,
            source="copy_engine",
            constraints=constraints,
            source_evidence=source_evidence,
        )
        candidates.append(candidate)
        if candidate.status == "pass":
            passed_descriptions.append(text)
    if len(passed_descriptions) != 4:
        failed = [candidate for candidate in candidates if candidate.asset_type == "description" and candidate.status != "pass"]
        raise ValueError(f"Could not generate 4 passing descriptions for {ad_group}: {failed}")

    return RsaCopyBundle(
        campaign=campaign,
        ad_group=ad_group,
        headlines=passed_headlines,
        descriptions=passed_descriptions,
        candidates=candidates,
    )


def enforce_headline_mix(ad_group: str, candidates: list[CopyCandidate], passed_headlines: list[str]) -> None:
    passed_texts = set(passed_headlines)
    roles = {
        candidate.role
        for candidate in candidates
        if candidate.asset_type == "headline" and candidate.status == "pass" and candidate.text in passed_texts
    }
    required = {"keyword_match", "geo", "benefit", "cta"}
    missing = sorted(required - roles)
    if not ({"credential", "soft_superlative"} & roles):
        missing.append("proof_or_availability")
    if missing:
        raise ValueError(f"Headline mix failed for {ad_group}: missing {missing}")


def service_description_specs(
    *,
    keyword: str,
    client_name: str,
    value_prop: str,
    delivery_line: str,
    mechanism: str,
    outcome: str,
    service_logic: Any,
    ctas: list[str],
    insurance_language: str,
) -> list[tuple[str, str]]:
    concepts = service_specific_terms({"service_logic": service_logic})
    if concepts & {"chef", "dining", "dinner", "food", "menu", "pairing", "reservation", "restaurant", "tasting", "wine"}:
        return [
            (append_cta("Guests review tasting menu reservations for Guatemalan dining", ctas[0]), "service_logic"),
            (append_cta("Guests confirm restaurant reservation fit for contemporary dining", ctas[1 % len(ctas)]), "service_logic"),
            (append_cta("Guests review tasting menu seating for Guatemalan dining", ctas[2 % len(ctas)]), "service_logic"),
            (append_cta("Guests schedule a private tasting menu with contemporary dining", ctas[3 % len(ctas)]), "service_logic"),
        ]
    if "counselor" in concepts and {"academy", "counseling", "training"} & concepts:
        return [
            (append_cta("Help organizations train staff in lay counseling skills for care access", ctas[0]), "service_logic"),
            (append_cta("Help organizations build lay counselor teams for mental health access", ctas[1 % len(ctas)]), "service_logic"),
            (append_cta("Review staff training for lay counseling skills and care capacity", ctas[2 % len(ctas)]), "service_logic"),
            (append_cta("Plan lay counselor training for organizations to expand mental health access", ctas[3 % len(ctas)]), "service_logic"),
        ]

    buyer = service_logic_buyer_term(service_logic)
    mechanism_short = compact_service_phrase(mechanism)
    outcome_short = compact_outcome_phrase(outcome or value_prop)
    description_outcome = outcome_short if len(outcome_short) >= 22 else f"{outcome_short} and support"
    delivery_copy = ""
    if delivery_line and delivery_line != "available next steps":
        delivery_copy = f" with {delivery_line}"
    differentiator = (
        f"{buyer.title()} compare {mechanism_short}{delivery_copy}"
        if delivery_copy
        else f"{buyer.title()} compare trusted {mechanism_short} for {description_outcome}"
    )
    return [
        (
            append_cta(
                f"{buyer.title()} compare {mechanism_short} for {description_outcome}",
                ctas[0],
            ),
            "service_logic",
        ),
        (
            append_cta(
                f"{buyer.title()} review {mechanism_short} for {description_outcome}",
                ctas[1 % len(ctas)],
            ),
            "service_logic",
        ),
        (
            append_cta(
                f"{buyer.title()} plan {mechanism_short} for {description_outcome}",
                ctas[2 % len(ctas)],
            ),
            "service_logic",
        ),
        (
            append_cta(
                insurance_language or differentiator,
                ctas[3 % len(ctas)],
            ),
            "differentiator",
        ),
    ]


def service_logic_buyer_term(service_logic: Any) -> str:
    if not isinstance(service_logic, dict):
        return "customers"
    buyer = str(service_logic.get("buyer", "")).lower()
    if "organization" in buyer:
        return "organizations"
    if "employer" in buyer:
        return "employers"
    if "clinical" in buyer:
        return "clinical teams"
    if "team" in buyer:
        return "teams"
    if "guest" in buyer:
        return "guests"
    return "customers"


def compact_service_phrase(value: str) -> str:
    text = clean_words(value).lower()
    replacements = {
        "employee mental health support and counseling access": "mental health support",
        "empathic communication training": "communication training",
        "integrated behavioral health consulting": "behavioral health",
        "learning and development programs": "development training",
        "human-centered care consulting": "human-centered care",
        "trauma-informed care training": "trauma-informed training",
    }
    if text in replacements:
        return replacements[text]
    words = [
        word
        for word in text.split()
        if word not in {"and", "program", "programs", "service", "services"}
    ]
    return " ".join(words[:4]) or "service support"


def compact_outcome_phrase(value: str) -> str:
    text = clean_words(value).lower()
    text = text.replace("clearer service options and next steps", "clearer next steps")
    text = text.replace("better employee wellbeing, fewer sick days, and easier counseling access", "employee wellbeing support")
    text = text.replace("better employee wellbeing fewer sick days and easier counseling access", "employee wellbeing support")
    text = text.replace("more coordinated behavioral health support inside care delivery", "coordinated care support")
    text = text.replace("more empathic human-centered communication", "empathic communication")
    text = text.replace("stronger staff skills and clearer support practices", "staff skills")
    text = text.replace("more human-centered care delivery", "human-centered care")
    text = text.replace("more trauma-informed care and support interactions", "trauma-informed support")
    words = [word for word in text.split() if word not in {"and", "more"}]
    return " ".join(words[:4]) or "clearer next steps"


def evaluate_candidate(
    *,
    campaign: str,
    ad_group: str,
    asset_type: str,
    slot: int,
    text: str,
    role: str,
    source: str,
    constraints: CopyConstraints,
    source_evidence: dict[str, Any] | None = None,
) -> CopyCandidate:
    issues = candidate_issues(asset_type, text, constraints, source_evidence or {})
    grade = "B" if not issues else "F"
    return CopyCandidate(
        campaign=campaign,
        ad_group=ad_group,
        asset_type=asset_type,
        slot=slot,
        text=text,
        chars=len(text),
        role=role,
        source=source,
        grade=grade,
        status="pass" if not issues else "fail",
        issues=issues,
    )


def candidate_issues(
    asset_type: str,
    text: str,
    constraints: CopyConstraints,
    source_evidence: dict[str, Any] | None = None,
) -> list[str]:
    issues: list[str] = []
    words = [word for word in re.split(r"\s+", text.strip()) if word]
    lower = text.lower()
    source_evidence = source_evidence or {}

    if asset_type == "headline":
        if len(text) > HEADLINE_MAX:
            issues.append("headline_over_limit")
        if len(text) < HEADLINE_MIN:
            issues.append("headline_under_value_minimum")
        if len(words) < 2:
            issues.append("bare_or_one_word_headline")
        if has_unverified_superlative(text, constraints):
            issues.append("unverified_superlative_claim")
    elif asset_type == "description":
        if len(text) > DESCRIPTION_MAX:
            issues.append("description_over_limit")
        if len(text) < DESCRIPTION_MIN:
            issues.append("description_under_value_minimum")
        if not has_approved_cta(text, constraints, source_evidence):
            issues.append("description_missing_cta")
        if not has_value_prop(text):
            issues.append("description_missing_value_prop")
        if has_generic_description_phrase(text):
            issues.append("description_generic_workflow_language")
        if has_incomplete_description_phrase(text):
            issues.append("description_incomplete_phrase")
        if not has_service_specific_description(text, source_evidence):
            issues.append("description_missing_service_specificity")

    for claim in constraints.blocked_claims:
        if claim and claim.lower() in lower:
            issues.append(f"blocked_claim:{claim}")
    for term in POLICY_RISK_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", lower):
            issues.append(f"policy_risk:{term}")
    if "!" in text:
        issues.append("exclamation_mark")
    for claim in unverified_delivery_claims(text, constraints, source_evidence):
        issues.append(f"unverified_delivery_claim:{claim}")
    return issues


def has_approved_cta(text: str, constraints: CopyConstraints, source_evidence: dict[str, Any] | None = None) -> bool:
    lower = text.lower()
    for cta in constraints.blocked_ctas:
        if cta and cta.lower() in lower:
            return False
    return any(cta.lower() in lower for cta in description_ctas(constraints, source_evidence or {}))


def has_value_prop(text: str) -> bool:
    tokens = {token for token in re.split(r"\W+", text.lower()) if token}
    return bool(tokens & VALUE_PROP_TERMS)


def has_generic_description_phrase(text: str) -> bool:
    lower = text.lower()
    return any(phrase in lower for phrase in GENERIC_DESCRIPTION_PHRASES)


def has_incomplete_description_phrase(text: str) -> bool:
    return bool(re.search(r"\b(and|for|through|to|via|with)\.(?:\s|$)", text.strip(), re.IGNORECASE))


def has_service_specific_description(text: str, source_evidence: dict[str, Any]) -> bool:
    required = service_specific_terms(source_evidence)
    if not required:
        return True
    tokens = set(tokenize_for_specificity(text))
    return bool(tokens & required)


def service_specific_terms(source_evidence: dict[str, Any]) -> set[str]:
    raw_terms: list[Any] = []
    for key in ("service_terms", "matched_terms", "message_match_terms"):
        raw_terms.extend(source_evidence.get(key, []) or [])
    service_logic = source_evidence.get("service_logic", {})
    if isinstance(service_logic, dict):
        raw_terms.extend(service_logic.get("concept_tokens", []) or [])
        raw_terms.extend(tokenize_for_specificity(str(service_logic.get("service_mechanism", ""))))
        raw_terms.extend(tokenize_for_specificity(str(service_logic.get("outcome", ""))))
    return {
        token
        for value in raw_terms
        for token in tokenize_for_specificity(str(value))
        if token not in GENERIC_DESCRIPTION_TERMS and len(token) >= 4
    }


def tokenize_for_specificity(value: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", value.lower()) if token]


def service_logic_value_prop(service_logic: Any) -> str:
    if not isinstance(service_logic, dict):
        return ""
    for key in ("outcome", "service_mechanism", "problem"):
        text = clean_words(str(service_logic.get(key, ""))).lower()
        if text and has_value_prop(text):
            return text[:70].rstrip(" ,;")
    return ""


def service_logic_mechanism(service_logic: Any) -> str:
    if not isinstance(service_logic, dict):
        return ""
    return clean_words(str(service_logic.get("service_mechanism", ""))).lower()


def service_logic_outcome(service_logic: Any) -> str:
    if not isinstance(service_logic, dict):
        return ""
    return clean_words(str(service_logic.get("outcome", ""))).lower()


def has_unverified_superlative(text: str, constraints: CopyConstraints) -> bool:
    approved = {value.lower() for value in constraints.approved_superlatives}
    lower = text.lower()
    if "#1" in lower and "#1" not in approved:
        return True
    if re.search(r"\bbest\b", lower) and "best" not in approved:
        return True
    return False


def allowed_delivery_claims(constraints: CopyConstraints, source_evidence: dict[str, Any]) -> set[str]:
    values = set()
    for source in (
        constraints.delivery_modes,
        constraints.availability_claims,
        source_evidence.get("delivery_modes", []),
        source_evidence.get("availability_signals", []),
        source_evidence.get("copy_allowed_claims", []),
    ):
        for value in source or []:
            normalized = normalize_delivery_claim(str(value))
            if normalized:
                values.add(normalized)
    return values


def normalize_delivery_claim(value: str) -> str:
    lower = value.lower().replace("_", " ")
    if DELIVERY_CLAIM_PATTERNS["24_7"].search(lower):
        return "24_7"
    if DELIVERY_CLAIM_PATTERNS["virtual"].search(lower):
        return "virtual"
    if DELIVERY_CLAIM_PATTERNS["in_person"].search(lower):
        return "in_person"
    return ""


def unverified_delivery_claims(text: str, constraints: CopyConstraints, source_evidence: dict[str, Any]) -> list[str]:
    allowed = allowed_delivery_claims(constraints, source_evidence)
    issues = []
    for claim, pattern in DELIVERY_CLAIM_PATTERNS.items():
        if pattern.search(text) and claim not in allowed:
            issues.append(claim)
    return issues


def first_value_prop(claims: list[Any]) -> str:
    for claim in claims:
        text = clean_words(str(claim)).lower()
        if text and has_value_prop(text):
            return text[:70].rstrip(" ,;")
    return ""


def delivery_description_fragment(allowed_delivery: set[str]) -> str:
    if {"virtual", "in_person"} <= allowed_delivery:
        return "online and in-person options"
    if "virtual" in allowed_delivery:
        return "online service options"
    if "in_person" in allowed_delivery:
        return "in-person service options"
    if "24_7" in allowed_delivery:
        return "availability options"
    return "available next steps"


def first_geo_label(geo: list[str]) -> str:
    if not geo:
        return "Local"
    value = geo[0].split("|", 1)[0]
    return title_words(value.split(",", 1)[0]) or "Local"


def write_copy_candidates(path: Path, candidates: list[CopyCandidate]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(candidate) for candidate in candidates], indent=2) + "\n", encoding="utf-8")
    return path


def write_rsa_copy_matrix(path: Path, candidates: list[CopyCandidate]) -> Path:
    failed = [candidate for candidate in candidates if candidate.status != "pass"]
    if failed:
        raise ValueError(f"Cannot write RSA copy matrix with failed candidates: {len(failed)}")

    fieldnames = ["campaign", "ad_group", "asset_type", "slot", "text", "chars", "role", "source", "grade", "status"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for candidate in candidates:
            row = asdict(candidate)
            row.pop("issues", None)
            writer.writerow(row)
    return path


__all__ = [
    "CopyCandidate",
    "CopyConstraints",
    "RsaCopyBundle",
    "build_rsa_copy",
    "candidate_issues",
    "fit_description",
    "fit_headline",
    "keyword_roots",
    "path_part",
    "write_copy_candidates",
    "write_rsa_copy_matrix",
]
