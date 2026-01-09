#!/bin/bash

set -e

echo "🚀 Starting Google Ads MCP Server Setup..."

MCP_DIR="/Users/home/aimacpro/7_tools/mcp_tools/servers/google_ads_mcp"

mkdir -p "$MCP_DIR"

cd "$MCP_DIR"

echo "✅ Created: $MCP_DIR"

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')

echo "   Found Python: $PYTHON_VERSION"

if ! command -v uv &> /dev/null; then

    echo "   Installing uv..."

    curl -LsSf https://astral.sh/uv/install.sh | sh

    export PATH="$HOME/.cargo/bin:$PATH"

    echo "✅ uv installed"

else

    echo "✅ uv already installed"

fi

if [ ! -d "venv" ]; then

    python3 -m venv venv

    echo "✅ Virtual environment created"

else

    echo "✅ Virtual environment already exists"

fi

source venv/bin/activate

VENV_PYTHON="$MCP_DIR/venv/bin/python"

ACTUAL_PYTHON_VERSION=$($VENV_PYTHON --version 2>&1 | awk '{print $2}')

echo "✅ Using venv Python: $ACTUAL_PYTHON_VERSION"

pip install --upgrade pip

echo "📥 Installing Google Ads MCP Server..."

if pip install git+https://github.com/google-marketing-solutions/google_ads_mcp.git; then

    echo "✅ Google Ads MCP Server installed"

else

    echo "❌ Installation failed!"

    exit 1

fi

if python3 -c "import ads_mcp" 2>/dev/null; then

    echo "✅ Package verified - ads_mcp is importable"

else

    echo "⚠️  Warning: Could not verify package import"

fi

cat > google-ads.yaml << 'EOF'

client_id: YOUR_CLIENT_ID_HERE

client_secret: YOUR_CLIENT_SECRET_HERE

refresh_token: YOUR_REFRESH_TOKEN_HERE

developer_token: YOUR_DEVELOPER_TOKEN_HERE

login_customer_id: YOUR_LOGIN_CUSTOMER_ID_HERE

EOF

echo "✅ Created: google-ads.yaml"

cat > SETUP_INSTRUCTIONS.md << 'EOF'

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

Edit /Users/home/aimacpro/7_tools/mcp_tools/servers/google_ads_mcp/google-ads.yaml with your actual credentials.

## ⚙️ Step 3: Configure MCP in Claude Code

The MCP configuration will be added to .cursor/mcp.json. After adding credentials, restart Cursor to load MCP servers.

You should see: google-ads: ✓ Connected

## 🧪 Step 4: Test the Server

Test manually:

cd /Users/home/aimacpro/7_tools/mcp_tools/servers/google_ads_mcp

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

EOF

echo "✅ Created: SETUP_INSTRUCTIONS.md"

CURSOR_CONFIG=".cursor/mcp.json"

BACKUP_CONFIG="${CURSOR_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

if [ -f "$CURSOR_CONFIG" ]; then

    cp "$CURSOR_CONFIG" "$BACKUP_CONFIG"

    echo "✅ Backed up existing config to: $BACKUP_CONFIG"

else

    mkdir -p "$(dirname "$CURSOR_CONFIG")"

    echo '{}' > "$CURSOR_CONFIG"

fi

if grep -q '"google-ads"' "$CURSOR_CONFIG" 2>/dev/null; then

    echo "⚠️  Google Ads MCP already configured in $CURSOR_CONFIG"

else

    python3 << PYTHON_SCRIPT

import json

import os

import sys

config_path = ".cursor/mcp.json"

mcp_dir = "/Users/home/aimacpro/7_tools/mcp_tools/servers/google_ads_mcp"

venv_python = f"{mcp_dir}/venv/bin/python"

if not os.path.exists(venv_python):

    print(f"❌ Error: venv Python not found at {venv_python}")

    sys.exit(1)

try:

    with open(config_path, 'r') as f:

        config = json.load(f)

