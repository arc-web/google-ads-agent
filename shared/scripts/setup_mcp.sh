#!/bin/bash

set -euo pipefail

cat <<'MESSAGE'
Google Ads MCP setup is inactive in this workflow.

Current Google Ads Agent cleanup keeps API and MCP automation salvage-only.
This script intentionally does not install packages, create virtual environments,
write credentials, edit Cursor or Claude configuration, or contact Google Ads.

Active workflow:
- generate Google Ads Editor staging files
- validate with shared/rebuild/staging_validator.py
- keep API upload off unless explicitly activated by the user
MESSAGE

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  exit 0
fi

exit 2
