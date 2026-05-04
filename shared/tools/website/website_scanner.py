#!/usr/bin/env python3
"""Generic website scanner for initial campaign builds."""

from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


SERVICE_HINTS = (
    "therapy",
    "counseling",
    "consulting",
    "service",
    "services",
    "repair",
    "installation",
    "restoration",
    "coaching",
    "treatment",
    "assessment",
    "testing",
    "support",
)

CTA_PATTERNS = {
    "Call Today": re.compile(r"\b(call|phone|speak)\b", re.IGNORECASE),
    "Book Today": re.compile(r"\b(book|appointment|schedule)\b", re.IGNORECASE),
    "Request Details": re.compile(r"\b(request|contact|details|learn more)\b", re.IGNORECASE),
    "Apply Today": re.compile(r"\b(apply|application|get started)\b", re.IGNORECASE),
    "Schedule Today": re.compile(r"\b(schedule|appointment|consultation|consult)\b", re.IGNORECASE),
}
DELIVERY_PATTERNS = {
    "virtual": re.compile(r"\b(virtual|online|telehealth|remote)\b", re.IGNORECASE),
    "in_person": re.compile(r"\b(in-person|in person|office visit|on-site|onsite|at our office)\b", re.IGNORECASE),
    "24_7": re.compile(r"\b(24/7|24 hours|after hours|answering service)\b", re.IGNORECASE),
}
VALUE_PROP_PATTERNS = (
    re.compile(r"\b(licensed|experienced|trusted|local|private|available|comprehensive|focused)\b[^.]{0,90}", re.IGNORECASE),
    re.compile(r"\b(clear|practical|personalized|support|guidance|next steps|options)\b[^.]{0,90}", re.IGNORECASE),
)


@dataclass
class PageScan:
    url: str
    title: str
    headings: list[str]
    links: list[str]
    tel_links: list[str]
    images: list[dict[str, str]]
    icons: list[dict[str, str]]
    meta_images: list[dict[str, str]]
    json_ld: list[str]
    text_sample: str
    error: str | None = None


class LinkAndTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.tel_links: list[str] = []
        self.images: list[dict[str, str]] = []
        self.icons: list[dict[str, str]] = []
        self.meta_images: list[dict[str, str]] = []
        self.json_ld: list[str] = []
        self.title_parts: list[str] = []
        self.headings: list[str] = []
        self.text_parts: list[str] = []
        self._tag_stack: list[str] = []
        self._json_ld_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._tag_stack.append(tag)
        attr_map = {key.lower(): value or "" for key, value in attrs}
        if tag == "a":
            href = attr_map.get("href")
            if href:
                if href.lower().startswith("tel:"):
                    self.tel_links.append(href)
                else:
                    self.links.append(href)
        elif tag == "img":
            src = attr_map.get("src")
            if src:
                self.images.append(
                    {
                        "src": src,
                        "srcset": attr_map.get("srcset", ""),
                        "alt": attr_map.get("alt", ""),
                        "width": attr_map.get("width", ""),
                        "height": attr_map.get("height", ""),
                        "class": attr_map.get("class", ""),
                        "id": attr_map.get("id", ""),
                    }
                )
        elif tag == "link":
            href = attr_map.get("href")
            rel = attr_map.get("rel", "").lower()
            if href and any(value in rel for value in ("icon", "apple-touch-icon", "shortcut icon")):
                self.icons.append({"src": href, "rel": rel})
        elif tag == "meta":
            content = attr_map.get("content")
            prop = attr_map.get("property", attr_map.get("name", "")).lower()
            if content and prop in {"og:image", "twitter:image", "image"}:
                self.meta_images.append({"src": content, "property": prop})
        elif tag == "script" and attr_map.get("type", "").lower() == "application/ld+json":
            self._json_ld_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._json_ld_depth:
            self._json_ld_depth -= 1
        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()

    def handle_data(self, data: str) -> None:
        text = normalize_text(data)
        if not text:
            return
        if self._json_ld_depth:
            self.json_ld.append(data.strip())
            return
        current_tag = self._tag_stack[-1] if self._tag_stack else ""
        if current_tag == "title":
            self.title_parts.append(text)
        elif current_tag in {"h1", "h2", "h3"}:
            self.headings.append(text)
        if current_tag not in {"script", "style"}:
            self.text_parts.append(text)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_url(url: str, base_url: str) -> str:
    absolute = urllib.parse.urljoin(base_url, url)
    parsed = urllib.parse.urlparse(absolute)
    if parsed.scheme not in {"http", "https", "file"}:
        return ""
    return urllib.parse.urlunparse(parsed._replace(fragment=""))


