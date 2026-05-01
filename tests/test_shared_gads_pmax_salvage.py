from __future__ import annotations

import pytest

from shared.gads.core.business_logic.google_ads_editor_exporter import (
    GoogleAdsEditorExporter,
    create_sample_pmax_campaign,
    create_sample_search_campaign,
)
from shared.gads.core.pmax_campaigns import PMAXCSVGenerator, PMAXWorkflowInactive


def test_pmax_generator_imports_but_blocks_csv_generation():
    generator = PMAXCSVGenerator()
    generator.add_pmax_campaign({"name": "Future PMAX Reference"})
    generator.add_pmax_asset_group(
        "Future PMAX Reference",
        {
            "name": "Core Assets",
            "final_url": "https://example.com",
            "headlines": ["Example Headline"],
            "descriptions": ["Example description."],
            "search_themes": ["service consultation"],
        },
    )

    assert generator.rows
    assert generator.asset_groups[0].name == "Core Assets"

    with pytest.raises(PMAXWorkflowInactive, match="salvage-only"):
        generator.generate_csv()


def test_pmax_campaigns_do_not_export_through_active_search_exporter():
    with pytest.raises(NotImplementedError, match="Only Search staging export is active"):
        GoogleAdsEditorExporter().export_campaign(create_sample_pmax_campaign())


def test_search_exporter_still_validates_after_pmax_salvage_guard(tmp_path):
    report = GoogleAdsEditorExporter().export_and_validate(
        [create_sample_search_campaign()],
        tmp_path / "Google_Ads_Editor_Staging_CURRENT.csv",
    )

    assert report["status"] == "pass"
    assert report["counts"]["keyword_rows"] == 1
    assert report["counts"].get("asset_group_rows", 0) == 0
