# User Story: Lokaler Standardbenutzer für Non-Auth-Modus

**ID**: US-003
**Titel**: Automatischer lokaler Standardbenutzer wenn Authentifizierung deaktiviert
**Status**: ✅ Implementiert
**Datum**: 2024-12-25

---

## Story

**Als** Benutzer des PDF/A-Service ohne OAuth-Integration
**möchte ich** dass automatisch ein lokaler Standardbenutzer erstellt wird, wenn die Authentifizierung deaktiviert ist
**damit** ich Zugriff auf Features wie Job-Verlauf und persistente Speicherung habe, ohne OAuth konfigurieren zu müssen.

---

## Kontext

**Aktueller Zustand (vor lokalem Standardbenutzer)**:
- Bei `AUTH_ENABLED=false` ist `user_id=None` für alle Jobs
- `get_current_user_optional()` gibt `None` zurück
- Features wie `/api/v1/jobs/history` funktionieren nicht (filtern nach user_id)
- MongoDB-Persistierung speichert Jobs ohne Benutzer-Zuordnung
- Kein Zugriff auf personalisierte Features im Non-Auth-Modus

**Problem**:
- Benutzer ohne OAuth können Job-Verlauf nicht nutzen
- Persistierte Jobs sind keinem Benutzer zugeordnet
- Features, die user_id benötigen, sind nicht verfügbar
- Inkonsistente User Experience zwischen Auth/Non-Auth-Modi

**Lösung**:
- Automatische Erstellung eines Standardbenutzers beim Startup (wenn Auth deaktiviert)
- Konfigurierbare Standardbenutzer-Felder via Umgebungsvariablen
- Dependency Injection gibt Standardbenutzer statt `None` zurück
- Idempotente Implementierung (safe für Multi-Instance)

---

## Akzeptanzkriterien

### 1. Automatische Erstellung beim Start
- **Given** der Service startet mit `AUTH_ENABLED=false`
- **When** MongoDB verfügbar ist
- **Then** sollte ein Standardbenutzer in der `users` Collection erstellt werden
- **And** sollte Standardwerte verwenden: `user_id="local-default"`, `email="local@localhost"`, `name="Local User"`
- **And** sollte beim Log "Default user ensured" ausgeben

### 2. Idempotente Erstellung
- **Given** ein Standardbenutzer existiert bereits in MongoDB
- **When** der Service neu startet
- **Then** sollte kein Duplikat erstellt werden
- **And** sollte der bestehende Benutzer aktualisiert werden (Upsert)
- **And** sollte `login_count` inkrementiert werden

### 3. Konfigurierbare Felder
- **Given** Umgebungsvariablen `DEFAULT_USER_ID`, `DEFAULT_USER_EMAIL`, `DEFAULT_USER_NAME` sind gesetzt
- **When** der Service startet
- **Then** sollten diese Werte statt der Standardwerte verwendet werden
- **And** sollten die konfigurierten Werte in MongoDB gespeichert werden

### 4. Job-Attribution
- **Given** der Service läuft mit `AUTH_ENABLED=false`
- **When** ein Job via WebSocket erstellt wird
- **Then** sollte `job.user_id` den Wert des Standardbenutzers haben
- **And** sollte der Job in MongoDB mit dieser user_id gespeichert werden

### 5. Job-Verlauf funktioniert
- **Given** Jobs wurden mit Standardbenutzer erstellt
- **When** `GET /api/v1/jobs/history` aufgerufen wird (ohne Auth-Header)
- **Then** sollten alle Jobs des Standardbenutzers zurückgegeben werden
- **And** sollte die Response Status 200 haben

### 6. Keine Interferenz mit Auth-Modus
- **Given** der Service startet mit `AUTH_ENABLED=true`
- **When** der Startup-Prozess läuft
- **Then** sollte KEIN Standardbenutzer erstellt werden
- **And** sollte `get_current_user_optional()` den OAuth-User zurückgeben

### 7. Fallback bei fehlender Config
- **Given** `auth_config` ist `None` (Edge Case)
- **When** `get_current_user_optional()` aufgerufen wird
- **Then** sollte ein Standardbenutzer mit Hardcoded-Defaults zurückgegeben werden
- **And** sollte `user_id="local-default"` sein

---

## Definition of Done

