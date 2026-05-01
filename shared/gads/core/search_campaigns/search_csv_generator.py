"""Generic Search staging generator for Google Ads Editor TSV output.

This module replaces an older client-shaped generator with a small shared helper
that writes the active staging format and validates through the rebuild
staging validator. It does not activate API upload, PMAX, broad match, or exact
match behavior.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

from shared.rebuild.staging_validator import (
    REQUIRED_HEADERS,
    REQUIRED_RSA_DESCRIPTIONS,
    REQUIRED_RSA_HEADLINES,
    validate_file,
)


OPTIONAL_HEADERS = [
    "Campaign status",
    "Ad Group status",
    "Keyword status",
    "Ad status",
    "Path 1",
    "Path 2",
    "Location",
    "Radius",
    "Bid Modifier",
]

SEARCH_STAGING_COLUMNS = [
    *REQUIRED_HEADERS,
    *REQUIRED_RSA_HEADLINES,
    *REQUIRED_RSA_DESCRIPTIONS,
    *[header for header in OPTIONAL_HEADERS if header not in REQUIRED_HEADERS],
]

ALLOWED_CRITERION_TYPES = {"Phrase", "Negative Phrase"}
SEARCH_NETWORK_VALUE = "Google search"


class SearchCSVGenerator:
    """Build Google Ads Editor Search staging rows in the active repo format."""

    columns = SEARCH_STAGING_COLUMNS

    def __init__(self) -> None:
        self.rows: list[dict[str, str]] = []

    def _blank_row(self) -> dict[str, str]:
        return {column: "" for column in self.columns}

    def add_campaign(
        self,
        campaign: str,
        budget: float | str,
        *,
        status: str = "Paused",
        networks: str = SEARCH_NETWORK_VALUE,
        budget_type: str = "Daily",
        eu_political_ads: str = "No",
        broad_match_keywords: str = "Off",
    ) -> dict[str, str]:
        """Add a Search campaign row."""
        budget_value = self._format_budget(budget)
        row = self._blank_row()
        row.update(
            {
                "Campaign": campaign,
                "Campaign Type": "Search",
                "Networks": self._search_network(networks),
                "Budget": budget_value,
                "Budget type": budget_type,
                "EU political ads": eu_political_ads,
                "Broad match keywords": broad_match_keywords,
                "Campaign status": status,
                "Status": status,
            }
        )
        self.rows.append(row)
        return row

    def add_search_campaign(self, campaign_data: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, str]:
        """Compatibility alias for older callers using dict-shaped campaign data."""
        data = {**(campaign_data or {}), **kwargs}
        campaign = data.get("name") or data.get("campaign") or data.get("Campaign")
        if not campaign:
            raise ValueError("Campaign name is required.")
        return self.add_campaign(
            str(campaign),
            data.get("budget", "1.00"),
            status=str(data.get("status", "Paused")),
            networks=str(data.get("networks", SEARCH_NETWORK_VALUE)),
            budget_type=str(data.get("budget_type", "Daily")),
            eu_political_ads=str(data.get("eu_political_ads", "No")),
            broad_match_keywords=str(data.get("broad_match_keywords", "Off")),
        )

    def add_ad_group(
        self,
        campaign: str,
        ad_group: str,
        *,
        status: str = "Paused",
    ) -> dict[str, str]:
        """Add an ad group row using the active `Ad Group` casing."""
        row = self._blank_row()
        row.update(
            {
                "Campaign": campaign,
                "Ad Group": ad_group,
                "Ad Group status": status,
                "Status": status,
            }
        )
        self.rows.append(row)
        return row

    def add_keyword(
        self,
        campaign: str,
        ad_group: str,
        keyword: str,
        *,
        final_url: str = "",
        criterion_type: str = "Phrase",
        status: str = "Paused",
    ) -> dict[str, str]:
        """Add a phrase keyword row.

        Match notation never belongs in the Keyword value. The active staging
        contract stores match behavior in `Criterion Type`.
        """
        self._validate_criterion_type(criterion_type)
        if criterion_type == "Negative Phrase":
            return self.add_negative_phrase(campaign, keyword, ad_group=ad_group, status=status)

        row = self._blank_row()
        row.update(
            {
                "Campaign": campaign,
                "Ad Group": ad_group,
                "Keyword": self._plain_keyword(keyword),
                "Criterion Type": "Phrase",
                "Final URL": final_url,
                "Keyword status": status,
                "Status": status,
            }
        )
        self.rows.append(row)
        return row

    def add_negative_phrase(
        self,
        campaign: str,
        keyword: str,
        *,
        ad_group: str = "",
        status: str = "Paused",
    ) -> dict[str, str]:
        """Add a negative phrase row without using leading-minus notation."""
        row = self._blank_row()
        row.update(
            {
                "Campaign": campaign,
                "Ad Group": ad_group,
                "Keyword": self._plain_keyword(keyword),
                "Criterion Type": "Negative Phrase",
                "Keyword status": status,
                "Status": status,
            }
        )
        self.rows.append(row)
        return row

    def add_rsa(
        self,
        campaign: str,
        ad_group: str,
        final_url: str,
        *,
        headlines: list[str],
        descriptions: list[str],
        path_1: str = "",
        path_2: str = "",
        status: str = "Paused",
    ) -> dict[str, str]:
        """Add a responsive search ad row with all required RSA assets."""
        self._validate_count("headlines", headlines, len(REQUIRED_RSA_HEADLINES))
        self._validate_count("descriptions", descriptions, len(REQUIRED_RSA_DESCRIPTIONS))

        row = self._blank_row()
        row.update(
            {
                "Campaign": campaign,
                "Ad Group": ad_group,
                "Final URL": final_url,
                "Ad type": "Responsive search ad",
                "Ad status": status,
                "Status": status,
                "Path 1": path_1,
                "Path 2": path_2,
            }
        )
        for header, value in zip(REQUIRED_RSA_HEADLINES, headlines):
            row[header] = value
        for header, value in zip(REQUIRED_RSA_DESCRIPTIONS, descriptions):
            row[header] = value
        self.rows.append(row)
        return row

    def add_location(
        self,
        campaign: str,
        location: str,
        *,
        location_id: str = "",
        radius: str = "",
        bid_modifier: str = "",
    ) -> dict[str, str]:
        """Add location targeting with Location ID when available."""
        row = self._blank_row()
        row.update(
            {
                "Campaign": campaign,
                "Location": location,
                "Location ID": location_id,
                "Radius": radius,
                "Bid Modifier": bid_modifier,
            }
        )
        self.rows.append(row)
        return row

    def to_rows(self) -> list[dict[str, str]]:
        """Return a copy of generated rows."""
        return [dict(row) for row in self.rows]

    def to_tsv(self) -> str:
        """Return tab-separated Google Ads Editor content."""
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=self.columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(self.rows)
        return buffer.getvalue()

    def write_tsv(self, path: str | Path) -> Path:
        """Write UTF-16 tab-separated staging output."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.to_tsv(), encoding="utf-16")
        return output_path

    def validate(self, path: str | Path) -> dict[str, Any]:
        """Validate a written staging file through the active rebuild validator."""
        return validate_file(Path(path))

    def write_and_validate(self, path: str | Path) -> dict[str, Any]:
        """Write the TSV and return the active staging validator report."""
        output_path = self.write_tsv(path)
        return self.validate(output_path)

    def generate_csv(self) -> str:
        """Compatibility method returning TSV content for older callers."""
        return self.to_tsv()

    def generate_campaign(self, *_args: Any, **_kwargs: Any) -> str:
        """Retired compatibility path for old client-shaped campaign generation."""
        raise NotImplementedError(
            "The old client-specific Search campaign generator is retired. "
            "Use add_campaign, add_ad_group, add_keyword, add_rsa, add_location, "
            "then write_and_validate."
        )

    def _validate_criterion_type(self, criterion_type: str) -> None:
        if criterion_type not in ALLOWED_CRITERION_TYPES:
            raise ValueError("SearchCSVGenerator only supports Phrase and Negative Phrase criterion types.")

    def _search_network(self, networks: str) -> str:
        if networks.strip() != SEARCH_NETWORK_VALUE:
            raise ValueError("Search partners are disabled. Active Search staging uses Google search only.")
        return SEARCH_NETWORK_VALUE

    def _plain_keyword(self, keyword: str) -> str:
        plain = keyword.strip()
        if plain.startswith(('"', "[", "-")) or plain.endswith(('"', "]")):
            raise ValueError("Keyword must be plain text. Match and negative behavior belong in Criterion Type.")
        return plain

    def _validate_count(self, label: str, values: list[str], required: int) -> None:
        if len(values) != required:
            raise ValueError(f"Responsive search ads require exactly {required} {label}.")
        if any(not value.strip() for value in values):
            raise ValueError(f"Responsive search ad {label} cannot be blank.")

    def _format_budget(self, budget: float | str) -> str:
        try:
            return f"{float(str(budget).replace(',', '')):.2f}"
        except ValueError as exc:
            raise ValueError("Campaign budget must be numeric.") from exc
