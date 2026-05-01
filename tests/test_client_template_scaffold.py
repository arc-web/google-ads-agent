from __future__ import annotations

from pathlib import Path

from shared.rebuild.scaffold_client import scaffold_client
from shared.rebuild.staging_validator import REQUIRED_RSA_DESCRIPTIONS, REQUIRED_RSA_HEADLINES, read_tsv, validate_file


def test_client_scaffold_materializes_active_template_filenames(tmp_path: Path) -> None:
    target = scaffold_client(
        agency="Example Agency",
        client="Example Client",
        display_name="Example Client",
        website="https://example.com/",
        clients_dir=tmp_path,
    )

    assert target == tmp_path / "example_agency" / "example_client"
    assert (target / "campaigns/account_export.csv").exists()
    assert not (target / "campaigns/account_export_template.csv").exists()
    assert (target / "reports/performance_inputs/search_terms_report.csv").exists()
    assert (target / "reports/performance_inputs/location_report.csv").exists()


def test_client_scaffold_account_export_template_matches_active_staging_contract(tmp_path: Path) -> None:
    target = scaffold_client(
        agency="Example Agency",
        client="Example Client",
        display_name="Example Client",
        website="https://example.com/",
        clients_dir=tmp_path,
    )
    staging_path = target / "campaigns/account_export.csv"

    headers, rows, encoding = read_tsv(staging_path)
    report = validate_file(staging_path)

    assert encoding in {"utf-8", "utf-8-sig"}
    assert report["status"] == "pass"
    assert report["counts"]["campaign_rows"] == 1
    assert report["counts"]["keyword_rows"] == 1
    assert report["counts"]["rsa_rows"] == 1
    assert report["counts"]["location_rows"] == 1
    assert "Ad Group" in headers
    assert "Ad group" not in headers
    assert all(header in headers for header in REQUIRED_RSA_HEADLINES)
    assert all(header in headers for header in REQUIRED_RSA_DESCRIPTIONS)

    keyword_row = next(row for row in rows if row.get("Keyword"))
    campaign_row = next(row for row in rows if row.get("Campaign Type") == "Search")
    assert keyword_row["Criterion Type"] == "Phrase"
    assert campaign_row["Broad match keywords"] == "Off"
    assert campaign_row["EU political ads"] == "Doesn't have EU political ads"


def test_scaffold_does_not_overwrite_existing_client(tmp_path: Path) -> None:
    scaffold_client(
        agency="Example Agency",
        client="Example Client",
        display_name="Example Client",
        website="https://example.com/",
        clients_dir=tmp_path,
    )

    try:
        scaffold_client(
            agency="Example Agency",
            client="Example Client",
            display_name="Example Client",
            website="https://example.com/",
            clients_dir=tmp_path,
        )
    except FileExistsError as exc:
        assert "Client directory already exists" in str(exc)
    else:
        raise AssertionError("Expected existing scaffold to be protected.")
