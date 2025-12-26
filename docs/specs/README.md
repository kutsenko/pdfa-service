# Spezifikationen / Specifications

Dieses Verzeichnis enthält formale User Stories und Gherkin Feature-Dateien für wichtige Features des PDF/A-Service.

This directory contains formal User Stories and Gherkin Feature files for major features of the PDF/A service.

---

## Struktur / Structure

```
docs/specs/
├── README.md                                    # Diese Datei / This file
├── user-stories/                                # User Stories (INVEST)
│   ├── README.md                                # Übersicht User Stories
│   ├── US-001-mongodb-integration.md            # MongoDB-Integration
│   ├── US-002-job-event-logging.md              # Job Event Logging
│   └── US-003-local-default-user.md             # Lokaler Standardbenutzer
└── features/                                     # Gherkin Features (BDD)
    ├── README.md                                 # Übersicht Gherkin Features
    ├── gherkin-mongodb-integration.feature       # MongoDB (36 Szenarien)
    ├── gherkin-job-event-logging.feature         # Event Logging (21 Szenarien)
    └── gherkin-local-default-user.feature        # Lokaler Standardbenutzer (18 Szenarien)
```

---

## Übersicht / Overview

| ID | Titel | Status | Datum | User Story | Gherkin Feature |
|----|-------|--------|-------|------------|-----------------|
| US-001 | MongoDB-Integration | ✅ Implementiert | 2024-12-21 | [User Story](user-stories/US-001-mongodb-integration.md) | [Feature](features/gherkin-mongodb-integration.feature) (36 Szenarien) |
| US-002 | Job Event Logging | ✅ Implementiert | 2024-12-25 | [User Story](user-stories/US-002-job-event-logging.md) | [Feature](features/gherkin-job-event-logging.feature) (21 Szenarien) |
| US-003 | Lokaler Standardbenutzer | ✅ Implementiert | 2024-12-25 | [User Story](user-stories/US-003-local-default-user.md) | [Feature](features/gherkin-local-default-user.feature) (18 Szenarien) |

---

## User Stories

📁 **Verzeichnis**: [`user-stories/`](user-stories/)

User Stories folgen dem **INVEST**-Prinzip und enthalten:
- Story im "Als... möchte ich... damit..." Format
- Kontext und Problemstellung
- Akzeptanzkriterien
- Definition of Done
- Technische Details
- Risiken & Mitigationen

### [US-001: MongoDB-Integration](user-stories/US-001-mongodb-integration.md)

**Zusammenfassung**: Einführung einer persistenten MongoDB-Datenbankschicht für Conversion-History, OAuth State Tokens und Audit Logs.

**Hauptziele**:
- Jobs überleben Server-Neustarts
- OAuth funktioniert in Multi-Instance-Deployments
- Audit Logs für Compliance und Analytics

**Collections**:
- `users` - Minimale User-Profile
- `jobs` - Conversion-History (TTL: 90 Tage)
- `oauth_states` - CSRF Token Validation (TTL: 10 Minuten)
- `audit_logs` - Event-Protokollierung (TTL: 1 Jahr)

**Gherkin Feature**: [gherkin-mongodb-integration.feature](features/gherkin-mongodb-integration.feature) - 36 Szenarien

---

### [US-002: Job Event Logging](user-stories/US-002-job-event-logging.md)

**Zusammenfassung**: Detaillierte Event-Liste für jeden Konvertierungsauftrag, um Entscheidungen nachvollziehbar zu machen.

**Event-Typen**:
- `format_conversion` - Office/Image→PDF Konvertierung
- `ocr_decision` - OCR Skip/Perform mit Statistiken
- `compression_selected` - Kompressionsprofilwahl
- `passthrough_mode` - PDF-Durchreichung ohne OCRmyPDF
- `fallback_applied` - Fallback-Tier-Aktivierung
- `job_timeout` - Job-Timeout-Ereignis
- `job_cleanup` - Job-Cleanup-Ereignis

