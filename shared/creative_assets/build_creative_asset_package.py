#!/usr/bin/env python3
"""Build a client approval package for Google Ads image and video creative."""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.rebuild.client_hq import update_client_hq_media_inventory
from shared.rebuild.scaffold_client import scaffold_client, slug
from shared.tools.website.website_scanner import WebsiteScanner


MAX_IMAGE_BYTES = 5 * 1024 * 1024
SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}
RISK_TERMS = {
    "button": "button_like_or_ui_element",
    "click": "button_like_or_ui_element",
    "guarantee": "unsupported_claim_review",
    "cure": "policy_or_claim_review",
    "before after": "before_after_claim_review",
    "sale": "offer_or_pricing_review",
    "discount": "offer_or_pricing_review",
}


@dataclass(frozen=True)
class AssetSpec:
    key: str
    label: str
    width: int
    height: int
    minimum_width: int
    minimum_height: int
    use: str


ASSET_SPECS = [
    AssetSpec("search_square", "Search image asset square", 1200, 1200, 300, 300, "Search image asset"),
    AssetSpec("search_landscape", "Search image asset landscape", 1200, 628, 600, 314, "Search image asset"),
    AssetSpec("display_landscape", "Responsive display landscape", 1200, 628, 600, 314, "Responsive display ad"),
    AssetSpec("display_square", "Responsive display square", 1200, 1200, 300, 300, "Responsive display ad"),
    AssetSpec("display_vertical", "Responsive display vertical", 900, 1600, 300, 533, "Responsive display ad"),
    AssetSpec("logo_square", "Logo square", 1200, 1200, 128, 128, "Logo asset"),
    AssetSpec("logo_landscape", "Logo landscape", 1200, 300, 512, 128, "Logo asset"),
]


@dataclass
class Candidate:
    source_url: str
    page_url: str
    source_type: str
    alt: str = ""
    page_title: str = ""
    headings: list[str] = field(default_factory=list)
    is_logo: bool = False
    local_original: str = ""
    original_width: int = 0
    original_height: int = 0
    original_bytes: int = 0
    score: int = 0
    status: str = "candidate"
    risk_flags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    perceptual_hash: str = ""


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def normalize_token_text(value: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", value.lower()) if len(token) >= 3]


def registered_root(hostname: str) -> str:
    parts = [part for part in hostname.lower().split(".") if part]
    if len(parts) <= 2:
        return hostname.lower()
    return ".".join(parts[-2:])


def is_first_party_url(url: str, website_url: str, allowed_domains: Iterable[str]) -> bool:
    parsed = urllib.parse.urlparse(url)
    site = urllib.parse.urlparse(website_url)
    if parsed.scheme == "file":
        return site.scheme == "file"
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or not site.hostname:
        return False
    image_host = parsed.hostname.lower()
    site_host = site.hostname.lower()
    allowed = {domain.lower() for domain in allowed_domains if domain}
    if image_host == site_host or image_host.endswith("." + site_host):
        return True
    if registered_root(image_host) == registered_root(site_host):
        return True
    return image_host in allowed or any(image_host.endswith("." + domain) for domain in allowed)


def srcset_candidates(srcset: str) -> list[tuple[str, int]]:
    urls: list[tuple[str, int]] = []
    for item in srcset.split(","):
        parts = item.strip().split()
        if parts:
            urls.append((parts[0], srcset_descriptor_width(parts)))
    return urls


def srcset_descriptor_width(parts: list[str]) -> int:
    for part in parts[1:]:
        if part.endswith("w") and part[:-1].isdigit():
            return int(part[:-1])
        if part.endswith("x"):
            try:
                return int(float(part[:-1]) * 1000)
            except ValueError:
                return 0
    parsed = urllib.parse.urlparse(parts[0])
    query = urllib.parse.parse_qs(parsed.query)
    for value in query.get("format", []):
        match = re.search(r"(\d+)w", value)
        if match:
            return int(match.group(1))
    return 0


def preferred_image_url(image: dict[str, str]) -> str:
    candidates = [(image.get("src", ""), 0), *srcset_candidates(image.get("srcset", ""))]
    candidates = [(url, width) for url, width in candidates if url]
    if not candidates:
        return ""
    return max(candidates, key=lambda item: item[1])[0]


def canonical_image_key(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    filtered = [(key, value) for key, value in query if key.lower() not in {"format", "width", "height"}]
    return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(filtered), fragment="")).lower()


def parse_youtube_video_id(value: str) -> str:
    if not value:
        return ""
    parsed = urllib.parse.urlparse(value.strip())
    host = (parsed.hostname or "").lower().removeprefix("www.")
    parts = [part for part in parsed.path.split("/") if part]
    if host == "youtu.be" and parts:
        return valid_youtube_video_id(parts[0])
    if host.endswith("youtube.com"):
        query_id = urllib.parse.parse_qs(parsed.query).get("v", [""])[0]
        if query_id:
            return valid_youtube_video_id(query_id)
        if len(parts) >= 2 and parts[0] in {"embed", "shorts", "live", "v"}:
            return valid_youtube_video_id(parts[1])
    match = re.search(r"(?:youtube\.com/(?:embed|shorts|live|v)/|youtu\.be/)([A-Za-z0-9_-]{11})", value)
    return valid_youtube_video_id(match.group(1)) if match else ""


def valid_youtube_video_id(value: str) -> str:
    return value if re.fullmatch(r"[A-Za-z0-9_-]{11}", value.strip()) else ""


def canonical_youtube_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def parse_youtube_channel_url(value: str) -> str:
    if not value:
        return ""
    parsed = urllib.parse.urlparse(value.strip())
    host = (parsed.hostname or "").lower().removeprefix("www.")
    parts = [part for part in parsed.path.split("/") if part]
    if not host.endswith("youtube.com") or not parts:
        return ""
    if parts[0].startswith("@"):
        return f"https://www.youtube.com/{parts[0]}"
    if len(parts) >= 2 and parts[0] in {"channel", "c", "user"}:
        identifier = re.sub(r"[^A-Za-z0-9_.@-]", "", parts[1])
        return f"https://www.youtube.com/{parts[0]}/{identifier}" if identifier else ""
    return ""


