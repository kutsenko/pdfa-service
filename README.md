# pdfa

Command-line tool that converts regular PDF documents into PDF/A files using [OCRmyPDF](https://ocrmypdf.readthedocs.io/) with built-in OCR.

## Features

- Wraps OCRmyPDF to generate PDF/A-2 compliant files with OCR enforced.
- Accepts input/output paths along with configurable OCR language and PDF/A level.
- Ships with tests, `black`, and `ruff` configurations for streamlined development.

## Requirements

- Python 3.11+
- OCRmyPDF runtime dependencies (Tesseract, Ghostscript, etc.) installed on your system. Refer to the [OCRmyPDF installation guide](https://ocrmypdf.readthedocs.io/en/latest/installation.html).

## Getting Started

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -e ".[dev]"
./.venv/bin/pdfa --help
```

> Tip: If you prefer to add `.venv/bin` to your `PATH`, activate the environment with `source .venv/bin/activate` before running the commands above.

## Usage

```bash
pdfa input.pdf output.pdf --language deu+eng --pdfa-level 3
```

This command converts `input.pdf` into a PDF/A file written to `output.pdf`, enforcing OCR with the specified Tesseract languages.

## Testing

```bash
./.venv/bin/pytest
```

## Project Layout

```
.
├── pyproject.toml
├── README.md
├── src
│   └── pdfa
│       ├── __init__.py
│       └── cli.py
└── tests
    ├── __init__.py
    └── test_cli.py
```
