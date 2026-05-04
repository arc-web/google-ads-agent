"""Match-type policy helpers for Search staging and optimization review.

Google Ads Editor CSVs stay import-safe. Origin, preservation, and exact-test
decisions are stored in sidecar artifacts instead of custom staging columns.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


MATCH_TYPE_MODES = {
    "new_rebuild",
    "revision_existing_account",
    "optimization_review",
    "exact_test",
}

DEFAULT_NEW_MATCH_TYPES = {"Phrase", "Negative Phrase"}
PRESERVABLE_EXISTING_MATCH_TYPES = {"Exact", "Negative Exact"}


@dataclass(frozen=True)
class MatchTypeDecision:
    status: str
    rule: str
    message: str
    criterion_type: str
    keyword_key: str = ""
    origin: str = ""


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def keyword_origin_key(row: dict[str, Any]) -> str:
    campaign = normalize_text(row.get("Campaign")).lower()
    ad_group = normalize_text(row.get("Ad Group") or row.get("Ad group")).lower()
    criterion_type = normalize_text(row.get("Criterion Type")).lower()
    keyword = normalize_text(row.get("Keyword")).lower()
    return "|".join([campaign, ad_group, criterion_type, keyword])


def load_keyword_origin_map(path: Path | str | None) -> dict[str, Any]:
    if not path:
        return {}
    source = Path(path)
    if not source.exists():
        return {}
    payload = json.loads(source.read_text(encoding="utf-8") or "{}")
    if isinstance(payload, dict) and isinstance(payload.get("keywords"), dict):
        return payload["keywords"]
    if isinstance(payload, dict):
        return payload
    return {}


def source_proven(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    origin = str(entry.get("origin") or entry.get("source") or "").strip()
    if origin in {"source_account_export", "existing_account_export", "original_account_export"}:
        return True
    return bool(entry.get("source_account_export") or entry.get("existing_account_export"))


def preservation_approved(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    if entry.get("preserve") is True:
        return True
    status = str(entry.get("relevance_status") or entry.get("decision") or entry.get("status") or "").lower()
    return status in {"preserve", "relevant", "review", "approved"}


def exact_test_approved(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    if entry.get("approved_exact_test") is True:
        return True
    status = str(entry.get("test_status") or entry.get("decision") or "").lower()
    return status in {"approved_exact_test", "approved_test", "exact_test_approved"}


def evaluate_match_type(
    row: dict[str, Any],
    *,
    mode: str = "new_rebuild",
    origin_map: dict[str, Any] | None = None,
) -> MatchTypeDecision:
    if mode not in MATCH_TYPE_MODES:
        raise ValueError(f"Unsupported match-type validation mode: {mode}")

    criterion_type = normalize_text(row.get("Criterion Type"))
    key = keyword_origin_key(row)
    entry = (origin_map or {}).get(key, {})
    origin = str(entry.get("origin") or entry.get("source") or "") if isinstance(entry, dict) else ""

    if not criterion_type:
        return MatchTypeDecision("error", "criterion_type_required", "Keyword row is missing Criterion Type.", criterion_type, key, origin)

    if criterion_type == "Broad":
        return MatchTypeDecision("error", "broad_match_blocked", "Broad match remains blocked in every workflow mode.", criterion_type, key, origin)

    if criterion_type in DEFAULT_NEW_MATCH_TYPES:
        return MatchTypeDecision("pass", "default_phrase_first_match_type", "Phrase-first match type is allowed.", criterion_type, key, origin)

    if criterion_type == "Exact":
        if mode == "exact_test" and exact_test_approved(entry):
            return MatchTypeDecision("warning", "approved_exact_test", "New exact match is approved as a controlled test sidecar decision.", criterion_type, key, origin)
        if mode in {"revision_existing_account", "optimization_review"} and source_proven(entry) and preservation_approved(entry):
            return MatchTypeDecision("warning", "preserved_existing_exact", "Existing relevant exact match is source-proven and preserved for review.", criterion_type, key, origin)
        return MatchTypeDecision("error", "new_exact_requires_approval", "New exact match requires source proof or an approved controlled exact-test sidecar decision.", criterion_type, key, origin)

    if criterion_type == "Negative Exact":
        if mode in {"revision_existing_account", "optimization_review"} and source_proven(entry):
            return MatchTypeDecision("warning", "preserved_existing_negative_exact", "Existing negative exact is source-proven and preserved for review.", criterion_type, key, origin)
        return MatchTypeDecision("error", "new_negative_exact_blocked", "New negative exact is blocked. Stage new negatives as Negative Phrase.", criterion_type, key, origin)

    return MatchTypeDecision("error", "unsupported_criterion_type", "Keyword row has unsupported Criterion Type.", criterion_type, key, origin)


def build_keyword_origin_map(rows: list[dict[str, Any]]) -> dict[str, Any]:
    keywords: dict[str, Any] = {}
    for row in rows:
        if not normalize_text(row.get("Keyword")):
            continue
        criterion_type = normalize_text(row.get("Criterion Type"))
        key = keyword_origin_key(row)
        keywords[key] = {
            "origin": "source_account_export",
            "campaign": normalize_text(row.get("Campaign")),
            "ad_group": normalize_text(row.get("Ad Group") or row.get("Ad group")),
            "keyword": normalize_text(row.get("Keyword")),
            "criterion_type": criterion_type,
            "preserve": criterion_type in PRESERVABLE_EXISTING_MATCH_TYPES,
            "relevance_status": "review" if criterion_type in PRESERVABLE_EXISTING_MATCH_TYPES else "source_observed",
        }
    return keywords


def write_match_type_sidecars(
    build_dir: Path,
    *,
    source_rows: list[dict[str, Any]] | None = None,
    staged_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Path]:
    build_dir.mkdir(parents=True, exist_ok=True)
    origin_map = build_keyword_origin_map(source_rows or [])
    keyword_origin_map = build_dir / "keyword_origin_map.json"
    preservation_audit = build_dir / "match_type_preservation_audit.json"
    existing_exact_review = build_dir / "existing_exact_review.csv"
    exact_candidates = build_dir / "exact_match_test_candidates.csv"

    keyword_origin_map.write_text(json.dumps({"keywords": origin_map}, indent=2) + "\n", encoding="utf-8")

    review_rows = [
        entry
        for entry in origin_map.values()
        if entry.get("criterion_type") in PRESERVABLE_EXISTING_MATCH_TYPES
    ]
    with existing_exact_review.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["campaign", "ad_group", "keyword", "criterion_type", "origin", "relevance_status", "preserve"],
        )
        writer.writeheader()
        for entry in review_rows:
            writer.writerow({field: entry.get(field, "") for field in writer.fieldnames})

    with exact_candidates.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["campaign", "ad_group", "keyword", "reason", "source_metric", "approval_status"],
        )
        writer.writeheader()

    decisions = []
    for row in staged_rows or []:
        if not normalize_text(row.get("Keyword")):
            continue
        decisions.append(asdict(evaluate_match_type(row, mode="revision_existing_account", origin_map=origin_map)))

    preservation_audit.write_text(
        json.dumps(
            {
                "policy": "phrase_first_exact_preserving",
                "source_existing_keywords": len(origin_map),
                "preserved_exact_review_rows": len(review_rows),
                "staged_keyword_decisions": decisions,
                "staging_csv_columns_extended": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "keyword_origin_map": keyword_origin_map,
        "match_type_preservation_audit": preservation_audit,
        "existing_exact_review": existing_exact_review,
        "exact_match_test_candidates": exact_candidates,
    }
