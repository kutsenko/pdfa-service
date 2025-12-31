# pdfa service

Command-line tool and REST API that converts PDF, Office, OpenDocument, and image files into PDF/A files using [OCRmyPDF](https://ocrmypdf.readthedocs.io/) with built-in OCR.

## 📚 Documentation & Language

| Link | Description |
|------|-------------|
| 🇩🇪 [Deutsch (German)](README.de.md) | Complete German documentation |
| ⚙️ [Compression Configuration](COMPRESSION.md) | **PDF compression settings** - Configure quality vs file size trade-offs |
| ⚙️ [Komprimierungs-Konfiguration (Deutsch)](COMPRESSION.de.md) | **PDF-Komprimierungseinstellungen** - Qualität vs. Dateigröße konfigurieren |
| 🥧 [OCR-SCANNER Setup Guide](OCR-SCANNER.md) | **Raspberry Pi & Network Setup** - Deploy pdfa-service as a network-wide OCR scanner |
| 🥧 [OCR-SCANNER (Deutsch)](OCR-SCANNER.de.md) | **Raspberry Pi & Netzwerk-Anleitung** - Einsatz als Dokumentenscanner im lokalen Netzwerk |
| 📋 [OCR-SCANNER Practical Guide](OCR-SCANNER-GUIDE.md) | **Real-world scenarios with Docker Compose** - Home office, law firms, medical practices |
| 📋 [OCR-SCANNER Praktische Anleitung](OCR-SCANNER-GUIDE.de.md) | **Praktische Szenarien mit Docker Compose** - Heimatelier, Kanzlei, Arztpraxis |

## Features

- Converts **PDF**, **MS Office** (DOCX, PPTX, XLSX), **OpenDocument** (ODT, ODS, ODP), and **image files** (JPG, PNG, TIFF, BMP, GIF) to PDF/A-compliant documents
- Office, OpenDocument, and image files are automatically converted to PDF before PDF/A processing
- Wraps OCRmyPDF to generate PDF/A-2 compliant files with configurable OCR
- Configurable OCR language and PDF/A level (1, 2, or 3)
- Offers a FastAPI REST endpoint for document conversions
- Ships with comprehensive tests, `black`, and `ruff` configurations
- **Camera Tab**: Multi-page document scanning with live camera preview, image editing, and drag-and-drop page reordering
- **Accessibility Features**: Audio-guided document scanning for blind and low-vision users with real-time edge detection

📚 **[Accessibility Guide](docs/ACCESSIBILITY.md)**: Complete documentation on audio-guided document scanning with real-time edge detection, voice feedback, and multi-language support.

## Installation

📚 **[Installation Guide](docs/INSTALLATION.md)**: Complete installation instructions for Debian/Ubuntu, Red Hat/Fedora, Arch Linux, and other distributions with dependency verification.

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

The CLI accepts PDF, MS Office (DOCX, PPTX, XLSX), OpenDocument (ODT, ODS, ODP), and image files (JPG, PNG, TIFF, BMP, GIF):

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

# Convert images to PDF/A (automatic)
pdfa-cli photo.jpg output.pdf --language eng
pdfa-cli scan.png output.pdf
pdfa-cli document.tiff output.pdf

# NEW: Convert to plain PDF instead of PDF/A (works with ANY input)
pdfa-cli document.docx output.pdf --pdfa-level pdf
pdfa-cli photo.jpg output.pdf --pdfa-level pdf
pdfa-cli existing.pdf output.pdf --pdfa-level pdf --no-ocr
```

#### Plain PDF Output (NEW - Universal)

**All input types** (PDFs, Office documents, images) can now output plain PDF instead of PDF/A using `--pdfa-level pdf`:

```bash
# Office document → PDF (fast, preserves accessibility)
pdfa-cli document.docx output.pdf --pdfa-level pdf

# Image → PDF with OCR
pdfa-cli photo.jpg output.pdf --pdfa-level pdf

# Image → PDF without OCR
pdfa-cli photo.jpg output.pdf --pdfa-level pdf --no-ocr

# Existing PDF → Copy (no processing)
pdfa-cli input.pdf output.pdf --pdfa-level pdf --no-ocr

# Existing PDF → Add OCR if needed
pdfa-cli input.pdf output.pdf --pdfa-level pdf
```

**When to use `--pdfa-level pdf`:**
- When PDF/A compliance is not required
- For faster conversion (especially with `--no-ocr`)
- To preserve original formatting and fonts
- When you just need a standard PDF output

**Behavior:**
- **With `--no-ocr`**: Direct copy/conversion without OCR processing (fastest)
- **With OCR enabled** (default): OCR only runs if needed (auto-skipped for PDFs with text/tags)
- Structure tags and formatting are preserved when present
- Works with all input types: PDF, Office (DOCX/PPTX/XLSX), ODF (ODT/ODS/ODP), Images (JPG/PNG/TIFF)

**Options**:
- `-l, --language`: Tesseract language codes for OCR (default: `deu+eng`)
- `--pdfa-level`: PDF/A compliance level (1, 2, or 3) or 'pdf' for plain PDF output (default: `2`)
- `--no-ocr`: Disable OCR and convert without text recognition
- `--force-ocr-on-tagged-pdfs`: Force OCR on PDFs with structure tags. By default, OCR is skipped for tagged PDFs to preserve accessibility information
- `-v, --verbose`: Enable verbose (debug) logging
- `--log-file`: Write logs to a file in addition to stderr

### Running the REST API

Start the REST service with [uvicorn](https://www.uvicorn.org/):

```bash
uvicorn pdfa.api:app --host 0.0.0.0 --port 8000
```

#### Web-Based Test Interface

Once the API is running, visit **`http://localhost:8000`** to access the interactive web interface where you can:
- Upload documents (PDF, Office, OpenDocument, and image formats)
- Select OCR language and PDF/A compliance level
- Toggle OCR on/off
- Skip OCR for tagged PDFs (enabled by default to preserve accessibility)
- Download converted files directly from your browser

This is the easiest way to test the service without using the command line.

#### Programmatic Usage

Upload a document via `POST /convert` with a `multipart/form-data` request:

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

# Convert image files to PDF/A (automatic)
curl -X POST "http://localhost:8000/convert" \
  -F "file=@photo.jpg;type=image/jpeg" \
  --output output.pdf

curl -X POST "http://localhost:8000/convert" \
  -F "file=@scan.png;type=image/png" \
  --output output.pdf

# NEW: Universal plain PDF output (works with ANY input type)

# Office document → PDF (fast, preserves accessibility)
curl -X POST "http://localhost:8000/convert" \
  -F "file=@document.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document" \
  -F "pdfa_level=pdf" \
  --output output.pdf

# Image → PDF with OCR
curl -X POST "http://localhost:8000/convert" \
  -F "file=@photo.jpg;type=image/jpeg" \
  -F "pdfa_level=pdf" \
  --output output.pdf

# Image → PDF without OCR (fast)
curl -X POST "http://localhost:8000/convert" \
  -F "file=@photo.jpg;type=image/jpeg" \
  -F "pdfa_level=pdf" \
  -F "ocr_enabled=false" \
  --output output.pdf

# Existing PDF → Copy (no processing, fastest)
curl -X POST "http://localhost:8000/convert" \
  -F "file=@input.pdf;type=application/pdf" \
  -F "pdfa_level=pdf" \
  -F "ocr_enabled=false" \
  --output output.pdf

# Existing PDF → Add OCR if needed
curl -X POST "http://localhost:8000/convert" \
  -F "file=@input.pdf;type=application/pdf" \
  -F "pdfa_level=pdf" \
  --output output.pdf
```

The service validates the upload, converts Office, OpenDocument, and image files to PDF (if needed), converts to PDF/A using OCRmyPDF, and returns the converted document as the HTTP response body.

#### Available Parameters

- `file` (required): PDF, MS Office (DOCX, PPTX, XLSX), OpenDocument (ODT, ODS, ODP), or image (JPG, PNG, TIFF, BMP, GIF) file to convert
- `language` (optional): Tesseract language codes for OCR (default: `deu+eng`)
- `pdfa_level` (optional): PDF/A compliance level (`1`, `2`, `3`) or `pdf` for plain PDF output (default: `2`)
- `ocr_enabled` (optional): Whether to perform OCR (default: `true`). Set to `false` to skip OCR.

Example without OCR:

```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@input.pdf;type=application/pdf" \
  -F "ocr_enabled=false" \
  --output output.pdf
```

## Authentication (Optional)

📚 **[Authentication Guide](docs/AUTHENTICATION.md)**: Complete guide for setting up Google OAuth 2.0 authentication, configuring JWT tokens, default user settings, and API usage with authentication.

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

Convert multiple file types (PDF, DOCX, PPTX, XLSX, ODT, ODS, ODP, JPG, PNG, TIFF, BMP, GIF) in a single directory:

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
    jpg|jpeg)
      mime="image/jpeg"
      ;;
    png)
      mime="image/png"
      ;;
    tiff|tif)
      mime="image/tiff"
      ;;
    bmp)
      mime="image/bmp"
      ;;
    gif)
      mime="image/gif"
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
find /path/to/documents -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.pptx" -o -name "*.xlsx" -o -name "*.odt" -o -name "*.odp" -o -name "*.ods" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.tiff" -o -name "*.tif" -o -name "*.bmp" -o -name "*.gif" \) | \
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
    [[ "$file" == *.jpg || "$file" == *.jpeg ]] && mime="image/jpeg"
    [[ "$file" == *.png ]] && mime="image/png"
    [[ "$file" == *.tiff || "$file" == *.tif ]] && mime="image/tiff"
    [[ "$file" == *.bmp ]] && mime="image/bmp"
    [[ "$file" == *.gif ]] && mime="image/gif"

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

### Unit and Integration Tests

Run the test suite:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

### Testing GitHub Actions Locally

The project uses [act](https://github.com/nektos/act) to run GitHub Actions workflows locally before pushing to GitHub.

**Prerequisites**: Install act following the [installation guide](https://github.com/nektos/act#installation)

**Run specific jobs**:

```bash
# Run tests
act -j test

# Run security scan
act -j security

# Run both (all stage 0 jobs)
act
```

**Configuration**: The `.actrc` file configures act to use the correct Docker image for local testing.

**Note**: The `build-and-push` job requires Docker Hub credentials and is typically not run locally.

## Deployment

### Docker

#### Docker Image Variants

Two Docker image variants are available:

| Variant | Tags | Features | Size | Use Case |
|---------|------|----------|------|----------|
| **Full** | `:latest`, `:1.2.3` | PDF, Office docs (.docx, .xlsx, .pptx), Images (.jpg, .png) | ~1.2 GB | Complete functionality with LibreOffice support |
| **Minimal** | `:latest-minimal`, `:1.2.3-minimal` | PDF to PDF/A only | ~400-500 MB | Smaller footprint, PDF/A conversion only |

**Choosing an Image:**

- Use the **full image** (`:latest`) if you need to convert Office documents or images
- Use the **minimal image** (`:latest-minimal`) if you only convert PDFs to PDF/A and want a smaller image

#### Building Locally

Build the full image (default):

```bash
docker build -t pdfa-service:latest .
```

Build the minimal image:

```bash
docker build --target minimal -t pdfa-service:minimal .
```

#### Using Pre-built Images from Docker Hub

Pull and run the full image:

```bash
docker pull <username>/pdfa-service:latest
docker run -p 8000:8000 <username>/pdfa-service:latest
```

Pull and run the minimal image:

```bash
docker pull <username>/pdfa-service:latest-minimal
docker run -p 8000:8000 <username>/pdfa-service:latest-minimal
```

#### Running the API Service

Run the API service in a container:

```bash
docker run -p 8000:8000 pdfa-service:latest
```

#### Using the CLI

Convert a PDF using the containerized CLI:

```bash
docker run --rm -v $(pwd):/data pdfa-service:latest \
  pdfa-cli /data/input.pdf /data/output.pdf --language eng
```

### Docker Compose

The simplest way to run the service locally:

```bash
docker compose up
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

## Security

This project uses automated vulnerability scanning to ensure dependency security:

- **pip-audit**: Scans Python dependencies for known CVEs using the PyPI Advisory Database
- **Trivy**: Scans Docker images for vulnerabilities in OS packages and Python dependencies
- **Dependabot**: Automatically creates pull requests for dependency updates and security patches

### CI/CD Security Pipeline

Security scans run on every push and pull request:

1. **Python Dependency Scan**: Runs in parallel with tests using pip-audit
2. **Docker Image Scan**: Scans both full and minimal image variants with Trivy before pushing
3. **Build Failure**: CI pipeline fails if HIGH or CRITICAL vulnerabilities are detected

Vulnerability reports are automatically uploaded to the GitHub Security tab for review.

### Running Security Scans Locally

Scan Python dependencies for vulnerabilities:

```bash
pip install pip-audit
pip-audit
```

Scan Docker images:

```bash
# Install Trivy
# See: https://aquasecurity.github.io/trivy/latest/getting-started/installation/

# Build and scan the image
docker build -t pdfa-service .
trivy image --severity HIGH,CRITICAL pdfa-service
```

### Automated Dependency Updates

Dependabot is configured to:
- Check for dependency updates weekly (Mondays at 06:00 UTC)
- Create pull requests for Python dependencies and GitHub Actions
- Automatically label security-related updates
- Limit open PRs to prevent overwhelming the repository

All Dependabot PRs trigger the full test suite and security scans before merge.

## Troubleshooting

### Ghostscript Rendering Errors

**Symptoms:**
- Error messages like: `Error: /undefined in --runpdf--`
- `Ghostscript rasterizing failed`
- Conversion fails during OCR processing

**Cause:**
Some PDFs contain features that Ghostscript cannot handle during OCR rasterization (e.g., complex graphics, certain compression types, problematic font embeddings).

**Automatic Three-Tier Fallback:**
The service automatically tries multiple strategies to handle problematic PDFs:

1. **Tier 1** - Normal conversion with your requested settings
2. **Tier 2** - Safe-mode OCR with Ghostscript-friendly parameters:
   - Lower DPI (100) for easier rendering
   - Preserved vector graphics
   - Minimal compression/optimization
   - Simpler PDF/A level (e.g., PDF/A-2 instead of PDF/A-3)
3. **Tier 3** - Conversion without OCR as final fallback
4. **Result**: Best possible PDF/A file, potentially with reduced quality or no searchable text

**Manual Workaround:**
If you encounter these errors, you can explicitly disable OCR:

```bash
# CLI
pdfa-cli input.pdf output.pdf --no-ocr

# API
curl -X POST -F "file=@input.pdf" \
  -F "ocr_enabled=false" \
  http://localhost:8000/api/v1/convert
```

### Encrypted PDFs

**Symptoms:**
- Error: `Cannot process encrypted PDF. Please remove encryption first.`

**Solution:**
Remove PDF encryption before conversion:

```bash
# Using qpdf
qpdf --decrypt --password=yourpassword encrypted.pdf decrypted.pdf

# Then convert
pdfa-cli decrypted.pdf output.pdf
```

### Corrupted or Invalid PDFs

**Symptoms:**
- Error: `Invalid or corrupted PDF file`
- Conversion fails immediately

**Solutions:**
1. Try repairing the PDF with Ghostscript:
   ```bash
   gs -o repaired.pdf -sDEVICE=pdfwrite -dPDFSETTINGS=/prepress input.pdf
   pdfa-cli repaired.pdf output.pdf
   ```

2. Re-export the PDF from its original source (Word, LibreOffice, etc.)

### PDFs Already Have OCR

**Symptoms:**
- Log message: `PDF already has OCR layer`
- Conversion completes successfully

**Action:**
No action needed. The service detects existing OCR and continues conversion. This is not an error.
