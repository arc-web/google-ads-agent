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

DEFAULT_CTAS = ["Call Today", "Book Today", "Request Details", "Apply Today", "Schedule Today"]
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
}
DELIVERY_CLAIM_PATTERNS = {
    "virtual": re.compile(r"\b(virtual|online|telehealth|remote)\b", re.IGNORECASE),
    "in_person": re.compile(r"\b(in-person|in person|office visit|on-site|onsite)\b", re.IGNORECASE),
    "24_7": re.compile(r"\b(24/7|24 hours|after hours|answering service)\b", re.IGNORECASE),
}


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
    return text[:DESCRIPTION_MAX].rstrip(" ,;") + "."


def append_cta(value: str, cta: str) -> str:
    text = clean_words(value).rstrip(".")
    cta = clean_words(cta).rstrip(".")
    if cta.lower() in text.lower():
        return fit_description(text)
    joined = f"{text}. {cta}."
    if len(joined) <= DESCRIPTION_MAX:
        return joined
    remaining = DESCRIPTION_MAX - len(f". {cta}.")
    return f"{truncate_to_word(text, remaining)}. {cta}."


def truncate_to_word(value: str, limit: int) -> str:
    text = value[:limit].rstrip(" ,;")
    if " " in text and len(value) > limit:
        text = text.rsplit(" ", 1)[0].rstrip(" ,;")
    return text


def description_ctas(constraints: CopyConstraints) -> list[str]:
    blocked = {cta.lower() for cta in constraints.blocked_ctas}
    candidates = constraints.approved_ctas or DEFAULT_CTAS
    output = [cta for cta in candidates if cta and cta.lower() not in blocked]
    return output or [cta for cta in DEFAULT_CTAS if cta.lower() not in blocked] or ["Request Details"]


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
    allowed_delivery = allowed_delivery_claims(constraints, source_evidence)
    ctas = description_ctas(constraints)
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

    value_prop = first_value_prop(landing_claims) or "clear next steps and practical support"
    delivery_line = delivery_description_fragment(allowed_delivery)
    description_specs = [
        (
            append_cta(
                f"Review {keyword.lower()} options with {value_prop} for your next step",
                ctas[0],
            ),
            "benefit_cta",
        ),
        (
            append_cta(
                f"Compare fit, availability, budget, and location before choosing {service_label.lower()}",
                ctas[1 % len(ctas)],
            ),
            "zero_risk",
        ),
        (
            append_cta(
                f"Local {service_label.lower()} support with practical guidance from intake through planning",
                ctas[2 % len(ctas)],
            ),
            "geo",
        ),
        (
            append_cta(
                constraints.insurance_language
                or f"{client_name} helps confirm service fit, timing, and {delivery_line}",
                ctas[3 % len(ctas)],
            ),
            "differentiator",
        ),
    ]
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
        if not has_approved_cta(text, constraints):
            issues.append("description_missing_cta")
        if not has_value_prop(text):
            issues.append("description_missing_value_prop")

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


def has_approved_cta(text: str, constraints: CopyConstraints) -> bool:
    lower = text.lower()
    for cta in constraints.blocked_ctas:
        if cta and cta.lower() in lower:
            return False
    return any(cta.lower() in lower for cta in description_ctas(constraints))


def has_value_prop(text: str) -> bool:
    tokens = {token for token in re.split(r"\W+", text.lower()) if token}
    return bool(tokens & VALUE_PROP_TERMS)


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
