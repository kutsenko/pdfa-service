# Gherkin Features

Dieses Verzeichnis enthält **Gherkin Feature-Dateien** im BDD-Format (Behavior Driven Development) für wichtige Features des PDF/A-Service.

This directory contains **Gherkin Feature files** in BDD format (Behavior Driven Development) for major features of the PDF/A service.

---

## Übersicht / Overview

| Feature | Szenarien | Sprache | Datei | User Story |
|---------|-----------|---------|-------|------------|
| MongoDB-Integration | 36 | Deutsch | [gherkin-mongodb-integration.feature](gherkin-mongodb-integration.feature) | [US-001](../user-stories/US-001-mongodb-integration.md) |
| Job Event Logging | 21 | Deutsch | [gherkin-job-event-logging.feature](gherkin-job-event-logging.feature) | [US-002](../user-stories/US-002-job-event-logging.md) |
| Lokaler Standardbenutzer | 18 | Deutsch | [gherkin-local-default-user.feature](gherkin-local-default-user.feature) | [US-003](../user-stories/US-003-local-default-user.md) |
| Camera Tab for Multi-Page Document Capture | 57 | English | [gherkin-camera-tab.feature](gherkin-camera-tab.feature) | [US-004](../user-stories/US-004-camera-tab.md) |
| Accessibility Camera Assistance | 65 | English | [gherkin-accessibility-camera-assistance.feature](gherkin-accessibility-camera-assistance.feature) | [US-005](../user-stories/US-005-accessibility-camera-assistance.md) |

**Gesamt**: 197 Szenarien in 5 Features

---

## Gherkin Format

Alle Features folgen dem **Gherkin**-Standard:

### Sprache
```gherkin
# language: de
```
Alle Features sind in **deutscher Sprache** verfasst.

### Struktur

```gherkin
Funktionalität: [Feature-Name]
  Als [Rolle]
  möchte ich [Ziel]
  damit [Nutzen]

  Hintergrund:
    Angenommen [Gemeinsamer Kontext für alle Szenarien]

  Szenario: [Beschreibung]
    Angenommen [Vorbedingung]
    Wenn [Aktion]
    Dann [Erwartetes Ergebnis]
    Und [Weitere Erwartung]
```

### Keywords

- **Funktionalität** - Beschreibt das Feature
- **Als/möchte ich/damit** - User Story Format
- **Hintergrund** - Gemeinsame Vorbedingungen
- **Szenario** - Einzelner Testfall
- **Angenommen** - Vorbedingung (Given)
- **Wenn** - Aktion (When)
- **Dann** - Erwartung (Then)
- **Und** - Weitere Schritte (And)

---

## Features

### [gherkin-mongodb-integration.feature](gherkin-mongodb-integration.feature)

**Feature**: Persistente Datenspeicherung mit MongoDB

**Beschreibung**: MongoDB-Integration für Conversion-History, OAuth-Tokens und Audit-Logs

**Szenarien**: 36 in 10 Gruppen

**Szenario-Gruppen**:
1. **Service-Start und MongoDB-Verbindung** (3 Szenarien)
   - Service startet mit MongoDB
   - Service-Start schlägt fehl ohne MongoDB
   - Falsche Credentials

2. **Job-Persistierung** (6 Szenarien)
   - Job-Erstellung
   - Status-Updates
   - Job-Completion mit Metadaten
   - Fehlgeschlagene Jobs
   - Jobs ohne Authentifizierung
   - TTL-Cleanup

3. **OAuth State Token Management** (4 Szenarien)
   - Token-Speicherung
   - Token-Validierung
   - Token-Ablauf
   - Multi-Instance-OAuth

4. **User-Profile** (3 Szenarien)
   - Neuer User bei erstem Login
   - Bestehender User bei Login
   - Minimale User-Profile

5. **Audit Logs** (5 Szenarien)
   - Login-Event
   - Fehlgeschlagener Login
   - Job-Erstellung
   - TTL-Cleanup
   - Security-Events-Abfrage

6. **Indexes und Performance** (3 Szenarien)
   - Index-Erstellung beim Start
   - Effiziente Job-Queries
   - Automatischer TTL-Cleanup

7. **Repository-Pattern** (4 Szenarien)
   - JobRepository.create_job()
   - JobRepository.update_job_status()
   - UserRepository.find_or_create_user()
   - OAuthStateRepository.validate_and_consume_state()

8. **Error Handling** (3 Szenarien)
   - Verbindungsfehler
   - Duplicate-Key-Error
   - Connection Pooling

9. **Backward Compatibility** (2 Szenarien)
   - Alte Jobs ohne neue Felder
   - Migration von In-Memory zu MongoDB

