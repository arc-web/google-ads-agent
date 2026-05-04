from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from shared.rebuild.staging_validator import (
    REQUIRED_HEADERS,
    REQUIRED_RSA_DESCRIPTIONS,
    REQUIRED_RSA_HEADLINES,
    validate_file,
)
from shared.rebuild.match_type_policy import keyword_origin_key

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


def staging_headers() -> list[str]:
    headers = list(REQUIRED_HEADERS)
    for header in REQUIRED_RSA_HEADLINES + REQUIRED_RSA_DESCRIPTIONS:
        if header not in headers:
            headers.append(header)
    for header in (
        "Path 1",
        "Path 2",
        "Radius",
        "Bid Modifier",
        "Asset type",
        "Asset level",
        "Link text",
        "Description line 1",
        "Description line 2",
        "Callout text",
        "Structured snippet header",
        "Structured snippet values",
        "Phone number",
        "Country code",
        "Price type",
        "Price qualifier",
        "Currency",
        "Price header",
        "Price description",
        "Price amount",
        "Price unit",
        "Promotion target",
        "Percent off",
        "Money amount off",
        "Promotion code",
        "Business name",
        "Bid Strategy Type",
        "Conversions last 30 days",
        "Audience targeting setting",
        "Conversion tracking status",
        "Time zone",
    ):
        if header not in headers:
            headers.append(header)
    return headers


def base_row(**overrides: str) -> dict[str, str]:
    row = {header: "" for header in staging_headers()}
    row.update(overrides)
    return row


def campaign_row(**overrides: str) -> dict[str, str]:
    row = base_row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Campaign Type": "Search",
            "Networks": "Google search",
            "Budget": "25.00",
            "Budget type": "Daily",
            "EU political ads": "Doesn't have EU political ads",
            "Broad match keywords": "Off",
            "Status": "Enabled",
        },
    )
    row.update(overrides)
    return row


def ad_group_row(**overrides: str) -> dict[str, str]:
    row = base_row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Ad Group": "Testing - General",
            "Status": "Enabled",
        },
    )
    row.update(overrides)
    return row


def keyword_row(**overrides: str) -> dict[str, str]:
    row = base_row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Ad Group": "Testing - General",
            "Keyword": "child psychological evaluation",
            "Criterion Type": "Phrase",
            "Status": "Enabled",
        },
    )
    row.update(overrides)
    return row


def negative_phrase_row(**overrides: str) -> dict[str, str]:
    row = base_row(
        Campaign="ARC - Search - Testing - V1",
        Keyword="free test",
        **{
            "Criterion Type": "Negative Phrase",
            "Status": "Enabled",
        },
    )
    row.update(overrides)
    return row


def rsa_row(**overrides: str) -> dict[str, str]:
    row = base_row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Ad Group": "Testing - General",
            "Ad type": "Responsive search ad",
            "Final URL": "https://example.com/testing",
            "Path 1": "Testing",
            "Path 2": "Care",
            "Status": "Enabled",
        },
    )
    for index in range(1, 16):
        row[f"Headline {index}"] = VALID_HEADLINES[index - 1]
    for index in range(1, 5):
        row[f"Description {index}"] = (
            f"Review testing support options with a focused local care team {index}. Schedule Today."
        )
    row.update(overrides)
    return row


def location_row(**overrides: str) -> dict[str, str]:
    row = base_row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Location": "Ashburn, Virginia, United States",
            "Location ID": "1027067",
            "Status": "Enabled",
        },
    )
    row.update(overrides)
    return row


def sitelink_row(**overrides: str) -> dict[str, str]:
    row = base_row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Ad Group": "Testing - General",
            "Asset type": "Sitelink",
            "Asset level": "ad_group",
            "Link text": "Testing Services",
            "Final URL": "https://example.com/testing",
            "Description line 1": "Review testing options",
            "Description line 2": "Confirm fit before launch",
            "Status": "Paused",
        },
    )
    row.update(overrides)
    return row


def callout_row(**overrides: str) -> dict[str, str]:
    row = base_row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Asset type": "Callout",
            "Asset level": "campaign",
            "Callout text": "Google Search Only",
            "Status": "Paused",
        },
    )
    row.update(overrides)
    return row


def structured_snippet_row(**overrides: str) -> dict[str, str]:
    row = base_row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Asset type": "Structured snippet",
            "Asset level": "campaign",
            "Structured snippet header": "Services",
            "Structured snippet values": "Testing;Consulting;Support",
            "Status": "Paused",
        },
    )
    row.update(overrides)
    return row


