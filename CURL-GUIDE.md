# curl Guide für pdfa-service

Quick reference für die Verwendung der pdfa-service REST API mit curl.

## Schnelleinstieg

### 1. API starten
```bash
uvicorn pdfa.api:app --host 0.0.0.0 --port 8000
```

### 2. Einzelne Datei konvertieren
```bash
# PDF konvertieren
curl -X POST "http://localhost:8000/convert" \
  -F "file=@input.pdf;type=application/pdf" \
  -F "language=deu+eng" \
  --output output-pdfa.pdf
```

### 3. Batch-Konvertierung
```bash
# Alle PDFs im Verzeichnis konvertieren
for file in *.pdf; do
  output="${file%.*}-pdfa.pdf"
  curl -s -X POST "http://localhost:8000/convert" \
    -F "file=@${file};type=application/pdf" \
    --output "$output"
done
```

### 4. Produktives Batch-Skript
```bash
# Mit Fehlerbehandlung, Logging und paralleler Verarbeitung
./scripts/batch-convert.sh /path/to/documents
```

---

## MIME-Typen nach Dateityp

### PDF
| Format | MIME-Type |
|--------|-----------|
| PDF | `application/pdf` |

### MS Office Formate
| Format | MIME-Type |
|--------|-----------|
| Word (.docx) | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| PowerPoint (.pptx) | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| Excel (.xlsx) | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |

### OpenDocument Formate (ODF)
| Format | MIME-Type |
|--------|-----------|
| Text (.odt) | `application/vnd.oasis.opendocument.text` |
| Spreadsheet (.ods) | `application/vnd.oasis.opendocument.spreadsheet` |
| Presentation (.odp) | `application/vnd.oasis.opendocument.presentation` |

---

## API Parameter

### Pflichtparameter
- `file`: Die zu konvertierende Datei (PDF oder Office-Dokument)

### Optionale Parameter
- `language`: Tesseract Sprachcodes (Standard: `deu+eng`)
- `pdfa_level`: PDF/A Level 1, 2 oder 3 (Standard: `2`)
- `ocr_enabled`: OCR aktivieren/deaktivieren (Standard: `true`)

---

## Häufige Aufgaben

### PDF mit verschiedenen Sprachen konvertieren

**Englisch:**
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@input.pdf;type=application/pdf" \
  -F "language=eng" \
  --output output.pdf
```

**Mehrsprachig (Deutsch + Englisch + Französisch):**
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@input.pdf;type=application/pdf" \
  -F "language=deu+eng+fra" \
  --output output.pdf
```

### OCR deaktivieren (schneller für bereits digitalisierte PDFs)
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@input.pdf;type=application/pdf" \
  -F "ocr_enabled=false" \
  --output output.pdf
```

### PDF/A Level wechseln

**PDF/A-1 (höchste Kompatibilität):**
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@input.pdf;type=application/pdf" \
  -F "pdfa_level=1" \
  --output output-level1.pdf
```

**PDF/A-3 (größte Flexibilität):**
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@input.pdf;type=application/pdf" \
  -F "pdfa_level=3" \
  --output output-level3.pdf
```

### Word-Dokument konvertieren
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@document.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document" \
  -F "language=deu+eng" \
  --output document-pdfa.pdf
```

### PowerPoint konvertieren
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@presentation.pptx;type=application/vnd.openxmlformats-officedocument.presentationml.presentation" \
  --output presentation-pdfa.pdf
```

### Excel konvertieren
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@spreadsheet.xlsx;type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" \
  --output spreadsheet-pdfa.pdf
```

### OpenDocument Text konvertieren
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@document.odt;type=application/vnd.oasis.opendocument.text" \
  -F "language=deu+eng" \
  --output document-pdfa.pdf
```

### OpenDocument Spreadsheet konvertieren
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@spreadsheet.ods;type=application/vnd.oasis.opendocument.spreadsheet" \
  --output spreadsheet-pdfa.pdf
```

### OpenDocument Presentation konvertieren
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@presentation.odp;type=application/vnd.oasis.opendocument.presentation" \
  --output presentation-pdfa.pdf
```

---

## Batch-Verarbeitung

### Einfache Schleife über alle PDFs
```bash
for file in *.pdf; do
  output="${file%.*}-pdfa.pdf"
  echo "Converting: $file -> $output"
  curl -s -X POST "http://localhost:8000/convert" \
    -F "file=@${file};type=application/pdf" \
    --output "$output"
done
```

### Gemischte Formate (alle unterstützten Dateitypen)
```bash
for file in *.{pdf,docx,pptx,xlsx,odt,ods,odp}; do
  [ ! -f "$file" ] && continue

  ext="${file##*.}"
  output="${file%.*}-pdfa.pdf"
  mime="application/pdf"

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
    ods)
      mime="application/vnd.oasis.opendocument.spreadsheet"
      ;;
    odp)
      mime="application/vnd.oasis.opendocument.presentation"
      ;;
  esac

  echo "Converting: $file"
  curl -s -X POST "http://localhost:8000/convert" \
    -F "file=@${file};type=${mime}" \
    --output "$output"