10. **Multi-Instance Deployment** (3 Szenarien)
    - Geteilte MongoDB zwischen Instanzen
    - Job-Updates von verschiedenen Instanzen
    - OAuth über Instanzen hinweg

**Zugehörige User Story**: [US-001: MongoDB-Integration](../user-stories/US-001-mongodb-integration.md)

---

### [gherkin-job-event-logging.feature](gherkin-job-event-logging.feature)

**Feature**: Detaillierte Event-Protokollierung für Konvertierungsaufträge

**Beschreibung**: Event-basiertes Logging-System für alle Konvertierungsentscheidungen

**Szenarien**: 21 in 9 Gruppen

**Szenario-Gruppen**:
1. **OCR-Entscheidung** (3 Szenarien)
   - OCR skip wegen Tagged-PDF
   - OCR skip wegen vorhandenem Text
   - OCR perform wegen fehlendem Text

2. **Format-Konvertierung** (3 Szenarien)
   - Office→PDF Konvertierung
   - Bild→PDF Konvertierung
   - PDF ohne Format-Konvertierung

3. **Fallback-Mechanismen** (3 Szenarien)
   - Tier 2 Fallback bei Ghostscript-Fehler
   - Tier 3 Fallback (kein OCR)
   - Keine Fallbacks bei Erfolg

4. **Pass-through-Modus** (2 Szenarien)
   - Pass-through für PDF-Ausgabe ohne OCR
   - Pass-through mit Tag-Erhaltung

5. **Kompressionsprofilwahl** (2 Szenarien)
   - Benutzer wählt Quality-Profil
   - Auto-Switch zu Preserve-Profil

6. **Job-Lifecycle-Events** (2 Szenarien)
   - Job-Timeout
   - Job-Cleanup wegen Alter

7. **Rückwärtskompatibilität** (2 Szenarien)
   - Alte Jobs ohne events-Feld
   - Neue Events zu alten Jobs hinzufügen

8. **Vollständige Job-Lifecycle-Beispiele** (2 Szenarien)
   - Office-Dokument mit OCR-Skip
   - Gescannte PDF mit Fallback

9. **Error Handling** (2 Szenarien)
   - Event-Logging-Fehler blockieren Konvertierung nicht
   - Event-Callback ist optional

**Zugehörige User Story**: [US-002: Job Event Logging](../user-stories/US-002-job-event-logging.md)

---

### [gherkin-local-default-user.feature](gherkin-local-default-user.feature)

**Feature**: Lokaler Standardbenutzer für Non-Auth-Modus

**Beschreibung**: Automatische Erstellung eines Standardbenutzers wenn Authentifizierung deaktiviert ist

**Szenarien**: 18 in 7 Gruppen

**Szenario-Gruppen**:
1. **Service-Start und Default User-Erstellung** (3 Szenarien)
   - Service mit deaktivierter Auth
   - Service mit aktivierter Auth (kein Default User)
   - Idempotente Erstellung

2. **Konfigurierbare Standardbenutzer-Felder** (2 Szenarien)
   - Custom Werte aus Umgebungsvariablen
   - Teilweise Custom-Werte

3. **Job-Attribution mit Default User** (3 Szenarien)
   - Job via WebSocket mit Default User
   - Custom Default User ID
   - OAuth User bei aktivierter Auth

4. **Job-Verlauf-Abfrage** (3 Szenarien)
   - Jobs des Default Users
   - Leerer Verlauf für neuen User
   - Custom Default User Verlauf

5. **Dependency Injection** (3 Szenarien)
   - get_current_user_optional() mit Default User
   - OAuth User bei aktivierter Auth
   - Fallback bei fehlender Config

6. **Edge Cases und Error Handling** (4 Szenarien)
   - MongoDB-Verbindungsfehler
   - Wechsel enabled→disabled
   - Wechsel disabled→enabled
   - Gelöschter Default User (Self-Healing)

7. **Vollständige Integration-Workflows** (2 Szenarien)
   - Kompletter Workflow ohne Auth
   - Multi-Instance-Deployment

**Zugehörige User Story**: [US-003: Lokaler Standardbenutzer](../user-stories/US-003-local-default-user.md)

---

### [gherkin-camera-tab.feature](gherkin-camera-tab.feature)

**Feature**: Camera Tab for Multi-Page Document Capture

**Description**: Browser-based camera interface for multi-page document scanning using getUserMedia API

**Scenarios**: 57 in 10 groups

**Scenario Groups**:
1. **Camera Access and Preview** (7 scenarios)
   - Permission request and grant
   - Live camera preview
   - Rear camera default on mobile
   - Camera selection dropdown
   - Camera switching
   - Permission denied error
   - No camera available fallback

