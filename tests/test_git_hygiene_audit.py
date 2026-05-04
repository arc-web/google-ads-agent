from __future__ import annotations

from shared.rebuild.git_hygiene_audit import audit_status_lines


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
