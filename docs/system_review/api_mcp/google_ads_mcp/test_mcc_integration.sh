#!/bin/bash

# Google Ads MCP MCC Integration Test Script
# Tests MCC account 211-993-1898 (2119931898) integration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/test_results"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
REPORT_FILE="${RESULTS_DIR}/test_results_mcc_${TIMESTAMP}.md"
MCC_ID="2119931898"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create results directory
mkdir -p "${RESULTS_DIR}"

# Initialize report
cat > "${REPORT_FILE}" << EOF
# Google Ads MCP MCC Integration Test Results

**Test Execution**: $(date)
**MCC ID**: ${MCC_ID} (211-993-1898)
**Test Environment**: $(uname -a)

---

## Test Summary

EOF

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Function to log test result
log_test() {
    local test_name="$1"
    local status="$2"
    local details="$3"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    if [ "$status" = "PASS" ]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "${GREEN}✓${NC} $test_name"
        echo "- [x] **$test_name**: PASS" >> "${REPORT_FILE}"
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "${RED}✗${NC} $test_name"
        echo "- [ ] **$test_name**: FAIL" >> "${REPORT_FILE}"
    fi
    
    if [ -n "$details" ]; then
        echo "  $details" >> "${REPORT_FILE}"
    fi
    echo "" >> "${REPORT_FILE}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "=========================================="
echo "Google Ads MCP MCC Integration Testing"
echo "MCC ID: ${MCC_ID} (211-993-1898)"
echo "=========================================="
echo ""

# Phase 1: Configuration Verification
echo "Phase 1: Configuration Verification"
echo "-----------------------------------"

# Test 1.1: MCC Configuration Check
echo "Test 1.1: Checking MCC configuration in google-ads.yaml..."
if grep -q "login_customer_id: ${MCC_ID}" "${SCRIPT_DIR}/google-ads.yaml"; then
    log_test "MCC Configuration Check" "PASS" "login_customer_id set to ${MCC_ID}"
else
    log_test "MCC Configuration Check" "FAIL" "login_customer_id not found or incorrect"
fi

# Test 1.2: Verify all required fields exist
echo "Test 1.2: Checking required configuration fields..."
REQUIRED_FIELDS=("client_id" "client_secret" "refresh_token" "developer_token" "login_customer_id")
MISSING_FIELDS=()

for field in "${REQUIRED_FIELDS[@]}"; do
    if ! grep -q "^${field}:" "${SCRIPT_DIR}/google-ads.yaml"; then
        MISSING_FIELDS+=("$field")
    fi
done

if [ ${#MISSING_FIELDS[@]} -eq 0 ]; then
    log_test "Required Fields Check" "PASS" "All required fields present"
else
    log_test "Required Fields Check" "FAIL" "Missing fields: ${MISSING_FIELDS[*]}"
fi

# Test 1.3: Check for placeholder values
echo "Test 1.3: Checking for placeholder values..."
if grep -q "YOUR_.*_HERE" "${SCRIPT_DIR}/google-ads.yaml"; then
    PLACEHOLDERS=$(grep "YOUR_.*_HERE" "${SCRIPT_DIR}/google-ads.yaml" | cut -d: -f1)
    log_test "Placeholder Check" "FAIL" "Found placeholders: ${PLACEHOLDERS}"
else
    log_test "Placeholder Check" "PASS" "No placeholder values found"
fi

# Phase 2: MCP Server Connectivity
echo ""
echo "Phase 2: MCP Server Connectivity"
echo "-----------------------------------"

# Test 2.1: Check Python and venv
echo "Test 2.1: Checking Python environment..."
if [ -d "${SCRIPT_DIR}/venv" ]; then
    PYTHON_EXEC="${SCRIPT_DIR}/venv/bin/python"
    if [ -f "$PYTHON_EXEC" ]; then
        log_test "Python Environment" "PASS" "Virtual environment found"
    else
        log_test "Python Environment" "FAIL" "venv/bin/python not found"
    fi
else
    log_test "Python Environment" "FAIL" "venv directory not found"
fi

# Test 2.2: Test server initialization
echo "Test 2.2: Testing server initialization..."
if [ -f "${SCRIPT_DIR}/test_server.py" ]; then
    cd "${SCRIPT_DIR}"
    if [ -f "${PYTHON_EXEC}" ]; then
        if "${PYTHON_EXEC}" test_server.py > "${RESULTS_DIR}/server_init_test.log" 2>&1; then
            log_test "Server Initialization" "PASS" "Server initialized successfully"
        else
            log_test "Server Initialization" "FAIL" "Server initialization failed. Check ${RESULTS_DIR}/server_init_test.log"
        fi
    else
        log_test "Server Initialization" "FAIL" "Python executable not found"
    fi
else
    log_test "Server Initialization" "FAIL" "test_server.py not found"
fi

# Test 2.3: Check MCP configuration (if Claude Code is available)
echo "Test 2.3: Checking MCP configuration..."
if command_exists claude; then
    if claude mcp list 2>/dev/null | grep -q "google-ads"; then
        if claude mcp list 2>/dev/null | grep "google-ads" | grep -q "✓ Connected"; then
            log_test "Claude Code MCP Connection" "PASS" "google-ads MCP connected"
        else
            log_test "Claude Code MCP Connection" "FAIL" "google-ads MCP not connected"
        fi
    else
        log_test "Claude Code MCP Connection" "FAIL" "google-ads MCP not configured"
    fi
else
    log_test "Claude Code MCP Connection" "SKIP" "claude command not available"
fi

# Phase 3: Configuration File Validation
echo ""
echo "Phase 3: Configuration File Validation"
echo "-----------------------------------"

# Test 3.1: Validate YAML syntax
echo "Test 3.1: Validating YAML syntax..."
if command_exists python3; then
    if python3 -c "import yaml; yaml.safe_load(open('${SCRIPT_DIR}/google-ads.yaml'))" 2>/dev/null; then
        log_test "YAML Syntax Validation" "PASS" "YAML syntax is valid"
    else
        log_test "YAML Syntax Validation" "FAIL" "YAML syntax error"
    fi
else
    log_test "YAML Syntax Validation" "SKIP" "Python3 not available"
fi

# Test 3.2: Check config file permissions
echo "Test 3.2: Checking config file permissions..."
if [ -r "${SCRIPT_DIR}/google-ads.yaml" ]; then
    log_test "Config File Readable" "PASS" "google-ads.yaml is readable"
else
    log_test "Config File Readable" "FAIL" "google-ads.yaml is not readable"
fi

# Generate summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "Total Tests: ${TESTS_TOTAL}"
echo -e "${GREEN}Passed: ${TESTS_PASSED}${NC}"
echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"

# Append summary to report
cat >> "${REPORT_FILE}" << EOF

---

## Test Summary

- **Total Tests**: ${TESTS_TOTAL}
- **Passed**: ${TESTS_PASSED}
- **Failed**: ${TESTS_FAILED}
- **Pass Rate**: $(awk "BEGIN {printf \"%.1f\", (${TESTS_PASSED}/${TESTS_TOTAL})*100}")%

## Next Steps

1. If configuration tests passed, proceed with MCP connectivity tests
2. If MCC ID is correct, test account access
3. Review failed tests and fix configuration issues
4. Run app and workflow tests after connectivity is verified

## Notes

- MCC ID format: ${MCC_ID} (no dashes)
- Config file: ${SCRIPT_DIR}/google-ads.yaml
- Test results: ${REPORT_FILE}
- Server logs: ${RESULTS_DIR}/server_init_test.log

EOF

echo ""
echo "Detailed report saved to: ${REPORT_FILE}"

# Exit with error if any tests failed
if [ ${TESTS_FAILED} -gt 0 ]; then
    exit 1
else
    exit 0
fi

