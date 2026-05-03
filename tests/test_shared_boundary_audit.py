from __future__ import annotations

from pathlib import Path

from shared.rebuild.code_boundary_audit import DEFAULT_BLOCKED_PATTERNS, audit_files, iter_python_files


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_active_shared_tools_do_not_contain_known_client_examples() -> None:
    files = iter_python_files(
        REPO_ROOT,
        ["shared/tools", "shared/gads/tools", "shared/new_campaign", "presentations/tools"],
    )
    findings = audit_files(REPO_ROOT, files, DEFAULT_BLOCKED_PATTERNS)

    assert findings == []
