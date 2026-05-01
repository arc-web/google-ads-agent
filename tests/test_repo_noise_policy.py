from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_machine_noise_ignore_rules_are_present() -> None:
    text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    for pattern in [".DS_Store", "__pycache__/", "*.pyc"]:
        assert pattern in text


def test_generated_noise_is_not_tracked_by_git() -> None:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    tracked = result.stdout.splitlines()
    generated = [
        path
        for path in tracked
        if path.endswith(".pyc")
        or "/__pycache__/" in path
        or path.endswith("/.DS_Store")
        or path == ".DS_Store"
        or "/.pytest_cache/" in path
        or path == ".pytest_cache"
    ]

    assert generated == []
