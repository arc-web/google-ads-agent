class EmailResponseGenerator(ClientResponseGenerator):
    """Extended response generator with email-specific features"""
    
    def __init__(self, openai_api_key: str, agency_config: Dict):
        super().__init__(openai_api_key, agency_config)
    
    async def generate_email_response(self, email: ClientEmail, sops: List[SOPDocument], 
                                    account_data: Optional[Dict] = None) -> EmailResponse:
        """Generate email response for a client inquiry"""
        
        # Create query object from email
        query = ClientQuery(
            client_id=email.sender,
            account_id=email.client_account_id or "unknown",
            query_text=email.body,
            query_type=self._detect_query_type(email.body),
            timestamp=email.timestamp,
            source="email",
            email_context=email
        )
        
        # Generate response content
        response_content = await self.generate_response(query, sops, account_data)
        
        # Format as professional email
        email_body = self._format_as_email(response_content, email, account_data)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(sops, account_data, email.body)
        
        return EmailResponse(
            to=email.sender,
            subject=f"Re: {email.subject}",
            body=email_body,
            thread_id=email.thread_id,
            confidence_score=confidence,
            includes_data=account_data is not None
        )
    
    def _format_as_email(self, content: str, original_email: ClientEmail, 
                        account_data: Optional[Dict]) -> str:
        """Format response as professional email"""
        
        # Extract client name from email
        client_name = self._extract_client_name(original_email.sender)
        
        # Build email body
        email_parts = [
            f"Hi {client_name},",
            "",
            "Thank you for your email regarding your Google Ads account.",
            "",
            content,
            ""
        ]
        
        # Add performance summary if we have data
        if account_data and 'totals' in account_data:
            email_parts.extend([
                "**Quick Account Summary (Last 30 Days):**",
                f"• Impressions: {account_data['totals'].get('impressions', 0):,}",
                f"• Clicks: {account_data['totals'].get('clicks', 0):,}",
                f"• Total Spend: ${account_data['totals'].get('cost', 0):.2f}",
                f"• Conversions: {account_data['totals'].get('conversions', 0)}",
                ""
            ])
        
        # Add closing
        email_parts.extend([
            "Please let me know if you have any other questions or would like to schedule a call to discuss your account performance in more detail.",
            "",
            "Best regards,",
            f"Your {self.agency_config.get('name', 'Agency')} Team",
            "",
            "---",
            "This response was generated using our comprehensive Google Ads management procedures."
        ])
        
        return "\n".join(email_parts)
    
    def _extract_client_name(self, email_address: str) -> str:
        """Extract client name from email address"""
        # Try to get name from email format "Name <email@domain.com>"
        name_match = re.search(r'^(.+?)\s*<', email_address)
        if name_match:
            return name_match.group(1).strip()
        
        # Fallback to part before @ symbol
        local_part = email_address.split('@')[0]
        # Convert underscore/dots to spaces and title case
        return local_part.replace('_', ' ').replace('.', ' ').title()
    
    def _calculate_confidence(self, sops: List[SOPDocument], 
                            account_data: Optional[Dict], query_text: str) -> float:
        """Calculate confidence score for automated sending"""
        confidence = 0.0
        
        # Base confidence from SOP relevance
        if sops:
            avg_relevance = sum(sop.relevance_score for sop in sops) / len(sops)
            confidence += min(avg_relevance / 10, 0.4)  # Max 0.4 from SOPs
        
        # Bonus for having account data
        if account_data:
            confidence += 0.2
        
        # Penalty for complex questions
        complexity_indicators = ['complex', 'issue', 'problem', 'not working', 'error', 'help']
        if any(indicator in query_text.lower() for indicator in complexity_indicators):
            confidence -= 0.2
        
        # Bonus for simple questions
        simple_indicators = ['performance', 'report', 'summary', 'status', 'how much', 'what is']
        if any(indicator in query_text.lower() for indicator in simple_indicators):
            confidence += 0.2
        
        return max(0.0, min(1.0, confidence))

