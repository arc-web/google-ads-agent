"""
Search ad extensions generator for the google_ads_agent copy engine.

Generates sitelinks, callouts, and structured snippets in a single LLM call.
Validates all Google Ads character limits and policy rules before returning.
"""

from dataclasses import dataclass, field
from copy_engine.context import ClientContext
from copy_engine.models import OpenRouterClient


# ---------------------------------------------------------------------------
# Character / count limits (Google Ads policy)
# ---------------------------------------------------------------------------
SITELINK_LINK_TEXT_MAX = 25
SITELINK_DESC_MAX = 35
SITELINK_MIN = 4
SITELINK_MAX = 20

CALLOUT_TEXT_MAX = 25
CALLOUT_MIN = 4
CALLOUT_MAX = 20

SNIPPET_VALUE_MAX = 25
SNIPPET_VALUES_MIN = 3
SNIPPET_VALUES_MAX = 10

# Google-approved structured snippet headers - "Services" and "Types" are
# the two most appropriate for healthcare; include both so the LLM can pick.
APPROVED_SNIPPET_HEADERS = {
    "Amenities", "Brands", "Courses", "Degree programs",
    "Destinations", "Featured hotels", "Insurance coverage",
    "Models", "Neighborhoods", "Service catalog",
    "Services", "Shows", "Styles", "Types",
}

HEALTHCARE_SNIPPET_HEADERS = {"Services", "Types"}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Sitelink:
    link_text: str      # max 25 chars
    description_1: str  # max 35 chars
    description_2: str  # max 35 chars


@dataclass
class Callout:
    text: str           # max 25 chars, noun phrase only


@dataclass
class StructuredSnippet:
    header: str         # must be from APPROVED_SNIPPET_HEADERS
    values: list[str] = field(default_factory=list)  # 3-10 values, max 25 chars each


@dataclass
class Extensions:
    sitelinks: list[Sitelink] = field(default_factory=list)
    callouts: list[Callout] = field(default_factory=list)
    snippets: list[StructuredSnippet] = field(default_factory=list)


# ---------------------------------------------------------------------------
# JSON schema passed to complete_json for LLM guidance
# ---------------------------------------------------------------------------

