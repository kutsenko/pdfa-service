# OCR-Dokumentenscanner - Praktisches Setup & Anwendungsszenarien

Eine umfassende Anleitung für den Einsatz von pdfa-service als Dokumentenscanner im Netzwerk mit Docker Compose.

## Schnelle Navigation

| Betriebssystem | Plattform | Anleitung |
|---|---|---|
| 🥧 **Raspberry Pi 4/5** | ARM64 (Lokales Netzwerk) | [Zu Raspberry Pi Setup](#raspberry-pi-netzwerk-scanner) |
| 🪟 **Windows 10/11** | x86_64 (Docker Desktop) | [Zu Windows Setup](#windows-docker-setup) |
| 🐧 **Linux** | x86_64 (Docker Compose) | [Zu Linux Server Setup](#linux-server-setup) |

---

## Praktische Anwendungsszenarien

### Szenario 1: Heimatelier - Dokumentendigitalisierung

**Aufbau**: Desktop-Scanner → Raspberry Pi (NAS) → PDF/A-Archiv

**Hardware**:
- Fujitsu ScanSnap oder Brother ADS-Scanner mit Netzwerkanbindung
- Raspberry Pi 4 mit 4GB RAM (läuft 24/7)
- NAS oder externe SSD für Dokumentenspeicherung

**Arbeitsablauf**:
1. Dokument am Scanner einscannen
2. Scanner lädt automatisch zur Pi-API hoch
3. OCR läuft im Hintergrund
4. Durchsuchbares PDF/A in Archiv gespeichert
5. Originalscan nach 7 Tagen gelöscht

**Docker Compose Konfiguration**:
```yaml
version: '3.8'
services:
  pdfa:
    image: pdfa-service:latest
    container_name: ocr-scanner
    ports:
      - "192.168.1.50:8000:8000"  # Pi's lokale IP
    volumes:
      - /mnt/nas/scans:/data/scans:rw
      - /mnt/nas/archive:/data/archive:rw
    environment:
      - TZ=Europe/Berlin
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]
      interval: 60s
      timeout: 10s
      retries: 3
```

**Scanner-Konfiguration** (Fujitsu-Beispiel):
- Upload-Ziel: `http://192.168.1.50:8000/convert`
- Ausgabeordner: `/mnt/nas/archive`
- Sprache: Deutsch (`deu`)

---

### Szenario 2: Kleine Kanzlei - Dokumentenverarbeitung mit Compliance

**Aufbau**: Mehrere Benutzer → Windows-PC zentral → PDF/A-Archiv + Compliance

**Hardware**:
- Windows 10/11 PC mit Docker Desktop
- Netzwerk-Freigabe für eingescannte Dokumente
- Dateiserver für Compliance-Backup

**Arbeitsablauf**:
1. Benutzer legen gescannte PDFs in Netzwerk-Ordner
2. Ordner-Monitor erkennt neue Dateien
3. API konvertiert zu PDF/A mit OCR
4. Dateien in Archiv verschoben und indexiert
5. Compliance-Bericht monatlich erstellt

**Docker Compose Konfiguration**:
```yaml
version: '3.8'
services:
  pdfa:
    image: pdfa-service:latest
    container_name: office-ocr-scanner
    ports:
      - "9000:8000"
    volumes:
      # Netzwerk-Freigaben
      - "\\\\fileserver\\scans:/data/scans:ro"
      - "\\\\fileserver\\archive:/data/archive:rw"
      - "\\\\fileserver\\logs:/data/logs:rw"
    environment:
      - LOG_LEVEL=INFO
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 3G
```

**PowerShell-Batch-Skript** (`process-documents.ps1`):
```powershell
# Ordner überwachen und Dateien verarbeiten
$ApiUrl = "http://localhost:9000/convert"
$ScanFolder = "\\fileserver\scans"
$ArchiveFolder = "\\fileserver\archive"

Get-ChildItem $ScanFolder -Filter "*.pdf" | ForEach-Object {
    Write-Host "Verarbeite: $($_.Name)"

    $output = "$ArchiveFolder\$($_.BaseName)_pdfa.pdf"

    $response = Invoke-WebRequest `
        -Uri $ApiUrl `
        -Method Post `
        -Form @{
            file = Get-Item $_
            language = "deu+eng"
            pdfa_level = "2"
        } `
        -OutFile $output

    if ($?) {
        Write-Host "✓ Konvertiert zu: $output"
        Remove-Item $_
    }
}
```

---

### Szenario 3: Arzt/Anwalt - Hochsichere Archivierung mit Audit-Trail

**Aufbau**: Sicheres Einscannen → Verschlüsseltes Archiv → Revisionssicherheit

**Hardware-Anforderungen**:
- Raspberry Pi mit 8GB RAM (mindestens)
- Verschlüsselte SSD für Dokumentenspeicherung
- Backup-NAS (RAID-1 oder RAID-5)

**Features**:
- PDF/A-3-Compliance (höchste Archivstufe)
- Revisions-Logging mit Zeitstempel
- Verschlüsselte Volumes
- Monatliche Backups an separaten Ort

**Docker Compose Konfiguration**:
```yaml
version: '3.8'
services:
  pdfa:
    image: pdfa-service:latest
    container_name: compliance-ocr

    ports:
      - "192.168.1.100:8000:8000"  # Eingeschränkter Zugriff

    volumes:
      - /mnt/encrypted-ssd/documents:/data/documents:rw
      - /mnt/encrypted-ssd/audit-logs:/data/audit-logs:rw
      - /mnt/backup-nas/archive:/data/backup:ro

    environment:
      - TZ=Europe/Berlin
      - MAX_UPLOAD_SIZE=500M
      - LOG_LEVEL=DEBUG

    restart: unless-stopped

    # Ressourcen-Limits für Pi-Stabilität
    deploy:
      resources:
        limits:
          cpus: '3'
          memory: 6G
        reservations:
          cpus: '1'
          memory: 2G

    # Health Checks
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Nginx Reverse Proxy mit Authentifizierung
  nginx:
    image: nginx:latest
    container_name: ocr-gateway
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - /data/audit-logs:/var/log/nginx:rw
    depends_on:
      - pdfa
    restart: unless-stopped
```

**nginx.conf** (mit Authentifizierung & Logging):
```nginx
events { worker_connections 1024; }

http {
  access_log /var/log/nginx/access.log combined;

  upstream pdfa {
    server pdfa:8000;
  }

  server {
    listen 80;
    server_name _;

    client_max_body_size 500M;

    # Authentifizierung
    location / {
      auth_basic "Zugang beschränkt - Nur autorisiertes Personal";
      auth_basic_user_file /etc/nginx/.htpasswd;

      proxy_pass http://pdfa;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;

      # Alle Anfragen für Audit-Trail protokollieren
      access_log /var/log/nginx/pdfa_audit.log combined;
    }
  }
}
```

**Authentifizierung einrichten**:
```bash
# Passwort-Datei erstellen
docker run --rm -v $(pwd):/data \
  httpd:latest \
  htpasswd -c /data/.htpasswd doctor1 passwort123
```

---

## Vollständige Installationsanleitungen

### Raspberry Pi - Netzwerk-Scanner

#### Hardware-Setup

**Anforderungen**:
- Raspberry Pi 4 oder 5 (4GB+ RAM empfohlen)
- 32GB+ microSD-Karte (Class 10)
- Externe SSD oder NAS für Dokumente
- Stromversorgung (USB-C, 5A empfohlen)

**Installationsschritte**:

1. **Betriebssystem installieren**:
```bash
# Raspberry Pi OS 64-bit herunterladen von https://www.raspberrypi.com/software/
# Raspberry Pi Imager nutzen zum Schreiben auf microSD
# SSH während Setup aktivieren
```

2. **Erste Konfiguration**:
```bash
# SSH zur Pi
ssh pi@192.168.1.XXX

# System aktualisieren
sudo apt update && sudo apt upgrade -y

# Hostname setzen
sudo hostnamectl set-hostname ocr-scanner

# Zeitzone konfigurieren
sudo timedatectl set-timezone Europe/Berlin
```

3. **Docker installieren**:
```bash
# Offizielles Docker-Installationsskript
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# pi-Benutzer zu docker-Gruppe hinzufügen
sudo usermod -aG docker pi
newgrp docker

# Docker beim Start aktivieren
sudo systemctl enable docker
sudo systemctl start docker

# Verifikation
docker --version
```

4. **Externe Speicherung mounten** (NAS oder SSD):
```bash
# Gerät finden
lsblk
# Ausgabe: sda (USB-SSD), sdb (NAS-Mount)

# Mount-Punkte erstellen
mkdir -p /mnt/external-ssd
mkdir -p /mnt/nas-storage

# /etc/fstab für persistente Mounts bearbeiten
sudo nano /etc/fstab

# Zeilen hinzufügen:
# /dev/sda1 /mnt/external-ssd ext4 defaults,nofail 0 2
# //nas-server/documents /mnt/nas-storage cifs credentials=/home/pi/.smbcredentials,nofail 0 0

# SMB-Anmeldedatei erstellen (bei NAS-Nutzung)
echo "username=nas_user" > ~/.smbcredentials
echo "password=nas_pass" >> ~/.smbcredentials
chmod 600 ~/.smbcredentials

# Alle mounten
sudo mount -a
```

5. **pdfa-service klonen und starten**:
```bash
# Repository klonen
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service

# Docker Compose Override für Pi erstellen
cat > docker-compose.pi.yml << 'EOF'
version: '3.8'
services:
  pdfa:
    image: pdfa-service:latest
    container_name: ocr-scanner-pi
    ports:
      - "0.0.0.0:8000:8000"
    volumes:
      - /mnt/external-ssd/scans:/data/scans:rw
      - /mnt/external-ssd/archive:/data/archive:rw
    environment:
      - TZ=Europe/Berlin
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2.5'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]
      interval: 60s
      timeout: 10s
      retries: 3
EOF

# Service starten
docker compose -f docker-compose.yml -f docker-compose.pi.yml up -d

# Logs ansehen
docker compose logs -f pdfa
```

6. **IP-Adresse der Pi finden**:
```bash
hostname -I
# Ausgabe: 192.168.1.42

# Von anderem Gerät testen
curl http://192.168.1.42:8000/docs
```

#### Scanner konfigurieren (Netzwerk-Gerät-Beispiel)

**Brother/Ricoh Network-Scanner**:
1. Scanner Web-UI → Netzwerkeinstellungen → HTTP-Upload
2. **URL**: `http://192.168.1.42:8000/convert`
3. **Methode**: POST
4. **Format**: PDF
5. **Erweitert**: OCR aktivieren, Sprache "Deutsch+English"
6. **Test**: Testseite versenden

#### Überwachen und Warten

```bash
# Service-Status prüfen
docker compose ps

# Echtzeit-Logs mit Zeitstempel anzeigen
docker compose logs -f --timestamps pdfa

# Ressourcennutzung überwachen
docker stats pdfa

# Neu starten falls nötig
docker compose restart pdfa

# Auf aktuellste Version aktualisieren
docker compose pull
docker compose down
docker compose up -d
```

---

### Windows - Docker Setup

#### Voraussetzungen

- Windows 10/11 (Home, Pro oder Enterprise)
- Docker Desktop für Windows installiert
- Mindestens 4GB RAM für Docker
- Netzwerkzugriff auf andere Geräte

#### Option A: Docker Desktop (Einfachste Methode)

1. **Docker Desktop installieren**:
   - Von https://www.docker.com/products/docker-desktop herunterladen
   - Installer ausführen und Anweisungen folgen
   - Computer neu starten
   - Verifikation: PowerShell öffnen und `docker --version` ausführen

2. **Repository klonen**:
```powershell
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service
```

3. **Lokale Ordner erstellen**:
```powershell
# Ordnerstruktur erstellen
New-Item -ItemType Directory -Force -Path ".\scans"
New-Item -ItemType Directory -Force -Path ".\archive"
New-Item -ItemType Directory -Force -Path ".\logs"
```

4. **Docker Compose Override erstellen**:
```powershell
# Speichern als docker-compose.windows.yml
@"
version: '3.8'
services:
  pdfa:
    image: pdfa-service:latest
    container_name: ocr-scanner-windows
    ports:
      - "8000:8000"
    volumes:
      - ./scans:/data/scans:rw
      - ./archive:/data/archive:rw
      - ./logs:/data/logs:rw
    environment:
      - TZ=Europe/Berlin
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 3G
"@ | Out-File -Encoding UTF8 docker-compose.windows.yml
```

5. **Service starten**:
```powershell
docker compose -f docker-compose.yml -f docker-compose.windows.yml up -d

# Auf Start warten
Start-Sleep -Seconds 5

# Test
Invoke-WebRequest http://localhost:8000/docs
```

6. **Web-Oberfläche öffnen**:
```powershell
Start-Process "http://localhost:8000"
```

#### Option B: WSL2 (Für fortgeschrittene Benutzer)

```powershell
# PowerShell als Administrator
wsl --install
wsl --set-default-version 2
wsl --install -d Ubuntu-22.04

# In WSL2 Ubuntu Terminal
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER

# Klonen und starten
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service
docker compose up -d
```

#### Netzwerk-Freigabe (Gemeinsame Nutzung zwischen Computern)

```yaml
# docker-compose.windows.yml
version: '3.8'
services:
  pdfa:
    image: pdfa-service:latest
    container_name: ocr-scanner
    ports:
      - "0.0.0.0:8000:8000"  # Auf allen Interfaces horchen
    volumes:
      - //192.168.1.100/shared-documents/scans:/data/scans:rw
      - //192.168.1.100/shared-documents/archive:/data/archive:rw
```

#### Windows Batch-Skript zur Überwachung

Speichern als `monitor-scans.cmd`:
```batch
@echo off
setlocal enabledelayedexpansion

set "SCAN_FOLDER=%CD%\scans"
set "API_URL=http://localhost:8000/convert"
set "ARCHIVE_FOLDER=%CD%\archive"
set "LOG_FILE=%CD%\logs\batch_log.txt"

:loop
for /f %%F in ('dir /b "%SCAN_FOLDER%\*.pdf" 2^>nul') do (
    set "FILE=%SCAN_FOLDER%\%%F"
    set "OUTPUT=%ARCHIVE_FOLDER%\%%~nF"

    echo [%date% %time%] Verarbeite: %%F >> "%LOG_FILE%"

    curl -X POST "%API_URL%" ^
        -F "file=@!FILE!;type=application/pdf" ^
        -F "language=deu+eng" ^
        -F "pdfa_level=2" ^
        --output "!OUTPUT!" 2>nul

    if exist "!OUTPUT!" (
        echo [%date% %time%] ERFOLG: %%F >> "%LOG_FILE%"
        del "!FILE!"
    ) else (
        echo [%date% %time%] FEHLER: %%F >> "%LOG_FILE%"
    )
)

timeout /t 10 /nobreak
goto loop
```

Mit Task Scheduler ausführen:
1. Task Scheduler öffnen
2. Neue Aufgabe erstellen → Name: "OCR Scanner Monitor"
3. Trigger: Beim Start (oder wiederkehrend)
4. Aktion: `cmd.exe /c C:\path\to\monitor-scans.cmd`
5. "Mit höchsten Berechtigungen ausführen" aktivieren

---

### Linux Server Setup

```bash
# Ubuntu 22.04+ / Debian 12+
sudo apt update
sudo apt install -y docker.io docker-compose

sudo usermod -aG docker $USER
newgrp docker

# Klonen und starten
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service

# Verzeichnisse erstellen
mkdir -p {scans,archive,logs}

# Starten
docker compose up -d

# Logs überwachen
docker compose logs -f
```

---

## Docker Compose Verwendungsbeispiele

### Einfaches Beispiel - Einzelner Computer

```yaml
version: '3.8'
services:
  pdfa:
    image: pdfa-service:latest
    container_name: pdfa-ocr
    ports:
      - "8000:8000"
    volumes:
      - ./documents:/data/documents:rw
    restart: unless-stopped
```

**Starten**:
```bash
docker compose up -d
```

**Test**:
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@sample.pdf" \
  --output sample_pdfa.pdf
```

---

### Erweitert - Production-Setup

```yaml
version: '3.8'
services:
  pdfa:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: pdfa-ocr-prod

    ports:
      - "127.0.0.1:8000:8000"  # Nur lokal

    volumes:
      - documents-volume:/data/documents
      - logs-volume:/data/logs
      - cache-volume:/tmp/pdfa-cache

    environment:
      - TZ=Europe/Berlin
      - LOG_LEVEL=INFO
      - MAX_WORKERS=2

    restart: unless-stopped

    # Ressource-Limits
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 3G
        reservations:
          cpus: '1'
          memory: 1.5G

    # Health Monitoring
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    # Logging
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Nginx Reverse Proxy
  nginx:
    image: nginx:latest
    container_name: pdfa-gateway
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - pdfa
    restart: unless-stopped

volumes:
  documents-volume:
    driver: local
  logs-volume:
    driver: local
  cache-volume:
    driver: local
```

---

## Praktische Verwendungsbeispiele

### 1. Einzelne Datei konvertieren

```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@dokument.pdf" \
  -F "language=deu+eng" \
  -F "pdfa_level=2" \
  --output dokument_pdfa.pdf
```

### 2. Batch-Verarbeitung - Bash-Skript

```bash
#!/bin/bash
# batch-convert.sh

API_URL="http://localhost:8000/convert"
INPUT_DIR="./scans"
OUTPUT_DIR="./archive"

for file in "$INPUT_DIR"/*.pdf; do
    [ ! -f "$file" ] && continue

    basename=$(basename "$file")
    output="$OUTPUT_DIR/${basename%.pdf}_pdfa.pdf"

    echo "Konvertiere: $basename"

    curl -s -X POST "$API_URL" \
        -F "file=@$file" \
        -F "language=deu+eng" \
        --output "$output"

    if [ -f "$output" ]; then
        echo "✓ Erfolg: $output"
    else
        echo "✗ Fehler: $basename"
    fi
done
```

**Ausführen**:
```bash
chmod +x batch-convert.sh
./batch-convert.sh
```

### 3. Kontinuierliche Überwachung - Bash-Skript

```bash
#!/bin/bash
# monitor.sh - Neue PDFs überwachen und automatisch konvertieren

WATCH_DIR="./scans"
API_URL="http://localhost:8000/convert"
PROCESSED_MARKER=".processed"

while true; do
    for file in "$WATCH_DIR"/*.pdf; do
        [ ! -f "$file" ] && continue
        [ -f "$file$PROCESSED_MARKER" ] && continue

        echo "[$(date)] Verarbeite: $(basename $file)"

        output="${file%.pdf}_pdfa.pdf"
        curl -s -X POST "$API_URL" \
            -F "file=@$file" \
            -F "language=deu+eng" \
            --output "$output"

        # Als verarbeitet markieren
        touch "$file$PROCESSED_MARKER"

        # Original nach 24h aus Archiv löschen
        find "$WATCH_DIR" -name "*.pdf$PROCESSED_MARKER" -mtime +1 -delete
    done

    sleep 30  # Alle 30 Sekunden prüfen
done
```

### 4. Parallele Verarbeitung

```bash
# Mehrere Dateien parallel verarbeiten (4 gleichzeitig)
find ./scans -name "*.pdf" -type f | \
  xargs -P 4 -I {} bash -c '
    file="{}"
    output="./archive/$(basename ${file%.pdf}_pdfa.pdf)"

    curl -s -X POST "http://localhost:8000/convert" \
        -F "file=@$file" \
        -F "language=deu+eng" \
        --output "$output"
  '
```

---

## Fehlerbehebung

### Service startet nicht
```bash
# Docker-Logs prüfen
docker compose logs pdfa

# Häufige Probleme:
# 1. Port bereits in Verwendung
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# 2. Unzureichende Ressourcen
docker stats

# 3. Berechtigungen auf gemountete Volumes
ls -la ./scans
chmod 755 ./scans
```

### Langsame Verarbeitung
```bash
# CPU/Speicher-Nutzung prüfen
docker stats pdfa

# Ressourcen erhöhen
# docker-compose.yml bearbeiten:
deploy:
  resources:
    limits:
      cpus: '3'
      memory: 4G
```

### OCR-Sprache fehlt
```bash
# Zusätzliche Sprache installieren
docker compose exec pdfa \
  apt-get update && apt-get install -y tesseract-ocr-fra

# Verifikation
docker compose exec pdfa tesseract --list-langs
```

---

## Performance-Benchmarks

**Verarbeitungszeit pro Seite** (mit OCR):

| Hardware | CPU | RAM | Sprache | Zeit |
|----------|-----|-----|---------|------|
| Raspberry Pi 4 | ARM Cortex-A72 | 4GB | deu+eng | 45-90s |
| Raspberry Pi 5 | ARM Cortex-A76 | 8GB | deu+eng | 25-45s |
| Intel i7 (modern) | x86_64 | 16GB | deu+eng | 5-10s |
| AMD Ryzen 5 | x86_64 | 16GB | deu+eng | 4-8s |

---

## Nächste Schritte

1. Hardware wählen (Raspberry Pi, Windows-PC oder Linux-Server)
2. Installationsanleitung für Ihre Plattform folgen
3. Mit Beispieldokumenten testen
4. Scanner oder Arbeitsablauf konfigurieren
5. Automatisierte Batch-Verarbeitung einrichten
6. Logs und Leistung überwachen

Für weitere Informationen siehe [README.de.md](README.de.md) und [OCR-SCANNER.de.md](OCR-SCANNER.de.md).