# Main orchestrator class
class GoogleAdsClientMCP:
    """Main MCP orchestrator for Google Ads client management with Airtable integration"""
    
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Initialize components
        self.airtable_manager = AirtableManager(
            os.getenv('AIRTABLE_TOKEN'),
            self.config
        )
        
        self.sop_manager = GoogleDriveSOPManager(
            self.config['platforms']['google_drive']['service_account_key']
        )
        
        self.ads_manager = GoogleAdsDataManager(
            self.config['platforms']['google_ads']['config_path']
        )
        
        self.gmail_manager = GmailManager(
            self.config['platforms']['gmail']['service_account_key'],
            self.config,
            self.airtable_manager
        )
        
        self.response_generator = EmailResponseGenerator(
            os.getenv('OPENAI_API_KEY'),
            self.config['agency']
        )
    
    async def process_email_batch(self) -> Dict[str, List[str]]:
        """Process a batch of incoming client emails with Airtable verification"""
        results = {
            'processed': [],
            'drafted': [],
            'errors': [],
            'skipped': []
        }
        
        try:
            # Fetch unread client emails (already filtered by Airtable verification)
            emails = await self.gmail_manager.fetch_unread_client_emails()
            
            for email in emails:
                try:
                    result = await self.process_single_email(email)
                    if 'sent automatically' in result:
                        results['processed'].append(f"{email.sender}: {result}")
                    elif 'draft created' in result:
                        results['drafted'].append(f"{email.sender}: {result}")
                    elif 'skipped' in result:
                        results['skipped'].append(f"{email.sender}: {result}")
                    else:
                        results['errors'].append(f"{email.sender}: {result}")
                        
                except Exception as e:
                    results['errors'].append(f"{email.sender}: Error - {str(e)}")
            
            return results
            
        except Exception as e:
            results['errors'].append(f"Batch processing error: {str(e)}")
            return results
    
    async def process_single_email(self, email: ClientEmail) -> str:
        """Process a single client email with full Airtable integration"""
        
        # Look up client in Airtable
        client_record = await self.airtable_manager.get_client_by_email(email.sender)
        
        if not client_record:
            return "Skipped: Sender not found in client database"
        
        if client_record.status != 'Active':
            return f"Skipped: Client status is {client_record.status}"
        
        if not client_record.google_ads_account_id:
            return "Skipped: No Google Ads account ID in client record"
        
        # Update email with client account ID
        email.client_account_id = client_record.google_ads_account_id
        
        # Analyze email content to find relevant SOPs
        keywords = self._extract_keywords(email.body)
        category = self._detect_category(email.body, email.subject)
        
        # Search for relevant SOPs
        sops = await self.sop_manager.search_sops(keywords, category)
        
        # Get account data if needed
        account_data = None
        if self._requires_account_data(email.body):
            account_data = await self.ads_manager.get_account_performance(
                email.client_account_id
            )
        
        # Generate email response
        response = await self.response_generator.generate_email_response(
            email, sops, account_data
        )
        
        # Log interaction in Airtable before sending
        await self.airtable_manager.log_interaction(
            client_record=client_record,
            query=email.body,
            response=response.body,
            confidence_score=response.confidence_score,
            auto_sent=response.confidence_score >= self.config['mcp']['guardrails']['auto_send_confidence_threshold']['value']
        )
        
        # Create and send/draft the response with proper CC handling
        return await self.gmail_manager.create_email_response(response, email, client_record)
    
    async def get_client_info(self, email_address: str) -> Optional[ClientRecord]:
        """Get client information from Airtable"""
        return await self.airtable_manager.get_client_by_email(email_address)
    
    async def answer_direct_query_with_client_context(self, email_address: str, query_text: str) -> str:
        """Handle direct queries with client context from Airtable"""
        
        # Look up client
        client_record = await self.airtable_manager.get_client_by_email(email_address)
        
        if not client_record:
            return "Error: Client not found in database"
        
        # Create query object
        query = ClientQuery(
            client_id=client_record.record_id,
            account_id=client_record.google_ads_account_id,
            query_text=query_text,
            query_type=self._detect_category(query_text),
            timestamp=datetime.now(),
            client_record=client_record
        )
        
        # Extract keywords and detect category
        keywords = self._extract_keywords(query.query_text)
        category = self._detect_category(query.query_text)
        
        # Search SOPs
        sops = await self.sop_manager.search_sops(keywords, category)
        
        # Get account data if needed
        account_data = None
        if self._requires_account_data(query.query_text):
            account_data = await self.ads_manager.get_account_performance(
                query.account_id
            )
        
        # Generate response
        response = await self.response_generator.generate_response(query, sops, account_data)
        
        # Log interaction in Airtable
        await self.airtable_manager.log_interaction(
            client_record=client_record,
            query=query_text,
            response=response,
            confidence_score=0.95,  # Direct queries are high confidence
            auto_sent=False  # Direct queries are not auto-sent
        )
        
        return response
    
    async def list_recent_interactions(self, client_email: str, days: int = 7) -> List[Dict]:
        """Get recent interactions for a client (would need additional Airtable query)"""
        # This would require implementing a search in the interactions table
        # filtered by client and date range
        pass
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        # Common Google Ads terms
        gads_terms = [
            'campaign', 'ad group', 'keywords', 'bidding', 'budget', 'performance',
            'impressions', 'clicks', 'ctr', 'cpc', 'conversions', 'roas', 'quality score',
            'disapproved', 'paused', 'optimization', 'targeting', 'audience', 'demographics'
        ]
        
        text_lower = text.lower()
        found_keywords = []
        
        for term in gads_terms:
            if term in text_lower:
                found_keywords.append(term)
        
        # Also extract potential custom keywords (capitalized words, numbers)
        words = re.findall(r'\b[A-Z][a-z]+\b|\b\d+\b', text)
        found_keywords.extend(words[:5])  # Limit to 5 additional keywords
        
        return found_keywords
    
    def _detect_category(self, text: str, subject: str = "") -> str:
        """Detect the category of the query"""
        combined_text = f"{subject} {text}".lower()
        
        category_patterns = {
            'reporting': ['report', 'performance', 'metrics', 'dashboard', 'summary', 'results'],
            'troubleshooting': ['issue', 'problem', 'error', 'not working', 'disapproved', 'rejected'],
            'billing': ['bill', 'invoice', 'payment', 'charge', 'cost', 'budget', 'spend'],
            'optimization': ['optimize', 'improve', 'increase', 'decrease', 'better', 'enhance'],
            'setup': ['setup', 'create', 'new', 'start', 'begin', 'launch'],
            'campaign_management': ['campaign', 'ad group', 'keyword', 'bid', 'target']
        }
        
        for category, patterns in category_patterns.items():
            if any(pattern in combined_text for pattern in patterns):
                return category
        
        return 'general'
    
    def _requires_account_data(self, text: str) -> bool:
        """Determine if the query requires live account data"""
        data_indicators = [
            'performance', 'spend', 'cost', 'clicks', 'impressions', 'conversions',
            'how much', 'how many', 'results', 'metrics', 'report', 'summary'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in data_indicators)

