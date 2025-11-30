# OCR Document Scanner - Practical Setup & Scenarios

A comprehensive guide for deploying pdfa-service as a networked OCR document scanner with Docker Compose.

## Quick Navigation

| Operating System | Platform | Guide |
|---|---|---|
| 🥧 **Raspberry Pi 4/5** | ARM64 (Local Network) | [Jump to Raspberry Pi Setup](#raspberry-pi-network-scanner) |
| 🪟 **Windows 10/11** | x86_64 (Docker Desktop) | [Jump to Windows Setup](#windows-docker-setup) |
| 🐧 **Linux** | x86_64 (Docker Compose) | [Jump to Linux Setup](#linux-server-setup) |

---

## Real-World Scenarios

### Scenario 1: Home Office Document Digitization

**Setup**: Desktop scanner → Raspberry Pi (NAS) → PDF/A archival

**Hardware**:
- Fujitsu ScanSnap or Brother ADS scanner connected to network
- Raspberry Pi 4 with 4GB RAM running 24/7
- NAS or external SSD for document storage

**Workflow**:
1. Scan document at office scanner
2. Scanner automatically uploads to Pi's API endpoint
3. OCR processes in background
4. Searchable PDF/A saved to archive folder
5. Original scan deleted after 7 days

**Docker Compose Configuration**:
```yaml
version: '3.8'
services:
  pdfa:
    image: pdfa-service:latest
    container_name: ocr-scanner
    ports:
      - "192.168.1.50:8000:8000"  # Pi's local IP
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

**Scanner Configuration** (Fujitsu example):
- Upload destination: `http://192.168.1.50:8000/convert`
- Output folder: `/mnt/nas/archive`
- Language: German (`deu`)

---

### Scenario 2: Small Office Document Processing Workflow

**Setup**: Multiple users → Central Windows PC → PDF/A archive + compliance

**Hardware**:
- Windows 10 PC running Docker Desktop
- Network folder share for incoming documents
- File server for compliance backup

**Workflow**:
1. Users drop scanned PDFs in shared network folder
2. Folder monitor detects new files
3. API converts to PDF/A with OCR
4. Files moved to archive and indexed
5. Compliance report generated monthly

**Docker Compose Configuration**:
```yaml
version: '3.8'
services:
  pdfa:
    image: pdfa-service:latest
    container_name: office-ocr-scanner
    ports:
      - "9000:8000"
    volumes:
      # Shared network folders
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

**Batch Script** (`process-documents.ps1`):
```powershell
# Watch folder and process files
$ApiUrl = "http://localhost:9000/convert"
$ScanFolder = "\\fileserver\scans"
$ArchiveFolder = "\\fileserver\archive"

Get-ChildItem $ScanFolder -Filter "*.pdf" | ForEach-Object {
    Write-Host "Processing: $($_.Name)"

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
        Write-Host "✓ Converted to: $output"
        Remove-Item $_
    }
}
```

---

### Scenario 3: Medical/Legal Practice - Compliance-Grade Archival

**Setup**: Secure scanning → Encrypted archive → Audit trail

**Hardware Requirements**:
- Raspberry Pi with 8GB RAM minimum
- Encrypted SSD for document storage
- Backup NAS (RAID-1 or RAID-5)

**Features**:
- PDF/A-3 compliance (highest archival level)
- Audit logging with timestamps
- Encrypted volumes
- Monthly backups to separate location

**Docker Compose Configuration**:
```yaml
version: '3.8'
services:
  pdfa:
    image: pdfa-service:latest
    container_name: compliance-ocr

    ports:
      - "192.168.1.100:8000:8000"  # Restricted access

    volumes:
      - /mnt/encrypted-ssd/documents:/data/documents:rw
      - /mnt/encrypted-ssd/audit-logs:/data/audit-logs:rw
      - /mnt/backup-nas/archive:/data/backup:ro

    environment:
      - TZ=Europe/Berlin
      - MAX_UPLOAD_SIZE=500M
      - LOG_LEVEL=DEBUG

    restart: unless-stopped

    # Resource limits for Pi stability
    deploy:
      resources:
        limits:
          cpus: '3'
          memory: 6G
        reservations:
          cpus: '1'
          memory: 2G

    # Health checks
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Optional: Nginx reverse proxy with auth
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

**nginx.conf** (with authentication & logging):
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

    # Authentication
    location / {
      auth_basic "Restricted - Authorized Personnel Only";
      auth_basic_user_file /etc/nginx/.htpasswd;

      proxy_pass http://pdfa;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;

      # Log all requests for audit trail
      access_log /var/log/nginx/pdfa_audit.log combined;
    }
  }
}
```

**Setup authentication**:
```bash
# Create password file
docker run --rm -v $(pwd):/data \
  httpd:latest \
  htpasswd -c /data/.htpasswd doctor1 password123
