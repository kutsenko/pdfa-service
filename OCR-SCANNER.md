# OCR Document Scanner Guide

Using pdfa-service as a document scanner with built-in OCR for digitizing physical documents.

**Dokumentation in anderen Sprachen**: [Deutsch](OCR-SCANNER.de.md)

## Overview

This guide demonstrates how to set up pdfa-service as an OCR document scanner in a local network environment. Convert scanned PDF files (from a scanner appliance or phone app) into searchable, archivable PDF/A documents with optical character recognition.

## Use Case Scenario

**Scenario**: A small office or home setup with:
- A document scanner or smartphone scanning solution
- A central NAS/storage or local network folder
- Need to automatically convert scanned PDFs to PDF/A with OCR
- Access via simple web interface from any network device
- Regular batch processing of accumulated scans

This setup eliminates the need for expensive document management software while providing professional PDF/A archival format.

## Quick Start with Docker Compose

### Prerequisites

- **Docker** installed (version 20.10+)
- **Docker Compose** installed (either standalone or Plugin version 2.0+)
- **Network Access**: Device with scanning capability and network connectivity
- **Storage**: USB drive, NAS, or local folder for document exchange

### Docker Compose Installation

Choose one of these methods:

**Option 1: Docker Compose Plugin (Recommended)**
```bash
# Part of Docker Desktop or installed separately
docker compose version  # Verify it's installed
```

**Option 2: Standalone Docker Compose**
```bash
# Older standalone version
docker compose version  # Verify it's installed
```

Both work identically; this guide uses `docker compose` (Plugin version).

### Basic Setup (x86_64 Linux / Windows with Docker Desktop)

1. **Clone the repository**:

```bash
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service
```

2. **Start the service**:

```bash
# Using Docker Compose Plugin (recommended)
docker compose up -d

# Or using standalone docker compose
docker compose up -d
```

The API will be available at `http://localhost:8000`

2. **Upload a scanned PDF**:

```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@scanned_document.pdf;type=application/pdf" \
  -F "language=eng" \
  -F "pdfa_level=2" \
  --output digitized_document.pdf
```

3. **Access from network**:

Replace `localhost` with the machine's IP address:

```bash
curl -X POST "http://192.168.1.100:8000/convert" \
  -F "file=@scanned_document.pdf;type=application/pdf" \
  --output digitized_document.pdf
```

## Installation by Operating System

### Linux (Ubuntu 22.04+ / Debian 12+)

#### Prerequisites

```bash
# Install Docker and Docker Compose
sudo apt update
sudo apt install -y docker.io docker-compose

# Add current user to docker group (optional, to run without sudo)
sudo usermod -aG docker $USER
newgrp docker
```

#### Run the Service

```bash
# Clone repository
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service

# Start with Docker Compose Plugin (recommended)
docker compose up -d

# Or using standalone docker compose
docker compose up -d

# Check service status
docker compose logs -f
# or: docker compose logs -f
```

Service available at: `http://localhost:8000`

---

### Raspberry Pi Setup

**Recommended**: Raspberry Pi 4 with 4GB+ RAM, 32GB+ SD card

#### Considerations for Raspberry Pi

- **Architecture**: ARM64 (64-bit OS required for OCR efficiency)
- **OS**: Raspberry Pi OS (64-bit) or Ubuntu 22.04 LTS (ARM64)
- **Performance**: OCR processing will be slower than x86_64 (30-60 seconds per page)
- **Storage**: Use external USB SSD or NAS for document storage

#### Installation Steps

