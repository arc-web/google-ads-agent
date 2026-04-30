#!/usr/bin/env python3
"""
Rendered PDF visual audit for client report QA.

Static HTML checks are necessary, but they cannot prove that a PDF page
looks filled after Chrome pagination. This script renders each page to PNG
and flags pages with too little non-background content.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image


@dataclass
class PageAudit:
    page: int
    width: int
    height: int
    content_ratio: float
    vertical_span_ratio: float
    max_content_y_ratio: float
    status: str
    image: str


def is_content_pixel(pixel: tuple[int, int, int]) -> bool:
    red, green, blue = pixel[:3]
    channels = (red, green, blue)

    if min(channels) < 120:
        return True

    # White paper and the report's warm off-white background should not count
    # as meaningful page content.
    if red >= 238 and green >= 235 and blue >= 228:
        return False

    # Very light beige panels can cover the page background. Count only when
    # the pixel is materially darker or more saturated.
    spread = max(channels) - min(channels)
    return spread > 14 or min(channels) < 218


def audit_image(path: Path, page: int, min_content_ratio: float) -> PageAudit:
    image = Image.open(path).convert("RGB")
    width, height = image.size
    pixels = image.get_flattened_data() if hasattr(image, "get_flattened_data") else image.getdata()
    total = width * height
    content = 0
    min_y: int | None = None
    max_y: int | None = None
    for index, pixel in enumerate(pixels):
        if not is_content_pixel(pixel):
            continue
        content += 1
        y = index // width
        min_y = y if min_y is None else min(min_y, y)
        max_y = y if max_y is None else max(max_y, y)
    ratio = content / total
    vertical_span_ratio = 0.0 if min_y is None or max_y is None else (max_y - min_y + 1) / height
    max_content_y_ratio = 0.0 if max_y is None else max_y / height
    status = "pass"
    if ratio < min_content_ratio:
        status = "fail"
    if vertical_span_ratio < 0.18 and max_content_y_ratio < 0.35:
        status = "fail"
    return PageAudit(
        page,
        width,
        height,
        ratio,
        vertical_span_ratio,
        max_content_y_ratio,
        status,
        str(path),
    )


def render_pdf(pdf_path: Path, output_dir: Path, resolution: int) -> list[Path]:
    prefix = output_dir / "page"
    cmd = [
        "pdftoppm",
        "-png",
        "-r",
        str(resolution),
        str(pdf_path),
        str(prefix),
    ]
    subprocess.run(cmd, check=True)
    return sorted(output_dir.glob("page-*.png"))


def audit_pdf(
    pdf_path: Path,
    pages_dir: Path | None,
    min_content_ratio: float,
    resolution: int,
) -> tuple[list[PageAudit], Path]:
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)

    if pages_dir:
        pages_dir.mkdir(parents=True, exist_ok=True)
        work_dir = pages_dir
        clear_after = False
    else:
        work_dir = Path(tempfile.mkdtemp(prefix="pdf_visual_audit_"))
        clear_after = True

    try:
        images = render_pdf(pdf_path, work_dir, resolution)
        audits = [
            audit_image(path, index, min_content_ratio)
            for index, path in enumerate(images, start=1)
        ]
        if clear_after:
            keep_dir = work_dir
        else:
            keep_dir = work_dir
        return audits, keep_dir
    except Exception:
        if clear_after:
            shutil.rmtree(work_dir, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit rendered PDF page density.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--pages-dir", type=Path)
    parser.add_argument("--min-content-ratio", type=float, default=0.032)
    parser.add_argument("--resolution", type=int, default=72)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    audits, pages_dir = audit_pdf(
        args.pdf,
        args.pages_dir,
        args.min_content_ratio,
        args.resolution,
    )
    failed = [audit for audit in audits if audit.status == "fail"]

    payload = {
        "pdf": str(args.pdf),
        "pages_dir": str(pages_dir),
        "pages": len(audits),
        "failures": len(failed),
        "min_content_ratio": args.min_content_ratio,
        "audits": [asdict(audit) for audit in audits],
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(
            f"pages={payload['pages']} failures={payload['failures']} "
            f"min_content_ratio={args.min_content_ratio}"
        )
        for audit in audits:
            print(
                f"page {audit.page}: {audit.status} "
                f"content_ratio={audit.content_ratio:.4f} "
                f"vertical_span={audit.vertical_span_ratio:.4f} "
                f"max_y={audit.max_content_y_ratio:.4f} image={audit.image}"
            )

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
