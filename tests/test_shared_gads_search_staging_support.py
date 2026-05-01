from __future__ import annotations

import pytest

from shared.gads.core.business_logic.google_ads_editor_exporter import (
    GoogleAdsEditorExporter,
    create_sample_search_campaign,
)
from shared.gads.tools.search_staging_support import (
    negative_phrase_keyword,
    phrase_keyword,
    search_ad_group,
)


def test_search_staging_support_builds_exporter_compatible_phrase_plan(tmp_path):
    campaign = create_sample_search_campaign()
    sample_ad_group = campaign["ad_groups"][0]
    campaign["ad_groups"] = [
        search_ad_group(
            "Core Services",
            ["service consultation"],
            final_url=campaign["final_url"],
            rsa=sample_ad_group["rsa"],
        ).to_exporter_dict()
    ]

    report = GoogleAdsEditorExporter().export_and_validate(
        [campaign],
        tmp_path / "Google_Ads_Editor_Staging_CURRENT.csv",
    )

    assert report["status"] == "pass"
    assert report["keyword_criterion_types"] == {"Phrase": 1}


def test_search_staging_support_builds_negative_phrase_plan():
    keyword = negative_phrase_keyword("irrelevant service")

    assert keyword.to_exporter_dict() == {
        "text": "irrelevant service",
        "criterion_type": "Negative Phrase",
        "final_url": "",
        "status": "Paused",
    }


@pytest.mark.parametrize("keyword", ['"service consultation"', "[service consultation]", "-service consultation"])
def test_search_staging_support_rejects_old_keyword_notation(keyword):
    with pytest.raises(ValueError, match="Keyword must be plain text"):
        phrase_keyword(keyword)


@pytest.mark.parametrize("keyword", ["Broad", "Exact", "BROAD", "EXACT"])
def test_search_staging_support_rejects_match_type_as_keyword_text(keyword):
    with pytest.raises(ValueError, match="cannot be a match type"):
        phrase_keyword(keyword)
