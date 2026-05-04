from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_legacy_workflow_wrapper_points_to_active_contracts() -> None:
    result = subprocess.run(
        [sys.executable, "shared/google_ads_workflow.py"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "shared/rebuild/scaffold_client.py" in result.stdout
    assert "shared/rebuild/staging_validator.py" in result.stdout
    assert "Phrase-only by default" in result.stdout
    assert "API upload off" in result.stdout


def test_master_instructions_name_active_search_first_boundaries() -> None:
    instructions = (REPO_ROOT / "shared/MASTER_AI_AGENT_INSTRUCTIONS.md").read_text(encoding="utf-8")

    required_phrases = [
        "Validation authority: `python3 shared/rebuild/staging_validator.py --csv PATH_TO_STAGING_CSV`",
        "Search rebuild keywords are phrase match only by default.",
        "Generate 15 RSA headlines and 4 descriptions when possible.",
        "Keep Google Ads API upload off unless the user explicitly activates live automation.",
        "Validation reads and reports. It must not auto-fix or rewrite source staging CSVs.",
    ]

    for phrase in required_phrases:
        assert phrase in instructions


def test_master_instructions_keep_human_review_stops_visible() -> None:
    instructions = (REPO_ROOT / "shared/MASTER_AI_AGENT_INSTRUCTIONS.md").read_text(encoding="utf-8")

    for phrase in [
        "activating Google Ads API upload or any live account mutation",
        "activating PMAX as part of the current workflow",
        "deleting, archiving, or moving client data",
        "dropping safety branches or stashes after cleanup inventory",
        "changing the default Search policy away from phrase-only",
        "promoting client-specific strategy into shared code",
    ]:
        assert phrase in instructions


def test_no_blind_purge_contract_stays_visible() -> None:
    sources = [
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "docs" / "CLIENT_DIRECTORY_SCAFFOLDING.md",
        REPO_ROOT / "shared" / "MASTER_AI_AGENT_INSTRUCTIONS.md",
    ]

    required_phrases = [
        "Never purge, drop, archive, delete, or discard",
        "Every removal needs a documented logical resolution",
        "Client data, source inputs, reports, stashes, and generated artifacts must be preserved until",
    ]

    for source in sources:
        text = source.read_text(encoding="utf-8")
        for phrase in required_phrases:
            assert phrase in text
