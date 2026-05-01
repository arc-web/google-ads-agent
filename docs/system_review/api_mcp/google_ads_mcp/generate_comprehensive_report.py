#!/usr/bin/env python3
"""
Generate Comprehensive MCC Test Report
Combines all test results into a single report
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

RESULTS_DIR = Path(__file__).parent / "test_results"
MCC_ID = "2119931898"

def find_latest_report(pattern: str) -> Path:
    """Find the latest test report matching pattern"""
    reports = list(RESULTS_DIR.glob(pattern))
    if not reports:
        return None
    
    # Sort by modification time, newest first
    reports.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return reports[0]

def parse_markdown_report(report_file: Path) -> Dict[str, Any]:
    """Parse markdown test report"""
    if not report_file or not report_file.exists():
        return None
    
    content = report_file.read_text()
    
    # Extract summary
    summary = {}
    if "Total Tests:" in content:
        for line in content.split("\n"):
            if "Total Tests:" in line:
                summary["total"] = int(line.split(":")[1].strip())
            elif "Passed:" in line:
                summary["passed"] = int(line.split(":")[1].strip())
            elif "Failed:" in line:
                summary["failed"] = int(line.split(":")[1].strip())
            elif "Warnings:" in line:
                summary["warnings"] = int(line.split(":")[1].strip())
    
    return {
        "file": report_file.name,
        "summary": summary,
        "content": content
    }

def generate_comprehensive_report():
    """Generate comprehensive test report"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = RESULTS_DIR / f"comprehensive_test_results_mcc_{timestamp}.md"
    
    # Find all test reports
    config_report = find_latest_report("test_results_mcc_*.md")
    app_report = find_latest_report("app_tests_mcc_*.md")
    workflow_report = find_latest_report("workflow_tests_mcc_*.md")
    
    # Parse reports
    config_data = parse_markdown_report(config_report)
    app_data = parse_markdown_report(app_report)
    workflow_data = parse_markdown_report(workflow_report)
    
    # Generate comprehensive report
    report = f"""# Google Ads MCP MCC Comprehensive Test Results

**Report Generated**: {datetime.now().isoformat()}
**MCC ID**: {MCC_ID} (211-993-1898)

---

## Executive Summary

This comprehensive report combines results from all test phases:

1. **Configuration Verification** - MCC setup and config validation
2. **MCP Server Connectivity** - Server initialization and connection
3. **App Functionality** - Account, Campaign, and Performance apps
4. **Workflow Templates** - Workflow structure and MCC context support

---

## Test Phase Results

### Phase 1: Configuration Verification

"""
    
    if config_data:
        report += f"**Report**: `{config_data['file']}`\n\n"
        if config_data['summary']:
            s = config_data['summary']
            report += f"- **Total Tests**: {s.get('total', 'N/A')}\n"
            report += f"- **Passed**: {s.get('passed', 'N/A')}\n"
            report += f"- **Failed**: {s.get('failed', 'N/A')}\n"
            pass_rate = (s.get('passed', 0) / s.get('total', 1) * 100) if s.get('total', 0) > 0 else 0
            report += f"- **Pass Rate**: {pass_rate:.1f}%\n\n"
    else:
        report += "**Status**: No configuration test report found\n\n"
    
    report += "### Phase 2: App Functionality Testing\n\n"
    
    if app_data:
        report += f"**Report**: `{app_data['file']}`\n\n"
        if app_data['summary']:
            s = app_data['summary']
            report += f"- **Total Tests**: {s.get('total', 'N/A')}\n"
            report += f"- **Passed**: {s.get('passed', 'N/A')}\n"
            report += f"- **Failed**: {s.get('failed', 'N/A')}\n"
            pass_rate = (s.get('passed', 0) / s.get('total', 1) * 100) if s.get('total', 0) > 0 else 0
            report += f"- **Pass Rate**: {pass_rate:.1f}%\n\n"
    else:
        report += "**Status**: No app test report found\n\n"
    
    report += "### Phase 3: Workflow Template Testing\n\n"
    
    if workflow_data:
        report += f"**Report**: `{workflow_data['file']}`\n\n"
        if workflow_data['summary']:
            s = workflow_data['summary']
            report += f"- **Total Tests**: {s.get('total', 'N/A')}\n"
            report += f"- **Passed**: {s.get('passed', 'N/A')}\n"
            report += f"- **Failed**: {s.get('failed', 'N/A')}\n"
            report += f"- **Warnings**: {s.get('warnings', 'N/A')}\n"
            pass_rate = (s.get('passed', 0) / s.get('total', 1) * 100) if s.get('total', 0) > 0 else 0
            report += f"- **Pass Rate**: {pass_rate:.1f}%\n\n"
    else:
        report += "**Status**: No workflow test report found\n\n"
    
    # Overall summary
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    for data in [config_data, app_data, workflow_data]:
        if data and data.get('summary'):
            total_tests += data['summary'].get('total', 0)
            total_passed += data['summary'].get('passed', 0)
            total_failed += data['summary'].get('failed', 0)
    
    report += f"""---

## Overall Test Summary

- **Total Tests Across All Phases**: {total_tests}
- **Total Passed**: {total_passed}
- **Total Failed**: {total_failed}
- **Overall Pass Rate**: {(total_passed/total_tests*100) if total_tests > 0 else 0:.1f}%

---

## MCC Configuration Status

**MCC ID**: {MCC_ID} (211-993-1898)

**Configuration File**: `google-ads.yaml`
- `login_customer_id` should be set to: `{MCC_ID}` (no dashes)

**Status**: {'✓ Configured' if config_data else '⚠ Not verified'}

---

## Key Findings

### Configuration
"""
    
    if config_data:
        if config_data['summary'].get('failed', 0) == 0:
            report += "- ✓ MCC configuration verified\n"
            report += "- ✓ All required fields present\n"
        else:
            report += "- ⚠ Some configuration issues found\n"
            report += "- Review placeholder values in google-ads.yaml\n"
    else:
        report += "- ⚠ Configuration tests not run\n"
    
    report += "\n### Apps\n"
    
    if app_data:
        if app_data['summary'].get('failed', 0) == 0:
            report += "- ✓ All apps import successfully\n"
            report += "- ✓ Required methods are present\n"
        else:
            report += "- ⚠ Some app issues found\n"
    else:
        report += "- ⚠ App tests not run\n"
    
    report += "\n### Workflows\n"
    
    if workflow_data:
        if workflow_data['summary'].get('failed', 0) == 0:
            report += "- ✓ All workflow templates validated\n"
            report += "- ✓ Workflows support MCC context\n"
        else:
            report += "- ⚠ Some workflow issues found\n"
    else:
        report += "- ⚠ Workflow tests not run\n"
    
    report += f"""

---

## Next Steps

### Immediate Actions

1. **Fill in Credentials**: Update `google-ads.yaml` with actual credentials
   - Replace `YOUR_CLIENT_ID_HERE` with actual client ID
   - Replace `YOUR_CLIENT_SECRET_HERE` with actual client secret
   - Replace `YOUR_REFRESH_TOKEN_HERE` with actual refresh token
   - Replace `YOUR_DEVELOPER_TOKEN_HERE` with actual developer token
   - Verify `login_customer_id: {MCC_ID}` is set correctly

2. **Test MCP Connection**: Once credentials are filled in:
   ```bash
   cd $MCP_TOOLS_ROOT/servers/google_ads_mcp
   python3 test_server.py
   ```

3. **Verify MCC Access**: Test listing accessible customers:
   - Use MCP tool `list_accessible_customers`
   - Verify all accounts are under MCC {MCC_ID}

4. **Test Apps with MCP**: Run apps with actual MCP client:
   - Test Account Management App
   - Test Campaign Management App
   - Test Performance Analysis App

5. **Execute Workflows**: Test workflow execution:
   - Account Audit Workflow
   - Daily Reporting Workflow
   - Campaign Launch Workflow
   - Performance Optimization Workflow

### Integration Testing

Once basic tests pass:

1. **End-to-End Test**: Full workflow from MCC → Accounts → Campaigns → Reports
2. **Multi-Account Test**: Test operations across multiple customer accounts
3. **Error Handling**: Test error scenarios and edge cases
4. **Performance**: Test with large datasets and multiple accounts

---

## Test Reports

Detailed reports available in: `{RESULTS_DIR}`

- Configuration Tests: `{config_data['file'] if config_data else 'N/A'}`
- App Tests: `{app_data['file'] if app_data else 'N/A'}`
- Workflow Tests: `{workflow_data['file'] if workflow_data else 'N/A'}`

---

## Support

For issues or questions:
- Review test logs in `{RESULTS_DIR}`
- Check MCP server logs
- Verify MCC account has API access enabled
- Ensure developer token has proper permissions

---

**Report Generated**: {datetime.now().isoformat()}
"""
    
    RESULTS_DIR.mkdir(exist_ok=True)
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"Comprehensive report generated: {report_file}")
    return report_file

if __name__ == "__main__":
    generate_comprehensive_report()

