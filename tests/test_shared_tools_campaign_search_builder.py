from __future__ import annotations

import pytest

from shared.tools.campaign import (
    SearchAdGroupBuild,
    SearchCampaignBuild,
    SearchRSAAssets,
    build_search_campaign_staging,
    to_exporter_campaign,
)
from shared.tools.campaign.campaign_plan import CampaignPlanInactive, create_campaign_plan


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
        "Get clear next steps from a local team focused on useful service support.",
        "Review service options, availability, and fit before you decide.",
        "Schedule a consultation and get answers from an experienced team.",
        "Plan the right service path with practical guidance and transparent details.",
    ]


def _campaign() -> SearchCampaignBuild:
    rsa = SearchRSAAssets(
        headlines=_headlines(),
        descriptions=_descriptions(),
        final_url="https://example.com/services",
        path_1="services",
        path_2="consult",
    )
    return SearchCampaignBuild(
        name="Search - Services - V1",
        budget=100.0,
        locations=[{"location": "United States", "location_id": "2840"}],
        ad_groups=[
            SearchAdGroupBuild(
                name="Core Services",
                keywords=["service consultation"],
                rsa=rsa,
            )
        ],
    )


def test_search_campaign_builder_writes_staging_file_that_validates(tmp_path):
    output_path = tmp_path / "Google_Ads_Editor_Staging_CURRENT.csv"

    report = build_search_campaign_staging(_campaign(), output_path)

    assert report["status"] == "pass"
    assert report["encoding"] == "utf-16"
    assert report["keyword_criterion_types"] == {"Phrase": 1}
    assert report["counts"]["rsa_rows"] == 1
    assert output_path.exists()


def test_search_campaign_builder_exports_only_search_safe_shape():
    campaign_data = to_exporter_campaign(_campaign())

    assert campaign_data["type"] == "Search"
    assert campaign_data["broad_match_keywords"] == "Off"
    assert campaign_data["ad_groups"][0]["keywords"][0]["criterion_type"] == "Phrase"
    assert len(campaign_data["ad_groups"][0]["rsa"]["headlines"]) == 15
    assert len(campaign_data["ad_groups"][0]["rsa"]["descriptions"]) == 4


def test_search_campaign_builder_rejects_search_partners():
    campaign = _campaign()
    bad_campaign = SearchCampaignBuild(
        name=campaign.name,
        budget=campaign.budget,
        ad_groups=campaign.ad_groups,
        locations=campaign.locations,
        networks="Google search;Search Partners",
    )

    with pytest.raises(ValueError, match="Search partners are disabled"):
        to_exporter_campaign(bad_campaign)


@pytest.mark.parametrize("keyword", ["Broad", "Exact", '"service consultation"', "[service consultation]"])
def test_search_campaign_builder_rejects_inactive_keyword_shapes(keyword):
    campaign = _campaign()
    bad_group = SearchAdGroupBuild(
        name="Core Services",
        keywords=[keyword],
        rsa=campaign.ad_groups[0].rsa,
    )
    bad_campaign = SearchCampaignBuild(
        name=campaign.name,
        budget=campaign.budget,
        ad_groups=[bad_group],
        locations=campaign.locations,
    )

    with pytest.raises(ValueError):
        to_exporter_campaign(bad_campaign)


def test_old_campaign_plan_entrypoint_is_inactive():
    with pytest.raises(CampaignPlanInactive, match="inactive"):
        create_campaign_plan()