def price_row(**overrides: str) -> dict[str, str]:
    row = base_row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Asset type": "Price",
            "Asset level": "campaign",
            "Price type": "Services",
            "Price qualifier": "From",
            "Currency": "USD",
            "Price header": "Service Plan",
            "Price description": "Website listed price",
            "Price amount": "$125",
            "Price unit": "None",
            "Final URL": "https://example.com/pricing",
            "Status": "Paused",
        },
    )
    row.update(overrides)
    return row


def promotion_row(**overrides: str) -> dict[str, str]:
    row = base_row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Asset type": "Promotion",
            "Asset level": "campaign",
            "Promotion target": "Spring Offer",
            "Percent off": "10%",
            "Final URL": "https://example.com/promo",
            "Status": "Paused",
        },
    )
    row.update(overrides)
    return row


def business_name_row(**overrides: str) -> dict[str, str]:
    row = base_row(
        Campaign="ARC - Search - Testing - V1",
        **{
            "Asset type": "Business name",
            "Asset level": "campaign",
            "Business name": "Testing Clinic",
            "Status": "Paused",
        },
    )
    row.update(overrides)
    return row


def write_tsv(path: Path, rows: list[dict[str, str]], encoding: str = "utf-16") -> None:
    with path.open("w", encoding=encoding, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=staging_headers(), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def issue_rules(report: dict) -> set[str]:
    return {issue["rule"] for issue in report["issues"]}


def test_valid_current_phrase_workflow_accepts_utf16_and_campaign_level_negatives(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(
        csv_path,
        [
            campaign_row(),
            ad_group_row(),
            keyword_row(),
            negative_phrase_row(),
            rsa_row(),
            location_row(),
        ],
        encoding="utf-16",
    )

    report = validate_file(csv_path)

    assert report["status"] == "pass"
    assert report["encoding"] == "utf-16"
    assert report["counts"]["keyword_rows"] == 1
    assert report["counts"]["negative_keyword_rows"] == 1
    assert report["keyword_criterion_types"] == {"Phrase": 1, "Negative Phrase": 1}
    assert report["issues"] == []


@pytest.mark.parametrize(
    ("criterion_type", "rule"),
    [
        ("Broad", "broad_match_blocked"),
        ("Exact", "new_exact_requires_approval"),
    ],
)
def test_broad_and_new_exact_keyword_types_fail(tmp_path: Path, criterion_type: str, rule: str) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(), keyword_row(**{"Criterion Type": criterion_type})])

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert rule in issue_rules(report)


