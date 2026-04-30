"""
build_review_doc.py

Stage 9 entry point: takes a finished review HTML and exports the
client-facing PDF using Chrome headless with the canonical flags.

Lesson (see hitl_doc_design_postmortem_2026-04-28.md):
The PDF export command has 6 flags that all matter. Forgetting any of
them produces a broken PDF (page numbers in margins, white edges, gpu
crash, mid-render screenshots). This script wraps the working command
so future builds run identically.

Usage:
    python3 -m shared.presentation.build_review_doc \\
        --html clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28.html \\
        --pdf  clients/therappc/thinkhappylivehealthy/build/2026-04-28_account_rebuild/campaign_review_2026-04-28.pdf \\
        --mirror-desktop

Or programmatically:
    from shared.presentation.build_review_doc import export_pdf
    export_pdf(html_path, pdf_path, mirror_desktop=True)
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Canonical Chrome headless flags. Each one matters - do not drop any.
PDF_FLAGS = [
    "--headless=new",
    "--print-to-pdf-no-header",
    "--no-pdf-header-footer",
    "--no-margins",
    "--disable-gpu",
    "--run-all-compositor-stages-before-draw",
]


class PDFBuildError(RuntimeError):
    """Chrome headless export failed."""


def export_pdf(
    html_path: Path | str,
    pdf_path: Path | str,
    *,
    mirror_desktop: bool = False,
    chrome_bin: str = CHROME_BIN,
    timeout_seconds: int = 60,
) -> Path:
    """
    Export an HTML review document to PDF via Chrome headless.

    Args:
        html_path: absolute path to the source HTML.
        pdf_path: absolute path where the PDF should be written.
        mirror_desktop: if True, also copy the PDF + HTML to ~/Desktop
            for fast client handoff. Canonical copy stays in the repo.
        chrome_bin: path to Chrome on disk.
        timeout_seconds: hard timeout for the chrome subprocess call.
            Never call subprocess without one (subprocess timeout rule).

    Returns:
        The absolute Path of the written PDF.

    Raises:
        FileNotFoundError if html_path does not exist.
        PDFBuildError if Chrome exits non-zero or times out.
    """
    html_path = Path(html_path).resolve()
    pdf_path = Path(pdf_path).resolve()

    if not html_path.is_file():
        raise FileNotFoundError(f"HTML not found: {html_path}")

    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        chrome_bin,
        f"--print-to-pdf={pdf_path}",
        *PDF_FLAGS,
        f"file://{html_path}",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise PDFBuildError(
            f"Chrome timed out after {timeout_seconds}s building {pdf_path}"
        ) from exc

    if result.returncode != 0 or not pdf_path.exists():
        raise PDFBuildError(
            f"Chrome exited {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    if mirror_desktop:
        desktop = Path.home() / "Desktop"
        if desktop.is_dir():
            shutil.copy2(pdf_path, desktop / pdf_path.name)
            shutil.copy2(html_path, desktop / html_path.name)

    return pdf_path


def _cli() -> int:
    parser = argparse.ArgumentParser(
        description="Build the client-facing campaign review PDF.",
    )
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument(
        "--mirror-desktop",
        action="store_true",
        help="Also copy HTML+PDF to ~/Desktop for fast handoff.",
    )
    args = parser.parse_args()

    try:
        out = export_pdf(
            args.html,
            args.pdf,
            mirror_desktop=args.mirror_desktop,
        )
    except (FileNotFoundError, PDFBuildError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
