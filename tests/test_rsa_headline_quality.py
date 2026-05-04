from __future__ import annotations

import pytest

from shared.rebuild.rsa_headline_quality import audit_rsa_headlines, generate_quality_headlines


VALID_HEADLINES = [
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
]


def issue_rules(headlines: list[str], service_label: str = "Consulting Services") -> set[str]:
    audit = audit_rsa_headlines(
        ad_group=f"Services - {service_label}",
        service_label=service_label,
        client_name="EM Consulting",
        headlines=headlines,
    )
    return {issue.rule for issue in audit.issues}


def test_clean_headlines_pass_quality_audit() -> None:
    audit = audit_rsa_headlines(
        ad_group="Services - Consulting",
        service_label="Consulting Services",
        client_name="EM Consulting",
        headlines=VALID_HEADLINES,
    )

    assert audit.status == "pass"
    assert audit.issues == []


def test_exact_duplicate_headlines_fail() -> None:
    headlines = [*VALID_HEADLINES]
    headlines[1] = headlines[0]

    assert "headline_exact_duplicate" in issue_rules(headlines)


def test_repeated_service_only_headlines_fail() -> None:
    headlines = [
        "Employee Mental Health Support",
        "Employee Mental Health Support",
        "Employee Mental Health Support",
        *VALID_HEADLINES[:12],
    ]

    rules = issue_rules(headlines, "Employee Mental Health Support")

    assert "headline_low_value_filler" in rules
    assert "headline_exact_duplicate" in rules


def test_broken_truncated_headline_fails() -> None:
    headlines = [*VALID_HEADLINES]
    headlines[0] = "Integrated Behavioral Health C"

    assert "headline_broken_truncation" in issue_rules(headlines)


def test_semantic_repeated_headlines_fail() -> None:
    headlines = [*VALID_HEADLINES]
    headlines[:4] = [
        "Lay Counselor Academy Service",
        "Lay Counselor Academy Consult",
        "Lay Counselor Academy Options",
        "Lay Counselor Academy Planning",
    ]

    assert "headline_semantic_duplicate" in issue_rules(headlines, "Lay Counselor Academy")


@pytest.mark.parametrize(
    "service_label",
    [
        "Lay Counselor Academy",
        "Employee Mental Health Support",
        "Integrated Behavioral Health Consulting",
        "Empathic Communication Training",
        "Trauma-Informed Care Training",
    ],
)
def test_generator_handles_long_service_names_without_truncation(service_label: str) -> None:
    headlines = generate_quality_headlines(
        client_name="EM Consulting",
        service_label=service_label,
        ad_group=f"Services - {service_label}",
    )
    audit = audit_rsa_headlines(
        ad_group=f"Services - {service_label}",
        service_label=service_label,
        client_name="EM Consulting",
        headlines=headlines,
    )

    assert len(headlines) == 15
    assert audit.status == "pass"
    assert all(25 <= len(headline) <= 30 for headline in headlines)
    assert all("Chef S" not in headline for headline in headlines)


@pytest.mark.parametrize(
    "service_label",
    [
        "12 Course Mayan Tasting Menu",
        "Chef's Table Guatemala City",
        "Fine Dining Reservations",
        "Contemporary Guatemalan Food",
        "Wine Pairing Dinner",
    ],
)
def test_generator_handles_high_end_restaurant_services(service_label: str) -> None:
    service_logic = {
        "status": "pass",
        "buyer_type": "b2c",
        "buyer": "Guests choosing a restaurant or tasting menu reservation",
        "end_user": "Guests planning a fine dining meal in Guatemala City",
        "service_mechanism": "Restaurant reservation for a tasting menu experience",
        "problem": "Guests need to choose and reserve a distinctive high-end restaurant experience",
        "outcome": "Reserved contemporary Guatemalan dining experience in Guatemala City",
        "concept_tokens": [
            "chef",
            "contemporary",
            "culture",
            "dining",
            "dinner",
            "fine",
            "food",
            "guest",
            "guatemala",
            "guatemalan",
            "mayan",
            "menu",
            "pairing",
            "popol",
            "reservation",
            "restaurant",
            "seat",
            "story",
            "table",
            "tasting",
            "vuh",
            "wine",
        ],
    }
    headlines = generate_quality_headlines(
        client_name="Flor de Lis Xibalba",
        service_label=service_label,
        ad_group=f"Services - {service_label}",
        service_logic=service_logic,
    )
    audit = audit_rsa_headlines(
        ad_group=f"Services - {service_label}",
        service_label=service_label,
        client_name="Flor de Lis Xibalba",
        headlines=headlines,
        service_logic=service_logic,
    )

    assert len(headlines) == 15
    assert audit.status == "pass"
    assert all(25 <= len(headline) <= 30 for headline in headlines)