2. **Photo Capture** (6 scenarios)
   - Capture button and Space bar
   - Full camera resolution
   - Camera shutter sound
   - Photo editor opening
   - Portrait and landscape support

3. **Photo Editor** (10 scenarios)
   - Image display
   - Rotation controls (left/right, multiple rotations)
   - Brightness and contrast adjustments
   - Combined adjustments
   - Accept and Retake buttons
   - Escape key handling

4. **Multi-Page Support** (8 scenarios)
   - First and subsequent pages
   - Page counter updates
   - Thumbnail generation
   - Unlimited pages
   - Camera preview between captures
   - Convert button states

5. **Page Management** (6 scenarios)
   - Drag and drop reordering
   - Page deletion
   - Delete all pages
   - Retake page
   - Thumbnail updates
   - Page renumbering

6. **Document Submission** (8 scenarios)
   - Single and multi-page submission
   - Progress indicator
   - PDF/A settings application
   - Compression profile
   - Successful conversion
   - Conversion errors
   - Network failure handling

7. **Accessibility Integration** (6 scenarios)
   - Accessibility checkbox visibility
   - Screen reader auto-enable
   - Manual activation
   - Auto-capture workflow
   - Auto-crop application
   - Multi-page accessibility

8. **Camera Settings** (3 scenarios)
   - Camera preference persistence
   - Seamless camera switching
   - Preference survival across sessions

9. **Error Handling** (4 scenarios)
   - Permission error instructions
   - getUserMedia error
   - Canvas error
   - API error with retry

10. **Responsive Design** (6 scenarios)
    - Desktop browser support
    - Mobile device support
    - Tablet support
    - Portrait orientation
    - Landscape orientation
    - Orientation change handling

**Related User Story**: [US-004: Camera Tab for Multi-Page Document Capture](../user-stories/US-004-camera-tab.md)

---

### [gherkin-accessibility-camera-assistance.feature](gherkin-accessibility-camera-assistance.feature)

**Feature**: Accessibility Camera Assistance for Blind Users

**Description**: Audio-guided document capture with automatic edge detection, auto-crop and perspective correction

**Scenarios**: 65 in 18 groups

**Scenario Groups**:
1. **Screen Reader Auto-Detection & Initialization** (3 scenarios)
   - Screen reader automatically detected
   - No screen reader - feature disabled
   - Manual activation

2. **iOS Safari Audio/TTS Unlock** (4 scenarios)
   - AudioContext unlock in user gesture
   - SpeechSynthesis unlock
   - Unlock tone is played
   - Immediate TTS announcement before library loading

3. **Page Reload AudioContext Handling** (2 scenarios)
   - AudioContext closed after reload
   - AudioContext suspended is resumed

4. **Edge Detection with jscanify** (4 scenarios)
   - jscanify loads successfully
   - CDN failed - degraded mode
   - OpenCV.js loads successfully
   - Real-time edge detection

5. **Confidence Calculation with Partial Capture** (5 scenarios)
   - 40% area - optimal confidence
   - 33% area - acceptable (1/3 document)
   - 10% area - minimal
   - 5% area - too small
   - 95% area - too close

6. **Hysteresis to Prevent Flickering** (3 scenarios)
   - Transition to "detected" (upper threshold)
   - Stays "detected" despite fluctuation
   - Transition to "lost" (lower threshold)

7. **Audio Feedback (Tones + TTS)** (5 scenarios)
   - Success tone on edge detection
   - Warning tone on edges lost
   - Continuous tone indicates confidence
   - TTS announcement throttling
   - Force-priority bypasses throttling

8. **Edge-Based Guidance** (4 scenarios)
   - Top edge too close
   - Multiple edges not visible
   - All edges visible - centered
   - Periodic guidance update

9. **Auto-Capture on Stable Recognition** (5 scenarios)
   - Stability counter increments
   - Countdown starts after 10 frames
   - Countdown announcements "2", "1"
   - Photo taken after countdown
   - Auto-capture canceled on loss

10. **Auto-Crop and Perspective Correction** (7 scenarios)
    - lastDetectedCorners stored
    - Auto-crop applied
    - Corner scaling to full resolution
    - OpenCV.js perspective correction
    - Mat to Canvas conversion
    - High-quality JPEG (90%)
    - Fallback on error

11. **Multilingualism (i18n)** (4 scenarios)
    - German announcements
    - English announcements
    - Spanish announcements
    - French announcements

12. **Visual Indicators** (2 scenarios)
    - Green overlay on success
    - Yellow overlay on warning

13. **ARIA Live Regions** (1 scenario)
    - Screen reader receives updates

14. **Volume Control** (1 scenario)
    - Volume slider changes volume

15. **Test Audio Button** (1 scenario)
    - Test audio plays tone and TTS

