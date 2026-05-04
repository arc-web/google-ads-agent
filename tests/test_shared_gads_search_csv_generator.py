from __future__ import annotations

import csv

import pytest

from shared.gads.core.search_campaigns.search_csv_generator import SearchCSVGenerator


def _headlines() -> list[str]:
    return [
        "Get Clear Service Support",
        "Book A Service Consult Today",
        "Local Service Team Ready Now",
        "Compare Your Service Options",
        "Plan Your Next Service Step",
        "Trusted Service Guidance Now",
        "Fast Scheduling Support Today",
        "Helpful Service Answers Today",
        "Expert Service Support Team",
        "Simple Online Service Booking",
        "Focused Support For Goals",
        "Quality Care Team Support",
        "Request Service Details Today",
        "Speak With A Service Team",
        "Start With A Service Call",
    ]


def _descriptions() -> list[str]:
    return [
        "Review service support options with clear local guidance and a focused team. Call Today.",
        "Compare availability, budget, and service fit before choosing next steps. Book Today.",
        "Schedule practical service guidance with an experienced team. Schedule Today.",
        "Request service details, timing, and support options before review. Request Details.",
    ]


def test_search_csv_generator_writes_active_utf16_tsv_that_validates(tmp_path):
    generator = SearchCSVGenerator()
    generator.add_campaign("ARC - Search - Services - V1", "125.00")
    generator.add_ad_group("ARC - Search - Services - V1", "Core Services")
    generator.add_keyword(
        "ARC - Search - Services - V1",
        "Core Services",
        "service consultation",
        final_url="https://example.com/services",
    )
    generator.add_rsa(
        "ARC - Search - Services - V1",
        "Core Services",
        "https://example.com/services",
        headlines=_headlines(),
        descriptions=_descriptions(),
        path_1="services",
        path_2="consult",
    )
    generator.add_location(
        "ARC - Search - Services - V1",
        "United States",
        location_id="2840",
    )
    generator.add_sitelink(
        "ARC - Search - Services - V1",
        "Service Details",
        "https://example.com/services/details",
        ad_group="Core Services",
        description_1="Review service details",
        description_2="Confirm fit before launch",
        level="ad_group",
    )
    generator.add_callout("ARC - Search - Services - V1", "Google Search Only")
    generator.add_structured_snippet(
        "ARC - Search - Services - V1",
        "Services",
        ["Consulting", "Repair", "Support"],
    )
    for header, price in (("Plan One", "$125"), ("Plan Two", "$225"), ("Plan Three", "$325")):
        generator.add_price(
            "ARC - Search - Services - V1",
            header,
            "Website listed price",
            price,
            "https://example.com/pricing",
        )
    generator.add_promotion(
        "ARC - Search - Services - V1",
        "Spring Offer",
        "https://example.com/promo",
        percent_off="10%",
    )
    generator.add_business_name("ARC - Search - Services - V1", "Example Services")

    output_path = tmp_path / "Google_Ads_Editor_Staging_CURRENT.csv"
    report = generator.write_and_validate(output_path)

    assert report["status"] == "pass"
    assert report["encoding"] == "utf-16"
    assert report["counts"]["campaign_rows"] == 1
    assert report["counts"]["keyword_rows"] == 1
    assert report["counts"]["rsa_rows"] == 1
    assert report["counts"]["location_rows"] == 1
    assert report["counts"]["sitelink_rows"] == 1
    assert report["counts"]["callout_rows"] == 1
    assert report["counts"]["structured_snippet_rows"] == 1
    assert report["counts"]["price_rows"] == 3
    assert report["counts"]["promotion_rows"] == 1
    assert report["counts"]["business_name_rows"] == 1

    with output_path.open("r", encoding="utf-16", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    assert rows[0]["Broad match keywords"] == "Off"
    assert rows[2]["Criterion Type"] == "Phrase"
    assert rows[2]["Keyword"] == "service consultation"
    assert rows[3]["Ad type"] == "Responsive search ad"
    assert rows[3]["Headline 15"] == "Start With A Service Call"
    assert rows[3]["Description 4"].startswith("Request service details")
    assert rows[5]["Asset type"] == "Sitelink"
    assert rows[5]["Link text"] == "Service Details"
    assert rows[6]["Callout text"] == "Google Search Only"
    assert rows[7]["Structured snippet values"] == "Consulting;Repair;Support"
    assert rows[8]["Price header"] == "Plan One"
    assert rows[11]["Promotion target"] == "Spring Offer"
    assert rows[12]["Business name"] == "Example Services"


def test_search_csv_generator_rejects_search_partners():
    generator = SearchCSVGenerator()

    with pytest.raises(ValueError, match="Search partners are disabled"):
        generator.add_campaign(
            "ARC - Search - Services - V1",
            "125.00",
            networks="Google search;Search Partners",
        )


@pytest.mark.parametrize("criterion_type", ["Broad", "Exact"])
def test_search_csv_generator_rejects_inactive_match_types(criterion_type):
    generator = SearchCSVGenerator()

    with pytest.raises(ValueError, match="only supports Phrase"):
        generator.add_keyword(
            "ARC - Search - Services - V1",
            "Core Services",
            "service consultation",
            criterion_type=criterion_type,
        )


@pytest.mark.parametrize("keyword", ['"service consultation"', "[service consultation]", "-service consultation"])
def test_search_csv_generator_requires_plain_keyword_text(keyword):
    generator = SearchCSVGenerator()

    with pytest.raises(ValueError, match="Keyword must be plain text"):
        generator.add_keyword("ARC - Search - Services - V1", "Core Services", keyword)


def test_search_csv_generator_requires_complete_responsive_search_ad_assets():
    generator = SearchCSVGenerator()

    with pytest.raises(ValueError, match="exactly 15 headlines"):
        generator.add_rsa(
            "ARC - Search - Services - V1",
            "Core Services",
            "https://example.com/services",
            headlines=_headlines()[:14],
            descriptions=_descriptions(),
        )

    with pytest.raises(ValueError, match="exactly 4 descriptions"):
        generator.add_rsa(
            "ARC - Search - Services - V1",
            "Core Services",
            "https://example.com/services",
            headlines=_headlines(),
            descriptions=_descriptions()[:3],
        )


def test_old_client_shaped_campaign_generation_is_explicitly_retired():
    generator = SearchCSVGenerator()

    with pytest.raises(NotImplementedError, match="old client-specific"):
        generator.generate_campaign("Campaign", "county", "client")
