# 🚀 Platform Integrations (integrations layer)

## Overview
Platform integration layer for the Google Ads Client MCP system, including Airtable setup automation and natural language interface for conversational interaction with Google Ads accounts and client data.

## Dependencies
- Parent layer: Requires core at `../core`
- Libraries: `aiohttp`, `openai`, `pyairtable`, `asyncio`

## Usage
```bash
# Setup Airtable integration
python setup_airtable_integration.py

# Start natural language interface
python natural_language_interface.py

# Example queries:
# "List accounts"
# "Show campaign performance"
# "List clients"
# "Show spend data"
```

## Success Criteria
- ✅ Airtable integration retrieves API credentials and client data
- ✅ Natural language interface responds to user queries
- ✅ OpenAI integration processes complex queries
- ✅ Mock data provides immediate functionality
- ✅ Environment file generation works correctly

## Links
- Parent docs: ../../README.md
- Child components: 
  - `setup_airtable_integration.py` - Airtable setup and credential retrieval
  - `natural_language_interface.py` - Conversational interface for Google Ads 