def same_site(url: str, start_url: str) -> bool:
    parsed_url = urllib.parse.urlparse(url)
    parsed_start = urllib.parse.urlparse(start_url)
    if parsed_start.scheme == "file":
        return parsed_url.scheme == "file"
    return parsed_url.netloc == parsed_start.netloc


def read_url(url: str, timeout: int = 12) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme == "file":
        return Path(urllib.request.url2pathname(parsed.path)).read_text(encoding="utf-8")
    request = urllib.request.Request(url, headers={"User-Agent": "Google_Ads_Agent website scanner"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def parse_page(url: str, html: str) -> PageScan:
    parser = LinkAndTextParser()
    parser.feed(html)
    links = [normalize_url(link, url) for link in parser.links]
    links = sorted({link for link in links if link})
    tel_links = sorted({link for link in parser.tel_links if link})
    images = [
        {
            **image,
            "src": normalize_url(image.get("src", ""), url),
            "srcset": normalize_srcset(image.get("srcset", ""), url),
        }
        for image in parser.images
    ]
    icons = [
        {
            **icon,
            "src": normalize_url(icon.get("src", ""), url),
        }
        for icon in parser.icons
    ]
    meta_images = [
        {
            **image,
            "src": normalize_url(image.get("src", ""), url),
        }
        for image in parser.meta_images
    ]
    text = normalize_text(" ".join(parser.text_parts))
    return PageScan(
        url=url,
        title=normalize_text(" ".join(parser.title_parts)),
        headings=parser.headings[:24],
        links=links,
        tel_links=tel_links,
        images=[image for image in images if image["src"]],
        icons=[icon for icon in icons if icon["src"]],
        meta_images=[image for image in meta_images if image["src"]],
        json_ld=parser.json_ld,
        text_sample=text[:4000],
    )


def candidate_service_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    slug = parsed.path.strip("/").split("/")[-1]
    if not slug:
        return ""
    slug = re.sub(r"\.(html?|php|aspx?)$", "", slug, flags=re.IGNORECASE)
    words = [word for word in re.split(r"[-_]+", slug) if word and not word.isdigit()]
    if not any(word.lower() in SERVICE_HINTS for word in words):
        return ""
    return " ".join(word.title() for word in words)


def normalize_srcset(srcset: str, base_url: str) -> str:
    if not srcset:
        return ""
    candidates: list[str] = []
    for item in srcset.split(","):
        parts = item.strip().split()
        if not parts:
            continue
        resolved = normalize_url(parts[0], base_url)
        if resolved:
            descriptor = " ".join(parts[1:])
            candidates.append(f"{resolved} {descriptor}".strip())
    return ", ".join(candidates)


def is_generic_service_heading(value: str) -> bool:
    words = [word.lower() for word in re.findall(r"[a-zA-Z0-9]+", value)]
    if not words:
        return True
    generic = {
        "available",
        "best",
        "clear",
        "expert",
        "focused",
        "helpful",
        "local",
        "professional",
        "trusted",
        "useful",
    }
    service_words = {"service", "services", "support", "solutions", "care"}
    return any(word in service_words for word in words) and all(word in generic | service_words for word in words)


def infer_services(pages: Iterable[PageScan], explicit_services: list[str] | None = None) -> list[str]:
    services: list[str] = []
    for service in explicit_services or []:
        if service and service not in services:
            services.append(service)
    for page in pages:
        candidate = candidate_service_from_url(page.url)
        if candidate and candidate not in services:
            services.append(candidate)
        for heading in page.headings:
            lowered = heading.lower()
            if explicit_services and is_generic_service_heading(heading):
                continue
            if any(hint in lowered for hint in SERVICE_HINTS) and heading not in services:
                services.append(heading[:80])
    return services[:12]


def unique_values(values: Iterable[str], limit: int = 20) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = normalize_text(str(value))
        key = text.lower()
        if text and key not in seen:
            output.append(text)
            seen.add(key)
        if len(output) >= limit:
            break
    return output


def extract_value_props(text: str) -> list[str]:
    claims: list[str] = []
    for pattern in VALUE_PROP_PATTERNS:
        for match in pattern.finditer(text):
            claim = normalize_text(match.group(0).strip(" .,:;"))
            if 12 <= len(claim) <= 90:
                claims.append(claim)
    return unique_values(claims, limit=12)


def extract_copy_signals(pages: Iterable[PageScan]) -> dict[str, list[str]]:
    all_text = " ".join(page.text_sample for page in pages if not page.error)
    delivery_modes: list[str] = []
    availability_signals: list[str] = []
    for label, pattern in DELIVERY_PATTERNS.items():
        if pattern.search(all_text):
            if label == "24_7":
                availability_signals.append(label)
            else:
                delivery_modes.append(label)
    return {
        "delivery_modes": unique_values(delivery_modes),
        "availability_signals": unique_values(availability_signals),
        "cta_signals": [label for label, pattern in CTA_PATTERNS.items() if pattern.search(all_text)],
        "landing_page_claims": extract_value_props(all_text),
    }


def build_page_evidence(page: PageScan) -> dict[str, object]:
    signals = extract_copy_signals([page])
    return {
        "url": page.url,
        "status": "unreadable" if page.error else "readable",
        "error": page.error or "",
        "title": page.title,
        "headings": page.headings[:8],
        "text_sample": page.text_sample[:1200],
        "delivery_modes": signals["delivery_modes"],
        "availability_signals": signals["availability_signals"],
        "cta_signals": signals["cta_signals"],
        "landing_page_claims": signals["landing_page_claims"],
        "copy_allowed_claims": [
            *signals["delivery_modes"],
            *signals["availability_signals"],
            *signals["landing_page_claims"],
        ],
    }


PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}")
PRICE_RE = re.compile(r"\$\s?\d{1,5}(?:,\d{3})*(?:\.\d{2})?")
PROMOTION_RE = re.compile(
    r"\b(sale|discount|coupon|promo code|promotion|special offer|% off|percent off|deal|limited time|save)\b",
    re.IGNORECASE,
)
ADDRESS_RE = re.compile(r"\b\d{2,6}\s+[A-Za-z0-9 .'-]+\s+(?:Street|St|Road|Rd|Avenue|Ave|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way)\b", re.IGNORECASE)


def clean_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value.replace("tel:", ""))
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits


