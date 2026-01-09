#!/usr/bin/env python3
"""
Natural Language Interface for Google Ads Client MCP
Allows conversational interaction with Google Ads accounts
"""

import asyncio
import json
import os
from typing import Dict, List, Optional
import openai
from datetime import datetime, timedelta

class NaturalLanguageInterface:
    """Natural language interface for Google Ads management"""
    
    def __init__(self, config_file: str = "../core/gads_client_config.json"):
        self.config = self.load_config(config_file)
        self.credentials = self.load_credentials()
        self.setup_openai()
        
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Config file {config_file} not found")
            return {}
    
    def load_credentials(self) -> Dict:
        """Load credentials from .env file"""
        credentials = {}
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        credentials[key] = value
        except FileNotFoundError:
            print("⚠️  .env file not found. Please run setup_airtable_integration.py first")
        return credentials
    
    def setup_openai(self):
        """Setup OpenAI client"""
        api_key = self.credentials.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
        if api_key:
            openai.api_key = api_key
        else:
            print("⚠️  OpenAI API key not found")
    
    async def process_natural_language_query(self, query: str) -> str:
        """Process natural language query and return response"""
        
        # Simple keyword-based processing for immediate functionality
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['account', 'accounts', 'list']):
            return await self.list_accounts()
        
        elif any(word in query_lower for word in ['campaign', 'campaigns', 'performance']):
            return await self.get_campaign_performance(query)
        
        elif any(word in query_lower for word in ['client', 'clients', 'list clients']):
            return await self.list_clients()
        
        elif any(word in query_lower for word in ['spend', 'cost', 'budget']):
            return await self.get_spend_data(query)
        
        elif any(word in query_lower for word in ['help', 'what can you do']):
            return self.get_help()
        
        else:
            # Use OpenAI for complex queries
            return await self.process_with_openai(query)
    
    async def list_accounts(self) -> str:
        """List Google Ads accounts"""
        try:
            # This would normally connect to Google Ads API
            # For now, return mock data
            accounts = [
                {"id": "123456789", "name": "Client A - E-commerce", "status": "active"},
                {"id": "987654321", "name": "Client B - B2B Services", "status": "active"},
                {"id": "456789123", "name": "Client C - Local Business", "status": "paused"}
            ]
            
            response = "📊 **Google Ads Accounts:**\n\n"
            for account in accounts:
                status_emoji = "🟢" if account["status"] == "active" else "🟡"
                response += f"{status_emoji} **{account['name']}**\n"
                response += f"   ID: `{account['id']}`\n"
                response += f"   Status: {account['status'].title()}\n\n"
            
            return response
        except Exception as e:
            return f"❌ Error listing accounts: {e}"
    
    async def get_campaign_performance(self, query: str) -> str:
        """Get campaign performance data"""
        try:
            # Extract account ID from query if mentioned
            account_id = None
            if "account" in query.lower():
                # Simple extraction - in real implementation, use NLP
                words = query.split()
                for i, word in enumerate(words):
                    if word.lower() == "account" and i + 1 < len(words):
                        account_id = words[i + 1]
                        break
            
            # Mock campaign data
            campaigns = [
                {
                    "name": "Brand Awareness Campaign",
                    "status": "active",
                    "clicks": 1250,
                    "impressions": 45000,
                    "cost": 1250.50,
                    "ctr": 2.78,
                    "cpc": 1.00
                },
                {
                    "name": "Conversion Campaign",
                    "status": "active", 
                    "clicks": 890,
                    "impressions": 28000,
                    "cost": 890.25,
                    "ctr": 3.18,
                    "cpc": 1.00
                }
            ]
            
            response = "📈 **Campaign Performance**\n\n"
            for campaign in campaigns:
                status_emoji = "🟢" if campaign["status"] == "active" else "🟡"
                response += f"{status_emoji} **{campaign['name']}**\n"
                response += f"   Clicks: {campaign['clicks']:,}\n"
                response += f"   Impressions: {campaign['impressions']:,}\n"
                response += f"   Cost: ${campaign['cost']:,.2f}\n"
                response += f"   CTR: {campaign['ctr']}%\n"
                response += f"   CPC: ${campaign['cpc']:.2f}\n\n"
            
            return response
        except Exception as e:
            return f"❌ Error getting campaign performance: {e}"
    
    async def list_clients(self) -> str:
        """List clients from Airtable"""
        try:
            # This would normally connect to Airtable
            # For now, return mock data
            clients = [
                {"name": "Client A", "email": "clienta@example.com", "status": "active"},
                {"name": "Client B", "email": "clientb@example.com", "status": "active"},
                {"name": "Client C", "email": "clientc@example.com", "status": "inactive"}
            ]
            
            response = "👥 **Clients:**\n\n"
            for client in clients:
                status_emoji = "🟢" if client["status"] == "active" else "🔴"
                response += f"{status_emoji} **{client['name']}**\n"
                response += f"   Email: {client['email']}\n"
                response += f"   Status: {client['status'].title()}\n\n"
            
            return response
        except Exception as e:
            return f"❌ Error listing clients: {e}"
    
    async def get_spend_data(self, query: str) -> str:
        """Get spend/budget data"""
        try:
            # Mock spend data
            spend_data = {
                "total_spend": 2140.75,
                "daily_average": 71.36,
                "monthly_budget": 5000.00,
                "budget_utilization": 42.8,
                "top_spending_campaigns": [
                    {"name": "Brand Awareness", "spend": 1250.50},
                    {"name": "Conversion Campaign", "spend": 890.25}
                ]
            }
            
            response = "💰 **Spend Overview**\n\n"
            response += f"💵 **Total Spend:** ${spend_data['total_spend']:,.2f}\n"
            response += f"📅 **Daily Average:** ${spend_data['daily_average']:.2f}\n"
            response += f"🎯 **Monthly Budget:** ${spend_data['monthly_budget']:,.2f}\n"
            response += f"📊 **Budget Utilization:** {spend_data['budget_utilization']}%\n\n"
            
            response += "🔥 **Top Spending Campaigns:**\n"
            for campaign in spend_data["top_spending_campaigns"]:
                response += f"   • {campaign['name']}: ${campaign['spend']:,.2f}\n"
            
            return response
        except Exception as e:
            return f"❌ Error getting spend data: {e}"
    
    async def process_with_openai(self, query: str) -> str:
        """Process complex queries with OpenAI"""
        try:
            if not openai.api_key:
                return "❌ OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file."
            
            # Create context for the AI
            context = f"""
            You are a Google Ads management assistant. The user is asking about their Google Ads accounts.
            
            Available data:
            - Account information
            - Campaign performance
            - Client data
            - Spend/budget information
            
            User query: {query}
            
            Provide a helpful response about Google Ads management. If you need specific data, mention that the user can ask for:
            - "List accounts" to see all Google Ads accounts
            - "Show campaign performance" to see campaign metrics
            - "List clients" to see client information
            - "Show spend data" to see budget and spending information
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": query}
                ],
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ Error processing with OpenAI: {e}"
    
    def get_help(self) -> str:
        """Get help information"""
        return """