- [x] TDD: Alle Tests geschrieben und bestanden
- [x] Volle pytest-Suite grün (100%)
- [x] Code formatiert (black)
- [x] Linting sauber (ruff)
- [x] Dokumentation aktualisiert (README.md, .env.example)
- [x] User Story erstellt (diese Datei)
- [x] Gherkin Feature erstellt
- [x] Manuelles Testen durchgeführt
- [x] Keine Breaking Changes

---

## Technische Details

### Datenmodell

**AuthConfig** (erweitert):
```python
@dataclass
class AuthConfig:
    enabled: bool
    # ... bestehende Felder ...

    # Neu: Standardbenutzer-Felder
    default_user_id: str = "local-default"
    default_user_email: str = "local@localhost"
    default_user_name: str = "Local User"
```

**UserDocument** (keine Änderungen):
```python
class UserDocument(BaseModel):
    user_id: str
    email: str
    name: str
    picture: str | None
    created_at: datetime
    last_login_at: datetime
    login_count: int
```

### Implementierte Komponenten

**1. Konfiguration** (`src/pdfa/auth_config.py`):
- 3 neue Felder: `default_user_id`, `default_user_email`, `default_user_name`
- `from_env()` lädt Werte aus Umgebungsvariablen
- Fallback zu Standardwerten wenn nicht gesetzt

**2. Startup-Integration** (`src/pdfa/api.py`):
- `ensure_default_user()` Funktion (neu)
  - Prüft ob Auth deaktiviert
  - Erstellt UserDocument mit Standardwerten
  - Ruft `UserRepository.create_or_update_user()` auf
  - Logging der Aktion
- `startup_event()` (erweitert)
  - Lädt `auth_config` nach MongoDB-Verbindung
  - Ruft `ensure_default_user()` auf

**3. Dependency Injection** (`src/pdfa/auth.py`):
- `get_current_user_optional()` (modifiziert)
  - Prüft ob Auth deaktiviert
  - Gibt User-Objekt mit Standardwerten zurück (statt `None`)
  - Fallback zu Hardcoded-Defaults wenn `auth_config` fehlt
  - Normale OAuth-Logik bei aktivierter Auth

**4. Tests**:
- `tests/test_auth.py` - Konfiguration und Dependency Injection
- `tests/test_api.py` - Integration Tests für Startup und WebSocket
- `tests/test_repositories.py` - Idempotente User-Erstellung

### Architektur

**Flow bei Service-Start**:
```
Service Start
    ↓
MongoDB Verbindung (bestehend)
    ↓
auth_config = AuthConfig.from_env()
    ↓
ensure_default_user()
    ├─ Auth enabled? → Skip
    └─ Auth disabled:
        ↓
        UserRepository.create_or_update_user()
        ↓
        MongoDB Upsert (idempotent)
```

**Flow bei Job-Erstellung**:
```
WebSocket /convert
    ↓
get_current_user_optional()
    ├─ Auth enabled → OAuth User
    └─ Auth disabled → Default User Object
        ↓
process_conversion_job(user=default_user)
    ↓
job.user_id = "local-default"
    ↓
MongoDB jobs.insert_one()
```

### Umgebungsvariablen

Neue Variablen:
```bash
# Standardbenutzer-Konfiguration (nur relevant wenn AUTH_ENABLED=false)
DEFAULT_USER_ID=local-default          # Standard-User-ID
DEFAULT_USER_EMAIL=local@localhost     # Standard-Email
DEFAULT_USER_NAME=Local User           # Standard-Name
```

Bestehende Variablen:
```bash
AUTH_ENABLED=false                     # Authentifizierung deaktivieren
MONGODB_URL=mongodb://...              # MongoDB-Verbindung
MONGODB_DB=pdfa_service                # Datenbank-Name
```

---

## TDD Implementierungsphasen

### Phase 1: Konfiguration ✅
- Tests für AuthConfig-Felder
- Tests für from_env() mit Environment-Variablen
- Implementierung der 3 neuen Felder
- Update von from_env() Methode

### Phase 2: Default User Creation ✅
- Tests für ensure_default_user() Funktion
- Tests für Idempotenz (mehrfache Aufrufe)
- Tests für Auth-enabled/disabled Logik
- Implementierung von ensure_default_user()
- Integration in startup_event()

### Phase 3: Dependency Injection ✅
- Tests für get_current_user_optional() Return-Werte
- Tests für Auth disabled → Default User
- Tests für Auth enabled → OAuth User
- Tests für auth_config=None Fallback
- Modifikation von get_current_user_optional()

