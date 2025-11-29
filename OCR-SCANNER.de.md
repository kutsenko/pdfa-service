# OCR-Dokumentenscanner Anleitung

pdfa-service als Dokumentenscanner mit integrierter OCR zur Digitalisierung von physischen Dokumenten verwenden.

**English Version**: [English](OCR-SCANNER.md)

## Überblick

Diese Anleitung zeigt, wie man pdfa-service als OCR-Dokumentenscanner in einer lokalen Netzwerkumgebung einrichtet. Konvertieren Sie gescannte PDF-Dateien (von einem Scanner-Gerät oder Smartphone-App) in durchsuchbare, archivierbare PDF/A-Dokumente mit optischer Zeichenerkennung (OCR).

## Use-Case-Szenario

**Szenario**: Ein kleines Büro oder Heimatelier mit:
- Einem Dokumentenscanner oder Smartphone-Scann-Lösung
- Einem zentralen NAS/Speicher oder lokalem Netzwerk-Ordner
- Automatischer Konvertierung gescannter PDFs zu PDF/A mit OCR
- Zugriff über eine einfache Web-Oberfläche von jedem Netzwerkgerät
- Regelmäßige Batch-Verarbeitung von akkumulierten Scans

Dieses Setup eliminiert die Notwendigkeit für teure Dokumentenmanagementsoftware und bietet gleichzeitig ein professionelles PDF/A-Archivformat.

## Schnellstart mit Docker Compose

### Voraussetzungen

- **Docker** installiert (Version 20.10+)
- **Docker Compose** installiert (entweder Standalone oder Plugin Version 2.0+)
- **Netzwerkzugriff**: Gerät mit Scannfunktion und Netzwerkverbindung
- **Speicher**: USB-Laufwerk, NAS oder lokaler Ordner für Dateiaustausch

### Docker Compose Installation

Wählen Sie eine dieser Methoden:

**Option 1: Docker Compose Plugin (Empfohlen)**
```bash
# Teil von Docker Desktop oder separat installiert
docker compose version  # Überprüfen Sie die Installation
```

**Option 2: Standalone Docker Compose**
```bash
# Ältere Standalone-Version
docker-compose version  # Überprüfen Sie die Installation
```

Beide funktionieren identisch; diese Anleitung verwendet `docker compose` (Plugin-Version).

### Basis-Setup (x86_64 Linux / Windows mit Docker Desktop)

1. **Repository klonen**:

```bash
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service
```

2. **Service starten**:

```bash
# Docker Compose Plugin (empfohlen)
docker compose up -d

# Oder Standalone docker-compose
docker-compose up -d
```

Die API ist verfügbar unter `http://localhost:8000`

2. **Gescanntes PDF hochladen**:

```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@gescanntes_dokument.pdf;type=application/pdf" \
  -F "language=deu" \
  -F "pdfa_level=2" \
  --output digitalisiertes_dokument.pdf
```

3. **Zugriff vom Netzwerk**:

Ersetzen Sie `localhost` mit der IP-Adresse des Computers:

```bash
curl -X POST "http://192.168.1.100:8000/convert" \
  -F "file=@gescanntes_dokument.pdf;type=application/pdf" \
  --output digitalisiertes_dokument.pdf
```

## Installation nach Betriebssystem

### Linux (Ubuntu 22.04+ / Debian 12+)

#### Voraussetzungen

```bash
# Docker und Docker Compose installieren
sudo apt update
sudo apt install -y docker.io docker-compose

# Aktuellen Benutzer der docker-Gruppe hinzufügen (optional, um ohne sudo zu laufen)
sudo usermod -aG docker $USER
newgrp docker
```

#### Service starten

```bash
# Repository klonen
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service

# Mit Docker Compose Plugin starten (empfohlen)
docker compose up -d

# Oder mit Standalone docker-compose
docker-compose up -d

# Service-Status überprüfen
docker compose logs -f
# oder: docker-compose logs -f
```

Service verfügbar unter: `http://localhost:8000`

---

### Raspberry Pi Setup

**Empfohlen**: Raspberry Pi 4 mit 4GB+ RAM, 32GB+ SD-Karte

#### Überlegungen für Raspberry Pi

