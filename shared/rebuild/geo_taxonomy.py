"""Shared Search campaign geo taxonomy planning."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable


KNOWN_STATES = {
    "new york": {"label": "NY", "name": "New York", "location": "New York, United States", "location_id": "21167"},
    "ny": {"label": "NY", "name": "New York", "location": "New York, United States", "location_id": "21167"},
    "new jersey": {"label": "NJ", "name": "New Jersey", "location": "New Jersey, United States", "location_id": "21164"},
    "nj": {"label": "NJ", "name": "New Jersey", "location": "New Jersey, United States", "location_id": "21164"},
}


@dataclass(frozen=True)
class GeoTarget:
    name: str
    location: str
    location_id: str = ""
    label: str = ""
    kind: str = "region"
    state_label: str = ""
    modifiers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GeoAdGroupPlan:
    campaign: str
    ad_group: str
    service: str
    final_url: str
    path_1: str
    path_2: str
    keywords: list[str]
    intent_tier: str
    geo_label: str = ""
    geo_name: str = ""
    location: GeoTarget | None = None


def parse_geo_target(value: str, location_id: str = "") -> GeoTarget:
    raw = value.strip()
    if "|" in raw:
        raw, parsed_id = raw.split("|", 1)
        location_id = location_id or parsed_id.strip()
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    lowered = raw.lower()
    for key, state in KNOWN_STATES.items():
        if lowered == key or lowered.startswith(f"{key},") or key in [part.lower() for part in parts]:
            is_state = parts and parts[0].lower() in {key, state["name"].lower(), state["label"].lower()}
            if is_state or len(parts) <= 2:
                return GeoTarget(
                    name=state["name"],
                    location=state["location"],
                    location_id=location_id or state["location_id"],
                    label=state["label"],
                    kind="state",
                    state_label=state["label"],
                    modifiers=(state["name"], state["label"]),
                )
            city = parts[0]
            return GeoTarget(
                name=city,
                location=raw,
                location_id=location_id,
                label=city,
                kind="city",
                state_label=state["label"],
                modifiers=tuple(unique([city, f"{city} {state['label']}", f"{city} {state['name']}"])),
            )
    return GeoTarget(name=parts[0] if parts else raw, location=raw, location_id=location_id, label=parts[0] if parts else raw)


def campaign_name_for_geo(base_campaign: str, target: GeoTarget, version_suffix: str) -> str:
    base = re.sub(r"\s+-\s+V\d+$", "", base_campaign).strip()
    base = re.sub(r"\s+-\s+(NY|NJ|REV\d+|V\d+)$", "", base).strip()
    if target.kind == "state":
        return f"{base} - {target.label} - {version_suffix}"
    return f"{base} - {version_suffix}"


def build_geo_ad_group_plans(
    *,
    base_campaign: str,
    services: list[str],
    locations: list[GeoTarget],
    final_url_for_service: Callable[[str], str],
    path_part: Callable[[str], str],
    version_suffix: str = "V1",
    split_by_state: bool = False,
    ad_group_prefix: str = "Services",
) -> list[GeoAdGroupPlan]:
    states = [target for target in locations if target.kind == "state"]
    cities = [target for target in locations if target.kind == "city"]
    state_split = split_by_state or len(states) > 1
    campaign_targets = states if state_split and states else [GeoTarget(name="", location="", label="", kind="general")]
    plans: list[GeoAdGroupPlan] = []
    for campaign_target in campaign_targets:
        campaign = campaign_name_for_geo(base_campaign, campaign_target, version_suffix) if state_split else base_campaign
        state_cities = [city for city in cities if not campaign_target.state_label or city.state_label == campaign_target.state_label]
        for service in services:
            final_url = final_url_for_service(service)
            plans.extend(
                [
                    geo_plan(campaign, service, final_url, path_part, ad_group_prefix, "General", base_keywords(service), "general"),
                    geo_plan(campaign, service, final_url, path_part, ad_group_prefix, "Near Me", near_me_keywords(service), "near_me"),
                ]
            )
            if campaign_target.kind == "state":
                plans.append(
                    geo_plan(
                        campaign,
                        service,
                        final_url,
                        path_part,
                        ad_group_prefix,
                        campaign_target.name,
                        state_keywords(service, campaign_target),
                        "state",
                        location=campaign_target,
                    )
                )
            for city in state_cities:
                plans.append(
                    geo_plan(
                        campaign,
                        service,
                        final_url,
                        path_part,
                        ad_group_prefix,
                        city.name,
                        city_keywords(service, city),
                        "city",
                        location=city,
                    )
                )
    return plans


def geo_plan(
    campaign: str,
    service: str,
    final_url: str,
    path_part: Callable[[str], str],
    prefix: str,
    suffix: str,
    keywords: list[str],
    tier: str,
    location: GeoTarget | None = None,
) -> GeoAdGroupPlan:
    return GeoAdGroupPlan(
        campaign=campaign,
        ad_group=f"{prefix} - {service[:50]} - {suffix}",
        service=service,
        final_url=final_url,
        path_1=path_part(service),
        path_2=path_part(suffix),
        keywords=keywords,
        intent_tier=tier,
        geo_label=location.label if location else "",
        geo_name=location.name if location else "",
        location=location,
    )


def base_keywords(service: str) -> list[str]:
    root = service.lower()
    return unique([root, f"{root} services", f"{root} consultation", f"{root} online"])


def near_me_keywords(service: str) -> list[str]:
    root = service.lower()
    return unique([f"{root} near me", f"local {root}", f"{root} nearby", f"{root} in my area"])


def state_keywords(service: str, state: GeoTarget) -> list[str]:
    root = service.lower()
    return unique([f"{root} in {state.name}", f"{state.name} {root}", f"{root} {state.label}", f"online {root} {state.name}"])


def city_keywords(service: str, city: GeoTarget) -> list[str]:
    root = service.lower()
    values: list[str] = []
    for modifier in city.modifiers:
        values.extend([f"{root} in {modifier}", f"{modifier} {root}", f"{root} near {modifier}"])
    return unique(values)


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        cleaned = re.sub(r"\s+", " ", value).strip()
        key = cleaned.lower()
        if cleaned and key not in seen:
            output.append(cleaned)
            seen.add(key)
    return output
