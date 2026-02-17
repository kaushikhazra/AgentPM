# Docker Hub Publishing — Tasks

- [x] Create GitHub Actions workflow `.github/workflows/docker-publish.yml`
  - [x] Configure trigger on `v*` tag push
  - [x] Set up QEMU + Buildx for multi-platform builds
  - [x] Add Docker Hub login step
  - [x] Add metadata extraction for both images
  - [x] Add build+push for `taskyn-core` (from `Dockerfile.mcp`)
  - [x] Add build+push for `taskyn-web` (from `Dockerfile.web`)
  _US-2: Automated image publishing on release_
  _US-3: Multi-platform support_

- [x] Clean up deprecated Dockerfile
  - [x] Delete root `Dockerfile`
  - [x] Update `docker-compose.https.yml` to reference `Dockerfile.mcp`
  - [x] Update `Caddyfile` reverse_proxy from port 8020 to 8000
  _US-4: Clean Docker configuration_

- [ ] Manual setup (Kaushik)
  - [ ] Create Docker Hub account / access token
  - [ ] Add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` as GitHub repo secrets
  - [ ] Test with `git tag v0.6.0-rc1 && git push origin v0.6.0-rc1`
  _US-1: Pull and run Taskyn from Docker Hub_
