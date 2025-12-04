# PDF-Komprimierungs-Konfiguration

**Dokumentation in anderen Sprachen**: [English](COMPRESSION.md)

Der PDF/A-Service bietet umfangreiche Konfigurationsmöglichkeiten für die PDF-Komprimierung, um die Balance zwischen Dateigröße und Bildqualität optimal anzupassen.

## Übersicht der Parameter

Alle Komprimierungsparameter können über Umgebungsvariablen konfiguriert werden. Die Standardwerte bieten eine ausgewogene Balance zwischen Qualität und Dateigröße.

### PDFA_IMAGE_DPI

**Beschreibung:** Ziel-Auflösung für Bilder in DPI (Dots Per Inch)

**Standardwert:** `150`

**Gültiger Bereich:** 72-600 DPI

**Auswirkungen:**
- **Niedrigere Werte (72-100 DPI):**
  - Kleinere Dateigrößen (bis zu 80% Reduktion)
  - Geeignet für reine Textdokumente
  - Bilder können pixelig erscheinen
  - Optimal für Archivierung mit wenig Bildinhalt

- **Mittlere Werte (150-200 DPI):**
  - Ausgewogenes Verhältnis (Standard)
  - Gute Lesbarkeit von Text und Bildern
  - Moderate Dateigröße
  - Ideal für die meisten Bürodokumente

- **Höhere Werte (300-600 DPI):**
  - Hochwertige Bildqualität
  - Größere Dateien (2-4x größer als 150 DPI)
  - Notwendig für Fotos und detaillierte Grafiken
  - Empfohlen für Druckvorlagen

**Beispiel:**
```yaml
- PDFA_IMAGE_DPI=100  # Aggressive Komprimierung
- PDFA_IMAGE_DPI=150  # Balanced (Standard)
- PDFA_IMAGE_DPI=300  # Hohe Qualität
```

### PDFA_JPG_QUALITY

**Beschreibung:** JPEG-Komprimierungsqualität für Farbbilder

**Standardwert:** `85`

**Gültiger Bereich:** 1-100 (höher = bessere Qualität)

**Auswirkungen:**
- **Niedrige Werte (60-75):**
  - Deutliche Dateigröße-Reduktion (50-70% kleiner)
  - Sichtbare JPEG-Artefakte möglich
  - Nur für unkritische Dokumente geeignet

- **Mittlere Werte (80-90):**
  - Gute Balance (Standard: 85)
  - Kaum sichtbare Qualitätsverluste
  - Empfohlen für die meisten Anwendungsfälle

- **Hohe Werte (91-100):**
  - Minimale Kompression
  - Sehr hohe Bildqualität
  - Deutlich größere Dateien
  - Nur bei kritischen Anforderungen nutzen

**Beispiel:**
```yaml
- PDFA_JPG_QUALITY=70  # Starke Komprimierung
- PDFA_JPG_QUALITY=85  # Balanced (Standard)
- PDFA_JPG_QUALITY=95  # Hohe Qualität
```

### PDFA_OPTIMIZE

**Beschreibung:** OCRmyPDF-Optimierungslevel

**Standardwert:** `1`

**Gültige Werte:** 0, 1, 2, 3

**Auswirkungen:**
- **Level 0 (Keine Optimierung):**
  - Schnellste Verarbeitung
  - Größte Dateien
  - Nur für Testzwecke empfohlen

- **Level 1 (Niedrige Optimierung):**
  - Verlustfreie Komprimierung
  - Schnelle Verarbeitung (Standard)
  - Moderate Dateigröße-Reduktion (20-30%)
  - Empfohlen für Produktivbetrieb

- **Level 2 (Mittlere Optimierung):**
  - Erfordert `pngquant` (im Docker-Image enthalten)
  - Bessere PNG-Komprimierung
  - Längere Verarbeitungszeit
  - 30-50% Dateigröße-Reduktion

- **Level 3 (Hohe Optimierung):**
  - Erfordert `pngquant`
  - Maximale Komprimierung
  - Deutlich längere Verarbeitungszeit
  - 40-60% Dateigröße-Reduktion
  - Nur bei hohem Optimierungsbedarf nutzen

**Beispiel:**
```yaml
- PDFA_OPTIMIZE=1  # Schnell und verlustfrei (Standard)
- PDFA_OPTIMIZE=2  # Bessere Komprimierung
- PDFA_OPTIMIZE=3  # Maximale Komprimierung (langsam)
```

### PDFA_REMOVE_VECTORS

**Beschreibung:** Vektorgrafiken in Rastergrafiken umwandeln

**Standardwert:** `true`

**Gültige Werte:** `true`, `false`, `1`, `0`, `yes`, `no`

**Auswirkungen:**
- **true (aktiviert):**
  - Vektorgrafiken werden gerastert
  - Kleinere Dateien (bis zu 50% bei vielen Vektoren)
  - Möglicher Qualitätsverlust bei Skalierung
  - Empfohlen für Archivierung

