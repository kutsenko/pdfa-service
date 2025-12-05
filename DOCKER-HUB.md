# Docker Hub Integration

This document describes the automated Docker image build and publishing pipeline for pdfa-service.

## Overview

GitHub Actions automatically builds and publishes **two Docker image variants** to Docker Hub:

| Variant | Tags | Features | Size |
|---------|------|----------|------|
| **Full** | `:latest`, `:1.2.3` | PDF, Office docs, Images | ~1.2 GB |
| **Minimal** | `:latest-minimal`, `:1.2.3-minimal` | PDF to PDF/A only | ~400-500 MB |

Build triggers:
- **Push to main branch** → tagged as `latest` and `latest-minimal`
- **Version tags** (e.g., `v1.2.3`) → tagged with version numbers and `-minimal` variants
- **Pull requests** → builds only (no push)

## Initial Setup

### 1. Create Docker Hub Access Token

1. Log in to [Docker Hub](https://hub.docker.com/)
2. Go to **Account Settings** → **Security** → **New Access Token**
3. Create a token with **Read & Write** permissions
4. Copy the token (you won't be able to see it again)

### 2. Configure GitHub Secrets

Add the following secrets to your GitHub repository:

1. Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username | Used for authentication |
| `DOCKERHUB_TOKEN` | Access token from step 1 | Used for authentication |

### 3. Create Docker Hub Repository

1. Log in to [Docker Hub](https://hub.docker.com/)
2. Click **Create Repository**
3. Repository name: `pdfa-service`
4. Visibility: **Public** or **Private** (your choice)
5. Click **Create**

## Image Variants

### Full Image (Default)

- **Tags**: `:latest`, `:1.2.3`, `:1.2`, `:1`
- **Features**: Complete functionality
  - PDF to PDF/A conversion
  - Office document conversion (.docx, .xlsx, .pptx)
  - OpenDocument conversion (.odt, .ods, .odp)
  - Image conversion (.jpg, .png, .tiff, .bmp, .gif)
- **Dependencies**: Includes LibreOffice for Office document support
- **Size**: ~1.2 GB
- **Use Case**: Full-featured document processing

### Minimal Image

- **Tags**: `:latest-minimal`, `:1.2.3-minimal`, `:1.2-minimal`, `:1-minimal`
- **Features**: PDF to PDF/A conversion only
  - No Office document support
  - No image conversion support
- **Dependencies**: OCRmyPDF, Tesseract, Ghostscript, qpdf (no LibreOffice)
- **Size**: ~400-500 MB (60% smaller than full image)
- **Use Case**: When you only need PDF/A conversion and want minimal footprint

**Important**: Attempting to convert Office documents or images with the minimal image will result in an error.

## Image Tags

The workflow automatically creates the following tags for **both variants**:

| Trigger | Full Image Tags | Minimal Image Tags | Example |
|---------|----------------|-------------------|---------|
| Push to main | `latest`, `sha-<hash>` | `latest-minimal`, `sha-<hash>-minimal` | `latest`, `latest-minimal` |
| Version tag | `<version>`, `<major>.<minor>`, `<major>` | `<version>-minimal`, `<major>.<minor>-minimal`, `<major>-minimal` | `1.2.3`, `1.2.3-minimal` |
| Branch push | `<branch>`, `sha-<hash>` | `<branch>-minimal`, `sha-<hash>-minimal` | `feature-xyz`, `feature-xyz-minimal` |
| Pull request | `pr-<number>` | `pr-<number>-minimal` | `pr-42`, `pr-42-minimal` (build only, not pushed) |

## Usage

### Full Image

Pull the latest full image:

```bash
docker pull <username>/pdfa-service:latest
```

Pull a specific version:

```bash
docker pull <username>/pdfa-service:1.2.3
```

Run the full image:

```bash
docker run -p 8000:8000 <username>/pdfa-service:latest
```

### Minimal Image

Pull the latest minimal image:

```bash
docker pull <username>/pdfa-service:latest-minimal
```

Pull a specific version:

```bash
docker pull <username>/pdfa-service:1.2.3-minimal
```

Run the minimal image:

```bash
docker run -p 8000:8000 <username>/pdfa-service:latest-minimal
```

### Choosing Between Variants

**Use the full image** when:
- You need to convert Office documents (.docx, .xlsx, .pptx)
- You need to convert images (.jpg, .png, .tiff)
- You want complete functionality

**Use the minimal image** when:
- You only convert PDF files to PDF/A
- You want a smaller Docker image
- You want faster image pull times
- You have storage or bandwidth constraints

## Release Process

To create a new release with automatic Docker images:

1. Update version in `pyproject.toml`
2. Commit changes
3. Create and push a version tag:

```bash
git tag v1.2.3
git push origin v1.2.3
```

GitHub Actions will automatically:
- Build **both full and minimal images** for `linux/amd64` and `linux/arm64`
- Push full image with tags: `1.2.3`, `1.2`, `1`, and `latest`
- Push minimal image with tags: `1.2.3-minimal`, `1.2-minimal`, `1-minimal`, and `latest-minimal`
- Update the Docker Hub description with README.md content

## Multi-Platform Support

The workflow builds images for:
- `linux/amd64` (Intel/AMD 64-bit)
- `linux/arm64` (ARM 64-bit, e.g., Apple Silicon, AWS Graviton)

Users on any platform can pull the appropriate image automatically:

```bash
# Automatically selects the right platform
docker pull <username>/pdfa-service:latest
```

## Workflow Features

- **Dual Image Variants**: Automatically builds both full and minimal images in parallel
- **Security Scanning**: Uses Trivy to scan Docker images for vulnerabilities
- **Python Vulnerability Scanning**: Uses pip-audit to check Python dependencies
- **Build Cache**: Uses GitHub Actions cache for faster builds
- **Multi-platform**: Builds for amd64 and arm64 architectures
- **Auto-tagging**: Intelligent tagging based on git refs with `-minimal` suffix for minimal images
- **README Sync**: Automatically updates Docker Hub description from README.md
- **PR Validation**: Builds (but doesn't push) on pull requests
- **Test-First**: All tests must pass before building images

## Troubleshooting

### Build Fails with Authentication Error

**Problem**: `Error: Cannot perform an interactive login from a non TTY device`

**Solution**: Verify that `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets are correctly set in GitHub repository settings.

### Image Not Appearing on Docker Hub

**Problem**: Build succeeds but image not visible on Docker Hub

**Solution**:
1. Check that the Docker Hub repository exists
2. Verify the repository name matches `<username>/pdfa-service`
3. Ensure the workflow didn't run on a pull request (PRs don't push images)

### Wrong Image Name

**Problem**: Image pushed to incorrect repository

**Solution**: Update the `DOCKER_IMAGE` environment variable in `.github/workflows/docker-publish.yml`:

```yaml
env:
  DOCKER_IMAGE: <your-dockerhub-username>/pdfa-service
```

## Security Notes

- Never commit Docker Hub credentials to the repository
- Use Docker Hub access tokens instead of passwords
- Regularly rotate access tokens
- Use minimal permissions for access tokens (Read & Write is sufficient)
- Review GitHub Actions logs to ensure no secrets are exposed

## Workflow File

The workflow is defined in `.github/workflows/docker-publish.yml`. Key components:

- **Checkout**: Uses `actions/checkout@v4`
- **Docker Buildx**: Uses `docker/setup-buildx-action@v3` for multi-platform builds
- **Login**: Uses `docker/login-action@v3` with secrets
- **Metadata**: Uses `docker/metadata-action@v5` for tag generation
- **Build**: Uses `docker/build-push-action@v5` with cache

## Additional Resources

- [Docker Hub Documentation](https://docs.docker.com/docker-hub/)
- [GitHub Actions Docker Documentation](https://docs.github.com/en/actions/publishing-packages/publishing-docker-images)
- [Docker Buildx Documentation](https://docs.docker.com/buildx/working-with-buildx/)
