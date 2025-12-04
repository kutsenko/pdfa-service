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