🤖 **Google Ads Client MCP - Natural Language Interface**

**Available Commands:**

📊 **Account Management:**
• "List accounts" - Show all Google Ads accounts
• "Show account [ID] performance" - Get specific account data

📈 **Campaign Performance:**
• "Show campaign performance" - Get campaign metrics
• "Campaign status" - Check campaign status
• "Top performing campaigns" - Show best campaigns

👥 **Client Management:**
• "List clients" - Show all clients
• "Client [name] status" - Check specific client status

💰 **Financial Data:**
• "Show spend data" - Get budget and spending information
• "Monthly spend" - Show monthly spending
• "Budget utilization" - Check budget usage

🔧 **Other Commands:**
• "Help" - Show this help message
• "What can you do?" - List available features

**Examples:**
• "How are my campaigns performing?"
• "Show me the spend for account 123456789"
• "List all active clients"
• "What's my budget utilization this month?"

💡 **Tip:** You can ask questions in natural language, and I'll help you get the information you need!
"""

async def main():
    """Main interactive loop"""
    print("🤖 Google Ads Client MCP - Natural Language Interface")
    print("=" * 60)
    print("Type 'help' for available commands or 'quit' to exit")
    print("=" * 60)
    
    interface = NaturalLanguageInterface()
    
    while True:
        try:
            # Get user input
            query = input("\n💬 You: ").strip()
            
            if query.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye! Thanks for using Google Ads Client MCP!")
                break
            
            if not query:
                continue
            
            # Process query
            print("🤖 Processing...")
            response = await interface.process_natural_language_query(query)
            print(f"\n🤖 Assistant: {response}")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye! Thanks for using Google Ads Client MCP!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 