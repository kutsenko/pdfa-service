# Architecture Documentation

**Technical Architecture and Design Patterns for pdfa-service**

This document contains all architectural guidelines, design patterns, and implementation details for the pdfa-service project.

For general development guidelines, see [AGENTS.md](AGENTS.md).

---

## Table of Contents

1. [Project Architecture](#project-architecture)
2. [File Reference](#file-reference)
3. [Error Handling Architecture](#error-handling-architecture)
4. [Performance Considerations](#performance-considerations)

---

## Project Architecture

### Dual Interface Design Principle

Both CLI and REST API must use the **same conversion function** (`convert_to_pdfa()`) to ensure feature parity and prevent divergence. This is the key architectural principle.

```
Input (CLI args / HTTP request)
    ↓
Validation & Parsing (cli.py / api.py)
    ↓
Shared Conversion Logic (converter.py)
    ↓
OCRmyPDF Library
    ↓
Output (Exit code / HTTP response)
```

### Error Handling Pattern

Both interfaces must translate low-level errors consistently:
- **File not found**: CLI returns exit code 1, API returns HTTP 400
- **OCRmyPDF failures**: CLI propagates exit code, API returns HTTP 500
- Shared logic in `converter.py` raises exceptions; interfaces handle translation

### Configuration Distribution

- Configuration (language, PDF/A level) is passed as **function arguments**, not environment variables
- This enables per-request configuration in API, easier testing, and avoids global state
- Example: `convert_to_pdfa(input_path, output_path, language="eng+deu", pdfa_level="2")`

### Dependency Abstraction

- OCRmyPDF is imported at module level (mockable in tests)
- Provide simple wrapper around `ocrmypdf.ocr()` for maintainability
- API responses include proper headers: `Content-Type: application/pdf`, `Content-Disposition: attachment`

### Temporary File Handling

- REST endpoint uses `TemporaryDirectory()` context manager for uploaded files
- Ensures cleanup even on errors
- Supports clean streaming semantics

### Office Document and Image Support

- Office/OpenDocument files (DOCX, PPTX, XLSX, ODT, ODS, ODP) are automatically detected
- Image files (JPG, PNG, TIFF, BMP, GIF) are automatically detected
- Office/ODF conversion to PDF happens via LibreOffice (CLI subprocess, no Python fallbacks)
- Image conversion to PDF happens via img2pdf library
- Format detection uses file extension in `format_converter.py` and `image_converter.py`
- Custom exceptions: `OfficeConversionError`, `UnsupportedFormatError`

### Job Event Logging System

The service includes a comprehensive event logging system that tracks all conversion decisions and milestones in MongoDB for post-execution analysis.

#### Event Types

All events are stored in `JobDocument.events` as a list of `JobEvent` objects:

- **format_conversion**: Tracks Office/Image→PDF conversions with timing
- **ocr_decision**: Logs OCR skip/perform decisions with statistics (tagged_pdf, has_text, no_text)
- **compression_selected**: Records compression profile selection and auto-switches
- **passthrough_mode**: Documents when PDFs bypass OCRmyPDF (PDF output + no OCR)
- **fallback_applied**: Captures fallback tier activations (Tier 2/3) with error details
- **job_timeout**: Logs job timeouts with runtime information
- **job_cleanup**: Records cleanup events (age_exceeded, timeout) with file details

#### Architecture

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

#### Key Components

- `src/pdfa/event_logger.py`: 7 async helper functions for logging events
- `src/pdfa/converter.py`: `log_event()` helper + event logging at decision points
- `src/pdfa/api.py`: `event_callback()` creation in `process_conversion_job()`
- `src/pdfa/job_manager.py`: Cleanup/timeout event logging
- `src/pdfa/models.py`: `JobEvent` and `JobDocument.events` field
- `src/pdfa/repositories.py`: `add_job_event()` method using MongoDB `$push`

#### Event Callback Pattern

The `event_callback` parameter is optional in `convert_to_pdfa()`. When provided, it receives events from the sync conversion context and schedules them asynchronously:

```python
def log_event(event_type: str, **kwargs: Any) -> None:
    if event_callback:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(event_callback(event_type, **kwargs))
        except RuntimeError:
            asyncio.run(event_callback(event_type, **kwargs))
```

#### Example Event Flow

For a tagged PDF without OCR:
1. `format_conversion` - No conversion (PDF→PDF)
2. `passthrough_mode` - Enabled (pdf_output_no_ocr, tags_preserved=True)
3. `ocr_decision` - Skip (reason=tagged_pdf, has_struct_tree_root=True)

For a scanned PDF with fallback:
1. `format_conversion` - No conversion (PDF→PDF)
2. `ocr_decision` - Perform (reason=no_text, pages_with_text=0, text_ratio=0.0)
3. `fallback_applied` - Tier 2 (ghostscript_error, safe_mode_config, pdfa_level_downgrade)

#### Backward Compatibility

Jobs created before the event system was implemented work seamlessly:
- `events` field defaults to `[]` via `Field(default_factory=list)`
- No database migration required
- Old jobs simply have empty events list

#### WebSocket Event Broadcasting (US-004)

**Feature**: Live event display in web UI with real-time WebSocket broadcasting

All 7 event logging functions in `event_logger.py` broadcast events to connected WebSocket clients immediately after MongoDB persistence:

```python
async def log_ocr_decision_event(job_id: str, decision: str, reason: str, **kwargs):
    # 1. Create JobEvent
    event = JobEvent(...)

    # 2. Persist to MongoDB
    await repo.add_job_event(job_id, event)

    # 3. Broadcast via WebSocket (NEW)
    try:
        job_manager = get_job_manager()
        ws_message = JobEventMessage(
            job_id=job_id,
            event_type=event.event_type,
            timestamp=event.timestamp.isoformat(),
            message=event.message,  # English fallback
            details={
                **event.details,
                "_i18n_key": f"{event.event_type}.{decision}.{reason}",
                "_i18n_params": {"decision": decision, "reason": reason}
            }
        )

        # Best-effort async broadcast with timeout protection
        await asyncio.wait_for(
            job_manager.broadcast_to_job(job_id, ws_message.to_dict()),
            timeout=5.0
        )
    except Exception as e:
        logger.warning(f"Event broadcast failed: {e}")
        # MongoDB persistence already completed - continue
```

**WebSocket Protocol Extension**:

New server-to-client message type: `job_event`

```json
{
  "type": "job_event",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "ocr_decision",
  "timestamp": "2025-12-25T10:30:15.123Z",
  "message": "OCR skipped: tagged PDF detected",
  "details": {
    "decision": "skip",
    "reason": "tagged_pdf",
    "_i18n_key": "ocr_decision.skip.tagged_pdf",
    "_i18n_params": {"decision": "skip", "reason": "tagged_pdf"}
  }
}
```

**Key Properties**:

- **Best-Effort**: Broadcast failures don't block MongoDB persistence
- **Timeout Protection**: 5-second timeout prevents blocking on slow connections
- **Localization**: `_i18n_key` and `_i18n_params` enable frontend translation
- **Fallback**: English `message` always included for missing translations
- **Backward Compatible**: Old WebSocket clients ignore unknown `job_event` type

**Frontend Integration** (web_ui.html):

- Events displayed as expandable list below progress bar
- 4-language support (EN, DE, ES, FR) with parameter substitution
- Color-coded event types with emoji icons
- Screen reader announcements for high-priority events (3 of 7 types)
- ARIA accessibility attributes (role="log", aria-live="polite")
- Dark mode and reduced motion support

**Files Modified**:

- `src/pdfa/websocket_protocol.py`: Added `JobEventMessage` dataclass
- `src/pdfa/event_logger.py`: Added broadcasting to all 7 event functions
- `src/pdfa/web_ui.html`: UI components, CSS, i18n, JavaScript event handlers
- `tests/test_websocket_protocol.py`: Unit tests for JobEventMessage

**Performance**: ~350ms total overhead per job (7 events × 50ms), negligible compared to 10-60s conversion time

---

## File Reference

| File | Purpose |
|------|---------|
| `src/pdfa/converter.py` | Core conversion logic; single source of truth for OCRmyPDF integration; event logging |
| `src/pdfa/cli.py` | CLI with argparse; entry point is `main(argv)` |
| `src/pdfa/api.py` | FastAPI app; endpoint is `POST /convert`; job event callback integration |
| `src/pdfa/event_logger.py` | Job event logging helpers for MongoDB persistence; WebSocket broadcasting |
| `src/pdfa/websocket_protocol.py` | WebSocket message protocol schemas; JobEventMessage for live events |
| `src/pdfa/job_manager.py` | In-memory job management; cleanup/timeout event logging |
| `src/pdfa/models.py` | Pydantic models including JobDocument with events field |
| `src/pdfa/repositories.py` | MongoDB repositories including add_job_event() method |
| `src/pdfa/format_converter.py` | Office/ODF document format detection and LibreOffice conversion |
| `src/pdfa/image_converter.py` | Image format detection and img2pdf conversion |
| `src/pdfa/exceptions.py` | Custom exception definitions |
| `src/pdfa/logging_config.py` | Logging configuration and setup |
| `src/pdfa/__init__.py` | Package metadata (version) |
| `tests/conftest.py` | Pytest fixtures, OCRmyPDF mocking |
| `tests/test_cli.py` | CLI unit tests |
| `tests/test_api.py` | API endpoint unit tests |
| `tests/test_event_logger.py` | Event logger helper function tests |
| `tests/test_websocket_protocol.py` | WebSocket protocol message schema tests; JobEventMessage validation |
| `tests/test_converter_events.py` | Converter event logging integration tests |
| `tests/test_format_converter.py` | Format detection and Office conversion tests |
| `tests/test_image_converter.py` | Image format detection and conversion tests |
| `tests/test_cli_office.py` | CLI Office document handling tests |
| `tests/test_api_office.py` | API Office document handling tests |
| `tests/integration/test_conversion.py` | End-to-end PDF conversion integration tests |
| `tests/integration/test_office_conversion.py` | End-to-end Office conversion integration tests |
| `pyproject.toml` | Project metadata, dependencies, tool configs |

---

## Error Handling Architecture

### Architectural Notes for Future Development

#### Single Conversion Function

The design principle of a single `convert_to_pdfa()` function is intentional:
- Both CLI and API must call the same function to stay in sync
- Changes to conversion logic automatically apply to both interfaces
- Prevents feature divergence between CLI and API

#### Error Handling

When adding new OCRmyPDF exception handling:
- Exceptions should be caught and translated in both CLI and API interfaces
- Maintain consistency: same error should produce same exit code/HTTP status
- Document error mappings in code comments

**Handled OCRmyPDF Exceptions:**

1. **`SubprocessOutputError`** (Ghostscript rendering failures)
   - **Cause**: Ghostscript cannot render the PDF during OCR processing
   - **Symptoms**: Errors like "/undefined in --runpdf--" or "Ghostscript rasterizing failed"
   - **Three-Tier Fallback Strategy**:
     1. **Tier 1**: Normal conversion with user-specified settings
     2. **Tier 2**: Safe-mode OCR with Ghostscript-friendly parameters:
        - Low DPI (100 instead of 150+)
        - Preserve vectors (no rasterization)
        - High JPEG quality (95)
        - No optimization (avoid extra processing)
        - Disable JBIG2 compression
        - Downgrade PDF/A level (3→2, 2→1) for better compatibility
     3. **Tier 3**: Conversion without OCR as last resort
   - **Rationale**: Some PDFs contain features that Ghostscript struggles with (complex graphics, certain compression types, problematic font embeddings, memory-intensive rendering). Using conservative parameters makes Ghostscript more likely to succeed while still preserving OCR capability.
   - **Tests**:
     - `tests/test_converter_errors.py::test_ghostscript_safe_mode_fallback_succeeds`
     - `tests/test_converter_errors.py::test_ghostscript_three_tier_fallback`
     - `tests/test_converter_errors.py::test_ghostscript_pdfa_level_downgrade`

2. **`EncryptedPdfError`**
   - **Cause**: PDF has password protection or encryption
   - **Action**: Fail immediately with clear error message
   - **Error Message**: "Cannot process encrypted PDF. Please remove encryption first."
   - **Tests**: `tests/test_converter_errors.py::test_encrypted_pdf_error`

3. **`InputFileError`**
   - **Cause**: PDF is corrupted or invalid
   - **Action**: Fail with descriptive error
   - **Error Message**: "Invalid or corrupted PDF file: {details}"
   - **Tests**: `tests/test_converter_errors.py::test_invalid_pdf_error`

4. **`PriorOcrFoundError`**
   - **Cause**: PDF already has an OCR text layer
   - **Action**: Log and continue (not an error condition)
   - **Tests**: `tests/test_converter_errors.py::test_prior_ocr_found_is_handled_gracefully`

**Fallback Decision Tree:**
```
PDF Conversion Attempt (Tier 1: Normal settings)
├─ Success → Done
├─ SubprocessOutputError (Ghostscript fails)
│  ├─ If OCR was enabled
│  │  ├─ TIER 2: Retry with safe-mode OCR
│  │  │  ├─ Parameters: Low DPI (100), preserve vectors, no optimization
│  │  │  ├─ PDF/A level: Downgrade if possible (3→2, 2→1)
│  │  │  ├─ Success → Done (logged as safe-mode fallback)
│  │  │  └─ SubprocessOutputError (safe-mode fails)
│  │  │     ├─ TIER 3: Retry without OCR (keep safe-mode compression)
│  │  │     │  ├─ Success → Done (logged as final fallback)
│  │  │     │  └─ Failure → Error: "All fallback strategies exhausted"
│  └─ If OCR was disabled → Error: "Ghostscript could not render the PDF"
├─ EncryptedPdfError → Error: "Cannot process encrypted PDF"
├─ InputFileError → Error: "Invalid or corrupted PDF file"
├─ PriorOcrFoundError → Log and continue
└─ Other exceptions → Re-raise with logging
```

#### Configuration

New configuration parameters must be:
- Passed as function arguments, not globals or environment variables
- Type-hinted with appropriate types (Literal, str, int, etc.)
- Documented in docstrings and AGENTS.md file
- Tested with multiple values

---

## Performance Considerations

### Processing Times (Reference)

Typical OCR processing times per page:

| Hardware | Language | Time |
|----------|----------|------|
| Raspberry Pi 4 (ARM64) | English | 30-60s |
| Raspberry Pi 4 (ARM64) | English + German | 45-90s |
| Modern x86_64 CPU | English | 5-10s |
| Modern x86_64 CPU | English + German | 8-15s |

### Optimization Guidelines

- When modifying OCRmyPDF integration, consider impact on slow hardware
- Use resource limits appropriately (especially for Raspberry Pi)
- Profile before optimizing; only optimize hot paths
- Document performance implications in commit messages

---

## References

- [OCRmyPDF Documentation](https://ocrmypdf.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Best Practices](https://www.mongodb.com/docs/manual/administration/production-notes/)
- [WebSocket Protocol](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)

---

## Summary

This document describes the technical architecture of pdfa-service:

### Key Architectural Principles

1. **Dual Interface with Shared Core**
   - CLI and API both use `convert_to_pdfa()`
   - Ensures feature parity and prevents divergence

2. **Event-Driven Architecture**
   - Comprehensive event logging to MongoDB
   - Real-time WebSocket broadcasting
   - Post-execution analysis capabilities

3. **Robust Error Handling**
   - Three-tier fallback strategy for Ghostscript failures
   - Consistent error translation across interfaces
   - Graceful degradation when possible

4. **Performance Optimization**
   - Event callback pattern for async processing
   - Lazy-loading of events in job lists
   - Temporary file cleanup with context managers

### For Developers

- **Architecture decisions**: Follow the patterns described here
- **New features**: Maintain dual-interface design
- **Error handling**: Use established fallback patterns
- **Performance**: Consider slow hardware (Raspberry Pi)

See [AGENTS.md](AGENTS.md) for development workflow and testing standards.
