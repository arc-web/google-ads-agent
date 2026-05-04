"""Deterministic quality gates for responsive search ad headlines."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any


HEADLINE_MINIMUM = 25
HEADLINE_LIMIT = 30
REQUIRED_HEADLINE_COUNT = 15
SEMANTIC_OVERLAP_THRESHOLD = 0.8
REPEATED_ROOT_LIMIT = 3

STOP_WORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "in",
    "near",
    "now",
    "of",
    "or",
    "the",
    "to",
    "today",
    "with",
    "your",
}
GENERIC_WORDS = {
    "answers",
    "appointment",
    "appointments",
    "book",
    "call",
    "care",
    "clear",
    "compare",
    "consult",
    "consulting",
    "details",
    "expert",
    "experts",
    "focused",
    "guidance",
    "help",
    "local",
    "next",
    "options",
    "plan",
    "planning",
    "practical",
    "program",
    "request",
    "review",
    "schedule",
    "service",
    "services",
    "start",
    "step",
    "steps",
    "support",
    "team",
    "today",
    "top",
    "trusted",
}
GENERIC_VALUE_HEADLINES = {
    "clear implementation steps",
    "compare support options today",
    "plan your next service step",
    "practical support planning",
    "review team support needs",
    "start with a focused review",
    "support for better access",
    "talk with a consulting team",
}
APPROVED_SHORT_TOKENS = {"ai", "api", "cfo", "dc", "em", "hr", "it", "ny", "pr", "uk", "us", "va"}
BROKEN_ENDINGS = {
    "appoi",
    "appointm",
    "answe",
    "communicat",
    "con",
    "consu",
    "develo",
    "developme",
    "detai",
    "exp",
    "fro",
    "hea",
    "hel",
    "optio",
    "plann",
    "servi",
    "ste",
    "su",
    "suppo",
    "trai",
    "tr",
}


@dataclass(frozen=True)
class HeadlineQualityIssue:
    rule: str
    message: str
    slots: list[int] = field(default_factory=list)
    headlines: list[str] = field(default_factory=list)
    severity: str = "error"


@dataclass(frozen=True)
class RsaHeadlineAudit:
    status: str
    ad_group: str
    service_label: str
    client_name: str
    headline_count: int
    headline_characters: list[dict[str, int | str]]
    issues: list[HeadlineQualityIssue]
    duplicate_groups: list[list[str]]
    repeated_root_counts: dict[str, int]
    broken_truncations: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["issues"] = [asdict(issue) for issue in self.issues]
        return payload


def clean_text(value: str) -> str:
    value = re.sub(r"(?i)\b([a-z]+)['’]s\b", r"\1", value)
    return re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9 &/+.-]+", " ", value)).strip()


def title_text(value: str) -> str:
    small_words = {"a", "an", "and", "or", "for", "of", "the", "to", "in", "with", "from"}
    acronyms = {"ai", "api", "cfo", "dc", "em", "hr", "it", "pr", "uk", "us", "va"}
    words: list[str] = []
    for index, word in enumerate(clean_text(value).replace("-", " ").split()):
        lower = word.lower()
        if lower in acronyms:
            words.append(lower.upper())
        elif index > 0 and lower in small_words:
            words.append(lower)
        else:
            words.append(lower.capitalize())
    return " ".join(words)


def normalize_headline(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()


def tokenize(value: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z0-9]+", value)]


def significant_tokens(value: str) -> list[str]:
    return [token for token in tokenize(value) if token not in STOP_WORDS and token not in GENERIC_WORDS]


def semantic_signature(value: str) -> frozenset[str]:
    tokens = significant_tokens(value)
    if tokens:
        return frozenset(tokens)
    return frozenset(token for token in tokenize(value) if token not in STOP_WORDS)


def root_signature(value: str) -> str:
    tokens = significant_tokens(value)
    if not tokens:
        tokens = [token for token in tokenize(value) if token not in STOP_WORDS]
    return " ".join(tokens[:3])


def has_broken_truncation(value: str) -> bool:
    stripped = value.strip()
    if re.search(r"\s[A-Z]$", stripped):
        return True
    tokens = tokenize(stripped)
    if not tokens:
        return False
    last = tokens[-1]
    if last in BROKEN_ENDINGS:
        return True
    if len(last) <= 2 and last not in APPROVED_SHORT_TOKENS and not last.isdigit():
        return True
    return False


def is_low_value_filler(value: str, service_label: str) -> bool:
    normalized = normalize_headline(value)
    service_normalized = normalize_headline(service_label)
    if service_normalized and normalized == service_normalized:
        return True
    if re.search(r"\bsupport\s+\d+$", normalized):
        return True
    if re.fullmatch(r"(service|services|support|care|options)(\s+\w+){0,2}", normalized):
        return True
    return False


def service_logic_tokens(service_logic: dict[str, Any] | None) -> set[str]:
    if not service_logic:
        return set()
    output: set[str] = set()
    for token in service_logic.get("concept_tokens", []) or []:
        cleaned = normalize_headline(str(token))
        if cleaned:
            output.add(cleaned)
    explicit = set(output)
    for field in ("buyer", "end_user", "service_mechanism", "problem", "outcome"):
        output.update(significant_tokens(str(service_logic.get(field, ""))))
    return {token for token in output if (token in explicit or token not in GENERIC_WORDS) and len(token) > 2}


def headline_matches_service_logic(headline: str, service_logic: dict[str, Any] | None) -> bool:
    concepts = service_logic_tokens(service_logic)
    if not concepts:
        return True
    return bool(set(tokenize(headline)) & concepts)


def is_wrong_buyer_type_headline(headline: str, service_logic: dict[str, Any] | None) -> bool:
    if not service_logic:
        return False
    if str(service_logic.get("buyer_type", "")) not in {"b2b", "b2b2c"}:
        return False
    normalized = normalize_headline(headline)
    return any(
        pattern in normalized
        for pattern in (
            "appointments",
            "book",
            "counseling for you",
            "near you",
            "therapy for you",
        )
    )


def audit_rsa_headlines(
    *,
    ad_group: str,
    headlines: list[str],
    service_label: str = "",
    client_name: str = "",
    service_logic: dict[str, Any] | None = None,
) -> RsaHeadlineAudit:
    issues: list[HeadlineQualityIssue] = []
    cleaned = [clean_text(headline) for headline in headlines]
    character_rows = [
        {"slot": index, "headline": headline, "chars": len(headline)}
        for index, headline in enumerate(cleaned, start=1)
    ]

    if len(cleaned) != REQUIRED_HEADLINE_COUNT:
        issues.append(
            HeadlineQualityIssue(
                rule="headline_count",
                message=f"RSA must include exactly {REQUIRED_HEADLINE_COUNT} headlines.",
                headlines=cleaned,
            )
        )

    if service_logic and service_logic.get("status") != "pass":
        issues.append(
            HeadlineQualityIssue(
                rule="service_logic_insufficient_evidence",
                message="Service logic research did not provide enough evidence for ad copy generation.",
                headlines=cleaned,
            )
        )

    for index, headline in enumerate(cleaned, start=1):
        if not headline:
            issues.append(
                HeadlineQualityIssue(
                    rule="rsa_headline_required",
                    message="RSA headline is required.",
                    slots=[index],
                    headlines=[headline],
                )
            )
        elif len(headline) > HEADLINE_LIMIT:
            issues.append(
                HeadlineQualityIssue(
                    rule="headline_length",
                    message=f"Headline exceeds {HEADLINE_LIMIT} characters.",
                    slots=[index],
                    headlines=[headline],
                )
            )
        elif len(headline) < HEADLINE_MINIMUM:
            issues.append(
                HeadlineQualityIssue(
                    rule="headline_minimum_value",
                    message=f"Headline must use at least {HEADLINE_MINIMUM} characters with concrete value.",
                    slots=[index],
                    headlines=[headline],
                )
            )
        if headline and has_broken_truncation(headline):
            issues.append(
                HeadlineQualityIssue(
                    rule="headline_broken_truncation",
                    message="Headline appears to end with a cut-off word or dangling fragment.",
                    slots=[index],
                    headlines=[headline],
                )
            )
        if headline and is_low_value_filler(headline, service_label):
            issues.append(
                HeadlineQualityIssue(
                    rule="headline_low_value_filler",
                    message="Headline is a bare label or filler pattern, not usable ad copy.",
                    slots=[index],
                    headlines=[headline],
                )
            )
        if headline and service_logic and normalize_headline(headline) in GENERIC_VALUE_HEADLINES:
            issues.append(
                HeadlineQualityIssue(
                    rule="headline_generic_value",
                    message="Headline is too generic to communicate the service value.",
                    slots=[index],
                    headlines=[headline],
                )
            )
        if headline and service_logic and not headline_matches_service_logic(headline, service_logic):
            issues.append(
                HeadlineQualityIssue(
                    rule="headline_missing_service_concept",
                    message="Headline does not map to the researched service concept.",
                    slots=[index],
                    headlines=[headline],
                )
            )
        if headline and is_wrong_buyer_type_headline(headline, service_logic):
            issues.append(
                HeadlineQualityIssue(
                    rule="headline_wrong_buyer_type",
                    message="Headline reads like direct consumer copy for a B2B or B2B2C service.",
                    slots=[index],
                    headlines=[headline],
                )
            )

    exact_slots: dict[str, list[int]] = defaultdict(list)
    exact_headlines: dict[str, list[str]] = defaultdict(list)
    for index, headline in enumerate(cleaned, start=1):
        normalized = normalize_headline(headline)
        if not normalized:
            continue
        exact_slots[normalized].append(index)
        exact_headlines[normalized].append(headline)
    duplicate_groups = [values for values in exact_headlines.values() if len(values) > 1]
    for normalized, slots in exact_slots.items():
        if len(slots) > 1:
            issues.append(
                HeadlineQualityIssue(
                    rule="headline_exact_duplicate",
                    message="RSA contains exact duplicate headlines.",
                    slots=slots,
                    headlines=exact_headlines[normalized],
                )
            )

    semantic_pairs: list[tuple[int, int, str, str]] = []
    signatures = [semantic_signature(headline) for headline in cleaned]
    for left_index, left_tokens in enumerate(signatures):
        if not left_tokens:
            continue
        for right_index in range(left_index + 1, len(signatures)):
            right_tokens = signatures[right_index]
            if not right_tokens:
                continue
            overlap = len(left_tokens & right_tokens) / max(len(left_tokens | right_tokens), 1)
            if overlap >= SEMANTIC_OVERLAP_THRESHOLD:
                semantic_pairs.append(
                    (left_index + 1, right_index + 1, cleaned[left_index], cleaned[right_index])
                )
    if semantic_pairs:
        first_pairs = semantic_pairs[:8]
        issues.append(
            HeadlineQualityIssue(
                rule="headline_semantic_duplicate",
                message="RSA repeats the same headline idea too often.",
                slots=sorted({slot for pair in first_pairs for slot in pair[:2]}),
                headlines=[headline for pair in first_pairs for headline in pair[2:]],
            )
        )

    roots = [root_signature(headline) for headline in cleaned if root_signature(headline)]
    repeated_roots = {
        root: count
        for root, count in Counter(roots).items()
        if count > REPEATED_ROOT_LIMIT and root
    }
    for root, count in repeated_roots.items():
        issues.append(
            HeadlineQualityIssue(
                rule="headline_repeated_root",
                message=f"Headline root `{root}` appears {count} times.",
                headlines=[headline for headline in cleaned if root_signature(headline) == root],
            )
        )

    broken = [headline for headline in cleaned if has_broken_truncation(headline)]
    return RsaHeadlineAudit(
        status="fail" if issues else "pass",
        ad_group=ad_group,
        service_label=service_label,
        client_name=client_name,
        headline_count=len(cleaned),
        headline_characters=character_rows,
        issues=issues,
        duplicate_groups=duplicate_groups,
        repeated_root_counts=repeated_roots,
        broken_truncations=broken,
    )


SERVICE_SPECIFIC_HEADLINES = {
    "tasting menu": [
        "Reserve A Tasting Menu",
        "Book A Tasting Menu Seat",
        "Mayan Tasting Menu Seats",
        "Guatemala Tasting Menu",
        "Fine Dining Tasting Menu",
        "Contemporary Dining Menu",
        "Book A Fine Dining Dinner",
        "Reserve A Dining Experience",
        "Tasting Menu Reservations",
        "Guatemalan Dining Experience",
        "Limited Seating Dinner",
        "Plan A Tasting Menu Dinner",
        "Reserve Dinner In Guatemala",
        "Book Contemporary Dining",
        "Mayan Dinner Experience",
    ],
    "chef": [
        "Reserve Chef Table Seating",
        "Book Chef Table Seating Now",
        "Chef Table In Guatemala City",
        "Chef Table Tasting Dinner",
        "Kitchen Counter Dining",
        "Book A Chef Table Dinner",
        "Limited Chef Table Seats Now",
        "Fine Dining Chef Table Seats",
        "Chef Choice Dinner Seats",
        "Reserve Kitchen Bar Seats",
        "Chef Table Reservations Now",
        "Plan A Chef Table Night Out",
        "Book A Kitchen Bar Dinner",
        "Guatemala Chef Table Dinner",
        "Reserve Chef Menu Seating",
    ],
    "fine dining": [
        "Book Fine Dining Tonight",
        "Reserve A Fine Dining Seat",
        "Fine Dining In Guatemala",
        "Guatemala City Fine Dining",
        "Contemporary Fine Dining",
        "Book A High End Dinner",
        "Reserve A Dining Experience",
        "Fine Dining Reservations",
        "Plan A Fine Dining Night",
        "Guatemalan Fine Dining",
        "Limited Seating Fine Dining",
        "Fine Dining Tasting Menu",
        "Book A Restaurant Seat",
        "Reserve Dinner In Guatemala",
        "Modern Guatemalan Dining",
    ],
    "guatemalan food": [
        "Contemporary Guatemalan Food",
        "Modern Guatemalan Dining",
        "Guatemalan Dining Experience",
        "Reserve Guatemalan Dining",
        "Book Guatemalan Fine Dining",
        "Mayan Inspired Dinner Menu",
        "Guatemala City Dining",
        "Book A Cultural Dinner",
        "Reserve A Story Driven Menu",
        "Guatemalan Tasting Menu",
        "Book A Popol Vuh Menu",
        "Fine Guatemalan Dining",
        "Plan A Guatemala Dinner",
        "Reserve Contemporary Dining",
        "Book A Restaurant Seat",
    ],
    "wine pairing": [
        "Book Dinner With Wine Pairing",
        "Reserve A Wine Pairing",
        "Wine Pairing Dinner Seats",
        "Tasting Menu Wine Pairing",
        "Fine Dining Wine Pairing",
        "Book A Paired Dinner",
        "Reserve Dinner And Wine",
        "Plan A Wine Pairing Dinner",
        "Guatemala Wine Pairing",
        "Wine Pairing Reservations",
        "Book A Tasting Menu Pairing",
        "Reserve A Paired Menu",
        "Pair Wine With Dinner",
        "Fine Dinner With Wine",
        "Book A Wine Pairing Seat",
    ],
    "repair": [
        "Affordable Repair Service Help",
        "Reliable Repair Service Plans",
        "Customer Repair Help Options",
        "Repair Support For Customers",
        "Repair Request Review Today",
        "Repair Planning For Customers",
        "Repair Service Fit Review",
        "Repair Details For Customers",
        "Repair Service Scope Review",
        "Repair Help For Customer Needs",
        "Repair Options For Customers",
        "Repair Cost Review Options",
        "Repair Timeline Review Help",
        "Repair Quality Review Help",
        "Repair Provider Fit Review",
        "Repair Project Scope Help",
        "Repair Service Budget Review",
        "Repair Issue Planning Help",
        "Repair Estimate Review Help",
        "Repair Process Review Help",
    ],
    "consulting": [
        "Consulting Service Fit Review",
        "Customer Consulting Options",
        "Consulting Planning Support",
        "Consulting Details Review",
        "Consulting Scope Review",
        "Reliable Consulting Plans",
        "Consulting Request Review",
        "Customer Consulting Support",
        "Consulting Service Options",
        "Consulting Help For Customers",
        "Consulting Needs Review",
        "Consulting Scope Review Help",
        "Consulting Timeline Planning",
        "Consulting Provider Fit Help",
        "Consulting Process Review",
        "Consulting Project Planning",
        "Consulting Service Roadmap",
        "Consulting Decision Support",
        "Consulting Strategy Review",
    ],
    "lay counselor": [
        "Lay Counselor Staff Training",
        "Train Staff In Counseling",
        "Build Lay Counselor Teams",
        "Mental Health Access Plan",
        "Care Team Counseling Skills",
        "Expand Mental Health Access",
        "Counseling Skills For Staff",
        "Lay Counselor Skills Course",
        "Grow Organizational Capacity",
        "Train Community Care Teams",
        "Lay Counseling For Teams",
        "Build Care Access Capacity",
        "Staff Mental Health Training",
        "Academy For Care Teams",
        "Skills To Expand Access",
    ],
    "employee mental health": [
        "Employee Wellbeing Planning",
        "Employee Mental Health Plans",
        "Workplace Mental Health Help",
        "Employee Counseling Access",
        "Support Employee Wellbeing",
        "Employee Care Access Review",
        "Workplace Counseling Access",
        "Plan Employee Support Paths",
        "Mental Health For Employees",
        "Employee Wellbeing Programs",
        "Employer Mental Health Help",
        "Improve Workplace Wellbeing",
        "Employee Support Planning",
        "Counseling Access For Teams",
        "Review Employee Care Needs",
    ],
    "integrated behavioral": [
        "Behavioral Health Consulting",
        "Integrated Care Consulting",
        "Integrated Care Team Support",
        "Behavioral Workflow Support",
        "Clinical Integration Plans",
        "Integrated Health Workflows",
        "Behavioral Care Workflows",
        "Coordinate Care Team Support",
        "Clinical Team Integration",
        "Integrated Patient Support",
        "Behavioral Health Planning",
        "Integrated Clinical Support",
        "Plan Behavioral Care Teams",
        "Health Workflow Consulting",
    ],
    "empathic communication": [
        "Empathic Communication Help",
        "Communication Training Help",
        "Train Empathic Care Teams",
        "Communication Skills Course",
        "Improve Care Conversations",
        "Staff Communication Training",
        "Care Team Conversation Help",
        "Build Empathic Team Skills",
        "Training For Staff Empathy",
        "Support Conversation Skills",
        "Empathic Care Team Skills",
        "Team Communication Training",
    ],
    "clinical support": [
        "Clinical Team Support Plans",
        "Clinical Support Planning",
        "Clinical Care Team Support",
        "Healthcare Team Consulting",
        "Clinical Workflow Support",
        "Care Delivery Support Plan",
        "Support Clinical Workflows",
        "Clinical Practice Support",
        "Plan Clinical Team Support",
        "Clinical Support For Teams",
        "Clinical Operations Support",
        "Healthcare Support Planning",
    ],
    "learning and development": [
        "Learning Development Help",
        "Learning And Development Plan",
        "Learning Programs For Teams",
        "Staff Development Planning",
        "Support Staff Development",
        "Build Practical Team Skills",
        "Training Program Planning",
        "Improve Staff Support Skills",
        "Learning Paths For Care Teams",
        "Team Development Programs",
    ],
    "human-centered": [
        "Human Centered Care Plans",
        "Human Centered Consulting",
        "Human Centered Care Support",
        "People Centered Care Help",
        "Human Care Model Consulting",
        "Build Human Centered Care",
        "Human Centered Care Review",
        "People Focused Care Plans",
        "Healthcare Care Model Help",
        "Human Centered Team Support",
        "Human Centered Health Care",
        "People Centered Care Teams",
        "Human Care Delivery Plans",
        "Human Care Consulting Help",
        "People First Care Support",
        "Human Care For Organizations",
        "Centered Care Team Support",
    ],
    "human centered": [
        "Human Centered Care Plans",
        "Human Centered Consulting",
        "Human Centered Care Support",
        "People Centered Care Help",
        "Human Care Model Consulting",
        "Build Human Centered Care",
        "Human Centered Care Review",
        "People Focused Care Plans",
        "Healthcare Care Model Help",
        "Human Centered Team Support",
        "Human Centered Health Care",
        "People Centered Care Teams",
        "Human Care Delivery Plans",
        "Human Care Consulting Help",
        "People First Care Support",
        "Human Care For Organizations",
        "Centered Care Team Support",
    ],
    "trauma-informed": [
        "Trauma Informed Training Help",
        "Care Team Training Support",
        "Trauma Informed Care Teams",
        "Trauma Care Training Plans",
        "Safer Support Team Training",
        "Trauma Informed Staff Skills",
        "Care Safety Training Help",
        "Trauma Support Skills Course",
        "Train Trauma Informed Teams",
        "Trauma Informed Care Help",
        "Build Safer Support Teams",
        "Staff Trauma Care Training",
        "Trauma Training For Teams",
        "Support Safer Care Skills",
    ],
    "trauma informed": [
        "Trauma Informed Training Help",
        "Care Team Training Support",
        "Trauma Informed Care Teams",
        "Trauma Care Training Plans",
        "Safer Support Team Training",
        "Trauma Informed Staff Skills",
        "Care Safety Training Help",
        "Trauma Support Skills Course",
        "Train Trauma Informed Teams",
        "Trauma Informed Care Help",
        "Build Safer Support Teams",
        "Staff Trauma Care Training",
        "Trauma Training For Teams",
        "Support Safer Care Skills",
    ],
}

GENERAL_HEADLINE_POOL = [
    "Practical Support Planning",
    "Training For Care Teams Now",
    "Support For Better Access",
    "Build Human Centered Care",
    "Clear Implementation Steps",
    "Review Team Support Needs",
    "Improve Care Team Readiness",
    "Plan Your Next Service Step",
    "Consulting For Care Teams",
    "Skills For Support Teams Now",
    "Focused Training Review Today",
    "Request Program Details Now",
    "Compare Support Options Today",
    "Talk With A Consulting Team",
    "Start With A Focused Review",
    "Support Team Skill Building",
    "Plan Care Team Training Now",
    "Care Team Training Support",
    "Review Training Priorities",
    "Practical Consulting Support",
    "Clear Program Launch Steps",
    "Review Service Fit First",
    "Confirm Needs Before Launch",
    "Build Better Support Paths",
]


def service_specific_candidates(service_label: str) -> list[str]:
    lower = service_label.lower()
    candidates: list[str] = []
    for marker, headlines in SERVICE_SPECIFIC_HEADLINES.items():
        if marker in lower:
            candidates.extend(headlines)
    return candidates


def service_logic_headline_candidates(service_logic: dict[str, Any] | None) -> list[str]:
    if not service_logic:
        return []
    buyer_type = str(service_logic.get("buyer_type", ""))
    mechanism = str(service_logic.get("service_mechanism", ""))
    outcome = str(service_logic.get("outcome", ""))
    buyer = str(service_logic.get("buyer", ""))
    candidates = [
        mechanism,
        outcome,
        f"{mechanism} For Teams",
        f"{mechanism} For Staff",
        f"{outcome} Planning",
        f"{buyer} Support",
    ]
    if buyer_type in {"b2b", "b2b2c"}:
        candidates.extend(
            [
                "Training For Care Teams Now",
                "Care Team Training Support",
                "Skills For Support Teams Now",
                "Build Organizational Capacity",
                "Support Team Skill Building",
            ]
        )
    elif buyer_type == "b2c" and "restaurant" in " ".join(str(token) for token in service_logic.get("concept_tokens", [])).lower():
        candidates.extend(
            [
                "Reserve A Tasting Menu",
                "Book A Fine Dining Dinner",
                "Guatemala City Fine Dining",
                "Reserve A Dining Experience",
                "Limited Seating Dinner",
                "Fine Dining Reservations",
                "Mayan Inspired Dinner Menu",
                "Popol Vuh Inspired Dining",
                "Story Driven Tasting Menu",
                "Culture Driven Dinner Menu",
                "Modern Guatemalan Dining",
                "Casa Del Aguila Restaurant",
                "Cuatro Grados Norte Dining",
                "Contemporary Dining Menu",
                "Ancestral Cooking Experience",
                "Only Sixteen Seats Nightly",
                "Chef Guided Dinner Seats",
                "Reserve A Restaurant Seat",
                "Guatemalan Food Experience",
                "Book A Cultural Dinner",
            ]
        )
    return candidates


def service_from_ad_group(ad_group: str) -> str:
    label = ad_group.replace("Services - ", "", 1)
    for suffix in (" - General", " - Near Me"):
        if label.endswith(suffix):
            label = label[: -len(suffix)]
    parts = label.split(" - ")
    if len(parts) > 1 and len(parts[-1]) <= 35:
        label = " - ".join(parts[:-1])
    return label


def find_service_logic(service_label: str, service_logic_map: dict[str, dict[str, Any]] | None) -> dict[str, Any] | None:
    if not service_logic_map:
        return None
    normalized = normalize_headline(service_label)
    for service, logic in service_logic_map.items():
        service_norm = normalize_headline(service)
        if service_norm == normalized or service_norm in normalized or normalized in service_norm:
            return logic
    return None


def token_forms(values: set[str]) -> set[str]:
    output = set(values)
    for value in values:
        if len(value) > 3 and value.endswith("s"):
            output.add(value[:-1])
        elif len(value) > 3:
            output.add(f"{value}s")
    return output


def description_has_service_logic(description: str, service_logic: dict[str, Any]) -> bool:
    concepts = service_logic_tokens(service_logic)
    if not concepts:
        return False
    description_tokens = token_forms(set(tokenize(description)))
    buyer_tokens = token_forms(set(significant_tokens(str(service_logic.get("buyer", "")))))
    mechanism_tokens = token_forms(set(significant_tokens(str(service_logic.get("service_mechanism", "")))))
    outcome_tokens = token_forms(set(significant_tokens(str(service_logic.get("outcome", "")))))
    if not mechanism_tokens:
        mechanism_tokens = token_forms({token for token in service_logic.get("concept_tokens", []) if len(str(token)) > 2})
    if not outcome_tokens:
        return bool(description_tokens & buyer_tokens) and bool(description_tokens & mechanism_tokens)
    return bool(description_tokens & buyer_tokens) and bool(description_tokens & mechanism_tokens) and bool(description_tokens & outcome_tokens)


def generate_quality_headlines(
    *,
    client_name: str,
    service_label: str,
    ad_group: str = "",
    service_logic: dict[str, Any] | None = None,
) -> list[str]:
    """Generate 15 complete, audit-passing RSA headlines.

    The generator intentionally avoids character slicing. Any candidate outside
    the active 25 to 30 character range is ignored instead of repaired.
    """
    candidates = [
        f"Review {service_label} Fit",
        f"Compare {service_label} Options",
        f"{service_label} Planning Help",
        f"{service_label} Next Steps",
        f"{service_label} Support Review",
        f"Request {service_label} Details",
        f"Plan {service_label} Needs",
        *service_specific_candidates(service_label),
        *service_logic_headline_candidates(service_logic),
        *GENERAL_HEADLINE_POOL,
    ]
    if client_name:
        client_candidate = title_text(f"{client_name} Support Team")
        if HEADLINE_MINIMUM <= len(client_candidate) <= HEADLINE_LIMIT:
            candidates.insert(2, client_candidate)

    selected: list[str] = []
    seen: set[str] = set()
    for raw in candidates:
        headline = title_text(raw)
        normalized = normalize_headline(headline)
        if normalized in seen:
            continue
        if not (HEADLINE_MINIMUM <= len(headline) <= HEADLINE_LIMIT):
            continue
        trial = [*selected, headline]
        partial = audit_rsa_headlines(
            ad_group=ad_group,
            service_label=service_label,
            client_name=client_name,
            headlines=trial,
            service_logic=service_logic,
        )
        blocking = [
            issue
            for issue in partial.issues
            if issue.rule
            not in {
                "headline_count",
            }
        ]
        if blocking:
            continue
        selected.append(headline)
        seen.add(normalized)
        if len(selected) == REQUIRED_HEADLINE_COUNT:
            break

    if len(selected) != REQUIRED_HEADLINE_COUNT:
        raise ValueError(
            f"Could not generate {REQUIRED_HEADLINE_COUNT} clean RSA headlines for {ad_group or service_label}."
        )
    audit = audit_rsa_headlines(
        ad_group=ad_group,
        service_label=service_label,
        client_name=client_name,
        headlines=selected,
        service_logic=service_logic,
    )
    if audit.status != "pass":
        issue_rules = sorted({issue.rule for issue in audit.issues})
        raise ValueError(f"Generated RSA headlines failed quality audit for {ad_group or service_label}: {issue_rules}")
    return selected


def audit_rows(
    rows: list[dict[str, str]],
    service_logic_map: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    audits = []
    for row in rows:
        if row.get("Ad type", "").strip().lower() != "responsive search ad":
            continue
        ad_group = row.get("Ad Group", "")
        service_label = service_from_ad_group(ad_group)
        service_logic = find_service_logic(service_label, service_logic_map)
        headlines = [row.get(f"Headline {index}", "") for index in range(1, 16)]
        audit = audit_rsa_headlines(
            ad_group=ad_group,
            service_label=service_label,
            client_name="",
            headlines=headlines,
            service_logic=service_logic,
        )
        issues = list(audit.issues)
        if service_logic:
            descriptions = [row.get(f"Description {index}", "") for index in range(1, 5)]
            for index, description in enumerate(descriptions, start=1):
                if description and not description_has_service_logic(description, service_logic):
                    issues.append(
                        HeadlineQualityIssue(
                            rule="description_missing_buyer_or_mechanism",
                            message="Description does not include the researched buyer, mechanism, and outcome.",
                            slots=[index],
                            headlines=[description],
                        )
                    )
        payload = audit.to_dict()
        if issues != audit.issues:
            payload["issues"] = [asdict(issue) for issue in issues]
            payload["status"] = "fail"
        audits.append(payload)
    failing = [audit for audit in audits if audit["status"] != "pass"]
    return {
        "status": "fail" if failing else "pass",
        "rsa_rows": len(audits),
        "failing_rsa_rows": len(failing),
        "audits": audits,
    }


def audit_ad_group_plans(ad_groups: list[Any], *, client_name: str = "") -> dict[str, Any]:
    audits = []
    for ad_group in ad_groups:
        name = getattr(ad_group, "name", "")
        service_label = service_from_ad_group(name)
        headlines = list(getattr(ad_group, "headlines", []))
        service_logic = getattr(ad_group, "service_logic", None)
        audit = audit_rsa_headlines(
            ad_group=name,
            service_label=service_label,
            client_name=client_name,
            headlines=headlines,
            service_logic=service_logic,
        )
        issues = list(audit.issues)
        if service_logic:
            descriptions = list(getattr(ad_group, "descriptions", []))
            for index, description in enumerate(descriptions, start=1):
                if description and not description_has_service_logic(description, service_logic):
                    issues.append(
                        HeadlineQualityIssue(
                            rule="description_missing_buyer_or_mechanism",
                            message="Description does not include the researched buyer, mechanism, and outcome.",
                            slots=[index],
                            headlines=[description],
                        )
                    )
        payload = audit.to_dict()
        if issues != audit.issues:
            payload["issues"] = [asdict(issue) for issue in issues]
            payload["status"] = "fail"
        audits.append(payload)
    failing = [audit for audit in audits if audit["status"] != "pass"]
    return {
        "status": "fail" if failing else "pass",
        "rsa_rows": len(audits),
        "failing_rsa_rows": len(failing),
        "audits": audits,
    }
