#!/usr/bin/env python3
"""
Airtable Integration Setup Script
Quick setup to connect to your Airtable and access stored API keys/credentials
"""

import os
import json
import asyncio
from typing import Dict, Optional
import aiohttp
from dataclasses import dataclass

@dataclass
class AirtableConfig:
    """Configuration for Airtable integration"""
    api_key: str
    base_id: str
    tables: Dict[str, str]

class AirtableSetup:
    """Setup and test Airtable integration"""
    
    def __init__(self, config: AirtableConfig):
        self.config = config
        self.base_url = f"https://api.airtable.com/v0/{config.base_id}"
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
    
    async def test_connection(self) -> bool:
        """Test if we can connect to Airtable"""
        try:
            async with aiohttp.ClientSession() as session:
                # Try to list tables by making a request to any table
                for table_name, table_id in self.config.tables.items():
                    url = f"{self.base_url}/{table_id}?maxRecords=1"
                    async with session.get(url, headers=self.headers) as response:
                        if response.status == 200:
                            print(f"✅ Successfully connected to table: {table_name}")
                            return True
                        else:
                            print(f"❌ Failed to connect to table: {table_name}")
                            return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    async def get_api_credentials(self) -> Optional[Dict]:
        """Retrieve API credentials from Airtable"""
        try:
            # Assuming you have a table for API credentials
            credentials_table = self.config.tables.get("api_credentials", "tblApiCredentials")
            url = f"{self.base_url}/{credentials_table}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        records = data.get("records", [])
                        
                        credentials = {}
                        for record in records:
                            fields = record.get("fields", {})
                            service = fields.get("service", "")
                            api_key = fields.get("api_key", "")
                            credentials[service] = api_key
                        
                        print(f"✅ Retrieved {len(credentials)} API credentials")
                        return credentials
                    else:
                        print(f"❌ Failed to retrieve credentials: {response.status}")
                        return None
        except Exception as e:
            print(f"❌ Error retrieving credentials: {e}")
            return None
    
    async def get_client_data(self) -> Optional[Dict]:
        """Retrieve client data from Airtable"""
        try:
            clients_table = self.config.tables.get("clients", "tblClients")
            url = f"{self.base_url}/{clients_table}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        records = data.get("records", [])
                        
                        clients = {}
                        for record in records:
                            fields = record.get("fields", {})
                            email = fields.get("email", "")
                            client_id = record.get("id", "")
                            clients[email] = {
                                "id": client_id,
                                "name": fields.get("name", ""),
                                "google_ads_id": fields.get("google_ads_id", ""),
                                "status": fields.get("status", "active")
                            }
                        
                        print(f"✅ Retrieved {len(clients)} client records")
                        return clients
                    else:
                        print(f"❌ Failed to retrieve clients: {response.status}")
                        return None
        except Exception as e:
            print(f"❌ Error retrieving clients: {e}")
            return None

async def interactive_setup():
    """Interactive setup process"""
    print("🚀 Google Ads Client MCP - Airtable Setup")
    print("=" * 50)
    
    # Get Airtable credentials
    print("\n📋 Please provide your Airtable credentials:")
    api_key = input("Airtable API Key: ").strip()
    base_id = input("Airtable Base ID: ").strip()
    
    # Get table mappings
    print("\n📊 Please provide your table IDs (press Enter to use defaults):")
    clients_table = input("Clients table ID (default: tblClients): ").strip() or "tblClients"
    api_credentials_table = input("API Credentials table ID (default: tblApiCredentials): ").strip() or "tblApiCredentials"
    interactions_table = input("Interactions table ID (default: tblInteractions): ").strip() or "tblInteractions"
    
    # Create config
    config = AirtableConfig(
        api_key=api_key,
        base_id=base_id,
        tables={
            "clients": clients_table,
            "api_credentials": api_credentials_table,
            "interactions": interactions_table
        }
    )
    
    # Test connection
    print("\n🔗 Testing Airtable connection...")
    setup = AirtableSetup(config)
    
    if await setup.test_connection():
        print("✅ Airtable connection successful!")
        
        # Retrieve data
        print("\n📥 Retrieving stored data...")
        credentials = await setup.get_api_credentials()
        clients = await setup.get_client_data()
        
        # Save configuration
        config_data = {
            "airtable": {
                "api_key": api_key,
                "base_id": base_id,
                "tables": config.tables
            },
            "retrieved_data": {
                "credentials_count": len(credentials) if credentials else 0,
                "clients_count": len(clients) if clients else 0
            }
        }
        
        with open("airtable_setup.json", "w") as f:
            json.dump(config_data, f, indent=2)
        
        print("✅ Configuration saved to airtable_setup.json")
        
        # Show summary
        print("\n📊 Setup Summary:")
        print(f"   • Connected to Airtable base: {base_id}")
        print(f"   • Retrieved {len(credentials) if credentials else 0} API credentials")
        print(f"   • Retrieved {len(clients) if clients else 0} client records")
        
        return config, credentials, clients
    else:
        print("❌ Failed to connect to Airtable. Please check your credentials.")
        return None, None, None

def create_env_file(credentials: Dict):
    """Create .env file with retrieved credentials"""
    if not credentials:
        return
    
    env_content = "# Environment variables for Google Ads Client MCP\n"
    env_content += "# Generated from Airtable integration\n\n"
    
    for service, api_key in credentials.items():
        env_content += f"{service.upper()}_API_KEY={api_key}\n"
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✅ Created .env file with API credentials")

async def main():
    """Main setup function"""
    print("🎯 Setting up Airtable integration for Google Ads Client MCP")
    
    # Run interactive setup
    config, credentials, clients = await interactive_setup()
    
    if config and credentials:
        # Create environment file
        create_env_file(credentials)
        
        print("\n🎉 Setup complete! Next steps:")
        print("1. Review the generated .env file")
        print("2. Run: python gads/core/gads_client_implementation.py")
        print("3. Start using natural language interface")
        
        # Show available credentials
        print(f"\n🔑 Available API credentials:")
        for service in credentials.keys():
            print(f"   • {service}")
        
        # Show client summary
        if clients:
            print(f"\n👥 Client summary:")
            active_clients = [c for c in clients.values() if c.get("status") == "active"]
            print(f"   • Total clients: {len(clients)}")
            print(f"   • Active clients: {len(active_clients)}")
    else:
        print("\n❌ Setup failed. Please check your Airtable credentials and try again.")

if __name__ == "__main__":
    asyncio.run(main()) 