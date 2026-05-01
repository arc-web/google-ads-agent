#!/usr/bin/env python3
"""
Google Ads MCP MCC Workflow Testing Script
Tests workflow templates with MCC context
"""

import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Try to import yaml, but handle gracefully if not available
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# Test results
test_results: List[Dict[str, Any]] = []
MCC_ID = "2119931898"
WORKFLOWS_DIR = Path(__file__).parent.parent.parent.parent.parent / "5_workflows" / "templates" / "google_ads"

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

def test_workflow_file(workflow_file: Path):
    """Test a workflow YAML file"""
    workflow_name = workflow_file.stem
    
    if not YAML_AVAILABLE:
        # Basic file validation without yaml parsing
        try:
            content = workflow_file.read_text()
            log_test(
                f"Workflow {workflow_name}: File Read",
                "PASS",
                "Workflow file readable"
            )
            
            # Basic checks without yaml parsing
            if "name:" in content:
                log_test(
                    f"Workflow {workflow_name}: Name Field",
                    "PASS",
                    "Name field present"
                )
            if "workflow:" in content:
                log_test(
                    f"Workflow {workflow_name}: Workflow Field",
                    "PASS",
                    "Workflow field present"
                )
            if MCC_ID in content or "customer_id" in content.lower():
                log_test(
                    f"Workflow {workflow_name}: MCC Context",
                    "PASS",
                    "Workflow supports customer/MCC context"
                )
            return True
        except Exception as e:
            log_test(
                f"Workflow {workflow_name}: File Read",
                "FAIL",
                f"Error reading file: {str(e)}"
            )
            return False
    
    try:
        with open(workflow_file, 'r') as f:
            workflow = yaml.safe_load(f)
        
        # Check required fields
        required_fields = ["name", "description", "workflow"]
        missing_fields = [field for field in required_fields if field not in workflow]
        
        if missing_fields:
            log_test(
                f"Workflow {workflow_name}: Required Fields",
                "FAIL",
                f"Missing fields: {', '.join(missing_fields)}"
            )
        else:
            log_test(
                f"Workflow {workflow_name}: Required Fields",
                "PASS",
                "All required fields present"
            )
        
        # Check workflow steps reference apps
        if "workflow" in workflow:
            steps = workflow["workflow"]
            app_references = []
            
            for step in steps:
                if isinstance(step, dict):
                    if "app" in step:
                        app_references.append(step["app"])
            
            if app_references:
                log_test(
                    f"Workflow {workflow_name}: App References",
                    "PASS",
                    f"References apps: {', '.join(set(app_references))}"
                )
            else:
                log_test(
                    f"Workflow {workflow_name}: App References",
                    "WARN",
                    "No app references found in workflow steps"
                )
        
        # Check for MCC context usage
        workflow_str = yaml.dump(workflow)
        if MCC_ID in workflow_str or "customer_id" in workflow_str.lower():
            log_test(
                f"Workflow {workflow_name}: MCC Context",
                "PASS",
                "Workflow supports customer/MCC context"
            )
        else:
            log_test(
                f"Workflow {workflow_name}: MCC Context",
                "WARN",
                "Workflow may not explicitly use MCC context"
            )
        
        # Check success criteria
        if "success_criteria" in workflow:
            log_test(
                f"Workflow {workflow_name}: Success Criteria",
                "PASS",
                f"Defines {len(workflow['success_criteria'])} success criteria"
            )
        else:
            log_test(
                f"Workflow {workflow_name}: Success Criteria",
                "WARN",
                "No success criteria defined"
            )
        
        # Check failure handling
        if "failure_handling" in workflow:
            log_test(
                f"Workflow {workflow_name}: Failure Handling",
                "PASS",
                f"Defines {len(workflow['failure_handling'])} failure handling rules"
            )
        else:
            log_test(
                f"Workflow {workflow_name}: Failure Handling",
                "WARN",
                "No failure handling defined"
            )
        
        return True
        
    except yaml.YAMLError as e:
        log_test(
            f"Workflow {workflow_name}: YAML Parse",
            "FAIL",
            f"YAML parsing error: {str(e)}"
        )
        return False
    except Exception as e:
        log_test(
            f"Workflow {workflow_name}: Test",
            "FAIL",
            f"Error: {str(e)}"
        )
        return False

def test_all_workflows():
    """Test all workflow files"""
    print("\n=== Testing Workflow Templates ===")
    
    if not WORKFLOWS_DIR.exists():
        log_test(
            "Workflows Directory",
            "FAIL",
            f"Directory not found: {WORKFLOWS_DIR}"
        )
        return
    
    workflow_files = list(WORKFLOWS_DIR.glob("*.yaml")) + list(WORKFLOWS_DIR.glob("*.yml"))
    
    if not workflow_files:
        log_test(
            "Workflow Files",
            "FAIL",
            f"No workflow files found in {WORKFLOWS_DIR}"
        )
        return
    
    log_test(
        "Workflow Files Discovery",
        "PASS",
        f"Found {len(workflow_files)} workflow file(s)"
    )
    
    for workflow_file in workflow_files:
        test_workflow_file(workflow_file)

def generate_report():
    """Generate test report"""
    results_dir = Path(__file__).parent / "test_results"
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = results_dir / f"workflow_tests_mcc_{timestamp}.md"
    
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    warned = sum(1 for r in test_results if r["status"] == "WARN")
    total = len(test_results)
    
    report = f"""# Google Ads MCP Workflow Test Results

**Test Execution**: {datetime.now().isoformat()}
**MCC ID**: {MCC_ID} (211-993-1898)
**Workflows Directory**: {WORKFLOWS_DIR}

---

## Test Summary

- **Total Tests**: {total}
- **Passed**: {passed}
- **Failed**: {failed}
- **Warnings**: {warned}
- **Pass Rate**: {(passed/total*100) if total > 0 else 0:.1f}%

---

## Test Results

"""
    
    for result in test_results:
        status_icon = {"PASS": "✓", "FAIL": "✗", "WARN": "⚠"}.get(result["status"], "?")
        report += f"### {status_icon} {result['test_name']}\n\n"
        report += f"**Status**: {result['status']}\n\n"
        if result['details']:
            report += f"**Details**: {result['details']}\n\n"
        report += f"**Timestamp**: {result['timestamp']}\n\n"
        report += "---\n\n"
    
    report += f"""
## Notes

- These tests verify workflow structure and MCC context support
- Full workflow execution requires workflow engine and MCP client
- MCC context (customer_id) should be passed to workflow steps

## Workflow Files Tested

"""
    
    workflow_files = list(WORKFLOWS_DIR.glob("*.yaml")) + list(WORKFLOWS_DIR.glob("*.yml"))
    for wf_file in workflow_files:
        report += f"- `{wf_file.name}`\n"
    
    report += f"""
## Next Steps

1. Verify workflow engine can execute these workflows
2. Test workflows with actual MCP client connection
3. Verify MCC context is passed correctly to apps
4. Test workflow execution with real customer accounts
"""
    
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to: {report_file}")
    return report_file

def main():
    """Run workflow tests"""
    print("=" * 60)
    print("Google Ads MCP Workflow Testing")
    print(f"MCC ID: {MCC_ID} (211-993-1898)")
    print("=" * 60)
    
    test_all_workflows()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    warned = sum(1 for r in test_results if r["status"] == "WARN")
    total = len(test_results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Warnings: {warned}")
    
    report_file = generate_report()
    
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

