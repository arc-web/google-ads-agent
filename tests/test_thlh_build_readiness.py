from __future__ import annotations

import csv
from pathlib import Path

from shared.validators.master_validator import MasterValidator
from shared.validators.search_master_validator import SearchMasterValidator


REPO_ROOT = Path(__file__).resolve().parents[1]
THLH_BUILD = REPO_ROOT / "clients/therappc/thinkhappylivehealthy/build/search_rebuild_test"
REV1 = THLH_BUILD / "THHL_Search_Services_Editor_Staging_REV1.csv"
DOC = REPO_ROOT / "docs/system_review/THLH_BUILD_READINESS_2026-05-01.md"


def test_thlh_rev1_staging_is_current_validator_clean() -> None:
    master = MasterValidator().validate_csv_file(str(REV1))
    search = SearchMasterValidator().validate_csv_file(str(REV1))

    assert master["final_status"] == "PASS"
    assert master["validation_report"]["total_issues"] == 0
    assert search["success"] is True
    assert search["validation_report"]["total_issues"] == 0


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


def test_thlh_readiness_doc_separates_staging_clean_from_one_shot_package() -> None:
    text = DOC.read_text(encoding="utf-8")

    for phrase in [
        "THLH is the active first client",
        "not a live-launch approval",
        "one-shot output contract is not fully packaged yet",
        "older `human_review.md` describes an earlier broad service build",
        "current REV1 review authority is `THHL_Search_Services_Editor_Staging_REV1_review.md`",
        "Keep API upload off",
    ]:
        assert phrase in text
