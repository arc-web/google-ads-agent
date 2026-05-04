"""Shared naming helpers for generated Google Ads Editor CSV files."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path


CSV_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


def slugify_client(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        raise ValueError("Client name is required for generated CSV filenames.")
    return normalized


def normalize_timestamp(value: str | None = None) -> str:
    if not value:
        return datetime.now(timezone.utc).strftime(CSV_TIMESTAMP_FORMAT)
    cleaned = value.strip()
    for fmt in ("%Y%m%d_%H%M%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(cleaned, fmt).strftime(CSV_TIMESTAMP_FORMAT)
        except ValueError:
            continue
    raise ValueError("CSV timestamp must use YYYYMMDD_HHMMSS, YYYY-MM-DDTHH:MM:SS, or YYYY-MM-DD HH:MM:SS.")


def generated_csv_name(client: str, purpose: str, timestamp: str | None = None) -> str:
    client_slug = slugify_client(client)
    purpose_slug = slugify_client(purpose)
    return f"{client_slug}_{purpose_slug}_{normalize_timestamp(timestamp)}.csv"


def generated_csv_path(output_dir: str | Path, client: str, purpose: str, timestamp: str | None = None) -> Path:
    return Path(output_dir) / generated_csv_name(client, purpose, timestamp)


def validate_generated_csv_name(path: str | Path, client: str) -> None:
    csv_path = Path(path)
    client_slug = slugify_client(client)
    pattern = re.compile(rf"^{re.escape(client_slug)}_[a-z0-9_]+_\d{{8}}_\d{{6}}\.csv$")
    if not pattern.match(csv_path.name):
        raise ValueError(
            "Generated CSV filename must include client slug and date/time, "
            f"for example {client_slug}_google_ads_editor_staging_YYYYMMDD_HHMMSS.csv."
        )
