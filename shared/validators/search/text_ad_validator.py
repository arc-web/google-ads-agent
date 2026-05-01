#!/usr/bin/env python3
"""Legacy Search text ad validator wrapper."""

from __future__ import annotations

from typing import Any

from .search_text_ad_validator import SearchTextAdValidator


class TextAdValidator:
    """
    Compatibility wrapper around the active RSA validator.

    The old implementation assumed expanded text ads and one client-specific
    brand. This class now validates generic Responsive Search Ad staging rows.
    """

    def __init__(self, validation_rules: dict[str, Any] | None = None):
        self.validator = SearchTextAdValidator(validation_rules)

    def validate_text_ad(self, csv_path: str, row: dict[str, Any], row_num: int) -> list[dict[str, Any]]:
        """Validate one RSA row using active rules."""
        if not self._looks_like_ad_row(row):
            return []
        return self.validate_text_ad_row(row, row_num)

    def validate_text_ad_row(self, row: dict[str, Any], row_num: int) -> list[dict[str, Any]]:
        """Validate one RSA row using active rules."""
        return [issue.__dict__ for issue in self.validator.validate_text_ad_row(row, row_num)]

    def validate_text_ad_data(self, ad_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate multiple RSA rows using active rules."""
        return [issue.__dict__ for issue in self.validator.validate_text_ad_data(ad_rows)]

    def assess_ad_quality(self, row: dict[str, Any]) -> dict[str, Any]:
        """Return generic RSA completeness metadata."""
        headline_count = sum(1 for index in range(1, 16) if str(row.get(f"Headline {index}", "") or "").strip())
        description_count = sum(1 for index in range(1, 5) if str(row.get(f"Description {index}", "") or "").strip())
        has_final_url = bool(str(row.get("Final URL", "") or "").strip())
        quality_score = headline_count + (description_count * 2) + (2 if has_final_url else 0)
        max_score = 25

        return {
            "quality_score": quality_score,
            "max_score": max_score,
            "quality_rating": "High" if quality_score >= 22 else "Medium" if quality_score >= 14 else "Low",
            "headline_count": headline_count,
            "description_count": description_count,
            "has_final_url": has_final_url,
            "recommendations": self._quality_recommendations(headline_count, description_count, has_final_url),
        }

    def _looks_like_ad_row(self, row: dict[str, Any]) -> bool:
        ad_type = str(row.get("Ad type") or row.get("Ad Type") or "").strip()
        return bool(ad_type or row.get("Headline 1") or row.get("Description 1"))

    def _quality_recommendations(
        self, headline_count: int, description_count: int, has_final_url: bool
    ) -> list[str]:
        recommendations: list[str] = []
        if headline_count < 15:
            recommendations.append("Provide 15 RSA headlines when possible.")
        if description_count < 4:
            recommendations.append("Provide 4 RSA descriptions when possible.")
        if not has_final_url:
            recommendations.append("Provide a final URL.")
        return recommendations
