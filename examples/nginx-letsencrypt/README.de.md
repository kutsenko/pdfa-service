# Nginx Reverse Proxy mit Let's Encrypt SSL/TLS

**Dokumentation in anderen Sprachen**: [English](README.md)

Dieses Beispiel zeigt, wie der PDF/A-Konvertierungsdienst hinter einem Nginx Reverse Proxy mit automatischen SSL/TLS-Zertifikaten von Let's Encrypt über Certbot betrieben wird.

## Features

- **Automatisches SSL/TLS**: Kostenlose Zertifikate von Let's Encrypt
- **Auto-Erneuerung**: Certbot erneuert Zertifikate automatisch
- **HTTPS-Erzwingung**: HTTP-Traffic wird zu HTTPS umgeleitet
- **Moderne Sicherheit**: TLS 1.2+ mit starken Verschlüsselungen
- **Security-Header**: HSTS, CSP, X-Frame-Options, etc.
- **Große Dateien**: Konfiguriert für maximal 100MB Upload-Größe
- **Erweiterte Timeouts**: Ermöglicht lange OCR-Operationen
- **Produktionsbereit**: Vollständiges Setup für öffentlich zugängliche Deployments

## Architektur

```
Internet
  ↓
Port 80 (HTTP) → Umleitung zu HTTPS
Port 443 (HTTPS) ← Let's Encrypt SSL
  ↓
Nginx Reverse Proxy
  ↓
pdfa-service:8000 (internes Netzwerk)
  ↑
Certbot (automatische Erneuerung alle 12h)
```

## Voraussetzungen

1. **Domainnamen**: Sie benötigen eine Domain, die auf Ihren Server zeigt
   - Beispiel: `doc.example.com`
   - DNS A-Record muss auf die IP-Adresse Ihres Servers zeigen

2. **Öffentlicher Server**: Muss aus dem Internet erreichbar sein
   - Ports 80 und 443 müssen offen sein
   - Let's Encrypt muss Domain-Besitz verifizieren können

3. **Docker & Docker Compose**: Installiert und lauffähig

## Schnellstart

### 1. Domain konfigurieren

Bearbeiten Sie `init-letsencrypt.sh` und aktualisieren Sie die Konfiguration:

```bash
# Ändern Sie dies auf Ihre tatsächliche Domain
domains=(doc.example.com)

# Fügen Sie Ihre E-Mail für Let's Encrypt Benachrichtigungen hinzu
email="admin@example.com"

# Staging-Modus für Tests verwenden (optional)
staging=0  # Auf 1 für Tests setzen, 0 für Produktion
```

Aktualisieren Sie auch `nginx.conf` - ersetzen Sie alle Vorkommen von `doc.example.com` mit Ihrer Domain:

```bash
# Schnelles Ersetzen (Linux/macOS)
sed -i 's/doc\.example\.com/ihredomain.de/g' nginx.conf

# Oder bearbeiten Sie nginx.conf manuell und ändern Sie:
# server_name doc.example.com;
# ssl_certificate /etc/letsencrypt/live/doc.example.com/...
```

### 2. Let's Encrypt initialisieren

Führen Sie das Initialisierungs-Skript aus:

```bash
./init-letsencrypt.sh
```

Das Skript wird:
1. Empfohlene TLS-Parameter herunterladen
2. Ein Dummy-Zertifikat erstellen
3. nginx starten
4. Echtes Zertifikat von Let's Encrypt anfordern
5. nginx mit dem echten Zertifikat neu laden

**Hinweis**: Beim ersten Durchlauf sollten Sie `staging=1` verwenden, um Ihr Setup zu testen und Rate Limits zu vermeiden.

### 3. Setup überprüfen

```bash
# Prüfen, ob alle Container laufen
docker-compose ps

# Zertifikat prüfen
docker-compose exec nginx ls -la /etc/letsencrypt/live/

# HTTPS-Zugriff testen
curl https://ihredomain.de/health
```

### 4. Auf Ihren Dienst zugreifen

Öffnen Sie Ihren Browser und navigieren Sie zu:
```
https://ihredomain.de
```

Sie sollten ein gültiges SSL-Zertifikat und die pdfa-service Web-UI sehen.

## Konfiguration

### Domain ändern

1. Aktualisieren Sie `init-letsencrypt.sh`:
   ```bash
   domains=(ihre-domain.de www.ihre-domain.de)
   ```

2. Aktualisieren Sie `nginx.conf`:
   ```nginx
   server_name ihre-domain.de www.ihre-domain.de;
   ssl_certificate /etc/letsencrypt/live/ihre-domain.de/fullchain.pem;
   ssl_certificate_key /etc/letsencrypt/live/ihre-domain.de/privkey.pem;
   ```

