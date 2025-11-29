# Development Guidelines for AI Agents and Contributors

**Single Source of Truth for pdfa-service Development**

This document contains all guidelines for working with the pdfa-service repository. Use this as your primary reference for development practices, architecture, and testing standards.

---

## Project Overview

**pdfa-service** is a lightweight Python tool that converts regular PDFs and Office documents into PDF/A-compliant, searchable documents with OCR using [OCRmyPDF](https://ocrmypdf.readthedocs.io/).

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
- **Documentation**: Write all documentation, comments, and identifiers in English

### Type Hints

- Use Python 3.11+ type hints throughout the codebase
- Use `Literal` types for configuration: `PdfaLevel = Literal["1", "2", "3"]`
- Use `pathlib.Path` for file path handling
- Maintain type coverage for IDE support and code clarity

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

### Office Document Support

- Office/OpenDocument files (DOCX, PPTX, XLSX, ODT, ODS, ODP) are automatically detected
- Conversion to PDF happens via LibreOffice (CLI subprocess, no Python fallbacks)
- Format detection uses file extension in `format_converter.py`
- Custom exceptions: `OfficeConversionError`, `UnsupportedFormatError`

---

## File Reference

| File | Purpose |
|------|---------|
| `src/pdfa/converter.py` | Core conversion logic; single source of truth for OCRmyPDF integration |
| `src/pdfa/cli.py` | CLI with argparse; entry point is `main(argv)` |
| `src/pdfa/api.py` | FastAPI app; endpoint is `POST /convert` |
| `src/pdfa/format_converter.py` | Office/ODF document format detection and LibreOffice conversion |
| `src/pdfa/exceptions.py` | Custom exception definitions |
| `src/pdfa/logging_config.py` | Logging configuration and setup |
| `src/pdfa/__init__.py` | Package metadata (version) |
| `tests/conftest.py` | Pytest fixtures, OCRmyPDF mocking |
| `tests/test_cli.py` | CLI unit tests |
| `tests/test_api.py` | API endpoint unit tests |
| `tests/test_format_converter.py` | Format detection and Office conversion tests |
| `tests/test_cli_office.py` | CLI Office document handling tests |
| `tests/test_api_office.py` | API Office document handling tests |
| `tests/integration/test_conversion.py` | End-to-end PDF conversion integration tests |
| `tests/integration/test_office_conversion.py` | End-to-end Office conversion integration tests |
| `pyproject.toml` | Project metadata, dependencies, tool configs |

---

## Testing Architecture

### Test Pyramid

1. **Unit Tests** (majority): Test CLI parsing, API validation, error handling with mocked OCRmyPDF
   - Run without system dependencies (Tesseract, Ghostscript)
   - Fast execution (< 10 seconds total)
   - Use `conftest.py` mocking for OCRmyPDF

2. **Integration Tests** (optional): End-to-end with real OCRmyPDF
   - Require system dependencies
   - Skipped automatically if dependencies unavailable
   - Use `@pytest.mark.skipif(not HAS_TESSERACT, ...)` for conditional execution

### Testing Requirements

- **Mandatory**: Execute full test suite with `pytest` before every commit
- `conftest.py` provides `ocrmypdf` module mocking so tests run without Tesseract/Ghostscript
- Tests import from `src/` via `pythonpath` in `pyproject.toml`
- Run `pytest` to execute all available tests; integration tests auto-skip gracefully
- When adding features, add unit tests with mocked OCRmyPDF first, then optional integration tests

### Smoke Test

After changes affecting CLI behavior:
```bash
pdfa-cli --help
```

### Test Files Explained

- `test_cli.py`: Argument parsing, error cases, success paths
- `test_api.py`: Endpoint validation, file upload, response headers
- `test_format_converter.py`: Format detection, Office/ODF conversion
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

### Required Steps Before Commit

1. Make changes to `src/pdfa/` or `tests/`
2. Format code: `black src tests`
3. Lint: `ruff check src tests --fix`
4. Run tests: `pytest` (must pass)
5. Update `README.md` if behavior changes
6. Commit with concise, imperative message:
   ```bash
   git commit -m "Add feature X to handle scenario Y"
   ```

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

### Configuration

New configuration parameters must be:
- Passed as function arguments, not globals or environment variables
- Type-hinted with appropriate types (Literal, str, int, etc.)
- Documented in docstrings and this AGENTS.md file
- Tested with multiple values

### New Features Checklist

When adding a new feature:
- [ ] Write unit tests with mocked dependencies first
- [ ] Implement feature in shared logic (converter.py)
- [ ] Add CLI support (cli.py)
- [ ] Add API support (api.py)
- [ ] Ensure both interfaces use same core function
- [ ] Update README.md with usage examples
- [ ] Add integration tests (optional but recommended)
- [ ] Update this AGENTS.md if adding new patterns
- [ ] Format with `black` and lint with `ruff`
- [ ] All tests pass before committing

---

## Documentation and Language

### Documentation Standards

- All documentation must be in English
- Comments should explain "why" not "what" (code explains "what")
- Use clear examples in README and docstrings
- Keep AGENTS.md as single source of truth

### Multilingual Documentation

Translations of user-facing documentation are maintained separately:
- English: `README.md`, `CLAUDE.md`, `OCR-SCANNER.md`
- German: `README.de.md`, `CLAUDE.de.md`, `OCR-SCANNER.de.md`
- See `TRANSLATIONS.md` for framework and status

**Important**: Development documentation (this file) is English-only.

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

- Follow the architecture principles to maintain code quality
- Use the file reference to understand codebase structure
- Execute the development workflow for all changes
- Write tests first, implement second
- Keep both CLI and API in sync by using shared functions
- Commit early, commit often, with clear messages

For user-facing questions, see `README.md`. For setup instructions, see `OCR-SCANNER.md`.
