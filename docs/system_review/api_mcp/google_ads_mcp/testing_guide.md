# Google Ads MCP MCC Testing Guide

## Overview

This guide explains how to test the Google Ads MCP integration with MCC account 211-993-1898.

## Prerequisites

1. MCC ID configured: `2119931898` (no dashes) in `google-ads.yaml`
2. Google Ads API credentials filled in `google-ads.yaml`
3. Python virtual environment set up
4. MCP server installed

## Test Scripts

### 1. Configuration and Connectivity Test

```bash
cd $MCP_TOOLS_ROOT/servers/google_ads_mcp
bash test_mcc_integration.sh
```

**What it tests**:
- MCC configuration in `google-ads.yaml`
- Required fields presence
- Python environment
- Server initialization
- MCP connection status

**Output**: `test_results/test_results_mcc_*.md`

### 2. Apps Functionality Test

```bash
cd $MCP_TOOLS_ROOT/servers/google_ads_mcp
python3 test_mcc_apps.py
```

**What it tests**:
- Account Management App import and methods
- Campaign Management App import and methods
- Performance Analysis App import and methods

**Output**: `test_results/app_tests_mcc_*.md`

### 3. Workflow Templates Test

```bash
cd $MCP_TOOLS_ROOT/servers/google_ads_mcp
python3 test_mcc_workflows.py
```

**What it tests**:
- Workflow YAML file structure
- Required fields
- App references
- MCC context support
- Success criteria and failure handling

**Output**: `test_results/workflow_tests_mcc_*.md`

### 4. Comprehensive Report Generation

```bash
cd $MCP_TOOLS_ROOT/servers/google_ads_mcp
python3 generate_comprehensive_report.py
```

**What it does**:
- Combines all test results
- Generates executive summary
- Provides next steps

**Output**: `test_results/comprehensive_test_results_mcc_*.md`

## Running All Tests

Run all tests in sequence:

```bash
cd $MCP_TOOLS_ROOT/servers/google_ads_mcp

# 1. Configuration test
bash test_mcc_integration.sh

# 2. Apps test
python3 test_mcc_apps.py

# 3. Workflows test
python3 test_mcc_workflows.py

# 4. Generate comprehensive report
python3 generate_comprehensive_report.py
```

## Test Results Location

All test results are saved in:
```
$MCP_TOOLS_ROOT/servers/google_ads_mcp/test_results/
```

## MCC Configuration

The MCC ID `211-993-1898` must be configured as `2119931898` (no dashes) in:

**File**: `google-ads.yaml`
```yaml
login_customer_id: 2119931898
```

## Next Steps After Testing

1. **Fill in Credentials**: Update `google-ads.yaml` with actual API credentials
2. **Test MCP Connection**: Verify MCP server connects successfully
3. **Test Account Access**: Use `list_accessible_customers` to verify MCC access
4. **Test Apps**: Run apps with actual MCP client
5. **Execute Workflows**: Test workflow execution with real data

## Troubleshooting

### Configuration Tests Fail

- Check `google-ads.yaml` has MCC ID set correctly
- Verify all required fields are present
- Replace placeholder values with actual credentials

### Server Initialization Fails

- Check Python virtual environment is activated
- Verify MCP server dependencies are installed
- Check server logs in `test_results/`

### Apps Tests Fail

- Verify apps are in correct location: `6_apps/google_ads/`
- Check Python path includes apps directory
- Verify app imports work correctly

### Workflow Tests Fail

- Check workflow files exist: `5_workflows/templates/google_ads/`
- Verify YAML syntax is valid
- Check workflow structure matches expected format

## Support

For issues:
- Review test logs in `test_results/`
- Check MCP server documentation
- Verify MCC account has API access enabled
- Ensure developer token has proper permissions