3. Führen Sie die Initialisierung erneut aus:
   ```bash
   ./init-letsencrypt.sh
   ```

### Mehrere Domains

Sie können mehrere Domains mit einem einzigen Setup absichern:

```bash
# In init-letsencrypt.sh
domains=(doc.example.com pdf.example.com)
```

Jede Domain benötigt:
- Separaten `server`-Block in nginx.conf
- DNS A-Record, der auf Ihren Server zeigt

### Upload-Größenlimit anpassen

Bearbeiten Sie `nginx.conf`:
```nginx
# Ändern Sie von 100M auf die gewünschte Größe
client_max_body_size 500M;
```

Dann nginx neu laden:
```bash
docker-compose exec nginx nginx -s reload
```

### Timeouts anpassen

Bearbeiten Sie `nginx.conf`:
```nginx
# Für sehr große Dateien oder langsame Verarbeitung anpassen
proxy_connect_timeout 600s;
proxy_send_timeout 600s;
proxy_read_timeout 600s;
```

### PDF-Komprimierung konfigurieren

Bearbeiten Sie Umgebungsvariablen in `docker-compose.yml`:
```yaml
pdfa:
  environment:
    - PDFA_IMAGE_DPI=150
    - PDFA_JPG_QUALITY=85
    - PDFA_OPTIMIZE=1
```

Siehe [COMPRESSION.de.md](../../COMPRESSION.de.md) für detaillierte Dokumentation.

## Zertifikatsverwaltung

### Automatische Erneuerung

Der Certbot-Container prüft automatisch alle 12 Stunden auf Erneuerung. Kein manuelles Eingreifen erforderlich.

### Manuelle Erneuerung

Zertifikatserneuerung erzwingen:

```bash
docker-compose run --rm certbot renew
docker-compose exec nginx nginx -s reload
```

### Zertifikatsablauf prüfen

```bash
docker-compose run --rm certbot certificates
```

### Zertifikat widerrufen

```bash
docker-compose run --rm certbot revoke \
  --cert-path /etc/letsencrypt/live/ihredomain.de/cert.pem
```

## Testen mit Staging

Let's Encrypt hat Rate Limits (50 Zertifikate pro Domain pro Woche). Verwenden Sie Staging-Modus zum Testen:

1. Setzen Sie `staging=1` in `init-letsencrypt.sh`
2. Führen Sie `./init-letsencrypt.sh` aus
3. Browser zeigt Zertifikatswarnung (erwartet)
4. Sobald bestätigt funktioniert, setzen Sie `staging=0`
5. Führen Sie `./init-letsencrypt.sh` erneut aus für Produktionszertifikat

## Fehlerbehebung

### Zertifikatsanforderung fehlgeschlagen

**Problem**: Certbot kann kein Zertifikat erhalten

**Lösungen**:
- DNS A-Record prüfen: `dig ihredomain.de`
- Ports 80 und 443 prüfen: `netstat -tuln | grep -E '80|443'`
- Domain-Erreichbarkeit prüfen: `curl http://ihredomain.de/.well-known/acme-challenge/test`
- Certbot-Logs prüfen: `docker-compose logs certbot`

### nginx startet nicht

**Problem**: nginx startet nach Zertifikatsinstallation nicht

**Lösungen**:
- nginx-Konfigurationssyntax prüfen: `docker-compose exec nginx nginx -t`
- Zertifikatsdateien prüfen: `docker-compose exec nginx ls -la /etc/letsencrypt/live/`
- nginx-Logs prüfen: `docker-compose logs nginx`
- Domain-Namen in nginx.conf und Zertifikatspfad prüfen

### Browser zeigt Zertifikatsfehler

**Problem**: Browser zeigt "Nicht sicher" oder Zertifikatswarnung

**Lösungen**:
- Bei Staging-Modus ist dies erwartet (Staging-Zertifikate sind nicht vertrauenswürdig)
- Zertifikat für richtige Domain prüfen: `docker-compose run --rm certbot certificates`
- Gültigkeit der Zertifikatsdaten prüfen
- Browser-Cache leeren und erneut versuchen
- Produktionsmodus (`staging=0`) für vertrauenswürdige Zertifikate verwenden

### Rate Limit überschritten

**Problem**: Let's Encrypt Rate Limit erreicht

**Lösungen**:
- 7 Tage warten für Rate Limit Reset
- Staging-Modus für Tests verwenden
- Rate Limits prüfen: https://letsencrypt.org/de/docs/rate-limits/
- Wildcard-Zertifikate erwägen bei vielen Subdomains

### Zertifikat wird nicht erneuert