# Enhanced CLI interface with Airtable features
async def main():
    """Enhanced main function with Airtable integration"""
    
    # Initialize the MCP system
    mcp = GoogleAdsClientMCP('config.json')
    
    print("Google Ads Client Management MCP Started (with Airtable)")
    print("Available modes:")
    print("1. Process email batch")
    print("2. Answer direct query (with client lookup)")
    print("3. Start email monitoring (continuous)")
    print("4. Look up client information")
    print("5. Test Airtable connection")
    
    mode = input("Select mode (1-5): ")
    
    if mode == "1":
        # Process current batch of emails
        print("Processing email batch...")
        results = await mcp.process_email_batch()
        
        print(f"\nResults:")
        print(f"Processed: {len(results['processed'])}")
        print(f"Drafted: {len(results['drafted'])}")
        print(f"Skipped: {len(results['skipped'])}")
        print(f"Errors: {len(results['errors'])}")
        
        for category, items in results.items():
            if items:
                print(f"\n{category.title()}:")
                for item in items:
                    print(f"  - {item}")
    
    elif mode == "2":
        # Handle direct query with client context
        client_email = input("Client email address: ")
        query_text = input("Query: ")
        
        print("Looking up client and generating response...")
        response = await mcp.answer_direct_query_with_client_context(client_email, query_text)
        print(f"\nResponse:\n{response}")
    
    elif mode == "3":
        # Continuous email monitoring
        print("Starting continuous email monitoring...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                results = await mcp.process_email_batch()
                
                if any(results.values()):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{timestamp}] Processed: {len(results['processed'])}, "
                          f"Drafted: {len(results['drafted'])}, "
                          f"Skipped: {len(results['skipped'])}, "
                          f"Errors: {len(results['errors'])}")
                
                # Wait for next check interval
                await asyncio.sleep(
                    mcp.config['platforms']['gmail']['auto_processing']['check_interval_minutes'] * 60
                )
                
        except KeyboardInterrupt:
            print("\nEmail monitoring stopped")
    
    elif mode == "4":
        # Look up client information
        email_address = input("Client email address: ")
        
        print("Looking up client...")
        client_record = await mcp.get_client_info(email_address)
        
        if client_record:
            print(f"\nClient Information:")
            print(f"Name: {client_record.client_name}")
            print(f"Status: {client_record.status}")
            print(f"Google Ads Account: {client_record.google_ads_account_id}")
            print(f"Account Manager: {client_record.account_manager}")
            print(f"Primary Email: {client_record.primary_email}")
            print(f"CC Emails: {', '.join(client_record.cc_emails)}")
            print(f"Communication Preferences: {client_record.communication_preferences}")
        else:
            print("Client not found in Airtable database")
    
    elif mode == "5":
        # Test Airtable connection
        print("Testing Airtable connection...")
        
        test_email = input("Enter a test email address to look up: ")
        client_record = await mcp.airtable_manager.get_client_by_email(test_email)
        
        if client_record:
            print("✅ Airtable connection working!")
            print(f"Found client: {client_record.client_name}")
        else:
            print("❌ No client found or connection issue")

