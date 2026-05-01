"""Guarded PMAX campaign salvage facade.

PMAX is preserved for future review, but it is not part of the active
Search-first Google Ads Editor staging workflow. This module keeps the old
``PMAXCSVGenerator`` import path stable while blocking PMAX output until a
separate PMAX activation phase is approved and tested.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class PMAXWorkflowInactive(RuntimeError):
    """Raised when PMAX generation is called before PMAX activation."""


@dataclass(frozen=True)
class PMAXAssetGroupReference:
    """Reference container for future PMAX asset group review."""

    name: str
    final_url: str = ""
    headlines: list[str] = field(default_factory=list)
    descriptions: list[str] = field(default_factory=list)
    search_themes: list[str] = field(default_factory=list)


class PMAXCSVGenerator:
    """Compatibility facade that keeps PMAX generation inactive."""

    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self.asset_groups: list[PMAXAssetGroupReference] = []

    def add_pmax_campaign(self, campaign_data: dict[str, Any]) -> None:
        """Record reference data, but do not activate PMAX generation."""
        self.rows.append({"type": "campaign_reference", **campaign_data})

    def add_pmax_asset_group(self, campaign_name: str, asset_group_data: dict[str, Any]) -> None:
        """Record reference asset group data for future PMAX review."""
        self.asset_groups.append(
            PMAXAssetGroupReference(
                name=str(asset_group_data.get("name", "")),
                final_url=str(asset_group_data.get("final_url", "")),
                headlines=[str(value) for value in asset_group_data.get("headlines", [])],
                descriptions=[str(value) for value in asset_group_data.get("descriptions", [])],
                search_themes=[str(value) for value in asset_group_data.get("search_themes", [])],
            )
        )
        self.rows.append({"type": "asset_group_reference", "campaign": campaign_name, **asset_group_data})

    def add_pmax_asset(self, campaign_name: str, asset_group_name: str, asset_data: dict[str, Any]) -> None:
        """Record reference asset data for future PMAX review."""
        self.rows.append(
            {
                "type": "asset_reference",
                "campaign": campaign_name,
                "asset_group": asset_group_name,
                **asset_data,
            }
        )

    def add_pmax_search_theme(self, campaign_name: str, asset_group_name: str, theme_data: dict[str, Any]) -> None:
        """Record reference search theme data for future PMAX review."""
        self.rows.append(
            {
                "type": "search_theme_reference",
                "campaign": campaign_name,
                "asset_group": asset_group_name,
                **theme_data,
            }
        )

    def generate_csv(self) -> str:
        """Block PMAX CSV generation until the workflow is active."""
        self._raise_inactive()

    def save_csv(self, filename: str | Path) -> None:
        """Block PMAX file output until the workflow is active."""
        del filename
        self._raise_inactive()

    def _raise_inactive(self) -> None:
        raise PMAXWorkflowInactive(
            "PMAX generation is salvage-only. The active workflow is Search staging through "
            "shared/rebuild/staging_validator.py."
        )


__all__ = ["PMAXCSVGenerator", "PMAXAssetGroupReference", "PMAXWorkflowInactive"]
