# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

### Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Common Commands
- **CLI Help**: `pdfa-cli --help`
- **Run Tests**: `pytest`
- **Run Single Test**: `pytest tests/test_cli.py::test_parse_args`
- **Format Code**: `black src tests`
- **Lint**: `ruff check src tests`
- **Run API Locally**: `uvicorn pdfa.api:app --host 0.0.0.0 --port 8000`

### System Dependencies
Before running with real PDFs, install OCRmyPDF runtime dependencies:
```bash
# Ubuntu 24.04
sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu ghostscript qpdf
```

Tests can run without these dependencies using mocked OCRmyPDF.

## Project Architecture

**pdfa-service** is a lightweight Python tool that converts regular PDFs into PDF/A-compliant documents with OCR using [OCRmyPDF](https://ocrmypdf.readthedocs.io/). It has two interfaces:

### Dual Interface Design
1. **CLI** (`src/pdfa/cli.py`): Command-line tool registered as `pdfa-cli` entry point
2. **REST API** (`src/pdfa/api.py`): FastAPI endpoint (`POST /convert`) for file uploads

### Shared Core Logic
Both interfaces use a single `convert_to_pdfa()` function (`src/pdfa/converter.py`) to ensure feature parity and eliminate duplication. This is the key design principle: **single conversion implementation serving multiple entry points**.

### Architecture Layers
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
Both interfaces translate low-level errors consistently:
- **File not found**: CLI returns exit code 1, API returns HTTP 400
- **OCRmyPDF failures**: CLI propagates exit code, API returns HTTP 500
- Shared logic in `converter.py` raises exceptions; interfaces handle translation

## Testing Architecture

### Test Pyramid
1. **Unit Tests** (majority): Test CLI parsing, API validation, error handling with mocked OCRmyPDF
2. **Integration Tests** (optional): End-to-end with real OCRmyPDF, skipped if system dependencies unavailable

### Key Testing Details
- `conftest.py` provides `ocrmypdf` module mocking so tests run without Tesseract/Ghostscript
- Tests import from `src/` via `pythonpath` in `pyproject.toml`
- Run `pytest` to execute all available tests; integration tests auto-skip gracefully
- Marker: `@pytest.mark.skipif(not HAS_TESSERACT, ...)` for conditional tests

### Test Files
- `test_cli.py`: Argument parsing, error cases, success paths
- `test_api.py`: Endpoint validation, file upload, response headers
- `test_conversion.py`: Real OCRmyPDF integration (integration tests)

## Code Quality Standards

### Python & Style
- **Python 3.11+** required
- **Code formatting**: `black` with 88-character line length
- **Linting**: `ruff` checks E (errors), F (pyflakes), W (warnings), I (imports), UP (upgrades), N (naming), D (docstrings)
- Docstring required for all modules, functions, classes except specific cases (D100, D101, D102, D103, D104, D105 ignored)

### Development Practices
- Follow PEP 8 conventions
- Organize modules by responsibility
- Keep methods focused and concise
- **Do not wrap imports in try/except** (per AGENTS.md)
- Write all documentation and comments in English

## Configuration

### CLI Parameters
- `input_pdf`: Path to input PDF (positional)
- `output_pdf`: Path to output PDF/A file (positional)
- `--language` / `-l`: Tesseract language codes, default "deu+eng"
- `--pdfa-level`: PDF/A compliance level (1, 2, or 3), default "2"

### API Parameters
- `file`: PDF file upload (multipart/form-data)
- `language`: Tesseract codes (default "deu+eng")
- `pdfa_level`: PDF/A level as string (default "2")

### Project Configuration
- **Tool versions** in `pyproject.toml` specify minimum versions
- **Entry point**: `pdfa-cli` → `pdfa.cli:main`
- **API app**: `pdfa.api:app` for ASGI servers

## Important Implementation Details

### Type System
- Uses Python 3.11+ type hints throughout
- `Literal` types for configuration: `PdfaLevel = Literal["1", "2", "3"]`
- `pathlib.Path` for file paths in core logic

### Temporary File Handling (API)
- REST endpoint uses `TemporaryDirectory()` context manager for uploaded files
- Ensures cleanup even on errors; supports clean streaming semantics

### Configuration Distribution
- Configuration (language, PDF/A level) passed as **function arguments**, not environment variables
- Enables per-request configuration in API, easier testing, no global state

### Dependency Abstraction
- OCRmyPDF imported at module level (mockable in tests)
- Simple wrapper around `ocrmypdf.ocr()` for maintainability
- API response includes proper headers: `Content-Type: application/pdf`, `Content-Disposition: attachment`

## File Reference

| File | Purpose |
|------|---------|
| `src/pdfa/converter.py` | Core conversion logic; single source of truth for OCRmyPDF integration |
| `src/pdfa/cli.py` | CLI with argparse; entry point is `main(argv)` |
| `src/pdfa/api.py` | FastAPI app; endpoint is `POST /convert` |
| `src/pdfa/__init__.py` | Package metadata (version) |
| `tests/conftest.py` | Pytest fixtures, OCRmyPDF mocking |
| `tests/test_cli.py` | CLI unit tests |
| `tests/test_api.py` | API endpoint unit tests |
| `tests/integration/test_conversion.py` | End-to-end integration tests |
| `pyproject.toml` | Project metadata, dependencies, tool configs |

## Development Workflow

1. **Make changes** to `src/pdfa/` or `tests/`
2. **Format code**: `black src tests`
3. **Lint**: `ruff check src tests --fix` (auto-fix what possible)
4. **Run tests**: `pytest` (mandatory before commit)
5. **Update README.md** if behavior changes
6. **Commit** with concise, imperative message

## Notes for Future Development

- **Single conversion function** is intentional: both CLI and API must call the same `convert_to_pdfa()` to stay in sync
- **Mocked tests first**: Add unit tests with mocked OCRmyPDF before integration tests
- **Error handling**: New OCRmyPDF exceptions should be caught and translated in both interfaces consistently
- **Configuration**: New parameters should be function arguments, not globals or environment variables
- **Type hints**: Maintain type coverage for IDE support and clarity
