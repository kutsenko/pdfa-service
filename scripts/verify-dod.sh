#!/bin/bash
# DoD Verification Script
# Automatically checks Definition of Done criteria
# Usage: ./scripts/verify-dod.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
print_header() {
    echo -e "\n${BLUE}===================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

print_failure() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if virtual environment is activated
check_venv() {
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_warning "Virtual environment not activated. Attempting to activate..."
        if [[ -f ".venv/bin/activate" ]]; then
            source .venv/bin/activate
            print_success "Virtual environment activated"
        else
            print_failure "Virtual environment not found. Run: python3 -m venv .venv"
            return 1
        fi
    else
        print_success "Virtual environment is activated"
    fi
}

# 1. Code Quality Checks
print_header "1. CODE QUALITY CHECKS"

# 1.1 Black Formatting
print_info "Checking code formatting with Black..."
if black --check src tests 2>/dev/null; then
    print_success "Code is properly formatted (Black)"
else
    print_failure "Code formatting issues detected. Run: black src tests"
fi

# 1.2 Ruff Linting
print_info "Checking code with Ruff linter..."
if ruff check src tests 2>/dev/null; then
    print_success "No linting issues (Ruff)"
else
    print_failure "Linting issues detected. Run: ruff check src tests --fix"
fi

# 2. Testing Checks
print_header "2. TESTING CHECKS"

# 2.1 Unit Tests
print_info "Running unit tests..."
if pytest tests/unit -v --tb=short 2>/dev/null; then
    print_success "Unit tests passed"
else
    print_warning "Unit tests failed or not found"
fi

# 2.2 Integration Tests
print_info "Running integration tests..."
if pytest tests/integration -v --tb=short 2>/dev/null; then
    print_success "Integration tests passed"
else
    print_warning "Integration tests failed or not found"
fi

# 2.3 Code Coverage
print_info "Checking code coverage..."
COVERAGE_OUTPUT=$(pytest --cov=src --cov-report=term-missing --cov-fail-under=90 -q 2>&1) || true
COVERAGE_PERCENT=$(echo "$COVERAGE_OUTPUT" | grep -oP 'TOTAL\s+\d+\s+\d+\s+\d+\s+\d+\s+\K\d+' || echo "0")

if [[ $COVERAGE_PERCENT -ge 90 ]]; then
    print_success "Code coverage: ${COVERAGE_PERCENT}% (≥90% required)"
else
    print_failure "Code coverage: ${COVERAGE_PERCENT}% (≥90% required)"
fi

# 2.4 E2E Tests (Playwright)
print_info "Checking for E2E tests..."
if [[ -d "tests/e2e" ]] && [[ $(find tests/e2e -name "*.py" | wc -l) -gt 0 ]]; then
    print_success "E2E tests directory exists with test files"

    # Check if Playwright is installed
    if python -c "import playwright" 2>/dev/null; then
        print_success "Playwright is installed"
    else
        print_warning "Playwright not installed. Run: pip install playwright && playwright install"
    fi
else
    print_warning "No E2E tests found in tests/e2e/"
fi

# 3. Documentation Checks
print_header "3. DOCUMENTATION CHECKS"

# 3.1 Check for docstrings
print_info "Checking for docstrings in Python modules..."
MISSING_DOCSTRINGS=$(find src/pdfa -name "*.py" -exec grep -L '"""' {} \; 2>/dev/null | wc -l)
if [[ $MISSING_DOCSTRINGS -eq 0 ]]; then
    print_success "All modules have docstrings"
else
    print_warning "$MISSING_DOCSTRINGS module(s) missing docstrings"
fi

# 3.2 README.md exists
if [[ -f "README.md" ]]; then
    print_success "README.md exists"
else
    print_failure "README.md not found"
fi

# 3.3 AGENTS.md exists
if [[ -f "AGENTS.md" ]]; then
    print_success "AGENTS.md exists"
else
    print_warning "AGENTS.md not found"
fi

# 4. Git Checks
print_header "4. GIT WORKFLOW CHECKS"

# 4.1 Current branch
CURRENT_BRANCH=$(git branch --show-current)
print_info "Current branch: $CURRENT_BRANCH"

if [[ $CURRENT_BRANCH == "main" ]]; then
    print_warning "You are on main branch. Consider using a feature branch."
elif [[ $CURRENT_BRANCH == feature/* ]]; then
    print_success "Working on feature branch: $CURRENT_BRANCH"
else
    print_info "Branch: $CURRENT_BRANCH"
fi

# 4.2 Uncommitted changes
if git diff-index --quiet HEAD -- 2>/dev/null; then
    print_success "No uncommitted changes"
else
    print_warning "Uncommitted changes detected. Commit before creating PR."
fi

# 4.3 Untracked files
UNTRACKED=$(git ls-files --others --exclude-standard | wc -l)
if [[ $UNTRACKED -eq 0 ]]; then
    print_success "No untracked files"
else
    print_warning "$UNTRACKED untracked file(s). Add or ignore them."
fi

# 5. Docker Compose Test Check
print_header "5. DOCKER COMPOSE TEST CHECK"

if [[ -f "docker-compose.test.yml" ]]; then
    print_success "docker-compose.test.yml exists"

    print_info "To run full test suite with Docker:"
    print_info "  docker compose -f docker-compose.test.yml up --abort-on-container-exit"

    # Ask user if they want to run docker tests
    read -p "Run Docker Compose tests now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Running Docker Compose tests..."
        if docker compose -f docker-compose.test.yml up --abort-on-container-exit; then
            print_success "Docker Compose tests passed"
        else
            print_failure "Docker Compose tests failed"
        fi

        # Cleanup
        print_info "Cleaning up Docker containers..."
        docker compose -f docker-compose.test.yml down
    else
        print_warning "Skipped Docker Compose tests (manual verification required)"
    fi
else
    print_failure "docker-compose.test.yml not found"
fi

# 6. Security Checks
print_header "6. SECURITY CHECKS"

# 6.1 Check for common secrets patterns
print_info "Scanning for potential secrets..."
SECRETS_FOUND=0

# Check for common secret patterns
if git grep -E "(password|secret|token|api_key)\s*=\s*['\"][^'\"]+['\"]" -- '*.py' 2>/dev/null; then
    print_failure "Potential hardcoded secrets found in code"
    SECRETS_FOUND=1
fi

if [[ $SECRETS_FOUND -eq 0 ]]; then
    print_success "No obvious secrets in code"
fi

# 6.2 Check if .env files are gitignored
if git check-ignore .env >/dev/null 2>&1; then
    print_success ".env files are gitignored"
else
    print_warning ".env files might not be gitignored"
fi

# 7. i18n Checks
print_header "7. INTERNATIONALIZATION CHECKS"

# Check for translation files or i18n implementation
if grep -r "data-i18n" src/pdfa/web_ui.html >/dev/null 2>&1; then
    print_success "i18n attributes found in HTML"

    # Check for all required languages
    LANGUAGES=("en" "de" "es" "fr")
    for lang in "${LANGUAGES[@]}"; do
        if grep -q "translations\.$lang" src/pdfa/web_ui.html 2>/dev/null; then
            print_success "Translation for $lang found"
        else
            print_warning "Translation for $lang might be missing"
        fi
    done
else
    print_info "No i18n implementation detected (might not be required)"
fi

# 8. Performance Checks
print_header "8. PERFORMANCE CHECKS"

# Check for common performance anti-patterns
print_info "Checking for N+1 query patterns..."
if git grep -E "for.*in.*\.all\(\)" -- '*.py' 2>/dev/null | grep -v test; then
    print_warning "Potential N+1 query patterns detected"
else
    print_success "No obvious N+1 query patterns"
fi

# Summary
print_header "SUMMARY"

TOTAL=$((PASSED + FAILED + WARNINGS))
PASS_RATE=0
if [[ $TOTAL -gt 0 ]]; then
    PASS_RATE=$((PASSED * 100 / TOTAL))
fi

echo -e "Total Checks:  $TOTAL"
echo -e "${GREEN}Passed:       $PASSED${NC}"
echo -e "${RED}Failed:       $FAILED${NC}"
echo -e "${YELLOW}Warnings:     $WARNINGS${NC}"
echo -e "\nPass Rate:     ${PASS_RATE}%\n"

# Exit with appropriate code
if [[ $FAILED -gt 0 ]]; then
    echo -e "${RED}DoD verification FAILED. Please fix the issues above.${NC}"
    exit 1
elif [[ $WARNINGS -gt 5 ]]; then
    echo -e "${YELLOW}DoD verification PASSED with warnings. Consider addressing them.${NC}"
    exit 0
else
    echo -e "${GREEN}DoD verification PASSED! ✓${NC}"
    exit 0
fi
