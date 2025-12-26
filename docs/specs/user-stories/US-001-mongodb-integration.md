# User Story: MongoDB-Integration

**ID**: US-001
**Titel**: Persistente Datenspeicherung mit MongoDB einführen
**Status**: ✅ Implementiert
**Datum**: 2024-12-21

---

## Story

**Als** Systemadministrator und Benutzer des PDF/A-Service
**möchte ich** dass Conversion-History, OAuth-Tokens und Audit-Logs persistent in einer Datenbank gespeichert werden
**damit** ich die Service-Nutzung nachvollziehen kann, OAuth in Multi-Instance-Deployments funktioniert und Daten über Server-Neustarts hinweg erhalten bleiben.

---

## Kontext

**Aktueller Zustand (vor MongoDB)**:
- Jobs nur im RAM (1h TTL, verloren bei Server-Neustart)
- OAuth State Tokens im RAM (funktioniert nicht mit Load Balancer)
- Keine Conversion-History
- Keine Audit-Logs

**Problem**:
- Benutzer können ihre vergangenen Konvertierungen nicht einsehen
- OAuth schlägt fehl bei Multi-Instance-Deployments
- Keine Nachvollziehbarkeit für Security-Events
- Job-Daten gehen bei Server-Neustart verloren

**Lösung**:
- MongoDB als persistente Datenschicht
- Hard Migration (Service startet nicht ohne DB)
- Docker Compose mit MongoDB-Authentifizierung

---

## Akzeptanzkriterien

### 1. MongoDB-Verbindung ist erforderlich
- **Given** der Service wird gestartet
- **When** MongoDB nicht erreichbar ist
- **Then** sollte der Service mit Fehler beenden
- **And** eine klare Fehlermeldung ausgeben

### 2. Conversion-History wird persistent gespeichert
- **Given** ein Benutzer konvertiert ein Dokument
- **When** die Konvertierung abgeschlossen ist
- **Then** sollte der Job in MongoDB `jobs` Collection gespeichert werden
- **And** sollte die Job-ID, Status, Konfiguration und Zeiten enthalten
- **And** sollte nach 90 Tagen automatisch gelöscht werden (TTL)

### 3. OAuth State Tokens sind persistent
- **Given** ein Benutzer startet OAuth-Flow
- **When** der State Token generiert wird
- **Then** sollte er in MongoDB `oauth_states` Collection gespeichert werden
- **And** sollte nach 10 Minuten automatisch gelöscht werden (TTL)
- **And** sollte IP-Adresse und User-Agent enthalten

### 4. Audit Logs werden gespeichert
- **Given** ein relevantes Event tritt auf (Login, Job-Erstellung, etc.)
- **When** das Event eintritt
- **Then** sollte es in MongoDB `audit_logs` Collection gespeichert werden
- **And** sollte Typ, User-ID, Timestamp und Details enthalten
- **And** sollte nach 1 Jahr automatisch gelöscht werden (TTL)

### 5. User-Profile werden minimal gespeichert
- **Given** ein Benutzer loggt sich erstmalig ein
- **When** OAuth erfolgreich ist
- **Then** sollte ein User-Dokument in `users` Collection erstellt werden
- **And** sollte Email, Name, Picture und Timestamps enthalten
- **And** sollte Login-Count inkrementieren bei jedem Login

### 6. Backward Compatibility für Auth-Disabled Mode
- **Given** der Service läuft ohne Authentifizierung (AUTH_ENABLED=false)
- **When** ein Job erstellt wird
- **Then** sollte `user_id` auf `null` gesetzt werden
- **And** sollte der Job normal in MongoDB gespeichert werden

---

## Definition of Done

- [x] MongoDB Docker Container läuft mit Authentifizierung
- [x] 4 Collections erstellt: `users`, `jobs`, `oauth_states`, `audit_logs`
- [x] TTL-Indexes konfiguriert (90d, 10min, 1 Jahr)
- [x] Repository-Pattern implementiert (JobRepository, UserRepository, etc.)
- [x] Alle Unit-Tests bestehen mit MongoDB-Mocking
- [x] Integration-Tests mit echtem MongoDB
- [x] Dokumentation in AGENTS.md
- [x] Docker Compose konfiguriert mit MongoDB
- [x] Umgebungsvariablen dokumentiert (MONGODB_URL, MONGODB_DB)

---

## Technische Details

### MongoDB Schema

**Collections**:
1. `users` - User-Profile (minimal)
2. `jobs` - Conversion-History
3. `oauth_states` - OAuth CSRF Tokens
4. `audit_logs` - Event-Protokollierung

**Indexes**:
- `users`: `user_id` (unique), `email`, `last_login_at`
- `jobs`: `job_id` (unique), `user_id+created_at`, `status+created_at`, TTL auf `created_at` (90d)
- `oauth_states`: `state` (unique), TTL auf `created_at` (10min)
- `audit_logs`: `user_id+timestamp`, `event_type+timestamp`, TTL auf `timestamp` (1 Jahr)

### Deployment

**Docker Compose**:
```yaml
services:
  mongodb:
    image: mongo:7
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD}
    volumes:
      - mongodb_data:/data/db
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js

  pdfa-service:
    environment:
      MONGODB_URL: mongodb://pdfa_user:${MONGO_PDFA_PASSWORD}@mongodb:27017/
      MONGODB_DB: pdfa_service
```

### Implementierte Komponenten

**Repositories** (`src/pdfa/repositories.py`):
- `UserRepository` - User-CRUD-Operationen
- `JobRepository` - Job-CRUD + Events
- `OAuthStateRepository` - State Token Management
- `AuditLogRepository` - Event-Logging

**Models** (`src/pdfa/models.py`):
- `UserDocument` - Pydantic Model für User
- `JobDocument` - Pydantic Model für Jobs
- `OAuthStateDocument` - Pydantic Model für OAuth States
- `AuditLogDocument` - Pydantic Model für Audit Logs

**Connection Management** (`src/pdfa/db.py`):
- `MongoDBConnection` - Singleton für DB-Verbindung
- `get_db()` - Dependency Injection Helper
- `ensure_indexes()` - Index-Erstellung bei Startup

---

## Abhängigkeiten

**Python Packages**:
- `motor` - Async MongoDB Driver
- `pymongo` - Sync MongoDB Driver (für Indexes)
- `pydantic` - Data Validation

**Infrastructure**:
- MongoDB 7.x
- Docker Compose

---

## Risiken & Mitigationen

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| MongoDB nicht erreichbar | Mittel | Hoch | Health Checks, klare Fehlermeldungen, Service beendet |
| Datenbank-Performance | Niedrig | Mittel | Indexes, TTL-Cleanup, Monitoring |
| Daten-Migration bei Schema-Änderungen | Mittel | Mittel | Pydantic default_factory, backward compatibility |
| Verbindungs-Leaks | Niedrig | Hoch | Motor Connection Pooling, Singleton Pattern |

---

## Verwandte Spezifikationen

**User Stories**:
- [US-002: Job Event Logging](US-002-job-event-logging.md) - Baut auf MongoDB auf

**Gherkin Features**:
- [MongoDB Integration](../features/gherkin-mongodb-integration.feature) - 36 detaillierte Szenarien

---

## Änderungshistorie

| Datum | Version | Änderung |
|-------|---------|----------|
| 2024-12-21 | 1.0 | Initiale Implementierung |
| 2024-12-25 | 1.1 | Dokumentation vervollständigt |
| 2024-12-25 | 1.2 | Umstrukturierung: User Stories und Gherkin Features getrennt |
