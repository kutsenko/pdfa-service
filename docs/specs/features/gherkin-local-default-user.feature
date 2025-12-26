# language: de
Funktionalität: Lokaler Standardbenutzer für Non-Auth-Modus
  Als Benutzer des PDF/A-Service ohne OAuth-Integration
  möchte ich dass automatisch ein lokaler Standardbenutzer erstellt wird
  damit ich auf Features wie Job-Verlauf und persistente Speicherung zugreifen kann

  Hintergrund:
    Angenommen MongoDB ist verfügbar und erreichbar
    Und die Service-Umgebung ist korrekt konfiguriert

  # ============================================================================
  # 1. Service-Start und Default User-Erstellung
  # ============================================================================

  Szenario: Service startet mit deaktivierter Auth und erstellt Default User
    Angenommen die Umgebungsvariable AUTH_ENABLED ist "false"
    Und die Umgebungsvariable DEFAULT_USER_ID ist nicht gesetzt
    Wenn der Service gestartet wird
    Dann sollte ein Benutzer in der MongoDB users Collection existieren
    Und sollte der user_id "local-default" haben
    Und sollte der email "local@localhost" haben
    Und sollte der name "Local User" haben
    Und sollte login_count 1 sein
    Und sollte das Log "Default user ensured" enthalten

  Szenario: Service startet mit aktivierter Auth und erstellt KEINEN Default User
    Angenommen die Umgebungsvariable AUTH_ENABLED ist "true"
    Und die Umgebungsvariable GOOGLE_CLIENT_ID ist gesetzt
    Wenn der Service gestartet wird
    Dann sollte KEIN Benutzer mit user_id "local-default" in MongoDB existieren
    Und sollte das Log NICHT "Default user ensured" enthalten

  Szenario: Service startet mehrfach mit deaktivierter Auth (Idempotenz)
    Angenommen die Umgebungsvariable AUTH_ENABLED ist "false"
    Und der Service wurde bereits einmal gestartet
    Und ein Default User existiert in MongoDB mit login_count 1
    Wenn der Service neu gestartet wird
    Dann sollte NUR EIN Benutzer mit user_id "local-default" existieren
    Und sollte login_count inkrementiert sein (auf 2)
    Und sollte last_login_at aktualisiert sein

  # ============================================================================
  # 2. Konfigurierbare Standardbenutzer-Felder
  # ============================================================================

  Szenario: Default User mit benutzerdefinierten Werten aus Umgebungsvariablen
    Angenommen die Umgebungsvariable AUTH_ENABLED ist "false"
    Und die Umgebungsvariable DEFAULT_USER_ID ist "my-local-user"
    Und die Umgebungsvariable DEFAULT_USER_EMAIL ist "admin@example.com"
    Und die Umgebungsvariable DEFAULT_USER_NAME ist "Admin User"
    Wenn der Service gestartet wird
    Dann sollte ein Benutzer in MongoDB existieren mit:
      | Feld    | Wert                 |
      | user_id | my-local-user        |
      | email   | admin@example.com    |
      | name    | Admin User           |

  Szenario: Default User mit Teilweisen Custom-Werten
    Angenommen die Umgebungsvariable AUTH_ENABLED ist "false"
    Und die Umgebungsvariable DEFAULT_USER_ID ist "custom-id"
    Und DEFAULT_USER_EMAIL ist NICHT gesetzt
    Und DEFAULT_USER_NAME ist NICHT gesetzt
    Wenn der Service gestartet wird
    Dann sollte ein Benutzer in MongoDB existieren mit:
      | Feld    | Wert            |
      | user_id | custom-id       |
      | email   | local@localhost |
      | name    | Local User      |

  # ============================================================================
  # 3. Job-Attribution mit Default User
  # ============================================================================

  Szenario: Job-Erstellung via WebSocket verwendet Default User
    Angenommen die Umgebungsvariable AUTH_ENABLED ist "false"
    Und der Service läuft mit Default User "local-default"
    Und eine PDF-Datei "document.pdf" existiert
    Wenn ein Job via WebSocket /convert erstellt wird ohne Auth-Header
    Dann sollte der Job in MongoDB gespeichert werden
    Und sollte job.user_id "local-default" sein
    Und sollte job.status "completed" sein
    Und sollte job.created_at gesetzt sein

  Szenario: Job-Erstellung mit Custom Default User ID
    Angenommen die Umgebungsvariable AUTH_ENABLED ist "false"
    Und die Umgebungsvariable DEFAULT_USER_ID ist "admin"
    Und der Service läuft mit Default User "admin"
    Wenn ein Job via WebSocket erstellt wird
    Dann sollte job.user_id "admin" sein
    Und sollte der Job dem Default User zugeordnet sein

  Szenario: Job-Erstellung mit aktivierter Auth verwendet OAuth User
    Angenommen die Umgebungsvariable AUTH_ENABLED ist "true"
    Und ein OAuth-Benutzer "google-oauth2|123456" ist authentifiziert
    Wenn ein Job via WebSocket erstellt wird mit gültigem JWT
    Dann sollte job.user_id "google-oauth2|123456" sein
    Und sollte NICHT "local-default" sein

  # ============================================================================
  # 4. Job-Verlauf-Abfrage
  # ============================================================================

  Szenario: Job-Verlauf-Abfrage gibt Jobs des Default Users zurück
    Angenommen die Umgebungsvariable AUTH_ENABLED ist "false"
    Und der Default User "local-default" hat 3 Jobs erstellt
    Und die Job-IDs sind "job-1", "job-2", "job-3"
    Wenn GET /api/v1/jobs/history aufgerufen wird ohne Auth-Header
    Dann sollte die Response Status 200 haben
    Und sollten 3 Jobs zurückgegeben werden
    Und sollten alle Jobs user_id "local-default" haben
    Und sollten die Jobs nach created_at sortiert sein (neueste zuerst)

  Szenario: Job-Verlauf ist leer für neuen Default User
    Angenommen die Umgebungsvariable AUTH_ENABLED ist "false"
    Und der Default User "local-default" existiert
    Und der Default User hat noch keine Jobs erstellt
    Wenn GET /api/v1/jobs/history aufgerufen wird
    Dann sollte die Response Status 200 haben
    Und sollte die jobs-Liste leer sein

  Szenario: Job-Verlauf mit Custom Default User
    Angenommen die Umgebungsvariable AUTH_ENABLED ist "false"
    Und die Umgebungsvariable DEFAULT_USER_ID ist "my-user"
    Und der Default User "my-user" hat 5 Jobs erstellt
    Wenn GET /api/v1/jobs/history aufgerufen wird
    Dann sollten alle 5 Jobs user_id "my-user" haben
    Und sollten KEINE Jobs mit user_id "local-default" zurückgegeben werden

  # ============================================================================
  # 5. Dependency Injection: get_current_user_optional()
  # ============================================================================

  Szenario: get_current_user_optional() gibt Default User bei deaktivierter Auth
    Angenommen die Umgebungsvariable AUTH_ENABLED ist "false"
    Und auth_config.default_user_id ist "local-default"
    Wenn get_current_user_optional() aufgerufen wird
    Dann sollte ein User-Objekt zurückgegeben werden (nicht None)
    Und sollte user.user_id "local-default" sein
    Und sollte user.email "local@localhost" sein
    Und sollte user.name "Local User" sein
    Und sollte user.picture None sein

  Szenario: get_current_user_optional() gibt OAuth User bei aktivierter Auth
    Angenommen die Umgebungsvariable AUTH_ENABLED ist "true"
    Und ein gültiges JWT für User "oauth-user-123" ist vorhanden
    Wenn get_current_user_optional() aufgerufen wird
    Dann sollte user.user_id "oauth-user-123" sein
    Und sollte NICHT "local-default" sein

  Szenario: get_current_user_optional() Fallback bei fehlender auth_config
    Angenommen auth_config ist None (Edge Case)
    Und AUTH_ENABLED ist nicht gesetzt
    Wenn get_current_user_optional() aufgerufen wird
    Dann sollte ein User-Objekt mit Hardcoded-Defaults zurückgegeben werden
    Und sollte user.user_id "local-default" sein
    Und sollte user.email "local@localhost" sein

  # ============================================================================
  # 6. Edge Cases und Error Handling
  # ============================================================================

  Szenario: MongoDB-Verbindungsfehler beim Start verhindert Service-Start
    Angenommen die Umgebungsvariable AUTH_ENABLED ist "false"
    Und MongoDB ist NICHT erreichbar
    Wenn der Service gestartet wird
    Dann sollte der Service-Start fehlschlagen
    Und sollte ein Fehler geloggt werden
    Und sollte KEIN Default User erstellt werden

  Szenario: Wechsel von Auth enabled→disabled erstellt Default User
    Angenommen der Service lief mit AUTH_ENABLED="true"
    Und KEIN Default User existiert in MongoDB
    Wenn AUTH_ENABLED auf "false" geändert wird
    Und der Service neu gestartet wird
    Dann sollte ein Default User erstellt werden
    Und sollte user_id "local-default" haben

  Szenario: Wechsel von Auth disabled→enabled verwendet KEINEN Default User mehr
    Angenommen der Service lief mit AUTH_ENABLED="false"
    Und ein Default User "local-default" existiert in MongoDB
    Wenn AUTH_ENABLED auf "true" geändert wird
    Und der Service neu gestartet wird
    Dann sollte KEIN neuer Default User erstellt werden
    Und sollte get_current_user_optional() den OAuth User zurückgeben
    Und sollte der alte Default User in MongoDB bleiben (harmlos)

  Szenario: Gelöschter Default User wird beim Neustart neu erstellt (Self-Healing)
    Angenommen die Umgebungsvariable AUTH_ENABLED ist "false"
    Und ein Default User existierte
    Und der Default User wurde manuell aus MongoDB gelöscht
    Wenn der Service neu gestartet wird
    Dann sollte der Default User neu erstellt werden
    Und sollte login_count 1 sein (frischer Start)

  # ============================================================================
  # 7. Vollständige Integration-Workflows
  # ============================================================================

  Szenario: Kompletter Workflow ohne Auth - Service Start bis Job-Verlauf
    Angenommen die Umgebungsvariable AUTH_ENABLED ist "false"
    Und MongoDB ist leer
    Wenn der Service gestartet wird
    Dann sollte ein Default User "local-default" erstellt werden
    Wenn eine PDF via WebSocket konvertiert wird
    Dann sollte der Job user_id "local-default" haben
    Wenn GET /api/v1/jobs/history aufgerufen wird
    Dann sollte der erstellte Job in der Response sein
    Und sollte die Response Status 200 haben

  Szenario: Multi-Instance-Deployment mit Default User
    Angenommen die Umgebungsvariable AUTH_ENABLED ist "false"
    Und 3 Service-Instanzen starten gleichzeitig
    Wenn alle Instanzen ensure_default_user() aufrufen
    Dann sollte NUR EIN Default User in MongoDB existieren
    Und sollte login_count 3 sein (3 Upserts)
    Und sollten keine Duplicate-Key-Errors auftreten

# ============================================================================
# Zusammenfassung
# ============================================================================
# Gesamt: 18 Szenarien in 7 Gruppen
# - Service-Start und Default User-Erstellung: 3 Szenarien
# - Konfigurierbare Standardbenutzer-Felder: 2 Szenarien
# - Job-Attribution mit Default User: 3 Szenarien
# - Job-Verlauf-Abfrage: 3 Szenarien
# - Dependency Injection: 3 Szenarien
# - Edge Cases und Error Handling: 4 Szenarien
# - Vollständige Integration-Workflows: 2 Szenarien (inkl. Multi-Instance)