if __name__ == "__main__":
    asyncio.run(main())print("Starting continuous email monitoring...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                results = await mcp.process_email_batch()
                
                if any(results.values()):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{timestamp}] Processed: {len(results['processed'])}, "
                          f"Drafted: {len(results['drafted'])}, Errors: {len(results['errors'])}")
                
                # Wait for next check interval
                await asyncio.sleep(
                    mcp.config['platforms']['gmail']['auto_processing']['check_interval_minutes'] * 60
                )
                
        except KeyboardInterrupt:
            print("\nEmail monitoring stopped")

if __name__ == "__main__":
    asyncio.run(main())#!/usr/bin/env python3
"""
Google Ads Client Management MCP Implementation
Integrates with Google Drive SOPs and Gmail to provide client-specific responses
"""

import os
import json
import re
import asyncio
import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

import aiohttp
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.ads.googleads.client import GoogleAdsClient
import openai

@dataclass
class ClientRecord:
    """Represents a client record from Airtable"""
    record_id: str
    client_name: str
    primary_email: str
    cc_emails: List[str]
    google_ads_account_id: str
    account_manager: str
    communication_preferences: Dict
    status: str
    
@dataclass
class EmailRouting:
    """Represents email routing information"""
    email_address: str
    client_record_id: str
    contact_type: str  # "primary", "secondary", "billing", etc.
    is_primary: bool
    cc_on_responses: bool

@dataclass
class ClientEmail:
    """Represents a client email"""
    message_id: str
    thread_id: str
    sender: str
    subject: str
    body: str
    timestamp: datetime
    client_account_id: Optional[str] = None
    processed: bool = False

@dataclass
class EmailResponse:
    """Represents a generated email response"""
    to: str
    subject: str
    body: str
    thread_id: str
    confidence_score: float
    includes_data: bool = False
    
@dataclass
class ClientQuery:
    """Represents a client's question or request"""
    client_id: str
    account_id: str
    query_text: str
    query_type: str
    timestamp: datetime
    user_role: str = "client"
    source: str = "direct"  # "direct" or "email"
    email_context: Optional[ClientEmail] = None

@dataclass
class SOPDocument:
    """Represents an SOP document from Google Drive"""
    file_id: str
    name: str
    content: str
    category: str
    last_modified: datetime
    relevance_score: float

