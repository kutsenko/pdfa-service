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
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pdfa --help
```

## Usage

```bash
pdfa input.pdf output.pdf --language deu+eng --pdfa-level 3
```

This command converts `input.pdf` into a PDF/A file written to `output.pdf`, enforcing OCR with the specified Tesseract languages.

## Testing

```bash
pytest
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
