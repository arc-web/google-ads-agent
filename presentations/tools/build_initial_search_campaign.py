#!/usr/bin/env python3
"""Wrapper for the shared one-shot initial Search campaign builder."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.presentation.build_initial_search_campaign import main


if __name__ == "__main__":
    raise SystemExit(main())