class GmailManager:
    """Manages Gmail integration for client communication"""
    
    def __init__(self, service_account_path: str, config: Dict, airtable_manager: AirtableManager):
        self.credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=['https://www.googleapis.com/auth/gmail.modify']
        )
        self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
        self.config = config
        self.airtable_manager = airtable_manager
    
    async def fetch_unread_client_emails(self) -> List[ClientEmail]:
        """Fetch unread emails from verified clients about Google Ads"""
        try:
            # Build query for Google Ads related emails
            keywords = self.config['gmail']['auto_processing']['filters']['subject_keywords']
            query_parts = [
                "is:unread",
                f"({' OR '.join([f'subject:{keyword}' for keyword in keywords])})"
            ]
            query = " ".join(query_parts)
            
            # Get message list
            response = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10
            ).execute()
            
            emails = []
            for message in response.get('messages', []):
                email_data = await self._get_email_content(message['id'])
                if email_data:
                    # Verify sender is a known client
                    client_record = await self.airtable_manager.get_client_by_email(email_data.sender)
                    if client_record and client_record.status == 'Active':
                        email_data.client_account_id = client_record.google_ads_account_id
                        emails.append(email_data)
            
            return emails
            
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []
    
    async def create_email_response(self, response: EmailResponse, 
                                  original_email: ClientEmail,
                                  client_record: ClientRecord) -> str:
        """Create email response with proper CC handling from Airtable"""
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['To'] = client_record.primary_email
            msg['Subject'] = response.subject
            msg['In-Reply-To'] = original_email.message_id
            msg['References'] = original_email.message_id
            
            # Add CC recipients if specified
            cc_recipients = []
            if client_record.cc_emails:
                cc_recipients.extend(client_record.cc_emails)
            
            # Check if account manager should be CC'd based on preferences
            if 'cc_account_manager' in client_record.communication_preferences:
                if client_record.communication_preferences['cc_account_manager'].lower() == 'yes':
                    # Add account manager email (you'd need to map this)
                    cc_recipients.append(f"{client_record.account_manager}@youragency.com")
            
            if cc_recipients:
                msg['Cc'] = ', '.join(cc_recipients)
            
            # Add body
            msg.attach(MIMEText(response.body, 'plain'))
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
            
            # Decide whether to send or create draft based on confidence
            if response.confidence_score >= self.config['mcp']['guardrails']['auto_send_confidence_threshold']['value']:
                # Send directly
                sent_message = self.gmail_service.users().messages().send(
                    userId='me',
                    body={
                        'raw': raw_message,
                        'threadId': response.thread_id
                    }
                ).execute()
                
                # Mark original as processed
                await self._mark_email_processed(original_email.message_id)
                
                return f"Email sent automatically to {client_record.client_name} (confidence: {response.confidence_score:.2f})"
            else:
                # Create draft for review
                draft = self.gmail_service.users().drafts().create(
                    userId='me',
                    body={
                        'message': {
                            'raw': raw_message,
                            'threadId': response.thread_id
                        }
                    }
                ).execute()
                
                return f"Draft created for {client_record.client_name} - needs review (confidence: {response.confidence_score:.2f})"
                
        except Exception as e:
            print(f"Error creating email response: {e}")
            return "Error creating email response"
    
    async def _get_email_content(self, message_id: str) -> Optional[ClientEmail]:
        """Get full content of an email"""
        try:
            message = self.gmail_service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = {h['name']: h['value'] for h in message['payload']['headers']}
            sender = headers.get('From', '')
            subject = headers.get('Subject', '')
            thread_id = message['threadId']
            
            # Extract body
            body = self._extract_email_body(message['payload'])
            
            # Parse timestamp
            timestamp = datetime.fromtimestamp(int(message['internalDate']) / 1000)
            
            # Map sender to client account (now handled by Airtable lookup)
            sender_email = re.search(r'<(.+?)>', sender)
            if sender_email:
                sender_email = sender_email.group(1)
            else:
                sender_email = sender.strip()
            
            return ClientEmail(
                message_id=message_id,
                thread_id=thread_id,
                sender=sender_email,
                subject=subject,
                body=body,
                timestamp=timestamp,
                client_account_id=None  # Will be populated by Airtable lookup
            )
            
        except Exception as e:
            print(f"Error getting email content: {e}")
            return None
    
    def _extract_email_body(self, payload: Dict) -> str:
        """Extract text body from email payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html':
                    # Fallback to HTML if no plain text
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        elif payload['mimeType'] == 'text/plain':
            data = payload['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body
    
    async def create_email_response(self, response: EmailResponse, 
                                  original_email: ClientEmail) -> str:
        """Create email response as draft or send directly"""
        # This method is now replaced by the enhanced version above
        passd
            msg['References'] = original_email.message_id
            
            # Add body
            msg.attach(MIMEText(response.body, 'plain'))
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
            
            # Decide whether to send or create draft based on confidence
            if response.confidence_score >= self.config['mcp']['guardrails']['auto_send_confidence_threshold']['value']:
                # Send directly
                sent_message = self.gmail_service.users().messages().send(
                    userId='me',
                    body={
                        'raw': raw_message,
                        'threadId': response.thread_id
                    }
                ).execute()
                
                # Mark original as processed
                await self._mark_email_processed(original_email.message_id)
                
                return f"Email sent automatically (confidence: {response.confidence_score:.2f})"
            else:
                # Create draft for review
                draft = self.gmail_service.users().drafts().create(
                    userId='me',
                    body={
                        'message': {
                            'raw': raw_message,
                            'threadId': response.thread_id
                        }
                    }
                ).execute()
                
                return f"Draft created for review (confidence: {response.confidence_score:.2f})"
                
        except Exception as e:
            print(f"Error creating email response: {e}")
            return "Error creating email response"
    
    async def _mark_email_processed(self, message_id: str):
        """Mark email as processed with appropriate labels"""
        try:
            # Add processed label and remove unread
            self.gmail_service.users().messages().modify(
                userId='me',
                id=message_id,
                body={
                    'addLabelIds': [self.config['gmail']['labels']['processed']],
                    'removeLabelIds': ['UNREAD']
                }
            ).execute()
        except Exception as e:
            print(f"Error marking email as processed: {e}")

class GoogleDriveSOPManager:
    """Manages SOP documents from Google Drive"""
    
    def __init__(self, service_account_path: str):
        self.credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
        self.sop_cache = {}
        self.cache_expiry = {}
    
    async def search_sops(self, query_keywords: List[str], category: str = None) -> List[SOPDocument]:
        """Search for relevant SOP documents"""
        # Build search query
        search_terms = []
        for keyword in query_keywords:
            search_terms.append(f"fullText contains '{keyword}'")
        
        if category:
            search_terms.append(f"name contains '{category}'")
        
        # Add SOP folder restriction
        search_terms.append("parents in 'SOP_FOLDER_ID'")
        
        query = " AND ".join(search_terms)
        
        try:
            results = self.drive_service.files().list(
                q=query,
                fields="files(id,name,mimeType,modifiedTime,webViewLink)",
                pageSize=10
            ).execute()
            
            sop_docs = []
            for file_info in results.get('files', []):
                content = await self._get_document_content(file_info['id'])
                relevance = self._calculate_relevance(content, query_keywords)
                
                sop_doc = SOPDocument(
                    file_id=file_info['id'],
                    name=file_info['name'],
                    content=content,
                    category=self._detect_category(file_info['name']),
                    last_modified=datetime.fromisoformat(file_info['modifiedTime'].replace('Z', '+00:00')),
                    relevance_score=relevance
                )
                sop_docs.append(sop_doc)
            
            # Sort by relevance
            return sorted(sop_docs, key=lambda x: x.relevance_score, reverse=True)
            
        except Exception as e:
            print(f"Error searching SOPs: {e}")
            return []
    
    async def _get_document_content(self, file_id: str) -> str:
        """Get content from a Google Drive document"""
        # Check cache first
        if file_id in self.sop_cache:
            if datetime.now() < self.cache_expiry.get(file_id, datetime.min):
                return self.sop_cache[file_id]
        
        try:
            # Export as plain text
            content = self.drive_service.files().export(
                fileId=file_id,
                mimeType='text/plain'
            ).execute()
            
            content_str = content.decode('utf-8')
            
            # Cache for 24 hours
            self.sop_cache[file_id] = content_str
            self.cache_expiry[file_id] = datetime.now() + timedelta(hours=24)
            
            return content_str
            
        except Exception as e:
            print(f"Error getting document content: {e}")
            return ""
    
    def _calculate_relevance(self, content: str, keywords: List[str]) -> float:
        """Calculate relevance score based on keyword matches"""
        content_lower = content.lower()
        score = 0.0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            count = content_lower.count(keyword_lower)
            score += count * 0.1
            
            # Bonus for title matches
            if keyword_lower in content_lower[:200]:
                score += 0.5
        
        return min(score, 10.0)  # Cap at 10
    
    def _detect_category(self, filename: str) -> str:
        """Detect SOP category from filename"""
        filename_lower = filename.lower()
        
        categories = {
            'setup': ['setup', 'onboarding', 'initial', 'new account'],
            'campaign': ['campaign', 'ad group', 'keywords', 'bidding'],
            'reporting': ['report', 'dashboard', 'metrics', 'analysis'],
            'troubleshooting': ['troubleshoot', 'issue', 'problem', 'error'],
            'billing': ['billing', 'invoice', 'payment', 'budget'],
            'communication': ['communication', 'client', 'template', 'email']
        }
        
        for category, keywords in categories.items():
            if any(keyword in filename_lower for keyword in keywords):
                return category
        
        return 'general'

class GoogleAdsDataManager:
    """Manages Google Ads account data"""
    
    def __init__(self, config_path: str):
        self.client = GoogleAdsClient.load_from_storage(config_path)
    
    async def get_account_performance(self, customer_id: str, date_range: str = "LAST_30_DAYS") -> Dict:
        """Get account performance data"""
        ga_service = self.client.get_service("GoogleAdsService")
        
        query = f"""
            SELECT
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.cost_micros,
                metrics.conversions,
                metrics.cost_per_conversion
            FROM campaign
            WHERE segments.date DURING {date_range}
        """
        
        try:
            response = ga_service.search_stream(customer_id=customer_id, query=query)
            
            campaigns = []
            total_metrics = {
                'impressions': 0,
                'clicks': 0,
                'cost': 0,
                'conversions': 0
            }
            
            for batch in response:
                for row in batch.results:
                    campaign_data = {
                        'name': row.campaign.name,
                        'impressions': row.metrics.impressions,
                        'clicks': row.metrics.clicks,
                        'ctr': row.metrics.ctr,
                        'cost': row.metrics.cost_micros / 1000000,
                        'conversions': row.metrics.conversions,
                        'cost_per_conversion': row.metrics.cost_per_conversion
                    }
                    campaigns.append(campaign_data)
                    
                    # Aggregate totals
                    total_metrics['impressions'] += campaign_data['impressions']
                    total_metrics['clicks'] += campaign_data['clicks']
                    total_metrics['cost'] += campaign_data['cost']
                    total_metrics['conversions'] += campaign_data['conversions']
            
            return {
                'campaigns': campaigns,
                'totals': total_metrics,
                'date_range': date_range
            }
            
        except Exception as e:
            print(f"Error getting account performance: {e}")
            return {}

class ClientResponseGenerator:
    """Generates client responses based on SOPs and account data"""
    
    def __init__(self, openai_api_key: str, agency_config: Dict):
        openai.api_key = openai_api_key
        self.agency_config = agency_config
    
    async def generate_response(self, query: ClientQuery, sops: List[SOPDocument], 
                              account_data: Optional[Dict] = None) -> str:
        """Generate a comprehensive response to the client query"""
        
        # Prepare context
        context = self._build_context(query, sops, account_data)
        
        # Generate response using OpenAI
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(query, context)
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return self._generate_fallback_response(query)
    
    def _build_context(self, query: ClientQuery, sops: List[SOPDocument], 
                      account_data: Optional[Dict]) -> str:
        """Build context from SOPs and account data"""
        context_parts = []
        
        # Add SOP information
        if sops:
            context_parts.append("**Relevant Agency Procedures:**")
            for sop in sops[:3]:  # Limit to top 3 most relevant
                context_parts.append(f"- {sop.name}: {sop.content[:500]}...")
        
        # Add account data if available
        if account_data:
            context_parts.append("\n**Account Performance Data:**")
            if 'totals' in account_data:
                totals = account_data['totals']
                context_parts.append(f"- Total Impressions: {totals.get('impressions', 0):,}")
                context_parts.append(f"- Total Clicks: {totals.get('clicks', 0):,}")
                context_parts.append(f"- Total Cost: ${totals.get('cost', 0):.2f}")
                context_parts.append(f"- Total Conversions: {totals.get('conversions', 0)}")
        
        return "\n".join(context_parts)
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the AI"""
        agency_name = self.agency_config.get('name', 'Our Agency')
        
        return f"""You are a Google Ads specialist representing {agency_name}. 
        
        Your role is to answer client questions about their Google Ads accounts based on:
        1. Our agency's Standard Operating Procedures (