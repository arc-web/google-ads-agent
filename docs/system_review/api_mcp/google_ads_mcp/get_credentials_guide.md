# Google Ads API Credentials - Step-by-Step Guide

## Overview

This guide walks you through getting all 4 required credentials for Google Ads MCP:
1. **Client ID** & **Client Secret** (from Google Cloud Console)
2. **Developer Token** (from Google Ads)
3. **Refresh Token** (from OAuth Playground)
4. **MCC ID** (211-993-1898) - Already configured ✅

---

## What You Need

| Credential | Where to Get | Status |
|------------|--------------|--------|
| `client_id` | Google Cloud Console → Credentials | ⚠️ Need to get |
| `client_secret` | Google Cloud Console → Credentials | ⚠️ Need to get |
| `developer_token` | Google Ads → API Center | ⚠️ Need to get |
| `refresh_token` | OAuth Playground | ⚠️ Need to get |
| `login_customer_id` | Your MCC account | ✅ Already set: 2119931898 |

---

## Part 1: Get Client ID & Client Secret (Google Cloud Console)

### Step-by-Step Browser Automation Plan

**URL**: https://console.cloud.google.com

#### Step 1: Navigate to Google Cloud Console
```
1. Go to: https://console.cloud.google.com
2. Sign in with your Google account
3. Select or create a project
```

#### Step 2: Enable Google Ads API
```
1. Click "APIs & Services" in left menu
2. Click "Library"
3. Search for "Google Ads API"
4. Click on "Google Ads API"
5. Click "Enable" button
```

#### Step 3: Create OAuth Credentials
```
1. Go to: APIs & Services → Credentials
2. Click "+ CREATE CREDENTIALS" button
3. Select "OAuth client ID"
4. If prompted, configure OAuth consent screen first:
   - User Type: External (or Internal if using Google Workspace)
   - App name: "Google Ads MCP"
   - User support email: Your email
   - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Add "https://www.googleapis.com/auth/adwords"
   - Click "Save and Continue"
   - Test users: Add your email (if External)
   - Click "Save and Continue"
   - Click "Back to Dashboard"
5. Back at Credentials page:
   - Application type: Select "Desktop app"
   - Name: "Google Ads MCP Desktop Client"
   - Click "Create"
6. A popup will show your credentials:
   - Copy "Your Client ID" → This is `client_id`
   - Copy "Your Client Secret" → This is `client_secret`
   - Click "OK"
```

**Browser Automation Selectors**:
- APIs & Services menu: `text="APIs & Services"`
- Library link: `text="Library"`
- Search box: `input[placeholder*="Search"]`
- Enable button: `button:has-text("Enable")`
- Credentials link: `text="Credentials"`
- Create Credentials button: `button:has-text("CREATE CREDENTIALS")`
- OAuth client ID option: `text="OAuth client ID"`
- Desktop app option: `text="Desktop app"`

---

## Part 2: Get Developer Token (Google Ads)

### Step-by-Step Browser Automation Plan

**URL**: https://ads.google.com

#### Step 1: Navigate to Google Ads
```
1. Go to: https://ads.google.com
2. Sign in with your Google account
3. Select your MCC account (211-993-1898) if prompted
```

#### Step 2: Access API Center
```
1. Click the tools icon (wrench) in top right
2. Under "Setup" section, click "API Center"
   OR
   Direct URL: https://ads.google.com/aw/apicenter
```

#### Step 3: Get Developer Token
```
1. Look for "Developer Token" section
2. If you don't have one:
   - Click "Apply for access" or "Get started"
   - Fill out the application form
   - Wait for approval (can take 24-48 hours)
3. If you already have one:
   - Copy the Developer Token
   - This is your `developer_token`
```

**Browser Automation Selectors**:
- Tools icon: `button[aria-label*="Tools"]` or `svg[aria-label*="Tools"]`
- API Center link: `text="API Center"`
- Developer Token section: `text="Developer Token"`
- Copy button: `button:has-text("Copy")` or `button[aria-label*="Copy"]`

---

## Part 3: Get Refresh Token (OAuth Playground)

### Step-by-Step Browser Automation Plan

**URL**: https://developers.google.com/oauthplayground

#### Step 1: Configure OAuth Playground
```
1. Go to: https://developers.google.com/oauthplayground
2. Click the gear icon (Settings) in top right
3. Check "Use your own OAuth credentials"
4. Enter your Client ID (from Part 1)
5. Enter your Client Secret (from Part 1)
6. Click "Close"
```

#### Step 2: Select Google Ads API Scopes
```
1. In the left panel, find "Google Ads API"
2. Expand it
3. Select: "https://www.googleapis.com/auth/adwords"
4. Click "Authorize APIs" button
```