1. **Install Raspberry Pi OS 64-bit**:
   - Download from [raspberrypi.com](https://www.raspberrypi.com/software/)
   - Use Raspberry Pi Imager to write to SD card

2. **Update system**:

```bash
sudo apt update && sudo apt upgrade -y
```

3. **Install Docker**:

```bash
# Install Docker using official script
curl -fsSL https://get.docker.com | sh

# Add pi user to docker group
sudo usermod -aG docker pi

# Enable Docker to start on boot
sudo systemctl enable docker
```

4. **Install Docker Compose**:

```bash
# For Raspberry Pi 4 (ARM64)
sudo apt install -y docker-compose

# Or using pip3 (alternative)
sudo pip3 install docker-compose
```

5. **Configure for Raspberry Pi**:

Edit `docker-compose.yml` and modify resource limits:

```yaml
services:
  pdfa:
    # ... existing config ...

    # Add resource limits for Pi stability
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 1500M
        reservations:
          cpus: '0.5'
          memory: 512M
```

6. **Start the service**:

```bash
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service
docker compose up -d
# or: docker compose up -d
```

7. **Find Raspberry Pi IP address**:

```bash
hostname -I
# Output: 192.168.1.50
```

Access from any device on network: `http://192.168.1.50:8000`

#### Performance Tips for Raspberry Pi

- Process one document at a time (avoid parallel uploads)
- Use `--language eng` if German OCR not needed (reduces processing time)
- Consider disabling OCR for pre-digitized documents: `ocr_enabled=false`
- Monitor disk space; store converted PDFs on external SSD/NAS

---

### Windows 10/11 Setup

#### Option A: Using WSL2 (Windows Subsystem for Linux)

**Advantages**: Native Docker performance, Linux environment

1. **Enable WSL2**:

```powershell
# Run PowerShell as Administrator
wsl --install
wsl --set-default-version 2
```

2. **Install Ubuntu in WSL2**:

```powershell
wsl --install -d Ubuntu-22.04
```

3. **Inside WSL2 terminal** (start Ubuntu):

```bash
# Update package list
sudo apt update

# Install Docker and Docker Compose
sudo apt install -y docker.io docker-compose

# Configure Docker socket permissions
sudo usermod -aG docker $USER
```

4. **Clone and start service**:

```bash
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service

# Using Docker Compose Plugin (recommended)
docker compose up -d

# Or using standalone docker compose
docker compose up -d
```

5. **Access from Windows**:

```powershell
# Find WSL2 IP address (from PowerShell)
wsl hostname -I

# Example: http://172.20.10.50:8000
```

#### Option B: Docker Desktop for Windows

**Advantages**: GUI, easier setup, automatic resource management

1. **Download and Install**:
   - Download [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Install with default settings
   - Restart computer if prompted

2. **Clone repository**:

```powershell
# Using PowerShell or Git Bash
git clone https://github.com/kutsenko/pdfa-service.git
cd pdfa-service
```

3. **Start service**:

```powershell
# Using Docker Compose Plugin (recommended)
docker compose up -d

# Or using standalone docker compose
docker compose up -d
```

4. **Access service**:

```powershell
# Access from Windows
Start-Process "http://localhost:8000"
```

#### Windows Storage Integration

Mount a shared folder for document exchange:

```yaml
# In docker compose.yml
services:
  pdfa:
    # ... existing config ...
    volumes:
      - ./scans:/data/scans
      - ./archive:/data/archive
```

Create folders in Windows:

```powershell
New-Item -ItemType Directory -Path ".\scans"
New-Item -ItemType Directory -Path ".\archive"
```

Drop scanned PDFs into `.\scans`, retrieve converted documents from `.\archive`.

---

## Usage Examples

### Web Interface Upload

For a browser-based interface, deploy a simple HTML form:

```html
<!DOCTYPE html>
<html>
<head>
    <title>OCR Document Scanner</title>
    <style>
        body { font-family: Arial; max-width: 600px; margin: 50px auto; }
        input { padding: 10px; margin: 10px 0; width: 100%; }
        button { padding: 10px 20px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>📄 Document Scanner</h1>
    <form id="uploadForm">
        <input type="file" id="file" accept=".pdf" required>
        <select id="language">
            <option value="eng">English</option>
            <option value="deu">German</option>
            <option value="eng+deu">English + German</option>
        </select>
        <select id="pdfa_level">
            <option value="2" selected>PDF/A-2</option>
            <option value="3">PDF/A-3</option>
        </select>
        <button type="submit">Convert to PDF/A</button>
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
                document.getElementById('result').textContent = '✓ Conversion successful!';
            } else {
                document.getElementById('result').textContent = '✗ Conversion failed';
            }
        } catch (error) {
            document.getElementById('result').textContent = '✗ Error: ' + error;
        }
    });
    </script>
</body>
</html>
```

Save as `index.html` and serve alongside the API.

### Batch Processing Script

Convert a folder of scanned PDFs automatically:

```bash
#!/bin/bash
# batch-ocr-scan.sh - Process all PDFs in a folder

SCAN_FOLDER="${1:-.}"
API_URL="${2:-http://localhost:8000/convert}"
LANGUAGE="${3:-eng+deu}"
OUTPUT_SUFFIX="_pdfa"

echo "Processing PDFs in: $SCAN_FOLDER"
echo "API: $API_URL"

for pdf in "$SCAN_FOLDER"/*.pdf; do
    [ ! -f "$pdf" ] && continue

    filename=$(basename "$pdf" .pdf)
    output="${SCAN_FOLDER}/${filename}${OUTPUT_SUFFIX}.pdf"

    echo "Converting: $filename..."

    curl -s -X POST "$API_URL" \
        -F "file=@$pdf;type=application/pdf" \
        -F "language=$LANGUAGE" \
        -F "pdfa_level=2" \
        --output "$output" 2>/dev/null

    if [ -f "$output" ]; then
        echo "  ✓ Success -> $output"
    else
        echo "  ✗ Failed"
    fi
done

echo "Done!"
```

**Usage**:

```bash
chmod +x batch-ocr-scan.sh
./batch-ocr-scan.sh ~/Documents/Scans http://192.168.1.50:8000/convert eng+deu
```

### Integration with Scanning Appliance

Most office scanners support uploading to an HTTP endpoint:

1. In scanner settings, configure: `http://[pi-ip]:8000/convert`
2. Set output format to PDF
3. Configure OCR language in scanner UI
4. Test with single document
5. Enable automatic upload after each scan

### Folder Monitoring (Auto-Processing)

Watch a folder and automatically convert new PDFs:

```bash
#!/bin/bash
# monitor-and-convert.sh

WATCH_DIR="$1"
API_URL="${2:-http://localhost:8000/convert}"

echo "Monitoring $WATCH_DIR for new PDFs..."

while true; do
    for pdf in "$WATCH_DIR"/*.pdf; do
        [ ! -f "$pdf" ] && continue

        # Skip if already processed
        [ -f "$pdf.processing" ] && continue

        touch "$pdf.processing"
        echo "Processing: $(basename $pdf)"

        curl -s -X POST "$API_URL" \
            -F "file=@$pdf;type=application/pdf" \
            -F "language=eng+deu" \
            --output "${pdf%.pdf}_pdfa.pdf"

        rm "$pdf.processing"
    done

    sleep 5  # Check every 5 seconds
done
```

---

## Network Configuration

### Local Network Access

**Raspberry Pi / Linux Server**:

```bash
# Find IP address
hostname -I

# Access from other device
curl http://192.168.1.50:8000/convert ...
```

**Windows with Docker Desktop**:

```powershell
# Docker Desktop IP is usually localhost:8000
# Or find WSL2 IP:
wsl hostname -I
```

### Port Configuration

Expose different port if 8000 is in use:

```yaml
# docker compose.yml
services:
  pdfa:
    ports:
      - "9000:8000"  # Access at :9000
```

### Firewall Rules

**Linux**:

```bash
sudo ufw allow 8000/tcp
sudo ufw enable
```

**Windows** (Windows Defender Firewall):

1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Add docker or wsl2 to allowed apps
4. Ensure "Private networks" is checked

---

## Performance & Optimization

### Processing Times

Typical OCR processing times per page:

| Device | Language | Time |
|--------|----------|------|
| Raspberry Pi 4 (ARM64) | English | 30-60s |
| Raspberry Pi 4 (ARM64) | English + German | 45-90s |
| Modern x86_64 CPU | English | 5-10s |
| Modern x86_64 CPU | English + German | 8-15s |

### Optimization Tips

1. **Disable OCR for pre-digitized documents**:
   ```bash
   curl ... -F "ocr_enabled=false" ...
   ```

2. **Use single language when possible**:
   ```bash
   curl ... -F "language=eng" ...  # Faster than eng+deu
   ```

3. **Process in sequence** (avoid parallel uploads on Pi):
   ```bash
   # Good: Sequential processing
   for pdf in *.pdf; do
       curl ... "$pdf" ...
       wait  # Wait for completion
   done
   ```

4. **Allocate sufficient resources in docker compose.yml**:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 2G
   ```

5. **Use PDF/A-2** (default, faster than PDF/A-3):
   ```bash
   curl ... -F "pdfa_level=2" ...
   ```

---

## Security Considerations

⚠️ **Important for Production Use**

### Local Network Only

The default setup is suitable for **local network use only**:

```yaml
# docker compose.yml
services:
  pdfa:
    ports:
      - "127.0.0.1:8000:8000"  # Only accessible from localhost
```

To allow network access (with caution):

```yaml
ports:
  - "8000:8000"  # Accessible from any network device
```

### Reverse Proxy with Authentication (Recommended)

For network-wide access, use a reverse proxy:

```yaml
# docker compose.yml with nginx
version: '3.8'
services:
  pdfa:
    image: pdfa-service:latest
    ports:
      - "127.0.0.1:8000:8000"  # Only local access

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - pdfa
```

**nginx.conf** (with basic auth):

```nginx
events { worker_connections 1024; }
http {
  server {
    listen 80;

    # Add basic authentication
    location / {
      auth_basic "Restricted";
      auth_basic_user_file /etc/nginx/.htpasswd;

      proxy_pass http://pdfa:8000;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
    }
  }
}
```

### File Upload Limits

Set maximum upload size in docker compose:

```yaml
environment:
  - MAX_UPLOAD_SIZE=100M  # Limit large files
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs (Docker Compose Plugin)
docker compose logs pdfa
# or: docker compose logs pdfa

# Common issue: Port already in use
sudo lsof -i :8000  # Find process using port 8000

# Kill process and restart
docker compose restart
# or: docker compose restart
```

### OCR Errors

```bash
# Check if Tesseract is available
docker compose exec pdfa which tesseract
# or: docker compose exec pdfa which tesseract

# Install missing language pack (inside container)
docker compose exec pdfa apt-get update && apt-get install -y tesseract-ocr-fra
# or: docker compose exec pdfa apt-get update && apt-get install -y tesseract-ocr-fra
```

### Slow Processing

- Reduce concurrent uploads
- Monitor CPU usage: `docker stats`
- Check available disk space: `df -h`
- Consider upgrading language option to single language

### Network Access Issues

```bash
# From scanner/client device, test connectivity
ping 192.168.1.50  # Ping Raspberry Pi
curl http://192.168.1.50:8000/docs  # Test API

# From Pi, check service is running
docker compose ps
docker compose logs pdfa
```

---

## Maintenance

### Regular Cleanup

```bash
#!/bin/bash
# Cleanup old files

# Remove converted PDFs older than 30 days
find ./archive -name "*_pdfa.pdf" -mtime +30 -delete

# Prune Docker images
docker image prune -a --filter "until=720h"
```

### Monitor Disk Usage

```bash
# Check Docker volume usage
docker system df

# Clean up unused volumes
docker volume prune
```

### Update Service

```bash
# Pull latest image
docker compose pull
# or: docker compose pull

# Restart with new version
docker compose down
docker compose up -d
# or: docker compose down && docker compose up -d
```

---

## References

- [OCRmyPDF Documentation](https://ocrmypdf.readthedocs.io/)
- [Docker Documentation](https://docs.docker.com/)
- [Raspberry Pi Setup Guide](https://www.raspberrypi.com/documentation/)
- [PDF/A Specification](https://en.wikipedia.org/wiki/PDF/A)

---

## Next Steps

- Test with sample scanned PDFs
- Configure document naming conventions
- Set up scheduled cleanup tasks
- Document your workflow and language settings

Happy document scanning! 📋✨