**Problem**: Automatische Erneuerung schlägt fehl

**Lösungen**:
- Certbot-Container läuft: `docker-compose ps`
- Erneuerung manuell testen: `docker-compose run --rm certbot renew --dry-run`
- Port 80 erreichbar (für Erneuerung erforderlich)
- Certbot-Logs prüfen: `docker-compose logs certbot`

## Sicherheitsempfehlungen

1. **Software aktuell halten**: Docker-Images regelmäßig aktualisieren
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

2. **Zertifikatsablauf überwachen**: Monitoring-Alerts einrichten
   - Let's Encrypt Zertifikate sind 90 Tage gültig
   - Auto-Erneuerung erfolgt 30 Tage vor Ablauf

3. **Firewall-Konfiguration**:
   - Nur Ports 80 und 443 öffnen
   - Direkten Zugriff auf Port 8000 blockieren
   - fail2ban für Brute-Force-Schutz verwenden

4. **HSTS-Konfiguration**: Bereits in nginx.conf aktiviert
   - Browser verwenden nach erstem Besuch nur noch HTTPS
   - Erwägen Sie Domain zur HSTS-Preload-Liste hinzuzufügen

5. **Regelmäßige Backups**: Zertifikatsdaten sichern
   ```bash
   tar -czf certbot-backup-$(date +%Y%m%d).tar.gz certbot/
   ```

6. **Security-Header**: Alle wichtigen Header sind konfiguriert
   - CSP-Policy für Ihre spezifischen Bedürfnisse prüfen
   - X-Frame-Options anpassen falls Einbettung benötigt

## Produktions-Checkliste

- [ ] Domain-DNS korrekt konfiguriert
- [ ] Ports 80 und 443 in Firewall geöffnet
- [ ] init-letsencrypt.sh mit Ihrer Domain und E-Mail konfiguriert
- [ ] nginx.conf mit Ihrem Domain-Namen aktualisiert
- [ ] Mit staging=1 zuerst getestet
- [ ] Produktionszertifikate erhalten (staging=0)
- [ ] Alle Dienste laufen: `docker-compose ps`
- [ ] HTTPS funktioniert: `curl https://ihredomain.de/health`
- [ ] HTTP leitet zu HTTPS um
- [ ] Zertifikats-Auto-Erneuerung getestet
- [ ] Upload-Größenlimits konfiguriert
- [ ] Komprimierungseinstellungen optimiert
- [ ] Monitoring/Alerts eingerichtet
- [ ] Backup-Strategie implementiert

## Dateien in diesem Beispiel

- `nginx.conf` - Nginx Reverse Proxy Konfiguration mit SSL/TLS
- `docker-compose.yml` - Vollständiger Service-Stack (nginx, pdfa, certbot)
- `init-letsencrypt.sh` - Zertifikats-Initialisierungs-Skript
- `README.md` - Englische Dokumentation
- `README.de.md` - Diese Datei (Deutsch)

## Verzeichnisstruktur nach Setup

```
nginx-letsencrypt/
├── certbot/
│   ├── conf/
│   │   ├── live/
│   │   │   └── ihredomain.de/
│   │   │       ├── fullchain.pem
│   │   │       └── privkey.pem
│   │   ├── options-ssl-nginx.conf
│   │   └── ssl-dhparams.pem
│   └── www/
│       └── .well-known/
├── docker-compose.yml
├── init-letsencrypt.sh
├── nginx.conf
└── README.md
```

## Migration von HTTP zu HTTPS

Falls Sie ein bestehendes HTTP-Deployment aktualisieren:

1. Alle Daten sichern
2. DNS aktualisieren (falls nötig)
3. `./init-letsencrypt.sh` ausführen
4. Gründlich testen
5. API-Clients auf HTTPS-URLs aktualisieren

## Weiterführende Informationen

- [Let's Encrypt Dokumentation](https://letsencrypt.org/de/docs/)
- [Certbot Dokumentation](https://certbot.eff.org/docs/)
- [Nginx SSL Konfiguration](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [pdfa-service Dokumentation](../../README.de.md)
- [Komprimierungs-Konfiguration](../../COMPRESSION.de.md)

## Support

Bei Problemen mit diesem Beispiel:
1. DNS korrekt konfiguriert prüfen
2. Ports 80 und 443 erreichbar prüfen
3. Certbot und nginx Logs überprüfen
4. Zuerst mit Staging-Modus testen

Bei pdfa-service Problemen siehe die [Haupt-README](../../README.de.md).

## Credits

Basiert auf dem ausgezeichneten [nginx-certbot](https://github.com/wmnnd/nginx-certbot) Projekt von Philipp Schmieder.