def test_revision_mode_preserves_source_proven_existing_exact_as_warning(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    exact = keyword_row(**{"Criterion Type": "Exact"})
    write_tsv(csv_path, [campaign_row(), exact, rsa_row(), location_row()])
    origin_map = tmp_path / "keyword_origin_map.json"
    origin_map.write_text(
        json.dumps(
            {
                "keywords": {
                    keyword_origin_key(exact): {
                        "origin": "source_account_export",
                        "preserve": True,
                        "relevance_status": "preserve",
                    }
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = validate_file(csv_path, match_type_mode="revision_existing_account", keyword_origin_map_path=origin_map)

    assert report["status"] == "pass"
    assert "preserved_existing_exact" in issue_rules(report)


def test_revision_mode_preserves_source_negative_exact_for_review(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    negative_exact = negative_phrase_row(**{"Criterion Type": "Negative Exact"})
    write_tsv(csv_path, [campaign_row(), keyword_row(), negative_exact, rsa_row(), location_row()])
    origin_map = tmp_path / "keyword_origin_map.json"
    origin_map.write_text(
        json.dumps({"keywords": {keyword_origin_key(negative_exact): {"origin": "source_account_export"}}}) + "\n",
        encoding="utf-8",
    )

    report = validate_file(csv_path, match_type_mode="revision_existing_account", keyword_origin_map_path=origin_map)

    assert report["status"] == "pass"
    assert "preserved_existing_negative_exact" in issue_rules(report)


def test_new_negative_exact_fails(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(), keyword_row(), negative_phrase_row(**{"Criterion Type": "Negative Exact"})])

    report = validate_file(csv_path, match_type_mode="revision_existing_account")

    assert report["status"] == "fail"
    assert "new_negative_exact_blocked" in issue_rules(report)


def test_quoted_keyword_text_fails_even_when_criterion_type_is_phrase(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(), keyword_row(Keyword='"child psychological evaluation"')])

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "plain_keyword_text" in issue_rules(report)


def test_broad_match_campaign_setting_must_be_off(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(**{"Broad match keywords": "On"}), keyword_row()])

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "broad_match_off" in issue_rules(report)


def test_search_partners_network_setting_fails(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(Networks="Google search;Search Partners"), keyword_row()])

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "search_partners_disabled" in issue_rules(report)


def test_search_display_expansion_fails(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(Networks="Google search;Display Network"), keyword_row()])

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "search_display_opt_in_blocked" in issue_rules(report)


def test_department_operational_fields_are_checked_when_present(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(
        csv_path,
        [
            campaign_row(
                **{
                    "Bid Strategy Type": "Target CPA",
                    "Conversions last 30 days": "4",
                    "Audience targeting setting": "Targeting",
                    "Conversion tracking status": "Unverified",
                    "Time zone": "Confirm before launch",
                }
            ),
            keyword_row(),
            rsa_row(),
            location_row(),
        ],
    )

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    rules = issue_rules(report)
    assert "smart_bidding_data_threshold_review" in rules
    assert "audience_targeting_mode_review" in rules
    assert "conversion_tracking_not_ready" in rules
    assert "time_zone_review" in rules


def test_short_low_value_rsa_headline_fails(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(), keyword_row(), rsa_row(**{"Headline 1": "Ashburn Care"}), location_row()])

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "headline_minimum_value" in issue_rules(report)


def test_duplicate_rsa_headline_fails(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(
        csv_path,
        [
            campaign_row(),
            keyword_row(),
            rsa_row(**{"Headline 2": VALID_HEADLINES[0]}),
            location_row(),
        ],
    )

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "headline_exact_duplicate" in issue_rules(report)


def test_broken_truncated_rsa_headline_fails(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(
        csv_path,
        [
            campaign_row(),
            keyword_row(),
            rsa_row(**{"Headline 1": "Integrated Behavioral Health C"}),
            location_row(),
        ],
    )

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "headline_broken_truncation" in issue_rules(report)


def test_semantic_repeated_rsa_headlines_fail(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    repeated = {
        f"Headline {index}": value
        for index, value in enumerate(
            [
                "Lay Counselor Academy Service",
                "Lay Counselor Academy Consult",
                "Lay Counselor Academy Options",
                "Lay Counselor Academy Planning",
            ],
            start=1,
        )
    }
    write_tsv(csv_path, [campaign_row(), keyword_row(), rsa_row(**repeated), location_row()])

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "headline_semantic_duplicate" in issue_rules(report)


def test_short_rsa_description_fails(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(), keyword_row(), rsa_row(**{"Description 1": "Testing support is available. Call Today."}), location_row()])

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "description_under_value_minimum" in issue_rules(report)


def test_rsa_description_without_cta_fails(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(
        csv_path,
        [
            campaign_row(),
            keyword_row(),
            rsa_row(**{"Description 1": "Review testing support options with practical local guidance and a focused team."}),
            location_row(),
        ],
    )

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "description_missing_cta" in issue_rules(report)


@pytest.mark.parametrize(
    "cta",
    [
        "Book Your Reservation",
        "Reserve Your Table",
        "Check Availability",
        "Book A Tasting Menu",
        "Book A Consultation",
        "Confirm Fit",
        "Call Us Today",
        "Request A Quote",
        "Schedule Service",
        "Compare Options",
        "Review Program Fit",
        "Plan Next Steps",
        "Schedule A Review",
    ],
)
def test_contextual_rsa_description_ctas_pass(tmp_path: Path, cta: str) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(
        csv_path,
        [
            campaign_row(),
            keyword_row(),
            rsa_row(
                **{
                    "Description 1": f"Review local support options with clear process and care team. {cta}."
                }
            ),
            location_row(),
        ],
    )

    report = validate_file(csv_path)

    assert report["status"] == "pass"
    assert "description_missing_cta" not in issue_rules(report)


def test_rsa_description_without_value_prop_fails(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(
        csv_path,
        [
            campaign_row(),
            keyword_row(),
            rsa_row(**{"Description 1": "This message has enough characters to pass length but says almost nothing. Call Today."}),
            location_row(),
        ],
    )

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "description_missing_value_prop" in issue_rules(report)


def test_rsa_description_with_internal_workflow_language_fails(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(
        csv_path,
        [
            campaign_row(),
            keyword_row(),
            rsa_row(
                **{
                    "Description 1": (
                        "Schedule today to compare support options before campaign approval and account import"
                    )
                }
            ),
            location_row(),
        ],
    )

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "description_generic_workflow_language" in issue_rules(report)


def test_rsa_description_with_incomplete_phrase_fails(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(
        csv_path,
        [
            campaign_row(),
            keyword_row(),
            rsa_row(**{"Description 1": "Review staff training options for care access and team support with. Request Details."}),
            location_row(),
        ],
    )

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "description_incomplete_phrase" in issue_rules(report)


def test_missing_location_id_is_warning_not_failure(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(), keyword_row(), rsa_row(), location_row(**{"Location ID": ""})])

    report = validate_file(csv_path)

    assert report["status"] == "pass"
    assert report["issue_counts"] == {"warning": 1}
    assert "location_id_preferred" in issue_rules(report)


def test_valid_search_asset_rows_are_counted_and_validate(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(
        csv_path,
        [
            campaign_row(),
            ad_group_row(),
            keyword_row(),
            rsa_row(),
            location_row(),
            sitelink_row(),
            callout_row(),
            structured_snippet_row(),
            price_row(**{"Price header": "Plan One", "Price amount": "$125"}),
            price_row(**{"Price header": "Plan Two", "Price amount": "$225"}),
            price_row(**{"Price header": "Plan Three", "Price amount": "$325"}),
            promotion_row(),
            business_name_row(),
        ],
    )

    report = validate_file(csv_path)

    assert report["status"] == "pass"
    assert report["counts"]["sitelink_rows"] == 1
    assert report["counts"]["callout_rows"] == 1
    assert report["counts"]["structured_snippet_rows"] == 1
    assert report["counts"]["price_rows"] == 3
    assert report["counts"]["promotion_rows"] == 1
    assert report["counts"]["business_name_rows"] == 1


def test_sitelink_text_over_limit_fails(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(), keyword_row(), rsa_row(), location_row(), sitelink_row(**{"Link text": "This Sitelink Text Is Too Long"})])

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "sitelink_link_text_length" in issue_rules(report)


def test_sitelink_requires_description_pair(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(), keyword_row(), rsa_row(), location_row(), sitelink_row(**{"Description line 2": ""})])

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "sitelink_description_pair_required" in issue_rules(report)


def test_duplicate_sitelink_text_in_same_branch_fails(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(
        csv_path,
        [
            campaign_row(),
            keyword_row(),
            rsa_row(),
            location_row(),
            sitelink_row(),
            sitelink_row(**{"Final URL": "https://example.com/other"}),
        ],
    )

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "sitelink_duplicate_link_text" in issue_rules(report)


def test_callout_text_over_limit_fails(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(), keyword_row(), rsa_row(), location_row(), callout_row(**{"Callout text": "This callout is definitely too long"})])

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "callout_text_length" in issue_rules(report)


@pytest.mark.parametrize(
    ("values", "rule"),
    [
        ("Testing;Consulting", "structured_snippet_min_values"),
        ("One;Two;Three;Four;Five;Six;Seven;Eight;Nine;Ten;Eleven", "structured_snippet_max_values"),
        ("Testing;Consulting;This Structured Snippet Value Is Too Long", "structured_snippet_value_length"),
    ],
)
def test_structured_snippet_value_rules_fail(tmp_path: Path, values: str, rule: str) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(
        csv_path,
        [campaign_row(), keyword_row(), rsa_row(), location_row(), structured_snippet_row(**{"Structured snippet values": values})],
    )

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert rule in issue_rules(report)


def test_structured_snippet_invalid_header_fails(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(
        csv_path,
        [campaign_row(), keyword_row(), rsa_row(), location_row(), structured_snippet_row(**{"Structured snippet header": "Bad Header"})],
    )

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "structured_snippet_header" in issue_rules(report)


def test_price_assets_require_three_items_per_branch(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(), keyword_row(), rsa_row(), location_row(), price_row()])

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "price_min_items" in issue_rules(report)


def test_price_text_and_amount_rules_fail(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(
        csv_path,
        [
            campaign_row(),
            keyword_row(),
            rsa_row(),
            location_row(),
            price_row(**{"Price header": "This Price Header Is Too Long", "Price amount": "$125"}),
            price_row(**{"Price header": "Plan Two", "Price amount": "call"}),
            price_row(**{"Price header": "Plan Three", "Price amount": "$325"}),
        ],
    )

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "price_header_length" in issue_rules(report)
    assert "price_amount_format" in issue_rules(report)


def test_promotion_requires_offer_evidence(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(), keyword_row(), rsa_row(), location_row(), promotion_row(**{"Percent off": ""})])

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "promotion_offer_required" in issue_rules(report)


def test_business_name_length_fails(tmp_path: Path) -> None:
    csv_path = tmp_path / "staging.csv"
    write_tsv(csv_path, [campaign_row(), keyword_row(), rsa_row(), location_row(), business_name_row(**{"Business name": "This Business Name Is Too Long"})])

    report = validate_file(csv_path)

    assert report["status"] == "fail"
    assert "business_name_length" in issue_rules(report)
