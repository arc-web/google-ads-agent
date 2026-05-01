#!/usr/bin/env python3
"""Wrapper for client review HTML preparation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.presentation.prepare_client_review_html import main


if __name__ == "__main__":
    raise SystemExit(main())
