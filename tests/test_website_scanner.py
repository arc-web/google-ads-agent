from __future__ import annotations

import json
import gzip
from pathlib import Path
import urllib.request

from shared.tools.website.website_scanner import WebsiteScanner, read_url


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


def test_website_scanner_extracts_copy_signals(tmp_path: Path) -> None:
    site = tmp_path / "site"
    site.mkdir()
    index = site / "index.html"
    index.write_text(
        """<!doctype html>
<html>
<head><title>Signal Company</title></head>
<body>
  <h1>Repair Services</h1>
  <p>Book online and in-person repair appointments with experienced local support.</p>
  <p>Our answering service is available 24/7 for urgent service questions.</p>
  <a href="repair-services.html">Repair Services</a>
</body>
</html>
""",
        encoding="utf-8",
    )
    (site / "repair-services.html").write_text(
        "<html><body><h1>Repair Services</h1><p>Schedule repair support with practical options.</p></body></html>",
        encoding="utf-8",
    )

    paths = WebsiteScanner().write_artifacts(start_url=index.as_uri(), output_dir=tmp_path / "out", max_pages=5)
    website_scan = json.loads(paths["website_scan"].read_text(encoding="utf-8"))

    facts = website_scan["extracted_facts"]
    assert "virtual" in facts["delivery_modes"]
    assert "in_person" in facts["delivery_modes"]
    assert "24_7" in facts["availability_signals"]
    assert "Book Today" in facts["cta_signals"]
    assert website_scan["page_evidence"][index.as_uri()]["status"] == "readable"


def test_website_scanner_extracts_logo_asset_evidence(tmp_path: Path) -> None:
    site = tmp_path / "site"
    site.mkdir()
    (site / "logo.png").write_bytes(b"not-an-image-for-scanner")
    (site / "icon.png").write_bytes(b"not-an-image-for-scanner")
    index = site / "index.html"
    index.write_text(
        """<!doctype html>
<html>
<head>
  <title>Logo Evidence Company</title>
  <meta property="og:image" content="logo.png">
  <link rel="icon" href="icon.png">
  <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"Organization","name":"Logo Evidence Company","logo":"logo.png"}
  </script>
</head>
<body>
  <img src="logo.png" alt="Logo Evidence Company logo" width="512" height="512">
</body>
</html>
""",
        encoding="utf-8",
    )

    paths = WebsiteScanner().write_artifacts(start_url=index.as_uri(), output_dir=tmp_path / "out", max_pages=1)
    website_scan = json.loads(paths["website_scan"].read_text(encoding="utf-8"))
    evidence = website_scan["extracted_facts"]["asset_evidence"]

    logo_urls = {item["url"] for item in evidence["logo_candidates"]}
    assert (site / "logo.png").as_uri() in logo_urls
    assert (site / "icon.png").as_uri() in logo_urls
    assert "Logo Evidence Company" in {item["value"] for item in evidence["business_names"]}


def test_read_url_decodes_gzip_response(monkeypatch) -> None:
    class FakeHeaders:
        def get_content_charset(self) -> str:
            return "utf-8"

        def get(self, key: str, default: str = "") -> str:
            return "gzip" if key == "Content-Encoding" else default

    class FakeResponse:
        headers = FakeHeaders()

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def read(self) -> bytes:
            return gzip.compress(b"<html><body>Learning and Development</body></html>")

    monkeypatch.setattr(urllib.request, "urlopen", lambda request, timeout=12: FakeResponse())

    assert "Learning and Development" in read_url("https://example.com/")
