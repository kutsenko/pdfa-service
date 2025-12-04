# pdfa-service Beispiele

**Dokumentation in anderen Sprachen**: [English](README.md)

Dieses Verzeichnis enthält gebrauchsfertige Konfigurationsbeispiele und Deployment-Szenarien für den pdfa-service.

## Verfügbare Beispiele

### 🔒 [Nginx Reverse Proxy mit Basic Auth](nginx-reverse-proxy/)

Betreiben Sie pdfa-service hinter einem Nginx Reverse Proxy mit HTTP Basic Authentication für sichere Zugriffskontrolle.

**Features:**
- HTTP Basic Authentication mit Benutzername/Passwort
- SSL/TLS-fertige Konfiguration
- Security-Header (X-Frame-Options, CSP, etc.)
- Unterstützung für große Datei-Uploads (konfigurierbar bis 500MB+)
- Erweiterte Timeouts für lange OCR-Operationen
- Health-Check-Endpunkt für Monitoring
- Vollständige Isolation (pdfa-service nicht direkt erreichbar)

**Anwendungsfälle:**
- Produktiv-Deployment mit Zugriffskontrolle
- Interner Firmen-Dokumentenverarbeitungsdienst
- Gemeinsame Team-Ressource mit Benutzerverwaltung
- Internet-zugänglicher Service mit Authentifizierung

**Dateien:**
- `nginx.conf` - Vollständige Nginx-Konfiguration
- `docker-compose.yml` - Multi-Container-Setup
- `htpasswd/.htpasswd.example` - Passwort-Datei-Vorlage
- `README.md` / `README.de.md` - Detaillierte Einrichtungsanleitung

[→ Zum Nginx Reverse Proxy Beispiel](nginx-reverse-proxy/)

---

### 🔐 [Nginx Reverse Proxy mit Let's Encrypt SSL/TLS](nginx-letsencrypt/)

Betreiben Sie pdfa-service mit automatischen SSL/TLS-Zertifikaten von Let's Encrypt über Certbot für produktionsreifes HTTPS.

**Features:**
- Automatische SSL/TLS-Zertifikate von Let's Encrypt
- Automatische Zertifikatserneuerung alle 12 Stunden
- HTTPS-Erzwingung (HTTP zu HTTPS Umleitung)
- Modernes TLS 1.2/1.3 mit starken Verschlüsselungen
- Security-Header (HSTS, CSP, X-Frame-Options, etc.)
- Unterstützung für große Datei-Uploads (konfigurierbar bis 500MB+)
- Erweiterte Timeouts für lange OCR-Operationen
- Produktionsreites öffentlich zugängliches Deployment

**Anwendungsfälle:**
- Öffentlich zugänglicher PDF-Konvertierungsdienst
- Produktiv-Deployment mit gültigen SSL-Zertifikaten
- Professioneller Dokumentenverarbeitungsdienst
- Internet-zugänglicher Service mit Verschlüsselung

**Dateien:**
- `nginx.conf` - Nginx-Konfiguration mit SSL/TLS
- `docker-compose.yml` - Multi-Container-Setup (nginx, pdfa, certbot)
- `init-letsencrypt.sh` - Zertifikats-Initialisierungs-Skript
- `README.md` / `README.de.md` - Detaillierte Einrichtungsanleitung

**Voraussetzungen:**
- Domainname (z.B. doc.example.com)
- Öffentlicher Server mit Ports 80 und 443 erreichbar
- DNS A-Record, der auf Ihren Server zeigt

[→ Zum Let's Encrypt SSL/TLS Beispiel](nginx-letsencrypt/)

---

## Beispiele beitragen

Haben Sie ein nützliches Deployment-Szenario oder eine Konfiguration? Wir freuen uns über Beiträge!

### Beispiel-Ideen

- **Load Balancer**: Multi-Instanz pdfa-service mit Load Balancing
- **S3-Integration**: Automatischer Upload konvertierter PDFs zu S3
- **Kubernetes**: K8s-Deployment mit Ingress und Secrets
- **Traefik**: Alternativer Reverse Proxy mit Let's Encrypt
- **Monitoring**: Prometheus + Grafana Integration
- **Queue-System**: Redis/RabbitMQ für Hintergrundverarbeitung
- **API Gateway**: Kong oder ähnliches API-Management
- **Cloud-Deployments**: AWS ECS, Azure Container Instances, GCP Cloud Run

### Beitragsrichtlinien

1. Erstellen Sie ein neues Verzeichnis unter `examples/`
2. Fügen Sie vollständige, funktionierende Konfigurationsdateien hinzu
3. Fügen Sie bilinguale README hinzu (Englisch + Deutsch)
4. Testen Sie gründlich vor der Einreichung
5. Dokumentieren Sie alle Voraussetzungen und Abhängigkeiten
6. Fügen Sie wenn möglich eine docker-compose.yml hinzu
7. Fügen Sie einen Abschnitt zu Sicherheitsüberlegungen hinzu
8. Aktualisieren Sie diese Index-Datei

## Beispiel-Vorlagenstruktur

```
examples/
└── ihr-beispiel-name/
    ├── README.md              # Englische Dokumentation
    ├── README.de.md           # Deutsche Dokumentation
    ├── docker-compose.yml     # Vollständiges Setup
    ├── config/                # Konfigurationsdateien
    │   └── ...
    └── scripts/               # Hilfsskripte (optional)
        └── ...
```

## Beispiele testen

Vor der Verwendung eines Beispiels in Produktion:

1. **In Entwicklung testen**: Verwenden Sie zuerst eine Testumgebung
2. **Sicherheit überprüfen**: Prüfen Sie Authentifizierung, Firewall-Regeln, SSL/TLS
3. **Limits anpassen**: Konfigurieren Sie Upload-Größen, Timeouts für Ihre Bedürfnisse
4. **Performance überwachen**: Testen Sie mit realistischen Dateigrößen und -volumina
5. **Zugangsdaten aktualisieren**: Ändern Sie alle Standard-Passwörter
6. **Konfigurationen sichern**: Bewahren Sie Kopien funktionierender Konfigurationen auf

## Support

Bei Problemen mit spezifischen Beispielen:
1. Prüfen Sie die README des Beispiels auf Fehlerbehebung
2. Verifizieren Sie, dass alle Voraussetzungen erfüllt sind
3. Überprüfen Sie Docker und Docker Compose Logs
4. Testen Sie, ob der Basis-pdfa-service eigenständig funktioniert

Bei allgemeinen pdfa-service Problemen siehe die [Haupt-README](../README.de.md).

## Lizenz

Alle Beispiele werden unter der gleichen Lizenz wie pdfa-service bereitgestellt. Siehe [LICENSE](../LICENSE) für Details.
