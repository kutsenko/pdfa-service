# Definition of Done (DoD)

**Version:** 1.0
**Datum:** 2025-12-27
**Projekt:** pdfa-service

---

## Übersicht

Dieses Dokument definiert die Kriterien, die erfüllt sein müssen, damit ein Feature, eine User Story oder ein Bug Fix als "fertig" (Done) gilt. Alle Teammitglieder und AI-Agenten müssen diese Kriterien vor dem Abschluss einer Aufgabe erfüllen.

---

## 1. Dokumentation

### 1.1 User Story / Feature Specification
- [ ] **User Story erstellt** (für neue Features)
  - Format: `docs/specs/user-stories/US-XXX-feature-name.md`
  - Enthält: Business Value, Acceptance Criteria, Technical Implementation
  - Status: Von "🚧 In Progress" zu "✅ Implemented" aktualisiert

- [ ] **Gherkin Feature Spec erstellt** (für neue Features)
  - Format: `docs/specs/features/gherkin-feature-name.feature`
  - Deckt alle Acceptance Criteria ab
  - Szenarien für Happy Path, Edge Cases, Error Handling

### 1.2 Code-Dokumentation
- [ ] **Docstrings vollständig**
  - Alle öffentlichen Funktionen, Klassen, Module dokumentiert
  - Args, Returns, Raises Sections vorhanden
  - Beispiele für komplexe Funktionen

- [ ] **README.md aktualisiert** (bei Behavior-Änderungen)
  - Neue Features dokumentiert
  - API-Änderungen beschrieben
  - Beispiele aktualisiert

- [ ] **AGENTS.md aktualisiert** (bei neuen Patterns/Practices)
  - Neue Entwicklungspatterns dokumentiert
  - Architekturentscheidungen festgehalten

---

## 2. Code-Qualität

### 2.1 Code-Standards
- [ ] **Code formatiert mit Black**
  ```bash
  black src tests
  ```
  - Keine Formatter-Warnungen

- [ ] **Linting mit Ruff bestanden**
  ```bash
  ruff check src tests
  ```
  - Keine Fehler (Warnungen D203/D213 sind akzeptabel)
  - Alle Auto-Fixes angewendet

- [ ] **Type Hints vorhanden**
  - Alle Funktionsparameter typisiert
  - Return-Types definiert
  - Python 3.11+ Type-Hints verwendet

### 2.2 Code Review
- [ ] **Selbst-Review durchgeführt**
  - Code auf Lesbarkeit geprüft
  - Keine offensichtlichen Bugs
  - Keine auskommentierter Code
  - Keine Debug-Statements (console.log, print)

- [ ] **SOLID-Prinzipien befolgt**
  - Single Responsibility
  - Open/Closed
  - Liskov Substitution
  - Interface Segregation
  - Dependency Inversion

- [ ] **DRY-Prinzip befolgt**
  - Keine Code-Duplikation
  - Shared Logic in `converter.py` (nicht in CLI und API dupliziert)

---

## 3. Testing

### 3.1 Test Coverage
- [ ] **Minimum 90% Code Coverage**
  ```bash
  pytest --cov=src --cov-report=term-missing
  ```
  - Coverage-Report generiert
  - Kritische Pfade zu 100% abgedeckt
  - Nur triviale Getter/Setter ausgenommen

### 3.2 Unit Tests
- [ ] **Aussagekräftige Unit Tests vorhanden**
  - Jede neue Funktion/Klasse hat Tests
  - Tests folgen AAA-Pattern (Arrange, Act, Assert)
  - Edge Cases getestet
  - Error Handling getestet
  - Mocking für externe Abhängigkeiten (OCRmyPDF, MongoDB)

- [ ] **Test-Namenskonvention eingehalten**
  - Format: `test_should_<expected_behavior>_when_<condition>`
  - Beispiel: `test_should_return_404_when_user_not_found`

### 3.3 Integration Tests
- [ ] **Aussagekräftige Integration Tests vorhanden**
  - API-Endpoints end-to-end getestet
  - Datenbankinteraktionen getestet
  - Authentifizierungs-Flows getestet

