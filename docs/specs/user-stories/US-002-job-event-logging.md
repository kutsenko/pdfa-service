# User Story: Job Event Logging

**ID**: US-002
**Titel**: Job-Ausführungsdetails als Event-Liste speichern
**Status**: ✅ Implementiert
**Datum**: 2024-12-25

---

## Story

**Als** Benutzer des PDF/A-Service
**möchte ich** eine detaillierte Event-Liste für jeden Konvertierungsauftrag im System gespeichert haben
**damit** ich die einzelnen Entscheidungen und Schritte der Konvertierung nachträglich nachvollziehen kann.

---

## Kontext

**Aktueller Zustand (vor Event Logging)**:
- Nur finaler Status wird gespeichert (queued, processing, completed, failed)
- Wichtige Zwischenentscheidungen gehen verloren:
  - Warum wurde OCR übersprungen/durchgeführt?
  - Welches Kompressionsprofi wurde verwendet?
  - Welche Fallback-Stufe wurde aktiviert?
  - Warum wurde Pass-through-Modus verwendet?
- WebSocket-Progress wird NUR live übertragen, NICHT gespeichert
- Cleanup-Events werden nur geloggt, nicht in DB gespeichert

**Problem**:
- Benutzer können nicht nachvollziehen, warum eine Konvertierung bestimmte Entscheidungen getroffen hat
- Debugging von Problemen ist schwierig ohne historische Daten
- Keine Transparenz über Service-Verhalten

**Lösung**:
- Event-basiertes Logging-System
- Alle relevanten Entscheidungspunkte werden als Events in MongoDB gespeichert
- Events sind strukturiert und maschinenlesbar
- Backward-kompatibel mit existierenden Jobs

---

## Akzeptanzkriterien

### 1. OCR-Entscheidung wird protokolliert
- **Given** ein PDF wird konvertiert
- **When** eine OCR-Entscheidung getroffen wird
- **Then** sollte ein `ocr_decision` Event gespeichert werden
- **And** sollte den Grund enthalten (tagged_pdf, has_text, no_text)
- **And** sollte Statistiken enthalten (pages_with_text, text_ratio, total_characters)

### 2. Format-Konvertierung wird protokolliert
- **Given** ein Office-Dokument oder Bild wird hochgeladen
- **When** die Format-Konvertierung stattfindet
- **Then** sollte ein `format_conversion` Event gespeichert werden
- **And** sollte Source-/Target-Format enthalten
- **And** sollte Konvertierungszeit enthalten
- **And** sollte Converter-Name enthalten (office_to_pdf, image_to_pdf)

### 3. Fallback-Tiers werden protokolliert
- **Given** OCRmyPDF schlägt mit Standard-Einstellungen fehl
- **When** ein Fallback-Tier aktiviert wird
- **Then** sollte ein `fallback_applied` Event gespeichert werden
- **And** sollte Tier-Nummer enthalten (2 oder 3)
- **And** sollte Original-Fehler enthalten
- **And** sollte Safe-Mode-Config enthalten
- **And** sollte PDF/A-Level-Downgrade enthalten (falls anwendbar)

### 4. Cleanup wird protokolliert
- **Given** ein alter Job wird aufgeräumt
- **When** der Cleanup-Prozess läuft
- **Then** sollte ein `job_cleanup` Event gespeichert werden
- **And** sollte Trigger enthalten (age_exceeded, timeout)
- **And** sollte TTL und Alter enthalten
- **And** sollte gelöschte Dateien auflisten
- **And** sollte Gesamtgröße der gelöschten Dateien enthalten

### 5. Pass-through-Modus wird protokolliert
- **Given** pdfa_level="pdf" und ocr_enabled=False
- **When** der Intermediate-PDF direkt zurückgegeben wird
- **Then** sollte ein `passthrough_mode` Event gespeichert werden
- **And** sollte Grund enthalten (pdf_output_no_ocr)
- **And** sollte Tag-Status enthalten (has_tags, tags_preserved)

### 6. Kompressionsprofilwahl wird protokolliert
- **Given** ein Kompressionsprofi wird ausgewählt
- **When** die Konvertierung startet
- **Then** sollte ein `compression_selected` Event gespeichert werden
- **And** sollte Profil-Name enthalten (quality, balanced, preserve)
- **And** sollte Auswahlgrund enthalten (user_selected, auto_switched_for_tagged_pdf)
- **And** sollte Original-Profil enthalten (bei Auto-Switch)
- **And** sollte Einstellungen enthalten (image_dpi, remove_vectors, etc.)

---

## Definition of Done

- [x] Alle Event-Typen werden in `JobDocument.events` gespeichert
- [x] Events sind über MongoDB-API abrufbar (GET /jobs/{job_id})
- [x] Alle Unit-Tests bestehen (pytest)
- [x] Integration-Tests mit vollständigem Job-Lifecycle
- [x] Code ist formatiert (black) und gelintet (ruff)
- [x] Rückwärtskompatibilität: Alte Jobs ohne events-Feld funktionieren
- [x] Dokumentation in AGENTS.md
- [x] TDD-Ansatz befolgt (Tests vor Code)

---

## Technische Details

### Datenmodell

**JobEvent** (Pydantic Model):
```python
class JobEvent(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: Literal[
        "format_conversion",
        "ocr_decision",
        "compression_selected",
        "passthrough_mode",
        "fallback_applied",
        "job_timeout",
        "job_cleanup",
    ]
    message: str  # Human-readable description
    details: dict[str, Any]  # Structured event data
```

**JobDocument** (erweitert):
```python
class JobDocument(BaseModel):
    # ... existing fields ...
    events: list[JobEvent] = Field(default_factory=list)  # NEW
```

### Event-Typen und Details

