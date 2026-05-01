#!/usr/bin/env python3
"""Inactive compatibility wrapper for the cleaned Google Ads Agent workflow.

The previous google_ads_workflow module was a legacy single-entry workflow with
client-specific assumptions. It is intentionally disabled so it cannot compete
with the current Google_Ads_Agent rebuild process.

Active workflow summary:
  Search-first account rebuilds
  Phrase match keywords by default
  Google Ads Editor staging files
  Validation through shared/rebuild/staging_validator.py
  Human review before any live account action
  API upload remains off
"""

from __future__ import annotations

import sys


MESSAGE = """\
shared/google_ads_workflow.py is deprecated.

Use the current Google_Ads_Agent process:
  docs/GOOGLE_ADS_AGENT_PROCESS.md

For a new client scaffold:
  python3 shared/rebuild/scaffold_client.py --agency AGENCY --client CLIENT

For active staging validation:
  python3 shared/rebuild/staging_validator.py --csv PATH_TO_STAGING_CSV

Current boundaries:
  Search-first
  Phrase-only by default
  Google Ads Editor staging
  API upload off
"""


def main() -> int:
    print(MESSAGE)
    return 2


if __name__ == "__main__":
    sys.exit(main())