### 3.4 E2E Tests (UI Features)
- [ ] **Playwright E2E Tests basierend auf Acceptance Criteria**
  - Jedes Acceptance Criteria hat mindestens einen E2E Test
  - Tests in `tests/e2e/test_<feature>.py`
  - Test-Klassen nach Feature-Bereichen strukturiert
  - Mindestens 90% der E2E Tests bestehen

- [ ] **E2E Test Coverage**
  - Happy Path: Vollständig getestet
  - Error Cases: Kritische Fehler getestet
  - i18n: Alle unterstützten Sprachen getestet (EN, DE, ES, FR)
  - Responsive Design: Desktop, Tablet, Mobile getestet
  - Dark Mode: Getestet (falls relevant)

### 3.5 Test Execution
- [ ] **Alle Tests lokal bestanden**
  ```bash
  pytest -v
  ```
  - Unit Tests: 100% bestanden
  - Integration Tests: 100% bestanden
  - E2E Tests (Playwright): ≥90% bestanden

- [ ] **Tests mit docker-compose bestanden**
  ```bash
  docker compose -f docker-compose.test.yml up --abort-on-container-exit
  ```
  - Alle Services starten erfolgreich
  - Alle Tests in isolierter Umgebung bestanden
  - Keine Flaky Tests

- [ ] **GitHub Actions CI/CD bestanden**
  - `test` Job: ✅ Passed
  - `security` Job: ✅ Passed
  - Keine Regressionen in bestehenden Tests

---

## 4. Funktionalität

### 4.1 Feature Completeness
- [ ] **Alle Acceptance Criteria erfüllt**
  - Jedes Kriterium aus der User Story implementiert
  - Keine TODOs oder Platzhalter im Code
  - Keine geplanten Features zurückgestellt

### 4.2 Error Handling
- [ ] **Robuste Fehlerbehandlung implementiert**
  - Alle erwarteten Fehler abgefangen
  - Benutzerfreundliche Fehlermeldungen
  - Logging für Debugging vorhanden
  - Keine unbehandelten Exceptions

### 4.3 Performance
- [ ] **Performance-Anforderungen erfüllt**
  - API-Responses < 2s (ohne Conversion)
  - UI responsiv (< 100ms für Interaktionen)
  - Keine Memory Leaks
  - Keine N+1 Query Probleme

---

## 5. Sicherheit

### 5.1 Security Checks
- [ ] **Keine bekannten Sicherheitslücken**
  - OWASP Top 10 beachtet
  - Keine SQL Injection, XSS, CSRF Risiken
  - Secrets nicht im Code
  - Input-Validierung implementiert

- [ ] **Security Scan bestanden**
  - Bandit (Python Security Linter)
  - Dependabot Alerts gelöst
  - Keine Critical/High Vulnerabilities

### 5.2 Authentication & Authorization
- [ ] **Auth korrekt implementiert** (falls relevant)
  - JWT-Tokens sicher gespeichert
  - CSRF-Protection vorhanden
  - IP-Tracking mit X-Forwarded-For
  - Session-Handling sicher

---

## 6. Internationalization (i18n)

### 6.1 Multi-Language Support
- [ ] **Alle Sprachen vollständig**
  - Englisch (EN): ✅
  - Deutsch (DE): ✅
  - Spanisch (ES): ✅
  - Französisch (FR): ✅

- [ ] **i18n Keys konsistent**
  - Namenskonvention: `<bereich>.<element>`
  - Beispiel: `konto.accountInfo`, `form.pdfType`
  - Keine Hardcoded Strings im UI

- [ ] **i18n Tests bestanden**
  - Jede Sprache hat E2E Tests
  - Keine fehlenden Übersetzungen
  - Platzhalter korrekt ersetzt

---

## 7. UI/UX (Frontend Features)

### 7.1 Design
- [ ] **Responsive Design implementiert**
  - Desktop (>1200px): ✅
  - Tablet (768px - 1199px): ✅
  - Mobile (< 768px): ✅
  - Keine horizontalen Scrollbars (außer bei absichtlich scrollbaren Containern)

- [ ] **Dark Mode Support** (falls relevant)
  - Alle Komponenten im Dark Mode getestet
  - Kontrast-Ratios WCAG-konform
  - Keine unlesbaren Texte

### 7.2 Accessibility (a11y)

