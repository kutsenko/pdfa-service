# Nginx Reverse Proxy mit Basic Authentication

**Dokumentation in anderen Sprachen**: [English](README.md)

Dieses Beispiel zeigt, wie der PDF/A-Konvertierungsdienst hinter einem Nginx Reverse Proxy mit HTTP Basic Authentication für sichere Zugriffskontrolle betrieben wird.

## Features

- **Basic Authentication**: Schützt den Dienst mit Benutzername/Passwort-Authentifizierung
- **Reverse Proxy**: Nginx leitet Anfragen an das pdfa-service Backend weiter
- **Security Header**: Fügt Standard-Sicherheitsheader hinzu (X-Frame-Options, X-Content-Type-Options, etc.)
- **Große Dateien**: Konfiguriert für maximal 100MB Upload-Größe
- **Erweiterte Timeouts**: Ermöglicht lange OCR-Operationen (bis zu 5 Minuten)
- **Health Check Endpoint**: Monitoring-Endpunkt ohne Authentifizierung
- **Vollständige Isolation**: pdfa-service nur über nginx erreichbar (kein direkter Zugriff)

## Architektur

```
Internet/Netzwerk
      ↓
   Port 8080 (nginx)
      ↓
  Basic Auth Prüfung
      ↓
  Nginx Reverse Proxy
      ↓
  pdfa-service:8000 (nur internes Netzwerk)
```

## Schnellstart

### 1. Passwort-Datei erstellen

Erstellen Sie zunächst Ihre `.htpasswd`-Datei mit Benutzer-Zugangsdaten:

**Option A: Mit htpasswd (empfohlen)**
```bash
# Installieren Sie apache2-utils (Debian/Ubuntu)
sudo apt-get install apache2-utils

# Erstellen Sie .htpasswd mit erstem Benutzer
htpasswd -c htpasswd/.htpasswd admin

# Weitere Benutzer hinzufügen (ohne -c Flag)
htpasswd htpasswd/.htpasswd user2
```

**Option B: Mit openssl**
```bash
# Passwort erstellen und zu .htpasswd hinzufügen
echo "admin:$(openssl passwd -apr1)" > htpasswd/.htpasswd
```

**Option C: Beispiel-Datei kopieren**
```bash
# Beispiel-Datei mit Standard-Zugangsdaten verwenden (admin/changeme)
# WARNUNG: Passwort in Produktion sofort ändern!
cp htpasswd/.htpasswd.example htpasswd/.htpasswd
```

### 2. Dienste starten

```bash
# Aus diesem Verzeichnis
docker-compose up -d
```

### 3. Zugriff testen

```bash
# Ohne Authentifizierung (sollte mit 401 fehlschlagen)
curl http://localhost:8080/

# Mit Authentifizierung
curl -u admin:ihrpasswort http://localhost:8080/

# Konvertierungs-Endpunkt testen
curl -u admin:ihrpasswort \
  -F "file=@test.pdf" \
  -F "language=deu+eng" \
  -F "pdfa_level=2" \
  http://localhost:8080/convert \
  -o output.pdf
```

### 4. Web UI aufrufen

Öffnen Sie Ihren Browser und navigieren Sie zu:
```
http://localhost:8080/
```

Sie werden nach Benutzername und Passwort gefragt.

## Konfiguration

### Port ändern

Bearbeiten Sie `docker-compose.yml`:
```yaml
nginx:
  ports:
    - "80:80"  # Ändern Sie 8080 auf den gewünschten Port
```

### Upload-Größenlimit anpassen

Bearbeiten Sie `nginx.conf`:
```nginx
# Ändern Sie von 100M auf die gewünschte Größe
client_max_body_size 500M;
```

### Timeouts anpassen

Bearbeiten Sie `nginx.conf`:
```nginx
# Passen Sie Timeouts für sehr große Dateien oder langsame Verarbeitung an
proxy_connect_timeout 600s;
proxy_send_timeout 600s;
proxy_read_timeout 600s;
```

### PDF-Komprimierung konfigurieren

Bearbeiten Sie Umgebungsvariablen in `docker-compose.yml`:
```yaml
pdfa:
  environment:
    - PDFA_IMAGE_DPI=150          # Qualität anpassen
    - PDFA_JPG_QUALITY=85
    - PDFA_OPTIMIZE=1
```

Siehe [COMPRESSION.de.md](../../COMPRESSION.de.md) für detaillierte Dokumentation.

### Eigene Domain hinzufügen

1. Aktualisieren Sie `nginx.conf`:
```nginx
server {
    listen 80;
    server_name pdfa.ihredomain.de;  # Ändern Sie dies
    # ... Rest der Konfiguration
}
```

2. Aktualisieren Sie Ihr DNS, um auf den Server zu zeigen
3. Erwägen Sie SSL/TLS hinzuzufügen (siehe SSL-Setup unten)

## SSL/TLS Setup (HTTPS)

Für Produktivbetrieb sollten Sie SSL/TLS-Verschlüsselung hinzufügen:

### Option 1: Let's Encrypt mit Certbot

```bash
# Installieren Sie certbot
sudo apt-get install certbot python3-certbot-nginx

# Zertifikat generieren
sudo certbot --nginx -d pdfa.ihredomain.de

# Certbot aktualisiert nginx.conf automatisch
```

### Option 2: Manuelle SSL-Konfiguration

