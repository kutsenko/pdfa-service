# CLAUDE.de.md - Schnellreferenz

Anleitung für Claude Code und AI Agents bei der Arbeit mit dem pdfa-service Repository.

**English Version**: [English](CLAUDE.md)

## ⚠️ Wichtig

Alle Entwicklungsrichtlinien sind in **[AGENTS.md](AGENTS.md)** konsolidiert - verwenden Sie diese als primäre Referenz.

Dieses Dokument ist eine Schnellreferenz. Für vollständige Details zu:
- Entwicklungsstandards und Code-Qualität
- Projektarchitektur und Design-Patterns
- Testanforderungen und -verfahren
- Sicherheitsrichtlinien
- Leistungsaspekte

Siehe [AGENTS.md](AGENTS.md).

---

## Schnelle Einrichtung

```bash
# Umgebungssetup (einmalig)
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Tägliche Befehle
pytest                              # Alle Tests ausführen (vor Commit erforderlich)
black src tests                     # Code formatieren
ruff check src tests --fix          # Linting und Auto-Fix
pdfa-cli --help                     # CLI testen
uvicorn pdfa.api:app --port 8000   # API lokal ausführen
```

## Wesentlich vor Commit

1. **Formatieren**: `black src tests`
2. **Linting**: `ruff check src tests --fix`
3. **Testen**: `pytest` (muss bestehen)
4. **Committen**: Klare, imperative Nachricht verwenden

## Wichtigste Dateien

| Datei | Zweck |
|-------|-------|
| `AGENTS.md` | **Vollständige Entwicklungsrichtlinien** (Single Source of Truth) |
| `src/pdfa/converter.py` | Kernkonvertierungslogik |
| `src/pdfa/cli.py` | CLI Entry Point |
| `src/pdfa/api.py` | REST API |
| `tests/` | Testsuite |
| `README.de.md` | Benutzerdokumentation (Deutsch) |

## Wichtigste Prinzipien

1. **Einzelne Konvertierungsfunktion**: CLI und API müssen `convert_to_pdfa()` verwenden
2. **Konfiguration als Argumente**: Konfiguration als Funktionsparameter übergeben, nicht als Globals
3. **Gemeinsame Fehlerbehandlung**: Konsistente Fehlerübersetzung über Schnittstellen hinweg
4. **Tests zuerst**: Zuerst Tests mit gemockten Abhängigkeiten schreiben, dann implementieren
5. **Type Hints**: Python 3.13+ Type Hints überall verwenden

## System-Setup

Vor dem Ausführen mit echten PDFs:
```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr ghostscript qpdf libreoffice

# Fedora
sudo dnf install tesseract ghostscript qpdf libreoffice

# Arch
sudo pacman -S tesseract ghostscript qpdf libreoffice-still
```

Tests laufen ohne diese Abhängigkeiten mit gemocktem OCRmyPDF.

## Projektstruktur

```
pdfa-service/
├── AGENTS.md                 # Entwicklungsrichtlinien (hier klicken!)
├── README.de.md              # Benutzerdokumentation (Deutsch)
├── OCR-SCANNER.de.md         # Scanner-Setup-Anleitung (Deutsch)
├── src/pdfa/
│   ├── converter.py          # Kernlogik (Single Source of Truth)
│   ├── cli.py                # CLI-Schnittstelle
│   ├── api.py                # REST API-Schnittstelle
│   ├── format_converter.py    # Office-Dokumentkonvertierung
│   ├── exceptions.py          # Benutzerdefinierte Exceptions
│   └── logging_config.py      # Logging-Setup
└── tests/
    ├── conftest.py           # Pytest-Konfiguration mit OCRmyPDF Mocking
    ├── test_cli.py           # CLI-Tests
    ├── test_api.py           # API-Tests
    ├── test_format_converter.py
    └── integration/          # Integrationstests (mit echtem OCRmyPDF)
```

## Häufige Aufgaben

### Eine neue Funktion hinzufügen

1. Unit-Tests schreiben (mit gemocktem OCRmyPDF) in `tests/`
2. In `converter.py` implementieren (gemeinsame Kernlogik)
3. CLI-Unterstützung in `cli.py` hinzufügen
4. API-Unterstützung in `api.py` hinzufügen
5. `README.de.md` mit Beispielen aktualisieren
6. Vollständige Testsuite ausführen: `pytest`
7. Mit klarer Nachricht committen

### Bestimmten Test ausführen

```bash
pytest tests/test_cli.py::test_main_success
pytest -k "office"  # Tests mit Pattern ausführen
```

### Ein Problem debuggen

```bash
# Vollständige Fehlerausgabe sehen
pytest -v tests/test_file.py

# Mit Print-Anweisungen ausführen
pytest -s tests/test_file.py

# Einzelnen Test mit Debugging ausführen
python -m pdb -c continue -m pytest tests/test_file.py::test_name
```

## Code-Qualitäts-Checkliste

Vor jedem Commit:

- [ ] Alle Tests bestehen: `pytest`
- [ ] Code formatiert: `black src tests`
- [ ] Keine Linting-Probleme: `ruff check src tests`
- [ ] Smoke Test bestanden: `pdfa-cli --help`
- [ ] Commit-Nachricht ist klar und imperativ
- [ ] README.de.md aktualisiert, falls Verhalten sich geändert hat

## Architektur-Erinnerung

Das Schlüsseldesignprinzip gewährleistet Konsistenz:

```
                    Beide Schnittstellen verwenden dieselbe Funktion
                            ↓
                    convert_to_pdfa()
                       ↙          ↖
                     CLI          API
                   (/bin)      (HTTP)
```

Niemals Logik zwischen CLI und API duplizieren. Gemeinsame Logik immer in `converter.py` platzieren.

## Hilfe erhalten

- **Entwicklungsrichtlinien**: Lesen Sie [AGENTS.md](AGENTS.md)
- **Benutzerfragen**: Siehe [README.de.md](README.de.md)
- **Setup-Anweisungen**: Siehe [OCR-SCANNER.de.md](OCR-SCANNER.de.md)
- **Architektur-Details**: Abschnitt "Project Architecture" in [AGENTS.md](AGENTS.md)

---

**Denken Sie daran**: AGENTS.md ist Ihre Single Source of Truth für Entwicklungspraktiken.
