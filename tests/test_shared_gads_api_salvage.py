from __future__ import annotations

import asyncio
import json

import pytest

from shared.gads.core.google_ads_api_service import (
    GoogleAdsAPIService,
    LiveGoogleAdsAutomationDisabled,
)


def test_google_ads_api_service_imports_without_live_dependency():
    service = GoogleAdsAPIService()

    assert service.client is None
    assert service.enable_live_mutations is False


@pytest.mark.parametrize(
    ("method_name", "args"),
    [
        ("validate_account_access", ("1234567890",)),
        ("check_account_structure", ("1234567890",)),
        ("create_campaign_budget", ({"name": "Budget"},)),
        ("create_campaign", ({"name": "Campaign"}, "123")),
        ("create_asset_group", ("123", {"name": "Assets"})),
        ("create_ad_group", ("123", {"name": "Ad Group"})),
        ("create_keywords", ("123", ["service consultation"])),
        ("create_responsive_search_ad", ("123", {"headlines": []})),
        ("build_complete_campaign", ({"name": "Campaign"},)),
    ],
)
def test_google_ads_api_service_blocks_live_operations(method_name, args):
    service = GoogleAdsAPIService()

    with pytest.raises(LiveGoogleAdsAutomationDisabled, match="salvage-only"):
        getattr(service, method_name)(*args)


def test_google_ads_api_service_blocks_parent_mcp_calls():
    service = GoogleAdsAPIService()

    with pytest.raises(LiveGoogleAdsAutomationDisabled, match="Parent MCP"):
        asyncio.run(service.validate_account_access_via_mcp("1234567890"))


def test_gads_client_config_has_no_hard_coded_local_parent_path():
    with open("shared/gads/core/gads_client_config.json", encoding="utf-8") as handle:
        config = json.load(handle)

    mcp_server = config["platforms"]["google_ads"]["mcp_server"]

    assert mcp_server["use_parent_directory"] is False
    assert mcp_server["parent_config_path"] == "${ENV:GOOGLE_ADS_MCP_CONFIG_PATH}"
    local_path_token = "/" + "Users/"
    assert local_path_token not in json.dumps(config)
