#!/usr/bin/env python3
"""Compatibility wrapper for the retired campaign planning script.

The previous script generated one-client and PMAX-shaped campaign exports. It
is intentionally inactive. Use ``search_campaign_builder.py`` for active
Search-first Google Ads Editor staging builds.
"""

from __future__ import annotations

import argparse


class CampaignPlanInactive(RuntimeError):
    """Raised when old campaign planning behavior is invoked."""


def create_campaign_plan(*_args, **_kwargs):
    """Retired compatibility function for old imports."""
    raise CampaignPlanInactive(
        "campaign_plan.py is inactive. Use shared.tools.campaign.search_campaign_builder "
        "for Search-first Google Ads Editor staging."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Retired campaign plan compatibility wrapper.")
    parser.add_argument("args", nargs="*", help="Ignored legacy arguments.")
    parser.parse_args()
    raise CampaignPlanInactive(
        "campaign_plan.py is inactive. Use shared.tools.campaign.search_campaign_builder "
        "for active Search staging generation."
    )


if __name__ == "__main__":
    raise SystemExit(main())
