#!/usr/bin/env python3
"""Wrapper for HTML to PDF export."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.presentation.build_review_doc import _cli


if __name__ == "__main__":
    raise SystemExit(_cli())
