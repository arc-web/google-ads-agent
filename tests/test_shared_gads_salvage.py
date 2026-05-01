from __future__ import annotations

import importlib


def test_shared_gads_core_import_is_lightweight_without_google_ads_dependency():
    module = importlib.import_module("shared.gads.core")

    assert "GoogleAdsAPIService" in module.__all__


def test_search_campaigns_salvage_package_imports_existing_generator():
    module = importlib.import_module("shared.gads.core.search_campaigns")

    assert module.SearchCSVGenerator.__name__ == "SearchCSVGenerator"


def test_pmax_campaigns_salvage_package_imports_existing_generator():
    module = importlib.import_module("shared.gads.core.pmax_campaigns")

    assert module.PMAXCSVGenerator.__name__ == "PMAXCSVGenerator"
