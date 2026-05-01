from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC = REPO_ROOT / "docs/system_review/CLIENT_TEST_CANDIDATES_2026-05-01.md"


def test_client_candidate_review_covers_required_test_categories() -> None:
    text = DOC.read_text(encoding="utf-8")

    for phrase in [
        "Current Search Staging Candidate",
        "PMAX-Heavy Guard Candidate",
        "Simpler Raw Export Candidate",
        "clients/therappc/thinkhappylivehealthy/",
        "clients/evolution_restoration_and_renovation/",
        "clients/skytherapies/",
    ]:
        assert phrase in text


def test_client_candidate_review_does_not_authorize_client_data_movement() -> None:
    text = DOC.read_text(encoding="utf-8").lower()

    for phrase in [
        "keep all client data in place",
        "without moving, archiving, deleting, or reclassifying client data",
        "stop before:",
        "moving or archiving any client folder",
    ]:
        assert phrase in text
