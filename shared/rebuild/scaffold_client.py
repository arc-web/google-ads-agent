#!/usr/bin/env python3
"""Create a new Google_Ads_Agent client directory from the template."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = ROOT / "templates" / "client_template"
CLIENTS_DIR = ROOT / "clients"


def slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        raise ValueError("Slug cannot be empty")
    return normalized


def replace_placeholders(path: Path, replacements: dict[str, str]) -> None:
    if path.is_dir():
        return
    if path.suffix.lower() not in {".md", ".yaml", ".yml", ".csv", ".txt"}:
        return
    text = path.read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace(key, value)
    path.write_text(text, encoding="utf-8")


def materialize_template_filenames(target: Path) -> None:
    """Rename copied *_template files to their active client filenames."""
    for path in sorted(target.rglob("*_template.*")):
        active_name = path.name.replace("_template", "", 1)
        path.rename(path.with_name(active_name))


def scaffold_client(
    agency: str,
    client: str,
    display_name: str | None,
    website: str | None,
    clients_dir: Path = CLIENTS_DIR,
) -> Path:
    agency_slug = slug(agency)
    client_slug = slug(client)
    target = clients_dir / agency_slug / client_slug

    if target.exists():
        raise FileExistsError(f"Client directory already exists: {target}")
    if not TEMPLATE_DIR.exists():
        raise FileNotFoundError(f"Template directory missing: {TEMPLATE_DIR}")

    shutil.copytree(TEMPLATE_DIR, target)

    replacements = {
        "{{AGENCY_SLUG}}": agency_slug,
        "{{CLIENT_SLUG}}": client_slug,
        "{{CLIENT_DISPLAY_NAME}}": display_name or client.replace("_", " ").title(),
        "{{WEBSITE_URL}}": website or "https://example.com/",
    }

    for path in target.rglob("*"):
        replace_placeholders(path, replacements)

    materialize_template_filenames(target)

    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Google_Ads_Agent client scaffold")
    parser.add_argument("--agency", required=True, help="Agency or workspace slug")
    parser.add_argument("--client", required=True, help="Client slug")
    parser.add_argument("--display-name", help="Human-readable client name")
    parser.add_argument("--website", help="Client website URL")
    parser.add_argument("--clients-dir", type=Path, default=CLIENTS_DIR, help="Root clients directory")
    args = parser.parse_args()

    target = scaffold_client(args.agency, args.client, args.display_name, args.website, clients_dir=args.clients_dir)
    print(f"Created client scaffold: {target}")
    print("Next: add account export to campaigns/account_export.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