#### Step 3: Authorize Access
```
1. You'll be redirected to Google sign-in
2. Sign in with your Google account
3. Review permissions
4. Click "Allow" or "Continue"
5. You'll be redirected back to OAuth Playground
```

#### Step 4: Exchange for Refresh Token
```
1. Click "Exchange authorization code for tokens" button
2. You'll see tokens displayed:
   - Access Token (temporary)
   - Refresh Token (permanent) ← This is what you need!
3. Copy the "Refresh token" value
   - This is your `refresh_token`
```

**Browser Automation Selectors**:
- Settings gear: `button[aria-label*="Settings"]` or `svg[aria-label*="Settings"]`
- Use own credentials checkbox: `input[type="checkbox"]` near "Use your own OAuth credentials"
- Client ID input: `input[name*="client_id"]` or `input[placeholder*="Client ID"]`
- Client Secret input: `input[name*="client_secret"]` or `input[type="password"]`
- Google Ads API scope: `text="https://www.googleapis.com/auth/adwords"`
- Authorize button: `button:has-text("Authorize")`
- Exchange button: `button:has-text("Exchange")`
- Refresh token field: Look for "Refresh token" label

---

## Part 4: Update Configuration File

Once you have all credentials:

### Update google-ads.yaml

**File**: `$MCP_TOOLS_ROOT/servers/google_ads_mcp/google-ads.yaml`

```yaml
client_id: <paste-your-client-id-here>
client_secret: <paste-your-client-secret-here>
refresh_token: <paste-your-refresh-token-here>
developer_token: <paste-your-developer-token-here>
login_customer_id: 2119931898
```

---

## Browser Automation Script Plan

Here's a high-level plan for automating credential collection:

### Phase 1: Google Cloud Console
1. Navigate to console.cloud.google.com
2. Select/create project
3. Enable Google Ads API
4. Create OAuth credentials
5. Extract client_id and client_secret

### Phase 2: Google Ads
1. Navigate to ads.google.com
2. Access API Center
3. Extract developer_token

### Phase 3: OAuth Playground
1. Navigate to oauthplayground
2. Configure with client credentials
3. Authorize Google Ads API scope
4. Exchange for refresh_token
5. Extract refresh_token

### Phase 4: Update Config
1. Read google-ads.yaml
2. Replace placeholder values
3. Save updated config

---

## Manual Steps (If Browser Automation Fails)

If browser automation encounters issues, here are manual steps:

### Quick Reference URLs:
- **Google Cloud Console**: https://console.cloud.google.com
- **Google Ads**: https://ads.google.com
- **API Center Direct**: https://ads.google.com/aw/apicenter
- **OAuth Playground**: https://developers.google.com/oauthplayground

### What to Look For:

**Client ID & Secret**:
- Format: Long alphanumeric strings
- Location: Google Cloud Console → Credentials → OAuth 2.0 Client IDs
- Example format: `123456789-abcdefghijklmnop.apps.googleusercontent.com`

**Developer Token**:
- Format: Usually 10+ character alphanumeric
- Location: Google Ads → Tools → API Center
- Example format: `AbCdEfGhIjKlMnOpQrSt`

**Refresh Token**:
- Format: Long alphanumeric string
- Location: OAuth Playground after authorization
- Example format: `1//0abcdefghijklmnopqrstuvwxyz...`

---

## Verification Steps

After updating credentials:

1. **Test Configuration**:
   ```bash
   cd $MCP_TOOLS_ROOT/servers/google_ads_mcp
   python3 test_server.py
   ```

2. **Check MCP Connection**:
   ```bash
   claude mcp list
   ```
   Should show: `google-ads: ✓ Connected`

3. **Test Account Access**:
   Use MCP tool `list_accessible_customers` to verify MCC access

---

## Troubleshooting

### "Invalid credentials" error
- Double-check all values are copied correctly
- Ensure no extra spaces or newlines
- Verify client_id and client_secret match

### "Developer token not approved"
- Developer tokens need approval (24-48 hours)
- Check API Center for approval status
- Use test account if available

### "Refresh token expired"
- Refresh tokens can expire if not used
- Re-generate via OAuth Playground
- Consider using service account for production

### "MCC access denied"
- Verify login_customer_id is correct (2119931898)
- Ensure OAuth account has access to MCC
- Check MCC account permissions

---

## Security Notes

⚠️ **Important**:
- Never commit credentials to git
- Keep `google-ads.yaml` in `.gitignore`
- Use environment variables for production
- Rotate credentials periodically
- Use service accounts for automated systems

---

## Next Steps

Once credentials are configured:

1. Run test suite: `bash test_mcc_integration.sh`
2. Test MCP connection
3. Verify MCC account access
4. Test apps with real data
5. Execute workflows

See `TESTING_GUIDE.md` for detailed testing instructions.

