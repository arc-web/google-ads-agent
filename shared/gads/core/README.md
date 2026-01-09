# 🚀 Google Ads Core System (core layer)

## Overview
Core orchestrator and configuration for the Google Ads Client MCP system, including the main implementation, configuration files, and MCP system prompts that drive the entire automation workflow.

## Dependencies
- Parent layer: Requires root at `../..`
- Libraries: `aiohttp`, `google-ads`, `openai`, `pyairtable`

## Usage
```bash
# Run the main orchestrator
python gads_client_implementation.py

# View configuration
cat gads_client_config.json

# Check MCP system prompt
cat gads_client_mcp.txt
```

## Success Criteria
- ✅ Main orchestrator processes email batches successfully
- ✅ Configuration file contains all necessary settings
- ✅ MCP system prompt defines agent behavior correctly
- ✅ Integration with all external APIs (Airtable, Gmail, Google Ads)
- ✅ Response generation works with OpenAI integration

## Links
- Parent docs: ../../README.md
- Child components: 
  - `gads_client_implementation.py` - Main orchestrator (1,032 lines)
  - `gads_client_config.json` - Configuration and settings (294 lines)
  - `gads_client_mcp.txt` - MCP system prompt (418 lines) 