def extract_asset_evidence(pages: list[PageScan], title: str) -> dict[str, list[dict[str, str]]]:
    phones: list[dict[str, str]] = []
    prices: list[dict[str, str]] = []
    promotions: list[dict[str, str]] = []
    business_names: list[dict[str, str]] = []
    service_areas: list[dict[str, str]] = []
    addresses: list[dict[str, str]] = []
    images: list[dict[str, str]] = []
    logos: list[dict[str, str]] = []
    gbp_mentions: list[dict[str, str]] = []

    if title:
        business_names.append({"value": title, "source": "site title"})

    for page in pages:
        for tel in page.tel_links:
            phones.append({"value": clean_phone(tel), "source": page.url, "evidence": tel})
        for phone in PHONE_RE.findall(page.text_sample):
            phones.append({"value": clean_phone(phone), "source": page.url, "evidence": phone})
        for price in PRICE_RE.findall(page.text_sample):
            prices.append({"value": price.replace(" ", ""), "source": page.url, "evidence": price})
        if PROMOTION_RE.search(page.text_sample):
            match = PROMOTION_RE.search(page.text_sample)
            promotions.append({"value": match.group(0) if match else "promotion", "source": page.url, "evidence": page.text_sample[:240]})
        for address in ADDRESS_RE.findall(page.text_sample):
            addresses.append({"value": str(address), "source": page.url, "evidence": page.text_sample[:240]})
        if "google.com/maps" in page.text_sample.lower() or "business profile" in page.text_sample.lower():
            gbp_mentions.append({"value": "possible_google_business_profile", "source": page.url})
        for image in [*page.images, *page.meta_images]:
            candidate = {
                "url": image.get("src", ""),
                "source": page.url,
                "alt": image.get("alt", ""),
                "width": image.get("width", ""),
                "height": image.get("height", ""),
                "evidence_type": "image",
            }
            images.append(candidate)
            marker = " ".join([image.get("src", ""), image.get("alt", ""), image.get("class", ""), image.get("id", "")]).lower()
            if "logo" in marker or "brand" in marker:
                logos.append({**candidate, "evidence_type": "logo"})
        for icon in page.icons:
            logos.append(
                {
                    "url": icon.get("src", ""),
                    "source": page.url,
                    "alt": "site icon",
                    "width": "",
                    "height": "",
                    "evidence_type": "logo",
                }
            )
        for heading in page.headings:
            if any(token in heading.lower() for token in ("serving", "service area", "locations", "areas")):
                service_areas.append({"value": heading, "source": page.url})

    def dedupe(items: list[dict[str, str]], key: str = "value") -> list[dict[str, str]]:
        seen: set[str] = set()
        output: list[dict[str, str]] = []
        for item in items:
            value = item.get(key, item.get("url", "")).strip().lower()
            if value and value not in seen:
                output.append(item)
                seen.add(value)
        return output

    return {
        "phone_numbers": dedupe(phones),
        "pricing": dedupe(prices),
        "promotions": dedupe(promotions, "source"),
        "business_names": dedupe(business_names),
        "service_areas": dedupe(service_areas),
        "addresses": dedupe(addresses, "source"),
        "image_candidates": dedupe(images, "url"),
        "logo_candidates": dedupe(logos, "url"),
        "gbp_mentions": dedupe(gbp_mentions, "source"),
    }


