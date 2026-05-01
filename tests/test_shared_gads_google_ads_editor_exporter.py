from __future__ import annotations

import csv

import pytest

from shared.gads.core.business_logic.google_ads_editor_exporter import (
    GoogleAdsEditorExporter,
    create_sample_pmax_campaign,
    create_sample_search_campaign,
    export_campaigns_to_csv,
)


def test_google_ads_editor_exporter_exports_search_staging_that_validates(tmp_path):
    exporter = GoogleAdsEditorExporter()
    output_path = tmp_path / "Google_Ads_Editor_Staging_CURRENT.csv"

    report = exporter.export_and_validate([create_sample_search_campaign()], output_path)

    assert report["status"] == "pass"
    assert report["encoding"] == "utf-16"
    assert report["counts"]["campaign_rows"] == 1
    assert report["counts"]["keyword_rows"] == 1
    assert report["counts"]["rsa_rows"] == 1
    assert report["counts"]["location_rows"] == 1

    with output_path.open("r", encoding="utf-16", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))

    assert rows[0]["Campaign Type"] == "Search"
    assert rows[0]["Broad match keywords"] == "Off"
    keyword_row = next(row for row in rows if row["Keyword"])
    rsa_row = next(row for row in rows if row["Ad type"] == "Responsive search ad")
    assert keyword_row["Criterion Type"] == "Phrase"
    assert rsa_row["Headline 15"] == "Start With A Call"


def test_google_ads_editor_exporter_convenience_function_writes_utf16(tmp_path):
    output_path = tmp_path / "search_staging.csv"

    csv_content = export_campaigns_to_csv([create_sample_search_campaign()], output_path)

    assert csv_content.startswith("Campaign\t")
    assert output_path.read_text(encoding="utf-16").startswith("Campaign\t")


def test_google_ads_editor_exporter_uses_active_validator_for_content():
    exporter = GoogleAdsEditorExporter()
    csv_content = exporter.export_campaign(create_sample_search_campaign())

    assert exporter.validate_csv_data(csv_content) == []


@pytest.mark.parametrize("criterion_type", ["Broad", "Exact"])
def test_google_ads_editor_exporter_rejects_inactive_match_types(criterion_type):
    campaign = create_sample_search_campaign()
    campaign["ad_groups"][0]["keywords"][0] = {
        "text": "service consultation",
        "criterion_type": criterion_type,
    }

    with pytest.raises(ValueError, match="only supports Phrase"):
        GoogleAdsEditorExporter().export_campaign(campaign)


def test_google_ads_editor_exporter_keeps_pmax_salvage_inactive():
    with pytest.raises(NotImplementedError, match="Only Search staging export is active"):
        GoogleAdsEditorExporter().export_campaign(create_sample_pmax_campaign())
