#!/usr/bin/env python3
"""
Automated Google Ads Credentials Collection Script
Uses Playwright to automate credential collection from Google Cloud Console,
Google Ads, and OAuth Playground.
"""

import asyncio
import re
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser
from typing import Dict, Optional, Tuple

# Configuration
CONFIG_FILE = Path(__file__).parent / "google-ads.yaml"
MCC_ID = "2119931898"

class CredentialCollector:
    def __init__(self):
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self.developer_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def initialize_browser(self, headless: bool = False):
        """Initialize Playwright browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=headless)
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        self.page = await context.new_page()
        print("✅ Browser initialized")

    async def close_browser(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            print("✅ Browser closed")

    async def get_oauth_credentials(self) -> Tuple[str, str]:
        """
        Part 1: Get Client ID and Client Secret from Google Cloud Console
        """
        print("\n" + "="*60)
        print("PART 1: Getting OAuth Credentials from Google Cloud Console")
        print("="*60)
        
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        # Step 1: Navigate to Google Cloud Console
        print("\n📍 Step 1: Navigating to Google Cloud Console...")
        await self.page.goto("https://console.cloud.google.com", wait_until="networkidle")
        print("✅ Loaded Google Cloud Console")
        
        # Wait for user to select project (manual step)
        print("\n⏸️  MANUAL STEP REQUIRED:")
        print("   Please select your project in the project selector")
        print("   Press ENTER when ready to continue...")
        input()
        
        # Step 2: Navigate to APIs & Services
        print("\n📍 Step 2: Navigating to APIs & Services...")
        try:
            await self.page.click('text="APIs & Services"', timeout=10000)
            await self.page.wait_for_load_state("networkidle")
            print("✅ Opened APIs & Services")
        except Exception as e:
            print(f"⚠️  Could not click 'APIs & Services', trying alternative...")
            await self.page.goto("https://console.cloud.google.com/apis", wait_until="networkidle")
        
        # Step 3: Go to Library
        print("\n📍 Step 3: Opening API Library...")
        try:
            await self.page.click('text="Library"', timeout=10000)
            await self.page.wait_for_load_state("networkidle")
            print("✅ Opened API Library")
        except Exception as e:
            print(f"⚠️  Could not click 'Library', trying direct URL...")
            await self.page.goto("https://console.cloud.google.com/apis/library", wait_until="networkidle")
        
        # Step 4: Search for Google Ads API
        print("\n📍 Step 4: Searching for Google Ads API...")
        search_input = self.page.locator('input[placeholder*="Search"], input[type="search"]').first()
        await search_input.fill("Google Ads API")
        await self.page.wait_for_timeout(2000)
        
        # Step 5: Click on Google Ads API
        print("\n📍 Step 5: Opening Google Ads API...")
        try:
            await self.page.click('text="Google Ads API"', timeout=10000)
            await self.page.wait_for_load_state("networkidle")
            print("✅ Opened Google Ads API page")
        except Exception as e:
            print(f"⚠️  Error clicking Google Ads API: {e}")
            print("   Please navigate manually and press ENTER...")
            input()
        
        # Step 6: Enable API if needed
        print("\n📍 Step 6: Checking if API needs to be enabled...")
        enable_button = self.page.locator('button:has-text("Enable")').first()
        if await enable_button.is_visible(timeout=5000):
            print("   Enabling Google Ads API...")
            await enable_button.click()
            await self.page.wait_for_load_state("networkidle")
            print("✅ Google Ads API enabled")
        else:
            print("✅ Google Ads API already enabled")
        
        # Step 7: Navigate to Credentials
        print("\n📍 Step 7: Navigating to Credentials...")
        try:
            await self.page.click('text="Credentials"', timeout=10000)
            await self.page.wait_for_load_state("networkidle")
            print("✅ Opened Credentials page")
        except Exception as e:
            print(f"⚠️  Could not click 'Credentials', trying direct URL...")
            await self.page.goto("https://console.cloud.google.com/apis/credentials", wait_until="networkidle")
        
        # Step 8: Create OAuth Credentials
        print("\n📍 Step 8: Creating OAuth credentials...")
        print("⏸️  MANUAL STEP REQUIRED:")
        print("   Please click 'CREATE CREDENTIALS' → 'OAuth client ID'")
        print("   If consent screen needs configuration, follow the prompts")
        print("   Application type: Desktop app")
        print("   Name: Google Ads MCP Desktop Client")
        print("   Press ENTER when credentials are created...")
        input()
        
        # Step 9: Extract credentials
        print("\n📍 Step 9: Extracting credentials...")
        
        # Try to find client ID (usually in an input field or text)
        client_id_pattern = r'[0-9]+-[a-zA-Z0-9_-]+\.apps\.googleusercontent\.com'
        
        # Look for input fields first
        inputs = await self.page.locator('input').all()
        for inp in inputs:
            value = await inp.input_value()
            if re.search(client_id_pattern, value):
                self.client_id = value
                print(f"✅ Found Client ID: {self.client_id[:50]}...")
                break
        
        # If not found in inputs, look in page text
        if not self.client_id:
            page_text = await self.page.content()
            match = re.search(client_id_pattern, page_text)
            if match:
                self.client_id = match.group(0)
                print(f"✅ Found Client ID: {self.client_id[:50]}...")
        
        # Look for client secret (usually in password input)
        secret_inputs = await self.page.locator('input[type="password"]').all()
        for inp in secret_inputs:
            value = await inp.input_value()
            if len(value) > 20:  # Client secrets are usually long
                self.client_secret = value
                print(f"✅ Found Client Secret: {self.client_secret[:20]}...")
                break
        
        # If not found, ask user to copy
        if not self.client_id:
            print("\n⚠️  Could not automatically extract Client ID")
            self.client_id = input("   Please paste Client ID: ").strip()
        
        if not self.client_secret:
            print("\n⚠️  Could not automatically extract Client Secret")
            self.client_secret = input("   Please paste Client Secret: ").strip()
        
        print("\n✅ OAuth credentials collected!")
        return self.client_id, self.client_secret

    async def get_developer_token(self) -> str:
        """
        Part 2: Get Developer Token from Google Ads
        """
        print("\n" + "="*60)
        print("PART 2: Getting Developer Token from Google Ads")
        print("="*60)
        
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        # Step 1: Navigate to Google Ads
        print("\n📍 Step 1: Navigating to Google Ads...")
        await self.page.goto("https://ads.google.com", wait_until="networkidle")
        print("✅ Loaded Google Ads")
        
        # Step 2: Handle account selection if needed
        print("\n⏸️  MANUAL STEP:")
        print("   If prompted, select your MCC account (211-993-1898)")
        print("   Press ENTER when ready...")
        input()
        
        # Step 3: Navigate to API Center
        print("\n📍 Step 2: Navigating to API Center...")
        try:
            # Try clicking tools icon
            tools_button = self.page.locator('button[aria-label*="Tools"], button[aria-label*="tools"]').first()
            if await tools_button.is_visible(timeout=5000):
                await tools_button.click()
                await self.page.wait_for_timeout(1000)
            
            # Click API Center
            await self.page.click('text="API Center"', timeout=10000)
            await self.page.wait_for_load_state("networkidle")
            print("✅ Opened API Center")
        except Exception as e:
            print(f"⚠️  Could not navigate via menu, trying direct URL...")
            await self.page.goto("https://ads.google.com/aw/apicenter", wait_until="networkidle")
        
        # Step 4: Find Developer Token
        print("\n📍 Step 3: Looking for Developer Token...")
        await self.page.wait_for_timeout(2000)
        
        # Look for developer token text (usually 10+ characters alphanumeric)
        page_text = await self.page.content()
        token_pattern = r'Developer Token[:\s]+([A-Za-z0-9]{10,})'
        match = re.search(token_pattern, page_text, re.IGNORECASE)
        
        if match:
            self.developer_token = match.group(1)
            print(f"✅ Found Developer Token: {self.developer_token[:20]}...")
        else:
            # Try to find copy button and click it
            copy_buttons = await self.page.locator('button[aria-label*="Copy"], button:has-text("Copy")').all()
            for btn in copy_buttons:
                try:
                    await btn.click()
                    await self.page.wait_for_timeout(1000)
                    # Token should be in clipboard now
                    print("✅ Clicked copy button")
                except:
                    pass
            
            # If still not found, ask user
            if not self.developer_token:
                print("\n⚠️  Could not automatically extract Developer Token")
                self.developer_token = input("   Please paste Developer Token: ").strip()
        
        print("\n✅ Developer Token collected!")
        return self.developer_token

    async def get_refresh_token(self) -> str:
        """
        Part 3: Get Refresh Token from OAuth Playground
        """
        print("\n" + "="*60)
        print("PART 3: Getting Refresh Token from OAuth Playground")
        print("="*60)
        
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        if not self.client_id or not self.client_secret:
            raise RuntimeError("Need Client ID and Secret first")
        
        # Step 1: Navigate to OAuth Playground
        print("\n📍 Step 1: Navigating to OAuth Playground...")
        await self.page.goto("https://developers.google.com/oauthplayground", wait_until="networkidle")
        print("✅ Loaded OAuth Playground")
        
        # Step 2: Open Settings
        print("\n📍 Step 2: Opening Settings...")
        try:
            settings_button = self.page.locator('button[aria-label*="Settings"], button:has-text("Settings")').first()
            await settings_button.click()
            await self.page.wait_for_timeout(1000)
            print("✅ Opened Settings")
        except Exception as e:
            print(f"⚠️  Could not find settings button: {e}")
            print("   Please open settings manually and press ENTER...")
            input()
        
        # Step 3: Enable "Use your own OAuth credentials"
        print("\n📍 Step 3: Enabling 'Use your own OAuth credentials'...")
        checkboxes = await self.page.locator('input[type="checkbox"]').all()
        for checkbox in checkboxes:
            label = await checkbox.evaluate('el => el.closest("label")?.textContent || ""')
            if "your own" in label.lower() or "oauth credentials" in label.lower():
                await checkbox.check()
                print("✅ Checked 'Use your own OAuth credentials'")
                break
        
        # Step 4: Enter Client ID
        print("\n📍 Step 4: Entering Client ID...")
        client_id_inputs = await self.page.locator('input[name*="client_id"], input[placeholder*="Client ID"]').all()
        if client_id_inputs:
            await client_id_inputs[0].fill(self.client_id)
            print("✅ Entered Client ID")
        else:
            print("⚠️  Could not find Client ID input, please enter manually")
            input("   Press ENTER when Client ID is entered...")
        
        # Step 5: Enter Client Secret
        print("\n📍 Step 5: Entering Client Secret...")
        secret_inputs = await self.page.locator('input[name*="client_secret"], input[type="password"]').all()
        if secret_inputs:
            await secret_inputs[0].fill(self.client_secret)
            print("✅ Entered Client Secret")
        else:
            print("⚠️  Could not find Client Secret input, please enter manually")
            input("   Press ENTER when Client Secret is entered...")
        
        # Step 6: Close Settings
        print("\n📍 Step 6: Closing Settings...")
        close_buttons = await self.page.locator('button:has-text("Close"), button[aria-label*="Close"]').all()
        if close_buttons:
            await close_buttons[0].click()
            await self.page.wait_for_timeout(1000)
        
        # Step 7: Find and select Google Ads API scope
        print("\n📍 Step 7: Selecting Google Ads API scope...")
        await self.page.wait_for_timeout(1000)
        
        # Search for Google Ads API
        search_inputs = await self.page.locator('input[placeholder*="Search"], input[type="search"]').all()
        if search_inputs:
            await search_inputs[0].fill("Google Ads API")
            await self.page.wait_for_timeout(1000)
        
        # Find and check the scope checkbox
        scope_checkboxes = await self.page.locator('input[value*="adwords"]').all()
        if scope_checkboxes:
            await scope_checkboxes[0].check()
            print("✅ Selected Google Ads API scope")
        else:
            print("⚠️  Could not find scope checkbox, please select manually")
            input("   Press ENTER when scope is selected...")
        
        # Step 8: Authorize
        print("\n📍 Step 8: Authorizing...")
        print("⏸️  MANUAL STEP:")
        print("   Click 'Authorize APIs' button")
        print("   Sign in and approve permissions")
        print("   Press ENTER when redirected back to playground...")
        input()
        
        # Step 9: Exchange for tokens
        print("\n📍 Step 9: Exchanging authorization code for tokens...")
        try:
            exchange_button = self.page.locator('button:has-text("Exchange"), button:has-text("Exchange authorization")').first()
            await exchange_button.click()
            await self.page.wait_for_load_state("networkidle")
            print("✅ Exchanged authorization code")
        except Exception as e:
            print(f"⚠️  Could not click exchange button: {e}")
            print("   Please click 'Exchange authorization code for tokens' manually")
            input("   Press ENTER when done...")
        
        # Step 10: Extract Refresh Token
        print("\n📍 Step 10: Extracting Refresh Token...")
        await self.page.wait_for_timeout(2000)
        
        # Look for refresh token (usually starts with "1//")
        page_text = await self.page.content()
        refresh_token_pattern = r'"refresh_token"\s*:\s*"([^"]+)"|Refresh token[:\s]+([A-Za-z0-9_-]+)'
        matches = re.findall(refresh_token_pattern, page_text, re.IGNORECASE)
        
        if matches:
            # Get the first non-empty match
            for match in matches:
                token = match[0] or match[1]
                if token and len(token) > 20:
                    self.refresh_token = token
                    print(f"✅ Found Refresh Token: {self.refresh_token[:30]}...")
                    break
        
        # If not found, look in textarea/input fields
        if not self.refresh_token:
            textareas = await self.page.locator('textarea, input').all()
            for ta in textareas:
                value = await ta.input_value()
                if value.startswith("1//") and len(value) > 50:
                    self.refresh_token = value
                    print(f"✅ Found Refresh Token: {self.refresh_token[:30]}...")
                    break
        
        # If still not found, ask user
        if not self.refresh_token:
            print("\n⚠️  Could not automatically extract Refresh Token")
            self.refresh_token = input("   Please paste Refresh Token: ").strip()
        
        print("\n✅ Refresh Token collected!")
        return self.refresh_token

    def update_config_file(self):
        """Update google-ads.yaml with collected credentials"""
        print("\n" + "="*60)
        print("PART 4: Updating Configuration File")
        print("="*60)
        
        # Read current config
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config_content = f.read()
        else:
            config_content = """client_id: YOUR_CLIENT_ID_HERE
