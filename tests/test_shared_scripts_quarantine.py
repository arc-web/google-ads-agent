from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_migration_script_is_audit_only(tmp_path: Path) -> None:
    output_path = tmp_path / "migration_audit.json"

    result = subprocess.run(
        [
            sys.executable,
            "shared/scripts/migrate_campaign_architecture.py",
            "--analyze",
            "--json-output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["mode"] == "audit_only"
    assert report["mutations_enabled"] is False
    assert report["current_policy"]["match_type"] == "Phrase"
    assert report["current_policy"]["api_upload"] == "off"


def test_migration_script_rejects_legacy_mutation_mode() -> None:
    result = subprocess.run(
        [sys.executable, "shared/scripts/migrate_campaign_architecture.py", "--migrate"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "inactive" in result.stderr
    assert not (REPO_ROOT / "docs/MIGRATION_REPORT.md").exists()


def test_setup_mcp_script_is_inactive() -> None:
    help_result = subprocess.run(
        ["bash", "shared/scripts/setup_mcp.sh", "--help"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    run_result = subprocess.run(
        ["bash", "shared/scripts/setup_mcp.sh"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert help_result.returncode == 0
    assert "inactive" in help_result.stdout
    assert run_result.returncode == 2
    assert "does not install packages" in run_result.stdout


def test_shared_sql_status_script_is_documentation_only() -> None:
    sql_path = REPO_ROOT / "shared/scripts/database/update-client-status.sql"
    executable_lines = [
        line.strip()
        for line in sql_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("--")
    ]

    assert executable_lines == []


def test_shared_scripts_do_not_track_python_cache_files() -> None:
    result = subprocess.run(
        ["git", "ls-files", "shared/scripts"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    tracked_scripts = result.stdout.splitlines()
    assert not any(path.endswith((".pyc", ".pyo")) or "__pycache__" in path for path in tracked_scripts)
