# Nginx Reverse Proxy with Let's Encrypt SSL/TLS

**Documentation in other languages**: [Deutsch (German)](README.de.md)

This example demonstrates how to deploy the PDF/A conversion service behind an Nginx reverse proxy with automatic SSL/TLS certificates from Let's Encrypt using Certbot.

## Features

- **Automatic SSL/TLS**: Free certificates from Let's Encrypt
- **Auto-Renewal**: Certbot automatically renews certificates
- **HTTPS Enforcement**: HTTP traffic redirected to HTTPS
- **Modern Security**: TLS 1.2+ with strong ciphers
- **Security Headers**: HSTS, CSP, X-Frame-Options, etc.
- **Large File Support**: Configured for 100MB maximum upload size
- **Extended Timeouts**: Allows long-running OCR operations
- **Production Ready**: Complete setup for public-facing deployment

## Architecture

```
Internet
  ↓
Port 80 (HTTP) → Redirect to HTTPS
Port 443 (HTTPS) ← Let's Encrypt SSL
  ↓
Nginx Reverse Proxy
  ↓
pdfa-service:8000 (internal network)
  ↑
Certbot (automatic renewal every 12h)
```

## Prerequisites

1. **Domain Name**: You need a domain pointing to your server
   - Example: `doc.example.com`
   - DNS A record must point to your server's IP address

2. **Public Server**: Must be accessible from the internet
   - Ports 80 and 443 must be open
   - Let's Encrypt needs to verify domain ownership

3. **Docker & Docker Compose**: Installed and running

## Quick Start

### 1. Configure Your Domain

Edit `init-letsencrypt.sh` and update the configuration:

```bash
# Change this to your actual domain
domains=(doc.example.com)

# Add your email for Let's Encrypt notifications
email="admin@example.com"

# Use staging mode for testing (optional)
staging=0  # Set to 1 for testing, 0 for production
```

Also update `nginx.conf` - replace all instances of `doc.example.com` with your domain:

```bash
# Quick replace (Linux/macOS)
sed -i 's/doc\.example\.com/yourdomain.com/g' nginx.conf

# Or manually edit nginx.conf and change:
# server_name doc.example.com;
# ssl_certificate /etc/letsencrypt/live/doc.example.com/...
```

### 2. Initialize Let's Encrypt

Run the initialization script:

```bash
./init-letsencrypt.sh
```

The script will:
1. Download recommended TLS parameters
2. Create a dummy certificate
3. Start nginx
4. Request real certificate from Let's Encrypt
5. Reload nginx with the real certificate

**Note**: First run should use `staging=1` to test your setup and avoid rate limits.

### 3. Verify Setup

```bash
# Check if all containers are running
docker-compose ps

# Check certificate
docker-compose exec nginx ls -la /etc/letsencrypt/live/

# Test HTTPS access
curl https://yourdomain.com/health
```

### 4. Access Your Service

Open your browser and navigate to:
```
https://yourdomain.com
```

You should see a valid SSL certificate and the pdfa-service web UI.

## Configuration

### Change Domain

1. Update `init-letsencrypt.sh`:
   ```bash
   domains=(your-domain.com www.your-domain.com)
   ```

2. Update `nginx.conf`:
   ```nginx
   server_name your-domain.com www.your-domain.com;
   ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
   ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
   ```

3. Re-run initialization:
   ```bash
   ./init-letsencrypt.sh
   ```

### Multiple Domains

You can secure multiple domains with a single setup:

```bash
# In init-letsencrypt.sh
domains=(doc.example.com pdf.example.com)
```

Each domain needs:
- Separate `server` block in nginx.conf
- DNS A record pointing to your server

### Adjust Upload Size Limit

Edit `nginx.conf`:
```nginx
# Change from 100M to your desired size
client_max_body_size 500M;
```

Then reload nginx:
```bash
docker-compose exec nginx nginx -s reload
```

### Modify Timeouts

Edit `nginx.conf`:
```nginx
# Adjust for very large files or slow processing
proxy_connect_timeout 600s;
proxy_send_timeout 600s;
proxy_read_timeout 600s;
```

### Configure PDF Compression

Edit `docker-compose.yml` environment variables:
```yaml
pdfa:
  environment:
    - PDFA_IMAGE_DPI=150
    - PDFA_JPG_QUALITY=85
    - PDFA_OPTIMIZE=1
```

See [COMPRESSION.md](../../COMPRESSION.md) for detailed documentation.

## Certificate Management

### Automatic Renewal

Certbot container checks for renewal every 12 hours automatically. No manual intervention needed.

### Manual Renewal

Force certificate renewal:

```bash
docker-compose run --rm certbot renew
docker-compose exec nginx nginx -s reload
```

### Check Certificate Expiry

```bash
docker-compose run --rm certbot certificates
```

### Revoke Certificate

```bash
docker-compose run --rm certbot revoke \
  --cert-path /etc/letsencrypt/live/yourdomain.com/cert.pem
```

## Testing with Staging

Let's Encrypt has rate limits (50 certificates per domain per week). Use staging mode for testing:

1. Set `staging=1` in `init-letsencrypt.sh`
2. Run `./init-letsencrypt.sh`
3. Browser will show certificate warning (expected)
4. Once confirmed working, set `staging=0`
5. Run `./init-letsencrypt.sh` again for production certificate

## Troubleshooting

### Certificate Request Failed

**Problem**: Certbot can't obtain certificate

**Solutions**:
- Verify DNS A record points to your server: `dig yourdomain.com`
- Check ports 80 and 443 are open: `netstat -tuln | grep -E '80|443'`
- Ensure domain is accessible: `curl http://yourdomain.com/.well-known/acme-challenge/test`
- Check certbot logs: `docker-compose logs certbot`

### nginx Won't Start

**Problem**: nginx fails to start after certificate installation

**Solutions**:
- Check nginx configuration syntax: `docker-compose exec nginx nginx -t`
- Verify certificate files exist: `docker-compose exec nginx ls -la /etc/letsencrypt/live/`
- Check nginx logs: `docker-compose logs nginx`
- Ensure domain name matches in nginx.conf and certificate path

### Browser Shows Certificate Error

**Problem**: Browser shows "Not Secure" or certificate warning

**Solutions**:
- If using staging mode, this is expected (staging certs are not trusted)
- Check certificate is for correct domain: `docker-compose run --rm certbot certificates`
- Verify certificate dates are valid
- Clear browser cache and try again
- Use production mode (`staging=0`) for trusted certificates

### Rate Limit Exceeded

**Problem**: Let's Encrypt rate limit hit

**Solutions**:
- Wait 7 days for rate limit reset
- Use staging mode for testing
- Check rate limits: https://letsencrypt.org/docs/rate-limits/
- Consider using wildcard certificates if you have many subdomains

### Certificate Not Renewing

**Problem**: Automatic renewal fails

**Solutions**:
- Check certbot container is running: `docker-compose ps`
- Test renewal manually: `docker-compose run --rm certbot renew --dry-run`
- Ensure port 80 is accessible (required for renewal)
- Check certbot logs: `docker-compose logs certbot`

## Security Recommendations

1. **Keep Software Updated**: Regularly update Docker images
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

2. **Monitor Certificate Expiry**: Set up monitoring alerts
   - Let's Encrypt certificates are valid for 90 days
   - Auto-renewal happens at 30 days before expiry

3. **Firewall Configuration**:
   - Only open ports 80 and 443
   - Block direct access to port 8000
   - Use fail2ban for brute force protection

4. **HSTS Configuration**: Already enabled in nginx.conf
   - Browsers will only use HTTPS after first visit
   - Consider adding domain to HSTS preload list

5. **Regular Backups**: Backup certificate data
   ```bash
   tar -czf certbot-backup-$(date +%Y%m%d).tar.gz certbot/
   ```

6. **Security Headers**: All important headers are configured
   - Review CSP policy for your specific needs
   - Adjust X-Frame-Options if embedding is needed

## Production Checklist

- [ ] Domain DNS configured correctly
- [ ] Ports 80 and 443 open in firewall
- [ ] init-letsencrypt.sh configured with your domain and email
- [ ] nginx.conf updated with your domain name
- [ ] Tested with staging=1 first
- [ ] Production certificates obtained (staging=0)
- [ ] All services running: `docker-compose ps`
- [ ] HTTPS working: `curl https://yourdomain.com/health`
- [ ] HTTP redirects to HTTPS
- [ ] Certificate auto-renewal tested
- [ ] Upload size limits configured
- [ ] Compression settings optimized
- [ ] Monitoring/alerts set up
- [ ] Backup strategy implemented

## Files in This Example

- `nginx.conf` - Nginx reverse proxy configuration with SSL/TLS
- `docker-compose.yml` - Complete service stack (nginx, pdfa, certbot)
- `init-letsencrypt.sh` - Certificate initialization script
- `README.md` - This file (English)
- `README.de.md` - German documentation

## Directory Structure After Setup

```
nginx-letsencrypt/
├── certbot/
│   ├── conf/
│   │   ├── live/
│   │   │   └── yourdomain.com/
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

## Migrating from HTTP to HTTPS

If you're upgrading an existing HTTP deployment:

1. Ensure all data is backed up
2. Update DNS (if needed)
3. Run `./init-letsencrypt.sh`
4. Test thoroughly
5. Update any API clients to use HTTPS URLs

## Further Reading

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)
- [Nginx SSL Configuration](https://nginx.org/en/docs/http/configuring_https_servers.html)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [pdfa-service Documentation](../../README.md)
- [Compression Configuration](../../COMPRESSION.md)

## Support

For issues specific to this example:
1. Verify DNS is configured correctly
2. Check ports 80 and 443 are accessible
3. Review certbot and nginx logs
4. Test with staging mode first

For pdfa-service issues, see the [main README](../../README.md).

## Credits

Based on the excellent [nginx-certbot](https://github.com/wmnnd/nginx-certbot) project by Philipp Schmieder.