**Architektur**:
- Event-Callback-Pattern in converter.py
- Async Event-Logger-Helper
- MongoDB $push für atomare Updates
- Backward-kompatibel (default_factory)

**Gherkin Feature**: [gherkin-job-event-logging.feature](features/gherkin-job-event-logging.feature) - 21 Szenarien

---

### [US-003: Lokaler Standardbenutzer](user-stories/US-003-local-default-user.md)

**Zusammenfassung**: Automatische Erstellung eines lokalen Standardbenutzers wenn Authentifizierung deaktiviert ist.

**Hauptziele**:
- Job-Verlauf und persistente Features auch ohne OAuth
- Konfigurierbare Standardbenutzer-Felder
- Idempotente Multi-Instance-fähige Implementierung

**Kernfeatures**:
- `ensure_default_user()` - Erstellt User beim Startup
- `DEFAULT_USER_ID`, `DEFAULT_USER_EMAIL`, `DEFAULT_USER_NAME` - Umgebungsvariablen
- `get_current_user_optional()` - Gibt Default User statt None zurück
- Backward-kompatibel mit Auth-Modus

**Gherkin Feature**: [gherkin-local-default-user.feature](features/gherkin-local-default-user.feature) - 18 Szenarien

---

## Gherkin Features

📁 **Verzeichnis**: [`features/`](features/)

Gherkin-Features sind in **deutscher Sprache** verfasst (language: de) und folgen dem **Given-When-Then**-Pattern.

### [gherkin-mongodb-integration.feature](features/gherkin-mongodb-integration.feature)

**Szenario-Gruppen**:
1. Service-Start und MongoDB-Verbindung (3 Szenarien)
2. Job-Persistierung (6 Szenarien)
3. OAuth State Token Management (4 Szenarien)
4. User-Profile (3 Szenarien)
5. Audit Logs (5 Szenarien)
6. Indexes und Performance (3 Szenarien)
7. Repository-Pattern (4 Szenarien)
8. Error Handling (3 Szenarien)
9. Backward Compatibility (2 Szenarien)
10. Multi-Instance Deployment (3 Szenarien)

**Gesamt**: 36 Szenarien

**Zugehörige User Story**: [US-001: MongoDB-Integration](user-stories/US-001-mongodb-integration.md)

---

### [gherkin-job-event-logging.feature](features/gherkin-job-event-logging.feature)

**Szenario-Gruppen**:
1. OCR-Entscheidung (3 Szenarien)
2. Format-Konvertierung (3 Szenarien)
3. Fallback-Mechanismen (3 Szenarien)
4. Pass-through-Modus (2 Szenarien)
5. Kompressionsprofilwahl (2 Szenarien)
6. Job-Lifecycle-Events (2 Szenarien)
7. Rückwärtskompatibilität (2 Szenarien)
8. Vollständige Job-Lifecycle-Beispiele (2 Szenarien)
9. Error Handling (2 Szenarien)

**Gesamt**: 21 Szenarien

**Zugehörige User Story**: [US-002: Job Event Logging](user-stories/US-002-job-event-logging.md)

---

### [gherkin-local-default-user.feature](features/gherkin-local-default-user.feature)

**Szenario-Gruppen**:
1. Service-Start und Default User-Erstellung (3 Szenarien)
2. Konfigurierbare Standardbenutzer-Felder (2 Szenarien)
3. Job-Attribution mit Default User (3 Szenarien)
4. Job-Verlauf-Abfrage (3 Szenarien)
5. Dependency Injection (3 Szenarien)
6. Edge Cases und Error Handling (4 Szenarien)
7. Vollständige Integration-Workflows (2 Szenarien)

**Gesamt**: 18 Szenarien (inkl. Multi-Instance)

**Zugehörige User Story**: [US-003: Lokaler Standardbenutzer](user-stories/US-003-local-default-user.md)

---

## Verwendung / Usage

### Für Entwickler / For Developers

