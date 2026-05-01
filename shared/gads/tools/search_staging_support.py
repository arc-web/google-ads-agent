"""Search-safe support helpers for active Google Ads Editor staging.

This module is the active Search support surface inside ``shared/gads/tools``.
Older keyword, ad group, extension, and planning tools remain salvage material
until their reusable behavior is migrated here or into another tested helper.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


INACTIVE_MATCH_TYPES = {"Broad", "Exact", "BROAD", "EXACT"}
ACTIVE_MATCH_TYPE = "Phrase"
ACTIVE_NEGATIVE_MATCH_TYPE = "Negative Phrase"


@dataclass(frozen=True)
class SearchKeywordPlan:
    """Generic keyword plan for Search staging."""

    text: str
    criterion_type: str = ACTIVE_MATCH_TYPE
    final_url: str = ""
    status: str = "Paused"

    def to_exporter_dict(self) -> dict[str, str]:
        """Return the dictionary shape expected by GoogleAdsEditorExporter."""
        return {
            "text": self.text,
            "criterion_type": self.criterion_type,
            "final_url": self.final_url,
            "status": self.status,
        }


@dataclass(frozen=True)
class SearchAdGroupPlan:
    """Generic ad group plan for Search staging."""

    name: str
    keywords: list[SearchKeywordPlan] = field(default_factory=list)
    final_url: str = ""
    status: str = "Paused"
    rsa: dict[str, Any] | None = None

    def to_exporter_dict(self) -> dict[str, Any]:
        """Return the dictionary shape expected by GoogleAdsEditorExporter."""
        row: dict[str, Any] = {
            "name": self.name,
            "keywords": [keyword.to_exporter_dict() for keyword in self.keywords],
            "final_url": self.final_url,
            "status": self.status,
        }
        if self.rsa:
            row["rsa"] = self.rsa
        return row


def phrase_keyword(text: str, *, final_url: str = "", status: str = "Paused") -> SearchKeywordPlan:
    """Create a plain phrase keyword plan for the active Search workflow."""
    return SearchKeywordPlan(
        text=_plain_keyword_text(text),
        criterion_type=ACTIVE_MATCH_TYPE,
        final_url=final_url,
        status=status,
    )


def negative_phrase_keyword(text: str, *, status: str = "Paused") -> SearchKeywordPlan:
    """Create a plain negative phrase keyword plan for the active Search workflow."""
    return SearchKeywordPlan(
        text=_plain_keyword_text(text),
        criterion_type=ACTIVE_NEGATIVE_MATCH_TYPE,
        status=status,
    )


def search_ad_group(
    name: str,
    keywords: list[str | SearchKeywordPlan],
    *,
    final_url: str = "",
    rsa: dict[str, Any] | None = None,
    status: str = "Paused",
) -> SearchAdGroupPlan:
    """Create a generic Search ad group plan with phrase-only keyword defaults."""
    ad_group_name = name.strip()
    if not ad_group_name:
        raise ValueError("Ad group name is required.")

    keyword_plans = [
        keyword if isinstance(keyword, SearchKeywordPlan) else phrase_keyword(keyword, final_url=final_url, status=status)
        for keyword in keywords
    ]
    return SearchAdGroupPlan(
        name=ad_group_name,
        keywords=keyword_plans,
        final_url=final_url,
        status=status,
        rsa=rsa,
    )


def _plain_keyword_text(text: str) -> str:
    keyword = text.strip()
    if not keyword:
        raise ValueError("Keyword text is required.")
    if keyword in INACTIVE_MATCH_TYPES:
        raise ValueError("Keyword text cannot be a match type.")
    if keyword.startswith(('"', "[", "-")) or keyword.endswith(('"', "]")):
        raise ValueError("Keyword must be plain text. Match behavior belongs in Criterion Type.")
    return keyword