def build_review_artifacts(
    *,
    start_url: str,
    pages: list[PageScan],
    source_pages: list[str],
    explicit_services: list[str] | None = None,
) -> dict[str, dict]:
    services = infer_services(pages, explicit_services)
    title = next((page.title for page in pages if page.title), "")
    page_urls = [page.url for page in pages]
    asset_evidence = extract_asset_evidence(pages, title)
    copy_signals = extract_copy_signals(pages)
    page_evidence = {page.url: build_page_evidence(page) for page in pages}
    website_scan = {
        "website": start_url,
        "source_pages_scanned": page_urls,
        "page_evidence": page_evidence,
        "extracted_facts": {
            "primary_positioning": title,
            "services": services,
            "audience": [],
            "service_area": [],
            "modalities": copy_signals["delivery_modes"],
            "delivery_modes": copy_signals["delivery_modes"],
            "availability_signals": copy_signals["availability_signals"],
            "cta_signals": copy_signals["cta_signals"],
            "landing_page_claims": copy_signals["landing_page_claims"],
            "billing": "",
            "consultation": "",
            "asset_evidence": asset_evidence,
        },
        "fact_review": {
            "verified_website_facts": [
                {"fact": f"Page scanned: {page.url}", "source": page.url} for page in pages if not page.error
            ],
            "strategy_inferences": [
                {
                    "fact": "Service candidates were inferred from page URLs and headings.",
                    "source": "scanner heuristic",
                }
            ],
            "human_review_needed": [
                "Confirm active services and priority order before launch.",
                "Confirm target locations and location IDs before launch.",
                "Confirm budget and conversion tracking before launch.",
            ],
        },
        "human_review_needed": [
            "Confirm active services and priority order before launch.",
            "Confirm target locations and location IDs before launch.",
            "Confirm budget and conversion tracking before launch.",
        ],
    }
    source_attribution = {
        "website": start_url,
        "source_pages": [
            {
                "url": page.url,
                "used_for": ["website crawl", "service candidate extraction", "landing page review"],
                "title": page.title,
                "headings": page.headings[:8],
            }
            for page in pages
        ],
        "requested_source_pages": source_pages,
        "not_available": [
            "Google Ads account export",
            "search terms report",
            "location performance report",
            "conversion action report",
        ],
    }
    raw_crawl = {
        "start_url": start_url,
        "pages_scanned": len(pages),
        "pages": [asdict(page) for page in pages],
    }
    return {
        "website_scan": website_scan,
        "source_attribution": source_attribution,
        "raw_crawl": raw_crawl,
    }