1. SSL-Zertifikate beziehen (von Ihrer CA oder Let's Encrypt)

2. Aktualisieren Sie `nginx.conf`:
```nginx
server {
    listen 443 ssl http2;
    server_name pdfa.ihredomain.de;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... Rest der Konfiguration
}

# HTTP zu HTTPS umleiten
server {
    listen 80;
    server_name pdfa.ihredomain.de;
    return 301 https://$server_name$request_uri;
}
```

3. Zertifikate in `docker-compose.yml` einbinden:
```yaml
nginx:
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
    - ./htpasswd/.htpasswd:/etc/nginx/.htpasswd:ro
    - ./ssl:/etc/nginx/ssl:ro  # SSL-Zertifikate hinzufügen
```

## Benutzerverwaltung

### Neuen Benutzer hinzufügen

```bash
htpasswd htpasswd/.htpasswd neuerbenutzer
```

### Benutzer entfernen

Bearbeiten Sie `htpasswd/.htpasswd` und entfernen Sie die Zeile des Benutzers.

### Passwort ändern

```bash
htpasswd htpasswd/.htpasswd existierenderbenutzer
```

### Benutzer auflisten

```bash
cut -d: -f1 htpasswd/.htpasswd
```

## Monitoring und Logs

### Logs anzeigen

```bash
# Nginx Access-Logs
docker-compose logs -f nginx

# pdfa-service Logs
docker-compose logs -f pdfa

# Beide Dienste
docker-compose logs -f
```

### Health Check

Nginx enthält einen Health-Check-Endpunkt (keine Authentifizierung erforderlich):

```bash
curl http://localhost:8080/health
# Sollte zurückgeben: healthy
```

Verwenden Sie diesen Endpunkt für Monitoring-Tools (Prometheus, Nagios, etc.).

## Sicherheitsempfehlungen

1. **Standard-Zugangsdaten ändern**: Niemals die Beispiel-`.htpasswd` in Produktion verwenden
2. **Starke Passwörter verwenden**: Sichere Passwörter für alle Benutzer generieren
3. **HTTPS aktivieren**: Immer SSL/TLS in Produktionsumgebungen verwenden
4. **Upload-Größe begrenzen**: `client_max_body_size` an Ihre Bedürfnisse anpassen
5. **Regelmäßige Updates**: Nginx und pdfa-service Docker-Images aktuell halten
6. **Firewall**: Nur Port 80/443 freigeben, direkten Zugriff auf Port 8000 blockieren
7. **Log-Monitoring**: Nginx Access-Logs regelmäßig auf verdächtige Aktivitäten überprüfen

## Fehlerbehebung

### 401 Unauthorized Fehler

- Prüfen Sie, dass `.htpasswd`-Datei existiert: `ls -la htpasswd/.htpasswd`
- Prüfen Sie Dateiberechtigungen: `chmod 644 htpasswd/.htpasswd`
- Testen Sie Zugangsdaten manuell
- Prüfen Sie nginx-Logs: `docker-compose logs nginx`

### 502 Bad Gateway Fehler

- Stellen Sie sicher, dass pdfa-service läuft: `docker-compose ps`
- Prüfen Sie pdfa-service Logs: `docker-compose logs pdfa`
- Prüfen Sie Netzwerkverbindung: `docker-compose exec nginx ping pdfa`

### Upload Too Large Fehler (413)

- Erhöhen Sie `client_max_body_size` in `nginx.conf`
- Starten Sie nginx neu: `docker-compose restart nginx`

### Timeout-Fehler

- Erhöhen Sie Timeout-Werte in `nginx.conf`
- Prüfen Sie, ob Dateiverarbeitung zu lange dauert
- Überprüfen Sie pdfa-service Logs auf Fehler

### Connection Refused

- Prüfen Sie, ob Port bereits verwendet wird: `netstat -tuln | grep 8080`
- Prüfen Sie Docker-Netzwerk: `docker network ls`
- Stellen Sie sicher, dass beide Dienste im selben Netzwerk sind

## Produktions-Checkliste

- [ ] Eigene `.htpasswd` mit starken Passwörtern erstellt
- [ ] SSL/TLS-Zertifikate konfiguriert
- [ ] Eigene Domain konfiguriert
- [ ] Firewall-Regeln eingerichtet
- [ ] Upload-Größenlimits an Nutzung angepasst
- [ ] Komprimierungseinstellungen optimiert
- [ ] Log-Rotation konfiguriert
- [ ] Monitoring/Health-Checks eingerichtet
- [ ] Backup-Strategie für Konfigurationen
- [ ] Dokumentation für Ihr Team

## Dateien in diesem Beispiel

- `nginx.conf` - Nginx Reverse Proxy Konfiguration
- `docker-compose.yml` - Vollständiger Service-Stack
- `htpasswd/.htpasswd.example` - Beispiel-Passwort-Datei
- `htpasswd/.gitignore` - Schützt echte Zugangsdaten vor git
- `README.md` - Englische Dokumentation
- `README.de.md` - Diese Datei (Deutsch)

## Weiterführende Informationen

- [Nginx Dokumentation](https://nginx.org/en/docs/)
- [HTTP Basic Authentication](https://de.wikipedia.org/wiki/HTTP-Authentifizierung#Basic_Authentication)
- [Docker Compose Dokumentation](https://docs.docker.com/compose/)
- [pdfa-service Dokumentation](../../README.de.md)
- [Komprimierungs-Konfiguration](../../COMPRESSION.de.md)

## Support

Bei Problemen mit diesem Beispiel prüfen Sie:
1. Docker und Docker Compose sind korrekt installiert
2. Ports sind nicht bereits belegt
3. Dateiberechtigungen sind korrekt
4. Beide Dienste laufen

Bei pdfa-service Problemen siehe die [Haupt-README](../../README.de.md).
