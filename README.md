# pdfa service

Command-line tool and REST API that converts PDF, Office, and OpenDocument files into PDF/A files using [OCRmyPDF](https://ocrmypdf.readthedocs.io/) with built-in OCR.

## Features

- Converts **PDF**, **MS Office** (DOCX, PPTX, XLSX), and **OpenDocument** (ODT, ODS, ODP) files to PDF/A-compliant documents
- Office and OpenDocument files are automatically converted to PDF before PDF/A processing
- Wraps OCRmyPDF to generate PDF/A-2 compliant files with configurable OCR
- Configurable OCR language and PDF/A level (1, 2, or 3)
- Offers a FastAPI REST endpoint for document conversions
- Ships with comprehensive tests, `black`, and `ruff` configurations

## Requirements

- **Python 3.11+**
- **LibreOffice** (for Office document conversion)
- **OCRmyPDF runtime dependencies**: Tesseract OCR, Ghostscript, and qpdf for PDF processing

For detailed installation instructions, refer to the [OCRmyPDF installation guide](https://ocrmypdf.readthedocs.io/en/latest/installation.html).

### System Dependencies by Distribution

#### Debian 12+ / Ubuntu 22.04+ / Linux Mint

Install the system dependencies before setting up the virtual environment:

```bash
sudo apt update
sudo apt install python3-venv python3-pip \
  libreoffice-calc libreoffice-impress \
  tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu \
  ghostscript qpdf
```

#### Red Hat / Fedora / AlmaLinux / Rocky Linux

Install the system dependencies using DNF:

```bash
sudo dnf install python3.11+ python3-pip \
  libreoffice-calc libreoffice-impress \
  tesseract tesseract-langpack-deu tesseract-langpack-eng \
  ghostscript qpdf
```

For **RHEL 9 and older versions**, you may need to enable the PowerTools repository for some packages:

```bash
sudo dnf config-manager --set-enabled powertools  # RHEL
# or for other RHEL-based distros, check your repository configuration
```

#### Arch Linux / Manjaro

Install the system dependencies using Pacman:

```bash
sudo pacman -Syu
sudo pacman -S python python-pip \
  libreoffice-still \
  tesseract tesseract-data-deu tesseract-data-eng \
  ghostscript qpdf
```

Note: Arch provides `libreoffice-still` (stable) instead of splitting Calc and Impress into separate packages.

### Language Support and Verification

**Adding Additional OCR Languages**:

The default installation includes English (`eng`) and German (`deu`) OCR support. To add more languages:

| Distribution | Command |
|---|---|
| Debian/Ubuntu | `sudo apt install tesseract-ocr-<lang>` (e.g., `tesseract-ocr-fra` for French) |
| Red Hat/Fedora | `sudo dnf install tesseract-langpack-<lang>` (e.g., `tesseract-langpack-fra`) |
| Arch Linux | `sudo pacman -S tesseract-data-<lang>` (e.g., `tesseract-data-fra`) |

**Verifying Installation**:

After installation, verify that all dependencies are available:

```bash
# Check Python version (3.11+)
python3 --version

# Verify Tesseract OCR
tesseract --version

# Verify Ghostscript
gs --version

# Verify qpdf
qpdf --version

# Verify LibreOffice
libreoffice --version
```

All commands should return version information without errors.

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

The CLI accepts PDF, MS Office (DOCX, PPTX, XLSX), and OpenDocument (ODT, ODS, ODP) files:

```bash
# Convert PDF to PDF/A
pdfa-cli input.pdf output.pdf --language deu+eng --pdfa-level 3

# Convert Office documents to PDF/A (automatic)
pdfa-cli document.docx output.pdf --language eng
pdfa-cli presentation.pptx output.pdf
pdfa-cli spreadsheet.xlsx output.pdf

# Convert OpenDocument files to PDF/A (automatic)
pdfa-cli document.odt output.pdf --language eng
pdfa-cli presentation.odp output.pdf
pdfa-cli spreadsheet.ods output.pdf
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

# Convert MS Office documents to PDF/A (automatic)
curl -X POST "http://localhost:8000/convert" \
  -F "file=@document.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document" \
  --output output.pdf

curl -X POST "http://localhost:8000/convert" \
  -F "file=@presentation.pptx;type=application/vnd.openxmlformats-officedocument.presentationml.presentation" \
  --output output.pdf

curl -X POST "http://localhost:8000/convert" \
  -F "file=@spreadsheet.xlsx;type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" \
  --output output.pdf

# Convert OpenDocument files to PDF/A (automatic)
curl -X POST "http://localhost:8000/convert" \
  -F "file=@document.odt;type=application/vnd.oasis.opendocument.text" \
  --output output.pdf

curl -X POST "http://localhost:8000/convert" \
  -F "file=@presentation.odp;type=application/vnd.oasis.opendocument.presentation" \
  --output output.pdf

curl -X POST "http://localhost:8000/convert" \
  -F "file=@spreadsheet.ods;type=application/vnd.oasis.opendocument.spreadsheet" \
  --output output.pdf
```

The service validates the upload, converts Office and OpenDocument files to PDF (if needed), converts to PDF/A using OCRmyPDF, and returns the converted document as the HTTP response body.

#### Available Parameters

- `file` (required): PDF, MS Office (DOCX, PPTX, XLSX), or OpenDocument (ODT, ODS, ODP) file to convert
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

## Advanced Usage

### Batch Processing with curl

Convert multiple files in a directory recursively:

```bash
# Convert all PDFs in directory and subdirectories, save with -pdfa.pdf suffix
find /path/to/documents -name "*.pdf" -type f | while read file; do
  output="${file%.*}-pdfa.pdf"
  echo "Converting: $file -> $output"
  curl -s -X POST "http://localhost:8000/convert" \
    -F "file=@${file};type=application/pdf" \
    -F "language=deu+eng" \
    -F "pdfa_level=2" \
    --output "$output"
done
```

### Mixed Format Batch Processing

Convert multiple file types (PDF, DOCX, PPTX, XLSX, ODT, ODS, ODP) in a single directory:

```bash
# Convert all supported formats
for file in /path/to/documents/*.*; do
  [ ! -f "$file" ] && continue

  ext="${file##*.}"
  output="${file%.*}-pdfa.pdf"

  # Determine MIME type
  case "$ext" in
    pdf)
      mime="application/pdf"
      ;;
    docx)
      mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      ;;
    pptx)
      mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
      ;;
    xlsx)
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      ;;
    odt)
      mime="application/vnd.oasis.opendocument.text"
      ;;
    odp)
      mime="application/vnd.oasis.opendocument.presentation"
      ;;
    ods)
      mime="application/vnd.oasis.opendocument.spreadsheet"
      ;;
    *)
      echo "Skipping unsupported format: $file"
      continue
      ;;
  esac

  echo "Converting: $file -> $output"
  curl -s -X POST "http://localhost:8000/convert" \
    -F "file=@${file};type=${mime}" \
    -F "language=deu+eng" \
    -F "pdfa_level=2" \
    --output "$output"
done
```

### Parallel Processing

For faster batch processing with multiple concurrent requests:

```bash
# Convert up to 4 files in parallel (all supported formats)
find /path/to/documents -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.pptx" -o -name "*.xlsx" -o -name "*.odt" -o -name "*.odp" -o -name "*.ods" \) | \
  xargs -P 4 -I {} bash -c '
    file="{}"
    output="${file%.*}-pdfa.pdf"
    mime="application/pdf"
    [[ "$file" == *.docx ]] && mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    [[ "$file" == *.pptx ]] && mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    [[ "$file" == *.xlsx ]] && mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    [[ "$file" == *.odt ]] && mime="application/vnd.oasis.opendocument.text"
    [[ "$file" == *.odp ]] && mime="application/vnd.oasis.opendocument.presentation"
    [[ "$file" == *.ods ]] && mime="application/vnd.oasis.opendocument.spreadsheet"

    echo "Converting: $file"
    curl -s -X POST "http://localhost:8000/convert" \
      -F "file=@${file};type=${mime}" \
      -F "language=deu+eng" \
      --output "$output"
  '
```

### Batch Script

For a more robust solution with error handling, logging, and progress tracking, use the provided batch conversion script:

```bash
# Make the script executable
chmod +x scripts/batch-convert.sh

# Convert all documents in a directory (recursive)
./scripts/batch-convert.sh /path/to/documents

# With custom API endpoint and language
./scripts/batch-convert.sh /path/to/documents \
  --api-url "http://api-server:8000" \
  --language "eng" \
  --pdfa-level "3"

# Dry-run mode (preview without actually converting)
./scripts/batch-convert.sh /path/to/documents --dry-run
```

See [scripts/README.md](scripts/README.md) for detailed documentation on the batch conversion script.

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