def find_youtube_urls(text: str) -> list[str]:
    pattern = re.compile(r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/[^\s\"'<>]+", re.IGNORECASE)
    return [match.group(0).rstrip(").,;") for match in pattern.finditer(text or "")]


def find_youtube_channel_urls(text: str) -> list[str]:
    urls = [channel for url in find_youtube_urls(text) if (channel := parse_youtube_channel_url(url))]
    seen = set()
    out = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def add_youtube_video(rows: list[dict[str, Any]], url: str, source_page: str, source_type: str, title: str) -> None:
    video_id = parse_youtube_video_id(url)
    if not video_id:
        return
    rows.append({"video_id": video_id, "title": title, "source_url": canonical_youtube_url(video_id), "source_page": source_page, "source_type": source_type, "proposed_google_use": "Google Ads YouTube video asset", "approval_status": "needs client approval", "sync_status": "needs Google Ads and YouTube link confirmation", "rights_status": "needs client rights confirmation", "campaign_ready": False, "notes": [], "risk_flags": []})


def extract_jsonld_youtube_videos(value: str, source_page: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return []
    rows: list[dict[str, Any]] = []
    def walk(node: Any, title: str = "") -> None:
        if isinstance(node, dict):
            next_title = str(node.get("name") or node.get("headline") or title)
            node_type = node.get("@type", "")
            types = node_type if isinstance(node_type, list) else [node_type]
            if any(str(item).lower() == "videoobject" for item in types):
                for key in ("url", "embedUrl", "contentUrl"):
                    if isinstance(node.get(key), str):
                        add_youtube_video(rows, node[key], source_page, "json_ld_video", next_title)
            for child in node.values():
                walk(child, next_title)
        elif isinstance(node, list):
            for child in node:
                walk(child, title)
    walk(payload)
    return rows


def collect_youtube_videos(raw_crawl: dict[str, Any], explicit_video_urls: list[str], channel_url: str, sync_status_path: Path | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for url in explicit_video_urls:
        add_youtube_video(rows, url, "operator supplied video URL", "operator_supplied_video", "")
    for page in raw_crawl.get("pages", []):
        page_url = page.get("url", "")
        page_title = page.get("title", "")
        for link in page.get("links", []):
            add_youtube_video(rows, link, page_url, "website_link", page_title)
        for embed in page.get("embeds", []):
            add_youtube_video(rows, embed.get("src", ""), page_url, "website_embed", embed.get("title", page_title))
        for url in find_youtube_urls(" ".join([page.get("text_sample", ""), json.dumps(page.get("links", []))])):
            add_youtube_video(rows, url, page_url, "website_text", page_title)
        for json_ld in page.get("json_ld", []):
            rows.extend(extract_jsonld_youtube_videos(json_ld, page_url))
    seen = set()
    out = []
    for row in rows:
        if row["video_id"] in seen:
            continue
        seen.add(row["video_id"])
        row["youtube_channel_url"] = channel_url
        row["thumbnail_url"] = f"https://i.ytimg.com/vi/{row['video_id']}/hqdefault.jpg"
        row["sync_evidence_path"] = str(sync_status_path) if sync_status_path else ""
        row["sync_evidence_status"] = "missing" if not sync_status_path else "provided"
        if not channel_url:
            row["risk_flags"].append("youtube_channel_url_not_provided")
        if row["sync_evidence_status"] == "missing":
            row["risk_flags"].append("youtube_sync_not_confirmed")
        out.append(row)
    return out


def add_youtube_account(rows: list[dict[str, Any]], url: str, source_page: str, source_type: str, title: str, confidence: str) -> None:
    channel_url = parse_youtube_channel_url(url)
    if not channel_url:
        return
    rows.append({"channel_url": channel_url, "title": title, "source_url": url, "source_page": source_page, "source_type": source_type, "confidence": confidence, "approval_status": "needs client approval", "google_ads_link_status": "not_checked", "rights_status": "needs client rights confirmation", "campaign_ready": False, "notes": [], "risk_flags": []})


def collect_youtube_accounts(raw_crawl: dict[str, Any], website_url: str, explicit_channel_urls: list[str], google_ads_evidence_path: Path | None, brand_aliases: list[str], known_social_profiles: list[str], enable_public_youtube_search: bool) -> list[dict[str, Any]]:
    del website_url, brand_aliases, google_ads_evidence_path, enable_public_youtube_search
    rows: list[dict[str, Any]] = []
    for url in explicit_channel_urls + known_social_profiles:
        add_youtube_account(rows, url, "operator supplied channel URL", "operator_supplied_channel", "", "needs_confirmation")
    for page in raw_crawl.get("pages", []):
        page_url = page.get("url", "")
        page_title = page.get("title", "")
        for link in page.get("links", []):
            add_youtube_account(rows, link, page_url, "website_link", page_title, "confirmed_from_client_site")
        for url in find_youtube_channel_urls(" ".join([page.get("text_sample", ""), json.dumps(page.get("links", []))])):
            add_youtube_account(rows, url, page_url, "website_text", page_title, "confirmed_from_client_site")
    seen = set()
    out = []
    for row in rows:
        if row["channel_url"] in seen:
            continue
        seen.add(row["channel_url"])
        if row["confidence"] == "needs_confirmation":
            row["risk_flags"].append("ownership_not_confirmed")
        if row["google_ads_link_status"] != "linked_confirmed":
            row["risk_flags"].append("youtube_link_not_confirmed")
        if row["rights_status"] != "rights_confirmed":
            row["risk_flags"].append("rights_not_confirmed")
        out.append(row)
    return out


def youtube_video_required(campaign_intents: list[str], require_video_assets: bool) -> bool:
    intents = {str(value).strip().lower().replace("-", "_") for value in campaign_intents}
    return require_video_assets or bool(intents & {"pmax", "performance_max", "demand_gen", "youtube", "youtube_video", "video"})


def youtube_readiness_status(video_rows: list[dict[str, Any]], account_rows: list[dict[str, Any]], required: bool) -> str:
    if not required:
        return "not_required"
    if video_rows:
        return "youtube_ready_for_approval"
    if account_rows:
        return "youtube_access_needed"
    return "youtube_not_located"


def validate_youtube(video_rows: list[dict[str, Any]], account_rows: list[dict[str, Any]], required: bool) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    campaign_ready = sum(1 for row in video_rows if row.get("campaign_ready"))
    status = youtube_readiness_status(video_rows, account_rows, required)
    if required and campaign_ready == 0:
        issues.append({"issue_type": "blocked_pending_client_video", "status": status})
    return {"status": status, "readiness_status": status, "issues": issues, "campaign_ready_videos": campaign_ready, "video_count": len(video_rows), "account_candidate_count": len(account_rows), "campaign_ready_accounts": 0, "video_required": required}


def write_youtube_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: "; ".join(row.get(field, [])) if isinstance(row.get(field), list) else row.get(field, "") for field in fields})


def write_account_discovery_md(path: Path, account_rows: list[dict[str, Any]], required: bool, status: str) -> None:
    lines = ["# YouTube Account Discovery", "", f"Video asset readiness status: `{status}`", f"Video required for this package: {'yes' if required else 'no'}", "", "## Candidate Channels", ""]
    lines.extend([f"- {row.get('channel_url')} | {row.get('confidence')} | {row.get('google_ads_link_status')} | {row.get('rights_status')}" for row in account_rows] or ["- No reliable YouTube channel candidates were found."])
    lines.extend(["", "## Client Follow-Up", "", "- Confirm the official YouTube channel URL.", "- Confirm who owns or can approve the channel.", "- Confirm Google Ads may link the channel or specific videos.", "- Confirm the client has rights to use each selected video in ads.", "- Confirm priority videos before Performance Max, Demand Gen, or YouTube campaigns use video assets."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def extract_jsonld_images(value: str) -> list[str]:
    urls: list[str] = []
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return urls

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if key.lower() == "image":
                    walk_image(child)
                else:
                    walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    def walk_image(node: Any) -> None:
        if isinstance(node, str):
            urls.append(node)
        elif isinstance(node, dict):
            for key in ("url", "contentUrl", "@id"):
                if isinstance(node.get(key), str):
                    urls.append(node[key])
            for child in node.values():
                walk_image(child)
        elif isinstance(node, list):
            for child in node:
                walk_image(child)

    walk(payload)
    return urls


def load_or_scan_website(
    *,
    website_url: str,
    website_scan_path: Path | None,
    raw_crawl_path: Path | None,
    output_dir: Path,
    landing_pages: list[str],
    service_theme: str,
    max_pages: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if website_scan_path:
        website_scan = read_json(website_scan_path)
        raw_crawl = read_json(raw_crawl_path) if raw_crawl_path and raw_crawl_path.exists() else {"pages": []}
        return website_scan, raw_crawl
    paths = WebsiteScanner().write_artifacts(
        start_url=website_url,
        output_dir=output_dir,
        source_pages=landing_pages,
        explicit_services=[service_theme] if service_theme else [],
        max_pages=max_pages,
    )
    return read_json(paths["website_scan"]), read_json(paths["raw_crawl"])


def candidate_rows(website_scan: dict[str, Any], raw_crawl: dict[str, Any], max_candidates: int = 80) -> list[Candidate]:
    candidates: list[Candidate] = []
    pages = raw_crawl.get("pages", [])
    for page in pages:
        page_url = page.get("url", "")
        page_title = page.get("title", "")
        headings = [str(value) for value in page.get("headings", [])]
        for image in page.get("images", []):
            image_url = preferred_image_url(image)
            if image_url:
                candidates.append(
                    Candidate(
                        source_url=image_url,
                        page_url=page_url,
                        source_type="srcset" if image.get("srcset") else "img",
                        alt=image.get("alt", ""),
                        page_title=page_title,
                        headings=headings,
                        is_logo=looks_like_logo(image),
                    )
                )
        for image in page.get("meta_images", []):
            candidates.append(
                Candidate(
                    source_url=image.get("src", ""),
                    page_url=page_url,
                    source_type=image.get("property", "meta_image"),
                    page_title=page_title,
                    headings=headings,
                )
            )
        for icon in page.get("icons", []):
            candidates.append(
                Candidate(
                    source_url=icon.get("src", ""),
                    page_url=page_url,
                    source_type="icon",
                    page_title=page_title,
                    headings=headings,
                    is_logo=True,
                )
            )
        for json_ld in page.get("json_ld", []):
            for image_url in extract_jsonld_images(json_ld):
                candidates.append(
                    Candidate(
                        source_url=image_url,
                        page_url=page_url,
                        source_type="json_ld_image",
                        page_title=page_title,
                        headings=headings,
                    )
                )

    asset_evidence = (
        website_scan.get("extracted_facts", {})
        .get("asset_evidence", {})
    )
    for image in asset_evidence.get("image_candidates", []):
        candidates.append(
            Candidate(
                source_url=image.get("url", ""),
                page_url=image.get("source", ""),
                source_type=image.get("evidence_type", "website_scan_image"),
                alt=image.get("alt", ""),
            )
        )
    for image in asset_evidence.get("logo_candidates", []):
        candidates.append(
            Candidate(
                source_url=image.get("url", ""),
                page_url=image.get("source", ""),
                source_type=image.get("evidence_type", "website_scan_logo"),
                alt=image.get("alt", ""),
                is_logo=True,
            )
        )

    seen: set[str] = set()
    output: list[Candidate] = []
    for candidate in candidates:
        key = canonical_image_key(candidate.source_url)
        if not candidate.source_url or key in seen:
            continue
        seen.add(key)
        output.append(candidate)
        if len(output) >= max_candidates:
            break
    return output


def looks_like_logo(image: dict[str, str]) -> bool:
    marker = " ".join(
        [
            image.get("src", ""),
            image.get("alt", ""),
            image.get("class", ""),
            image.get("id", ""),
        ]
    ).lower()
    return "logo" in marker or "brand" in marker or "icon" in marker


def safe_filename(url: str, index: int, extension: str = ".jpg") -> str:
    parsed = urllib.parse.urlparse(url)
    stem = Path(urllib.parse.unquote(parsed.path)).stem
    stem = re.sub(r"[^a-zA-Z0-9]+", "_", stem).strip("_").lower()[:48]
    if not stem:
        stem = f"image_{index:03d}"
    if not extension.startswith("."):
        extension = "." + extension
    return f"{index:03d}_{stem}{extension.lower()}"


def download_candidate(candidate: Candidate, output_path: Path, timeout: int = 20) -> None:
    parsed = urllib.parse.urlparse(candidate.source_url)
    if parsed.scheme == "file":
        source = Path(urllib.request.url2pathname(parsed.path))
        output_path.write_bytes(source.read_bytes())
        return
    request = urllib.request.Request(candidate.source_url, headers={"User-Agent": "Google_Ads_Agent creative asset tool"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        output_path.write_bytes(response.read())


def image_hash(image: Image.Image) -> str:
    small = ImageOps.grayscale(image.resize((8, 8)))
    values = list(image_pixels(small))
    average = sum(values) / len(values)
    return "".join("1" if value >= average else "0" for value in values)


def clarity_score(image: Image.Image) -> float:
    gray = ImageOps.grayscale(image.resize((160, 160)))
    edges = gray.filter(ImageFilter.FIND_EDGES)
    values = list(image_pixels(edges))
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance)


def image_pixels(image: Image.Image) -> Iterable[int]:
    pixel_reader = getattr(image, "get_flattened_data", None)
    if callable(pixel_reader):
        return pixel_reader()
    return image.getdata()


def text_density_risk(candidate: Candidate) -> bool:
    text = " ".join([candidate.alt, candidate.source_url]).lower()
    word_count = len(re.findall(r"[a-z]{3,}", text))
    return word_count >= 12 or any(term in text for term in ("infographic", "flyer", "poster", "coupon"))


def relevance_score(candidate: Candidate, service_theme: str, landing_pages: list[str]) -> int:
    haystack = " ".join(
        [
            candidate.alt,
            candidate.source_url,
            candidate.page_url,
            candidate.page_title,
            " ".join(candidate.headings),
        ]
    ).lower()
    terms = set(normalize_token_text(service_theme))
    for page in landing_pages:
        terms.update(normalize_token_text(page))
    if not terms:
        return 8
    hits = sum(1 for term in terms if term in haystack)
    return min(20, hits * 5)


def score_candidate(candidate: Candidate, image: Image.Image, service_theme: str, landing_pages: list[str]) -> None:
    width, height = image.size
    candidate.original_width = width
    candidate.original_height = height
    candidate.perceptual_hash = image_hash(image)
    score = 0
    flags: list[str] = []
    notes: list[str] = []
    if candidate.is_logo:
        if width >= 1200 and height >= 1200:
            score += 30
        elif width >= 1200 and height >= 300:
            score += 28
        elif width >= 512 and height >= 128:
            score += 22
        elif width >= 128 and height >= 128:
            score += 16
        else:
            flags.append("too_small_for_logo_assets")
    else:
        if width >= 1200 and height >= 628:
            score += 30
        elif width >= 600 and height >= 314:
            score += 22
        elif width >= 300 and height >= 300:
            score += 12
        else:
            flags.append("too_small_for_primary_google_assets")
    ratio = width / height if height else 0
    if 0.85 <= ratio <= 1.25 or 1.75 <= ratio <= 2.05 or 0.5 <= ratio <= 0.65 or (candidate.is_logo and 3.5 <= ratio <= 4.5):
        score += 18
    else:
        notes.append("aspect ratio needs crop or padding")
    clarity = clarity_score(image)
    if clarity >= 18:
        score += 18
    elif clarity >= 10:
        score += 8
        notes.append("moderate clarity")
    elif candidate.is_logo:
        score += 4
        notes.append("logo clarity needs manual review")
    else:
        flags.append("low_visual_clarity")
    score += relevance_score(candidate, service_theme, landing_pages)
    if candidate.is_logo:
        score += 8
    if text_density_risk(candidate):
        flags.append("possible_text_heavy_asset")
    risk_text = " ".join([candidate.alt, candidate.source_url, candidate.page_title, " ".join(candidate.headings)]).lower()
    for term, flag in RISK_TERMS.items():
        if term in risk_text and flag not in flags:
            flags.append(flag)
    candidate.score = min(100, score)
    candidate.risk_flags = flags
    candidate.notes = notes
    if "too_small_for_primary_google_assets" in flags or "too_small_for_logo_assets" in flags or "low_visual_clarity" in flags:
        candidate.status = "rejected"
    elif flags:
        candidate.status = "needs legal or client confirmation"
    else:
        candidate.status = "revise" if candidate.score < 55 else "candidate"


def crop_or_pad(image: Image.Image, spec: AssetSpec, is_logo: bool) -> Image.Image:
    image = ImageOps.exif_transpose(image).convert("RGBA")
    if is_logo or "logo" in spec.key:
        fitted = ImageOps.contain(image, (spec.width, spec.height))
        canvas = Image.new("RGBA", (spec.width, spec.height), (255, 255, 255, 255))
        offset = ((spec.width - fitted.width) // 2, (spec.height - fitted.height) // 2)
        canvas.alpha_composite(fitted, offset)
        return canvas.convert("RGB")
    source_ratio = image.width / image.height
    target_ratio = spec.width / spec.height
    if abs(source_ratio - target_ratio) <= 0.18:
        fitted = ImageOps.fit(image, (spec.width, spec.height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.45))
        return fitted.convert("RGB")
    background = ImageOps.fit(image, (spec.width, spec.height), method=Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(18))
    background = ImageEnhance.Brightness(background).enhance(0.88)
    foreground = ImageOps.contain(image, (spec.width, spec.height))
    background = background.convert("RGBA")
    offset = ((spec.width - foreground.width) // 2, (spec.height - foreground.height) // 2)
    background.alpha_composite(foreground, offset)
    return background.convert("RGB")


def enhance(image: Image.Image) -> Image.Image:
    image = ImageEnhance.Contrast(image).enhance(1.06)
    image = ImageEnhance.Sharpness(image).enhance(1.08)
    return image


def save_under_limit(image: Image.Image, path: Path) -> int:
    quality = 92
    while quality >= 72:
        image.save(path, format="JPEG", quality=quality, optimize=True)
        size = path.stat().st_size
        if size <= MAX_IMAGE_BYTES:
            return size
        quality -= 5
    return path.stat().st_size


def generated_draft(service_theme: str, brand_rules: str, spec: AssetSpec) -> Image.Image:
    base = Image.new("RGB", (spec.width, spec.height), (246, 248, 247))
    accent = (37, 86, 99)
    secondary = (219, 176, 88)
    draw = ImageDrawSafe(base)
    draw.rectangle((0, 0, spec.width, max(18, spec.height // 28)), fill=accent)
    draw.rectangle((0, spec.height - max(18, spec.height // 28), spec.width, spec.height), fill=secondary)
    label = "Generated draft"
    theme = service_theme[:48] or "Service creative"
    draw.center_text(label, y=spec.height // 2 - 36, size=max(22, spec.width // 38), fill=(57, 67, 72))
    draw.center_text(theme, y=spec.height // 2 + 8, size=max(28, spec.width // 28), fill=(26, 39, 45))
    if brand_rules:
        draw.center_text(brand_rules[:70], y=spec.height // 2 + 58, size=max(18, spec.width // 54), fill=(88, 95, 99))
    return base


class ImageDrawSafe:
    def __init__(self, image: Image.Image) -> None:
        from PIL import ImageDraw, ImageFont

        self.image = image
        self.draw = ImageDraw.Draw(image)
        self.font_module = ImageFont

    def rectangle(self, coords: tuple[int, int, int, int], fill: tuple[int, int, int]) -> None:
        self.draw.rectangle(coords, fill=fill)

    def center_text(self, text: str, *, y: int, size: int, fill: tuple[int, int, int]) -> None:
        font = self.font_module.load_default(size=size)
        bbox = self.draw.textbbox((0, 0), text, font=font)
        x = (self.image.width - (bbox[2] - bbox[0])) // 2
        self.draw.text((x, y), text, fill=fill, font=font)


def process_assets(
    *,
    candidates: list[Candidate],
    source_dir: Path,
    processed_dir: Path,
    website_url: str,
    service_theme: str,
    landing_pages: list[str],
    brand_rules: str,
    allowed_domains: list[str],
    minimum_approved_source_images: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    manifest_rows: list[dict[str, Any]] = []
    attribution_rows: list[dict[str, Any]] = []
    seen_hashes: dict[str, str] = {}
    usable_sources = 0

    for index, candidate in enumerate(candidates, start=1):
        if candidate.source_type != "logo_file" and not is_first_party_url(candidate.source_url, website_url, allowed_domains):
            candidate.status = "rejected"
            candidate.risk_flags.append("not_first_party_or_allowed_domain")
            manifest_rows.append(candidate_manifest_row(candidate, []))
            attribution_rows.append(attribution_row(candidate, [], generated=False))
            continue
        extension = Path(urllib.parse.urlparse(candidate.source_url).path).suffix or mimetypes.guess_extension("image/jpeg") or ".jpg"
        original_path = source_dir / safe_filename(candidate.source_url, index, extension)
        try:
            download_candidate(candidate, original_path)
            candidate.local_original = str(original_path)
            candidate.original_bytes = original_path.stat().st_size
            with Image.open(original_path) as opened:
                image = ImageOps.exif_transpose(opened).convert("RGB")
                if opened.format and opened.format not in SUPPORTED_FORMATS:
                    candidate.risk_flags.append("unsupported_source_format_needs_review")
                score_candidate(candidate, image, service_theme, landing_pages)
                if candidate.perceptual_hash in seen_hashes:
                    candidate.risk_flags.append("near_duplicate")
                    candidate.notes.append(f"Similar to {seen_hashes[candidate.perceptual_hash]}")
                    candidate.status = "revise"
                else:
                    seen_hashes[candidate.perceptual_hash] = original_path.name
                variants = []
                if candidate.status != "rejected":
                    usable_sources += 1
                    for spec in ASSET_SPECS:
                        if "logo" in spec.key and not candidate.is_logo:
                            continue
                        if "logo" not in spec.key and candidate.is_logo:
                            continue
                        variant = crop_or_pad(image, spec, candidate.is_logo)
                        variant = enhance(variant)
                        variant_path = processed_dir / f"{original_path.stem}_{spec.key}.jpg"
                        size = save_under_limit(variant, variant_path)
                        variants.append(
                            {
                                "asset_id": f"{original_path.stem}_{spec.key}",
                                "file": str(variant_path),
                                "proposed_google_use": spec.use,
                                "variant_label": spec.label,
                                "width": spec.width,
                                "height": spec.height,
                                "file_size": size,
                                "approval_status": "needs client approval",
                            }
                        )
                manifest_rows.append(candidate_manifest_row(candidate, variants))
                attribution_rows.append(attribution_row(candidate, variants, generated=False))
        except (OSError, urllib.error.URLError, UnidentifiedImageError, ValueError) as exc:
            candidate.status = "rejected"
            candidate.risk_flags.append("download_or_image_open_failed")
            candidate.notes.append(str(exc))
            manifest_rows.append(candidate_manifest_row(candidate, []))
            attribution_rows.append(attribution_row(candidate, [], generated=False))

    if usable_sources < minimum_approved_source_images:
        for spec in ASSET_SPECS:
            if "logo" in spec.key:
                continue
            draft = generated_draft(service_theme, brand_rules, spec)
            draft_path = processed_dir / f"generated_draft_{spec.key}.jpg"
            size = save_under_limit(draft, draft_path)
            row = {
                "source_url": "generated draft",
                "source_type": "generated_draft",
                "page_url": "",
                "alt": "",
                "is_logo": False,
                "original_width": spec.width,
                "original_height": spec.height,
                "original_bytes": size,
                "score": 0,
                "status": "needs legal or client confirmation",
                "approval_status": "needs client approval",
                "campaign_ready": False,
                "risk_flags": ["generated_draft", "requires_client_approval_before_campaign_use"],
                "notes": ["Generated fallback draft based on website facts and service theme."],
                "variants": [
                    {
                        "asset_id": f"generated_draft_{spec.key}",
                        "file": str(draft_path),
                        "proposed_google_use": spec.use,
                        "variant_label": spec.label,
                        "width": spec.width,
                        "height": spec.height,
                        "file_size": size,
                        "approval_status": "needs client approval",
                    }
                ],
            }
            manifest_rows.append(row)
            attribution_rows.append(
                {
                    "asset_id": f"generated_draft_{spec.key}",
                    "source_url": "generated draft",
                    "source_page": "",
                    "source_type": "generated_draft",
                    "used_for": [spec.use],
                    "approval_status": "needs client approval",
                    "source_note": "Generated draft. Not source-backed client facility, staff, certification, outcome, or offer.",
                }
            )
    return manifest_rows, attribution_rows


def candidate_manifest_row(candidate: Candidate, variants: list[dict[str, Any]]) -> dict[str, Any]:
    row = asdict(candidate)
    row["variants"] = variants
    row["approval_status"] = "needs client approval"
    row["campaign_ready"] = False
    return row


def attribution_row(candidate: Candidate, variants: list[dict[str, Any]], *, generated: bool) -> dict[str, Any]:
    return {
        "asset_id": [variant["asset_id"] for variant in variants],
        "source_url": candidate.source_url,
        "source_page": candidate.page_url,
        "source_type": "generated_draft" if generated else candidate.source_type,
        "used_for": [variant["proposed_google_use"] for variant in variants],
        "approval_status": "needs client approval",
        "source_note": "Generated draft." if generated else "First-party website image candidate.",
    }


def write_review_csv(path: Path, manifest_rows: list[dict[str, Any]]) -> None:
    fields = [
        "asset_id",
        "file",
        "source_url",
        "proposed_google_use",
        "dimensions",
        "file_size",
        "approval_status",
        "notes",
        "risk_flags",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in manifest_rows:
            variants = row.get("variants") or [{}]
            for variant in variants:
                writer.writerow(
                    {
                        "asset_id": variant.get("asset_id", ""),
                        "file": variant.get("file", ""),
                        "source_url": row.get("source_url", ""),
                        "proposed_google_use": variant.get("proposed_google_use", ""),
                        "dimensions": f"{variant.get('width', row.get('original_width', ''))}x{variant.get('height', row.get('original_height', ''))}",
                        "file_size": variant.get("file_size", row.get("original_bytes", "")),
                        "approval_status": row.get("approval_status", "needs client approval"),
                        "notes": "; ".join(row.get("notes", [])),
                        "risk_flags": "; ".join(row.get("risk_flags", [])),
                    }
                )


def write_youtube_sync_checklist(path: Path, video_rows: list[dict[str, Any]], channel_url: str, account_rows: list[dict[str, Any]]) -> None:
    lines = ["# YouTube And Google Ads Sync Checklist", "", f"YouTube channel URL: {channel_url or 'Needs confirmation'}", "", "## Required Before Campaign Use", "", "- Confirm the Google Ads account has administrative access before requesting a YouTube channel or video link.", "- Confirm the YouTube channel owner has approved the channel or video link request.", "- Confirm the client has sufficient rights to use each video in ads.", "- Record the link status and rights status in `youtube_video_review.csv` before any video is staged for campaigns.", "", "## Account Review", ""]
    lines.extend([f"- {row.get('channel_url')} | {row.get('confidence')} | {row.get('google_ads_link_status')} | {row.get('rights_status')}" for row in account_rows] or ["- No YouTube channel candidates were confirmed."])
    lines.extend(["", "## Video Review", ""])
    lines.extend([f"- `{row.get('video_id')}` | {row.get('title') or 'Untitled video'} | {row.get('approval_status')} | {row.get('sync_status')} | {row.get('rights_status')}" for row in video_rows] or ["- No YouTube video candidates were found."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def relative_asset_path(asset_file: str, html_path: Path) -> str:
    return Path(os.path.relpath(Path(asset_file).resolve(), html_path.parent.resolve())).as_posix()


def write_html_gallery(path: Path, manifest_rows: list[dict[str, Any]], client: str, service_theme: str, youtube_rows: list[dict[str, Any]] | None = None, youtube_account_rows: list[dict[str, Any]] | None = None, youtube_status: str = "not_required") -> None:
    cards: list[str] = []
    for row in manifest_rows:
        for variant in row.get("variants", []):
            src = html.escape(relative_asset_path(variant["file"], path))
            risks = ", ".join(row.get("risk_flags", [])) or "None"
            notes = "; ".join(row.get("notes", []))
            cards.append(
                f"""
      <article class="asset-card">
        <img src="{src}" alt="{html.escape(variant['variant_label'])}">
        <div class="asset-meta">
          <h2>{html.escape(variant['variant_label'])}</h2>
          <p><strong>Use:</strong> {html.escape(variant['proposed_google_use'])}</p>
          <p><strong>Source:</strong> {html.escape(row.get('source_url', ''))}</p>
          <p><strong>Dimensions:</strong> {variant['width']}x{variant['height']}</p>
          <p><strong>File size:</strong> {variant['file_size']} bytes</p>
          <p><strong>Status:</strong> {html.escape(row.get('approval_status', 'needs client approval'))}</p>
          <p><strong>Risk flags:</strong> {html.escape(risks)}</p>
          <label><input type="checkbox"> Approved for campaign use</label>
          <label>Notes <textarea></textarea></label>
          <p class="notes">{html.escape(notes)}</p>
        </div>
      </article>"""
            )
    body = "\n".join(cards) or "<p>No usable image candidates were generated.</p>"
    account_cards = "".join(f"<article class=\"asset-card\"><div class=\"asset-meta\"><h2>YouTube channel candidate</h2><p><strong>Channel:</strong> {html.escape(row.get('channel_url', ''))}</p><p><strong>Package status:</strong> {html.escape(youtube_status)}</p><label><input type=\"checkbox\"> Confirmed for campaign use</label><label>Notes <textarea></textarea></label></div></article>" for row in (youtube_account_rows or [])) or f"<p>YouTube account status: {html.escape(youtube_status)}. No reliable channel candidates were found.</p>"
    video_cards = "".join(f"<article class=\"asset-card\"><iframe src=\"https://www.youtube.com/embed/{html.escape(row.get('video_id', ''))}\" title=\"YouTube video candidate\" loading=\"lazy\"></iframe><div class=\"asset-meta\"><h2>YouTube video candidate</h2><p><strong>Video ID:</strong> {html.escape(row.get('video_id', ''))}</p><p><strong>Source:</strong> {html.escape(row.get('source_url', ''))}</p><label><input type=\"checkbox\"> Approved for campaign use</label><label>Notes <textarea></textarea></label></div></article>" for row in (youtube_rows or [])) or "<p>No YouTube video candidates were found.</p>"
    path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Client Creative Approval</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; color: #1d2529; background: #f6f8f7; }}
    header {{ padding: 32px 40px; background: #173f4f; color: white; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 28px; }}
    .asset-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 18px; }}
    .asset-card {{ background: white; border: 1px solid #d8dfdc; border-radius: 8px; overflow: hidden; }}
    .asset-card img {{ width: 100%; aspect-ratio: 1.91 / 1; object-fit: contain; background: #eef2f0; display: block; }}
    .asset-card iframe {{ width: 100%; aspect-ratio: 16 / 9; border: 0; background: #eef2f0; display: block; }}
    .asset-meta {{ padding: 16px; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; }}
    h2 {{ margin: 0 0 12px; font-size: 18px; }}
    p {{ margin: 7px 0; font-size: 14px; }}
    label {{ display: block; margin-top: 12px; font-size: 14px; }}
    textarea {{ width: 100%; min-height: 60px; margin-top: 6px; }}
    .notes {{ color: #5c676b; }}
  </style>
</head>
<body>
  <header>
    <h1>Client Creative Approval</h1>
    <p>{html.escape(client)} | {html.escape(service_theme)} | Approval required before campaign use</p>
  </header>
  <main>
    <h2>Image Creative</h2>
    <section class="asset-grid">
{body}
    </section>
    <h2>YouTube Account And Video Readiness</h2>
    <section class="asset-grid">
{account_cards}
    </section>
    <h2>YouTube Videos</h2>
    <section class="asset-grid">
{video_cards}
    </section>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )


def write_email(path: Path, client: str, service_theme: str, html_path: Path, csv_path: Path, youtube_status: str = "not_required", video_required: bool = False) -> None:
    youtube_lines = []
    if video_required and youtube_status != "youtube_ready_for_approval":
        youtube_lines = ["", "For the video portion of this package, we still need YouTube confirmation before videos can be used in Performance Max, Demand Gen, or YouTube campaigns.", "Please send the official YouTube channel URL, the person who can approve channel or video linking, confirmation that videos may be used in ads, and any priority videos you want reviewed first."]
    path.write_text(
        "\n".join(
            [
                f"Subject: Creative asset approval requested for {client}",
                "",
                f"Hi {client},",
                "",
                f"We prepared image and YouTube creative candidates for the {service_theme} campaign theme.",
                "Please review the approval gallery and mark each asset as approved, revise, rejected, or needs legal or client confirmation.",
                *youtube_lines,
                "",
                "Nothing in this package will be used in campaigns until approval is returned.",
                "",
                f"Approval gallery: {html_path.name}",
                f"Review spreadsheet: {csv_path.name}",
                "",
                "Thank you.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def validate_package(manifest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    filenames: set[str] = set()
    approved = 0
    for row in manifest_rows:
        if row.get("campaign_ready"):
            issues.append({"issue_type": "unapproved_campaign_ready_asset", "asset": row.get("source_url", "")})
        if row.get("approval_status") == "approved":
            approved += 1
        if not row.get("source_url"):
            issues.append({"issue_type": "missing_source_attribution", "asset": row.get("source_url", "")})
        for variant in row.get("variants", []):
            path = Path(variant["file"])
            if path.name in filenames:
                issues.append({"issue_type": "duplicate_filename", "asset": path.name})
            filenames.add(path.name)
            if not path.exists():
                issues.append({"issue_type": "missing_processed_file", "asset": str(path)})
                continue
            if path.stat().st_size > MAX_IMAGE_BYTES:
                issues.append({"issue_type": "file_size_over_limit", "asset": str(path)})
            with Image.open(path) as image:
                if image.size != (variant["width"], variant["height"]):
                    issues.append({"issue_type": "dimension_mismatch", "asset": str(path)})
                if image.format not in SUPPORTED_FORMATS:
                    issues.append({"issue_type": "unsupported_format", "asset": str(path)})
    return {
        "status": "fail" if issues else "pass",
        "issues": issues,
        "approved_assets": approved,
        "campaign_ready_assets": 0,
        "asset_count": sum(len(row.get("variants", [])) for row in manifest_rows),
    }


def ensure_client_dir(agency: str, client: str, display_name: str, website: str, clients_dir: Path) -> Path:
    target = clients_dir / slug(agency) / slug(client)
    if target.exists():
        return target
    return scaffold_client(agency, client, display_name, website, clients_dir=clients_dir)


def build_creative_asset_package(args: argparse.Namespace) -> dict[str, Path]:
    run_date = args.build_date or date.today().isoformat()
    client_dir = args.client_dir or ensure_client_dir(
        args.agency,
        args.client,
        args.display_name or args.client,
        args.website,
        args.clients_dir,
    )
    client_dir.mkdir(parents=True, exist_ok=True)
    build_dir = args.output_build_path or client_dir / "media" / f"{run_date}_creative_assets"
    source_dir = build_dir / "source_images"
    processed_dir = build_dir / "processed_images"
    build_dir.mkdir(parents=True, exist_ok=True)

    website_scan, raw_crawl = load_or_scan_website(
        website_url=args.website,
        website_scan_path=args.website_scan_json,
        raw_crawl_path=args.raw_crawl_json,
        output_dir=build_dir,
        landing_pages=args.landing_page,
        service_theme=args.service_theme,
        max_pages=args.max_pages,
    )
    candidates = candidate_rows(website_scan, raw_crawl, max_candidates=args.max_candidates)
    for logo_file in args.logo_file:
        logo_path = Path(logo_file)
        candidates.append(
            Candidate(
                source_url=logo_path.resolve().as_uri(),
                page_url="operator supplied logo file",
                source_type="logo_file",
                alt="operator supplied logo",
                is_logo=True,
            )
        )
    manifest_rows, attribution_rows = process_assets(
        candidates=candidates,
        source_dir=source_dir,
        processed_dir=processed_dir,
        website_url=args.website,
        service_theme=args.service_theme,
        landing_pages=args.landing_page,
        brand_rules=args.brand_rules or "",
        allowed_domains=args.first_party_cdn_domain,
        minimum_approved_source_images=args.minimum_source_images,
    )

    video_is_required = youtube_video_required(getattr(args, "campaign_intent", []), getattr(args, "require_video_assets", False))
    channel_urls = [url for url in [getattr(args, "youtube_channel_url", "")] if url]
    channel_urls.extend(getattr(args, "youtube_channel_urls", []) or [])
    account_rows = collect_youtube_accounts(raw_crawl, args.website, channel_urls, getattr(args, "google_ads_evidence", None), getattr(args, "brand_alias", []), getattr(args, "known_social_profile", []), getattr(args, "enable_public_youtube_search", False))
    primary_channel = channel_urls[0] if channel_urls else next((row.get("channel_url", "") for row in account_rows), "")
    youtube_rows = collect_youtube_videos(raw_crawl, getattr(args, "youtube_video_url", []), primary_channel, getattr(args, "youtube_sync_status", None))
    youtube_validation = validate_youtube(youtube_rows, account_rows, video_is_required)
    youtube_status = youtube_readiness_status(youtube_rows, account_rows, video_is_required)

    manifest_path = build_dir / "creative_asset_manifest.json"
    review_csv = build_dir / "creative_asset_review.csv"
    youtube_manifest_path = build_dir / "youtube_video_manifest.json"
    youtube_review_csv = build_dir / "youtube_video_review.csv"
    youtube_account_manifest = build_dir / "youtube_account_discovery.json"
    youtube_account_review_csv = build_dir / "youtube_account_review.csv"
    youtube_account_discovery_md = build_dir / "youtube_account_discovery.md"
    youtube_sync_checklist = build_dir / "youtube_sync_checklist.md"
    html_path = build_dir / "Client_Creative_Approval.html"
    email_path = build_dir / "client_email_draft.md"
    attribution_path = build_dir / "creative_source_attribution.json"
    validation_path = build_dir / "validation_report.json"

    write_json(manifest_path, {"approval_required": True, "campaign_ready": False, "assets": manifest_rows})
    write_review_csv(review_csv, manifest_rows)
    write_json(youtube_manifest_path, {"approval_required": True, "campaign_ready": False, "youtube_channel_url": primary_channel, "videos": youtube_rows})
    write_youtube_csv(youtube_review_csv, youtube_rows, ["video_id", "title", "source_url", "source_page", "proposed_google_use", "approval_status", "sync_status", "rights_status", "campaign_ready", "notes", "risk_flags"])
    write_json(youtube_account_manifest, {"approval_required": True, "campaign_ready": False, "video_required": video_is_required, "readiness_status": youtube_status, "accounts": account_rows})
    write_youtube_csv(youtube_account_review_csv, account_rows, ["channel_url", "title", "source_url", "source_page", "source_type", "confidence", "approval_status", "google_ads_link_status", "rights_status", "campaign_ready", "notes", "risk_flags"])
    write_account_discovery_md(youtube_account_discovery_md, account_rows, video_is_required, youtube_status)
    write_youtube_sync_checklist(youtube_sync_checklist, youtube_rows, primary_channel, account_rows)
    write_html_gallery(html_path, manifest_rows, args.display_name or args.client, args.service_theme, youtube_rows, account_rows, youtube_status)
    write_email(email_path, args.display_name or args.client, args.service_theme, html_path, review_csv, youtube_status, video_is_required)
    write_json(attribution_path, {"website": args.website, "assets": attribution_rows})
    image_validation = validate_package(manifest_rows)
    issues = [*image_validation["issues"], *youtube_validation["issues"]]
    validation_report = {"status": "blocked_pending_client_video" if video_is_required and youtube_validation["campaign_ready_videos"] == 0 else image_validation["status"], "issues": issues, "image_assets": image_validation, "youtube_videos": youtube_validation, "approved_assets": image_validation["approved_assets"], "campaign_ready_assets": image_validation["campaign_ready_assets"], "asset_count": image_validation["asset_count"]}
    write_json(validation_path, validation_report)
    client_hq_media_inventory = update_client_hq_media_inventory(
        client_dir,
        media_package_dir=build_dir,
        creative_manifest={"approval_required": True, "campaign_ready": False, "assets": manifest_rows},
        youtube_manifest={"approval_required": True, "campaign_ready": False, "youtube_channel_url": primary_channel, "videos": youtube_rows},
        youtube_account_discovery={"approval_required": True, "campaign_ready": False, "video_required": video_is_required, "readiness_status": youtube_status, "accounts": account_rows},
        validation_report=validation_report,
    )

    return {
        "source_image_folder": source_dir,
        "processed_image_folder": processed_dir,
        "creative_asset_manifest": manifest_path,
        "creative_asset_review": review_csv,
        "youtube_video_manifest": youtube_manifest_path,
        "youtube_video_review": youtube_review_csv,
        "youtube_account_discovery": youtube_account_manifest,
        "youtube_account_review": youtube_account_review_csv,
        "youtube_account_discovery_md": youtube_account_discovery_md,
        "youtube_sync_checklist": youtube_sync_checklist,
        "client_hq_media_inventory": client_hq_media_inventory,
        "client_creative_approval_html": html_path,
        "client_email_draft": email_path,
        "creative_source_attribution": attribution_path,
        "validation_report": validation_path,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a Google Ads creative asset approval package.")
    parser.add_argument("--agency", required=True)
    parser.add_argument("--client", required=True)
    parser.add_argument("--display-name")
    parser.add_argument("--website", required=True)
    parser.add_argument("--website-scan-json", type=Path)
    parser.add_argument("--raw-crawl-json", type=Path)
    parser.add_argument("--service-theme", required=True)
    parser.add_argument("--landing-page", action="append", default=[])
    parser.add_argument("--brand-rules", default="")
    parser.add_argument("--logo-file", action="append", default=[])
    parser.add_argument("--youtube-channel-url", default="")
    parser.add_argument("--youtube-channel-urls", action="append", default=[])
    parser.add_argument("--youtube-video-url", action="append", default=[])
    parser.add_argument("--youtube-sync-status", type=Path)
    parser.add_argument("--google-ads-evidence", type=Path)
    parser.add_argument("--brand-alias", action="append", default=[])
    parser.add_argument("--known-social-profile", action="append", default=[])
    parser.add_argument("--campaign-intent", action="append", default=[])
    parser.add_argument("--require-video-assets", action="store_true")
    parser.add_argument("--enable-public-youtube-search", action="store_true")
    parser.add_argument("--output-build-path", type=Path)
    parser.add_argument("--client-dir", type=Path, help="Existing client folder to use instead of scaffolding clients/{agency}/{client}.")
    parser.add_argument("--clients-dir", type=Path, default=ROOT / "clients")
    parser.add_argument("--build-date")
    parser.add_argument("--max-pages", type=int, default=12)
    parser.add_argument("--max-candidates", type=int, default=24)
    parser.add_argument("--minimum-source-images", type=int, default=3)
    parser.add_argument("--first-party-cdn-domain", action="append", default=[])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    artifacts = build_creative_asset_package(args)
    print(json.dumps({key: str(path) for key, path in artifacts.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
