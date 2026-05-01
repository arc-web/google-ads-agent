#!/usr/bin/env python3
"""Wrapper for static HTML report audit."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.presentation.report_quality_audit import main


if __name__ == "__main__":
    raise SystemExit(main())
