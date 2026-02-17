# Docker Hub Publishing — Requirements

## User Stories

### US-1: Pull and run Taskyn from Docker Hub
**As a** developer or user,
**I want to** pull Taskyn images from Docker Hub with `docker pull kaushikhazra/taskyn-core` and `docker pull kaushikhazra/taskyn-web`,
**So that** I can run Taskyn without building from source.

### US-2: Automated image publishing on release
**As a** maintainer,
**I want** Docker images to be automatically built and pushed to Docker Hub when I create a version tag,
**So that** I don't have to manually build and push images for each release.

### US-3: Multi-platform support
**As a** user on ARM64 (Apple Silicon, Raspberry Pi) or AMD64,
**I want** the Docker images to support my platform,
**So that** I can run Taskyn natively without emulation.

### US-4: Clean Docker configuration
**As a** contributor,
**I want** deprecated Dockerfiles removed and references updated,
**So that** the project has a clear, unambiguous Docker setup.