16. **Disable Feature** (2 scenarios)
    - Audio guidance disabled
    - AudioContext closed

17. **Error Handling** (3 scenarios)
    - Browser without Web Audio API
    - getUserMedia failed
    - Canvas 2D Context error

18. **Performance & Memory** (4 scenarios)
    - 10 FPS frame analysis
    - Analysis canvas 640x480
    - Capture canvas full resolution
    - OpenCV Mat memory cleanup

**Related User Story**: [US-005: Accessibility Camera Assistance](../user-stories/US-005-accessibility-camera-assistance.md)

---

## Verwendung / Usage

### Für Tester / For Testers

1. **Nutzen Sie Szenarien als Testfälle**
   - Jedes Szenario = 1 Testfall
   - Given-When-Then als Test-Struktur

2. **Führen Sie manuelle Tests durch**
   - Folgen Sie den Steps
   - Verifizieren Sie erwartete Ergebnisse

3. **Automatisieren Sie mit BDD-Tools**
   ```bash
   # Beispiel mit behave (Python)
   behave features/gherkin-mongodb-integration.feature
   ```

### Für Entwickler / For Developers

1. **Verstehen Sie Anforderungen**
   - Szenarien zeigen konkrete Beispiele
   - Tables definieren Datenstrukturen

2. **Implementieren Sie mit TDD**
   - Schreiben Sie Tests basierend auf Szenarien
   - RED-GREEN-REFACTOR

3. **Erweitern Sie bei Bedarf**
   - Fügen Sie neue Szenarien für Edge Cases hinzu
   - Dokumentieren Sie in Gherkin

### Für Product Owner / For Product Owners

1. **Validieren Sie Szenarien**
   - Sind alle wichtigen Fälle abgedeckt?
   - Stimmen Erwartungen?

2. **Akzeptieren Sie basierend auf Szenarien**
   - Alle Szenarien müssen erfüllt sein
   - Definition of Done

---

## Best Practices

### Szenario-Namen

✅ **Gut**: "OCR wird übersprungen wegen Tagged-PDF"
❌ **Schlecht**: "Test 1"

### Given-When-Then

✅ **Gut**:
```gherkin
Angenommen eine PDF-Datei "document.pdf" wird hochgeladen
Wenn der Konvertierungsjob ausgeführt wird
Dann sollte ein Event mit Typ "format_conversion" existieren
```

❌ **Schlecht**:
```gherkin
Angenommen PDF
Wenn job
Dann event
```

### Tables für Daten

✅ **Gut**:
```gherkin
Und die Konfiguration ist:
  | Parameter  | Wert |
  | pdfa_level | 2    |
  | ocr_enabled| true |
```

❌ **Schlecht**:
```gherkin
Und pdfa_level ist 2 und ocr_enabled ist true
```

### Dokumentation

✅ **Gut**: JSON-Beispiele in Multiline-Strings
```gherkin
Und die Event-Details sollten enthalten:
  """
  {
    "decision": "skip",
    "reason": "tagged_pdf"
  }
  """
```

---

## Gherkin-Syntax-Referenz

### Schlüsselwörter

| Deutsch | English | Verwendung |
|---------|---------|------------|
| Funktionalität | Feature | Feature-Beschreibung |
| Hintergrund | Background | Gemeinsame Vorbedingungen |
| Szenario | Scenario | Einzelner Testfall |
| Angenommen | Given | Vorbedingung/Kontext |
| Wenn | When | Aktion/Event |
| Dann | Then | Erwartetes Ergebnis |
| Und | And | Weitere Schritte |
| Aber | But | Negative Erwartung |

### Datenstrukturen

**Table**:
```gherkin
| Spalte1 | Spalte2 |
| Wert1   | Wert2   |
```

**Multiline String (Doc String)**:
```gherkin
"""
Mehrzeiliger
Text
"""
```

---

## Automatisierung

### Mit Behave (Python)

```bash
# Installation
pip install behave

# Feature ausführen
behave features/gherkin-mongodb-integration.feature

# Spezifisches Szenario
behave features/gherkin-mongodb-integration.feature:10
```

### Mit Cucumber (JavaScript)

```bash
# Installation
npm install @cucumber/cucumber

# Feature ausführen
npx cucumber-js features/
```

---

## Verwandte Dokumentation / Related Documentation

- [Zurück zur Übersicht](../README.md)
- [User Stories](../user-stories/)
- [AGENTS.md](../../../AGENTS.md)
- [Behave Dokumentation](https://behave.readthedocs.io/)
- [Cucumber Dokumentation](https://cucumber.io/docs/gherkin/)

---

## Änderungshistorie / Change History

| Datum | Version | Änderung |
|-------|---------|----------|
| 2024-12-25 | 1.0 | Initiale Erstellung |
