# pdfa-service Examples

**Documentation in other languages**: [Deutsch (German)](README.de.md)

This directory contains ready-to-use configuration examples and deployment scenarios for the pdfa-service.

## Available Examples

### 🔒 [Nginx Reverse Proxy with Basic Auth](nginx-reverse-proxy/)

Deploy pdfa-service behind an Nginx reverse proxy with HTTP Basic Authentication for secure access control.

**Features:**
- HTTP Basic Authentication with username/password
- SSL/TLS ready configuration
- Security headers (X-Frame-Options, CSP, etc.)
- Large file upload support (configurable up to 500MB+)
- Extended timeouts for long OCR operations
- Health check endpoint for monitoring
- Complete isolation (pdfa-service not directly accessible)

**Use Cases:**
- Production deployment with access control
- Internal company document processing service
- Shared team resource with user management
- Internet-facing service with authentication

**Files:**
- `nginx.conf` - Complete Nginx configuration
- `docker-compose.yml` - Multi-container setup
- `htpasswd/.htpasswd.example` - Password file template
- `README.md` / `README.de.md` - Detailed setup guide

[→ Go to Nginx Reverse Proxy example](nginx-reverse-proxy/)

---

### 🔐 [Nginx Reverse Proxy with Let's Encrypt SSL/TLS](nginx-letsencrypt/)

Deploy pdfa-service with automatic SSL/TLS certificates from Let's Encrypt using Certbot for production-ready HTTPS.

**Features:**
- Automatic SSL/TLS certificates from Let's Encrypt
- Automatic certificate renewal every 12 hours
- HTTPS enforcement (HTTP to HTTPS redirect)
- Modern TLS 1.2/1.3 with strong ciphers
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Large file upload support (configurable up to 500MB+)
- Extended timeouts for long OCR operations
- Production-ready public-facing deployment

**Use Cases:**
- Public-facing PDF conversion service
- Production deployment with valid SSL certificates
- Professional document processing service
- Internet-accessible service with encryption

**Files:**
- `nginx.conf` - Nginx configuration with SSL/TLS
- `docker-compose.yml` - Multi-container setup (nginx, pdfa, certbot)
- `init-letsencrypt.sh` - Certificate initialization script
- `README.md` / `README.de.md` - Detailed setup guide

**Requirements:**
- Domain name (e.g., doc.example.com)
- Public server with ports 80 and 443 accessible
- DNS A record pointing to your server

[→ Go to Let's Encrypt SSL/TLS example](nginx-letsencrypt/)

---

## Contributing Examples

Have a useful deployment scenario or configuration? We welcome contributions!

### Example Ideas

- **Load Balancer**: Multi-instance pdfa-service with load balancing
- **S3 Integration**: Automatic upload of converted PDFs to S3
- **Kubernetes**: K8s deployment with ingress and secrets
- **Traefik**: Alternative reverse proxy with Let's Encrypt
- **Monitoring**: Prometheus + Grafana integration
- **Queue System**: Redis/RabbitMQ for background processing
- **API Gateway**: Kong or similar API management
- **Cloud Deployments**: AWS ECS, Azure Container Instances, GCP Cloud Run

### Submission Guidelines

1. Create a new directory under `examples/`
2. Include complete, working configuration files
3. Add bilingual README (English + German)
4. Test thoroughly before submitting
5. Document all prerequisites and dependencies
6. Include a docker-compose.yml when possible
7. Add security considerations section
8. Update this index file

## Example Template Structure

```
examples/
└── your-example-name/
    ├── README.md              # English documentation
    ├── README.de.md           # German documentation
    ├── docker-compose.yml     # Complete setup
    ├── config/                # Configuration files
    │   └── ...
    └── scripts/               # Helper scripts (optional)
        └── ...
```

## Testing Examples

Before using any example in production:

1. **Test in development**: Use a test environment first
2. **Review security**: Check authentication, firewall rules, SSL/TLS
3. **Adjust limits**: Configure upload sizes, timeouts for your needs
4. **Monitor performance**: Test with realistic file sizes and volumes
5. **Update credentials**: Change all default passwords
6. **Backup configurations**: Keep copies of working configs

## Support

For issues with specific examples:
1. Check the example's README for troubleshooting
2. Verify all prerequisites are met
3. Review Docker and Docker Compose logs
4. Test the base pdfa-service works standalone

For general pdfa-service issues, see the [main README](../README.md).

## License

All examples are provided under the same license as pdfa-service. See [LICENSE](../LICENSE) for details.
