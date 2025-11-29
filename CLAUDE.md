# CLAUDE.md - Quick Reference

Guidance for Claude Code and AI Agents working with the pdfa-service repository.

**Documentation in other languages**: [Deutsch](CLAUDE.de.md)

## ⚠️ Important

All development guidelines are consolidated in **[AGENTS.md](AGENTS.md)** - use that as your primary reference.

This document is a quick reference. For complete details on:
- Development standards and code quality
- Project architecture and design patterns
- Testing requirements and procedures
- Security guidelines
- Performance considerations

See [AGENTS.md](AGENTS.md).

---

## Quick Setup

```bash
# Environment setup (one-time)
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Daily commands
pytest                              # Run all tests (required before commit)
black src tests                     # Format code
ruff check src tests --fix          # Lint and auto-fix
pdfa-cli --help                     # Test CLI
uvicorn pdfa.api:app --port 8000   # Run API locally
```

## Essential Before Commit

1. **Format**: `black src tests`
2. **Lint**: `ruff check src tests --fix`
3. **Test**: `pytest` (must pass)
4. **Commit**: Use clear, imperative message

## Key Files

| File | Purpose |
|------|---------|
| `AGENTS.md` | **Complete development guidelines** (single source of truth) |
| `src/pdfa/converter.py` | Core conversion logic |
| `src/pdfa/cli.py` | CLI entry point |
| `src/pdfa/api.py` | REST API |
| `tests/` | Test suite |
| `README.md` | User documentation |

## Key Principles

1. **Single Conversion Function**: Both CLI and API must use `convert_to_pdfa()`
2. **Configuration as Arguments**: Pass config as function parameters, not globals
3. **Shared Error Handling**: Consistent error translation across interfaces
4. **Tests First**: Write tests with mocked dependencies before implementing
5. **Type Hints**: Use Python 3.11+ type hints throughout

## System Setup

Before running with real PDFs:
```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr ghostscript qpdf libreoffice

# Fedora
sudo dnf install tesseract ghostscript qpdf libreoffice

# Arch
sudo pacman -S tesseract ghostscript qpdf libreoffice-still
```

Tests run without these dependencies using mocked OCRmyPDF.

## Project Structure

```
pdfa-service/
├── AGENTS.md                 # Development guidelines (go here!)
├── README.md                 # User documentation
├── OCR-SCANNER.md            # Scanner setup guide
├── src/pdfa/
│   ├── converter.py          # Core logic (single source of truth)
│   ├── cli.py                # CLI interface
│   ├── api.py                # REST API interface
│   ├── format_converter.py    # Office document conversion
│   ├── exceptions.py          # Custom exceptions
│   └── logging_config.py      # Logging setup
└── tests/
    ├── conftest.py           # Pytest config with OCRmyPDF mocking
    ├── test_cli.py           # CLI tests
    ├── test_api.py           # API tests
    ├── test_format_converter.py
    └── integration/          # Integration tests (with real OCRmyPDF)
```

## Common Tasks

### Add a New Feature

1. Write unit tests (with mocked OCRmyPDF) in `tests/`
2. Implement in `converter.py` (shared core logic)
3. Add CLI support in `cli.py`
4. Add API support in `api.py`
5. Update `README.md` with examples
6. Run full test suite: `pytest`
7. Commit with clear message

### Run Specific Test

```bash
pytest tests/test_cli.py::test_main_success
pytest -k "office"  # Run tests matching pattern
```

### Debug an Issue

```bash
# See full error output
pytest -v tests/test_file.py

# Run with print statements
pytest -s tests/test_file.py

# Run single test with debugging
python -m pdb -c continue -m pytest tests/test_file.py::test_name
```

## Code Quality Checklist

Before every commit:

- [ ] All tests pass: `pytest`
- [ ] Code formatted: `black src tests`
- [ ] No linting issues: `ruff check src tests`
- [ ] Smoke test passes: `pdfa-cli --help`
- [ ] Commit message is clear and imperative
- [ ] README.md updated if behavior changed

## Architecture Reminder

The key design principle ensures consistency:

```
                    Both interfaces use same function
                            ↓
                    convert_to_pdfa()
                       ↙          ↖
                     CLI          API
                   (/bin)      (HTTP)
```

Never duplicate logic between CLI and API. Always put shared logic in `converter.py`.

## Getting Help

- **Development Guidelines**: Read [AGENTS.md](AGENTS.md)
- **User Questions**: See [README.md](README.md)
- **Setup Instructions**: See [OCR-SCANNER.md](OCR-SCANNER.md)
- **Architecture Details**: Section "Project Architecture" in [AGENTS.md](AGENTS.md)

---

**Remember**: AGENTS.md is your single source of truth for development practices.