```

---

## Complete Installation Guides

### Raspberry Pi Network Scanner

#### Hardware Setup

**Requirements**:
- Raspberry Pi 4 or 5 (4GB+ RAM recommended)
- 32GB+ microSD card (Class 10)
- External SSD or NAS for documents
- Power supply (USB-C, 5A recommended)

**Installation Steps**:

1. **Install OS**:
```bash
# Download Raspberry Pi OS 64-bit from https://www.raspberrypi.com/software/
# Use Raspberry Pi Imager to flash microSD card
# Enable SSH during setup
```

2. **Initial Configuration**:
```bash
# SSH into Pi
ssh pi@192.168.1.XXX

# Update system
sudo apt update && sudo apt upgrade -y

# Set hostname
sudo hostnamectl set-hostname ocr-scanner

# Configure timezone
sudo timedatectl set-timezone Europe/Berlin
```

3. **Install Docker**:
```bash
# Official Docker installation script
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add pi user to docker group
sudo usermod -aG docker pi
newgrp docker

# Enable Docker on boot
sudo systemctl enable docker
sudo systemctl start docker

# Verify installation
docker --version
```

4. **Mount External Storage** (NAS or SSD):
```bash
# Find device
lsblk
# Output: sda (USB SSD), sdb (NAS mount)

# Create mount points
mkdir -p /mnt/external-ssd
mkdir -p /mnt/nas-storage

# Edit /etc/fstab for persistent mounts
sudo nano /etc/fstab

# Add lines:
# /dev/sda1 /mnt/external-ssd ext4 defaults,nofail 0 2
# //nas-server/documents /mnt/nas-storage cifs credentials=/home/pi/.smbcredentials,nofail 0 0

# Create SMB credentials file (if using NAS)
echo "username=nas_user" > ~/.smbcredentials
echo "password=nas_pass" >> ~/.smbcredentials
chmod 600 ~/.smbcredentials

# Mount all
sudo mount -a
```

5. **Clone and Start pdfa-service**:
```bash
# Clone repository
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service

# Create docker-compose override for Pi
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

# Start service
docker compose -f docker-compose.yml -f docker-compose.pi.yml up -d

# View logs
docker compose logs -f pdfa
```

6. **Find Your Pi's IP**:
```bash
hostname -I
# Output: 192.168.1.42

# Test from another device
curl http://192.168.1.42:8000/docs
```

#### Configure Scanner (Network Device Example)

**Brother/Ricoh Network Scanner**:
1. Scanner Web UI → Network Settings → HTTP Upload
2. **URL**: `http://192.168.1.42:8000/convert`
3. **Method**: POST
4. **Format**: PDF
5. **Advanced**: Enable OCR, set language to "Deutsch+English"
6. **Test**: Send test page

#### Monitor and Maintain

```bash
# Check service status
docker compose ps

# View real-time logs with timestamps
docker compose logs -f --timestamps pdfa

# Monitor resource usage
docker stats pdfa

# Restart if needed
docker compose restart pdfa

# Update to latest version
docker compose pull
docker compose down
docker compose up -d
```

---

### Windows Docker Setup

#### Prerequisites

- Windows 10/11 (Home, Pro, or Enterprise)
- Docker Desktop for Windows installed
- Minimum 4GB RAM allocated to Docker
- Network access to other devices

#### Option A: Docker Desktop (Easiest)

1. **Install Docker Desktop**:
   - Download from https://www.docker.com/products/docker-desktop
   - Run installer and follow prompts
   - Restart computer
   - Verify: Open PowerShell and run `docker --version`

2. **Clone Repository**:
```powershell
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service
```

3. **Create Local Folders**:
```powershell
# Create folder structure
New-Item -ItemType Directory -Force -Path ".\scans"
New-Item -ItemType Directory -Force -Path ".\archive"
New-Item -ItemType Directory -Force -Path ".\logs"
```

4. **Create docker-compose Override**:
```powershell
# Save as docker-compose.windows.yml
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

5. **Start Service**:
```powershell
docker compose -f docker-compose.yml -f docker-compose.windows.yml up -d

# Wait for it to start
Start-Sleep -Seconds 5

# Test
Invoke-WebRequest http://localhost:8000/docs
```

6. **Access Web Interface**:
```powershell
Start-Process "http://localhost:8000"
```

#### Option B: WSL2 (For Advanced Users)

```powershell
# PowerShell as Administrator
wsl --install
wsl --set-default-version 2
wsl --install -d Ubuntu-22.04

# Inside WSL2 Ubuntu terminal
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER

# Clone and start
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service
docker compose up -d
```

#### Network Sharing (Share Across Computers)

```yaml
# docker-compose.windows.yml
version: '3.8'
services:
  pdfa:
    image: pdfa-service:latest
    container_name: ocr-scanner
    ports:
      - "0.0.0.0:8000:8000"  # Listen on all interfaces
    volumes:
      - //192.168.1.100/shared-documents/scans:/data/scans:rw
      - //192.168.1.100/shared-documents/archive:/data/archive:rw
```

#### Windows Batch Script for Monitoring

Save as `monitor-scans.cmd`:
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

    echo [%date% %time%] Processing: %%F >> "%LOG_FILE%"

    curl -X POST "%API_URL%" ^
        -F "file=@!FILE!;type=application/pdf" ^
        -F "language=deu+eng" ^
        -F "pdfa_level=2" ^
        --output "!OUTPUT!" 2>nul

    if exist "!OUTPUT!" (
        echo [%date% %time%] SUCCESS: %%F >> "%LOG_FILE%"
        del "!FILE!"
    ) else (
        echo [%date% %time%] FAILED: %%F >> "%LOG_FILE%"
    )
)

timeout /t 10 /nobreak
goto loop
```

