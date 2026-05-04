"""Read-only Supabase access for the ARC client registry.

Credentials are fetched from OpenBao at runtime. This module never writes to
Supabase and never prints credential values.
"""

from __future__ import annotations

import json
import subprocess
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


OPENBAO_AUTH_FILE = "/etc/openbao/cron-scripts.env"
SUPABASE_URL_PATH = "tool-infra/supabase-url"
SUPABASE_SERVICE_KEY_PATH = "tool-infra/supabase-service-key"
REQUIRED_OPENAPI_PATHS = (
    "/clients",
    "/companies",
    "/client_information",
    "/client_paid_ads",
    "/gads_mutation_audit",
)


@dataclass(frozen=True)
class SupabaseClientRecord:
    client_id: str
    status: str
    relationship_type: str
    company_id: str
    company_name: str
    company_type: str
    website_url: str
    supabase_paid_ads_id: str
    google_ads_customer_id: str
    google_ads_login_customer_id: str
    discord_channel_id: str

    @property
    def is_active_end_client(self) -> bool:
        return (
            self.status == "active"
            and self.relationship_type == "client"
            and self.company_type == "client"
        )


class SupabaseReadError(RuntimeError):
    """Raised when a read-only Supabase request fails."""


def read_openbao_secret(path: str, *, auth_file: str = OPENBAO_AUTH_FILE, ssh_host: str = "zeroclaw") -> str:
    """Read one OpenBao KV value through the VPS wrapper without writing files."""

    remote = (
        "source /opt/openbao-wrapper/lib.sh && "
        f"export BAO_AUTH_FILE={auth_file} && "
        "bao_auth >/dev/null && "
        "python3 - "
    )
    script = f"""
import json
import os
import sys
import urllib.request

url = os.environ.get("BAO_ADDR", "http://127.0.0.1:8200").rstrip("/") + "/v1/secret/data/{path}"
req = urllib.request.Request(url, headers={{"X-Vault-Token": os.environ["BAO_TOKEN"]}})
with urllib.request.urlopen(req, timeout=30) as resp:
    payload = json.loads(resp.read().decode("utf-8"))
value = payload.get("data", {{}}).get("data", {{}}).get("value", "")
sys.stdout.write(value)
"""
    result = subprocess.run(
        ["/usr/bin/ssh", ssh_host, remote],
        input=script,
        check=True,
        capture_output=True,
        text=True,
    )
    value = result.stdout.strip()
    if not value:
        raise SupabaseReadError(f"OpenBao path returned an empty value: {path}")
    return value


class SupabaseRegistryClient:
    def __init__(self, url: str, service_key: str) -> None:
        self.url = url.rstrip("/")
        self.service_key = service_key

    @classmethod
    def from_openbao(cls) -> "SupabaseRegistryClient":
        return cls(
            read_openbao_secret(SUPABASE_URL_PATH),
            read_openbao_secret(SUPABASE_SERVICE_KEY_PATH),
        )

    def get_json(self, path: str) -> Any:
        req = urllib.request.Request(
            self.url + path,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.service_key}",
                "apikey": self.service_key,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else None
        except Exception as exc:  # pragma: no cover - exercised in live smoke use
            raise SupabaseReadError(f"Supabase read failed for {path}: {exc}") from exc

    def active_client_rows(self) -> list[dict[str, Any]]:
        return self.get_json(
            "/rest/v1/clients?"
            "select=id,status,relationship_type,company_id,google_ads_account_id,login_customer_id,discord_channel_id"
            "&status=eq.active&relationship_type=eq.client&limit=1000"
        )

    def companies_by_id(self, company_ids: set[str]) -> dict[str, dict[str, Any]]:
        if not company_ids:
            return {}
        encoded = urllib.parse.quote("(" + ",".join(sorted(company_ids)) + ")", safe="(),-")
        rows = self.get_json(
            f"/rest/v1/companies?select=id,company_name,company_type,website&id=in.{encoded}&limit=1000"
        )
        return {row.get("id", ""): row for row in rows}

    def paid_ads_by_client_id(self) -> dict[str, dict[str, Any]]:
        rows = self.get_json("/rest/v1/client_paid_ads?select=*&limit=1000")
        return {row.get("client_id", ""): row for row in rows if row.get("client_id")}

    def active_end_clients(self) -> list[SupabaseClientRecord]:
        client_rows = self.active_client_rows()
        companies = self.companies_by_id({row.get("company_id", "") for row in client_rows if row.get("company_id")})
        paid_ads = self.paid_ads_by_client_id()
        records = [
            to_supabase_client_record(row, companies.get(row.get("company_id", ""), {}), paid_ads.get(row.get("id", ""), {}))
            for row in client_rows
        ]
        return [record for record in records if record.is_active_end_client]

    def verify_openapi_paths(self) -> dict[str, bool]:
        openapi = self.get_json("/rest/v1/")
        paths = openapi.get("paths", {}) if isinstance(openapi, dict) else {}
        return {path: path in paths for path in REQUIRED_OPENAPI_PATHS}


def first_value(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def to_supabase_client_record(
    client_row: dict[str, Any],
    company_row: dict[str, Any],
    paid_ads_row: dict[str, Any],
) -> SupabaseClientRecord:
    return SupabaseClientRecord(
        client_id=first_value(client_row.get("id")),
        status=first_value(client_row.get("status")),
        relationship_type=first_value(client_row.get("relationship_type")),
        company_id=first_value(client_row.get("company_id")),
        company_name=first_value(company_row.get("company_name")),
        company_type=first_value(company_row.get("company_type")),
        website_url=first_value(company_row.get("website")),
        supabase_paid_ads_id=first_value(paid_ads_row.get("id")),
        google_ads_customer_id=digits_only(
            first_value(
                client_row.get("google_ads_account_id"),
                paid_ads_row.get("google_ads_customer_id"),
                paid_ads_row.get("google_ads_account_id"),
            )
        ),
        google_ads_login_customer_id=digits_only(
            first_value(
                client_row.get("login_customer_id"),
                paid_ads_row.get("google_ads_login_customer_id"),
                paid_ads_row.get("login_customer_id"),
            )
        ),
        discord_channel_id=first_value(client_row.get("discord_channel_id")),
    )


def digits_only(value: str) -> str:
    return "".join(character for character in value if character.isdigit())
