"""Client HQ source-of-truth parsing and extraction."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile


DOCX_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


@dataclass(frozen=True)
class ClientHQFacts:
    client_name: str = ""
    website: str = ""
    google_ads_account_id: str = ""
    monthly_budget: str = ""
    contacts: list[str] = field(default_factory=list)
    primary_services: list[str] = field(default_factory=list)
    landing_pages: list[str] = field(default_factory=list)
    service_area_regions: list[str] = field(default_factory=list)
    telehealth_regions: list[str] = field(default_factory=list)
    physical_locations: list[str] = field(default_factory=list)
    virtual_only: bool = False
    do_not_target: list[str] = field(default_factory=list)
    tracking: dict[str, str] = field(default_factory=dict)
    billing_notes: list[str] = field(default_factory=list)
    distance_review_policy: str = "Ask one grouped regional confirmation question when location coverage is unclear."
    capacity_notes: list[str] = field(default_factory=list)
    audience_notes: list[str] = field(default_factory=list)
    paused_services: list[str] = field(default_factory=list)
    future_service_launches: list[str] = field(default_factory=list)
    growth_goals: dict[str, object] = field(default_factory=dict)
    billing_questions: list[str] = field(default_factory=list)
    revision_facts: dict[str, object] = field(default_factory=dict)
    sections: dict[str, list[str]] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2) + "\n"


def extract_docx_lines(path: Path) -> list[str]:
    with ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ET.fromstring(xml)
    lines: list[str] = []
    for paragraph in root.findall(".//w:p", DOCX_NS):
        texts = [node.text for node in paragraph.findall(".//w:t", DOCX_NS) if node.text]
        text = normalize("".join(texts))
        if text:
            lines.append(text)
    return lines


def parse_client_hq_docx(path: Path) -> ClientHQFacts:
    lines = extract_docx_lines(path)
    text = "\n".join(lines)
    sections = sectionize(lines)
    name = client_name_from(path, lines)
    website = first_domain(text) or first_url(text)
    contacts = contact_lines(lines)
    services = services_for(name, lines)
    service_regions, telehealth_regions, physical_locations, virtual_only = delivery_facts_for(name, lines)
    tracking = tracking_facts(lines)
    facts = ClientHQFacts(
        client_name=name,
        website=website,
        google_ads_account_id=first_match(text, r"Google Ads Account ID:\s*([0-9-]+)") or first_match(text, r"Google Ad Account ID:\s*([0-9-]+)"),
        monthly_budget=budget_from(text),
        contacts=contacts,
        primary_services=services,
        landing_pages=urls_from(lines),
        service_area_regions=service_regions,
        telehealth_regions=telehealth_regions,
        physical_locations=physical_locations,
        virtual_only=virtual_only,
        do_not_target=do_not_target(lines),
        tracking=tracking,
        billing_notes=billing_notes(lines),
        sections=sections,
    )
    return facts


def write_client_hq_artifacts(source_docx: Path, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    facts = parse_client_hq_docx(source_docx)
    md_path = output_dir / "client_hq.md"
    json_path = output_dir / "client_hq.json"
    md_path.write_text(render_markdown(facts, source_docx.name), encoding="utf-8")
    json_path.write_text(facts.to_json(), encoding="utf-8")
    return {"markdown": md_path, "json": json_path}


def render_markdown(facts: ClientHQFacts, source_name: str) -> str:
    lines = [
        f"# Client HQ - {facts.client_name}",
        "",
        f"Source: `{source_name}`",
        "",
        "## Core Facts",
        "",
        f"- Website: {facts.website}",
        f"- Google Ads Account ID: {facts.google_ads_account_id or 'Not specified'}",
        f"- Monthly Budget: {facts.monthly_budget or 'Not specified'}",
        f"- Virtual Only: {'Yes' if facts.virtual_only else 'No'}",
        "",
        "## Physical Locations",
        "",
        *bullet_lines(facts.physical_locations),
        "",
        "## Service Areas",
        "",
        *bullet_lines(facts.service_area_regions),
        "",
        "## Telehealth Or Virtual Coverage",
        "",
        *bullet_lines(facts.telehealth_regions),
        "",
        "## Priority Services",
        "",
        *bullet_lines(facts.primary_services),
        "",
        "## Landing Pages",
        "",
        *bullet_lines(facts.landing_pages),
        "",
        "## Contacts",
        "",
        *bullet_lines(facts.contacts),
        "",
        "## Do Not Target",
        "",
        *bullet_lines(facts.do_not_target),
        "",
        "## Tracking",
        "",
        *[f"- {key}: {value}" for key, value in facts.tracking.items()],
        "",
        "## Billing Notes",
        "",
        *bullet_lines(facts.billing_notes),
        "",
        "## Revision Facts",
        "",
        *bullet_lines(revision_lines(facts)),
        "",
    ]
    return "\n".join(lines).replace("\u2014", "-") + "\n"


def bullet_lines(values: list[str]) -> list[str]:
    return [f"- {value}" for value in values] if values else ["- Not specified"]


def revision_lines(facts: ClientHQFacts) -> list[str]:
    lines: list[str] = []
    for label, values in (
        ("Capacity", facts.capacity_notes),
        ("Audience", facts.audience_notes),
        ("Paused services", facts.paused_services),
        ("Future launches", facts.future_service_launches),
        ("Billing questions", facts.billing_questions),
    ):
        for value in values:
            lines.append(f"{label}: {value}")
    if facts.growth_goals:
        lines.append(f"Growth goals: {json.dumps(facts.growth_goals, sort_keys=True)}")
    return lines


def sectionize(lines: list[str]) -> dict[str, list[str]]:
    headings = {
        "google ads",
        "target locations",
        "audience targeting & landing pages",
        "landing pages",
        "tracking",
        "billing",
        "point of contacts",
        "business information",
        "industry & services",
        "target areas",
        "do not target",
    }
    current = "overview"
    sections: dict[str, list[str]] = {current: []}
    for line in lines:
        key = normalize(line).lower()
        if key in headings:
            current = key
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def client_name_from(path: Path, lines: list[str]) -> str:
    for line in lines[:20]:
        match = re.search(r"(?:Company|Business|Practice|Client)\s+Name:\s*(.+)", line, flags=re.IGNORECASE)
        if match:
            return normalize(match.group(1))
    fallback = path.stem.replace("Client HQ - ", "")
    return normalize(fallback or (lines[0] if lines else ""))


def services_for(name: str, lines: list[str]) -> list[str]:
    values: list[str] = []
    for line in lines:
        lowered = line.lower()
        if lowered.startswith("priority "):
            values.append(line.split(":", 1)[-1].split("(")[0])
        elif any(label in lowered for label in ("primary services", "supplemental clinical services", "professional services")):
            values.extend(split_service_phrase(line.split(":", 1)[-1] if ":" in line else line))
        elif lowered.endswith("(priority focus)") or lowered in {"psychiatry", "adult therapy", "psychological testing"}:
            values.append(line.replace("(priority focus)", ""))
    return unique([*values, *inferred_services(lines)])


def delivery_facts_for(name: str, lines: list[str]) -> tuple[list[str], list[str], list[str], bool]:
    service_area_regions: list[str] = []
    telehealth_regions: list[str] = []
    physical_locations: list[str] = []
    mode = ""
    for line in lines:
        lowered = line.lower()
        if lowered in {"target locations", "target areas", "target locations (neighborhoods & cities)"}:
            mode = "targeting"
            continue
        if lowered in {"in-person", "physical locations"}:
            mode = "physical"
            continue
        if lowered in {"telehealth", "virtual coverage", "telehealth or virtual coverage"}:
            mode = "telehealth"
            continue
        if lowered in {"audience targeting & landing pages", "landing pages", "billing", "tracking", "google ads"}:
            mode = ""
        if lowered.startswith("state targets:"):
            telehealth_regions.extend(split_locations(line.split(":", 1)[-1]))
            continue
        if lowered.startswith(("immediate neighborhoods", "surrounding neighborhoods", "nearby cities")):
            service_area_regions.extend(split_locations(line.split(":", 1)[-1]))
            continue
        if "fully virtual" in lowered or "virtual only" in lowered:
            mode = "telehealth"
        if mode == "physical" and looks_like_location(line):
            physical_locations.append(line)
            service_area_regions.append(line)
        elif mode == "telehealth" and looks_like_location(line):
            telehealth_regions.extend(split_locations(line))
            service_area_regions.extend(split_locations(line))
        elif mode == "targeting" and looks_like_location(line):
            service_area_regions.extend(split_locations(line))

    virtual_only = any("fully virtual" in line.lower() or "virtual only" in line.lower() for line in lines) and not physical_locations
    return (unique(service_area_regions), unique(telehealth_regions), unique(physical_locations), virtual_only)


def inferred_services(lines: list[str]) -> list[str]:
    values = []
    for line in lines:
        if any(word in line.lower() for word in ("therapy", "testing", "consulting", "training", "counseling")):
            values.append(line[:120])
    return unique(values[:12])


def split_service_phrase(value: str) -> list[str]:
    value = re.sub(r"\s+(?:and|&)\s+", ",", value, flags=re.IGNORECASE)
    pieces = re.split(r",| {2,}", value)
    output: list[str] = []
    for piece in pieces:
        cleaned = normalize(piece)
        if cleaned:
            output.append(cleaned)
    return output


def split_locations(value: str) -> list[str]:
    cleaned = re.sub(r"\([^)]*\)", "", value)
    parts = re.split(r",|;|/| {2,}", cleaned)
    return [normalize(part) for part in parts if normalize(part)]


def looks_like_location(value: str) -> bool:
    lowered = value.lower()
    if not value or "http" in lowered or "@" in value:
        return False
    if re.fullmatch(r"\d{5}(?:-\d{4})?", value.strip()):
        return True
    location_words = {
        "state",
        "states",
        "city",
        "county",
        "area",
        "region",
        "neighborhood",
        "telehealth",
        "statewide",
        "countywide",
        "wide",
    }
    if any(word in lowered for word in location_words):
        return True
    if re.search(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}\b", value):
        return True
    return bool(re.fullmatch(r"[A-Z][A-Za-z'. -]+", value.strip()))


def urls_from(lines: list[str]) -> list[str]:
    urls = []
    for line in lines:
        urls.extend(re.findall(r"https?://[^\s)]+|(?:[a-z0-9-]+\.)+[a-z]{2,}/[^\s)]+", line, flags=re.IGNORECASE))
    return unique(urls)


def first_url(text: str) -> str:
    urls = re.findall(r"https?://[^\s)]+", text)
    return urls[0] if urls else ""


def first_domain(text: str) -> str:
    match = re.search(r"(?:www\.)?[a-z0-9-]+\.[a-z]{2,}(?:/[^\s)]*)?", text, flags=re.IGNORECASE)
    if not match:
        return ""
    domain = match.group(0).rstrip(".")
    return domain if domain.startswith("http") else f"https://{domain}"


def contact_lines(lines: list[str]) -> list[str]:
    return unique([line for line in lines if "@" in line][:20])


def tracking_facts(lines: list[str]) -> dict[str, str]:
    facts = {}
    for line in lines:
        for label in ("GTM Container", "GA4 Property ID", "GA4 Measurement ID", "CMS", "Booking System"):
            if line.startswith(label):
                facts[label] = line.split(":", 1)[-1].strip()
    return facts


def billing_notes(lines: list[str]) -> list[str]:
    return unique([line for line in lines if "Payment Method" in line or "Payments Account" in line or "Stripe test coupon" in line])


def do_not_target(lines: list[str]) -> list[str]:
    output = []
    capture = False
    for line in lines:
        lowered = line.lower()
        if lowered.startswith("do not target") or lowered.startswith("things to avoid"):
            capture = True
            output.append(line)
            continue
        if capture and (line.endswith(":") or lowered in {"billing", "tracking", "point of contacts"}):
            break
        if capture:
            output.append(line)
    return unique(output)


def budget_from(text: str) -> str:
    return first_match(text, r"Monthly Budget(?: for Google)?:\s*([^\n]+)") or first_match(text, r"\$[0-9,]+(?:/month)?")


def first_match(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return normalize(match.group(1)) if match else ""


def normalize(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip().replace("\u2014", "-")
    return cleaned.lstrip("•-* ").strip()


def unique(values: list[str]) -> list[str]:
    output = []
    seen = set()
    for value in values:
        text = normalize(value)
        key = text.lower()
        if text and key not in seen:
            output.append(text)
            seen.add(key)
    return output



def update_client_hq_media_inventory(
    client_root: Path,
    *,
    media_package_dir: Path,
    creative_manifest: dict[str, object],
    youtube_manifest: dict[str, object],
    youtube_account_discovery: dict[str, object],
    validation_report: dict[str, object],
) -> Path:
    """Merge the latest creative media package summary into Client HQ."""
    hq_dir = client_root / "docs" / "client_hq"
    hq_dir.mkdir(parents=True, exist_ok=True)
    json_path = hq_dir / "client_hq.json"
    payload: dict[str, object] = {}
    if json_path.exists():
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {"client_hq_parse_warning": "Existing client_hq.json was unreadable before media inventory update."}
    inventory = build_media_inventory_summary(
        client_root=client_root,
        media_package_dir=media_package_dir,
        creative_manifest=creative_manifest,
        youtube_manifest=youtube_manifest,
        youtube_account_discovery=youtube_account_discovery,
        validation_report=validation_report,
    )
    payload["media_inventory"] = inventory
    history = payload.get("media_inventory_history", [])
    if not isinstance(history, list):
        history = []
    history = [inventory, *history]
    payload["media_inventory_history"] = history[:10]
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return json_path


def build_media_inventory_summary(
    *,
    client_root: Path,
    media_package_dir: Path,
    creative_manifest: dict[str, object],
    youtube_manifest: dict[str, object],
    youtube_account_discovery: dict[str, object],
    validation_report: dict[str, object],
) -> dict[str, object]:
    assets = creative_manifest.get("assets", [])
    assets = assets if isinstance(assets, list) else []
    videos = youtube_manifest.get("videos", [])
    videos = videos if isinstance(videos, list) else []
    accounts = youtube_account_discovery.get("accounts", [])
    accounts = accounts if isinstance(accounts, list) else []
    issues = validation_report.get("issues", [])
    issues = issues if isinstance(issues, list) else []
    return {
        "latest_media_package": relative_to_client(client_root, media_package_dir),
        "image_assets": {
            "source_count": len(assets),
            "variant_count": sum(len(asset.get("variants", [])) for asset in assets if isinstance(asset, dict)),
            "generated_draft_count": sum(1 for asset in assets if isinstance(asset, dict) and asset.get("source_type") == "generated_draft"),
            "approved_count": sum(1 for asset in assets if isinstance(asset, dict) and asset.get("approval_status") == "approved"),
            "campaign_ready_count": sum(1 for asset in assets if isinstance(asset, dict) and asset.get("campaign_ready")),
            "approval_required": bool(creative_manifest.get("approval_required", True)),
        },
        "youtube": {
            "channel_url": youtube_manifest.get("youtube_channel_url", ""),
            "video_count": len(videos),
            "account_candidate_count": len(accounts),
            "readiness_status": youtube_account_discovery.get("readiness_status", "not_required"),
            "video_required": bool(youtube_account_discovery.get("video_required", False)),
            "campaign_ready_video_count": sum(1 for video in videos if isinstance(video, dict) and video.get("campaign_ready")),
            "campaign_ready_account_count": sum(1 for account in accounts if isinstance(account, dict) and account.get("campaign_ready")),
            "approval_required": bool(youtube_manifest.get("approval_required", True)),
        },
        "validation": {
            "status": validation_report.get("status", "unknown"),
            "blockers": [issue for issue in issues if isinstance(issue, dict) and issue.get("issue_type") in {"blocked_pending_client_video", "youtube_campaign_ready_without_approval", "youtube_campaign_ready_without_sync_confirmation", "youtube_campaign_ready_without_rights_confirmation", "unapproved_campaign_ready_asset"}],
        },
    }


def relative_to_client(client_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(client_root.resolve()))
    except ValueError:
        return path.name