1. **Lesen Sie die User Story** um das "Warum" zu verstehen
   - 📄 Beginnen Sie in [`user-stories/`](user-stories/)
2. **Prüfen Sie die Akzeptanzkriterien** für Anforderungen
3. **Folgen Sie den Gherkin-Szenarien** für konkrete Beispiele
   - 🧪 Siehe [`features/`](features/)
4. **Implementieren Sie mit TDD** (RED-GREEN-REFACTOR)

### Für Tester / For Testers

1. **Nutzen Sie Gherkin-Szenarien** als Testfälle
   - 🧪 Alle Features in [`features/`](features/)
2. **Prüfen Sie alle Szenarien** gegen die Implementierung
3. **Erweitern Sie bei Bedarf** neue Edge Cases

### Für Product Owner / For Product Owners

1. **Validieren Sie Akzeptanzkriterien** in User Stories
   - 📄 Siehe [`user-stories/`](user-stories/)
2. **Prüfen Sie Definition of Done**
3. **Akzeptieren oder Ablehnen** basierend auf Erfüllung

---

## Standards

### User Story Format

**Template**:
```markdown
# User Story: [Titel]

**ID**: US-XXX
**Titel**: [Kurzbeschreibung]
**Status**: [In Arbeit / Implementiert / Abgelehnt]
**Datum**: YYYY-MM-DD

## Story
Als [Rolle]
möchte ich [Funktion]
damit [Nutzen]

## Kontext
[Hintergrund und Problemstellung]

## Akzeptanzkriterien
[Given-When-Then Kriterien]

## Definition of Done
- [ ] Checkliste

## Technische Details
[Implementierungsdetails]

## Verwandte Spezifikationen
**User Stories**: Links zu verwandten Stories
**Gherkin Features**: Links zu Gherkin Features
```

### Gherkin Format

**Template**:
```gherkin
# language: de
Funktionalität: [Titel]
  Als [Rolle]
  möchte ich [Ziel]
  damit [Nutzen]

  Hintergrund:
    Angenommen [Kontext]

  Szenario: [Beschreibung]
    Angenommen [Vorbedingung]
    Wenn [Aktion]
    Dann [Erwartetes Ergebnis]
```

---

## Statistiken

**User Stories**: 3
- US-001: MongoDB-Integration (6.1 KB)
- US-002: Job Event Logging (10 KB)
- US-003: Lokaler Standardbenutzer (14 KB)

**Gherkin Features**: 3
- MongoDB Integration (18 KB, 36 Szenarien)
- Job Event Logging (16 KB, 21 Szenarien)
- Lokaler Standardbenutzer (8 KB, 18 Szenarien)

**Gesamt**:
- 75 Gherkin-Szenarien
- ~72 KB Spezifikations-Content

**Abdeckung**:
- ✅ Alle implementierten Features dokumentiert
- ✅ Backward Compatibility berücksichtigt
- ✅ Error Handling spezifiziert
- ✅ Multi-Instance Scenarios (MongoDB)
- ✅ Performance-Aspekte dokumentiert

---

## Verwandte Dokumentation / Related Documentation

- [AGENTS.md](../../AGENTS.md) - Entwicklungsrichtlinien
- [README.md](../../README.md) - Benutzer-Dokumentation (Englisch)
- [README.de.md](../../README.de.md) - Benutzer-Dokumentation (Deutsch)
- [Plan-Dateien](../../../.claude/plans/) - Detaillierte Implementierungspläne

---

## Änderungshistorie / Change History

| Datum | Version | Änderung |
|-------|---------|----------|
| 2024-12-25 | 1.0 | Initiale Erstellung mit US-001 und US-002 |
| 2024-12-25 | 2.0 | Umstrukturierung: User Stories und Gherkin Features in separate Verzeichnisse |
| 2024-12-25 | 3.0 | US-003: Lokaler Standardbenutzer hinzugefügt (18 Szenarien) |