- **Architektur**: ARM64 (64-Bit-Betriebssystem erforderlich für OCR-Effizienz)
- **Betriebssystem**: Raspberry Pi OS (64-Bit) oder Ubuntu 22.04 LTS (ARM64)
- **Leistung**: OCR-Verarbeitung wird langsamer sein als x86_64 (30-60 Sekunden pro Seite)
- **Speicher**: Externes USB-SSD oder NAS für Dokumentenspeicherung verwenden

#### Installationsschritte

1. **Raspberry Pi OS 64-Bit installieren**:
   - Von [raspberrypi.com](https://www.raspberrypi.com/software/) herunterladen
   - Raspberry Pi Imager verwenden, um auf die SD-Karte zu schreiben

2. **System aktualisieren**:

```bash
sudo apt update && sudo apt upgrade -y
```

3. **Docker installieren**:

```bash
# Docker mit offiziellem Skript installieren
curl -fsSL https://get.docker.com | sh

# Pi-Benutzer zur docker-Gruppe hinzufügen
sudo usermod -aG docker pi

# Docker so konfigurieren, dass es beim Start ausgeführt wird
sudo systemctl enable docker
```

4. **Docker Compose installieren**:

```bash
# Für Raspberry Pi 4 (ARM64)
sudo apt install -y docker-compose

# Oder mit pip3 (Alternative)
sudo pip3 install docker-compose
```

5. **Für Raspberry Pi konfigurieren**:

Bearbeiten Sie `docker-compose.yml` und ändern Sie die Ressourcenlimits:

```yaml
services:
  pdfa:
    # ... vorhandene Konfiguration ...

    # Ressourcenlimits für Pi-Stabilität hinzufügen
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 1500M
        reservations:
          cpus: '0.5'
          memory: 512M
```

6. **Service starten**:

```bash
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service
docker compose up -d
# oder: docker-compose up -d
```

7. **Raspberry Pi IP-Adresse finden**:

```bash
hostname -I
# Ausgabe: 192.168.1.50
```

Zugriff von jedem Netzwerkgerät aus: `http://192.168.1.50:8000`

#### Leistungstipps für Raspberry Pi

- Dokumentieren Sie ein nacheinander (vermeiden Sie parallele Uploads)
- Verwenden Sie `--language deu`, wenn English OCR nicht benötigt wird (reduziert die Verarbeitungszeit)
- Erwägen Sie, OCR für bereits digitalisierte Dokumente zu deaktivieren: `ocr_enabled=false`
- Überwachen Sie den verfügbaren Speicherplatz; speichern Sie konvertierte PDFs auf externem SSD/NAS

---

### Windows 10/11 Setup

#### Option A: Verwendung von WSL2 (Windows Subsystem for Linux)

**Vorteile**: Native Docker-Leistung, Linux-Umgebung

1. **WSL2 aktivieren**:

```powershell
# PowerShell als Administrator ausführen
wsl --install
wsl --set-default-version 2
```

2. **Ubuntu in WSL2 installieren**:

```powershell
wsl --install -d Ubuntu-22.04
```

3. **Im WSL2-Terminal** (Ubuntu starten):

```bash
# Paketliste aktualisieren
sudo apt update

# Docker und Docker Compose installieren
sudo apt install -y docker.io docker-compose

# Docker-Socket-Berechtigungen konfigurieren
sudo usermod -aG docker $USER
```

4. **Repository klonen und Service starten**:

```bash
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service

# Docker Compose Plugin (empfohlen)
docker compose up -d

# Oder Standalone docker-compose
docker-compose up -d
```

5. **Zugriff von Windows**:

```powershell
# WSL2-IP-Adresse finden (von PowerShell)
wsl hostname -I

# Beispiel: http://172.20.10.50:8000
```

#### Option B: Docker Desktop für Windows

**Vorteile**: GUI, einfacheres Setup, automatische Ressourcenverwaltung

1. **Download und Installation**:
   - [Docker Desktop](https://www.docker.com/products/docker-desktop) herunterladen
   - Mit Standardeinstellungen installieren
   - Bei Bedarf Neustart durchführen

2. **Repository klonen**:

```powershell
# Mit PowerShell oder Git Bash
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service
```

3. **Service starten**:

```powershell
# Docker Compose Plugin (empfohlen)
docker compose up -d

# Oder Standalone docker-compose
docker-compose up -d
```

4. **Service zugreifen**:

```powershell
# Zugriff von Windows
Start-Process "http://localhost:8000"
```

#### Windows Speicherintegration

Einen freigegebenen Ordner für Dateiaustausch einbinden:

```yaml
# In docker-compose.yml
services:
  pdfa:
    # ... vorhandene Konfiguration ...
    volumes:
      - ./scans:/data/scans
      - ./archive:/data/archive
```

Ordner in Windows erstellen:

```powershell
New-Item -ItemType Directory -Path ".\scans"
New-Item -ItemType Directory -Path ".\archive"
```

Gescannte PDFs in `.\scans` ablegen, konvertierte Dokumente aus `.\archive` abrufen.

---

## Verwendungsbeispiele

### Web-Interface Upload

Für ein Browser-basiertes Interface stellen Sie ein einfaches HTML-Formular bereit:

```html
<!DOCTYPE html>
<html>
<head>
    <title>OCR Dokumentenscanner</title>
    <style>
        body { font-family: Arial; max-width: 600px; margin: 50px auto; }
        input { padding: 10px; margin: 10px 0; width: 100%; }
        button { padding: 10px 20px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>📄 Dokumentenscanner</h1>
    <form id="uploadForm">
        <input type="file" id="file" accept=".pdf" required>
        <select id="language">
            <option value="deu">Deutsch</option>
            <option value="eng">Englisch</option>
            <option value="deu+eng">Deutsch + Englisch</option>
        </select>
        <select id="pdfa_level">
            <option value="2" selected>PDF/A-2</option>
            <option value="3">PDF/A-3</option>
        </select>
        <button type="submit">In PDF/A konvertieren</button>
    </form>

    <div id="result"></div>

    <script>
    document.getElementById('uploadForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const file = document.getElementById('file').files[0];
        const language = document.getElementById('language').value;
        const pdfa_level = document.getElementById('pdfa_level').value;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('language', language);
        formData.append('pdfa_level', pdfa_level);

        try {
            const response = await fetch('/convert', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${file.name.replace('.pdf', '')}_pdfa.pdf`;
                a.click();
                document.getElementById('result').textContent = '✓ Konvertierung erfolgreich!';
            } else {
                document.getElementById('result').textContent = '✗ Konvertierung fehlgeschlagen';
            }
        } catch (error) {
            document.getElementById('result').textContent = '✗ Fehler: ' + error;
        }
    });
    </script>
