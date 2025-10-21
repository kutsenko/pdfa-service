# pdfa

Command-line tool that converts regular PDF documents into PDF/A files using [OCRmyPDF](https://ocrmypdf.readthedocs.io/) with built-in OCR.

## Features

- Wraps OCRmyPDF to generate PDF/A-2 compliant files with OCR enforced.
- Accepts input/output paths along with configurable OCR language and PDF/A level.
- Ships with tests, `black`, and `ruff` configurations for streamlined development.

## Requirements

- Python 3.11+
- OCRmyPDF runtime dependencies (Tesseract, Ghostscript, etc.) installed on your system. Refer to the [OCRmyPDF installation guide](https://ocrmypdf.readthedocs.io/en/latest/installation.html).

### Ubuntu 24.04

Install the system dependencies with APT before setting up the virtual environment:

```bash
sudo apt update
sudo apt install python3-venv python3-pip tesseract-ocr tesseract-ocr-eng ghostscript qpdf
```

Add extra `tesseract-ocr-<lang>` packages if you need OCR support for additional languages.

## Getting Started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pdfa-cli --help
```

> Tip: Activating the virtual environment adds `.venv/bin` to your `PATH`, so `pdfa-cli` is available directly.

## Usage

```bash
pdfa-cli input.pdf output.pdf --language deu+eng --pdfa-level 3
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