except (FileNotFoundError, json.JSONDecodeError):

    config = {}

if "projects" not in config:

    config["projects"] = {}

project_path = "/Users/home/aimacpro"

if project_path not in config["projects"]:

    config["projects"][project_path] = {}

if "mcpServers" not in config["projects"][project_path]:

    config["projects"][project_path]["mcpServers"] = {}

config["projects"][project_path]["mcpServers"]["google-ads"] = {

    "command": venv_python,

    "args": ["-m", "ads_mcp.server"],

    "env": {"GOOGLE_ADS_CONFIG_PATH": f"{mcp_dir}/google-ads.yaml"}

}

with open(config_path, 'w') as f:

    json.dump(config, f, indent=2)

print(f"✅ Updated {config_path}")

print(f"   Using venv Python: {venv_python}")

PYTHON_SCRIPT

    if [ $? -eq 0 ]; then

        echo "✅ MCP configuration updated"

    else

        echo "❌ Failed to update MCP configuration"

    fi

fi

cat > test_server.py << 'EOF'

#!/usr/bin/env python3

import sys

import os

import subprocess

venv_dir = os.path.join(os.path.dirname(__file__), 'venv')

if os.path.exists(venv_dir):

    python_exec = os.path.join(venv_dir, 'bin', 'python')

    if not os.path.exists(python_exec):

        for py_ver in ['python3.12', 'python3.11', 'python3']:

            alt_python = os.path.join(venv_dir, 'bin', py_ver)

            if os.path.exists(alt_python):

                python_exec = alt_python

                break

    site_packages = None

    for root, dirs, files in os.walk(os.path.join(venv_dir, 'lib')):

        if 'site-packages' in dirs:

            site_packages = os.path.join(root, 'site-packages')

            break

    if site_packages:

        sys.path.insert(0, site_packages)

else:

    python_exec = 'python3'

try:

    from ads_mcp.server import create_server

    import asyncio

    async def test():

        print("🔍 Testing Google Ads MCP Server...")

        print("")

        try:

            server = await create_server()

            tools = await server.list_tools()

            print(f"✅ Server initialized successfully!")

            print(f"📊 Available tools: {len(tools)}")

            print("")

            for tool in tools:

                print(f"   • {tool.name}")

                print(f"     {tool.description}")

                print("")

        except Exception as e:

            print(f"❌ Error: {e}")

            print("")

            print("💡 Make sure you've:")

            print("   1. Filled in google-ads.yaml with your credentials")

            print("   2. Installed all dependencies")

            print("   3. Have valid Google Ads API access")

    asyncio.run(test())

except ImportError as e:

    print(f"❌ Import error: {e}")

    print("")

    print("💡 Try running:")

    print("   cd /Users/home/aimacpro/7_tools/mcp_tools/servers/google_ads_mcp")

    print("   source venv/bin/activate")

    print("   pip install git+https://github.com/google-marketing-solutions/google_ads_mcp.git")

except Exception as e:

    print(f"❌ Error: {e}")

EOF

chmod +x test_server.py

echo "✅ Created: test_server.py"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "✅ SETUP COMPLETE!"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""

echo "📁 Installation Directory: $MCP_DIR"

echo ""

echo "📝 Next Steps:"

echo "   1. Edit google-ads.yaml with your credentials:"

echo "      nano $MCP_DIR/google-ads.yaml"

echo ""

echo "   2. Get your credentials:"

echo "      - Google Cloud Console → OAuth credentials"

echo "      - Google Ads → Developer Token"

echo "      - Generate Refresh Token via OAuth Playground"

echo ""

echo "   3. Test the server:"

echo "      cd $MCP_DIR"

echo "      source venv/bin/activate"

echo "      python3 test_server.py"

echo ""

echo "   4. Restart Claude Code and verify:"

echo "      claude mcp list"

echo ""

echo "📚 Full instructions: $MCP_DIR/SETUP_INSTRUCTIONS.md"

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