Run with Task Scheduler:
1. Open Task Scheduler
2. Create Basic Task → Name: "OCR Scanner Monitor"
3. Trigger: On startup (or recurring)
4. Action: `cmd.exe /c C:\path\to\monitor-scans.cmd`
5. Check "Run with highest privileges"

---

### Linux Server Setup

```bash
# Ubuntu 22.04+ / Debian 12+
sudo apt update
sudo apt install -y docker.io docker-compose

sudo usermod -aG docker $USER
newgrp docker

# Clone and start
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service

# Create directories
mkdir -p {scans,archive,logs}

# Start
docker compose up -d

# Monitor
docker compose logs -f
```

---

## Docker Compose Usage Examples

### Basic Example - Single Machine

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

**Start**:
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

### Advanced - Production Setup

```yaml
version: '3.8'
services:
  pdfa:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: pdfa-ocr-prod

    ports:
      - "127.0.0.1:8000:8000"  # Local only

    volumes:
      - documents-volume:/data/documents
      - logs-volume:/data/logs
      - cache-volume:/tmp/pdfa-cache

    environment:
      - TZ=Europe/Berlin
      - LOG_LEVEL=INFO
      - MAX_WORKERS=2

    restart: unless-stopped

    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 3G
        reservations:
          cpus: '1'
          memory: 1.5G

    # Health monitoring
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    # Logging configuration
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Nginx reverse proxy
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

## Usage Examples with Docker Compose

### 1. Single File Conversion

```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@document.pdf" \
  -F "language=deu+eng" \
  -F "pdfa_level=2" \
  --output document_pdfa.pdf
```

### 2. Batch Processing - Shell Script

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

    echo "Converting: $basename"

    curl -s -X POST "$API_URL" \
        -F "file=@$file" \
        -F "language=deu+eng" \
        --output "$output"

    if [ -f "$output" ]; then
        echo "✓ Success: $output"
    else
        echo "✗ Failed: $basename"
    fi
done
```

**Run**:
```bash
chmod +x batch-convert.sh
./batch-convert.sh
```

### 3. Continuous Monitoring - Bash Script

```bash
#!/bin/bash
# monitor.sh - Watch for new PDFs and auto-convert

WATCH_DIR="./scans"
API_URL="http://localhost:8000/convert"
PROCESSED_MARKER=".processed"

while true; do
    for file in "$WATCH_DIR"/*.pdf; do
        [ ! -f "$file" ] && continue
        [ -f "$file$PROCESSED_MARKER" ] && continue

        echo "[$(date)] Processing: $(basename $file)"

        output="${file%.pdf}_pdfa.pdf"
        curl -s -X POST "$API_URL" \
            -F "file=@$file" \
            -F "language=deu+eng" \
            --output "$output"

        # Mark as processed
        touch "$file$PROCESSED_MARKER"

        # Move original to archive after 24h
        find "$WATCH_DIR" -name "*.pdf$PROCESSED_MARKER" -mtime +1 -delete
    done

    sleep 30  # Check every 30 seconds
done
```

### 4. Parallel Processing

```bash
# Convert multiple files in parallel (4 at a time)
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

## Troubleshooting

### Service Won't Start
```bash
# Check Docker
docker compose logs pdfa

# Common issues:
# 1. Port already in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# 2. Insufficient resources
docker stats

# 3. Permissions on mounted volumes
ls -la ./scans
chmod 755 ./scans
```

### Slow Processing
```bash
# Check CPU/Memory usage
docker stats pdfa

# Increase resources
# Edit docker-compose.yml:
deploy:
  resources:
    limits:
      cpus: '3'
      memory: 4G
```

### OCR Language Missing
```bash
# Install additional language
docker compose exec pdfa \
  apt-get update && apt-get install -y tesseract-ocr-fra

# Verify
docker compose exec pdfa tesseract --list-langs
```

---

## Performance Benchmarks

**Processing Time per Page** (with OCR):

| Hardware | CPU | RAM | Language | Time |
|----------|-----|-----|----------|------|
| Raspberry Pi 4 | ARM Cortex-A72 | 4GB | deu+eng | 45-90s |
| Raspberry Pi 5 | ARM Cortex-A76 | 8GB | deu+eng | 25-45s |
| Intel i7 (modern) | x86_64 | 16GB | deu+eng | 5-10s |
| AMD Ryzen 5 | x86_64 | 16GB | deu+eng | 4-8s |

---

## Next Steps

1. Choose your hardware (Raspberry Pi, Windows PC, or Linux server)
2. Follow the installation guide for your platform
3. Test with sample documents
4. Configure your scanner or workflow
5. Set up automated batch processing
6. Monitor logs and performance

For more information, see the main [README.md](README.md) and [OCR-SCANNER.md](OCR-SCANNER.md).
