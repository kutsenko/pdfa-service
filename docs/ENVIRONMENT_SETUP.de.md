# Umgebungskonfiguration

**Auch verfügbar auf:** [English](ENVIRONMENT_SETUP.md)

## Schnellstart

1. **Beispieldatei kopieren:**
   ```bash
   cp .env.example .env
   ```

2. **`.env` mit Ihrer Konfiguration bearbeiten**

3. **Service starten:**
   ```bash
   uvicorn pdfa.api:app --env-file .env
   ```

---

## Authentifizierung einrichten (Optional)

Der Service unterstützt optionale Google OAuth 2.0 Authentifizierung. Standardmäßig ist die Authentifizierung **deaktiviert**.

### Schritt 1: Authentifizierung aktivieren

In Ihrer `.env` Datei setzen:

```bash
PDFA_ENABLE_AUTH=true
```

### Schritt 2: Google OAuth Credentials erstellen

1. Gehen Sie zur [Google Cloud Console](https://console.cloud.google.com/)
2. Erstellen Sie ein neues Projekt oder wählen Sie ein bestehendes aus
3. Aktivieren Sie die **Google+ API**
4. Gehen Sie zu **Anmeldedaten** → **Anmeldedaten erstellen** → **OAuth 2.0-Client-ID**
5. OAuth-Zustimmungsbildschirm konfigurieren:
   - Nutzertyp: Intern (für Organisation) oder Extern (für öffentlich)
   - App-Name: "PDF/A Service" (oder Ihr bevorzugter Name)
   - Bereiche: Fügen Sie `openid`, `email`, `profile` hinzu
6. OAuth 2.0-Client-ID erstellen:
   - Anwendungstyp: **Webanwendung**
   - Name: "PDF/A Service"
   - Autorisierte Weiterleitungs-URIs:
     - Für lokal: `http://localhost:8000/auth/callback`
     - Für Produktion: `https://ihredomain.de/auth/callback`
7. Kopieren Sie die **Client-ID** und das **Clientgeheimnis**

### Schritt 3: JWT-Geheimschlüssel generieren

Generieren Sie einen sicheren Zufallsschlüssel (mindestens 32 Zeichen):

```bash
openssl rand -hex 32
```

Oder mit Python:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Schritt 4: `.env` Datei konfigurieren

Bearbeiten Sie Ihre `.env` Datei mit den Werten aus Schritt 2 und 3:

```bash
# Authentifizierung aktivieren
PDFA_ENABLE_AUTH=true

# Google OAuth Credentials (aus Schritt 2)
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-AbCdEfGhIjKlMnOpQrStUvWxYz

# JWT-Geheimnis (aus Schritt 3)
JWT_SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2

# OAuth Weiterleitungs-URI (muss mit Google Console übereinstimmen)
REDIRECT_URI=http://localhost:8000/auth/callback

# Optional: JWT-Konfiguration
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24
```

### Schritt 5: Konfiguration überprüfen

Starten Sie den Service und prüfen Sie die Logs:

```bash
uvicorn pdfa.api:app --env-file .env --reload
```

Sie sollten sehen:
```
INFO:     Authentication ENABLED - Google OAuth + JWT
```

Wenn die Authentifizierung deaktiviert ist, sehen Sie:
```
INFO:     Authentication DISABLED (PDFA_ENABLE_AUTH=false)
```

---

## Konfigurationsreferenz

### Authentifizierungsparameter

| Parameter | Erforderlich | Standard | Beschreibung |
|-----------|--------------|----------|--------------|
| `PDFA_ENABLE_AUTH` | Nein | `false` | Authentifizierung aktivieren/deaktivieren (`true`/`false`) |
| `GOOGLE_CLIENT_ID` | Ja* | - | Google OAuth 2.0 Client-ID |
| `GOOGLE_CLIENT_SECRET` | Ja* | - | Google OAuth 2.0 Clientgeheimnis |
| `JWT_SECRET_KEY` | Ja* | - | Geheimer Schlüssel für JWT-Signierung (min 32 Zeichen) |
| `JWT_ALGORITHM` | Nein | `HS256` | JWT-Algorithmus (`HS256`, `HS384`, `HS512`) |
| `JWT_EXPIRY_HOURS` | Nein | `24` | JWT-Token Ablaufzeit in Stunden |
| `REDIRECT_URI` | Nein | `http://localhost:8000/auth/callback` | OAuth Weiterleitungs-URI |

\* Nur erforderlich wenn `PDFA_ENABLE_AUTH=true`

### Service-Parameter

| Parameter | Erforderlich | Standard | Beschreibung |
|-----------|--------------|----------|--------------|
| `HOST` | Nein | `0.0.0.0` | Server-Host-Adresse |
| `PORT` | Nein | `8000` | Server-Port |
| `LOG_LEVEL` | Nein | `INFO` | Logging-Level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## Sicherheits-Best-Practices

### JWT-Geheimschlüssel

✅ **TUN:**
- Generieren Sie einen **zufälligen** Geheimschlüssel (min 32 Zeichen)
- Verwenden Sie `openssl rand -hex 32` oder ähnlich
- Halten Sie den Geheimschlüssel **vertraulich**
- Verwenden Sie unterschiedliche Schlüssel für Entwicklung/Produktion
- Speichern Sie in Umgebungsvariablen oder Secret-Management

❌ **NICHT TUN:**
- Vorhersehbare Werte wie "secret" oder "password" verwenden
- Geheimschlüssel in Git committen
- Geheimschlüssel öffentlich teilen
- Denselben Schlüssel projektübergreifend verwenden

### OAuth-Credentials

✅ **TUN:**
- Clientgeheimnis vertraulich behandeln
- Unterschiedliche OAuth-Apps für Dev/Prod verwenden
- Autorisierte Weiterleitungs-URIs einschränken
- Credentials regelmäßig rotieren
- Internen Nutzertyp für Organisationen verwenden

❌ **NICHT TUN:**
- OAuth-Geheimnisse in Git committen
- Credentials öffentlich teilen
- Produktions-Credentials in Entwicklung verwenden

### Produktions-Deployment

Für Produktions-Deployments:

1. **HTTPS verwenden** für alle Weiterleitungs-URIs
2. **CORS-Einschränkungen** aktivieren
3. **Umgebungsspezifische** OAuth-Apps verwenden
4. **Secrets regelmäßig rotieren**
5. **Authentifizierungs-Logs überwachen**
6. **Redis/Datenbank verwenden** für OAuth State-Storage (nicht In-Memory)

---

## Setup testen

### 1. Test ohne Authentifizierung (Standard)

```bash
# .env Datei:
PDFA_ENABLE_AUTH=false

# Server starten
uvicorn pdfa.api:app --env-file .env

# API testen (keine Auth erforderlich)
curl http://localhost:8000/health
# → {"status":"healthy"}
```

### 2. Test mit Authentifizierung

```bash
# .env Datei:
PDFA_ENABLE_AUTH=true
GOOGLE_CLIENT_ID=ihre-client-id
GOOGLE_CLIENT_SECRET=ihr-geheimnis
JWT_SECRET_KEY=ihr-jwt-geheimnis

# Server starten
uvicorn pdfa.api:app --env-file .env

# Browser öffnen
open http://localhost:8000

# "Mit Google anmelden" klicken
# Nach Login sollten Sie die Upload-Oberfläche sehen
```

### 3. API-Authentifizierung testen

```bash
# Token über Web-UI-Login erhalten, dann:
curl http://localhost:8000/convert \
  -H "Authorization: Bearer IHR_JWT_TOKEN" \
  -F "file=@test.pdf"
```

---

## Fehlerbehebung

### Fehler "Invalid state parameter"

**Ursache:** OAuth-State nicht zwischen Anfragen persistiert (in neuester Version behoben)

**Lösung:** Auf neueste Version mit Module-Level State-Storage aktualisieren

### Fehler "GOOGLE_CLIENT_ID is required"

**Ursache:** Authentifizierung aktiviert aber Credentials nicht konfiguriert

**Lösung:**
1. Prüfen Sie, ob `.env` Datei existiert und geladen wird
2. Verifizieren Sie, dass `GOOGLE_CLIENT_ID` in `.env` gesetzt ist
3. Stellen Sie sicher, dass `.env` im Arbeitsverzeichnis liegt

### Fehler "JWT_SECRET_KEY must be at least 32 characters"

**Ursache:** JWT-Geheimnis zu kurz

**Lösung:** Längeres Geheimnis generieren:
```bash
openssl rand -hex 32
```

### Fehler "redirect_uri_mismatch"

**Ursache:** Weiterleitungs-URI stimmt nicht zwischen `.env` und Google Console überein

**Lösung:**
1. Prüfen Sie `REDIRECT_URI` in `.env`
2. Verifizieren Sie, dass es exakt in der Google Cloud Console übereinstimmt
3. Stellen Sie sicher, dass das Protokoll (http/https) übereinstimmt

### Authentifizierung funktioniert nicht

**Debug-Schritte:**
1. Prüfen Sie Server-Logs beim Start
2. Verifizieren Sie `PDFA_ENABLE_AUTH=true` in `.env`
3. Testen Sie `/auth/login` Endpoint manuell
4. Prüfen Sie Browser-Konsole auf Fehler
5. Verifizieren Sie, dass OAuth-App in Google Console aktiviert ist

---

## Beispiel `.env` Dateien

### Entwicklung (ohne Auth)

```bash
PDFA_ENABLE_AUTH=false
LOG_LEVEL=DEBUG
```

### Entwicklung (mit Auth)

```bash
PDFA_ENABLE_AUTH=true
GOOGLE_CLIENT_ID=123456-dev.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-dev-secret
JWT_SECRET_KEY=dev-secret-key-abcdef1234567890abcdef1234567890
REDIRECT_URI=http://localhost:8000/auth/callback
LOG_LEVEL=DEBUG
```

### Produktion

```bash
PDFA_ENABLE_AUTH=true
GOOGLE_CLIENT_ID=123456-prod.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=${GOOGLE_SECRET_FROM_VAULT}
JWT_SECRET_KEY=${JWT_SECRET_FROM_VAULT}
REDIRECT_URI=https://pdfa.ihredomain.de/auth/callback
JWT_EXPIRY_HOURS=12
LOG_LEVEL=INFO
```

---

## Zusätzliche Ressourcen

- [Google OAuth 2.0 Dokumentation](https://developers.google.com/identity/protocols/oauth2)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Projekt SECURITY.md](../SECURITY.md)
