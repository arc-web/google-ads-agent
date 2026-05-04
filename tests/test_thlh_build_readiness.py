from __future__ import annotations

import csv
from pathlib import Path

from shared.validators.master_validator import MasterValidator
from shared.validators.search_master_validator import SearchMasterValidator


REPO_ROOT = Path(__file__).resolve().parents[1]
THLH_BUILD = REPO_ROOT / "clients/therappc/thinkhappylivehealthy/build/search_rebuild_test"
REV1 = THLH_BUILD / "THHL_Search_Services_Editor_Staging_REV1.csv"
REV2 = THLH_BUILD / "THHL_Search_Services_Editor_Staging_REV2.csv"
DOC = REPO_ROOT / "docs/system_review/THLH_BUILD_READINESS_2026-05-01.md"


def test_thlh_rev1_staging_is_now_blocked_by_headline_and_description_quality() -> None:
    master = MasterValidator().validate_csv_file(str(REV1))
    search = SearchMasterValidator().validate_csv_file(str(REV1))

    assert master["final_status"] == "FAIL"
    assert master["validation_report"]["total_issues"] == 685
    assert search["success"] is False
    assert search["validation_report"]["total_issues"] == 685
    assert {
        issue["issue_type"] for issue in master["validation_report"]["issues"]
    } == {
        "description_missing_cta",
        "description_under_value_minimum",
        "headline_broken_truncation",
        "headline_low_value_filler",
        "headline_minimum_value",
        "headline_repeated_root",
        "headline_semantic_duplicate",
        "smart_bidding_data_threshold_review",
    }


def test_thlh_rev1_staging_shape_matches_readiness_doc() -> None:
    rows = list(csv.DictReader(REV1.read_text(encoding="utf-16").splitlines(), delimiter="\t"))

    assert len(rows) == 470
    assert {row["Campaign"] for row in rows if row.get("Campaign Type") == "Search"} == {
        "ARC - Search - Adult Therapy - V1",
        "ARC - Search - Brand - V1",
        "ARC - Search - Psychiatry - V1",
        "ARC - Search - Testing - V1",
    }
    assert {row["Criterion Type"] for row in rows if row.get("Keyword")} == {
        "Phrase",
        "Negative Phrase",
    }
    assert sum(1 for row in rows if row.get("Ad type") == "Responsive search ad") == 49
    assert not [header for header in rows[0] if "upload" in header.lower() or "api" in header.lower()]


def test_thlh_rev2_staging_passes_length_rules_but_needs_copy_rebuild() -> None:
    master = MasterValidator().validate_csv_file(str(REV2))
    search = SearchMasterValidator().validate_csv_file(str(REV2))
    rows = list(csv.DictReader(REV2.read_text(encoding="utf-16").splitlines(), delimiter="\t"))

    assert master["final_status"] == "FAIL"
    assert master["validation_report"]["total_issues"] == 238
    assert search["success"] is False
    assert search["validation_report"]["total_issues"] == 238
    assert {
        issue["issue_type"] for issue in master["validation_report"]["issues"]
    } == {
        "description_missing_cta",
        "description_under_value_minimum",
        "headline_broken_truncation",
        "headline_repeated_root",
        "headline_semantic_duplicate",
        "smart_bidding_data_threshold_review",
    }
    assert {row["Networks"] for row in rows if row.get("Networks")} == {"Google search"}
    for row in rows:
        if row.get("Ad type") != "Responsive search ad":
            continue
        for index in range(1, 16):
            assert 25 <= len(row[f"Headline {index}"]) <= 30


def test_thlh_readiness_doc_separates_staging_clean_from_one_shot_package() -> None:
    text = DOC.read_text(encoding="utf-8")

    for phrase in [
        "THLH is the active first client",
        "not a live-launch approval",
        "REV2 repairs the short RSA headlines",
        "headline repairs applied: 443 placements across 63 unique weak headlines",
        "all RSA headlines are now 25 to 30 characters",
        "older `human_review.md` describes an earlier broad service build",
        "current staging review authority is `THHL_Search_Services_Editor_Staging_REV2_review.md`",
        "Keep API upload off",
    ]:
        assert phrase in text
