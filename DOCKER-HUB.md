# Docker Hub Integration

This document describes the automated Docker image build and publishing pipeline for pdfa-service.

## Overview

GitHub Actions automatically builds and publishes Docker images to Docker Hub on:
- **Push to main branch** → tagged as `latest`
- **Version tags** (e.g., `v1.2.3`) → tagged with version numbers
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

## Image Tags

The workflow automatically creates the following tags:

| Trigger | Tags Created | Example |
|---------|--------------|---------|
| Push to main | `latest`, `main-<sha>` | `latest`, `main-a1b2c3d` |
| Version tag | `<version>`, `<major>.<minor>`, `<major>` | `1.2.3`, `1.2`, `1` |
| Branch push | `<branch>-<sha>` | `feature-xyz-a1b2c3d` |
| Pull request | `pr-<number>` | `pr-42` (build only, not pushed) |

## Usage

### Pull Latest Image

```bash
docker pull <username>/pdfa-service:latest
```

### Pull Specific Version

```bash
docker pull <username>/pdfa-service:1.2.3
```

### Run Container

```bash
docker run -p 8000:8000 <username>/pdfa-service:latest
```

## Release Process

To create a new release with automatic Docker image:

1. Update version in `pyproject.toml`
2. Commit changes
3. Create and push a version tag:

```bash
git tag v1.2.3
git push origin v1.2.3
```

GitHub Actions will automatically:
- Build the Docker image for both `linux/amd64` and `linux/arm64`
- Push with tags: `1.2.3`, `1.2`, `1`, and `latest`
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

- **Build Cache**: Uses GitHub Actions cache for faster builds
- **Multi-platform**: Builds for amd64 and arm64 architectures
- **Auto-tagging**: Intelligent tagging based on git refs
- **README Sync**: Automatically updates Docker Hub description from README.md
- **PR Validation**: Builds (but doesn't push) on pull requests

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
