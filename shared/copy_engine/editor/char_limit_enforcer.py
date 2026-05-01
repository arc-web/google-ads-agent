"""
char_limit_enforcer.py

Hard char-limit enforcer for Google Ads RSA assets.

Lesson (see hitl_doc_design_postmortem_2026-04-28.md, item 12):
The first THHL build shipped 6 over-limit assets to the client review
document. Headlines were flagged red rather than fixed at the source.
A client should never see a flagged violation - generators must enforce
the cap before any asset reaches a downstream stage.

Use this module's `enforce` functions in any RSA generator. They raise
CharLimitError on violation. Catch and rewrite, or fail the build.

Headline limit: 30 chars
Description limit: 90 chars
Path limit: 15 chars
"""

from __future__ import annotations

from dataclasses import dataclass

HEADLINE_MAX = 30
DESCRIPTION_MAX = 90
PATH_MAX = 15


class CharLimitError(ValueError):
    """Raised when an asset exceeds its hard char limit."""

    def __init__(self, asset_type: str, asset_text: str, limit: int):
        self.asset_type = asset_type
        self.asset_text = asset_text
        self.limit = limit
        self.actual = len(asset_text)
        super().__init__(
            f"{asset_type} exceeds {limit} char limit "
            f"({self.actual} chars): {asset_text!r}"
        )


@dataclass
class Violation:
    asset_type: str
    asset_text: str
    actual: int
    limit: int

    @property
    def overage(self) -> int:
        return self.actual - self.limit


def enforce_headline(text: str) -> str:
    """Return text unchanged if at or under 30 chars. Raise otherwise."""
    if len(text) > HEADLINE_MAX:
        raise CharLimitError("headline", text, HEADLINE_MAX)
    return text


def enforce_description(text: str) -> str:
    """Return text unchanged if at or under 90 chars. Raise otherwise."""
    if len(text) > DESCRIPTION_MAX:
        raise CharLimitError("description", text, DESCRIPTION_MAX)
    return text


def enforce_path(text: str) -> str:
    """Return text unchanged if at or under 15 chars. Raise otherwise."""
    if len(text) > PATH_MAX:
        raise CharLimitError("path", text, PATH_MAX)
    return text


def audit_rsa(
    headlines: list[str],
    descriptions: list[str],
    path1: str = "",
    path2: str = "",
) -> list[Violation]:
    """
    Return all char-limit violations across an RSA asset bundle.

    Use when you want to collect every violation rather than fail on the
    first one. Pair with a generator that retries headlines that exceed
    the cap.
    """
    violations: list[Violation] = []

    for h in headlines:
        if len(h) > HEADLINE_MAX:
            violations.append(
                Violation("headline", h, len(h), HEADLINE_MAX)
            )

    for d in descriptions:
        if len(d) > DESCRIPTION_MAX:
            violations.append(
                Violation("description", d, len(d), DESCRIPTION_MAX)
            )

    for p in (path1, path2):
        if p and len(p) > PATH_MAX:
            violations.append(Violation("path", p, len(p), PATH_MAX))

    return violations


def assert_rsa_clean(
    headlines: list[str],
    descriptions: list[str],
    path1: str = "",
    path2: str = "",
) -> None:
    """
    Raise CharLimitError on any violation. Use as a hard gate before
    writing an RSA to CSV or to the client review document.
    """
    violations = audit_rsa(headlines, descriptions, path1, path2)
    if violations:
        first = violations[0]
        raise CharLimitError(first.asset_type, first.asset_text, first.limit)


__all__ = [
    "HEADLINE_MAX",
    "DESCRIPTION_MAX",
    "PATH_MAX",
    "CharLimitError",
    "Violation",
    "enforce_headline",
    "enforce_description",
    "enforce_path",
    "audit_rsa",
    "assert_rsa_clean",
]
