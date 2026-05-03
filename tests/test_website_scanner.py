from __future__ import annotations

import json
from pathlib import Path

from shared.tools.website.website_scanner import WebsiteScanner


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "new_campaign_site"


def test_website_scanner_writes_generic_review_artifacts(tmp_path: Path) -> None:
    start_url = (FIXTURE_DIR / "index.html").as_uri()
    paths = WebsiteScanner().write_artifacts(start_url=start_url, output_dir=tmp_path, max_pages=5)

    website_scan = json.loads(paths["website_scan"].read_text(encoding="utf-8"))
    source_attribution = json.loads(paths["source_attribution"].read_text(encoding="utf-8"))
    raw_crawl = json.loads(paths["raw_crawl"].read_text(encoding="utf-8"))

    assert website_scan["extracted_facts"]["primary_positioning"] == "Example Services Company"
    assert "Repair Services" in website_scan["extracted_facts"]["services"]
    assert website_scan["fact_review"]["verified_website_facts"]
    assert website_scan["fact_review"]["strategy_inferences"]
    assert website_scan["fact_review"]["human_review_needed"]
    assert len(source_attribution["source_pages"]) >= 2
    assert raw_crawl["pages_scanned"] >= 2

    combined = json.dumps(raw_crawl).lower()
    assert "myexpertresume" not in combined
    assert "thinkhappylivehealthy" not in combined