**1. format_conversion**
```python
{
    "source_format": "docx",
    "target_format": "pdf",
    "conversion_required": true,
    "converter": "office_to_pdf",
    "conversion_time_seconds": 3.2
}
```

**2. ocr_decision**
```python
{
    "decision": "skip",  # or "perform"
    "reason": "has_text",  # or "tagged_pdf", "no_text"
    "pages_with_text": 3,
    "total_pages_checked": 3,
    "text_ratio": 1.0,
    "total_characters": 1523
}
```

**3. compression_selected**
```python
{
    "profile": "preserve",
    "reason": "auto_switched_for_tagged_pdf",
    "original_profile": "balanced",
    "settings": {
        "image_dpi": 300,
        "remove_vectors": false
    }
}
```

**4. passthrough_mode**
```python
{
    "enabled": true,
    "reason": "pdf_output_no_ocr",
    "pdfa_level": "pdf",
    "ocr_enabled": false,
    "has_tags": true,
    "tags_preserved": true
}
```

**5. fallback_applied**
```python
{
    "tier": 2,
    "reason": "ghostscript_error",
    "original_error": "SubprocessOutputError: ...",
    "safe_mode_config": {
        "image_dpi": 100,
        "optimize": 0
    },
    "pdfa_level_downgrade": {
        "original": "3",
        "fallback": "2"
    }
}
```

**6. job_timeout**
```python
{
    "timeout_seconds": 7200,
    "runtime_seconds": 7305,
    "job_cancelled": true
}
```

**7. job_cleanup**
```python
{
    "trigger": "age_exceeded",  # or "timeout"
    "ttl_seconds": 3600,
    "age_seconds": 3720,
    "files_deleted": {
        "input_file": "/tmp/input.pdf",
        "output_file": "/tmp/output.pdf",
        "temp_directory": "/tmp/job-123"
    },
    "total_size_bytes": 2048576
}
```

### Architektur

**Event Flow**:
```
API Request → process_conversion_job()
    ↓
event_callback() created (async)
    ↓
converter.convert_to_pdfa(event_callback=event_callback)
    ↓
log_event() helper → event_callback() → event_logger.log_*_event()
    ↓
JobRepository.add_job_event() → MongoDB $push
```

**Implementierte Komponenten**:
- `src/pdfa/event_logger.py` - 7 async helper functions
- `src/pdfa/converter.py` - log_event() helper + event logging
- `src/pdfa/api.py` - event_callback() creation
- `src/pdfa/job_manager.py` - cleanup/timeout event logging
- `src/pdfa/models.py` - JobEvent + JobDocument.events
- `src/pdfa/repositories.py` - add_job_event() method

### Event Callback Pattern

Der `event_callback` Parameter ist optional in `convert_to_pdfa()`. Wenn vorhanden, empfängt er Events aus dem Sync-Kontext und plant sie asynchron ein:

```python
def log_event(event_type: str, **kwargs: Any) -> None:
    """Log event if callback is provided."""
    if event_callback:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(event_callback(event_type, **kwargs))
        except RuntimeError:
            asyncio.run(event_callback(event_type, **kwargs))
```

### Backward Compatibility

**Pydantic default_factory Pattern**:
```python
events: list[JobEvent] = Field(default_factory=list)
```

- Alte Jobs ohne `events` Feld: MongoDB liefert dict ohne "events" key
- Pydantic verwendet `default_factory=list`
- Resultat: `job.events == []`
- **Keine Migration erforderlich!**

---

## TDD Implementation Phasen

### Phase 1: Models & Repository ✅
- JobEvent model
- JobDocument.events field
- JobRepository.add_job_event()
- Tests: test_models.py, test_repositories.py

### Phase 2: Event Logging Helpers ✅
- 7 async event_logger functions
- Tests: test_event_logger.py (13 tests)

### Phase 3: Converter Integration ✅
- needs_ocr() refactoring (tuple → dict)
- event_callback parameter
- 5 event logging points
- Tests: test_converter_events.py (8 tests)

### Phase 4: API Integration ✅
- event_callback in process_conversion_job
- format_conversion events
- job_manager cleanup/timeout events

### Phase 5: Testing & Polish ✅
- All tests passing
- Code formatted & linted
- AGENTS.md updated

---

## Performance Überlegungen

**Event Logging ist nicht blockierend**:
- Async, fire-and-forget mit error handling
- Conversion läuft weiter bei Event-Fehler
- Timeout-Schutz bei MongoDB-Operationen

**MongoDB Document Size**:
- Realistische Jobs: 5-10 events × 500 bytes = 5KB
- Worst case (100 events): 50KB
- MongoDB Limit: 16MB → kein Problem

**Write Performance**:
- `$push` ist atomic und effizient
- <10ms pro Event (lokal)
- <50ms (remote MongoDB)

---

## Risiken & Mitigationen

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Event logging verlangsamt Conversion | Niedrig | Mittel | Async, timeout, best-effort |
| MongoDB document size limit | Sehr niedrig | Hoch | Events klein halten, TTL cleanup |
| Backward compatibility Probleme | Niedrig | Mittel | Pydantic default_factory, Tests |
| Test coverage unzureichend | Niedrig | Hoch | TDD strikt befolgen, >90% target |

---

## Verwandte Spezifikationen

**User Stories**:
- [US-001: MongoDB Integration](US-001-mongodb-integration.md) - Grundlage für Event Storage

**Gherkin Features**:
- [Job Event Logging](../features/gherkin-job-event-logging.feature) - 21 detaillierte Szenarien

---

## Änderungshistorie

| Datum | Version | Änderung |
|-------|---------|----------|
| 2024-12-25 | 1.0 | Initiale Implementierung (Phase 1-5) |
| 2024-12-25 | 1.1 | Umstrukturierung: User Stories und Gherkin Features getrennt |
