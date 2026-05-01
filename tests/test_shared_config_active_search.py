from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from shared.config import ConfigLoader


CONFIG_DIR = Path("shared/config")


def test_config_loader_defaults_to_active_search_only():
    loader = ConfigLoader()

    assert loader.get_available_campaign_types() == ["search"]

    config = loader.load_campaign_config()

    assert config["active_workflow"]["campaign_type"] == "Search"
    assert config["keyword_criterion_type"] == "Phrase"
    assert config["broad_match_keywords"] == "Off"
    assert config["rsa_headlines_required"] == 15
    assert config["rsa_descriptions_required"] == 4
    assert config["output_encoding"] == "utf-16"
    assert "Performance Max" not in config.get("networks", [])


@pytest.mark.parametrize("campaign_type", ["performance_max", "pmax", "display", "shopping", "video"])
def test_config_loader_rejects_inactive_campaign_types_by_default(campaign_type):
    with pytest.raises(ValueError, match="inactive"):
        ConfigLoader().load_campaign_config(campaign_type)


def test_config_loader_filters_recommendations_to_active_search():
    recommendation = ConfigLoader().get_campaign_type_recommendations("lead_generation")

    assert recommendation["recommended_types"] == ["Search"]


def test_shared_business_config_is_generic_not_client_specific():
    business_config = yaml.safe_load((CONFIG_DIR / "business_config.yaml").read_text(encoding="utf-8"))
    business = business_config["business"]

    assert business["name"] == "Generic Client"
    assert business["services"] == []
    assert business["business_type_classification"]["verification_required"] is True


def test_shared_campaign_defaults_mark_non_search_as_inactive_reference():
    defaults = yaml.safe_load((CONFIG_DIR / "campaign_defaults.yaml").read_text(encoding="utf-8"))

    assert defaults["active_workflow"]["pmax_enabled"] is False
    assert defaults["active_workflow"]["api_upload_enabled"] is False
    assert defaults["inactive_campaign_types"]["performance_max"]["status"] == "salvage_only"
    assert defaults["campaign_type_selection"]["rules"]["lead_generation"]["recommended_types"] == ["Search"]


def test_ad_limits_match_active_rsa_contract():
    ad_limits = yaml.safe_load((CONFIG_DIR / "ad_limits.yaml").read_text(encoding="utf-8"))

    assert ad_limits["limits"]["headlines_max"] == 15
    assert ad_limits["limits"]["descriptions_max"] == 4
    assert ad_limits["business_overrides"] == {}
