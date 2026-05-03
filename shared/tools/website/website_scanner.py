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


@dataclass
class PageScan:
    url: str
    title: str
    headings: list[str]
    links: list[str]
    text_sample: str
    error: str | None = None


class LinkAndTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.title_parts: list[str] = []
        self.headings: list[str] = []
        self.text_parts: list[str] = []
        self._tag_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._tag_stack.append(tag)
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()

    def handle_data(self, data: str) -> None:
        text = normalize_text(data)
        if not text:
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
    text = normalize_text(" ".join(parser.text_parts))
    return PageScan(
        url=url,
        title=normalize_text(" ".join(parser.title_parts)),
        headings=parser.headings[:24],
        links=links,
        text_sample=text[:4000],
    )


def candidate_service_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    slug = parsed.path.strip("/").split("/")[-1]
    if not slug:
        return ""
    words = [word for word in re.split(r"[-_]+", slug) if word and not word.isdigit()]
    if not any(word.lower() in SERVICE_HINTS for word in words):
        return ""
    return " ".join(word.title() for word in words)


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
            if any(hint in lowered for hint in SERVICE_HINTS) and heading not in services:
                services.append(heading[:80])
    return services[:12]


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
    website_scan = {
        "website": start_url,
        "source_pages_scanned": page_urls,
        "extracted_facts": {
            "primary_positioning": title,
            "services": services,
            "audience": [],
            "service_area": [],
            "modalities": [],
            "billing": "",
            "consultation": "",
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
                page = PageScan(url=url, title="", headings=[], links=[], text_sample="", error=str(exc))
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
