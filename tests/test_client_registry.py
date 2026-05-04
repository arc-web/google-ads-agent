from __future__ import annotations

import csv
from pathlib import Path

from shared.clients.client_registry import (
    ProposedAccountChange,
    build_registry,
    scan_local_client_directories,
    scaffold_slug,
    write_gap_report,
    write_registry_csv,
)
from shared.clients.supabase_client_registry import SupabaseClientRecord
from shared.rebuild.scaffold_client import scaffold_client


def record(
    name: str,
    *,
    client_id: str = "client-1",
    website: str = "https://example.com/",
    customer_id: str = "",
) -> SupabaseClientRecord:
    return SupabaseClientRecord(
        client_id=client_id,
        status="active",
        relationship_type="client",
        company_id=f"company-{client_id}",
        company_name=name,
        company_type="client",
        website_url=website,
        supabase_paid_ads_id=f"paid-{client_id}",
        google_ads_customer_id=customer_id,
        google_ads_login_customer_id="2119931898" if customer_id else "",
        discord_channel_id="",
    )


def test_scanner_detects_agency_and_legacy_layouts(tmp_path: Path) -> None:
    scaffold_client("arc", "Example Client", "Example Client", "https://example.com/", clients_dir=tmp_path)
    legacy = tmp_path / "legacy_client"
    (legacy / "campaigns").mkdir(parents=True)

    directories = scan_local_client_directories(tmp_path)

    assert {directory.layout for directory in directories} == {"agency_client", "legacy"}
    assert {directory.client_slug for directory in directories} == {"example_client", "legacy_client"}


def test_registry_matching_prefers_google_ads_customer_id(tmp_path: Path) -> None:
    matched = scaffold_client("arc", "Wrong Name", "Wrong Name", "https://wrong.example/", clients_dir=tmp_path)
    hq_dir = matched / "docs" / "client_hq"
    hq_dir.mkdir(parents=True, exist_ok=True)
    (hq_dir / "client_hq.json").write_text('{"google_ads_customer_id": "123-456-7890"}\n', encoding="utf-8")

    other = scaffold_client("arc", "Real Name", "Real Name", "https://real.example/", clients_dir=tmp_path)
    rows, gaps = build_registry(
        [record("Real Name", website="https://real.example/", customer_id="1234567890")],
        scan_local_client_directories(tmp_path),
        checked_at="2026-05-05T00:00:00+00:00",
    )

    row = next(item for item in rows if item.supabase_client_id == "client-1")
    assert row.local_client_path == matched.as_posix()
    assert "customer ID" in row.mismatch_notes
    assert any(gap.local_client_path == other.as_posix() for gap in gaps)


def test_gap_report_emits_scaffold_commands_without_creating_directories(tmp_path: Path) -> None:
    rows, gaps = build_registry(
        [record("Missing Client", website="MissingClient.com")],
        [],
        checked_at="2026-05-05T00:00:00+00:00",
    )

    assert rows[0].directory_status == "missing"
    assert gaps[0].suggested_command.startswith("python3 shared/rebuild/scaffold_client.py")
    assert "--client 'missingclient'" in gaps[0].suggested_command
    assert not (tmp_path / "arc" / "missingclient").exists()


def test_csv_writer_has_stable_non_secret_columns(tmp_path: Path) -> None:
    rows, _ = build_registry(
        [record("Visible Client", website="VisibleClient.com")],
        [],
        checked_at="2026-05-05T00:00:00+00:00",
    )
    output = tmp_path / "client_registry.csv"

    write_registry_csv(rows, output)

    header = output.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert "api_key" not in header
    assert "service_key" not in header
    assert "client_name" in header
    assert "api_visibility_status" in header


def test_gap_report_writer_is_stable(tmp_path: Path) -> None:
    _, gaps = build_registry(
        [record("Visible Client", website="VisibleClient.com")],
        [],
        checked_at="2026-05-05T00:00:00+00:00",
    )
    output = tmp_path / "gap_report.csv"

    write_gap_report(gaps, output)

    with output.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["issue_type"] == "missing_local_directory"


def test_fdl_duplicate_resolution_prefers_fdl_xibalba_slug() -> None:
    assert scaffold_slug(record("fdlxibalba", website="")) == "fdl_xibalba"


def test_proposal_only_workflow_blocks_live_execution_and_executed_status() -> None:
    proposal = ProposedAccountChange(
        registry_row_id="arc/example",
        google_ads_customer_id="1234567890",
        mutation_type="budget_change",
        risk_tier="medium",
        target_resource="customers/1234567890/campaignBudgets/1",
        before_snapshot_required=True,
        rollback_payload_required=True,
        discord_proposal_channel_id="123",
        approver_ids=("u1",),
    )

    validated = proposal.transition("validated")
    approval_required = validated.transition("approval_required")

    assert approval_required.status == "approval_required"
    try:
        approval_required.transition("executed")
    except ValueError as exc:
        assert "not implemented" in str(exc)
    else:
        raise AssertionError("executed status should be blocked")
    try:
        approval_required.execute()
    except RuntimeError as exc:
        assert "blocked" in str(exc)
    else:
        raise AssertionError("live execution should be blocked")
