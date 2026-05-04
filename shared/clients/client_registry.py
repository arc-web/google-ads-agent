"""Local client registry reconciliation and proposal-only change guards."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from shared.clients.supabase_client_registry import SupabaseClientRecord, SupabaseRegistryClient


ROOT = Path(__file__).resolve().parents[2]
CLIENTS_DIR = ROOT / "clients"
REGISTRY_COLUMNS = [
    "agency_slug",
    "client_slug",
    "local_client_path",
    "local_layout",
    "directory_status",
    "supabase_client_id",
    "supabase_paid_ads_id",
    "client_name",
    "website_url",
    "google_ads_customer_id",
    "google_ads_login_customer_id",
    "gads_status",
    "discord_channel_id",
    "report_cadence",
    "gads_owner_identity",
    "allowed_agents",
    "api_visibility_status",
    "mismatch_notes",
    "last_checked_at",
]
SECRET_FIELD_PATTERNS = ("secret", "token", "password", "credential", "service_key", "api_key", "email")
ALLOWED_PROPOSAL_STATUSES = {"draft", "validated", "approval_required"}
BLOCKED_PROPOSAL_STATUSES = {"approved", "executed", "rolled_back"}


@dataclass(frozen=True)
class LocalClientDirectory:
    agency_slug: str
    client_slug: str
    path: Path
    layout: str
    client_name: str = ""
    website_url: str = ""
    google_ads_customer_id: str = ""
    google_ads_login_customer_id: str = ""

    @property
    def relative_path(self) -> str:
        try:
            return self.path.relative_to(ROOT).as_posix()
        except ValueError:
            return self.path.as_posix()

    @property
    def aliases(self) -> set[str]:
        return {
            normalize_key(self.client_slug),
            normalize_key(self.client_name),
            normalize_key(domain_from_url(self.website_url)),
        } - {""}


@dataclass(frozen=True)
class RegistryRow:
    agency_slug: str
    client_slug: str
    local_client_path: str
    local_layout: str
    directory_status: str
    supabase_client_id: str
    supabase_paid_ads_id: str
    client_name: str
    website_url: str
    google_ads_customer_id: str
    google_ads_login_customer_id: str
    gads_status: str
    discord_channel_id: str
    report_cadence: str
    gads_owner_identity: str
    allowed_agents: str
    api_visibility_status: str
    mismatch_notes: str
    last_checked_at: str


@dataclass(frozen=True)
class GapReportRow:
    issue_type: str
    agency_slug: str
    client_slug: str
    local_client_path: str
    supabase_client_id: str
    client_name: str
    website_url: str
    google_ads_customer_id: str
    notes: str
    suggested_command: str


@dataclass(frozen=True)
class ProposedAccountChange:
    registry_row_id: str
    google_ads_customer_id: str
    mutation_type: str
    risk_tier: str
    target_resource: str
    before_snapshot_required: bool
    rollback_payload_required: bool
    discord_proposal_channel_id: str
    approver_ids: tuple[str, ...]
    validate_only_result: str = ""
    status: str = "draft"

    def transition(self, next_status: str) -> "ProposedAccountChange":
        if next_status in BLOCKED_PROPOSAL_STATUSES:
            raise ValueError(f"Proposal status is not implemented in this phase: {next_status}")
        if next_status not in ALLOWED_PROPOSAL_STATUSES:
            raise ValueError(f"Unknown proposal status: {next_status}")
        if self.status == "draft" and next_status not in {"draft", "validated"}:
            raise ValueError("Draft proposals must validate before approval is required.")
        if self.status == "validated" and next_status not in {"validated", "approval_required"}:
            raise ValueError("Validated proposals can only move to approval_required.")
        return ProposedAccountChange(**{**asdict(self), "status": next_status})

    def execute(self) -> None:
        raise RuntimeError("Live Google Ads mutations are blocked in this proposal-only phase.")


def normalize_slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    return re.sub(r"_+", "_", normalized).strip("_")


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def digits_only(value: str) -> str:
    return "".join(character for character in str(value) if character.isdigit())


def domain_from_url(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"^https?://", "", text)
    text = text.split("/", 1)[0].removeprefix("www.")
    return re.sub(r"\.(com|org|net|co|io)$", "", text)


def scaffold_slug(record: SupabaseClientRecord) -> str:
    if normalize_key(record.company_name) == "fdlxibalba":
        return "fdl_xibalba"
    source = domain_from_url(record.website_url) or record.company_name or record.client_id
    return normalize_slug(source)


def scan_local_client_directories(clients_dir: Path = CLIENTS_DIR) -> list[LocalClientDirectory]:
    directories: list[LocalClientDirectory] = []
    if not clients_dir.exists():
        return directories
    agency_containers = {
        path.name
        for path in clients_dir.iterdir()
        if path.is_dir() and any((child / "config" / "client_profile.yaml").exists() for child in path.iterdir() if child.is_dir())
    }
    for agency_dir in sorted(path for path in clients_dir.iterdir() if path.is_dir() and path.name in agency_containers):
        for client_dir in sorted(path for path in agency_dir.iterdir() if path.is_dir()):
            if is_client_workspace(client_dir):
                directories.append(load_local_directory(client_dir, agency_dir.name, "agency_client"))
    for client_dir in sorted(path for path in clients_dir.iterdir() if path.is_dir() and path.name not in agency_containers):
        if is_client_workspace(client_dir):
            directories.append(load_local_directory(client_dir, "", "legacy"))
    return directories


def is_client_workspace(path: Path) -> bool:
    return any((path / name).exists() for name in ("config", "campaigns", "docs", "reports", "build", "search_themes"))


def load_local_directory(path: Path, agency_slug: str, layout: str) -> LocalClientDirectory:
    profile = read_client_profile(path / "config" / "client_profile.yaml")
    hq = read_client_hq(path / "docs" / "client_hq" / "client_hq.json")
    return LocalClientDirectory(
        agency_slug=profile.get("agency_slug") or agency_slug,
        client_slug=profile.get("client_slug") or path.name,
        path=path,
        layout=layout,
        client_name=profile.get("display_name") or hq.get("client_name", ""),
        website_url=profile.get("website_url") or hq.get("website_url", ""),
        google_ads_customer_id=digits_only(str(hq.get("google_ads_customer_id", ""))),
        google_ads_login_customer_id=digits_only(str(hq.get("google_ads_login_customer_id", ""))),
    )


def read_client_profile(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    in_client = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if line == "client:":
            in_client = True
            continue
        if line and not line.startswith(" ") and line.endswith(":"):
            in_client = False
        if in_client:
            match = re.match(r"\s+(display_name|client_slug|agency_slug|website_url):\s*[\"']?(.*?)[\"']?\s*$", line)
            if match:
                values[match.group(1)] = match.group(2)
    return values


def read_client_hq(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def build_registry(
    supabase_records: Iterable[SupabaseClientRecord],
    local_directories: Iterable[LocalClientDirectory],
    *,
    checked_at: str | None = None,
) -> tuple[list[RegistryRow], list[GapReportRow]]:
    checked = checked_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    locals_list = list(local_directories)
    matched_paths: set[Path] = set()
    rows: list[RegistryRow] = []
    gaps: list[GapReportRow] = []

    for record in sorted(supabase_records, key=lambda item: item.company_name.lower()):
        local, match_notes = match_local_directory(record, locals_list)
        if local:
            matched_paths.add(local.path)
            rows.append(registry_row_for_match(record, local, "exists", "visible", match_notes, checked))
        else:
            slug = scaffold_slug(record)
            path = f"clients/arc/{slug}"
            rows.append(
                registry_row_for_missing(record, slug, path, "missing", "visible", "No matching local directory found.", checked)
            )
            gaps.append(gap_row_for_missing(record, slug, path))

    for local in sorted(locals_list, key=lambda item: item.relative_path):
        if local.path in matched_paths:
            continue
        rows.append(registry_row_for_local_only(local, checked))
        gaps.append(gap_row_for_local_only(local))

    rows = sorted(rows, key=lambda row: (row.directory_status != "exists", row.agency_slug, row.client_slug))
    gaps = sorted(gaps, key=lambda row: (row.issue_type, row.local_client_path, row.client_slug))
    return rows, gaps


def match_local_directory(
    record: SupabaseClientRecord,
    local_directories: list[LocalClientDirectory],
) -> tuple[LocalClientDirectory | None, str]:
    customer_id = digits_only(record.google_ads_customer_id)
    if customer_id:
        for local in local_directories:
            if local.google_ads_customer_id and local.google_ads_customer_id == customer_id:
                return local, "Matched by Google Ads customer ID."
    target_aliases = {
        normalize_key(record.company_name),
        normalize_key(domain_from_url(record.website_url)),
        normalize_key(scaffold_slug(record)),
    } - {""}
    matches = [local for local in local_directories if local.aliases & target_aliases]
    if not matches:
        return None, ""
    preferred = sorted(matches, key=lambda item: (item.client_slug != "fdl_xibalba", item.relative_path))[0]
    if len(matches) > 1:
        return preferred, "Duplicate local candidates; preferred canonical path."
    return preferred, "Matched by normalized name, website, or slug."


def registry_row_for_match(
    record: SupabaseClientRecord,
    local: LocalClientDirectory,
    status: str,
    visibility: str,
    notes: str,
    checked_at: str,
) -> RegistryRow:
    return RegistryRow(
        agency_slug=local.agency_slug or "arc",
        client_slug=local.client_slug,
        local_client_path=local.relative_path,
        local_layout=local.layout,
        directory_status=status,
        supabase_client_id=record.client_id,
        supabase_paid_ads_id=record.supabase_paid_ads_id,
        client_name=record.company_name or local.client_name,
        website_url=record.website_url or local.website_url,
        google_ads_customer_id=record.google_ads_customer_id or local.google_ads_customer_id,
        google_ads_login_customer_id=record.google_ads_login_customer_id or local.google_ads_login_customer_id,
        gads_status="configured" if record.google_ads_customer_id else "missing_customer_id",
        discord_channel_id=record.discord_channel_id,
        report_cadence="",
        gads_owner_identity="ARC",
        allowed_agents="proposal_only",
        api_visibility_status=visibility,
        mismatch_notes=notes,
        last_checked_at=checked_at,
    )


def registry_row_for_missing(
    record: SupabaseClientRecord,
    slug: str,
    path: str,
    status: str,
    visibility: str,
    notes: str,
    checked_at: str,
) -> RegistryRow:
    return RegistryRow(
        agency_slug="arc",
        client_slug=slug,
        local_client_path=path,
        local_layout="agency_client",
        directory_status=status,
        supabase_client_id=record.client_id,
        supabase_paid_ads_id=record.supabase_paid_ads_id,
        client_name=record.company_name,
        website_url=record.website_url,
        google_ads_customer_id=record.google_ads_customer_id,
        google_ads_login_customer_id=record.google_ads_login_customer_id,
        gads_status="configured" if record.google_ads_customer_id else "missing_customer_id",
        discord_channel_id=record.discord_channel_id,
        report_cadence="",
        gads_owner_identity="ARC",
        allowed_agents="proposal_only",
        api_visibility_status=visibility,
        mismatch_notes=notes,
        last_checked_at=checked_at,
    )


def registry_row_for_local_only(local: LocalClientDirectory, checked_at: str) -> RegistryRow:
    return RegistryRow(
        agency_slug=local.agency_slug,
        client_slug=local.client_slug,
        local_client_path=local.relative_path,
        local_layout=local.layout,
        directory_status="local_only",
        supabase_client_id="",
        supabase_paid_ads_id="",
        client_name=local.client_name,
        website_url=local.website_url,
        google_ads_customer_id=local.google_ads_customer_id,
        google_ads_login_customer_id=local.google_ads_login_customer_id,
        gads_status="local_only",
        discord_channel_id="",
        report_cadence="",
        gads_owner_identity="ARC",
        allowed_agents="proposal_only",
        api_visibility_status="not_checked",
        mismatch_notes="Local directory has no matching active Supabase end-client row.",
        last_checked_at=checked_at,
    )


def gap_row_for_missing(record: SupabaseClientRecord, slug: str, path: str) -> GapReportRow:
    website_arg = f" --website {shell_quote(normalize_website(record.website_url))}" if record.website_url else ""
    command = (
        f"python3 shared/rebuild/scaffold_client.py --agency arc --client {shell_quote(slug)} "
        f"--display-name {shell_quote(record.company_name)}{website_arg}"
    )
    return GapReportRow(
        issue_type="missing_local_directory",
        agency_slug="arc",
        client_slug=slug,
        local_client_path=path,
        supabase_client_id=record.client_id,
        client_name=record.company_name,
        website_url=record.website_url,
        google_ads_customer_id=record.google_ads_customer_id,
        notes="Create from template before campaign work.",
        suggested_command=command,
    )


def gap_row_for_local_only(local: LocalClientDirectory) -> GapReportRow:
    return GapReportRow(
        issue_type="local_without_active_supabase_row",
        agency_slug=local.agency_slug,
        client_slug=local.client_slug,
        local_client_path=local.relative_path,
        supabase_client_id="",
        client_name=local.client_name,
        website_url=local.website_url,
        google_ads_customer_id=local.google_ads_customer_id,
        notes="Keep active until reviewed; do not archive automatically.",
        suggested_command="",
    )


def normalize_website(value: str) -> str:
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value
    return f"https://{value.rstrip('/')}/"


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def write_registry_csv(rows: Iterable[RegistryRow], output: Path) -> None:
    validate_registry_columns()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REGISTRY_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def write_gap_report(rows: Iterable[GapReportRow], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(GapReportRow.__dataclass_fields__)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def validate_registry_columns() -> None:
    blocked = [column for column in REGISTRY_COLUMNS if any(pattern in column for pattern in SECRET_FIELD_PATTERNS)]
    if blocked:
        raise ValueError(f"Registry columns cannot include secret-like fields: {', '.join(blocked)}")


def load_live_registry() -> tuple[list[RegistryRow], list[GapReportRow]]:
    client = SupabaseRegistryClient.from_openbao()
    return build_registry(client.active_end_clients(), scan_local_client_directories())


def run_sync(args: argparse.Namespace) -> int:
    rows, gaps = load_live_registry()
    write_registry_csv(rows, Path(args.output))
    write_gap_report(gaps, Path(args.gap_report))
    print(json.dumps({"registry_rows": len(rows), "gap_rows": len(gaps)}, indent=2))
    return 0


def run_verify_api(_: argparse.Namespace) -> int:
    client = SupabaseRegistryClient.from_openbao()
    visibility = client.verify_openapi_paths()
    clients = client.active_end_clients()
    print(json.dumps({"paths": visibility, "active_end_client_count": len(clients)}, indent=2, sort_keys=True))
    return 0 if all(visibility.values()) else 1


def run_scaffold_missing(args: argparse.Namespace) -> int:
    rows, gaps = load_live_registry()
    missing = [gap for gap in gaps if gap.issue_type == "missing_local_directory"]
    payload = {
        "dry_run": bool(args.dry_run),
        "missing_count": len(missing),
        "commands": [gap.suggested_command for gap in missing],
        "registry_rows": len(rows),
    }
    print(json.dumps(payload, indent=2))
    if not args.dry_run:
        raise SystemExit("Only --dry-run is supported in this phase.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reconcile Supabase clients with local client directories.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync = subparsers.add_parser("sync")
    sync.add_argument("--output", default="clients/client_registry.csv")
    sync.add_argument("--gap-report", default="clients/client_directory_gap_report.csv")
    sync.set_defaults(func=run_sync)

    verify = subparsers.add_parser("verify-api")
    verify.set_defaults(func=run_verify_api)

    scaffold = subparsers.add_parser("scaffold-missing")
    scaffold.add_argument("--dry-run", action="store_true", required=True)
    scaffold.set_defaults(func=run_scaffold_missing)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
