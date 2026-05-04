from __future__ import annotations

from pathlib import Path

from shared.rebuild.git_hygiene_audit import audit_status_lines, has_resolution_ledger


def test_git_hygiene_audit_flags_credentials_and_generated_noise() -> None:
    findings = audit_status_lines(
        [
            "?? CREDENTIALS.md",
            " M shared/module.py",
            "?? shared/__pycache__/module.cpython-314.pyc",
            "?? .env",
        ]
    )

    assert [(finding.category, finding.path) for finding in findings] == [
        ("credential", "CREDENTIALS.md"),
        ("generated", "shared/__pycache__/module.cpython-314.pyc"),
        ("credential", ".env"),
    ]


def test_resolution_ledger_mode_flags_unresolved_deletions() -> None:
    findings = audit_status_lines(
        [
            " D clients/example/build/stale.csv",
            "R  old/path.csv -> new/path.csv",
            " M shared/module.py",
        ],
        require_resolution_ledger=True,
        resolution_ledger_present=False,
    )

    assert [(finding.category, finding.path) for finding in findings] == [
        ("unresolved-removal", "clients/example/build/stale.csv"),
        ("unresolved-removal", "new/path.csv"),
    ]


def test_resolution_ledger_mode_allows_deletions_with_ledger() -> None:
    findings = audit_status_lines(
        [" D clients/example/build/stale.csv"],
        require_resolution_ledger=True,
        resolution_ledger_present=True,
    )

    assert findings == []


def test_resolution_ledger_detection_ignores_template(tmp_path: Path) -> None:
    review_dir = tmp_path / "docs" / "system_review"
    review_dir.mkdir(parents=True)
    (review_dir / "CLEANUP_RESOLUTION_LEDGER_TEMPLATE.md").write_text("template", encoding="utf-8")

    assert has_resolution_ledger(tmp_path) is False

    (review_dir / "CLEANUP_RESOLUTION_LEDGER_2026-05-05.md").write_text("real ledger", encoding="utf-8")

    assert has_resolution_ledger(tmp_path) is True
