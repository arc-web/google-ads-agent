"""
Input dataclasses for the google_ads_agent copy engine.

All generators consume AdGroupContext or ClientContext as their primary input.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AdGroupContext:
    name: str                          # ad group name
    service: str                       # primary service being advertised
    geo: list[str]                     # target location modifiers
    USPs: list[str]                    # unique selling points
    top_keywords: list[str]            # target keywords for this ad group
    landing_url: str                   # final URL
    industry: str                      # industry or compliance profile
    insurance_accepted: list[str] = field(default_factory=list)
    practice_name: str = ""
    additional_context: str = ""       # free-form extra info


@dataclass
class ClientContext:
    agency: str                        # agency slug
    client: str                        # client slug
    practice_name: str
    services: list[str]
    geo: list[str]
    USPs: list[str]
    insurance_accepted: list[str] = field(default_factory=list)
    practice_type: str = ""            # industry-specific practice type
    website_url: str = ""