- **false (deaktiviert):**
  - Vektorgrafiken bleiben erhalten
  - Größere Dateien
  - Bessere Skalierbarkeit
  - Empfohlen für Dokumente mit vielen Diagrammen/Logos

**Beispiel:**
```yaml
- PDFA_REMOVE_VECTORS=true   # Kleinere Dateien (Standard)
- PDFA_REMOVE_VECTORS=false  # Vektorgrafiken behalten
```

### PDFA_JBIG2_LOSSY

**Beschreibung:** Verlustbehaftete JBIG2-Komprimierung für Schwarz-Weiß-Bilder

**Standardwert:** `false`

**Gültige Werte:** `true`, `false`, `1`, `0`, `yes`, `no`

**Auswirkungen:**
- **false (verlustfrei):**
  - Empfohlen für Textdokumente (Standard)
  - Keine Qualitätsverluste
  - Sehr gute Komprimierung für S/W-Bilder
  - Text bleibt lesbar

- **true (verlustbehaftet):**
  - Noch kleinere Dateien (zusätzlich 10-30%)
  - Mögliche Textveränderungen
  - **Nicht empfohlen** für wichtige Dokumente
  - Nur für unkritische Archive

**Warnung:** Verlustbehaftete JBIG2-Komprimierung kann Text verändern und sollte für offizielle Dokumente vermieden werden!

**Beispiel:**
```yaml
- PDFA_JBIG2_LOSSY=false  # Sicher und empfohlen (Standard)
- PDFA_JBIG2_LOSSY=true   # Nur für unkritische Dokumente
```

### PDFA_JBIG2_PAGE_GROUP_SIZE

**Beschreibung:** Anzahl der Seiten, die für JBIG2-Komprimierung gruppiert werden

**Standardwert:** `10`

**Gültiger Bereich:** 0-100+ (0 deaktiviert Gruppierung)

**Auswirkungen:**
- **0 (deaktiviert):**
  - Keine seitenübergreifende Komprimierung
  - Schnellere Verarbeitung
  - Größere Dateien

- **10-20 (empfohlen):**
  - Gute Balance (Standard: 10)
  - Findet Muster über mehrere Seiten
  - Moderate Verarbeitungszeit

- **50-100 (aggressiv):**
  - Maximale Komprimierung für große Dokumente
  - Längere Verarbeitungszeit
  - Besonders effektiv bei wiederholenden Inhalten

**Beispiel:**
```yaml
- PDFA_JBIG2_PAGE_GROUP_SIZE=0   # Keine Gruppierung
- PDFA_JBIG2_PAGE_GROUP_SIZE=10  # Standard
- PDFA_JBIG2_PAGE_GROUP_SIZE=50  # Aggressive Komprimierung
```

## Vordefinierte Profile

Die `compression_config.py` definiert folgende vorgefertigte Profile:

### balanced (Standard)
Ausgewogene Einstellungen für die meisten Anwendungsfälle:
```yaml
- PDFA_IMAGE_DPI=150
- PDFA_JPG_QUALITY=85
- PDFA_OPTIMIZE=1
- PDFA_REMOVE_VECTORS=true
- PDFA_JBIG2_LOSSY=false
- PDFA_JBIG2_PAGE_GROUP_SIZE=10
```

**Ideal für:** Bürodokumente, allgemeine Archivierung

### quality (Hohe Qualität)
Maximale Qualität mit moderater Komprimierung:
```yaml
- PDFA_IMAGE_DPI=300
- PDFA_JPG_QUALITY=95
- PDFA_OPTIMIZE=1
- PDFA_REMOVE_VECTORS=false
- PDFA_JBIG2_LOSSY=false
- PDFA_JBIG2_PAGE_GROUP_SIZE=10
```

**Ideal für:** Druckvorlagen, Fotos, detaillierte Grafiken

### aggressive (Starke Komprimierung)
Deutliche Dateigröße-Reduktion bei akzeptabler Qualität:
```yaml
- PDFA_IMAGE_DPI=100
- PDFA_JPG_QUALITY=75
- PDFA_OPTIMIZE=3
- PDFA_REMOVE_VECTORS=true
- PDFA_JBIG2_LOSSY=false
- PDFA_JBIG2_PAGE_GROUP_SIZE=20
```

**Ideal für:** Langzeitarchivierung, große Dokumentenmengen

### minimal (Maximale Komprimierung)
Kleinste Dateigröße für unkritische Dokumente:
```yaml
- PDFA_IMAGE_DPI=72
- PDFA_JPG_QUALITY=70
- PDFA_OPTIMIZE=3
- PDFA_REMOVE_VECTORS=true
- PDFA_JBIG2_LOSSY=false
- PDFA_JBIG2_PAGE_GROUP_SIZE=50
```

**Ideal für:** Nur Lesbarkeit wichtig, maximale Speicherplatzersparnis

## Verwendung in docker-compose.yml

Die Standardeinstellungen sind bereits in `docker-compose.yml` konfiguriert. Passen Sie diese nach Bedarf an:

```yaml
services:
  pdfa:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
      # Beispiel: Aggressive Komprimierung
      - PDFA_IMAGE_DPI=100
      - PDFA_JPG_QUALITY=75
      - PDFA_OPTIMIZE=3
      - PDFA_REMOVE_VECTORS=true
      - PDFA_JBIG2_LOSSY=false
      - PDFA_JBIG2_PAGE_GROUP_SIZE=20
    restart: unless-stopped
```

## Verwendung in der CLI

Die CLI liest die gleichen Umgebungsvariablen:

```bash
# Mit Standardeinstellungen
pdfa-cli input.pdf output.pdf

# Mit angepassten Einstellungen
export PDFA_IMAGE_DPI=100
export PDFA_JPG_QUALITY=75
pdfa-cli input.pdf output.pdf

# Einmalig für einen Befehl
PDFA_IMAGE_DPI=300 PDFA_JPG_QUALITY=95 pdfa-cli foto.pdf output.pdf
```

## Empfehlungen nach Anwendungsfall

### Textdokumente (Rechnungen, Verträge)
```yaml
- PDFA_IMAGE_DPI=150
- PDFA_JPG_QUALITY=80
- PDFA_OPTIMIZE=1
- PDFA_REMOVE_VECTORS=true
- PDFA_JBIG2_LOSSY=false
```
**Ergebnis:** Kleine Dateien, gute Lesbarkeit, sichere Archivierung

### Dokumente mit Fotos
```yaml
- PDFA_IMAGE_DPI=200
- PDFA_JPG_QUALITY=90
- PDFA_OPTIMIZE=2
- PDFA_REMOVE_VECTORS=false
- PDFA_JBIG2_LOSSY=false
```
**Ergebnis:** Gute Bildqualität, moderate Dateigröße

### Gescannte Dokumente
```yaml
- PDFA_IMAGE_DPI=150
- PDFA_JPG_QUALITY=80
- PDFA_OPTIMIZE=2
- PDFA_REMOVE_VECTORS=true
- PDFA_JBIG2_LOSSY=false
- PDFA_JBIG2_PAGE_GROUP_SIZE=20
```
**Ergebnis:** Optimale Komprimierung für Scans

### Technische Zeichnungen/Diagramme
```yaml
- PDFA_IMAGE_DPI=300
- PDFA_JPG_QUALITY=90
- PDFA_OPTIMIZE=1
- PDFA_REMOVE_VECTORS=false
- PDFA_JBIG2_LOSSY=false
```
**Ergebnis:** Scharfe Linien, verlustfreie Vektoren

## Performance-Hinweise

Die Verarbeitungsgeschwindigkeit wird hauptsächlich von diesen Parametern beeinflusst:

1. **PDFA_OPTIMIZE:** Level 3 ist deutlich langsamer (3-5x) als Level 1
2. **PDFA_IMAGE_DPI:** Höhere DPI = längere Verarbeitung
3. **PDFA_JBIG2_PAGE_GROUP_SIZE:** Größere Werte = längere Verarbeitung

**Empfehlung für Produktivbetrieb:**
- Verwenden Sie `PDFA_OPTIMIZE=1` für schnelle Verarbeitung
- Nutzen Sie Level 2-3 nur nachts oder in Batch-Jobs
- Testen Sie die Einstellungen mit repräsentativen Dokumenten

## Dateigröße-Erwartungen

Beispiele für ein typisches 10-seitiges Dokument mit Text und Bildern:

| Konfiguration | Dateigröße | Qualität | Geschwindigkeit |
|---------------|------------|----------|-----------------|
| **quality** | ~2.5 MB | Ausgezeichnet | Schnell |
| **balanced** (Standard) | ~1.2 MB | Sehr gut | Schnell |
| **aggressive** | ~600 KB | Gut | Mittel |
| **minimal** | ~400 KB | Akzeptabel | Langsam |

Ergebnisse variieren je nach Dokumentinhalt erheblich.

## Fehlerbehebung

### Qualität zu niedrig
- Erhöhen Sie `PDFA_IMAGE_DPI` auf 200 oder 300
- Erhöhen Sie `PDFA_JPG_QUALITY` auf 90 oder höher
- Setzen Sie `PDFA_REMOVE_VECTORS=false`

### Dateien zu groß
- Reduzieren Sie `PDFA_IMAGE_DPI` auf 100-120
- Reduzieren Sie `PDFA_JPG_QUALITY` auf 75-80
- Erhöhen Sie `PDFA_OPTIMIZE` auf 2 oder 3
- Erhöhen Sie `PDFA_JBIG2_PAGE_GROUP_SIZE` auf 20-50

### Verarbeitung zu langsam
- Verwenden Sie `PDFA_OPTIMIZE=1`
- Reduzieren Sie `PDFA_IMAGE_DPI`
- Reduzieren Sie `PDFA_JBIG2_PAGE_GROUP_SIZE`

## Weitere Informationen

- [OCRmyPDF Dokumentation](https://ocrmypdf.readthedocs.io/)
- [JBIG2 Komprimierung](https://en.wikipedia.org/wiki/JBIG2)
- [PDF/A Standards](https://www.pdfa.org/)
