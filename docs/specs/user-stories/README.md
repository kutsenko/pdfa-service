# User Stories

Dieses Verzeichnis enthält formale User Stories im **INVEST**-Format für wichtige Features des PDF/A-Service.

This directory contains formal User Stories in **INVEST** format for major features of the PDF/A service.

---

## Übersicht / Overview

| ID | Titel | Status | Datum | Datei | Gherkin Feature |
|----|-------|--------|-------|-------|-----------------|
| US-001 | MongoDB-Integration | ✅ Implementiert | 2024-12-21 | [US-001-mongodb-integration.md](US-001-mongodb-integration.md) | [Feature](../features/gherkin-mongodb-integration.feature) |
| US-002 | Job Event Logging | ✅ Implementiert | 2024-12-25 | [US-002-job-event-logging.md](US-002-job-event-logging.md) | [Feature](../features/gherkin-job-event-logging.feature) |
| US-003 | Lokaler Standardbenutzer | ✅ Implementiert | 2024-12-25 | [US-003-local-default-user.md](US-003-local-default-user.md) | [Feature](../features/gherkin-local-default-user.feature) |
| US-007 | Camera Tab for Multi-Page Document Capture | ✅ Implemented | 2025-12-30 | [US-007-camera-tab.md](US-007-camera-tab.md) | [Feature](../features/gherkin-camera-tab.feature) |
| US-008 | Accessibility Camera Assistance | ✅ Implemented | 2026-01-01 | [US-008-accessibility-camera-assistance.md](US-008-accessibility-camera-assistance.md) | [Feature](../features/gherkin-accessibility-camera-assistance.feature) |

---

## INVEST-Prinzipien

Alle User Stories folgen dem **INVEST**-Prinzip:

- **I**ndependent - Unabhängig voneinander implementierbar
- **N**egotiable - Flexibel mit klaren Prioritäten
- **V**aluable - Klarer Business-Value
- **E**stimable - Zeitschätzungen möglich
- **S**mall - In 3-5 Tagen umsetzbar
- **T**estable - Mit Akzeptanzkriterien testbar

---

## User Story Struktur

Jede User Story enthält:

### 1. Metadaten
- **ID**: Eindeutige Kennung (US-XXX)
- **Titel**: Kurzbeschreibung
- **Status**: In Arbeit / Implementiert / Abgelehnt
- **Datum**: Erstellungsdatum

### 2. Story
```
Als [Rolle]
möchte ich [Funktion]
damit [Nutzen]
```

### 3. Kontext
- Aktueller Zustand (Ist)
- Problemstellung
- Lösung (Soll)

### 4. Akzeptanzkriterien
Given-When-Then Format:
```
Given [Vorbedingung]
When [Aktion]
Then [Erwartetes Ergebnis]
And [Weitere Erwartungen]
```

### 5. Definition of Done
Checkliste mit klaren Abnahmekriterien:
- [ ] Tests bestehen
- [ ] Code formatiert
- [ ] Dokumentation aktualisiert
- etc.

### 6. Technische Details
- Datenmodelle
- Architektur
- Implementierte Komponenten
- Deployment-Informationen

### 7. Risiken & Mitigationen
Tabelle mit:
- Risiko
- Wahrscheinlichkeit
- Impact
- Mitigation

### 8. Verwandte Spezifikationen
Links zu:
- Verwandten User Stories
- Gherkin Features
- Dokumentation

### 9. Änderungshistorie
Versions-Tracking mit:
- Datum
- Version
- Änderung

---

## User Stories

### [US-001: MongoDB-Integration](US-001-mongodb-integration.md)

**Story**: Als Systemadministrator möchte ich persistente Datenspeicherung mit MongoDB, damit Jobs Server-Neustarts überleben.

**Kernpunkte**:
- 4 MongoDB Collections (users, jobs, oauth_states, audit_logs)
- TTL-Indexes für automatische Cleanup
- Repository-Pattern für Datenzugriff
- Multi-Instance-fähig

**Status**: ✅ Implementiert (2024-12-21)

**Gherkin Feature**: [36 Szenarien](../features/gherkin-mongodb-integration.feature)

---

### [US-002: Job Event Logging](US-002-job-event-logging.md)

**Story**: Als Benutzer möchte ich detaillierte Event-Listen für jeden Job, damit ich Konvertierungsentscheidungen nachvollziehen kann.

**Kernpunkte**:
- 7 Event-Typen (format_conversion, ocr_decision, etc.)
- Event-Callback-Pattern in converter.py
- Async Event-Logger-Helper
- Backward-kompatibel (default_factory)

**Status**: ✅ Implementiert (2024-12-25)

**Gherkin Feature**: [21 Szenarien](../features/gherkin-job-event-logging.feature)

---

### [US-003: Lokaler Standardbenutzer](US-003-local-default-user.md)

**Story**: Als Benutzer ohne OAuth möchte ich einen automatischen lokalen Standardbenutzer, damit ich Features wie Job-Verlauf nutzen kann.

**Kernpunkte**:
- Automatische Erstellung bei AUTH_ENABLED=false
- Konfigurierbar via Umgebungsvariablen
- Idempotente Implementierung (Multi-Instance-safe)
- Dependency Injection gibt User statt None zurück

