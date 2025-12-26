# Development Guidelines for AI Agents and Contributors

**Single Source of Truth for pdfa-service Development**

This document contains all guidelines for working with the pdfa-service repository. Use this as your primary reference for development practices, architecture, and testing standards.

---

## Project Overview

**pdfa-service** is a lightweight Python tool that converts regular PDFs, Office documents, and images into PDF/A-compliant, searchable documents with OCR using [OCRmyPDF](https://ocrmypdf.readthedocs.io/).

The service provides two interfaces:
1. **CLI** (`src/pdfa/cli.py`): Command-line tool registered as `pdfa-cli` entry point
2. **REST API** (`src/pdfa/api.py`): FastAPI endpoint (`POST /convert`) for file uploads

See [`README.md`](README.md) for user-facing documentation and setup instructions.

---

## Core Development Guidelines

### General Standards

- **Python Version**: Python 3.11+ required
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

- Use Python 3.11+ type hints throughout the codebase
- Use `Literal` types for configuration: `PdfaLevel = Literal["1", "2", "3"]`
- Use `pathlib.Path` for file path handling
- Maintain type coverage for IDE support and code clarity

### Code Quality & Linting Requirements

**All code must be linted before committing.** This is a mandatory step in the development workflow.

#### Formatting with Black

```bash
# Format all code
black src tests

# Check formatting without changes
black --check src tests
```

- **Line length**: 88 characters (Black default)
- **Target Python version**: 3.11+
- Black formatting is **non-negotiable** - all code must pass Black formatting

#### Linting with Ruff

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

#### Pre-Commit Checklist

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

#### Test Quality Requirements

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

#### Handling Linting Errors

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

## Project Architecture

### Dual Interface Design Principle

Both CLI and REST API must use the **same conversion function** (`convert_to_pdfa()`) to ensure feature parity and prevent divergence. This is the key architectural principle.

```
Input (CLI args / HTTP request)
    ↓
Validation & Parsing (cli.py / api.py)
    ↓
Shared Conversion Logic (converter.py)
    ↓
OCRmyPDF Library
    ↓
Output (Exit code / HTTP response)
```

### Error Handling Pattern

Both interfaces must translate low-level errors consistently:
- **File not found**: CLI returns exit code 1, API returns HTTP 400
- **OCRmyPDF failures**: CLI propagates exit code, API returns HTTP 500
- Shared logic in `converter.py` raises exceptions; interfaces handle translation

### Configuration Distribution

- Configuration (language, PDF/A level) is passed as **function arguments**, not environment variables
- This enables per-request configuration in API, easier testing, and avoids global state
- Example: `convert_to_pdfa(input_path, output_path, language="eng+deu", pdfa_level="2")`

### Dependency Abstraction

- OCRmyPDF is imported at module level (mockable in tests)
- Provide simple wrapper around `ocrmypdf.ocr()` for maintainability
- API responses include proper headers: `Content-Type: application/pdf`, `Content-Disposition: attachment`

### Temporary File Handling

- REST endpoint uses `TemporaryDirectory()` context manager for uploaded files
- Ensures cleanup even on errors
- Supports clean streaming semantics

### Office Document and Image Support

- Office/OpenDocument files (DOCX, PPTX, XLSX, ODT, ODS, ODP) are automatically detected
- Image files (JPG, PNG, TIFF, BMP, GIF) are automatically detected
- Office/ODF conversion to PDF happens via LibreOffice (CLI subprocess, no Python fallbacks)
- Image conversion to PDF happens via img2pdf library
- Format detection uses file extension in `format_converter.py` and `image_converter.py`
- Custom exceptions: `OfficeConversionError`, `UnsupportedFormatError`

### Job Event Logging System

The service includes a comprehensive event logging system that tracks all conversion decisions and milestones in MongoDB for post-execution analysis.

#### Event Types

All events are stored in `JobDocument.events` as a list of `JobEvent` objects:

- **format_conversion**: Tracks Office/Image→PDF conversions with timing
- **ocr_decision**: Logs OCR skip/perform decisions with statistics (tagged_pdf, has_text, no_text)
- **compression_selected**: Records compression profile selection and auto-switches
- **passthrough_mode**: Documents when PDFs bypass OCRmyPDF (PDF output + no OCR)
- **fallback_applied**: Captures fallback tier activations (Tier 2/3) with error details
- **job_timeout**: Logs job timeouts with runtime information
- **job_cleanup**: Records cleanup events (age_exceeded, timeout) with file details

#### Architecture

```
API Request → process_conversion_job()
    ↓
event_callback() created (async)
    ↓
converter.convert_to_pdfa(event_callback=event_callback)
    ↓
log_event() helper → event_callback() → event_logger.log_*_event()
    ↓
JobRepository.add_job_event() → MongoDB $push
```

#### Key Components

- `src/pdfa/event_logger.py`: 7 async helper functions for logging events
- `src/pdfa/converter.py`: `log_event()` helper + event logging at decision points
- `src/pdfa/api.py`: `event_callback()` creation in `process_conversion_job()`
- `src/pdfa/job_manager.py`: Cleanup/timeout event logging
- `src/pdfa/models.py`: `JobEvent` and `JobDocument.events` field
- `src/pdfa/repositories.py`: `add_job_event()` method using MongoDB `$push`

#### Event Callback Pattern

The `event_callback` parameter is optional in `convert_to_pdfa()`. When provided, it receives events from the sync conversion context and schedules them asynchronously:

```python
def log_event(event_type: str, **kwargs: Any) -> None:
    if event_callback:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(event_callback(event_type, **kwargs))
        except RuntimeError:
            asyncio.run(event_callback(event_type, **kwargs))
```

#### Example Event Flow

For a tagged PDF without OCR:
1. `format_conversion` - No conversion (PDF→PDF)
2. `passthrough_mode` - Enabled (pdf_output_no_ocr, tags_preserved=True)
3. `ocr_decision` - Skip (reason=tagged_pdf, has_struct_tree_root=True)

For a scanned PDF with fallback:
1. `format_conversion` - No conversion (PDF→PDF)
2. `ocr_decision` - Perform (reason=no_text, pages_with_text=0, text_ratio=0.0)
3. `fallback_applied` - Tier 2 (ghostscript_error, safe_mode_config, pdfa_level_downgrade)

#### Backward Compatibility

Jobs created before the event system was implemented work seamlessly:
- `events` field defaults to `[]` via `Field(default_factory=list)`
- No database migration required
- Old jobs simply have empty events list

#### WebSocket Event Broadcasting (US-004)

**Feature**: Live event display in web UI with real-time WebSocket broadcasting

All 7 event logging functions in `event_logger.py` broadcast events to connected WebSocket clients immediately after MongoDB persistence:

```python
async def log_ocr_decision_event(job_id: str, decision: str, reason: str, **kwargs):
    # 1. Create JobEvent
    event = JobEvent(...)

    # 2. Persist to MongoDB
    await repo.add_job_event(job_id, event)

    # 3. Broadcast via WebSocket (NEW)
    try:
        job_manager = get_job_manager()
        ws_message = JobEventMessage(
            job_id=job_id,
            event_type=event.event_type,
            timestamp=event.timestamp.isoformat(),
            message=event.message,  # English fallback
            details={
                **event.details,
                "_i18n_key": f"{event.event_type}.{decision}.{reason}",
                "_i18n_params": {"decision": decision, "reason": reason}
            }
        )

        # Best-effort async broadcast with timeout protection
        await asyncio.wait_for(
            job_manager.broadcast_to_job(job_id, ws_message.to_dict()),
            timeout=5.0
        )
    except Exception as e:
        logger.warning(f"Event broadcast failed: {e}")
        # MongoDB persistence already completed - continue
```

**WebSocket Protocol Extension**:

New server-to-client message type: `job_event`

```json
{
  "type": "job_event",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "ocr_decision",
  "timestamp": "2025-12-25T10:30:15.123Z",
  "message": "OCR skipped: tagged PDF detected",
  "details": {
    "decision": "skip",
    "reason": "tagged_pdf",
    "_i18n_key": "ocr_decision.skip.tagged_pdf",
    "_i18n_params": {"decision": "skip", "reason": "tagged_pdf"}
  }
}
```

**Key Properties**:

- **Best-Effort**: Broadcast failures don't block MongoDB persistence
- **Timeout Protection**: 5-second timeout prevents blocking on slow connections
- **Localization**: `_i18n_key` and `_i18n_params` enable frontend translation
- **Fallback**: English `message` always included for missing translations
- **Backward Compatible**: Old WebSocket clients ignore unknown `job_event` type

**Frontend Integration** (web_ui.html):

- Events displayed as expandable list below progress bar
- 4-language support (EN, DE, ES, FR) with parameter substitution
- Color-coded event types with emoji icons
- Screen reader announcements for high-priority events (3 of 7 types)
- ARIA accessibility attributes (role="log", aria-live="polite")
- Dark mode and reduced motion support

**Files Modified**:

- `src/pdfa/websocket_protocol.py`: Added `JobEventMessage` dataclass
- `src/pdfa/event_logger.py`: Added broadcasting to all 7 event functions
- `src/pdfa/web_ui.html`: UI components, CSS, i18n, JavaScript event handlers
- `tests/test_websocket_protocol.py`: Unit tests for JobEventMessage

**Performance**: ~350ms total overhead per job (7 events × 50ms), negligible compared to 10-60s conversion time

---

## File Reference

| File | Purpose |
|------|---------|
| `src/pdfa/converter.py` | Core conversion logic; single source of truth for OCRmyPDF integration; event logging |
| `src/pdfa/cli.py` | CLI with argparse; entry point is `main(argv)` |
| `src/pdfa/api.py` | FastAPI app; endpoint is `POST /convert`; job event callback integration |
| `src/pdfa/event_logger.py` | Job event logging helpers for MongoDB persistence; WebSocket broadcasting |
| `src/pdfa/websocket_protocol.py` | WebSocket message protocol schemas; JobEventMessage for live events |
| `src/pdfa/job_manager.py` | In-memory job management; cleanup/timeout event logging |
| `src/pdfa/models.py` | Pydantic models including JobDocument with events field |
| `src/pdfa/repositories.py` | MongoDB repositories including add_job_event() method |
| `src/pdfa/format_converter.py` | Office/ODF document format detection and LibreOffice conversion |
| `src/pdfa/image_converter.py` | Image format detection and img2pdf conversion |
| `src/pdfa/exceptions.py` | Custom exception definitions |
| `src/pdfa/logging_config.py` | Logging configuration and setup |
| `src/pdfa/__init__.py` | Package metadata (version) |
| `tests/conftest.py` | Pytest fixtures, OCRmyPDF mocking |
| `tests/test_cli.py` | CLI unit tests |
| `tests/test_api.py` | API endpoint unit tests |
| `tests/test_event_logger.py` | Event logger helper function tests |
| `tests/test_websocket_protocol.py` | WebSocket protocol message schema tests; JobEventMessage validation |
| `tests/test_converter_events.py` | Converter event logging integration tests |
| `tests/test_format_converter.py` | Format detection and Office conversion tests |
| `tests/test_image_converter.py` | Image format detection and conversion tests |
| `tests/test_cli_office.py` | CLI Office document handling tests |
| `tests/test_api_office.py` | API Office document handling tests |
| `tests/integration/test_conversion.py` | End-to-end PDF conversion integration tests |
| `tests/integration/test_office_conversion.py` | End-to-end Office conversion integration tests |
| `pyproject.toml` | Project metadata, dependencies, tool configs |

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

### Test Files Explained

- `test_cli.py`: Argument parsing, error cases, success paths
- `test_api.py`: Endpoint validation, file upload, response headers
- `test_format_converter.py`: Format detection, Office/ODF conversion
- `test_image_converter.py`: Image format detection and conversion
- `test_cli_office.py`: CLI Office document handling
- `test_api_office.py`: API Office document handling
- `integration/test_conversion.py`: Real OCRmyPDF PDF conversion
- `integration/test_office_conversion.py`: Real OCRmyPDF Office conversion

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
   # All 46 tests must pass
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

---

## Architectural Notes for Future Development

### Single Conversion Function

The design principle of a single `convert_to_pdfa()` function is intentional:
- Both CLI and API must call the same function to stay in sync
- Changes to conversion logic automatically apply to both interfaces
- Prevents feature divergence between CLI and API

### Error Handling

When adding new OCRmyPDF exception handling:
- Exceptions should be caught and translated in both CLI and API interfaces
- Maintain consistency: same error should produce same exit code/HTTP status
- Document error mappings in code comments

**Handled OCRmyPDF Exceptions:**

1. **`SubprocessOutputError`** (Ghostscript rendering failures)
   - **Cause**: Ghostscript cannot render the PDF during OCR processing
   - **Symptoms**: Errors like "/undefined in --runpdf--" or "Ghostscript rasterizing failed"
   - **Three-Tier Fallback Strategy**:
     1. **Tier 1**: Normal conversion with user-specified settings
     2. **Tier 2**: Safe-mode OCR with Ghostscript-friendly parameters:
        - Low DPI (100 instead of 150+)
        - Preserve vectors (no rasterization)
        - High JPEG quality (95)
        - No optimization (avoid extra processing)
        - Disable JBIG2 compression
        - Downgrade PDF/A level (3→2, 2→1) for better compatibility
     3. **Tier 3**: Conversion without OCR as last resort
   - **Rationale**: Some PDFs contain features that Ghostscript struggles with (complex graphics, certain compression types, problematic font embeddings, memory-intensive rendering). Using conservative parameters makes Ghostscript more likely to succeed while still preserving OCR capability.
   - **Tests**:
     - `tests/test_converter_errors.py::test_ghostscript_safe_mode_fallback_succeeds`
     - `tests/test_converter_errors.py::test_ghostscript_three_tier_fallback`
     - `tests/test_converter_errors.py::test_ghostscript_pdfa_level_downgrade`

2. **`EncryptedPdfError`**
   - **Cause**: PDF has password protection or encryption
   - **Action**: Fail immediately with clear error message
   - **Error Message**: "Cannot process encrypted PDF. Please remove encryption first."
   - **Tests**: `tests/test_converter_errors.py::test_encrypted_pdf_error`

3. **`InputFileError`**
   - **Cause**: PDF is corrupted or invalid
   - **Action**: Fail with descriptive error
   - **Error Message**: "Invalid or corrupted PDF file: {details}"
   - **Tests**: `tests/test_converter_errors.py::test_invalid_pdf_error`

4. **`PriorOcrFoundError`**
   - **Cause**: PDF already has an OCR text layer
   - **Action**: Log and continue (not an error condition)
   - **Tests**: `tests/test_converter_errors.py::test_prior_ocr_found_is_handled_gracefully`

**Fallback Decision Tree:**
```
PDF Conversion Attempt (Tier 1: Normal settings)
├─ Success → Done
├─ SubprocessOutputError (Ghostscript fails)
│  ├─ If OCR was enabled
│  │  ├─ TIER 2: Retry with safe-mode OCR
│  │  │  ├─ Parameters: Low DPI (100), preserve vectors, no optimization
│  │  │  ├─ PDF/A level: Downgrade if possible (3→2, 2→1)
│  │  │  ├─ Success → Done (logged as safe-mode fallback)
│  │  │  └─ SubprocessOutputError (safe-mode fails)
│  │  │     ├─ TIER 3: Retry without OCR (keep safe-mode compression)
│  │  │     │  ├─ Success → Done (logged as final fallback)
│  │  │     │  └─ Failure → Error: "All fallback strategies exhausted"
│  └─ If OCR was disabled → Error: "Ghostscript could not render the PDF"
├─ EncryptedPdfError → Error: "Cannot process encrypted PDF"
├─ InputFileError → Error: "Invalid or corrupted PDF file"
├─ PriorOcrFoundError → Log and continue
└─ Other exceptions → Re-raise with logging
```

### Configuration

New configuration parameters must be:
- Passed as function arguments, not globals or environment variables
- Type-hinted with appropriate types (Literal, str, int, etc.)
- Documented in docstrings and this AGENTS.md file
- Tested with multiple values

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
- [ ] Update this AGENTS.md if adding new patterns
- [ ] Ensure both CLI and API use same core function
- [ ] Run full test suite: `pytest` (all 46+ tests must pass)

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
- **Development documentation**: All development guidelines (AGENTS.md) are in English

### Documentation Standards (English - Primary)

- Code comments should explain "why" not "what" (code explains "what")
- Use clear examples in README and docstrings
- Keep AGENTS.md as single source of truth for development
- Document all public APIs with docstrings
- Example: `def convert_to_pdfa(...): """Convert PDF to PDF/A format."""`

### Multilingual User Documentation

User-facing documentation is maintained in **both English and German in parallel:**

**English documentation:**
- `README.md` - Main user guide
- `CLAUDE.md` - Quick reference for developers
- `OCR-SCANNER.md` - Setup guide for OCR use case
- `COMPRESSION.md` - PDF compression configuration guide

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

**Note**: Development documentation (AGENTS.md, this file) is English-only. Only user-facing documentation has German translations.

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

## Performance and Optimization

### Processing Times (Reference)

Typical OCR processing times per page:

| Hardware | Language | Time |
|----------|----------|------|
| Raspberry Pi 4 (ARM64) | English | 30-60s |
| Raspberry Pi 4 (ARM64) | English + German | 45-90s |
| Modern x86_64 CPU | English | 5-10s |
| Modern x86_64 CPU | English + German | 8-15s |

### Optimization Guidelines

- When modifying OCRmyPDF integration, consider impact on slow hardware
- Use resource limits appropriately (especially for Raspberry Pi)
- Profile before optimizing; only optimize hot paths
- Document performance implications in commit messages

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

This document is the **single source of truth** for all development practices in pdfa-service:

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

3. **Architecture and Code Quality**
   - Follow the architecture principles to maintain code quality
   - Use the file reference to understand codebase structure
   - Keep both CLI and API in sync by using shared functions
   - Maintain dual documentation (English + German)

4. **Development Workflow**
   - Execute TDD workflow for all changes
   - Tests must be written before or parallel to production code
   - Full test suite must pass before commit
   - Code must be formatted with `black` and pass `ruff` checks

### Documentation

- **Code developers**: Reference [AGENTS.md](AGENTS.md) for complete development guidelines
- **Users (English)**: See `README.md` for usage and `OCR-SCANNER.md` for setup
- **Users (Deutsch)**: See `README.de.md` for usage and `OCR-SCANNER.de.md` for setup

### Key Reminders

- **TDD is non-negotiable**: No tests, no code acceptance
- **English is default**: Every line of code and comment in English
- **Dual documentation**: Every user-facing doc change requires English + German updates
- **Test quality matters**: Mocked unit tests first, integration tests second
- **Keep it simple**: Write minimal code to make tests pass

**This is your checklist for every feature or fix: RED → GREEN → REFACTOR → TEST → FORMAT → DOCUMENT → COMMIT**