</body>
</html>
```

Speichern Sie als `index.html` und servieren Sie sie zusammen mit der API.

### Batch-Verarbeitungs-Skript

Konvertieren Sie automatisch einen Ordner mit gescannten PDFs:

```bash
#!/bin/bash
# batch-ocr-scan.sh - Alle PDFs in einem Ordner verarbeiten

SCAN_FOLDER="${1:-.}"
API_URL="${2:-http://localhost:8000/convert}"
LANGUAGE="${3:-deu+eng}"
OUTPUT_SUFFIX="_pdfa"

echo "Verarbeite PDFs in: $SCAN_FOLDER"
echo "API: $API_URL"

for pdf in "$SCAN_FOLDER"/*.pdf; do
    [ ! -f "$pdf" ] && continue

    filename=$(basename "$pdf" .pdf)
    output="${SCAN_FOLDER}/${filename}${OUTPUT_SUFFIX}.pdf"

    echo "Konvertiere: $filename..."

    curl -s -X POST "$API_URL" \
        -F "file=@$pdf;type=application/pdf" \
        -F "language=$LANGUAGE" \
        -F "pdfa_level=2" \
        --output "$output" 2>/dev/null

    if [ -f "$output" ]; then
        echo "  ✓ Erfolg -> $output"
    else
        echo "  ✗ Fehlgeschlagen"
    fi
done

echo "Fertig!"
```

**Verwendung**:

```bash
chmod +x batch-ocr-scan.sh
./batch-ocr-scan.sh ~/Dokumente/Scans http://192.168.1.50:8000/convert deu+eng
```

### Integration mit Scanner-Gerät

Die meisten Office-Scanner unterstützen das Hochladen auf einen HTTP-Endpunkt:

1. In den Scanner-Einstellungen konfigurieren: `http://[pi-ip]:8000/convert`
2. Ausgabeformat auf PDF setzen
3. OCR-Sprache in der Scanner-Benutzeroberfläche konfigurieren
4. Mit einem Testdokument prüfen
5. Automatisches Hochladen nach jedem Scan aktivieren

### Ordner-Überwachung (Automatische Verarbeitung)

Überwachen Sie einen Ordner und konvertieren Sie neue PDFs automatisch:

```bash
#!/bin/bash
# monitor-and-convert.sh

WATCH_DIR="$1"
API_URL="${2:-http://localhost:8000/convert}"

echo "Überwache $WATCH_DIR auf neue PDFs..."

while true; do
    for pdf in "$WATCH_DIR"/*.pdf; do
        [ ! -f "$pdf" ] && continue

        # Überspringen, falls bereits verarbeitet
        [ -f "$pdf.processing" ] && continue

        touch "$pdf.processing"
        echo "Verarbeite: $(basename $pdf)"

        curl -s -X POST "$API_URL" \
            -F "file=@$pdf;type=application/pdf" \
            -F "language=deu+eng" \
            --output "${pdf%.pdf}_pdfa.pdf"

        rm "$pdf.processing"
    done

    sleep 5  # Prüfen alle 5 Sekunden
done
```

---

## Netzwerkkonfiguration

### Zugriff im lokalen Netzwerk

**Raspberry Pi / Linux Server**:

```bash
# IP-Adresse finden
hostname -I

# Von anderem Gerät aus zugreifen
curl http://192.168.1.50:8000/convert ...
```

**Windows mit Docker Desktop**:

```powershell
# Docker Desktop IP ist normalerweise localhost:8000
# Oder WSL2-IP finden:
wsl hostname -I
```

### Port-Konfiguration

Anderen Port verwenden, wenn 8000 belegt ist:

```yaml
# docker-compose.yml
services:
  pdfa:
    ports:
      - "9000:8000"  # Zugriff unter :9000
```

### Firewall-Regeln

**Linux**:

```bash
sudo ufw allow 8000/tcp
sudo ufw enable
```

**Windows** (Windows Defender Firewall):

1. Windows Defender Firewall öffnen
2. Auf „App durch Firewall zulassen" klicken
3. Docker oder wsl2 zu zugelassenen Apps hinzufügen
4. Sicherstellen, dass „Private Netzwerke" ausgewählt ist

---

## Leistung & Optimierung

### Verarbeitungszeiten

Typische OCR-Verarbeitungszeiten pro Seite:

| Gerät | Sprache | Zeit |
|-------|---------|------|
| Raspberry Pi 4 (ARM64) | Deutsch | 30-60s |
| Raspberry Pi 4 (ARM64) | Deutsch + Englisch | 45-90s |
| Moderner x86_64 CPU | Deutsch | 5-10s |
| Moderner x86_64 CPU | Deutsch + Englisch | 8-15s |

### Optimierungstipps

1. **OCR für bereits digitalisierte Dokumente deaktivieren**:
   ```bash
   curl ... -F "ocr_enabled=false" ...
   ```

2. **Verwenden Sie eine Sprache, wenn möglich**:
   ```bash
   curl ... -F "language=deu" ...  # Schneller als deu+eng
   ```

3. **Verarbeiten Sie sequenziell** (vermeiden Sie parallele Uploads auf Pi):
   ```bash
   # Gut: Sequenzielle Verarbeitung
   for pdf in *.pdf; do
       curl ... "$pdf" ...
       wait  # Auf Abschluss warten
   done
   ```

4. **Weisen Sie ausreichend Ressourcen in docker-compose.yml zu**:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 2G
   ```

5. **Verwenden Sie PDF/A-2** (Standard, schneller als PDF/A-3):
   ```bash
   curl ... -F "pdfa_level=2" ...
   ```

---

## Sicherheitsaspekte

⚠️ **Wichtig für die Produktivnutzung**

### Nur lokales Netzwerk

Das Standard-Setup ist für die **Verwendung nur im lokalen Netzwerk** geeignet:

```yaml
# docker-compose.yml
services:
  pdfa:
    ports:
      - "127.0.0.1:8000:8000"  # Nur von localhost erreichbar
```

Für Netzwerkzugriff (mit Vorsicht):

```yaml
ports:
  - "8000:8000"  # Von jedem Netzwerkgerät erreichbar
```

### Reverse Proxy mit Authentifizierung (Empfohlen)

Für netzwerkweiten Zugriff verwenden Sie einen Reverse Proxy:

```yaml
# docker-compose.yml mit nginx
version: '3.8'
services:
  pdfa:
    image: pdfa-service:latest
    ports:
      - "127.0.0.1:8000:8000"  # Nur lokaler Zugriff

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - pdfa
```

**nginx.conf** (mit Basis-Authentifizierung):

```nginx
events { worker_connections 1024; }
http {
  server {
    listen 80;

    # Basis-Authentifizierung hinzufügen
    location / {
      auth_basic "Geschützt";
      auth_basic_user_file /etc/nginx/.htpasswd;

      proxy_pass http://pdfa:8000;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
    }
  }
}
```

### Dateigröße-Limits

Maximale Upload-Größe in docker-compose festlegen:

```yaml
environment:
  - MAX_UPLOAD_SIZE=100M  # Große Dateien begrenzen
```

---

## Fehlerbehebung

### Service startet nicht

```bash
# Protokolle überprüfen
docker compose logs pdfa
# oder: docker-compose logs pdfa

# Häufiges Problem: Port bereits in Verwendung
sudo lsof -i :8000  # Prozess finden, der Port 8000 verwendet

# Prozess beenden und neu starten
docker compose restart
# oder: docker-compose restart
```

### OCR-Fehler

```bash
# Überprüfen, ob Tesseract verfügbar ist
docker compose exec pdfa which tesseract
# oder: docker-compose exec pdfa which tesseract

# Fehlendes Sprachpaket installieren (im Container)
docker compose exec pdfa apt-get update && apt-get install -y tesseract-ocr-fra
# oder: docker-compose exec pdfa apt-get update && apt-get install -y tesseract-ocr-fra
```

### Langsame Verarbeitung

- Reduzieren Sie gleichzeitige Uploads
- Überwachen Sie die CPU-Auslastung: `docker stats`
- Überprüfen Sie verfügbaren Speicherplatz: `df -h`
- Erwägen Sie ein Upgrade auf eine einzelne Sprache

### Netzwerkzugriffsprobleme

```bash
# Von Scanner/Client-Gerät aus, Verbindung testen
ping 192.168.1.50  # Raspberry Pi anpingen
curl http://192.168.1.50:8000/docs  # API testen

# Von Pi aus, Service-Status überprüfen
docker compose ps
# oder: docker-compose ps
docker compose logs pdfa
# oder: docker-compose logs pdfa
```

---

## Wartung

### Regelmäßige Bereinigung

```bash
#!/bin/bash
# Alte Dateien bereinigen

# Konvertierte PDFs älter als 30 Tage entfernen
find ./archive -name "*_pdfa.pdf" -mtime +30 -delete

# Docker-Images bereinigen
docker image prune -a --filter "until=720h"
```

### Speichernutzung überwachen

```bash
# Docker-Volumen-Nutzung überprüfen
docker system df

# Nicht verwendete Volumen bereinigen
docker volume prune
```

### Service aktualisieren

```bash
# Neuestes Image abrufen
docker compose pull
# oder: docker-compose pull

# Mit neuer Version neu starten
docker compose down
docker compose up -d
# oder: docker-compose down && docker-compose up -d
```

---

## Referenzen

- [OCRmyPDF Dokumentation](https://ocrmypdf.readthedocs.io/)
- [Docker Dokumentation](https://docs.docker.com/)
- [Raspberry Pi Setup Anleitung](https://www.raspberrypi.com/documentation/)
- [PDF/A Spezifikation](https://en.wikipedia.org/wiki/PDF/A)

---

## Nächste Schritte

- Mit Beispiel-gescannten PDFs testen
- Konventionen für Dokumentenbenennung konfigurieren
- Geplante Bereinigungsaufgaben einrichten
- Ihren Workflow und Ihre Spracheinstellungen dokumentieren

Viel Erfolg beim digitalen Scannen! 📋✨
