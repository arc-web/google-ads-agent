# Quick Start: Automated Credential Collection

## Quick Setup

Run the setup script to install dependencies:

```bash
cd $MCP_TOOLS_ROOT/servers/google_ads_mcp
bash setup_automation.sh
```

This will:
- Activate/create virtual environment
- Install Playwright
- Install Chromium browser

## Run the Script

```bash
python3 collect_credentials_automated.py
```

Or if using venv:

```bash
source venv/bin/activate
python3 collect_credentials_automated.py
```

## What Happens

The script will:

1. **Open a browser** (non-headless, so you can see what's happening)
2. **Navigate to Google Cloud Console** and guide you through:
   - Selecting your project
   - Enabling Google Ads API
   - Creating OAuth credentials
   - Extracting Client ID and Secret

3. **Navigate to Google Ads** and guide you through:
   - Selecting your MCC account (211-993-1898)
   - Opening API Center
   - Extracting Developer Token

4. **Navigate to OAuth Playground** and guide you through:
   - Configuring with your credentials
   - Authorizing Google Ads API scope
   - Exchanging for Refresh Token

5. **Update google-ads.yaml** automatically with all credentials

## Manual Steps You'll Need to Do

The script will pause and prompt you for these manual steps:

1. **Select Google Cloud Project** - Choose your project from the dropdown
2. **Create OAuth Credentials** - Click buttons to create credentials
3. **Configure OAuth Consent Screen** - If prompted, fill out the form
4. **Select MCC Account** - Choose account 211-993-1898 if prompted
5. **Sign In** - Sign in to Google accounts when prompted
6. **Approve Permissions** - Approve OAuth permissions
7. **Paste Credentials** - If auto-extraction fails, paste manually

## Troubleshooting

### "playwright not found"
```bash
pip install playwright
playwright install chromium
```

### Script can't find elements
- The script will prompt you to navigate manually
- Press ENTER when you're on the correct page
- The script will continue from there

### Credentials not extracted automatically
- The script will ask you to paste them manually
- Copy from the browser and paste when prompted

### Browser closes unexpectedly
- Run the script again
- It will start from the beginning
- You may need to re-authenticate

## After Collection

Once the script completes:

1. **Verify credentials**:
   ```bash
   python3 test_server.py
   ```

2. **Test MCP connection**:
   ```bash
   claude mcp list
   ```
   Should show: `google-ads: ✓ Connected`

3. **Run test suite**:
   ```bash
   bash test_mcc_integration.sh
   ```

## Alternative: Manual Collection

If automation doesn't work, see:
- `GET_CREDENTIALS_GUIDE.md` - Step-by-step manual guide
- `CREDENTIALS_COLLECTION_PLAN.md` - Quick reference