class WebsiteScanner:
    """Scan source pages and write campaign-build website artifacts."""

    def scan(
        self,
        *,
        start_url: str,
        source_pages: list[str] | None = None,
        max_pages: int = 12,
    ) -> list[PageScan]:
        queue = [normalize_url(start_url, start_url)]
        for page in source_pages or []:
            normalized = normalize_url(page, start_url)
            if normalized and normalized not in queue:
                queue.append(normalized)

        scanned: list[PageScan] = []
        seen: set[str] = set()
        while queue and len(scanned) < max_pages:
            url = queue.pop(0)
            if not url or url in seen:
                continue
            seen.add(url)
            try:
                page = parse_page(url, read_url(url))
            except (OSError, UnicodeDecodeError, urllib.error.URLError) as exc:
                page = PageScan(
                    url=url,
                    title="",
                    headings=[],
                    links=[],
                    tel_links=[],
                    images=[],
                    icons=[],
                    meta_images=[],
                    json_ld=[],
                    text_sample="",
                    error=str(exc),
                )
            scanned.append(page)
            for link in page.links:
                if same_site(link, start_url) and link not in seen and link not in queue:
                    queue.append(link)
        return scanned

    def write_artifacts(
        self,
        *,
        start_url: str,
        output_dir: Path,
        source_pages: list[str] | None = None,
        explicit_services: list[str] | None = None,
        max_pages: int = 12,
    ) -> dict[str, Path]:
        pages = self.scan(start_url=start_url, source_pages=source_pages, max_pages=max_pages)
        artifacts = build_review_artifacts(
            start_url=start_url,
            pages=pages,
            source_pages=source_pages or [],
            explicit_services=explicit_services,
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = {
            "website_scan": output_dir / "website_scan.json",
            "source_attribution": output_dir / "source_attribution.json",
            "raw_crawl": output_dir / "raw_website_crawl.json",
        }
        paths["website_scan"].write_text(json.dumps(artifacts["website_scan"], indent=2) + "\n", encoding="utf-8")
        paths["source_attribution"].write_text(
            json.dumps(artifacts["source_attribution"], indent=2) + "\n", encoding="utf-8"
        )
        paths["raw_crawl"].write_text(json.dumps(artifacts["raw_crawl"], indent=2) + "\n", encoding="utf-8")
        return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan a client website into new-campaign source artifacts.")
    parser.add_argument("--url", required=True, help="Client website URL or file URL.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Build directory for JSON artifacts.")
    parser.add_argument("--source-page", action="append", default=[], help="Additional source page URL. May repeat.")
    parser.add_argument("--service", action="append", default=[], help="Approved service override. May repeat.")
    parser.add_argument("--max-pages", type=int, default=12)
    args = parser.parse_args()

    paths = WebsiteScanner().write_artifacts(
        start_url=args.url,
        output_dir=args.output_dir,
        source_pages=args.source_page,
        explicit_services=args.service,
        max_pages=args.max_pages,
    )
    print(json.dumps({key: str(path) for key, path in paths.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
