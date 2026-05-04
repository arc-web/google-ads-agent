from __future__ import annotations

import pytest

from shared.rebuild.csv_naming import generated_csv_name, validate_generated_csv_name


def test_generated_csv_name_includes_client_and_timestamp() -> None:
    assert (
        generated_csv_name("Fixture Client", "Google Ads Editor Staging", "2026-05-04T15:30:45")
        == "fixture_client_google_ads_editor_staging_20260504_153045.csv"
    )


def test_generated_csv_name_rejects_missing_client_timestamp_shape() -> None:
    with pytest.raises(ValueError, match="must include client slug and date/time"):
        validate_generated_csv_name("Google_Ads_Editor_Staging_CURRENT.csv", "Fixture Client")
