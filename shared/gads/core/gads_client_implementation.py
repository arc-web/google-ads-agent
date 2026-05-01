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
    asyncio.run(main())
