from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from PIL import Image, ImageDraw

from shared.creative_assets.build_creative_asset_package import build_creative_asset_package, parse_youtube_video_id
from shared.tools.website.website_scanner import WebsiteScanner


def write_fixture_image(path: Path, size: tuple[int, int], color: tuple[int, int, int]) -> None:
    image = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(image)
    draw.rectangle((size[0] // 5, size[1] // 5, size[0] - 40, size[1] - 40), outline=(255, 255, 255), width=8)
    image.save(path, format="JPEG", quality=92)


def test_website_scanner_normalizes_srcset(tmp_path: Path) -> None:
    site = tmp_path / "site"
    site.mkdir()
    write_fixture_image(site / "hero.jpg", (1200, 628), (44, 93, 104))
    write_fixture_image(site / "hero-large.jpg", (1600, 900), (64, 116, 127))
    index = site / "index.html"
    index.write_text(
        """<!doctype html>
<html>
<head><title>Example Creative Site</title></head>
<body>
  <h1>Therapy Services</h1>
  <img src="hero.jpg" srcset="hero-large.jpg 2x" alt="therapy services office">
</body>
</html>
""",
        encoding="utf-8",
    )

    paths = WebsiteScanner().write_artifacts(start_url=index.as_uri(), output_dir=tmp_path / "out")
    raw = json.loads(paths["raw_crawl"].read_text(encoding="utf-8"))

    assert raw["pages"][0]["images"][0]["srcset"].startswith((site / "hero-large.jpg").as_uri())


def test_creative_asset_package_outputs_approval_artifacts(tmp_path: Path) -> None:
    site = tmp_path / "site"
    site.mkdir()
    write_fixture_image(site / "therapy-office.jpg", (1400, 900), (44, 93, 104))
    write_fixture_image(site / "logo.jpg", (900, 300), (238, 241, 240))
    index = site / "index.html"
    index.write_text(
        """<!doctype html>
<html>
<head>
  <title>Example Creative Site</title>
  <meta property="og:image" content="therapy-office.jpg">
</head>
<body>
  <h1>Therapy Services</h1>
  <img src="therapy-office.jpg" alt="therapy services office">
  <img src="logo.jpg" alt="Example Creative Site logo">
</body>
</html>
""",
        encoding="utf-8",
    )
    build_dir = tmp_path / "clients" / "agency" / "client" / "media" / "creative"

    artifacts = build_creative_asset_package(
        Namespace(
            agency="agency",
            client="client",
            display_name="Example Creative Site",
            website=index.as_uri(),
            website_scan_json=None,
            raw_crawl_json=None,
            service_theme="Therapy Services",
            landing_page=[],
            brand_rules="calm practical care",
            logo_file=[],
            youtube_channel_url="",
            youtube_video_url=["https://youtu.be/abc123DEF_0"],
            youtube_sync_status=None,
            output_build_path=build_dir,
            client_dir=None,
            clients_dir=tmp_path / "clients",
            build_date="2026-05-04",
            max_pages=3,
            max_candidates=80,
            minimum_source_images=1,
            first_party_cdn_domain=[],
        )
    )

    manifest = json.loads(artifacts["creative_asset_manifest"].read_text(encoding="utf-8"))
    attribution = json.loads(artifacts["creative_source_attribution"].read_text(encoding="utf-8"))
    validation = json.loads(artifacts["validation_report"].read_text(encoding="utf-8"))

    assert artifacts["source_image_folder"].is_dir()
    assert artifacts["processed_image_folder"].is_dir()
    assert artifacts["source_image_folder"] == build_dir / "source_images"
    assert artifacts["processed_image_folder"] == build_dir / "processed_images"
    assert artifacts["creative_asset_review"].exists()
    assert artifacts["youtube_video_manifest"].exists()
    assert artifacts["youtube_video_review"].exists()
    assert artifacts["youtube_sync_checklist"].exists()
    assert artifacts["client_creative_approval_html"].exists()
    assert artifacts["client_email_draft"].exists()
    assert validation["status"] == "pass"
    assert validation["campaign_ready_assets"] == 0
    assert manifest["approval_required"] is True
    assert manifest["campaign_ready"] is False
    assert any(asset["variants"] for asset in manifest["assets"])
    assert all(asset["approval_status"] == "needs client approval" for asset in manifest["assets"])
    assert attribution["assets"]
    assert all("source_url" in asset for asset in attribution["assets"])
    youtube_manifest = json.loads(artifacts["youtube_video_manifest"].read_text(encoding="utf-8"))
    assert youtube_manifest["approval_required"] is True
    assert youtube_manifest["campaign_ready"] is False
    assert youtube_manifest["videos"][0]["video_id"] == "abc123DEF_0"
    assert youtube_manifest["videos"][0]["approval_status"] == "needs client approval"
    assert youtube_manifest["videos"][0]["campaign_ready"] is False


def test_creative_asset_package_generates_labeled_drafts_when_sources_are_missing(tmp_path: Path) -> None:
    site = tmp_path / "site"
    site.mkdir()
    index = site / "index.html"
    index.write_text(
        """<!doctype html>
<html><head><title>No Images Site</title></head><body><h1>Repair Services</h1></body></html>
""",
        encoding="utf-8",
    )

    artifacts = build_creative_asset_package(
        Namespace(
            agency="agency",
            client="client",
            display_name="No Images Site",
            website=index.as_uri(),
            website_scan_json=None,
            raw_crawl_json=None,
            service_theme="Repair Services",
            landing_page=[],
            brand_rules="clear service support",
            logo_file=[],
            youtube_channel_url="",
            youtube_video_url=[],
            youtube_sync_status=None,
            output_build_path=tmp_path / "build",
            client_dir=None,
            clients_dir=tmp_path / "clients",
            build_date="2026-05-04",
            max_pages=1,
            max_candidates=80,
            minimum_source_images=2,
            first_party_cdn_domain=[],
        )
    )

    manifest = json.loads(artifacts["creative_asset_manifest"].read_text(encoding="utf-8"))
    generated = [asset for asset in manifest["assets"] if asset["source_type"] == "generated_draft"]

    assert generated
    assert all("generated_draft" in asset["risk_flags"] for asset in generated)
    assert all(asset["campaign_ready"] is False for asset in generated)


def test_youtube_video_url_parser_handles_common_formats() -> None:
    assert parse_youtube_video_id("https://www.youtube.com/watch?v=abc123DEF_0") == "abc123DEF_0"
    assert parse_youtube_video_id("https://youtu.be/abc123DEF_0") == "abc123DEF_0"
    assert parse_youtube_video_id("https://www.youtube.com/embed/abc123DEF_0") == "abc123DEF_0"
    assert parse_youtube_video_id("https://www.youtube.com/shorts/abc123DEF_0") == "abc123DEF_0"
    assert parse_youtube_video_id("https://www.youtube.com/playlist?list=abc123DEF_0") == ""


def test_creative_asset_package_writes_youtube_section_from_embeds_and_jsonld(tmp_path: Path) -> None:
    site = tmp_path / "site"
    site.mkdir()
    write_fixture_image(site / "therapy-office.jpg", (1400, 900), (44, 93, 104))
    index = site / "index.html"
    index.write_text(
        """<!doctype html>
<html>
<head>
  <title>Video Creative Site</title>
  <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"VideoObject","name":"Therapy overview","embedUrl":"https://www.youtube.com/embed/def456GHI_1"}
  </script>
</head>
<body>
  <h1>Therapy Services</h1>
  <iframe src="https://www.youtube.com/embed/abc123DEF_0" title="Therapy intro"></iframe>
  <a href="https://www.youtube.com/shorts/ghi789JKL_2">Watch short</a>
  <img src="therapy-office.jpg" alt="therapy services office">
</body>
</html>
""",
        encoding="utf-8",
    )

    artifacts = build_creative_asset_package(
        Namespace(
            agency="agency",
            client="client",
            display_name="Video Creative Site",
            website=index.as_uri(),
            website_scan_json=None,
            raw_crawl_json=None,
            service_theme="Therapy Services",
            landing_page=[],
            brand_rules="calm practical care",
            logo_file=[],
            youtube_channel_url="",
            youtube_video_url=["https://youtu.be/abc123DEF_0"],
            youtube_sync_status=None,
            output_build_path=tmp_path / "clients" / "agency" / "client" / "media" / "video",
            client_dir=None,
            clients_dir=tmp_path / "clients",
            build_date="2026-05-04",
            max_pages=3,
            max_candidates=80,
            minimum_source_images=1,
            first_party_cdn_domain=[],
        )
    )

    youtube_manifest = json.loads(artifacts["youtube_video_manifest"].read_text(encoding="utf-8"))
    validation = json.loads(artifacts["validation_report"].read_text(encoding="utf-8"))
    html_text = artifacts["client_creative_approval_html"].read_text(encoding="utf-8")
    video_ids = {video["video_id"] for video in youtube_manifest["videos"]}

    assert {"abc123DEF_0", "def456GHI_1", "ghi789JKL_2"} <= video_ids
    assert validation["status"] == "pass"
    assert validation["youtube_videos"]["campaign_ready_videos"] == 0
    assert "YouTube Videos" in html_text
    assert "youtube.com/embed/abc123DEF_0" in html_text
    assert artifacts["youtube_video_review"].read_text(encoding="utf-8").startswith("video_id,title,source_url")
    assert "Google Ads account has administrative access" in artifacts["youtube_sync_checklist"].read_text(encoding="utf-8")
