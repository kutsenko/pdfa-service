# Security Policy

## Reporting Security Issues

If you discover a security vulnerability in this project, please report it by emailing the maintainers. Do not create a public GitHub issue for security vulnerabilities.

## Known Dependencies with CVEs

This document tracks known security vulnerabilities in our dependencies and explains why they are not exploitable in our use case.

### CVE-2024-23342: ecdsa Timing Attack

**Package:** `ecdsa 0.19.1` (transitive dependency from `python-jose`)
**Severity:** High (CVSS 7.8)
**Status:** No fix available (project considers it out of scope)

**Description:**
The ecdsa library is vulnerable to a Minerva timing attack on the P-256 curve that could leak the internal nonce and potentially allow private key discovery.

**Why Not Exploitable in Our Case:**
- We use **HMAC-based JWT signing exclusively** (HS256, HS384, HS512)
- We **never use ECDSA algorithms** for JWT signing
- The vulnerable ECDSA code paths are never executed in our application
- See `src/pdfa/auth_config.py:94-96` for algorithm validation that enforces HMAC-only

**Mitigation:**
- CVE ignored in CI/CD pipeline (`.github/workflows/docker-publish.yml`)
- Algorithm validation prevents accidental use of ECDSA
- Monitoring for alternative JWT libraries without ecdsa dependency

**References:**
- https://nvd.nist.gov/vuln/detail/CVE-2024-23342
- https://github.com/advisories/GHSA-wj6h-64fc-37mp

---

### GHSA-f83h-ghpp-7wcc: pdfminer.six Pickle Deserialization

**Package:** `pdfminer.six 20251107` (transitive dependency from `ocrmypdf`)
**Severity:** High (CVSS 7.8)
**Status:** No fix available

**Description:**
pdfminer.six deserializes CMap pickle files from a configurable path (`CMAP_PATH`), which could allow arbitrary code execution if an attacker can write to that path.

**Why Not Exploitable in Our Case:**
- We **do not use CMap functionality** from pdfminer.six
- The `CMAP_PATH` environment variable is **not user-controllable**
- ocrmypdf uses pdfminer.six only for PDF structure analysis, not CMap processing
- Our application does not expose any interface to modify CMAP_PATH
- The application runs in a containerized environment with restricted filesystem access

**Mitigation:**
- CVE ignored in CI/CD pipeline (`.github/workflows/docker-publish.yml`)
- Docker containers run with minimal privileges (non-root user)
- Filesystem isolation prevents arbitrary file writes
- Monitoring for ocrmypdf updates that may remove this dependency

**References:**
- https://github.com/advisories/GHSA-f83h-ghpp-7wcc
- https://github.com/pdfminer/pdfminer.six/security/advisories

---

## Security Best Practices

### Authentication (Optional Feature)

When authentication is enabled:
- JWT tokens use HMAC with secrets ≥32 characters
- OAuth 2.0 state parameter provides CSRF protection
- WebSocket authentication uses the same JWT validation
- User-scoped access control for conversion jobs

### Dependency Management

- Dependencies are regularly reviewed for security updates
- `pip-audit` runs on every pull request
- Known non-exploitable CVEs are explicitly documented and ignored
- Trivy container scanning runs on all Docker builds

### Container Security

- Multi-stage Docker builds with minimal final images
- Non-root user in production containers
- Regular base image updates (Debian Bookworm)
- Security scanning with Trivy (HIGH and CRITICAL vulnerabilities)

### Input Validation

- File upload size limits enforced
- MIME type validation for uploaded files
- OCRmyPDF runs with sandboxed execution
- Temporary files cleaned up after processing

---

## Monitoring and Updates

We continuously monitor:
- GitHub Security Advisories
- PyPI Advisory Database
- Upstream project security pages
- CVE databases

Dependencies are reviewed and updated quarterly, or immediately for exploitable vulnerabilities.

---

**Last Updated:** 2025-12-22