**WCAG 2.1 Level AA Compliance erforderlich**

- [ ] **ARIA-Labels und Semantik**
  - Alle interaktiven Elemente haben aussagekräftige Labels
  - Buttons, Links, Inputs haben `aria-label` oder sichtbaren Text
  - `role`-Attribute korrekt gesetzt (button, navigation, dialog, etc.)
  - `aria-describedby` für zusätzliche Kontext-Informationen
  - `aria-live` für dynamische Inhalte (Loading-States, Fehler)
  - `aria-expanded`, `aria-controls` für Accordion/Dropdown-Elemente
  - `aria-invalid` und `aria-errormessage` für Formularvalidierung

- [ ] **Semantic HTML verwendet**
  - Korrekte HTML5-Elemente (`<nav>`, `<main>`, `<section>`, `<article>`, `<aside>`)
  - Heading-Hierarchie korrekt (h1 → h2 → h3, keine Ebenen überspringen)
  - `<button>` für Aktionen, `<a>` für Navigation
  - `<form>` mit `<label>` für alle Eingabefelder
  - Listen verwenden `<ul>`, `<ol>`, `<dl>` (nicht div-Pseudo-Listen)

- [ ] **Keyboard-Navigation**
  - Alle Funktionen per Tastatur erreichbar (keine Maus erforderlich)
  - Tab-Reihenfolge logisch (`tabindex` richtig gesetzt)
  - `Enter` und `Space` lösen Button-Aktionen aus
  - `Escape` schließt Modals/Dialoge
  - Fokus-Indikator sichtbar (`:focus-visible` Styles)
  - Fokus-Falle in Modals (Focus Trap implementiert)
  - Skip-Links für Hauptinhalt vorhanden

- [ ] **Farbkontrast (WCAG AA)**
  - Text-zu-Hintergrund Kontrast ≥ 4.5:1 (normaler Text)
  - Text-zu-Hintergrund Kontrast ≥ 3:1 (großer Text ≥18pt)
  - UI-Komponenten Kontrast ≥ 3:1 (Icons, Buttons)
  - Fokus-Indikator Kontrast ≥ 3:1
  - Keine Informationen nur durch Farbe vermittelt

- [ ] **Screen Reader Kompatibilität**
  - Getestet mit NVDA (Windows) oder VoiceOver (macOS)
  - Alle Formularfelder korrekt angekündigt
  - Fehlermeldungen werden vorgelesen
  - Bildschirmleser-freundliche Error Messages
  - Versteckte Inhalte mit `aria-hidden="true"` oder `hidden`
  - Dekorative Bilder mit `alt=""` (nicht `alt="image"`)

- [ ] **Formular-Accessibility**
  - Jedes `<input>` hat zugehöriges `<label>` (via `for`/`id` oder implicit)
  - Pflichtfelder mit `required` und `aria-required="true"`
  - Fehlermeldungen mit `aria-invalid` und `aria-describedby`
  - Autocomplete-Attribute gesetzt (email, name, tel, etc.)
  - Gruppierte Inputs mit `<fieldset>` und `<legend>`
  - Inline-Validierung zugänglich (nicht nur visuell)

- [ ] **Interaktive Elemente**
  - Mindestgröße 44×44px für Touch-Targets (mobil)
  - Genügend Abstand zwischen klickbaren Elementen (≥8px)
  - Hover- und Focus-States deutlich erkennbar
  - Disabled-States visuell und per Attribut (`disabled`, `aria-disabled`)
  - Loading-States mit `aria-busy="true"` und Spinner

- [ ] **Multimedia & Animationen**
  - Videos haben Untertitel (falls vorhanden)
  - Autoplay vermieden oder mit Pause-Button
  - `prefers-reduced-motion` respektiert (keine Animationen für Motion-Sensitive Users)
  - Gif-Animationen pausierbar
  - Zeitlimits vermeidbar/verlängerbar

- [ ] **Mobile Accessibility**
  - Pinch-to-Zoom nicht deaktiviert
  - Viewport Meta-Tag korrekt (`user-scalable=yes`)
  - Touch-Targets groß genug (≥44px)
  - Orientierung nicht gesperrt (Portrait/Landscape)

