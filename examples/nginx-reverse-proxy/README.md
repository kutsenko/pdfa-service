# Nginx Reverse Proxy with Basic Authentication

**Documentation in other languages**: [Deutsch (German)](README.de.md)

This example demonstrates how to deploy the PDF/A conversion service behind an Nginx reverse proxy with HTTP Basic Authentication for secure access control.

## Features

- **Basic Authentication**: Protects the service with username/password authentication
- **Reverse Proxy**: Nginx forwards requests to the pdfa-service backend
- **Security Headers**: Adds standard security headers (X-Frame-Options, X-Content-Type-Options, etc.)
- **Large File Support**: Configured for 100MB maximum upload size
- **Extended Timeouts**: Allows long-running OCR operations (up to 5 minutes)
- **Health Check Endpoint**: Monitoring endpoint without authentication
- **Complete Isolation**: pdfa-service only accessible through nginx (no direct access)

## Architecture

```
Internet/Network
      ↓
   Port 8080 (nginx)
      ↓
  Basic Auth Check
      ↓
  Nginx Reverse Proxy
      ↓
  pdfa-service:8000 (internal network only)
```

## Quick Start

### 1. Create Password File

First, create your `.htpasswd` file with user credentials:

**Option A: Using htpasswd (recommended)**
```bash
# Install apache2-utils (Debian/Ubuntu)
sudo apt-get install apache2-utils

# Create .htpasswd with first user
htpasswd -c htpasswd/.htpasswd admin

# Add additional users (without -c flag)
htpasswd htpasswd/.htpasswd user2
```

**Option B: Using openssl**
```bash
# Create password and add to .htpasswd
echo "admin:$(openssl passwd -apr1)" > htpasswd/.htpasswd
```

**Option C: Copy example file**
```bash
# Use example file with default credentials (admin/changeme)
# WARNING: Change password immediately in production!
cp htpasswd/.htpasswd.example htpasswd/.htpasswd
```

### 2. Start Services

```bash
# From this directory
docker-compose up -d
```

### 3. Test Access

```bash
# Without authentication (should fail with 401)
curl http://localhost:8080/

# With authentication
curl -u admin:yourpassword http://localhost:8080/

# Test conversion endpoint
curl -u admin:yourpassword \
  -F "file=@test.pdf" \
  -F "language=eng" \
  -F "pdfa_level=2" \
  http://localhost:8080/convert \
  -o output.pdf
```

### 4. Access Web UI

Open your browser and navigate to:
```
http://localhost:8080/
```

You will be prompted for username and password.

## Configuration

### Change Port

Edit `docker-compose.yml`:
```yaml
nginx:
  ports:
    - "80:80"  # Change 8080 to your desired port
```

### Adjust Upload Size Limit

Edit `nginx.conf`:
```nginx
# Change from 100M to your desired size
client_max_body_size 500M;
```

### Modify Timeouts

Edit `nginx.conf`:
```nginx
# Adjust timeouts for very large files or slow processing
proxy_connect_timeout 600s;
proxy_send_timeout 600s;
proxy_read_timeout 600s;
```

### Configure PDF Compression

Edit `docker-compose.yml` environment variables:
```yaml
pdfa:
  environment:
    - PDFA_IMAGE_DPI=150          # Adjust quality
    - PDFA_JPG_QUALITY=85
    - PDFA_OPTIMIZE=1
```

See [COMPRESSION.md](../../COMPRESSION.md) for detailed documentation.

### Add Custom Domain

1. Update `nginx.conf`:
```nginx
server {
    listen 80;
    server_name pdfa.yourdomain.com;  # Change this
    # ... rest of config
}
```

2. Update your DNS to point to the server
3. Consider adding SSL/TLS (see SSL Setup below)

## SSL/TLS Setup (HTTPS)

For production use, add SSL/TLS encryption:

### Option 1: Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d pdfa.yourdomain.com

