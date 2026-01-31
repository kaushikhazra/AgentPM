# Docker Deployment Requirements

## Epic
As a developer, I want to deploy AgentPM as a containerized MCP server so that I can access it remotely from any MCP-compatible client.

## User Stories

### DOCKER-01: Build Docker Image
**As a** developer
**I want to** build a Docker image for AgentPM
**So that** I can deploy it consistently across different environments

**Acceptance Criteria:**
- [ ] Dockerfile uses Python 3.11+ slim base image
- [ ] Image includes all production dependencies
- [ ] Image size is optimized (no dev dependencies, multi-stage build)
- [ ] Image can be built with `docker build -t agentpm .`

### DOCKER-02: Run MCP Server in Container
**As a** developer
**I want to** run the AgentPM MCP server in a container
**So that** I can access it over HTTP from remote clients

**Acceptance Criteria:**
- [ ] Container starts MCP server with streamable-http transport
- [ ] Server binds to 0.0.0.0 for external access
- [ ] Port 8020 is exposed and accessible
- [ ] Server responds to MCP protocol requests

### DOCKER-03: Persist Database
**As a** developer
**I want to** persist the SQLite database outside the container
**So that** my data survives container restarts and updates

**Acceptance Criteria:**
- [ ] Database stored in mounted volume at /data
- [ ] Data persists after container stop/start
- [ ] Data persists after container removal and recreation
- [ ] Default database path configured via environment variable

### DOCKER-04: Easy Deployment with Compose
**As a** developer
**I want to** deploy AgentPM with a single command
**So that** I can quickly start the service without remembering complex docker run commands

**Acceptance Criteria:**
- [ ] docker-compose.yml defines the service
- [ ] Volume mount configured for data persistence
- [ ] Port mapping configured (8020:8020)
- [ ] Environment variables properly set
- [ ] Can start with `docker-compose up -d`

### DOCKER-05: Health Check
**As a** developer
**I want to** verify the container is healthy
**So that** orchestrators can monitor and restart if needed

**Acceptance Criteria:**
- [ ] Container includes health check
- [ ] Health check verifies MCP server is responding
- [ ] Unhealthy containers can be detected by Docker

## Non-Functional Requirements

### NFR-1: Image Size
- Target: < 200MB
- Use slim base image and multi-stage build

### NFR-2: Startup Time
- Container should be ready to accept connections within 5 seconds

### NFR-3: Security
- Run as non-root user inside container
- No unnecessary packages installed
