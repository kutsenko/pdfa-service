# pdfa service

Kommandozeilen-Tool und REST-API zur Konvertierung von PDF-, Office-, OpenDocument- und Bilddateien in PDF/A-Dateien unter Verwendung von [OCRmyPDF](https://ocrmypdf.readthedocs.io/) mit integrierter OCR.

## 📚 Dokumentation & Sprache

| Link | Beschreibung |
|------|--------------|
| 🇬🇧 [English](README.md) | Vollständige englische Dokumentation |
| ⚙️ [Komprimierungs-Konfiguration](COMPRESSION.de.md) | **PDF-Komprimierungseinstellungen** - Qualität vs. Dateigröße konfigurieren |
| ⚙️ [Compression Configuration (English)](COMPRESSION.md) | **PDF compression settings** - Configure quality vs file size trade-offs |
| 🥧 [OCR-SCANNER Anleitung](OCR-SCANNER.de.md) | **Raspberry Pi & Netzwerk-Setup** - Einsatz als Dokumentenscanner im lokalen Netzwerk |
| 🥧 [OCR-SCANNER Setup Guide (English)](OCR-SCANNER.md) | **Raspberry Pi & Network Setup** - Deploy pdfa-service as a network-wide OCR scanner |
| 📋 [OCR-SCANNER Praktische Anleitung](OCR-SCANNER-GUIDE.de.md) | **Praktische Szenarien mit Docker Compose** - Heimatelier, Kanzlei, Arztpraxis |
| 📋 [OCR-SCANNER Practical Guide (English)](OCR-SCANNER-GUIDE.md) | **Real-world scenarios with Docker Compose** - Home office, law firms, medical practices |

## Features

- Konvertiert **PDF**, **MS Office** (DOCX, PPTX, XLSX), **OpenDocument** (ODT, ODS, ODP) und **Bilddateien** (JPG, PNG, TIFF, BMP, GIF) in PDF/A-konforme Dokumente
- Office-, OpenDocument- und Bilddateien werden automatisch in PDF konvertiert, bevor die PDF/A-Verarbeitung stattfindet
- Nutzt OCRmyPDF zur Erstellung von PDF/A-2-kompatiblen Dateien mit konfigurierbarer OCR
- Konfigurierbare OCR-Sprache und PDF/A-Stufe (1, 2 oder 3)
- Bietet einen FastAPI-REST-Endpunkt für Dokumentkonvertierungen
- Wird mit umfangreichen Tests, `black` und `ruff` Konfigurationen ausgeliefert

## Anforderungen

- **Python 3.11+**
- **LibreOffice** (für Office-Dokumentkonvertierung)
- **OCRmyPDF-Laufzeitabhängigkeiten**: Tesseract-OCR, Ghostscript und qpdf für PDF-Verarbeitung

Detaillierte Installationsanweisungen finden Sie im [OCRmyPDF-Installationshandbuch](https://ocrmypdf.readthedocs.io/en/latest/installation.html).

### Systemabhängigkeiten nach Distribution

#### Debian 12+ / Ubuntu 22.04+ / Linux Mint

Installieren Sie die Systemabhängigkeiten vor der Einrichtung der virtuellen Umgebung:

```bash
sudo apt update
sudo apt install python3-venv python3-pip \
  libreoffice-calc libreoffice-impress \
  tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu \
  ghostscript qpdf
```

#### Red Hat / Fedora / AlmaLinux / Rocky Linux

Installieren Sie die Systemabhängigkeiten mit DNF:

```bash
sudo dnf install python3.11+ python3-pip \
  libreoffice-calc libreoffice-impress \
  tesseract tesseract-langpack-deu tesseract-langpack-eng \
  ghostscript qpdf
```

Für **RHEL 9 und ältere Versionen** müssen Sie möglicherweise das PowerTools-Repository für einige Pakete aktivieren:

```bash
sudo dnf config-manager --set-enabled powertools  # RHEL
# oder für andere RHEL-basierte Distros, überprüfen Sie Ihre Repository-Konfiguration
```

#### Arch Linux / Manjaro

Installieren Sie die Systemabhängigkeiten mit Pacman:

```bash
sudo pacman -Syu
sudo pacman -S python python-pip \
  libreoffice-still \
  tesseract tesseract-data-deu tesseract-data-eng \
  ghostscript qpdf
```

Hinweis: Arch bietet `libreoffice-still` (stabil) statt geteilter Calc- und Impress-Pakete.

### Sprachunterstützung und Überprüfung

**Zusätzliche OCR-Sprachen hinzufügen**:

Die Standardinstallation umfasst Englisch (`eng`) und Deutsch (`deu`) OCR-Unterstützung. Um weitere Sprachen hinzuzufügen:

| Distribution | Befehl |
|---|---|
| Debian/Ubuntu | `sudo apt install tesseract-ocr-<lang>` (z.B. `tesseract-ocr-fra` für Französisch) |
| Red Hat/Fedora | `sudo dnf install tesseract-langpack-<lang>` (z.B. `tesseract-langpack-fra`) |
| Arch Linux | `sudo pacman -S tesseract-data-<lang>` (z.B. `tesseract-data-fra`) |

**Installation überprüfen**:

Nach der Installation überprüfen Sie, ob alle Abhängigkeiten verfügbar sind:

```bash
# Python-Version überprüfen (3.11+)
python3 --version

# Tesseract OCR überprüfen
tesseract --version

# Ghostscript überprüfen
gs --version

# qpdf überprüfen
qpdf --version

# LibreOffice überprüfen
libreoffice --version
```

Alle Befehle sollten Versionsinformationen ohne Fehler zurückgeben.

## Erste Schritte

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pdfa-cli --help
```

> Tipp: Die Aktivierung der virtuellen Umgebung fügt `.venv/bin` zu Ihrer `PATH` hinzu, daher ist `pdfa-cli` direkt verfügbar.

## Verwendung

### CLI: Dokumente konvertieren

Die CLI akzeptiert PDF-, MS Office (DOCX, PPTX, XLSX), OpenDocument (ODT, ODS, ODP) und Bilddateien (JPG, PNG, TIFF, BMP, GIF):

```bash
# PDF in PDF/A konvertieren
pdfa-cli input.pdf output.pdf --language deu+eng --pdfa-level 3

# Office-Dokumente in PDF/A konvertieren (automatisch)
pdfa-cli document.docx output.pdf --language eng
pdfa-cli presentation.pptx output.pdf
pdfa-cli spreadsheet.xlsx output.pdf

# OpenDocument-Dateien in PDF/A konvertieren (automatisch)
pdfa-cli document.odt output.pdf --language eng
pdfa-cli presentation.odp output.pdf
pdfa-cli spreadsheet.ods output.pdf

# Bilder in PDF/A konvertieren (automatisch)
pdfa-cli photo.jpg output.pdf --language eng
pdfa-cli scan.png output.pdf
pdfa-cli document.tiff output.pdf
```

**Optionen**:
- `-l, --language`: Tesseract-Sprachcodes für OCR (Standard: `deu+eng`)
- `--pdfa-level`: PDF/A-Konformitätsstufe (1, 2 oder 3; Standard: `2`)
- `--no-ocr`: OCR deaktivieren und ohne Texterkennung konvertieren
- `-v, --verbose`: Ausführliches (Debug) Logging aktivieren
- `--log-file`: Protokolle in eine Datei zusätzlich zu stderr schreiben

### REST-API ausführen

Starten Sie den REST-Service mit [uvicorn](https://www.uvicorn.org/):

```bash
uvicorn pdfa.api:app --host 0.0.0.0 --port 8000
```

Nach dem Start können Sie ein Dokument über `POST /convert` mit einer `multipart/form-data` Anfrage hochladen:

```bash
# PDF in PDF/A konvertieren
curl -X POST "http://localhost:8000/convert" \
  -F "file=@input.pdf;type=application/pdf" \
  -F "language=deu+eng" \
  -F "pdfa_level=2" \
  --output output.pdf

# MS Office-Dokumente in PDF/A konvertieren (automatisch)
curl -X POST "http://localhost:8000/convert" \
  -F "file=@document.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document" \
  --output output.pdf

curl -X POST "http://localhost:8000/convert" \
  -F "file=@presentation.pptx;type=application/vnd.openxmlformats-officedocument.presentationml.presentation" \
  --output output.pdf

curl -X POST "http://localhost:8000/convert" \
  -F "file=@spreadsheet.xlsx;type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" \
  --output output.pdf

# OpenDocument-Dateien in PDF/A konvertieren (automatisch)
curl -X POST "http://localhost:8000/convert" \
  -F "file=@document.odt;type=application/vnd.oasis.opendocument.text" \
  --output output.pdf

curl -X POST "http://localhost:8000/convert" \
  -F "file=@presentation.odp;type=application/vnd.oasis.opendocument.presentation" \
  --output output.pdf

curl -X POST "http://localhost:8000/convert" \
  -F "file=@spreadsheet.ods;type=application/vnd.oasis.opendocument.spreadsheet" \
  --output output.pdf

# Bilddateien in PDF/A konvertieren (automatisch)
curl -X POST "http://localhost:8000/convert" \
  -F "file=@photo.jpg;type=image/jpeg" \
  --output output.pdf

curl -X POST "http://localhost:8000/convert" \
  -F "file=@scan.png;type=image/png" \
  --output output.pdf

curl -X POST "http://localhost:8000/convert" \
  -F "file=@document.tiff;type=image/tiff" \
  --output output.pdf
```

Der Service validiert den Upload, konvertiert Office-, OpenDocument- und Bilddateien in PDF (falls erforderlich), konvertiert in PDF/A mit OCRmyPDF und gibt das konvertierte Dokument als HTTP-Response-Body zurück.

#### Verfügbare Parameter

- `file` (erforderlich): PDF-, MS Office (DOCX, PPTX, XLSX), OpenDocument (ODT, ODS, ODP) oder Bilddatei (JPG, PNG, TIFF, BMP, GIF) zum Konvertieren
- `language` (optional): Tesseract-Sprachcodes für OCR (Standard: `deu+eng`)
- `pdfa_level` (optional): PDF/A-Konformitätsstufe: `1`, `2` oder `3` (Standard: `2`)
- `ocr_enabled` (optional): Ob OCR durchgeführt werden soll (Standard: `true`). Auf `false` setzen, um OCR zu überspringen.

Beispiel ohne OCR:

```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@input.pdf;type=application/pdf" \
  -F "ocr_enabled=false" \
  --output output.pdf
```

## Fortgeschrittene Verwendung

### Batch-Verarbeitung mit curl

Mehrere Dateien in einem Verzeichnis rekursiv konvertieren:

```bash
# Alle PDFs im Verzeichnis und Unterverzeichnissen konvertieren, mit -pdfa.pdf Suffix speichern
find /path/to/documents -name "*.pdf" -type f | while read file; do
  output="${file%.*}-pdfa.pdf"
  echo "Konvertierung: $file -> $output"
  curl -s -X POST "http://localhost:8000/convert" \
    -F "file=@${file};type=application/pdf" \
    -F "language=deu+eng" \
    -F "pdfa_level=2" \
    --output "$output"
done
```

### Batch-Verarbeitung mit gemischten Formaten

Mehrere Dateitypen (PDF, DOCX, PPTX, XLSX, ODT, ODS, ODP, JPG, PNG, TIFF, BMP, GIF) in einem einzigen Verzeichnis konvertieren:

```bash
# Alle unterstützten Formate konvertieren
for file in /path/to/documents/*.*; do
  [ ! -f "$file" ] && continue

  ext="${file##*.}"
  output="${file%.*}-pdfa.pdf"

  # MIME-Typ bestimmen
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
      echo "Nicht unterstütztes Format übersprungen: $file"
      continue
      ;;
  esac

  echo "Konvertierung: $file -> $output"
  curl -s -X POST "http://localhost:8000/convert" \
    -F "file=@${file};type=${mime}" \
    -F "language=deu+eng" \
    -F "pdfa_level=2" \
    --output "$output"
done
```

### Parallele Verarbeitung

Für schnellere Batch-Verarbeitung mit mehreren gleichzeitigen Anfragen:

```bash
# Bis zu 4 Dateien gleichzeitig konvertieren (alle unterstützten Formate)
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

    echo "Konvertierung: $file"
    curl -s -X POST "http://localhost:8000/convert" \
      -F "file=@${file};type=${mime}" \
      -F "language=deu+eng" \
      --output "$output"
  '
```

## Testen

```bash
pytest
```

## Bereitstellung

### Docker

Docker-Image erstellen:

```bash
docker build -t pdfa-service:latest .
```

API-Service in einem Container ausführen:

```bash
docker run -p 8000:8000 pdfa-service:latest
```

PDF mit der containerisierten CLI konvertieren:

```bash
docker run --rm -v $(pwd):/data pdfa-service:latest \
  pdfa-cli /data/input.pdf /data/output.pdf --language eng
```

### Docker Compose

Der einfachste Weg, den Service lokal auszuführen:

```bash
docker compose up
```

Dies startet die REST-API auf `http://localhost:8000`. PDFs hochladen über:

```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@input.pdf;type=application/pdf" \
  -F "language=eng" \
  -F "pdfa_level=2" \
  --output output.pdf
```

## Projektstruktur

```
.
├── pyproject.toml
├── README.md
├── README.de.md
├── src
│   └── pdfa
│       ├── __init__.py
│       ├── api.py
│       ├── cli.py
│       ├── converter.py
│       ├── exceptions.py
│       ├── format_converter.py
│       └── logging_config.py
└── tests
    ├── __init__.py
    ├── conftest.py
    ├── integration/
    ├── test_api.py
    ├── test_api_office.py
    ├── test_cli.py
    ├── test_cli_office.py
    └── test_format_converter.py
```

## Lizenz

Siehe LICENSE-Datei für Details.