**Status**: ✅ Implementiert (2024-12-25)

**Gherkin Feature**: [18 Szenarien](../features/gherkin-local-default-user.feature)

---

### [US-007: Camera Tab for Multi-Page Document Capture](US-007-camera-tab.md)

**Story**: As a user of the PDF/A service, I want to capture multi-page documents using my device's camera directly in the browser so that I can create searchable PDF/A documents without needing a physical scanner or separate app.

**Key Points**:
- Browser-based camera interface using getUserMedia API
- Multi-page document capture with page management
- Built-in photo editor (rotation, brightness, contrast)
- Direct submission to PDF/A conversion pipeline
- Integration with accessibility features (US-008)
- Progressive Web App capabilities (works offline)

**Status**: ✅ Implemented (2025-12-30)

**Gherkin Feature**: [57 scenarios](../features/gherkin-camera-tab.feature)

---

### [US-008: Accessibility Camera Assistance](US-008-accessibility-camera-assistance.md)

**Story**: As a blind or visually impaired user I want to photograph documents using audio guidance so that I can create high-quality document scans without visual control with automatic cropping and perspective correction.

**Key Points**:
- Real-time edge detection with jscanify v1.4.0 and OpenCV.js 4.7.0
- Audio feedback via Web Audio API (tones) and Speech Synthesis API (TTS)
- iOS Safari compatibility (AudioContext + SpeechSynthesis unlock)
- Automatic capture on stable document recognition (10 frames)
- Auto-crop and perspective correction with full resolution
- Edge-based guidance ("Top edge not visible" instead of "Move camera down")
- Partial capture (10-90% of area, optimized for 1/3 documents)
- Hysteresis to prevent flickering (45%/35% thresholds)
- Multilingual (de, en, es, fr)

**Status**: ✅ Implemented (2026-01-01)

**Gherkin Feature**: [65 scenarios](../features/gherkin-accessibility-camera-assistance.feature)

---

## Verwendung / Usage

### Für Entwickler / For Developers

1. **Lesen Sie die komplette User Story** vor Implementierung
2. **Verstehen Sie den Business-Value** (Warum?)
3. **Prüfen Sie Akzeptanzkriterien** (Was muss erfüllt sein?)
4. **Folgen Sie der Definition of Done** (Wann ist es fertig?)
5. **Konsultieren Sie Gherkin Features** für konkrete Beispiele
6. **Implementieren Sie mit TDD** (RED-GREEN-REFACTOR)

### Für Product Owner / For Product Owners

1. **Validieren Sie den Business-Value**
2. **Prüfen Sie Akzeptanzkriterien** auf Vollständigkeit
3. **Bewerten Sie Risiken** und akzeptieren Sie Mitigationen
4. **Akzeptieren Sie basierend auf DoD**

### Für Tester / For Testers

1. **Nutzen Sie Akzeptanzkriterien** als Testfälle
2. **Referenzieren Sie Gherkin Features** für detaillierte Szenarien
3. **Dokumentieren Sie Abweichungen**

---

## Template

Neue User Stories sollten diesem Template folgen:

```markdown
# User Story: [Titel]

**ID**: US-XXX
**Titel**: [Kurzbeschreibung]
**Status**: In Arbeit
**Datum**: YYYY-MM-DD

---

## Story

Als [Rolle]
möchte ich [Funktion]
damit [Nutzen]

---

## Kontext

**Aktueller Zustand**:
- [Was ist jetzt der Fall?]

**Problem**:
- [Welches Problem besteht?]

**Lösung**:
- [Wie lösen wir es?]

---

## Akzeptanzkriterien

### 1. [Kriterium]
- **Given** [Vorbedingung]
- **When** [Aktion]
- **Then** [Erwartung]
- **And** [Weitere Erwartung]

---

## Definition of Done

- [ ] Tests geschrieben und bestanden
- [ ] Code formatiert (black) und gelintet (ruff)
- [ ] Dokumentation aktualisiert
- [ ] Gherkin Feature erstellt
- [ ] Code Review durchgeführt
- [ ] Deployment-Dokumentation aktualisiert

---

## Technische Details

[Implementierungsdetails]

---

## Risiken & Mitigationen

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| [Risiko] | [Niedrig/Mittel/Hoch] | [Niedrig/Mittel/Hoch] | [Mitigation] |

---

## Verwandte Spezifikationen

**User Stories**:
- [Related Story](US-XXX.md)

**Gherkin Features**:
- [Feature](../features/feature-name.feature)

---

## Änderungshistorie

| Datum | Version | Änderung |
|-------|---------|----------|
| YYYY-MM-DD | 1.0 | Initiale Erstellung |
```

---

## Verwandte Dokumentation / Related Documentation

- [Zurück zur Übersicht](../README.md)
- [Gherkin Features](../features/)
- [AGENTS.md](../../../AGENTS.md)
- [Implementierungspläne](../../../../.claude/plans/)

---

## Änderungshistorie / Change History

| Datum | Version | Änderung |
|-------|---------|----------|
| 2024-12-25 | 1.0 | Initiale Erstellung |
