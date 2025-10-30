# pdfa

Command-line tool that converts regular PDF documents into PDF/A files using [OCRmyPDF](https://ocrmypdf.readthedocs.io/) with built-in OCR.

## Features

- Wraps OCRmyPDF to generate PDF/A-2 compliant files with OCR enforced.
- Accepts input/output paths along with configurable OCR language and PDF/A level.
- Offers a FastAPI REST endpoint for PDF to PDF/A conversions.
- Ships with tests, `black`, and `ruff` configurations for streamlined development.

## Requirements

- Python 3.11+
- OCRmyPDF runtime dependencies (Tesseract, Ghostscript, etc.) installed on your system. Refer to the [OCRmyPDF installation guide](https://ocrmypdf.readthedocs.io/en/latest/installation.html).

### Ubuntu 24.04

Install the system dependencies with APT before setting up the virtual environment:

```bash
sudo apt update
sudo apt install python3-venv python3-pip tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu ghostscript qpdf
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

### Running the REST API

Start the REST service with [uvicorn](https://www.uvicorn.org/):

```bash
uvicorn pdfa.api:app --host 0.0.0.0 --port 8000
```

Once running, upload a PDF via `POST /convert` with a `multipart/form-data` request:

```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@input.pdf;type=application/pdf" \
  -F "language=deu+eng" \
  -F "pdfa_level=2" \
  --output output.pdf
```

The service validates the upload, converts it to PDF/A using OCRmyPDF, and returns the converted document as the HTTP response body.

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
