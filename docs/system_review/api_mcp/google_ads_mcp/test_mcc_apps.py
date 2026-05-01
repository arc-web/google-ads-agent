#!/usr/bin/env python3
"""
Google Ads MCP MCC Apps Testing Script
Tests all three apps with MCC context
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add apps to path
REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
APPS_PATH = REPO_ROOT / "6_apps" / "google_ads"
sys.path.insert(0, str(APPS_PATH))

# Test results
test_results: List[Dict[str, Any]] = []
MCC_ID = "2119931898"

def log_test(test_name: str, status: str, details: str = ""):
    """Log test result"""
    result = {
        "test_name": test_name,
        "status": status,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    
    status_symbol = "✓" if status == "PASS" else "✗"
    print(f"{status_symbol} {test_name}")
    if details:
        print(f"  {details}")

def test_account_management_app():
    """Test Account Management App"""
    print("\n=== Testing Account Management App ===")
    
    try:
        from account_management_app.account_management_app_main import AccountManagementApp
        
        # Note: In real testing, we'd need an MCP client
        # For now, we test the app structure
        app = AccountManagementApp()
        
        log_test(
            "Account Management App Import",
            "PASS",
            "App module imported successfully"
        )
        
        # Test that methods exist
        methods = ["list_accounts", "get_account_info", "get_account_hierarchy", 
                  "get_account_summary", "verify_account_access"]
        
        for method in methods:
            if hasattr(app, method):
                log_test(
                    f"Account App Method: {method}",
                    "PASS",
                    f"Method {method} exists"
                )
            else:
                log_test(
                    f"Account App Method: {method}",
                    "FAIL",
                    f"Method {method} not found"
                )
        
    except ImportError as e:
        log_test(
            "Account Management App Import",
            "FAIL",
            f"Import error: {str(e)}"
        )
    except Exception as e:
        log_test(
            "Account Management App Test",
            "FAIL",
            f"Error: {str(e)}"
        )

def test_campaign_management_app():
    """Test Campaign Management App"""
    print("\n=== Testing Campaign Management App ===")
    
    try:
        from campaign_management_app.campaign_management_app_main import CampaignManagementApp
        
        app = CampaignManagementApp()
        
        log_test(
            "Campaign Management App Import",
            "PASS",
            "App module imported successfully"
        )
        
        # Test that methods exist
        methods = ["list_campaigns", "get_campaign_details", "create_campaign",
                  "update_campaign_budget", "pause_campaign", "enable_campaign",
                  "get_campaign_performance"]
        
        for method in methods:
            if hasattr(app, method):
                log_test(
                    f"Campaign App Method: {method}",
                    "PASS",
                    f"Method {method} exists"
                )
            else:
                log_test(
                    f"Campaign App Method: {method}",
                    "FAIL",
                    f"Method {method} not found"
                )
        
    except ImportError as e:
        log_test(
            "Campaign Management App Import",
            "FAIL",
            f"Import error: {str(e)}"
        )
    except Exception as e:
        log_test(
            "Campaign Management App Test",
            "FAIL",
            f"Error: {str(e)}"
        )

def test_performance_analysis_app():
    """Test Performance Analysis App"""
    print("\n=== Testing Performance Analysis App ===")
    
    try:
        from performance_analysis_app.performance_analysis_app_main import PerformanceAnalysisApp
        
        app = PerformanceAnalysisApp()
        
        log_test(
            "Performance Analysis App Import",
            "PASS",
            "App module imported successfully"
        )
        
        # Test that methods exist
        methods = ["generate_performance_report", "compare_performance",
                  "identify_optimization_opportunities"]
        
        for method in methods:
            if hasattr(app, method):
                log_test(
                    f"Performance App Method: {method}",
                    "PASS",
                    f"Method {method} exists"
                )
            else:
                log_test(
                    f"Performance App Method: {method}",
                    "FAIL",
                    f"Method {method} not found"
                )
        
    except ImportError as e:
        log_test(
            "Performance Analysis App Import",
            "FAIL",
            f"Import error: {str(e)}"
        )
    except Exception as e:
        log_test(
            "Performance Analysis App Test",
            "FAIL",
            f"Error: {str(e)}"
        )

def generate_report():
    """Generate test report"""
    results_dir = Path(__file__).parent / "test_results"
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = results_dir / f"app_tests_mcc_{timestamp}.md"
    
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    total = len(test_results)
    
    report = f"""# Google Ads MCP Apps Test Results

**Test Execution**: {datetime.now().isoformat()}
**MCC ID**: {MCC_ID} (211-993-1898)

---

## Test Summary

- **Total Tests**: {total}
- **Passed**: {passed}
- **Failed**: {failed}
- **Pass Rate**: {(passed/total*100) if total > 0 else 0:.1f}%

---

## Test Results

"""
    
    for result in test_results:
        status_icon = "✓" if result["status"] == "PASS" else "✗"
        report += f"### {status_icon} {result['test_name']}\n\n"
        report += f"**Status**: {result['status']}\n\n"
        if result['details']:
            report += f"**Details**: {result['details']}\n\n"
        report += f"**Timestamp**: {result['timestamp']}\n\n"
        report += "---\n\n"
    
    report += f"""
## Notes

- These tests verify app structure and method availability
- Full integration tests require MCP client connection
- MCC context will be used when MCP client is available

## Next Steps

1. Verify MCP server connectivity
2. Test apps with actual MCP client
3. Test with real customer accounts under MCC
4. Verify MCC context is maintained throughout operations
"""
    
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to: {report_file}")
    return report_file

def main():
    """Run all app tests"""
    print("=" * 60)
    print("Google Ads MCP Apps Testing")
    print(f"MCC ID: {MCC_ID} (211-993-1898)")
    print("=" * 60)
    
    test_account_management_app()
    test_campaign_management_app()
    test_performance_analysis_app()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    total = len(test_results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    report_file = generate_report()
    
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

