#!/bin/bash

# Setup script for automated credential collection
# Installs Playwright and browser dependencies

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Setting up Automated Credential Collection"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✅ Virtual environment found"
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found"
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created"
fi

# Install Playwright
echo ""
echo "Installing Playwright..."
pip install -q playwright

# Install browser
echo ""
echo "Installing Chromium browser..."
playwright install chromium

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "You can now run:"
echo "  python3 collect_credentials_automated.py"
echo ""

