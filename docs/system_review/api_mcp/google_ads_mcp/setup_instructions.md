# Google Ads MCP Server Setup Instructions

## ✅ Installation Complete!

## 🔑 Step 1: Get Google Ads API Credentials

### A. Google Cloud Console Setup

1. Go to: https://console.cloud.google.com

2. Create or select a project

3. Enable **Google Ads API**: APIs & Services → Library → Search "Google Ads API" → Click "Enable"

4. Create OAuth 2.0 Credentials: APIs & Services → Credentials → Create Credentials → OAuth client ID → Application type: **Desktop app** → Download credentials JSON → Extract `client_id` and `client_secret`

### B. Get Developer Token

1. Go to: https://ads.google.com

2. Tools & Settings → API Center

3. Copy your **Developer Token**

### C. Generate Refresh Token

Use Google OAuth Playground:

1. Go to: https://developers.google.com/oauthplayground

2. Settings (gear icon) → Check "Use your own OAuth credentials"

3. Enter your Client ID and Client Secret

4. Find "Google Ads API" → Select scopes

5. Authorize → Exchange authorization code → Copy refresh_token

## 📝 Step 2: Update google-ads.yaml

Edit $MCP_TOOLS_ROOT/servers/google_ads_mcp/google-ads.yaml with your actual credentials.

## ⚙️ Step 3: Configure MCP in Claude Code

The MCP configuration will be added to ~/.claude.json. After adding credentials, run: claude mcp list

You should see: google-ads: ✓ Connected

## 🧪 Step 4: Test the Server

Test manually:

cd $MCP_TOOLS_ROOT/servers/google_ads_mcp

source venv/bin/activate

python3 -m ads_mcp.server

## 📊 Available Tools

1. **`search`** - Query Google Ads data using GAQL

2. **`list_accessible_customers`** - List all accessible customer accounts

## 🎯 Example Usage in Claude

Once set up, try asking Claude:

- "List all my Google Ads accounts"

- "Show me campaigns with more than 100 clicks"

- "What's the performance of my Search campaigns this month?"