_RESPONSE_SCHEMA = {
    "sitelinks": [
        {
            "link_text": "string, max 25 chars, service name or action phrase",
            "description_1": "string, max 35 chars",
            "description_2": "string, max 35 chars",
        }
    ],
    "callouts": [
        {"text": "string, max 25 chars, noun phrase only, no punctuation"}
    ],
    "snippets": [
        {
            "header": "string, must be 'Services' or 'Types' for healthcare",
            "values": ["string, max 25 chars each"],
        }
    ],
}


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class ExtensionGenerator:
    """
    Generates Google Search ad extensions (sitelinks, callouts, structured
    snippets) for a given ClientContext using a single LLM call.
    """

    def __init__(self, client: OpenRouterClient):
        self._client = client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, ctx: ClientContext) -> Extensions:
        """
        Call the LLM once, parse the JSON response, validate all limits,
        and return a populated Extensions dataclass.

        Raises ValueError if the LLM response fails validation after
        truncation/repair attempts.
        """
        system = self._build_system_prompt()
        user = self._build_user_prompt(ctx)

        raw = self._client.complete_json(
            system=system,
            user=user,
            schema=_RESPONSE_SCHEMA,
            max_tokens=2500,
        )

        extensions = self._parse(raw)
        errors = self.validate(extensions)
        if errors:
            # Attempt auto-repair (truncate to limits) then re-validate
            extensions = self._repair(extensions)
            errors = self.validate(extensions)
            if errors:
                raise ValueError(
                    f"Extensions failed validation after repair:\n"
                    + "\n".join(f"  - {e}" for e in errors)
                )

        return extensions

    def validate(self, extensions: Extensions) -> list[str]:
        """
        Check all character limits and count constraints.
        Returns a list of human-readable error strings (empty = valid).
        """
        errors: list[str] = []

        # --- Sitelinks ---
        n = len(extensions.sitelinks)
        if n < SITELINK_MIN:
            errors.append(f"Sitelinks: need at least {SITELINK_MIN}, got {n}")
        if n > SITELINK_MAX:
            errors.append(f"Sitelinks: max {SITELINK_MAX}, got {n}")
        for i, sl in enumerate(extensions.sitelinks):
            if len(sl.link_text) > SITELINK_LINK_TEXT_MAX:
                errors.append(
                    f"Sitelink[{i}] link_text too long "
                    f"({len(sl.link_text)} > {SITELINK_LINK_TEXT_MAX}): '{sl.link_text}'"
                )
            if len(sl.description_1) > SITELINK_DESC_MAX:
                errors.append(
                    f"Sitelink[{i}] description_1 too long "
                    f"({len(sl.description_1)} > {SITELINK_DESC_MAX}): '{sl.description_1}'"
                )
            if len(sl.description_2) > SITELINK_DESC_MAX:
                errors.append(
                    f"Sitelink[{i}] description_2 too long "
                    f"({len(sl.description_2)} > {SITELINK_DESC_MAX}): '{sl.description_2}'"
                )

        # --- Callouts ---
        n = len(extensions.callouts)
        if n < CALLOUT_MIN:
            errors.append(f"Callouts: need at least {CALLOUT_MIN}, got {n}")
        if n > CALLOUT_MAX:
            errors.append(f"Callouts: max {CALLOUT_MAX}, got {n}")
        for i, co in enumerate(extensions.callouts):
            if len(co.text) > CALLOUT_TEXT_MAX:
                errors.append(
                    f"Callout[{i}] text too long "
                    f"({len(co.text)} > {CALLOUT_TEXT_MAX}): '{co.text}'"
                )
            # Warn on policy violations (verb phrases, punctuation)
            if co.text.endswith("!"):
                errors.append(
                    f"Callout[{i}] ends with '!' - punctuation not allowed: '{co.text}'"
                )

        # --- Structured Snippets ---
        for i, sn in enumerate(extensions.snippets):
            if sn.header not in APPROVED_SNIPPET_HEADERS:
                errors.append(
                    f"Snippet[{i}] header '{sn.header}' not in approved list"
                )
            nv = len(sn.values)
            if nv < SNIPPET_VALUES_MIN:
                errors.append(
                    f"Snippet[{i}] '{sn.header}': need at least {SNIPPET_VALUES_MIN} values, got {nv}"
                )
            if nv > SNIPPET_VALUES_MAX:
                errors.append(
                    f"Snippet[{i}] '{sn.header}': max {SNIPPET_VALUES_MAX} values, got {nv}"
                )
            for j, val in enumerate(sn.values):
                if len(val) > SNIPPET_VALUE_MAX:
                    errors.append(
                        f"Snippet[{i}] '{sn.header}' value[{j}] too long "
                        f"({len(val)} > {SNIPPET_VALUE_MAX}): '{val}'"
                    )

        return errors

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_system_prompt(self) -> str:
        return (
            "You are a Google Ads specialist writing Search ad extensions "
            "for healthcare and mental health practices.\n\n"
            "SITELINK RULES:\n"
            "- link_text: max 25 chars. Must be a specific service name or "
            "action phrase (e.g. 'ADHD Testing', 'Book a Consultation'). "
            "Never use generic text like 'Learn More' or 'Click Here'.\n"
            "- description_1 and description_2: max 35 chars each. "
            "Be specific and benefit-driven.\n"
            "- Each sitelink must target a distinct page or service - "
            "never duplicate or all point to the homepage.\n"
            "- Generate between 6 and 8 sitelinks.\n\n"
            "CALLOUT RULES:\n"
            "- max 25 chars. Noun phrases ONLY.\n"
            "- NO verbs, NO punctuation, NO exclamation marks.\n"
            "- Good: 'Accepts Anthem BCBS', 'Online & In-Person', 'Same-Week Appts'\n"
            "- Bad: 'Schedule Today!', 'We Accept Insurance', 'Get Help Now'\n"
            "- Generate between 8 and 12 callouts.\n\n"
            "STRUCTURED SNIPPET RULES:\n"
            "- Use 'Services' or 'Types' as the header (Google-approved for healthcare).\n"
            "- Each value: max 25 chars.\n"
            "- Generate 1 snippet with 5 to 8 values.\n\n"
            "Return valid JSON only matching the schema provided."
        )

    def _build_user_prompt(self, ctx: ClientContext) -> str:
        services = ", ".join(ctx.services) if ctx.services else "general mental health"
        geo = ", ".join(ctx.geo) if ctx.geo else "local area"
        usps = ", ".join(ctx.USPs) if ctx.USPs else ""
        insurance = ", ".join(ctx.insurance_accepted) if ctx.insurance_accepted else ""

        parts = [
            f"Practice: {ctx.practice_name}",
            f"Type: {ctx.practice_type or 'mental health'}",
            f"Services: {services}",
            f"Locations: {geo}",
        ]
        if usps:
            parts.append(f"USPs: {usps}")
        if insurance:
            parts.append(f"Insurance accepted: {insurance}")
        if ctx.website_url:
            parts.append(f"Website: {ctx.website_url}")

        return (
            "Generate sitelinks, callouts, and structured snippets for this practice:\n\n"
            + "\n".join(parts)
        )

    def _parse(self, raw: dict) -> Extensions:
        """Convert raw LLM dict into typed dataclasses."""
        sitelinks = [
            Sitelink(
                link_text=str(sl.get("link_text", "")),
                description_1=str(sl.get("description_1", "")),
                description_2=str(sl.get("description_2", "")),
            )
            for sl in raw.get("sitelinks", [])
        ]
        callouts = [
            Callout(text=str(co.get("text", "")))
            for co in raw.get("callouts", [])
        ]
        snippets = [
            StructuredSnippet(
                header=str(sn.get("header", "Services")),
                values=[str(v) for v in sn.get("values", [])],
            )
            for sn in raw.get("snippets", [])
        ]
        return Extensions(sitelinks=sitelinks, callouts=callouts, snippets=snippets)

    def _repair(self, extensions: Extensions) -> Extensions:
        """
        Silently truncate fields that exceed character limits.
        Does not fix count violations - those require a new LLM call.
        """
        for sl in extensions.sitelinks:
            sl.link_text = sl.link_text[:SITELINK_LINK_TEXT_MAX]
            sl.description_1 = sl.description_1[:SITELINK_DESC_MAX]
            sl.description_2 = sl.description_2[:SITELINK_DESC_MAX]

        for co in extensions.callouts:
            co.text = co.text[:CALLOUT_TEXT_MAX].rstrip("!")

        for sn in extensions.snippets:
            sn.values = [v[:SNIPPET_VALUE_MAX] for v in sn.values[:SNIPPET_VALUES_MAX]]

        return extensions
