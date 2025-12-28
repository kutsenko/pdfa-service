# Development Guidelines for AI Agents and Contributors

**Single Source of Truth for pdfa-service Development**

This document contains general development guidelines, workflow, and testing standards for the pdfa-service repository.

**For architectural patterns and design decisions, see [ARCHITECTURE.md](ARCHITECTURE.md).**

---

## Project Overview

**pdfa-service** is a lightweight Python tool that converts regular PDFs, Office documents, and images into PDF/A-compliant, searchable documents with OCR using [OCRmyPDF](https://ocrmypdf.readthedocs.io/).

The service provides two interfaces:
1. **CLI** (`src/pdfa/cli.py`): Command-line tool registered as `pdfa-cli` entry point
2. **REST API** (`src/pdfa/api.py`): FastAPI endpoint (`POST /convert`) for file uploads

See [`README.md`](README.md) for user-facing documentation and [`ARCHITECTURE.md`](ARCHITECTURE.md) for technical architecture.

---

## Core Development Guidelines

### General Standards

- **Python Version**: Python 3.13+ required
- **Code Style**: Follow PEP 8 conventions and [python.org best practices](https://www.python.org/dev/peps/)
- **Code Formatting**: Use `black` with 88-character line length
- **Linting**: Use `ruff` to check:
  - E (errors)
  - F (pyflakes)
  - W (warnings)
  - I (imports)
  - UP (upgrades)
  - N (naming)
  - D (docstrings - exceptions: D100, D101, D102, D103, D104, D105)

### Code Organization & Style

- **Module Organization**: Organize modules by responsibility
  - Example: CLI parsing, backend abstractions, utilities, domain logic
- **Method Design**: Keep methods focused on a single semantic level
  - Use concise names in line with Clean Code principles
  - Methods should do one thing well
- **Import Statements**: Do NOT wrap imports in `try`/`except` blocks
- **Primary Language**: **English is the default language for all code and development**
  - All code identifiers, variables, functions, classes must be in English
  - All comments, docstrings, and commit messages must be in English
  - Documentation is maintained in both English and German (see Language Policy below)

### Type Hints

- Use Python 3.13+ type hints throughout the codebase
- Use `Literal` types for configuration: `PdfaLevel = Literal["1", "2", "3"]`
- Use `pathlib.Path` for file path handling
- Maintain type coverage for IDE support and code clarity

---

## Code Quality & Linting Requirements

**All code must be linted before committing.** This is a mandatory step in the development workflow.

### Formatting with Black

```bash
# Format all code
black src tests

# Check formatting without changes
black --check src tests
```

- **Line length**: 88 characters (Black default)
- **Target Python version**: 3.13+
- Black formatting is **non-negotiable** - all code must pass Black formatting

### Linting with Ruff

```bash
# Lint and auto-fix issues
ruff check src tests --fix

# Lint without auto-fix (CI mode)
ruff check src tests
```

**Ruff checks enabled:**
- **E** (pycodestyle errors) - PEP 8 style violations
- **F** (Pyflakes) - Logical errors, unused imports
- **W** (pycodestyle warnings) - Code style issues
- **I** (isort) - Import sorting and organization
- **UP** (pyupgrade) - Upgrade syntax to newer Python versions
- **N** (pep8-naming) - Naming conventions (PEP 8)
- **D** (pydocstyle) - Docstring conventions (with exceptions)

**Docstring exceptions** (D100-D105): Module, class, and method docstrings are encouraged but not required for simple, self-explanatory code.

### Pre-Commit Checklist

Before every commit, run these commands in sequence:

```bash
# 1. Run full test suite
pytest

# 2. Format code
black src tests

# 3. Lint and fix issues
ruff check src tests --fix

# 4. Verify no linting errors remain
ruff check src tests

# 5. Check that tests still pass
pytest
```

**All steps must pass before committing.** If linting reveals issues:
1. Fix issues automatically with `--fix` flag
2. Review changes to ensure they're correct
3. Manually fix issues that can't be auto-fixed
4. Re-run tests to ensure fixes didn't break functionality

### Test Quality Requirements

**CRITICAL: All tests must pass. No failing tests are allowed in the codebase.**

- **Zero Tolerance for Failing Tests**: The test suite must be 100% green at all times
- **No Disabled Tests**: Do not disable, skip, or comment out failing tests
- **Fix or Remove**: If a test fails, either:
  1. Fix the test if it's incorrect
  2. Fix the code if the implementation is wrong
  3. Remove the test if it's no longer relevant (with justification)
- **Before Every Commit**: Run `pytest` and ensure all tests pass
- **CI/CD Requirement**: All tests must pass in CI before merging
- **Test Maintenance**: Keep tests up-to-date with code changes

If you discover a failing test:
1. Investigate the root cause immediately
2. Fix the test or the underlying code
3. Never commit code with known failing tests
4. Document any test fixes in commit messages

### Handling Linting Errors

**Critical errors (must fix):**
- E (syntax errors, undefined names)
- F (unused imports, undefined variables)
- Import sorting issues

**Warning-level issues (should fix):**
- Line length violations (split long lines)
- Naming convention violations
- Missing type hints

**Acceptable exceptions:**
- Long lines in HTML strings or URLs (use `# noqa: E501` sparingly)
- Complex regex patterns that exceed line length

---

## Testing Architecture - Test-Driven Development (TDD) Required

### TDD Principle - STRICTLY ENFORCED

**MANDATORY: All development MUST follow Test-Driven Development (TDD).**

This is not optional. The TDD workflow is:

1. **FIRST: Write failing tests** for the feature or fix you plan to implement
   - Write unit tests that define the expected behavior
   - Run tests and verify they FAIL (red phase)
   - This proves the tests are actually testing something

2. **SECOND: Write minimal production code** to make tests pass
   - Implement only what's needed to pass the tests
   - Run tests and verify they PASS (green phase)
   - Do not add extra functionality not covered by tests

3. **THIRD: Refactor code** while keeping tests green
   - Clean up, optimize, improve code quality
   - Run tests continuously to ensure nothing breaks
   - All tests must remain green (passing)

4. **REPEAT** for each new feature, bug fix, or behavior change

**ABSOLUTE RULE**:
- **NO production code may be written before tests exist for it**
- **NO pull requests will be accepted with untested code**
- **NO commits should contain implementation without corresponding tests**

This strict TDD approach ensures:
- Better code design (writing tests first forces you to think about interfaces)
- Comprehensive test coverage (all functionality is tested by definition)
- Confidence in changes (tests prevent regressions)
- Documentation through tests (tests show exactly how code should be used)
- Faster debugging (issues are caught immediately during development)

### Test Pyramid

1. **Unit Tests** (majority): Test CLI parsing, API validation, error handling with mocked OCRmyPDF
   - Run without system dependencies (Tesseract, Ghostscript)
   - Fast execution (< 10 seconds total)
   - Use `conftest.py` mocking for OCRmyPDF
   - **Must be written first, before production code**

2. **Integration Tests** (recommended): End-to-end with real OCRmyPDF
   - Require system dependencies
   - Skipped automatically if dependencies unavailable
   - Use `@pytest.mark.skipif(not HAS_TESSERACT, ...)` for conditional execution
   - **Can be written alongside or after unit tests**

### Testing Requirements

- **Mandatory**: Execute full test suite with `pytest` before every commit
- **Mandatory**: Run security scans before every PR (see Security Testing below)
- **Mandatory**: All new code must have passing tests before commit
- **Mandatory**: Tests must be written before (or parallel to) production code
- `conftest.py` provides `ocrmypdf` module mocking so tests run without Tesseract/Ghostscript
- Tests import from `src/` via `pythonpath` in `pyproject.toml`
- Run `pytest` to execute all available tests; integration tests auto-skip gracefully
- **TDD Workflow**: Start with failing tests, write production code to make them pass, refactor

### Security Testing

Before creating a pull request, **mandatory security scans must pass**:

#### Local Security Testing

Run locally before pushing:

```bash
# Test GitHub Actions locally with act
act -j security

# Or run pip-audit directly
pip install pip-audit
pip-audit --desc on --ignore-vuln GHSA-f83h-ghpp-7wcc
```

#### CI/CD Security Pipeline

The GitHub Actions workflow automatically runs:

1. **Python Dependency Scan** (`pip-audit`):
   - Scans all Python dependencies for known CVEs
   - Fails on HIGH or CRITICAL vulnerabilities
   - Runs parallel to unit tests for speed

2. **Docker Image Scan** (`trivy`):
   - Scans both full and minimal Docker images
   - Checks OS packages and Python dependencies
   - Fails on HIGH or CRITICAL vulnerabilities
   - Results uploaded to GitHub Security tab

#### Known Exceptions

- **GHSA-f83h-ghpp-7wcc** (pdfminer.six pickle deserialization):
  - Transitive dependency from ocrmypdf
  - Not exploitable in our use case (no CMap usage, CMAP_PATH not user-controllable)
  - Ignored pending upstream fix

#### Testing Infrastructure

- **act**: Run GitHub Actions workflows locally before pushing
- **Configuration**: `.actrc` configures Docker images for local testing
- **Documentation**: See "Testing GitHub Actions Locally" in README.md

### Smoke Test

After changes affecting CLI behavior:
```bash
pdfa-cli --help
```

---

## Common Pitfalls and Solutions

### asyncio Event Loop Issues in Tests

**Problem**: Integration tests fail with `RuntimeError: Runner.run() cannot be called from a running event loop` when using `asyncio.run()` inside code that's already running in a pytest-asyncio event loop.

**Root Cause**: `asyncio.run()` creates a new event loop, which conflicts with pytest-asyncio's existing event loop.

**Solution**: Use `new_event_loop()` pattern instead:

```python
# DON'T: Fails in pytest-asyncio context
asyncio.run(event_callback(event_type, **kwargs))

# DO: Compatible with pytest-asyncio
loop = asyncio.new_event_loop()
try:
    loop.run_until_complete(event_callback(event_type, **kwargs))
finally:
    loop.close()
```

**Location**: `src/pdfa/converter.py` line 280-284

### Coverage Configuration

**Problem**: E2E tests show ERROR status (no server running) and lower overall coverage percentage, causing CI failures.

**Root Cause**: E2E tests require running API server and aren't meant for coverage measurement.

**Solution**: Exclude E2E tests from coverage:

```bash
# In CI and local testing
pytest --cov=src --cov-report=term-missing --cov-fail-under=80 --ignore=tests/e2e
```

**Configuration**: `.github/workflows/dod-check.yml` line 56

**Realistic Baseline**: 80% coverage is achievable and meaningful; 90%+ often forces artificial test coverage.

### Security Scan False Positives

**Problem**: Security scans detect "hardcoded secrets" in test fixtures (e.g., `test_client_secret_67890`).

**Root Cause**: Grep-based secret detection doesn't distinguish between test fixtures and production code.

**Solution**: Exclude test files from secret scanning:

```bash
# In secret detection workflow
git grep -E "(password|secret|token|api_key)\s*=\s*['\"][^'\"]+['\"]" -- '*.py' ':!tests/*'
```

**Configuration**: `.github/workflows/dod-check.yml` line 116

### Docker Compose Test Timeouts

**Problem**: Docker Compose test job runs for 6+ hours without completing.

**Root Cause**: `docker-compose.test.yml` only provides infrastructure (MongoDB) but no test execution.

**Solution**: Add test-runner service to actually execute tests:

```yaml
test-runner:
  build:
    context: .
    dockerfile: Dockerfile
  depends_on:
    mongodb-test:
      condition: service_healthy
  environment:
    MONGODB_URI: "mongodb://admin:test_password@mongodb-test:27017/pdfa_test?authSource=admin"
    AUTH_ENABLED: "false"
  volumes:
    - .:/app
  working_dir: /app
  command: >
    sh -c "
      pip install -e '.[dev]' &&
      pytest tests/ --ignore=tests/e2e -v --cov=src --cov-fail-under=79
    "
```

**Configuration**: `docker-compose.test.yml` test-runner service

### Python Version Consistency

**Problem**: CI/CD failures due to Python version mismatches between local development, CI workflows, and Docker images.

**Root Cause**: Multiple files reference Python version, and they can drift out of sync during updates.

**Solution**: When updating Python version, update ALL of these files:

1. **Configuration Files**:
   - `pyproject.toml` (requires-python, black target-version, ruff target-version)
   - `Dockerfile` (FROM python:X.Y-slim)
   - `.github/workflows/docker-publish.yml` (setup-python in test and security jobs)

2. **English Documentation**:
   - `README.md` (system requirements, installation commands, version checks)
   - `AGENTS.md` (Python version requirement)
   - `CLAUDE.md` (type hints reference)
   - `DEFINITION_OF_DONE.md` (quality checklist)

3. **German Documentation**:
   - `README.de.md` (system requirements, installation commands, version checks)
   - `CLAUDE.de.md` (type hints reference)

**Verification**: After update, search for old version references:

```bash
grep -r "3\.11\|3\.12" --include="*.md" --include="*.toml" --include="*.yml" \
  --include="Dockerfile" | grep -v ".venv" | grep -v ".git"
# Should return no relevant matches
```

**Note**: Use feature branch workflow for Python version updates to validate CI/CD compatibility before merging.

---

## Development Workflow

### Quick Start

```bash
# Environment setup
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Common commands
pdfa-cli --help                    # CLI help
pytest                             # Run tests
pytest tests/test_cli.py::test_*   # Run specific test
black src tests                    # Format code
ruff check src tests --fix         # Lint and auto-fix
uvicorn pdfa.api:app --host 0.0.0.0 --port 8000  # Run API locally
```

### System Dependencies

Before running with real PDFs, install OCRmyPDF runtime dependencies. See [README.md#system-dependencies-by-distribution](README.md#system-dependencies-by-distribution) for your distribution.

**Required packages**:
- Tesseract OCR with language packs (English and German by default)
- Ghostscript
- qpdf
- LibreOffice (for Office document conversion)

Tests can run without these using mocked OCRmyPDF.

### TDD Development Workflow (Required)

**Follow this workflow for every feature or fix:**

1. **Write failing tests first** in `tests/`
   ```bash
   pytest tests/test_feature.py -v
   # Tests should FAIL (red phase)
   ```

2. **Write minimal production code** in `src/pdfa/` to make tests pass
   - Don't over-engineer; just make the failing tests pass
   - This is the "green phase"

3. **Run tests again** to verify they pass
   ```bash
   pytest tests/test_feature.py -v
   # Tests should PASS (green phase)
   ```

4. **Refactor code** while keeping tests passing (optional but encouraged)
   - Improve code structure, readability, efficiency
   - Ensure tests still pass after each refactor

5. **Run full test suite** before commit
   ```bash
   pytest
   # All tests must pass
   ```

6. **Format and lint code**
   ```bash
   black src tests
   ruff check src tests --fix
   ```

7. **Update documentation** if behavior changes
   - Update `README.md` (English) with examples
   - Update `README.de.md` (German) with examples
   - Update docstrings with new parameters or behavior

8. **Commit with clear message**
   ```bash
   git commit -m "Add feature X to handle scenario Y"
   ```
   - Use imperative mood ("Add" not "Added")
   - Explain the "why", not just the "what"
   - Reference issue numbers if applicable

### Parallel Development Philosophy

When implementing a feature:
- **Tests and production code develop in parallel**
- Write a test → write code to pass it → move to next test
- Never write all tests upfront and then code
- Never write all code and then test

This keeps the development cycle short (minutes, not hours) and prevents regressions.

### Commit Message Guidelines

- Use imperative mood: "Add feature" not "Added feature"
- Focus on the "why" rather than the "what"
- Keep to one line (< 72 characters) for summary
- Reference issue numbers if applicable: `Fixes #123`
- Example: `Fix OCR timeout on large files by increasing process timeout`

### New Features Checklist (TDD Required)

When adding a new feature, follow TDD strictly:

**Phase 1: Red (Write Failing Tests)**
- [ ] Create test file or add tests to existing test file
- [ ] Write unit tests with mocked dependencies (should FAIL)
- [ ] Run tests: `pytest tests/test_feature.py -v` (expect failures)

**Phase 2: Green (Write Minimal Code)**
- [ ] Implement feature in shared logic (converter.py) - minimal code to pass tests
- [ ] Add CLI support (cli.py) - minimal code to pass tests
- [ ] Add API support (api.py) - minimal code to pass tests
- [ ] Run tests: `pytest tests/test_feature.py -v` (all should PASS)

**Phase 3: Refactor (Improve Code While Tests Stay Green)**
- [ ] Refactor code for clarity and efficiency
- [ ] Run tests after each refactor: `pytest tests/test_feature.py -v`
- [ ] Add integration tests (optional but recommended)

**Phase 4: Documentation and Polish**
- [ ] Update README.md (English) with usage examples
- [ ] Update README.de.md (German) with translated examples
- [ ] Update docstrings and code comments
- [ ] Update AGENTS.md or ARCHITECTURE.md if adding new patterns
- [ ] Ensure both CLI and API use same core function
- [ ] Run full test suite: `pytest` (all tests must pass)

**Phase 5: Final Quality Checks**
- [ ] Format with `black src tests`
- [ ] Lint with `ruff check src tests --fix`
- [ ] Run smoke tests: `pdfa-cli --help`
- [ ] All tests pass: `pytest`

**Never skip Phase 1**: Tests must be written BEFORE production code. This is non-negotiable for this project.

---

## Documentation and Language Policy

### English as Default Language

**English is the default language for this project:**

- **Code**: All code identifiers, variables, functions, classes, and methods must be in English
- **Comments**: All code comments must be in English
- **Docstrings**: All Python docstrings must be in English
- **Commit messages**: All git commit messages must be in English
- **Issues and PRs**: Discussion in English unless in a language-specific context
- **Development documentation**: All development guidelines (AGENTS.md, ARCHITECTURE.md) are in English

### Documentation Standards (English - Primary)

- Code comments should explain "why" not "what" (code explains "what")
- Use clear examples in README and docstrings
- Keep AGENTS.md as single source of truth for development workflow
- Keep ARCHITECTURE.md as single source of truth for technical architecture
- Document all public APIs with docstrings
- Example: `def convert_to_pdfa(...): """Convert PDF to PDF/A format."""`

### Multilingual User Documentation

User-facing documentation is maintained in **both English and German in parallel:**

**English documentation:**
- `README.md` - Main user guide
- `CLAUDE.md` - Quick reference for developers
- `OCR-SCANNER.md` - Setup guide for OCR use case
- `COMPRESSION.md` - PDF compression configuration guide
- `ARCHITECTURE.md` - Technical architecture documentation

**German documentation (maintained in parallel):**
- `README.de.md` - German translation of README.md
- `CLAUDE.de.md` - German translation of CLAUDE.md
- `OCR-SCANNER.de.md` - German translation of OCR-SCANNER.md
- `COMPRESSION.de.md` - German translation of COMPRESSION.md

**Rules for maintaining dual documentation:**
1. When you update `README.md`, also update `README.de.md`
2. When you update `CLAUDE.md`, also update `CLAUDE.de.md`
3. When you update `OCR-SCANNER.md`, also update `OCR-SCANNER.de.md`
4. When you update `COMPRESSION.md`, also update `COMPRESSION.de.md`
5. **English is the source language** - always write documentation in English first, then translate to German
6. Use `TRANSLATIONS.md` to track status of translations
7. Keep translations accurate and up-to-date (not allowed to fall behind)
8. Test both English and German documentation for accuracy

**Note**: Development documentation (AGENTS.md, ARCHITECTURE.md) is English-only. Only user-facing documentation has German translations.

---

## Code Quality and Maintainability

### Avoiding Over-Engineering

- Don't add error handling for scenarios that can't happen
- Trust internal code and framework guarantees
- Only validate at system boundaries (user input, external APIs)
- Don't create helpers or abstractions for one-time operations
- Implement the minimum complexity needed for the current task

### Example: What NOT to Do

```python
# DON'T: Over-engineered error handling
try:
    text = document_content[0]  # Internal code, not user input
except IndexError:
    logger.error("Content missing")  # Can't happen if we control it
```

```python
# DO: Trust internal guarantees
text = document_content[0]  # We ensure list is non-empty at boundaries
```

### Code Comments

- Write all comments and docstrings in English
- Comments should explain non-obvious logic
- Don't comment obvious code:
  ```python
  # DON'T: Obvious comment
  x = x + 1  # Increment x

  # DO: Explain why, not what
  x += 1  # Account for 0-indexed offset in OCR results
  ```

---

## Security Considerations

### Automated Vulnerability Scanning

The project uses automated security scanning in the CI/CD pipeline:

- **pip-audit**: Scans Python dependencies for CVEs from PyPI Advisory Database
- **Trivy**: Scans Docker images for vulnerabilities in OS packages and dependencies
- **Dependabot**: Automatically creates PRs for dependency updates and security patches
- **GitHub Security Tab**: Aggregates vulnerability reports for review

CI pipeline **fails** if HIGH or CRITICAL vulnerabilities are detected. See "Security Testing" section for details.

### Input Validation

- Validate all user inputs at boundaries (CLI, API)
- Validate file uploads (MIME type, size)
- Check file paths are within expected directories
- Don't assume internal code produces valid output (document assumptions)

### File Operations

- Use `pathlib.Path` for safe path handling
- Use `TemporaryDirectory()` context manager for cleanup
- Never construct paths by string concatenation
- Validate file extensions match expected formats

### API Security

- Use basic auth or reverse proxy for network access (see docker-compose examples)
- Set reasonable file size limits
- Implement rate limiting for production deployments
- Log all API requests for audit trails

---

## References

- [OCRmyPDF Documentation](https://ocrmypdf.readthedocs.io/)
- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [black Documentation](https://black.readthedocs.io/)
- [ruff Documentation](https://docs.astral.sh/ruff/)

---

## Summary

This document is the **single source of truth** for development workflow and testing standards in pdfa-service.

### Core Principles

1. **English is Default Language**
   - All code, comments, docstrings, and commits in English
   - User documentation maintained in both English and German

2. **Test-Driven Development (TDD) is Required**
   - Write tests first (RED phase)
   - Write minimal code to pass tests (GREEN phase)
   - Refactor while keeping tests passing (REFACTOR phase)
   - No production code without tests
   - Tests and code develop in parallel

3. **Code Quality**
   - Black formatting (mandatory)
   - Ruff linting (mandatory)
   - All tests passing (mandatory)
   - Clear documentation (mandatory)

4. **Development Workflow**
   - Execute TDD workflow for all changes
   - Tests must be written before or parallel to production code
   - Full test suite must pass before commit
   - Code must be formatted with `black` and pass `ruff` checks

### Documentation Structure

- **AGENTS.md** (this file): Development workflow, TDD, testing, code quality
- **ARCHITECTURE.md**: Technical architecture, design patterns, file reference
- **README.md**: User guide (English)
- **README.de.md**: User guide (German)

### Key Reminders

- **TDD is non-negotiable**: No tests, no code acceptance
- **English is default**: Every line of code and comment in English
- **Dual documentation**: Every user-facing doc change requires English + German updates
- **Test quality matters**: Mocked unit tests first, integration tests second
- **Keep it simple**: Write minimal code to make tests pass

**This is your checklist for every feature or fix: RED → GREEN → REFACTOR → TEST → FORMAT → DOCUMENT → COMMIT**

**For architectural details, see [ARCHITECTURE.md](ARCHITECTURE.md).**
