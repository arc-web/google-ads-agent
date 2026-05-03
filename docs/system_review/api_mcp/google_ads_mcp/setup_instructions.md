# Google Ads MCP Server - Credential Setup

## Where credentials live

**Never** create a `google-ads.yaml` file. Credentials are stored in OpenBao and fetched at runtime.

```
secret/tool-infra/google-ads-client-id
secret/tool-infra/google-ads-client-secret
secret/tool-infra/google-ads-refresh-token
secret/tool-infra/google-ads-developer-token
secret/tool-infra/google-ads-login-customer-id
```

## For agents / cron scripts (OpenBao AppRole)

Source `/opt/openbao-wrapper/lib.sh`, call `bao_auth`, then `bao_get`:

```bash
source /opt/openbao-wrapper/lib.sh
bao_auth
export CLIENT_ID=$(bao_get /tool-infra google-ads-client-id)
export CLIENT_SECRET=$(bao_get /tool-infra google-ads-client-secret)
export REFRESH_TOKEN=$(bao_get /tool-infra google-ads-refresh-token)
export DEV_TOKEN=$(bao_get /tool-infra google-ads-developer-token)
export LOGIN_ID=$(bao_get /tool-infra google-ads-login-customer-id)
```

See `/opt/openbao-wrapper/google-ads-report-v2.sh` for a working reference.

Load in Python via dict (no yaml file needed):

```python
from google.ads.googleads.client import GoogleAdsClient
import os

client = GoogleAdsClient.load_from_dict({
    "client_id": os.environ["CLIENT_ID"],
    "client_secret": os.environ["CLIENT_SECRET"],
    "refresh_token": os.environ["REFRESH_TOKEN"],
    "developer_token": os.environ["DEV_TOKEN"],
    "login_customer_id": os.environ["LOGIN_ID"],
    "use_proto_plus": True,
})
```

## For humans / local dev (1Password)

Get credentials from 1Password ARC vault. Use `op run` to inject into environment without writing to disk:

```bash
op run --env-file=.env.1p -- python3 your_script.py
```

`.env.1p` uses vault references only (no real values):
```
CLIENT_ID=op://ARC/Google Ads API/client_id
REFRESH_TOKEN=op://ARC/Google Ads API/refresh_token
```

## Updating credentials in OpenBao

```bash
# SSH to VPS, then:
ROOT_TOKEN=$(op item get hl23px33remaz2xecl5ecvvaem --vault ARC --fields root_token --reveal)
VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=$ROOT_TOKEN \
  bao kv put secret/tool-infra/google-ads-refresh-token value="NEW_TOKEN"
```

## Available tools

- `search` - GAQL queries against Google Ads data
- `list_accessible_customers` - list all accessible customer accounts

## MCC account

Login customer ID: `2119931898` (MCC - manages all client accounts)
