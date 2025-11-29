# Docker Compose Examples

This directory contains example docker-compose configurations for different deployment scenarios.

## Available Examples

### 1. Standard Deployment (`docker-compose.standard.yml`)

Basic configuration for Linux and macOS with default settings.

```bash
docker-compose -f docker-compose.standard.yml up -d
```

**Use case**: Development, testing, local network use

---

### 2. Raspberry Pi Deployment (`docker-compose.raspberry-pi.yml`)

Optimized for Raspberry Pi 4 with:
- ARM64 architecture support
- Resource limits for stability
- Reduced memory footprint
- Slow OCR processing times

```bash
docker-compose -f docker-compose.raspberry-pi.yml up -d
```

**Use case**: Small office, home setup, budget-friendly archival

---

### 3. Windows Deployment (`docker-compose.windows.yml`)

Configured for Windows with:
- Volume binds for easy file access
- Network-accessible paths
- Docker Desktop compatibility
- WSL2 support

```bash
docker-compose -f docker-compose.windows.yml up -d
```

**Use case**: Windows 10/11 with Docker Desktop

---

### 4. Secure Deployment with Nginx (`docker-compose.secure.yml`)

Production-ready setup with:
- Reverse proxy (nginx)
- Basic authentication
- Local-only pdfa service
- Network-wide access with credentials

```bash
docker-compose -f docker-compose.secure.yml up -d
```

**Prerequisites**: Create `.htpasswd` file for authentication

```bash
# Generate .htpasswd for basic auth (username: admin)
docker run --rm httpd:2.4-alpine htpasswd -c .htpasswd admin
# (Enter password when prompted)
```

**Use case**: Production network, multiple users

---

### 5. Development Deployment (`docker-compose.dev.yml`)

For developers working on pdfa-service:
- Mounts local source code
- Enables hot-reload
- Full debug logging
- Exposed ports for debugging

```bash
docker-compose -f docker-compose.dev.yml up -d
```

**Use case**: Contributing to pdfa-service development

---

## Quick Reference

| Scenario | File | Command |
|----------|------|---------|
| Local testing | `standard` | `docker-compose -f docker-compose.standard.yml up -d` |
| Raspberry Pi | `raspberry-pi` | `docker-compose -f docker-compose.raspberry-pi.yml up -d` |
| Windows | `windows` | `docker-compose -f docker-compose.windows.yml up -d` |
| Production | `secure` | `docker-compose -f docker-compose.secure.yml up -d` |
| Development | `dev` | `docker-compose -f docker-compose.dev.yml up -d` |

---

## Common Tasks

### View Logs

```bash
docker-compose -f docker-compose.*.yml logs -f pdfa
```

### Stop Service

```bash
docker-compose -f docker-compose.*.yml down
```

### Access Service

- **Standard**: `http://localhost:8000`
- **Raspberry Pi**: `http://[pi-ip]:8000`
- **Windows**: `http://localhost:8000` or `http://[wsl2-ip]:8000`
- **Secure**: `http://[ip]:80` (with basic auth)

### Test Service

```bash
curl -X POST "http://localhost:8000/docs" -F "file=@test.pdf;type=application/pdf"
```

---

## Configuration Variables

All examples support these environment variables:

- `PYTHONUNBUFFERED=1` - Live output from Python
- `MAX_WORKERS=4` - Concurrent processing (adjust for your hardware)
- `LOG_LEVEL=INFO` - Logging level (DEBUG, INFO, WARNING, ERROR)

---

## Customization

To create a custom configuration:

1. Copy an example file: `cp docker-compose.standard.yml docker-compose.custom.yml`
2. Edit for your needs
3. Use it: `docker-compose -f docker-compose.custom.yml up -d`

---

## Troubleshooting

- **Port already in use**: Change port mapping (e.g., `9000:8000`)
- **Memory errors**: Increase Docker memory limits in Docker Desktop settings
- **Network not accessible**: Check firewall rules and network configuration
- **Slow performance**: Review resource limits for your hardware

---

See [OCR-SCANNER.md](../OCR-SCANNER.md) for detailed setup guides for each scenario.