done
```

### Rekursive Konvertierung (alle Verzeichnisse)
```bash
find /path/to/documents -name "*.pdf" -type f | while read file; do
  output="${file%.*}-pdfa.pdf"
  echo "Converting: $file"
  curl -s -X POST "http://localhost:8000/convert" \
    -F "file=@${file};type=application/pdf" \
    --output "$output"
done
```

### Parallele Verarbeitung mit xargs (4 parallel)
```bash
find /path/to/documents -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.pptx" -o -name "*.xlsx" \) | \
  xargs -P 4 -I {} bash -c '
    file="{}"
    output="${file%.*}-pdfa.pdf"
    mime="application/pdf"
    [[ "$file" == *.docx ]] && mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    [[ "$file" == *.pptx ]] && mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    [[ "$file" == *.xlsx ]] && mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    echo "Converting: $file"
    curl -s -X POST "http://localhost:8000/convert" \
      -F "file=@${file};type=${mime}" \
      --output "$output"
  '
```

---

## Fehlerbehandlung

### HTTP Status Codes prüfen
```bash
http_code=$(curl -s -w "%{http_code}" -o output.pdf \
  -X POST "http://localhost:8000/convert" \
  -F "file=@input.pdf;type=application/pdf")

if [ "$http_code" == "200" ]; then
  echo "✓ Konvertierung erfolgreich"
else
  echo "✗ Fehler: HTTP $http_code"
fi
```

### Fehlerbehandlung in einer Schleife
```bash
total=$(find . -name "*.pdf" | wc -l)
converted=0
failed=0

find . -name "*.pdf" | while read file; do
  output="${file%.*}-pdfa.pdf"

  if curl -s -X POST "http://localhost:8000/convert" \
    -F "file=@${file};type=application/pdf" \
    -o "$output"; then
    ((converted++))
    echo "✓ Erfolgreich: $file"
  else
    ((failed++))
    echo "✗ Fehler: $file"
  fi
done

echo "Ergebnis: $converted erfolgreich, $failed fehlgeschlagen"
```

### Logging von Konvertierungen
```bash
LOG_FILE="pdfa-conversion-$(date +%Y%m%d).log"

for file in *.pdf; do
  output="${file%.*}-pdfa.pdf"

  {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting: $file"
    if curl -s -X POST "http://localhost:8000/convert" \
      -F "file=@${file};type=application/pdf" \
      --output "$output" 2>&1; then
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ Success: $output"
    else
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✗ Failed: $file"
    fi
  } | tee -a "$LOG_FILE"
done
```

---

## Produktive Batch-Verarbeitung

Für Produktionsumgebungen mit Fehlerbehandlung, Logging und paralleler Verarbeitung:

```bash
./scripts/batch-convert.sh /path/to/documents \
  --language "deu+eng" \
  --pdfa-level "2" \
  --workers 4 \
  --log-file "/var/log/pdfa-conversion.log"
```

Siehe [scripts/README.md](scripts/README.md) für vollständige Dokumentation des Batch-Skripts.

---

## Remote API Server

Alle Beispiele können mit einer anderen API-URL verwendet werden:

```bash
API_URL="http://pdfa-api.example.com:8000"

curl -X POST "${API_URL}/convert" \
  -F "file=@input.pdf;type=application/pdf" \
  --output output-pdfa.pdf
```

---

## Performance Tipps

### Parallele Verarbeitung anpassen

Standard (4 Worker):
```bash
./scripts/batch-convert.sh /path/to/documents --workers 4
```

Mehr Worker für schnellere Systeme:
```bash
./scripts/batch-convert.sh /path/to/documents --workers 8
```

Weniger Worker für Systeme mit wenig RAM:
```bash
./scripts/batch-convert.sh /path/to/documents --workers 2
```

### Bulk-Verarbeitung mit curl
- Limit: Curl lädt die gesamte Datei in den Speicher
- Für große Dateien (>500MB): in Chunks verarbeiten oder Batch-Skript verwenden

### API Server Optimierung
```bash
# Mit mehreren Uvicorn Workern
uvicorn pdfa.api:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

---

## Weitere Ressourcen

- **Main README**: [README.md](README.md) - Allgemeine Dokumentation
- **Advanced Usage**: [README.md - Advanced Usage](README.md#advanced-usage) - Curl Beispiele im Main README
- **Batch Script**: [scripts/README.md](scripts/README.md) - Detaillierte Batch-Dokumentation
- **curl Examples**: [scripts/curl-examples.sh](scripts/curl-examples.sh) - Interaktive Beispiele

---

## Lizenz

Siehe Hauptprojekt Dokumentation.