### Phase 4: Integration Tests ✅
- Tests für WebSocket Job-Erstellung mit Default User
- Tests für Job-History mit Default User
- Tests für Service-Start mit MongoDB
- End-to-End-Tests für kompletten Flow

### Phase 5: Dokumentation ✅
- .env.example aktualisiert
- README.md aktualisiert
- Diese User Story
- Gherkin Feature-Datei
- Volle Test-Suite

---

## Performance-Überlegungen

**Startup-Impact**:
- +1 MongoDB Query (~50ms) für Upsert
- Nur bei deaktivierter Auth
- Akzeptabler Overhead

**Runtime-Impact**:
- 0ms - keine zusätzlichen Queries zur Laufzeit
- Dependency Injection gibt statisches User-Objekt zurück
- Keine Änderung der bestehenden Performance

**Datenbank**:
- +1 Dokument in `users` Collection (~1KB)
- Vernachlässigbarer Speicher-Overhead
- Keine zusätzlichen Indexes erforderlich

---

## Risiken & Mitigationen

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| Config nicht geladen | Sehr niedrig | Mittel | Hardcoded Fallbacks in get_current_user_optional() |
| Race Condition (Multi-Instance) | Sehr niedrig | Niedrig | MongoDB Upsert ist atomar |
| Default User ID-Konflikt | Sehr niedrig | Niedrig | Dokumentation warnt vor "local-*" Pattern |
| Auth enabled→disabled Switch | Niedrig | Niedrig | Self-healing: User wird beim nächsten Start erstellt |
| Breaking Changes | Sehr niedrig | Hoch | Alle neuen Felder haben Standardwerte |
| MongoDB down beim Start | Mittel | Hoch | Service schlägt fehl (bestehende Logik) |

---

## Backward Compatibility

**Keine Breaking Changes**:
- Alle neuen Felder in AuthConfig haben Standardwerte
- Bestehender Auth-Flow völlig unverändert
- Keine DB-Migrationen erforderlich
- Service funktioniert weiterhin mit bestehenden Configs

**Upgrade-Pfad**:
1. Code deployen
2. Service neu starten
3. Bei AUTH_ENABLED=false wird Default User automatisch erstellt
4. Keine manuellen Schritte erforderlich

**Downgrade-Pfad**:
1. Code zurückrollen
2. Default User bleibt in MongoDB (harmlos)
3. Service funktioniert wie vorher
4. Keine Cleanup erforderlich

---

## Edge Cases

### 1. MongoDB-Verbindungsfehler beim Start
**Verhalten**: Service-Start schlägt fehl (bestehende Logik)
**Handling**: Keine Änderung, DB-Verbindung ist bereits Requirement

### 2. Race Condition (Multi-Instance)
**Verhalten**: Mehrere Instanzen starten gleichzeitig
**Handling**: MongoDB Upsert ist atomar, kein Problem

### 3. Auth-Config nicht geladen
**Verhalten**: `auth_config` ist `None`
**Handling**: Fallback zu Hardcoded-Defaults in get_current_user_optional()

### 4. Wechsel Auth disabled→enabled
**Verhalten**: Service wechselt von false zu true
**Handling**: Default User bleibt in DB (harmlos), wird nicht mehr verwendet

### 5. Wechsel Auth enabled→disabled
**Verhalten**: Service wechselt von true zu false
**Handling**: Default User wird beim nächsten Start erstellt

### 6. Default User gelöscht
**Verhalten**: Jemand löscht Default User aus MongoDB
**Handling**: Self-healing - wird beim nächsten Neustart neu erstellt

### 7. Custom Default User ID = OAuth User ID
**Verhalten**: Benutzer setzt DEFAULT_USER_ID auf OAuth-User-ID
**Handling**: User-Verantwortung, Dokumentation warnt davor

---

## Verwandte Spezifikationen

**User Stories**:
- [US-001: MongoDB Integration](US-001-mongodb-integration.md) - Grundlage für User-Persistierung
- [US-002: Job Event Logging](US-002-job-event-logging.md) - Verwendet user_id für Events

**Gherkin Features**:
- [Local Default User](../features/gherkin-local-default-user.feature) - 18 detaillierte Szenarien

**Dokumentation**:
- [AGENTS.md](../../../AGENTS.md) - Entwicklungsrichtlinien
- [README.md](../../../README.md) - Benutzer-Dokumentation

---

## Änderungshistorie

| Datum | Version | Änderung |
|-------|---------|----------|
| 2024-12-25 | 1.0 | Initiale Implementierung (Phase 1-5) |