# Certbot will automatically update nginx.conf
```

### Option 2: Manual SSL Configuration

1. Obtain SSL certificates (from your CA or Let's Encrypt)

2. Update `nginx.conf`:
```nginx
server {
    listen 443 ssl http2;
    server_name pdfa.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... rest of config
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name pdfa.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

3. Mount certificates in `docker-compose.yml`:
```yaml
nginx:
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf:ro
    - ./htpasswd/.htpasswd:/etc/nginx/.htpasswd:ro
    - ./ssl:/etc/nginx/ssl:ro  # Add SSL certificates
```

## User Management

### Add New User

```bash
htpasswd htpasswd/.htpasswd newuser
```

### Remove User

Edit `htpasswd/.htpasswd` and remove the user's line.

### Change Password

```bash
htpasswd htpasswd/.htpasswd existinguser
```

### List Users

```bash
cut -d: -f1 htpasswd/.htpasswd
```

## Monitoring and Logs

### View Logs

```bash
# Nginx access logs
docker-compose logs -f nginx

# pdfa-service logs
docker-compose logs -f pdfa

# Both services
docker-compose logs -f
```

### Health Check

Nginx includes a health check endpoint (no authentication required):

```bash
curl http://localhost:8080/health
# Should return: healthy
```

Use this endpoint for monitoring tools (Prometheus, Nagios, etc.).

## Security Recommendations

1. **Change Default Credentials**: Never use the example `.htpasswd` in production
2. **Use Strong Passwords**: Generate secure passwords for all users
3. **Enable HTTPS**: Always use SSL/TLS in production environments
4. **Limit Upload Size**: Adjust `client_max_body_size` to your needs
5. **Regular Updates**: Keep nginx and pdfa-service Docker images updated
6. **Firewall**: Only expose port 80/443, block direct access to port 8000
7. **Log Monitoring**: Regularly review nginx access logs for suspicious activity

## Troubleshooting

### 401 Unauthorized Error

- Check that `.htpasswd` file exists: `ls -la htpasswd/.htpasswd`
- Verify file permissions: `chmod 644 htpasswd/.htpasswd`
- Test credentials manually
- Check nginx logs: `docker-compose logs nginx`

### 502 Bad Gateway Error

- Ensure pdfa-service is running: `docker-compose ps`
- Check pdfa-service logs: `docker-compose logs pdfa`
- Verify network connectivity: `docker-compose exec nginx ping pdfa`

### Upload Too Large Error (413)

- Increase `client_max_body_size` in `nginx.conf`
- Restart nginx: `docker-compose restart nginx`

### Timeout Errors

- Increase timeout values in `nginx.conf`
- Check if file processing is taking too long
- Review pdfa-service logs for errors

### Connection Refused

- Verify port is not already in use: `netstat -tuln | grep 8080`
- Check Docker network: `docker network ls`
- Ensure both services are on the same network

## Production Checklist

- [ ] Custom `.htpasswd` with strong passwords created
- [ ] SSL/TLS certificates configured
- [ ] Custom domain configured
- [ ] Firewall rules in place
- [ ] Upload size limits adjusted for your use case
- [ ] Compression settings optimized
- [ ] Log rotation configured
- [ ] Monitoring/health checks set up
- [ ] Backup strategy for configurations
- [ ] Documentation for your team

## Files in This Example

- `nginx.conf` - Nginx reverse proxy configuration
- `docker-compose.yml` - Complete service stack
- `htpasswd/.htpasswd.example` - Example password file
- `htpasswd/.gitignore` - Protects real credentials from git
- `README.md` - This file (English)
- `README.de.md` - German documentation

## Further Reading

- [Nginx Documentation](https://nginx.org/en/docs/)
- [HTTP Basic Authentication](https://en.wikipedia.org/wiki/Basic_access_authentication)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [pdfa-service Documentation](../../README.md)
- [Compression Configuration](../../COMPRESSION.md)

## Support

For issues specific to this example, please check:
1. Docker and Docker Compose are properly installed
2. Ports are not already in use
3. File permissions are correct
4. Both services are running

For pdfa-service issues, see the [main README](../../README.md).
