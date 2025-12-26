# Event Summary Modal - E2E Tests

Comprehensive Playwright end-to-end tests for the Event Summary Modal feature (US-004).

## Test Coverage

### Test File: `test_event_summary_modal.py`

**Total Tests: 30**

#### 1. Basic Functionality (5 tests)
- ✅ Modal appears 500ms after successful conversion
- ✅ Modal contains all required UI elements (title, description, buttons)
- ✅ Modal displays conversion events with proper structure
- ✅ OK button receives initial focus
- ✅ Modal has correct open attribute

#### 2. Interaction Patterns (6 tests)
- ✅ OK button closes modal
- ✅ X (close) button closes modal
- ✅ Escape key closes modal
- ✅ Backdrop click closes modal
- ✅ Inline event list remains visible after modal closes
- ✅ Download button triggers file download

#### 3. Keyboard Navigation (4 tests)
- ✅ Tab key cycles through buttons (OK → Download → Close → OK)
- ✅ Shift+Tab navigates backwards
- ✅ Enter key on OK button closes modal
- ✅ Focus trap works correctly

#### 4. Accessibility (2 tests)
- ✅ Modal has required ARIA attributes (`aria-labelledby`)
- ✅ Event list has `role="list"` and items have `role="listitem"`
- ✅ Close button has `aria-label="Close modal"`

#### 5. Internationalization (4 tests)
- ✅ German (DE): "Konvertierungs-Zusammenfassung", "Herunterladen"
- ✅ Spanish (ES): "Resumen de Conversión", "Descargar"
- ✅ French (FR): "Résumé de Conversion", "Télécharger"
- ✅ English (EN): "Conversion Summary", "Download"

#### 6. Edge Cases (2 tests)
- ✅ Modal handles many events with scrollbar (`overflow-y: auto`)
- ✅ Modal is responsive on narrow viewports (mobile 375px)

#### 7. Dark Mode (2 tests)
- ✅ Dark mode applies correct styles (`#1f2937` background)
- ✅ Light mode applies correct styles (white background)

## Running the Tests

### Prerequisites

```bash
# Install dependencies
pip install -e ".[dev]"

# Install Playwright browsers (first time only)
playwright install
```

### Run All Modal Tests

```bash
# Run all event modal tests
pytest tests/e2e/test_event_summary_modal.py -v

# Run with headed browser (see tests execute)
pytest tests/e2e/test_event_summary_modal.py -v --headed

# Run specific test class
pytest tests/e2e/test_event_summary_modal.py::TestEventSummaryModalBasics -v

# Run specific test
pytest tests/e2e/test_event_summary_modal.py::TestEventSummaryModalBasics::test_modal_appears_after_conversion -v
```

### Run in Different Browsers

```bash
# Chromium (default)
pytest tests/e2e/test_event_summary_modal.py -v

# Firefox
pytest tests/e2e/test_event_summary_modal.py -v --browser firefox

# WebKit (Safari)
pytest tests/e2e/test_event_summary_modal.py -v --browser webkit
```

### Run with Debug Mode

```bash
# Slow down execution and pause on failure
pytest tests/e2e/test_event_summary_modal.py -v --headed --slowmo 500

# Debug mode with inspector
PWDEBUG=1 pytest tests/e2e/test_event_summary_modal.py::TestEventSummaryModalBasics::test_modal_appears_after_conversion
```

### Generate Test Report

```bash
# HTML report
pytest tests/e2e/test_event_summary_modal.py --html=report.html --self-contained-html

# Coverage report (if configured)
pytest tests/e2e/test_event_summary_modal.py --cov=pdfa --cov-report=html
```

## Test Structure

Each test follows this pattern:

```python
def test_feature_name(self, page_with_server: Page, test_pdfs: dict[str, Path]) -> None:
    """Test description."""
    page = page_with_server
    page.goto("http://localhost:8000/en")

    # 1. Upload file
    file_input = page.locator('input[type="file"]')
    file_input.set_input_files(test_pdfs["small"])

    # 2. Start conversion
    page.locator("#convertBtn").click()

    # 3. Wait for modal
    modal = page.locator("#eventSummaryModal")
    modal.wait_for(state="visible", timeout=35000)

    # 4. Test assertions
    expect(modal).to_be_visible()
    # ... more assertions
```

## Test Data

Tests use dynamically generated PDFs:
- **Small PDF**: 3 pages, generates ~2-5 events
- Test files are created in `tests/e2e/test_data/`
- Files are cached and reused across test runs

## Fixtures

### `page_with_server`
- Starts FastAPI server on `localhost:8000`
- Provides Playwright Page instance
- Automatically cleans up after tests

### `test_pdfs`
- Generates test PDF files
- Returns dictionary with file paths
- Cached at module scope for performance

## Debugging Failed Tests

### Screenshot on Failure

```bash
pytest tests/e2e/test_event_summary_modal.py --screenshot on
```

### Video Recording

```bash
pytest tests/e2e/test_event_summary_modal.py --video on
```

### Trace Viewer

```bash
# Run with tracing
pytest tests/e2e/test_event_summary_modal.py --tracing on

# Open trace viewer
playwright show-trace trace.zip
```

## Common Issues

### Issue: Modal doesn't appear
**Solution**: Increase timeout (conversion might take longer)
```python
modal.wait_for(state="visible", timeout=60000)  # 60 seconds
```

### Issue: Server already running
**Solution**: Stop existing server or use different port
```bash
pkill -f "uvicorn pdfa.api:app"
```

### Issue: Download test fails
**Solution**: Ensure download directory permissions
```bash
chmod 755 tests/e2e/test_data/
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Install Playwright
  run: playwright install --with-deps

- name: Run Modal E2E Tests
  run: |
    pytest tests/e2e/test_event_summary_modal.py \
      --browser chromium \
      --browser firefox \
      --video on \
      --screenshot on
```

## Performance

- **Average test duration**: 5-10 seconds per test
- **Total suite duration**: ~5 minutes (30 tests)
- **Server startup**: 2 seconds
- **PDF conversion**: 3-8 seconds

## Maintenance

### Adding New Tests

1. Create new test method in appropriate class
2. Follow naming convention: `test_<feature>_<scenario>`
3. Add docstring describing test purpose
4. Use existing fixtures (`page_with_server`, `test_pdfs`)
5. Update this README with new test count

### Test Organization

```
TestEventSummaryModalBasics          # Core functionality
TestEventSummaryModalInteractions    # User interactions
TestEventSummaryModalKeyboard        # Keyboard navigation
TestEventSummaryModalAccessibility   # ARIA, a11y
TestEventSummaryModalInternationalization  # i18n
TestEventSummaryModalEdgeCases       # Edge cases
TestEventSummaryModalDarkMode        # Theming
```

## Related Documentation

- **User Story**: `/docs/specs/user-stories/US-004-live-job-events.md`
- **Gherkin Specs**: `/docs/specs/features/gherkin-live-job-events.feature`
- **Implementation**: `/src/pdfa/web_ui.html` (lines 1038-1076, 649-851, 3329-3451)

## Contact

For questions or issues with these tests, see the main project README or AGENTS.md.
