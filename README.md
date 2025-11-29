# pdfa service

Command-line tool and REST API that converts PDF and Office documents into PDF/A files using [OCRmyPDF](https://ocrmypdf.readthedocs.io/) with built-in OCR.

## Features

- Converts **PDF, DOCX, PPTX, and XLSX** files to PDF/A-compliant documents
- Office documents (DOCX, PPTX, XLSX) are automatically converted to PDF before PDF/A processing
- Wraps OCRmyPDF to generate PDF/A-2 compliant files with configurable OCR
- Configurable OCR language and PDF/A level (1, 2, or 3)
- Offers a FastAPI REST endpoint for document conversions
- Ships with comprehensive tests, `black`, and `ruff` configurations

## Requirements

- Python 3.11+
- **LibreOffice** (for Office document conversion)
- **OCRmyPDF runtime dependencies**: Tesseract, Ghostscript, etc. Refer to the [OCRmyPDF installation guide](https://ocrmypdf.readthedocs.io/en/latest/installation.html).

### Ubuntu 24.04

Install the system dependencies with APT before setting up the virtual environment:

```bash
sudo apt update
sudo apt install python3-venv python3-pip \
  libreoffice-calc libreoffice-impress \
  tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu \
  ghostscript qpdf
```

**Language Support**:
- Add extra `tesseract-ocr-<lang>` packages for additional OCR languages (e.g., `tesseract-ocr-fra` for French)
- Office document conversion supports all languages that LibreOffice supports

## Getting Started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pdfa-cli --help
```

> Tip: Activating the virtual environment adds `.venv/bin` to your `PATH`, so `pdfa-cli` is available directly.

## Usage

### CLI: Converting Documents

The CLI accepts PDF, DOCX, PPTX, and XLSX files:

```bash
# Convert PDF to PDF/A
pdfa-cli input.pdf output.pdf --language deu+eng --pdfa-level 3

# Convert Office document to PDF/A (automatic)
pdfa-cli document.docx output.pdf --language eng
pdfa-cli presentation.pptx output.pdf
pdfa-cli spreadsheet.xlsx output.pdf
```

**Options**:
- `-l, --language`: Tesseract language codes for OCR (default: `deu+eng`)
- `--pdfa-level`: PDF/A compliance level (1, 2, or 3; default: `2`)
- `--no-ocr`: Disable OCR and convert without text recognition
- `-v, --verbose`: Enable verbose (debug) logging
- `--log-file`: Write logs to a file in addition to stderr

### Running the REST API

Start the REST service with [uvicorn](https://www.uvicorn.org/):

```bash
uvicorn pdfa.api:app --host 0.0.0.0 --port 8000
```

Once running, upload a document via `POST /convert` with a `multipart/form-data` request:

```bash
# Convert PDF to PDF/A
curl -X POST "http://localhost:8000/convert" \
  -F "file=@input.pdf;type=application/pdf" \
  -F "language=deu+eng" \
  -F "pdfa_level=2" \
  --output output.pdf

# Convert Office document to PDF/A (automatic)
curl -X POST "http://localhost:8000/convert" \
  -F "file=@document.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document" \
  --output output.pdf

curl -X POST "http://localhost:8000/convert" \
  -F "file=@presentation.pptx;type=application/vnd.openxmlformats-officedocument.presentationml.presentation" \
  --output output.pdf

curl -X POST "http://localhost:8000/convert" \
  -F "file=@spreadsheet.xlsx;type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" \
  --output output.pdf
```

The service validates the upload, converts Office documents to PDF (if needed), converts to PDF/A using OCRmyPDF, and returns the converted document as the HTTP response body.

#### Available Parameters

- `file` (required): PDF or Office file to convert (DOCX, PPTX, XLSX, PDF)
- `language` (optional): Tesseract language codes for OCR (default: `deu+eng`)
- `pdfa_level` (optional): PDF/A compliance level: `1`, `2`, or `3` (default: `2`)
- `ocr_enabled` (optional): Whether to perform OCR (default: `true`). Set to `false` to skip OCR.

Example without OCR:

```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@input.pdf;type=application/pdf" \
  -F "ocr_enabled=false" \
  --output output.pdf
```

## Testing

```bash
pytest
```

## Deployment

### Docker

Build the Docker image:

```bash
docker build -t pdfa-service:latest .
```

Run the API service in a container:

```bash
docker run -p 8000:8000 pdfa-service:latest
```

Convert a PDF using the containerized CLI:

```bash
docker run --rm -v $(pwd):/data pdfa-service:latest \
  pdfa-cli /data/input.pdf /data/output.pdf --language eng
```

### Docker Compose

The simplest way to run the service locally:

```bash
docker-compose up
```

This starts the REST API on `http://localhost:8000`. Upload PDFs via:

```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@input.pdf;type=application/pdf" \
  -F "language=eng" \
  -F "pdfa_level=2" \
  --output output.pdf
```

## Project Layout

```
.
├── pyproject.toml
├── README.md
├── src
│   └── pdfa
│       ├── __init__.py
│       ├── api.py
│       ├── cli.py
│       └── converter.py
└── tests
    ├── __init__.py
    ├── conftest.py
    ├── test_api.py
    └── test_cli.py
```
