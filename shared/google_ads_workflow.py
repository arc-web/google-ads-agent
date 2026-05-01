#!/usr/bin/env python3
"""Deprecated compatibility wrapper.

The previous google_ads_workflow module was a legacy single-entry workflow with
client-specific assumptions. It is intentionally disabled so it cannot compete
with the current Google_Ads_Agent rebuild process.

Use:
  docs/GOOGLE_ADS_AGENT_PROCESS.md
  shared/rebuild/scaffold_client.py
"""

from __future__ import annotations

import sys


MESSAGE = """\
shared/google_ads_workflow.py is deprecated.

Use the Google_Ads_Agent process:
  docs/GOOGLE_ADS_AGENT_PROCESS.md

For a new client scaffold:
  python3 shared/rebuild/scaffold_client.py --agency AGENCY --client CLIENT
"""


def main() -> int:
    print(MESSAGE)
    return 2


if __name__ == "__main__":
    sys.exit(main())
