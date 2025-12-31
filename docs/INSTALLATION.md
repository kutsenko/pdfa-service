# Installation Guide

## Requirements

- **Python 3.13+**
- **LibreOffice** (for Office document conversion)
- **OCRmyPDF runtime dependencies**: Tesseract OCR, Ghostscript, and qpdf for PDF processing

For detailed installation instructions, refer to the [OCRmyPDF installation guide](https://ocrmypdf.readthedocs.io/en/latest/installation.html).

## System Dependencies by Distribution

### Debian 12+ / Ubuntu 22.04+ / Linux Mint

Install the system dependencies before setting up the virtual environment:

```bash
sudo apt update
sudo apt install python3-venv python3-pip \
  libreoffice-calc libreoffice-impress \
  tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu \
  ghostscript qpdf
```

### Red Hat / Fedora / AlmaLinux / Rocky Linux

Install the system dependencies using DNF:

```bash
sudo dnf install python3.13+ python3-pip \
  libreoffice-calc libreoffice-impress \
  tesseract tesseract-langpack-deu tesseract-langpack-eng \
  ghostscript qpdf
```

For **RHEL 9 and older versions**, you may need to enable the PowerTools repository for some packages:

```bash
sudo dnf config-manager --set-enabled powertools  # RHEL
# or for other RHEL-based distros, check your repository configuration
```

### Arch Linux / Manjaro

Install the system dependencies using Pacman:

```bash
sudo pacman -Syu
sudo pacman -S python python-pip \
  libreoffice-still \
  tesseract tesseract-data-deu tesseract-data-eng \
  ghostscript qpdf
```

Note: Arch provides `libreoffice-still` (stable) instead of splitting Calc and Impress into separate packages.

## Language Support and Verification

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
# Check Python version (3.13+)
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
