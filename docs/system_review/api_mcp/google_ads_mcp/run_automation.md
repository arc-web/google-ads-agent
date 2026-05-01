# Running the Automation Script

## Quick Run

The automation script has been set up and is ready to run. Since it requires interactive browser sessions for sign-ins and approvals, here's how to use it:

### Option 1: Run Directly (Recommended)

```bash
cd $MCP_TOOLS_ROOT/servers/google_ads_mcp
source venv/bin/activate
python3 collect_credentials_automated.py
```

This will:
1. Open a browser window automatically
2. Navigate through each step
3. Pause and wait for you to:
   - Select your Google Cloud project
   - Sign in to Google accounts
   - Approve OAuth permissions
   - Create credentials (click buttons)
4. Extract credentials automatically
5. Update `google-ads.yaml` when done

### Option 2: Run in Background

If you want to run it in the background:

```bash
cd $MCP_TOOLS_ROOT/servers/google_ads_mcp
source venv/bin/activate
nohup python3 collect_credentials_automated.py > automation.log 2>&1 &
```

Then monitor the log:
```bash
tail -f automation.log
```

## What to Expect

### Part 1: Google Cloud Console
- Browser opens to console.cloud.google.com
- Script navigates to APIs & Services
- **You need to**: Select your project
- Script enables Google Ads API
- Script navigates to Credentials
- **You need to**: Click "CREATE CREDENTIALS" → "OAuth client ID"
- **You need to**: Fill consent screen if prompted
- **You need to**: Select "Desktop app" and create
- Script extracts Client ID and Secret

### Part 2: Google Ads
- Browser navigates to ads.google.com
- **You need to**: Select MCC account (211-993-1898) if prompted
- Script navigates to API Center
- Script extracts Developer Token

### Part 3: OAuth Playground
- Browser navigates to oauthplayground
- Script configures with your credentials
- Script selects Google Ads API scope
- **You need to**: Click "Authorize APIs"
- **You need to**: Sign in and approve permissions
- Script exchanges for tokens
- Script extracts Refresh Token

### Part 4: Update Config
- Script automatically updates `google-ads.yaml`
- All credentials saved!

## Interactive Prompts

The script will pause and show prompts like:

```
⏸️  MANUAL STEP REQUIRED:
   Please select your project in the project selector
   Press ENTER when ready to continue...
```

When you see these:
1. Complete the action in the browser
2. Press ENTER in the terminal to continue

## Troubleshooting

### Browser Doesn't Open
- Check if Playwright is installed: `playwright --version`
- Reinstall: `bash setup_automation.sh`

### Script Stuck Waiting
- Check the browser window - it may be waiting for your action
- Complete the step in the browser
- Press ENTER in terminal

### Credentials Not Extracted
- Script will ask you to paste manually
- Copy from browser and paste when prompted

### Need to Restart
- Press Ctrl+C to stop
- Run the script again
- It will start from the beginning

## After Completion

Once the script completes:

1. **Verify credentials are saved**:
   ```bash
   cat google-ads.yaml
   ```
   Should show all credentials (not placeholders)

2. **Test the setup**:
   ```bash
   python3 test_server.py
   ```

3. **Test MCP connection**:
   ```bash
   claude mcp list
   ```
   Should show: `google-ads: ✓ Connected`

## Status

✅ Script created and ready
✅ Dependencies installed
✅ MCC ID configured: 2119931898
⏸️  Ready for you to run and interact with browser

---

**To start collecting credentials, run:**
```bash
cd $MCP_TOOLS_ROOT/servers/google_ads_mcp
source venv/bin/activate
python3 collect_credentials_automated.py
```