- [ ] **Accessibility Testing Tools**
  - Axe DevTools: Keine kritischen Violations
  - Lighthouse Accessibility Score: ≥90
  - WAVE Browser Extension: Keine Errors
  - Keyboard-only Navigation: Manuell getestet
  - Screen Reader: Stichproben-Test durchgeführt

---

## 8. Integration

### 8.1 API Compatibility
- [ ] **Backward Compatibility gewährleistet** (falls relevant)
  - Keine Breaking Changes ohne Migration
  - API-Versionierung beachtet
  - Deprecated Features dokumentiert

### 8.2 Database
- [ ] **MongoDB Migrationen vorhanden** (falls relevant)
  - Indexes erstellt (`db.py` aktualisiert)
  - Migration-Script für bestehende Daten
  - Rollback-Plan vorhanden

---

## 9. Git & Deployment

### 9.1 Git Workflow
- [ ] **Feature Branch erstellt**
  - Naming: `feature/<feature-name>`
  - Von `main` abgezweigt
  - Regelmäßig mit `main` synchronisiert

- [ ] **Commits atomar und aussagekräftig**
  - Commit Message Format: `<type>: <description>`
  - Types: `feat`, `fix`, `test`, `docs`, `style`, `refactor`, `chore`
  - Jeder Commit kompiliert und Tests bestehen

- [ ] **Pull Request erstellt**
  - PR-Titel beschreibt Feature
  - PR-Description enthält:
    - Summary
    - Changes
    - Test Results
    - Breaking Changes (falls vorhanden)
  - Screenshots/GIFs für UI-Changes

### 9.2 Code Review
- [ ] **PR Review durchgeführt**
  - Mindestens 1 Approval (bei Team-Arbeit)
  - Alle Kommentare adressiert
  - Keine ungelösten Conversations

### 9.3 Merge & Cleanup
- [ ] **PR gemerged**
  - Squash Merge (für saubere History)
  - Feature Branch gelöscht (lokal und remote)

- [ ] **Post-Merge Verification**
  - GitHub Actions auf `main` bestanden
  - Deployment erfolgreich (falls Auto-Deploy)
  - Keine Regressionen in Production

---

## 10. Monitoring & Observability

### 10.1 Logging
- [ ] **Aussagekräftiges Logging implementiert**
  - INFO für wichtige Business Events
  - ERROR für Fehler mit Stack Traces
  - DEBUG für Debugging-Details
  - Keine sensiblen Daten geloggt (Passwords, Tokens)

### 10.2 Metrics
- [ ] **Monitoring berücksichtigt** (falls relevant)
  - Performance-Metriken erfassbar
  - Error-Rates trackbar
  - Audit Logs für wichtige Actions

---

## 11. Checkliste für verschiedene Task-Typen

### 11.1 Neue Features (User Stories)
Alle Punkte aus Abschnitten 1-10 müssen erfüllt sein.

**Zusätzlich:**
- [ ] Feature Flag implementiert (falls schrittweises Rollout)
- [ ] Analytics-Events implementiert (falls Tracking erforderlich)

### 11.2 Bug Fixes
**Erforderlich:**
- [ ] Root Cause identifiziert und dokumentiert
- [ ] Regression Test hinzugefügt (verhindert Wiederauftreten)
- [ ] Fix in betroffenen Branches/Versionen (falls relevant)

**Optional (je nach Schwere):**
- User Story/Gherkin Spec (für kritische Bugs)
- Post-Mortem Dokument (für Production Incidents)

### 11.3 Refactoring
**Erforderlich:**
- [ ] Keine Functional Changes (nur Struktur-Änderungen)
- [ ] Alle Tests bestehen unverändert
- [ ] Code Coverage bleibt gleich oder steigt
- [ ] Performance gleich oder besser

### 11.4 Dokumentation
**Erforderlich:**
- [ ] Grammatik und Rechtschreibung korrekt
- [ ] Code-Beispiele getestet und funktionsfähig
- [ ] Links aktuell und nicht broken
- [ ] Versionsnummern korrekt

---

## 12. Ausnahmen und Kompromisse

### 12.1 Wann DoD-Punkte übersprungen werden können

**Hotfixes (Production Critical):**
- Code Coverage kann temporär < 90% sein
- E2E Tests können nachgereicht werden
- MUSS innerhalb von 48h nachgeholt werden

