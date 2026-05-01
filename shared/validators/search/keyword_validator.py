#!/usr/bin/env python3
"""Legacy Search keyword validator wrapper."""

from __future__ import annotations

from typing import Any

from .search_keyword_validator import SearchKeywordValidator


class KeywordValidator:
    """
    Compatibility wrapper around the active Search keyword validator.

    The old implementation defaulted to Exact and allowed Broad. This wrapper
    now delegates to phrase-only active validation and keeps only lightweight
    quality metadata for callers that request it.
    """

    def __init__(self, validation_rules: dict[str, Any] | None = None):
        self.validator = SearchKeywordValidator(validation_rules)

    def validate_keywords(self, csv_path: str, row: dict[str, Any], row_num: int) -> list[dict[str, Any]]:
        """Validate one keyword row using active rules."""
        if not str(row.get("Keyword", "") or "").strip():
            return []
        return self.validate_keyword_row(row, row_num)

    def validate_keyword_row(self, row: dict[str, Any], row_num: int) -> list[dict[str, Any]]:
        """Validate one keyword row using active rules."""
        return [issue.__dict__ for issue in self.validator.validate_keyword_row(row, row_num)]

    def validate_keyword_data(self, keyword_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate multiple keyword rows using active rules."""
        return [issue.__dict__ for issue in self.validator.validate_keyword_data(keyword_rows)]

    def validate_keyword_quality(self, keyword: str, match_type: str) -> dict[str, Any]:
        """
        Return generic quality metadata without changing validation policy.

        Quality scoring is intentionally advisory. It does not recommend Exact
        or Broad because those are not active defaults in the current process.
        """
        word_count = len(keyword.split())
        recommendations: list[str] = []

        if match_type not in {"Phrase", "Negative Phrase"}:
            recommendations.append("Use active Criterion Type values: Phrase or Negative Phrase.")

        if word_count == 0:
            recommendations.append("Provide keyword text.")
        elif word_count > 10:
            recommendations.append("Review very long keyword phrases for import clarity.")

        quality_score = 2
        if 2 <= word_count <= 6:
            quality_score += 2
        if match_type == "Phrase":
            quality_score += 2
        elif match_type == "Negative Phrase":
            quality_score += 1

        return {
            "keyword": keyword,
            "quality_score": quality_score,
            "max_score": 6,
            "recommendations": recommendations,
            "quality_rating": "High" if quality_score >= 5 else "Medium" if quality_score >= 3 else "Low",
        }
