from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from shared.gads.core.search_campaigns.search_asset_generator import SearchAssetGenerator, write_asset_artifacts
from shared.tools.website.website_scanner import WebsiteScanner


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "asset_site"


@dataclass
class FakeAdGroup:
    name: str
    final_url: str
    keywords: list[str]
    headlines: list[str]
    descriptions: list[str]


def test_asset_generator_uses_evidence_and_blocks_guesswork(tmp_path: Path) -> None:
    website = (FIXTURE_DIR / "index.html").as_uri()
    paths = WebsiteScanner().write_artifacts(
        start_url=website,
        output_dir=tmp_path,
        explicit_services=["Individual Therapy", "Family Therapy", "Trauma Support"],
        max_pages=8,
    )
    website_scan = json.loads(paths["website_scan"].read_text(encoding="utf-8"))
    source_attribution = json.loads(paths["source_attribution"].read_text(encoding="utf-8"))
    source_pages = [page["url"] for page in source_attribution["source_pages"]]
    ad_group = FakeAdGroup(
        name="Services - Therapy Services",
        final_url=(FIXTURE_DIR / "therapy-services.html").as_uri(),
        keywords=["therapy services"],
        headlines=[],
        descriptions=[],
    )

    plan = SearchAssetGenerator().generate(
        campaign="ARC - Search - Therapy - V1",
        ad_groups=[ad_group],
        service_catalog={"active_services_for_staging": ["Individual Therapy", "Family Therapy", "Trauma Support"]},
        source_pages=source_pages,
        website=website,
        website_scan=website_scan,
    )
    artifacts = write_asset_artifacts(tmp_path, plan)

    assert plan.calls
    assert plan.prices and len(plan.prices) == 3
    assert plan.promotions
    assert plan.business_names
    assert plan.structured_snippets
    assert all(sitelink.link_text.lower() not in {"contact us", "services", "pricing"} for sitelink in plan.sitelinks)
    assert "gbp_linking_required" in {decision.reason for decision in plan.skipped_assets}
    assert Path(artifacts["ad_asset_research_matrix_json"]).exists()
    assert Path(artifacts["image_asset_manifest"]).exists()
    assert any(candidate.status == "ready_for_import_package" for candidate in plan.candidate_assets)


def test_asset_generator_skips_prices_promotions_and_calls_without_evidence(tmp_path: Path) -> None:
    website = (Path(__file__).resolve().parent / "fixtures" / "new_campaign_site" / "index.html").as_uri()
    paths = WebsiteScanner().write_artifacts(
        start_url=website,
        output_dir=tmp_path,
        explicit_services=["Repair Services", "Consulting Services", "Support Services"],
        max_pages=5,
    )
    website_scan = json.loads(paths["website_scan"].read_text(encoding="utf-8"))
    source_attribution = json.loads(paths["source_attribution"].read_text(encoding="utf-8"))
    source_pages = [page["url"] for page in source_attribution["source_pages"]]
    ad_group = FakeAdGroup(
        name="Services - Repair Services",
        final_url=(Path(__file__).resolve().parent / "fixtures" / "new_campaign_site" / "repair-services.html").as_uri(),
        keywords=["repair services"],
        headlines=[],
        descriptions=[],
    )

    plan = SearchAssetGenerator().generate(
        campaign="ARC - Search - Repair - V1",
        ad_groups=[ad_group],
        service_catalog={"active_services_for_staging": ["Repair Services", "Consulting Services", "Support Services"]},
        source_pages=source_pages,
        website=website,
        website_scan=website_scan,
    )

    assert not plan.calls
    assert not plan.prices
    assert not plan.promotions
    assert {"no_confirmed_phone_number", "insufficient_explicit_pricing", "no_explicit_promotion"} <= {
        decision.reason for decision in plan.skipped_assets
    }