**Proof of Concepts (PoC):**
- Tests optional (aber empfohlen)
- Dokumentation minimal
- MUSS mit `[PoC]` Tag markiert werden

**Experimentelle Features (Beta):**
- E2E Tests können reduziert sein (≥70%)
- MUSS mit Feature Flag abgesichert sein
- MUSS als "Beta" in UI markiert sein

### 12.2 Eskalation bei DoD-Verstößen
1. **Self-Check:** AI-Agent oder Entwickler prüft DoD vor PR
2. **PR Review:** Reviewer prüft DoD-Compliance
3. **CI/CD:** Automatische Checks verhindern Merge bei Violations
4. **Post-Merge:** Monitoring erkennt Production Issues

---

## 13. Werkzeuge und Automation

### 13.1 Automatisierte DoD-Checks

**Pre-Commit Hooks:**
```bash
# .git/hooks/pre-commit
black src tests
ruff check src tests --fix
pytest --cov=src --cov-report=term-missing --cov-fail-under=90
```

**GitHub Actions Workflow:**
```yaml
# .github/workflows/dod-check.yml
- Formatting Check (Black)
- Linting Check (Ruff)
- Unit Tests + Coverage (90%)
- Integration Tests
- E2E Tests (Playwright)
- Security Scan (Bandit)
- i18n Completeness Check
- Accessibility (a11y) Check
- Performance Anti-Patterns Check
```

**Pre-Push Script:**
```bash
# scripts/pre-push-check.sh
docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

### 13.2 DoD Verification Command
```bash
# Vollständiger DoD-Check (lokal)
./scripts/verify-dod.sh

# Führt aus:
# 1. black --check src tests
# 2. ruff check src tests
# 3. pytest --cov=src --cov-report=html --cov-fail-under=90
# 4. docker compose -f docker-compose.test.yml up --abort-on-container-exit
```

---

## 14. Kontinuierliche Verbesserung

### 14.1 DoD Review
- **Quartalsweise:** DoD auf Aktualität prüfen
- **Nach jedem Sprint:** Verbesserungsvorschläge sammeln
- **Bei Incidents:** DoD anpassen, um Wiederholung zu verhindern

### 14.2 Metriken
**Tracking:**
- DoD-Compliance Rate pro PR
- Durchschnittliche Zeit bis DoD erfüllt
- Anzahl Post-Merge Bugfixes (Indikator für DoD-Qualität)

**Ziele:**
- ≥95% DoD-Compliance vor Merge
- <5% Post-Merge Bugfix Rate
- Kontinuierliche Verbesserung der Test Coverage

---

## Appendix A: Schnell-Checkliste

**Vor dem Commit:**
```
□ Code formatiert (black)
□ Linting sauber (ruff)
□ Tests lokal bestanden (pytest)
□ Coverage ≥90%
```

**Vor dem PR:**
```
□ User Story + Gherkin Spec vorhanden
□ E2E Tests geschrieben (Playwright)
□ docker-compose Tests bestanden
□ Accessibility (a11y) geprüft:
  □ ARIA-Labels vorhanden
  □ Semantic HTML verwendet
  □ Keyboard-Navigation funktioniert
  □ Farbkontrast WCAG AA (≥4.5:1)
  □ Alt-Texte für Bilder
  □ Form Labels korrekt
□ README.md aktualisiert (falls nötig)
□ Commit Messages aussagekräftig
```

**Vor dem Merge:**
```
□ PR Review erhalten
□ GitHub Actions ✅
□ Feature Branch bereit zum Löschen
```

---

## Appendix B: Kontakte und Ressourcen

**Dokumentation:**
- [AGENTS.md](AGENTS.md) - Entwicklungsrichtlinien
- [README.md](README.md) - Benutzerdokumentation
- [CLAUDE.md](CLAUDE.md) - Quick Reference

**Tools:**
- Black Formatter: https://black.readthedocs.io/
- Ruff Linter: https://docs.astral.sh/ruff/
- Playwright: https://playwright.dev/python/
- pytest: https://docs.pytest.org/

---

**Letzte Aktualisierung:** 2025-12-27
**Nächste Review:** 2025-03-27
