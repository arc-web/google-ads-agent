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
    print("   cd $MCP_TOOLS_ROOT/servers/google_ads_mcp")
    print("   source venv/bin/activate")
    print("   pip install git+https://github.com/google-marketing-solutions/google_ads_mcp.git")
except Exception as e:
    print(f"❌ Error: {e}")

