# CLAUDE.md (Deutsch)

Diese Datei bietet Anleitung für Claude Code (claude.ai/code) bei der Arbeit mit Code in diesem Repository.

**Englische Version**: [English](CLAUDE.md)

## Schnelleinstieg

### Umgebungseinrichtung
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Häufig verwendete Befehle
- **CLI-Hilfe**: `pdfa-cli --help`
- **Tests ausführen**: `pytest`
- **Einen einzelnen Test ausführen**: `pytest tests/test_cli.py::test_parse_args`
- **Code formatieren**: `black src tests`
- **Linting**: `ruff check src tests`
- **API lokal ausführen**: `uvicorn pdfa.api:app --host 0.0.0.0 --port 8000`

### Systemabhängigkeiten

Bevor Sie mit echten PDFs arbeiten, installieren Sie die OCRmyPDF-Laufzeitabhängigkeiten. Detaillierte Installationsanweisungen für Ihre Distribution finden Sie im Abschnitt **Systemabhängigkeiten nach Distribution** in der [README.md](README.md#systemabhängigkeiten-nach-distribution).

**Erforderliche Pakete** (unterscheiden sich je nach Distribution):
- **Tesseract OCR**: `tesseract-ocr` (apt), `tesseract` (dnf), `tesseract` (pacman)
- **Sprachpakete**: Englisch und Deutsch standardmäßig; bei Bedarf weitere hinzufügen
- **Ghostscript**: `ghostscript` (alle Distributionen)
- **qpdf**: `qpdf` (alle Distributionen)
- **LibreOffice**: Für Office-Dokumentkonvertierung (DOCX, PPTX, XLSX)

Tests können ohne diese Abhängigkeiten mit gemocktem OCRmyPDF ausgeführt werden.

## Projektarchitektur

**pdfa-service** ist ein leichtgewichtiges Python-Tool, das reguläre PDFs mit OCR unter Verwendung von [OCRmyPDF](https://ocrmypdf.readthedocs.io/) in PDF/A-konforme Dokumente konvertiert. Es hat zwei Schnittstellen:

### Design mit dualer Schnittstelle
1. **CLI** (`src/pdfa/cli.py`): Kommandozeilen-Tool registriert als `pdfa-cli` Entry Point
2. **REST API** (`src/pdfa/api.py`): FastAPI-Endpunkt (`POST /convert`) für Datei-Uploads

### Gemeinsame Kernlogik
Beide Schnittstellen nutzen eine einzelne `convert_to_pdfa()`-Funktion (`src/pdfa/converter.py`), um Feature-Parität sicherzustellen und Duplikation zu vermeiden. Dies ist das Schlüsseldesign-Prinzip: **Eine einzelne Konvertierungsimplementierung für mehrere Einstiegspunkte**.

### Architektur-Ebenen
```
Input (CLI-Argumente / HTTP-Request)
    ↓
Validierung & Parsing (cli.py / api.py)
    ↓
Gemeinsame Konvertierungslogik (converter.py)
    ↓
OCRmyPDF Bibliothek
    ↓
Output (Exit Code / HTTP Response)
```

### Fehlerbehandlungsmuster
Beide Schnittstellen übersetzen Low-Level-Fehler konsistent:
- **Datei nicht gefunden**: CLI gibt Exit Code 1 zurück, API gibt HTTP 400 zurück
- **OCRmyPDF-Fehler**: CLI propagiert Exit Code, API gibt HTTP 500 zurück
- Gemeinsame Logik in `converter.py` wirft Exceptions; Schnittstellen handhaben Übersetzung

### Office-Dokumentkonvertierung
- **format_converter.py**: LibreOffice-Integration für Office→PDF Konvertierung
- **exceptions.py**: Benutzerdefinierte Exceptions für Fehlerbehandlung
- Unterstützte Formate: DOCX, PPTX, XLSX, ODT, ODS, ODP

## Test-Architektur

### Test-Pyramide
1. **Unit-Tests** (Mehrheit): Teste CLI-Parsing, API-Validierung, Fehlerbehandlung mit gemocktem OCRmyPDF
2. **Integrations-Tests** (optional): End-to-End mit echtem OCRmyPDF, werden übersprungen wenn Systemabhängigkeiten nicht verfügbar sind

### Wichtige Test-Details
- `conftest.py` bietet `ocrmypdf` Modul Mocking, damit Tests ohne Tesseract/Ghostscript laufen
- Tests importieren von `src/` über `pythonpath` in `pyproject.toml`
- Führen Sie `pytest` aus, um alle verfügbaren Tests auszuführen; Integrations-Tests werden anmutig übersprungen
- Markierung: `@pytest.mark.skipif(not HAS_TESSERACT, ...)` für bedingte Tests

### Test-Dateien
- `test_cli.py`: Argument Parsing, Fehlerfälle, Success Paths
- `test_api.py`: Endpunkt-Validierung, Datei-Upload, Response Header
- `test_cli_office.py`: Office-Dokumentbehandlung in CLI
- `test_api_office.py`: Office-Dokumentbehandlung in API
- `test_format_converter.py`: Format-Erkennung und Office-Konvertierung
- `integration/test_office_conversion.py`: End-to-End Office→PDF/A Konvertierung

## Code-Qualitätsstandards

### Python & Stil
- **Python 3.11+** erforderlich
- **Code-Formatierung**: `black` mit 88-Zeichen-Zeilenlänge
- **Linting**: `ruff` überprüft E (Fehler), F (pyflakes), W (Warnungen), I (Importe), UP (Upgrades), N (Naming), D (Docstrings)
- Docstring erforderlich für alle Module, Funktionen, Klassen außer bestimmten Fällen (D100, D101, D102, D103, D104, D105 ignoriert)

### Entwicklungspraktiken
- Befolgen Sie PEP 8 Konventionen
- Organisieren Sie Module nach Verantwortung
- Halten Sie Methoden fokussiert und prägnant
- **Wickeln Sie Importe nicht in try/except** (pro AGENTS.md)
- Schreiben Sie alle Dokumentation und Kommentare auf Englisch

## Konfiguration

### CLI-Parameter
- `input_file`: Pfad zur Eingabedatei (Positionsargument) - unterstützt PDF, DOCX, PPTX, XLSX, ODT, ODS, ODP
- `output_pdf`: Pfad zur PDF/A-Ausgabedatei (Positionsargument)
- `--language` / `-l`: Tesseract-Sprachcodes, Standard "deu+eng"
- `--pdfa-level`: PDF/A-Konformitätsstufe (1, 2 oder 3), Standard "2"
- `--no-ocr`: OCR deaktivieren
- `-v, --verbose`: Debug-Logging aktivieren
- `--log-file`: Logs in eine Datei schreiben

### API-Parameter
- `file`: Datei-Upload (multipart/form-data)
- `language`: Tesseract-Codes (Standard "deu+eng")
- `pdfa_level`: PDF/A-Stufe als String (Standard "2")
- `ocr_enabled`: Ob OCR durchgeführt werden soll (Standard true)

### Projektkonfiguration
- **Tool-Versionen** in `pyproject.toml` geben Mindestversionen an
- **Entry Point**: `pdfa-cli` → `pdfa.cli:main`
- **API-App**: `pdfa.api:app` für ASGI-Server

## Wichtige Implementierungsdetails

### Typsystem
- Verwendet Python 3.11+ Type Hints überall
- `Literal` Typen für Konfiguration: `PdfaLevel = Literal["1", "2", "3"]`
- `pathlib.Path` für Dateipfade in Kernlogik

### Temporäre Dateiverwaltung (API)
- REST-Endpunkt nutzt `TemporaryDirectory()` Context Manager für hochgeladene Dateien
- Gewährleistet Cleanup auch bei Fehlern; unterstützt saubere Streaming-Semantik

### Konfigurationsverteilung
- Konfiguration (Sprache, PDF/A-Stufe) wird als **Funktionsargumente** übergeben, nicht Umgebungsvariablen
- Ermöglicht Per-Request-Konfiguration in API, einfacheres Testen, kein globaler Status

### Abhängigkeits-Abstraktion
- OCRmyPDF im Modul importiert (mockbar in Tests)
- Einfacher Wrapper um `ocrmypdf.ocr()` für Wartbarkeit
- API-Response umfasst korrekte Header: `Content-Type: application/pdf`, `Content-Disposition: attachment`

### Office-Dokumentbehandlung
- LibreOffice über subprocess aufgerufen für Office→PDF Konvertierung
- Temporäre PDFs automatisch bereinigt
- Unterstützt DOCX, PPTX, XLSX (MS Office) und ODT, ODS, ODP (OpenDocument)

## Dateireferenz

| Datei | Zweck |
|---|---|
| `src/pdfa/converter.py` | Kernkonvertierungslogik; Single Source of Truth für OCRmyPDF-Integration |
| `src/pdfa/cli.py` | CLI mit argparse; Entry Point ist `main(argv)` |
| `src/pdfa/api.py` | FastAPI-App; Endpunkt ist `POST /convert` |
| `src/pdfa/format_converter.py` | Office→PDF Konvertierung via LibreOffice |
| `src/pdfa/exceptions.py` | Benutzerdefinierte Exceptions |
| `src/pdfa/logging_config.py` | Logging-Konfiguration |
| `src/pdfa/__init__.py` | Paket-Metadaten (Version) |
| `tests/conftest.py` | Pytest Fixtures, OCRmyPDF Mocking |
| `tests/test_cli.py` | CLI Unit-Tests |
| `tests/test_api.py` | API Endpunkt Unit-Tests |
| `tests/test_cli_office.py` | CLI Office-Handling Tests |
| `tests/test_api_office.py` | API Office-Handling Tests |
| `tests/test_format_converter.py` | Format-Erkennung und Office-Konvertierung Tests |
| `tests/integration/test_office_conversion.py` | End-to-End Integration Tests |
| `pyproject.toml` | Projekt-Metadaten, Abhängigkeiten, Tool-Konfigurationen |

## Entwicklungs-Workflow

1. **Änderungen vornehmen** in `src/pdfa/` oder `tests/`
2. **Code formatieren**: `black src tests`
3. **Linten**: `ruff check src tests --fix` (Auto-Fix wenn möglich)
4. **Tests ausführen**: `pytest` (Pflicht vor Commit)
5. **README.md aktualisieren** wenn sich Verhalten ändert
6. **Committen** mit prägnanter, imperativer Nachricht

## Hinweise für zukünftige Entwicklung

- **Einzelne Konvertierungsfunktion** ist absichtlich: Sowohl CLI als auch API müssen die gleiche `convert_to_pdfa()` aufrufen, um synchron zu bleiben
- **Gemockte Tests zuerst**: Fügen Sie Unit-Tests mit gemocktem OCRmyPDF vor Integrationstests hinzu
- **Fehlerbehandlung**: Neue OCRmyPDF-Exceptions sollten in beiden Schnittstellen konsistent gefangen und übersetzt werden
- **Konfiguration**: Neue Parameter sollten Funktionsargumente sein, nicht Globale oder Umgebungsvariablen
- **Type Hints**: Erhalten Sie Type Coverage für IDE-Unterstützung und Klarheit
- **Office-Dokumentunterstützung**: Erweiterungen sollten LibreOffice nutzen, nicht Python-Bibliotheken
