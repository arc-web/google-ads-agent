"""Guarded Google Ads API salvage facade.

The active workflow is Google Ads Editor staging, not live Google Ads API
mutation. This module keeps the older service import path available while
making live API and MCP operations explicitly inactive until a later activation
phase approves them.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:  # pragma: no cover - dependency is optional in local cleanup tests
    from google.ads.googleads.client import GoogleAdsClient
except ImportError:  # pragma: no cover
    GoogleAdsClient = None  # type: ignore[assignment]


class LiveGoogleAdsAutomationDisabled(RuntimeError):
    """Raised when salvage-only API automation is called as active behavior."""


class GoogleAdsAPIService:
    """Offline-safe facade for future Google Ads API work."""

    def __init__(
        self,
        config_path: str | Path | None = None,
        *,
        enable_live_mutations: bool = False,
    ) -> None:
        self.config_path = Path(config_path) if config_path else None
        self.enable_live_mutations = enable_live_mutations
        self.customer_id: str | None = None
        self.client: Any | None = None
        self.mcp_config = self._load_mcp_config()

        if enable_live_mutations:
            self.client = self._load_google_ads_client()

    def _load_google_ads_client(self) -> Any:
        if GoogleAdsClient is None:
            raise LiveGoogleAdsAutomationDisabled(
                "google.ads is not installed. API automation remains salvage-only."
            )
        if not self.config_path:
            raise LiveGoogleAdsAutomationDisabled(
                "A google-ads.yaml config path is required before API automation can be activated."
            )
        return GoogleAdsClient.load_from_storage(str(self.config_path))

    def _load_mcp_config(self) -> dict[str, Any]:
        config_file = Path(__file__).with_name("gads_client_config.json")
        if not config_file.exists():
            return {}
        try:
            config = json.loads(config_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            logger.warning("Could not parse gads_client_config.json: %s", exc)
            return {}
        return config.get("platforms", {}).get("google_ads", {}).get("mcp_server", {})

    async def _call_parent_mcp(self, method_name: str, **kwargs: Any) -> Any:
        """Blocked compatibility hook for parent MCP calls."""
        del method_name, kwargs
        raise LiveGoogleAdsAutomationDisabled(
            "Parent MCP Google Ads calls are salvage-only and require explicit activation."
        )

    async def validate_account_access_via_mcp(self, customer_id: str) -> dict[str, Any]:
        """Compatibility method for old MCP validation calls."""
        return await self._call_parent_mcp("google_ads_validate_account_access", customer_id=customer_id)

    async def create_campaign_budget_via_mcp(
        self,
        customer_id: str,
        budget_name: str,
        amount_micros: int,
        period: str,
    ) -> dict[str, Any]:
        """Compatibility method for old MCP budget calls."""
        return await self._call_parent_mcp(
            "google_ads_create_campaign_budget",
            customer_id=customer_id,
            budget_name=budget_name,
            amount_micros=amount_micros,
            period=period,
        )

    def validate_account_access(self, customer_id: str) -> dict[str, Any]:
        """Blocked live account check until API automation is explicitly active."""
        del customer_id
        self._raise_inactive("validate account access")

    def check_account_structure(self, customer_id: str) -> dict[str, Any]:
        """Blocked live account read until API automation is explicitly active."""
        del customer_id
        self._raise_inactive("check account structure")

    def create_campaign_budget(self, budget_data: dict[str, Any]) -> dict[str, Any]:
        """Blocked live budget mutation until API automation is explicitly active."""
        del budget_data
        self._raise_inactive("create campaign budget")

    def create_campaign(self, campaign_data: dict[str, Any], budget_id: str) -> dict[str, Any]:
        """Blocked live campaign mutation until API automation is explicitly active."""
        del campaign_data, budget_id
        self._raise_inactive("create campaign")

    def create_asset_group(self, campaign_id: str, asset_group_data: dict[str, Any]) -> dict[str, Any]:
        """Blocked live PMAX mutation until PMAX and API automation are activated."""
        del campaign_id, asset_group_data
        self._raise_inactive("create asset group")

    def create_ad_group(self, campaign_id: str, ad_group_data: dict[str, Any]) -> dict[str, Any]:
        """Blocked live ad group mutation until API automation is explicitly active."""
        del campaign_id, ad_group_data
        self._raise_inactive("create ad group")

    def create_keywords(self, ad_group_id: str, keywords: list[str]) -> dict[str, Any]:
        """Blocked live keyword mutation until API automation is explicitly active."""
        del ad_group_id, keywords
        self._raise_inactive("create keywords")

    def create_responsive_search_ad(self, ad_group_id: str, ad_data: dict[str, Any]) -> dict[str, Any]:
        """Blocked live ad mutation until API automation is explicitly active."""
        del ad_group_id, ad_data
        self._raise_inactive("create responsive search ad")

    def build_complete_campaign(self, campaign_config: dict[str, Any]) -> dict[str, Any]:
        """Blocked live campaign build until API automation is explicitly active."""
        del campaign_config
        self._raise_inactive("build complete campaign")

    def _raise_inactive(self, operation: str) -> None:
        raise LiveGoogleAdsAutomationDisabled(
            f"Cannot {operation}: live Google Ads API automation is salvage-only. "
            "Use Google Ads Editor staging output for the active workflow."
        )


__all__ = ["GoogleAdsAPIService", "LiveGoogleAdsAutomationDisabled"]
