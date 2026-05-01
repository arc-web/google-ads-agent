from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PRESENTATIONS = REPO_ROOT / "presentations"
TOOLS = PRESENTATIONS / "tools"
REVIEW_DOC = REPO_ROOT / "docs/system_review/PRESENTATION_REPORT_PATH_REVIEW_2026-05-01.md"


def test_presentation_docs_keep_human_facing_surface_visible() -> None:
    combined = "\n".join(
        [
            (PRESENTATIONS / "README.md").read_text(encoding="utf-8"),
            (PRESENTATIONS / "docs/BUILD_INSTRUCTIONS.md").read_text(encoding="utf-8"),
            REVIEW_DOC.read_text(encoding="utf-8"),
        ]
    )

    for phrase in [
        "presentations/` is the human-facing",
        "presentations/tools/` contains commands",
        "shared/presentation/` contains implementation",
        "generated HTML, PDF, previews, audits, and contact sheets stay inside",
    ]:
        assert phrase in combined


def test_presentation_tool_wrappers_delegate_to_shared_implementation() -> None:
    wrappers = sorted(TOOLS.glob("*.py"))
    assert wrappers

    for wrapper in wrappers:
        text = wrapper.read_text(encoding="utf-8")
        assert "sys.path.insert(0, str(Path(__file__).resolve().parents[2]))" in text
        assert "from shared.presentation." in text
        assert 'if __name__ == "__main__":' in text