client_secret: YOUR_CLIENT_SECRET_HERE
refresh_token: YOUR_REFRESH_TOKEN_HERE
developer_token: YOUR_DEVELOPER_TOKEN_HERE
login_customer_id: YOUR_LOGIN_CUSTOMER_ID_HERE
"""
        
        # Replace placeholders
        updated_config = config_content
        if self.client_id:
            updated_config = updated_config.replace('YOUR_CLIENT_ID_HERE', self.client_id)
            updated_config = re.sub(r'client_id:\s*[^\n]+', f'client_id: {self.client_id}', updated_config)
        
        if self.client_secret:
            updated_config = updated_config.replace('YOUR_CLIENT_SECRET_HERE', self.client_secret)
            updated_config = re.sub(r'client_secret:\s*[^\n]+', f'client_secret: {self.client_secret}', updated_config)
        
        if self.refresh_token:
            updated_config = updated_config.replace('YOUR_REFRESH_TOKEN_HERE', self.refresh_token)
            updated_config = re.sub(r'refresh_token:\s*[^\n]+', f'refresh_token: {self.refresh_token}', updated_config)
        
        if self.developer_token:
            updated_config = updated_config.replace('YOUR_DEVELOPER_TOKEN_HERE', self.developer_token)
            updated_config = re.sub(r'developer_token:\s*[^\n]+', f'developer_token: {self.developer_token}', updated_config)
        
        # Ensure MCC ID is set
        updated_config = updated_config.replace('YOUR_LOGIN_CUSTOMER_ID_HERE', MCC_ID)
        if f'login_customer_id: {MCC_ID}' not in updated_config:
            updated_config = re.sub(r'login_customer_id:\s*[^\n]+', f'login_customer_id: {MCC_ID}', updated_config)
        
        # Write updated config
        with open(CONFIG_FILE, 'w') as f:
            f.write(updated_config)
        
        print(f"\n✅ Configuration file updated: {CONFIG_FILE}")
        print("\n📋 Updated values:")
        print(f"   Client ID: {self.client_id[:50] if self.client_id else 'NOT SET'}...")
        print(f"   Client Secret: {'*' * 20 if self.client_secret else 'NOT SET'}")
        print(f"   Developer Token: {self.developer_token[:20] if self.developer_token else 'NOT SET'}...")
        print(f"   Refresh Token: {self.refresh_token[:30] if self.refresh_token else 'NOT SET'}...")
        print(f"   MCC ID: {MCC_ID}")

async def main():
    """Main execution function"""
    print("="*60)
    print("Google Ads API Credentials Collection - Automated")
    print("="*60)
    print("\nThis script will guide you through collecting Google Ads API credentials.")
    print("Some steps require manual interaction (sign-in, approvals, etc.)")
    print("\nStarting in 3 seconds...")
    import time
    time.sleep(3)
    
    collector = CredentialCollector()
    
    try:
        # Initialize browser
        await collector.initialize_browser(headless=False)
        
        # Part 1: Get OAuth credentials
        await collector.get_oauth_credentials()
        
        # Part 2: Get Developer Token
        await collector.get_developer_token()
        
        # Part 3: Get Refresh Token
        await collector.get_refresh_token()
        
        # Part 4: Update config file
        collector.update_config_file()
        
        print("\n" + "="*60)
        print("✅ CREDENTIAL COLLECTION COMPLETE!")
        print("="*60)
        print("\nNext steps:")
        print("1. Verify credentials: python3 test_server.py")
        print("2. Test MCP connection: claude mcp list")
        print("3. Run test suite: bash test_mcc_integration.sh")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Collection cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await collector.close_browser()

if __name__ == "__main__":
    asyncio.run(main())

