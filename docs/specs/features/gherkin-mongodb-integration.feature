# language: de
Funktionalität: MongoDB-Integration für persistente Datenspeicherung
  Als Systemadministrator und Benutzer
  möchte ich dass Conversion-History, OAuth-Tokens und Audit-Logs persistent gespeichert werden
  damit ich die Service-Nutzung nachvollziehen kann und Daten über Server-Neustarts hinweg erhalten bleiben

  Hintergrund:
    Angenommen der Service ist mit MongoDB verbunden
    Und die Datenbank "pdfa_service" existiert
    Und die Collections "users", "jobs", "oauth_states", "audit_logs" existieren

  # =============================================================================
  # Szenario-Gruppe 1: Service-Start und MongoDB-Verbindung
  # =============================================================================

  Szenario: Service startet erfolgreich mit MongoDB-Verbindung
    Angenommen MongoDB läuft auf "mongodb://localhost:27017"
    Und die Datenbank-Credentials sind korrekt
    Wenn der Service gestartet wird
    Dann sollte die MongoDB-Verbindung erfolgreich hergestellt werden
    Und alle Indexes sollten erstellt werden
    Und der Service sollte den Status "ready" haben

  Szenario: Service-Start schlägt fehl ohne MongoDB
    Angenommen MongoDB ist nicht erreichbar
    Wenn der Service gestartet wird
    Dann sollte der Service-Start fehlschlagen
    Und eine Fehlermeldung sollte angezeigt werden mit:
      """
      Failed to connect to MongoDB
      """
    Und der Exit-Code sollte nicht 0 sein

  Szenario: Service-Start schlägt fehl mit falschen Credentials
    Angenommen MongoDB läuft auf "mongodb://localhost:27017"
    Aber die Datenbank-Credentials sind falsch
    Wenn der Service gestartet wird
    Dann sollte der Service-Start fehlschlagen
    Und eine Fehlermeldung sollte "Authentication failed" enthalten

  # =============================================================================
  # Szenario-Gruppe 2: Job-Persistierung (Conversion History)
  # =============================================================================

  Szenario: Neuer Job wird in MongoDB gespeichert
    Angenommen ein Benutzer "user@example.com" ist authentifiziert
    Und eine PDF-Datei "document.pdf" wird hochgeladen
    Wenn ein Konvertierungsjob erstellt wird
    Dann sollte ein Job-Dokument in der "jobs" Collection gespeichert werden
    Und das Job-Dokument sollte folgende Felder enthalten:
      | Feld       | Typ        |
      | job_id     | string     |
      | user_id    | string     |
      | status     | string     |
      | filename   | string     |
      | config     | object     |
      | created_at | datetime   |
    Und der Status sollte "queued" sein
    Und die user_id sollte "google_123" sein (Google OAuth)

  Szenario: Job-Status-Updates werden persistent gespeichert
    Angenommen ein Job mit ID "test-job-123" existiert in MongoDB
    Und der aktuelle Status ist "queued"
    Wenn der Status auf "processing" aktualisiert wird
    Dann sollte das Job-Dokument in MongoDB aktualisiert werden
    Und das Feld "status" sollte "processing" sein
    Und das Feld "started_at" sollte gesetzt sein
    Und die Änderung sollte sofort in MongoDB sichtbar sein

  Szenario: Job-Completion wird mit Metadaten gespeichert
    Angenommen ein Job mit ID "test-job-456" wird verarbeitet
    Wenn die Konvertierung erfolgreich abgeschlossen wird
    Dann sollte der Job-Status auf "completed" gesetzt werden
    Und folgende Felder sollten gesetzt sein:
      | Feld                | Erwartung      |
      | completed_at        | aktueller Zeit |
      | duration_seconds    | > 0            |
      | file_size_input     | > 0            |
      | file_size_output    | > 0            |
    Und das "error" Feld sollte null sein

  Szenario: Fehlgeschlagener Job wird mit Error gespeichert
    Angenommen ein Job mit ID "test-job-789" schlägt fehl
    Und der Fehler ist "OCRmyPDF failed: Invalid PDF"
    Wenn der Job-Status auf "failed" gesetzt wird
    Dann sollte das "error" Feld den Fehlertext enthalten
    Und der "status" sollte "failed" sein
    Und "completed_at" sollte gesetzt sein

  Szenario: Job ohne Authentifizierung hat user_id null
    Angenommen der Service läuft im Modus AUTH_ENABLED=false
    Und eine PDF-Datei wird hochgeladen
    Wenn ein Konvertierungsjob erstellt wird
    Dann sollte das Job-Dokument gespeichert werden
    Und die "user_id" sollte null sein
    Aber alle anderen Felder sollten normal gesetzt sein

  Szenario: Alte Jobs werden nach TTL automatisch gelöscht
    Angenommen ein abgeschlossener Job ist 91 Tage alt
    Und der TTL-Index ist auf 90 Tage konfiguriert
    Wenn der MongoDB TTL-Monitor läuft
    Dann sollte der alte Job automatisch gelöscht werden
    Und neuere Jobs (< 90 Tage) sollten erhalten bleiben

  # =============================================================================
  # Szenario-Gruppe 3: OAuth State Token Management
  # =============================================================================

  Szenario: OAuth State Token wird persistent gespeichert
    Angenommen ein Benutzer startet den OAuth-Flow
    Wenn ein State Token "csrf-abc123" generiert wird
    Dann sollte der Token in der "oauth_states" Collection gespeichert werden
    Und das Dokument sollte folgende Felder enthalten:
      | Feld       | Wert              |
      | state      | csrf-abc123       |
      | ip_address | 192.168.1.100     |
      | user_agent | Mozilla/5.0...    |
    Und "created_at" sollte die aktuelle Zeit sein

  Szenario: OAuth State Token wird validiert
    Angenommen ein State Token "csrf-valid" existiert in MongoDB
    Und der Token ist weniger als 10 Minuten alt
    Wenn der OAuth-Callback mit state="csrf-valid" empfangen wird
    Dann sollte die Validierung erfolgreich sein
    Und der Token sollte aus MongoDB gelöscht werden (One-Time-Use)

  Szenario: Abgelaufene OAuth State Tokens werden automatisch gelöscht
    Angenommen ein State Token ist 11 Minuten alt
    Und der TTL-Index ist auf 10 Minuten konfiguriert
    Wenn der MongoDB TTL-Monitor läuft
    Dann sollte der abgelaufene Token automatisch gelöscht werden

  Szenario: OAuth funktioniert in Multi-Instance-Deployment
    Angenommen zwei Service-Instanzen laufen (Instance A und B)
    Und Instance A generiert State Token "csrf-multi"
    Wenn Instance B den OAuth-Callback mit "csrf-multi" empfängt
    Dann sollte Instance B den Token in MongoDB finden
    Und die Validierung sollte erfolgreich sein
    # Dies funktioniert nur mit MongoDB, nicht mit In-Memory-Storage

  # =============================================================================
  # Szenario-Gruppe 4: User-Profile (Minimal)
  # =============================================================================

  Szenario: Neuer Benutzer wird bei erstem Login erstellt
    Angenommen ein Google-Benutzer "newuser@gmail.com" loggt sich erstmalig ein
    Und die Google OAuth Daten sind:
      | Feld    | Wert                  |
      | user_id | google_12345          |
      | email   | newuser@gmail.com     |
      | name    | New User              |
      | picture | https://photo.url     |
    Wenn der OAuth-Prozess abgeschlossen wird
    Dann sollte ein User-Dokument in der "users" Collection erstellt werden
    Und das Dokument sollte enthalten:
      | Feld          | Wert              |
      | user_id       | google_12345      |
      | email         | newuser@gmail.com |
      | name          | New User          |
      | picture       | https://photo.url |
      | login_count   | 1                 |
    Und "created_at" und "last_login_at" sollten gesetzt sein

  Szenario: Bestehender Benutzer wird bei Login aktualisiert
    Angenommen ein User "existinguser@gmail.com" existiert in MongoDB
    Und der aktuelle "login_count" ist 5
    Und "last_login_at" ist vor 2 Tagen
    Wenn der Benutzer sich erneut einloggt
    Dann sollte das User-Dokument aktualisiert werden
    Und "login_count" sollte 6 sein
    Und "last_login_at" sollte auf die aktuelle Zeit aktualisiert werden
    Aber "created_at" sollte unverändert bleiben

  Szenario: User-Profile sind minimal (keine erweiterten Felder)
    Angenommen ein User wird in MongoDB gespeichert
    Dann sollte das Dokument NUR folgende Felder enthalten:
      | Erforderliche Felder |
      | user_id              |
      | email                |
      | name                 |
      | picture              |
      | created_at           |
      | last_login_at        |
      | login_count          |
    Und es sollten KEINE zusätzlichen Felder existieren wie:
      | Nicht erlaubte Felder |
      | preferences           |
      | settings              |
      | roles                 |
      | permissions           |

  # =============================================================================
  # Szenario-Gruppe 5: Audit Logs
  # =============================================================================

  Szenario: User-Login wird als Audit-Event protokolliert
    Angenommen ein Benutzer "user@example.com" loggt sich ein
    Wenn der Login erfolgreich ist
    Dann sollte ein Audit-Log-Event gespeichert werden
    Und das Event sollte folgende Felder enthalten:
      | Feld        | Wert                |
      | event_type  | user_login          |
      | user_id     | google_123          |
      | ip_address  | 192.168.1.100       |
    Und "timestamp" sollte die aktuelle Zeit sein
    Und "details" sollte Login-Methode enthalten (z.B. "google_oauth")

  Szenario: Fehlgeschlagener Login wird protokolliert
    Angenommen ein Login-Versuch mit ungültigem Token erfolgt
    Wenn die Authentifizierung fehlschlägt
    Dann sollte ein Audit-Log-Event gespeichert werden
    Und das Event sollte folgende Felder enthalten:
      | Feld        | Wert                |
      | event_type  | auth_failure        |
      | user_id     | null                |
      | ip_address  | 192.168.1.100       |
    Und "details" sollte den Fehlergrund enthalten

  Szenario: Job-Erstellung wird als Audit-Event protokolliert
    Angenommen ein Benutzer erstellt einen neuen Job
    Wenn der Job erfolgreich erstellt wird
    Dann sollte ein Audit-Log-Event gespeichert werden
    Und das Event sollte folgende Felder enthalten:
      | Feld        | Wert           |
      | event_type  | job_created    |
      | user_id     | google_123     |
    Und "details" sollte job_id und filename enthalten

  Szenario: Audit Logs werden nach 1 Jahr automatisch gelöscht
    Angenommen ein Audit-Log-Event ist 366 Tage alt
    Und der TTL-Index ist auf 365 Tage konfiguriert
    Wenn der MongoDB TTL-Monitor läuft
    Dann sollte das alte Event automatisch gelöscht werden

  Szenario: Security-Events können abgefragt werden
    Angenommen mehrere Audit-Events existieren:
      | event_type    | timestamp        |
      | user_login    | vor 1 Stunde     |
      | auth_failure  | vor 2 Stunden    |
      | auth_failure  | vor 3 Stunden    |
      | job_created   | vor 30 Minuten   |
    Wenn nach Security-Events der letzten 6 Stunden gefragt wird
    Dann sollten alle Events zurückgegeben werden
    Und sie sollten chronologisch sortiert sein
    Und auth_failure Events sollten filterbar sein

  # =============================================================================
  # Szenario-Gruppe 6: Indexes und Performance
  # =============================================================================

  Szenario: Alle erforderlichen Indexes werden beim Start erstellt
    Angenommen der Service wird gestartet
    Wenn die Index-Erstellung ausgeführt wird
    Dann sollten folgende Indexes existieren:
      | Collection    | Index                      | Type   |
      | users         | user_id                    | unique |
      | users         | email                      | single |
      | users         | last_login_at              | single |
      | jobs          | job_id                     | unique |
      | jobs          | user_id, created_at        | compound |
      | jobs          | status, created_at         | compound |
      | jobs          | created_at                 | TTL 90d |
      | oauth_states  | state                      | unique |
      | oauth_states  | created_at                 | TTL 10min |
      | audit_logs    | user_id, timestamp         | compound |
      | audit_logs    | event_type, timestamp      | compound |
      | audit_logs    | timestamp                  | TTL 1 Jahr |

  Szenario: Job-Queries nutzen Indexes effizient
    Angenommen 10000 Jobs existieren in MongoDB
    Wenn nach Jobs eines bestimmten Benutzers gefragt wird
    Dann sollte der Query den "user_id + created_at" Index nutzen
    Und die Antwortzeit sollte < 100ms sein
    Und MongoDB sollte einen Index-Scan durchführen (kein Collection-Scan)

  Szenario: TTL-Cleanup läuft automatisch
    Angenommen TTL-Indexes sind konfiguriert
    Und alte Dokumente existieren (> TTL)
    Wenn der MongoDB Background Thread läuft
    Dann sollten abgelaufene Dokumente automatisch gelöscht werden
    Ohne manuelle Intervention

  # =============================================================================
  # Szenario-Gruppe 7: Repository-Pattern
  # =============================================================================

  Szenario: JobRepository erstellt neuen Job
    Angenommen ein JobRepository-Objekt wird erstellt
    Wenn create_job() aufgerufen wird mit:
      | Parameter | Wert               |
      | user_id   | google_123         |
      | filename  | test.pdf           |
      | config    | {pdfa_level: "2"}  |
    Dann sollte ein Job in MongoDB erstellt werden
    Und eine job_id sollte generiert werden (UUID)
    Und die job_id sollte zurückgegeben werden

  Szenario: JobRepository aktualisiert Job-Status
    Angenommen ein Job mit ID "test-123" existiert
    Wenn update_job_status() aufgerufen wird mit:
      | Parameter | Wert       |
      | job_id    | test-123   |
      | status    | processing |
    Dann sollte der Job in MongoDB aktualisiert werden
    Und der neue Status sollte persistent sein
    Und started_at sollte automatisch gesetzt werden

  Szenario: UserRepository findet oder erstellt User
    Angenommen UserRepository wird verwendet
    Wenn find_or_create_user() aufgerufen wird für "newuser@gmail.com"
    Dann sollte entweder existierender User gefunden werden
    Oder ein neuer User sollte erstellt werden
    Und das User-Objekt sollte zurückgegeben werden

  Szenario: OAuthStateRepository validiert Token
    Angenommen ein State Token "valid-token" existiert in MongoDB
    Wenn validate_and_consume_state() aufgerufen wird
    Dann sollte die Validierung erfolgreich sein
    Und der Token sollte gelöscht werden (consumed)
    Und ein zweiter Aufruf sollte fehlschlagen (Already consumed)

  # =============================================================================
  # Szenario-Gruppe 8: Error Handling und Resilience
  # =============================================================================

  Szenario: Verbindungsfehler werden ordentlich behandelt
    Angenommen MongoDB läuft
    Aber die Verbindung wird während eines Requests unterbrochen
    Wenn ein Job-Update versucht wird
    Dann sollte eine geeignete Exception geworfen werden
    Und der Fehler sollte geloggt werden
    Aber der Service sollte nicht abstürzen

  Szenario: Duplizierte Job-ID wird verhindert
    Angenommen ein Job mit ID "duplicate-123" existiert
    Wenn versucht wird, einen weiteren Job mit derselben ID zu erstellen
    Dann sollte ein Duplicate-Key-Error auftreten
    Und der zweite Job sollte NICHT erstellt werden
    Und eine klare Fehlermeldung sollte zurückgegeben werden

  Szenario: Connection Pooling funktioniert
    Angenommen der Service läuft unter Last (100 concurrent requests)
    Wenn viele Job-Queries gleichzeitig ausgeführt werden
    Dann sollte Motor Connection Pooling genutzt werden
    Und es sollten nicht mehr als 100 Verbindungen geöffnet sein
    Und die Performance sollte stabil bleiben

  # =============================================================================
  # Szenario-Gruppe 9: Backward Compatibility
  # =============================================================================

  Szenario: Alte Jobs ohne neue Felder funktionieren
    Angenommen ein Job wurde vor einem Schema-Update gespeichert
    Und der Job hat kein "events" Feld
    Wenn der Job aus MongoDB geladen wird
    Dann sollte Pydantic default_factory das Feld initialisieren
    Und job.events sollte [] sein
    Und es sollte kein Fehler auftreten

  Szenario: Migration von In-Memory zu MongoDB
    Angenommen der Service lief zuvor ohne MongoDB
    Und einige Jobs existieren nur im RAM
    Wenn der Service mit MongoDB neu gestartet wird
    Dann sollten die RAM-Jobs verloren gehen (erwartet)
    Aber neue Jobs sollten in MongoDB gespeichert werden
    Und der Service sollte normal funktionieren

  # =============================================================================
  # Szenario-Gruppe 10: Multi-Instance Deployment
  # =============================================================================

  Szenario: Zwei Instanzen teilen sich dieselbe MongoDB
    Angenommen Instance A und Instance B laufen parallel
    Und beide sind mit derselben MongoDB verbunden
    Wenn Instance A einen Job erstellt
    Dann sollte Instance B den Job in MongoDB sehen
    Und beide Instanzen sollten auf denselben Job-Status zugreifen können

  Szenario: Job-Updates von verschiedenen Instanzen
    Angenommen Instance A erstellt Job "shared-job"
    Und Instance B verarbeitet den Job
    Wenn Instance B den Status auf "completed" setzt
    Dann sollte Instance A den neuen Status in MongoDB sehen
    Und beide Instanzen sollten konsistente Daten haben

  Szenario: OAuth State funktioniert über Instanzen hinweg
    Angenommen Instance A generiert OAuth State "cross-instance-token"
    Wenn der User OAuth-Callback zu Instance B geleitet wird
    Dann sollte Instance B den Token in MongoDB finden
    Und die Authentifizierung sollte erfolgreich sein
    # Dies ist der Hauptgrund für MongoDB bei OAuth
