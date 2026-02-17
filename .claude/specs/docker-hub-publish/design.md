# Docker Hub Publishing — Design

## Image Strategy

Two separate images matching the two-container architecture:

| Image | Dockerfile | Description |
|-------|-----------|-------------|
| `kaushikhazra/taskyn-core` | `Dockerfile.mcp` | MCP server (port 8000) |
| `kaushikhazra/taskyn-web` | `Dockerfile.web` | FastAPI backend + React frontend (port 3020) |

## Tagging Strategy

For a tag like `v0.6.0`, images get tagged:
- `v0.6.0` (full version)
- `0.6.0` (without v prefix)
- `0.6` (minor)
- `latest` (rolling latest)

Handled automatically by `docker/metadata-action`.

## CI/CD Pipeline

**Trigger:** Push of git tags matching `v*`
**Platform:** GitHub Actions with `ubuntu-latest`
**Multi-arch:** linux/amd64 + linux/arm64 via Docker Buildx + QEMU emulation
**Registry:** Docker Hub via `docker/login-action`

### Pipeline Flow
1. Checkout code
2. Set up QEMU (for ARM64 cross-compilation)
3. Set up Docker Buildx
4. Login to Docker Hub
5. Extract metadata (tags, labels) for both images
6. Build and push `taskyn-core` from `Dockerfile.mcp`
7. Build and push `taskyn-web` from `Dockerfile.web`

## Required GitHub Secrets

| Secret | Value |
|--------|-------|
| `DOCKERHUB_USERNAME` | Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token |

## Cleanup

- Delete root `Dockerfile` (deprecated, uses port 8020 and Python 3.11)
- Update `docker-compose.https.yml` to use `Dockerfile.mcp` instead
