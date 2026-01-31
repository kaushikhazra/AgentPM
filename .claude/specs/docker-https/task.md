# HTTPS Support Tasks

## Implementation Tasks

### 1. Create Caddyfile
- [x] Create Caddyfile with environment variable support
  - [x] DOMAIN variable for hostname
  - [x] EMAIL variable for Let's Encrypt
  - [x] Automatic TLS (internal for localhost, ACME for domains)
  - [x] Reverse proxy to agentpm:8020
  - [x] Security headers (HSTS, X-Content-Type-Options, X-Frame-Options)
  - [x] Console logging
  _HTTPS-01, HTTPS-02, HTTPS-04_

### 2. Create docker-compose.https.yml
- [x] Define agentpm service (internal only, no port mapping)
- [x] Define caddy service
  - [x] Use caddy:2-alpine image
  - [x] Map ports 80 and 443
  - [x] Mount Caddyfile
  - [x] Mount volumes for certificates
  - [x] Pass DOMAIN and EMAIL environment variables
  - [x] Depend on agentpm health
  - [ ] Add health check (skipped - Caddy has built-in monitoring)
  - [x] Add restart policy
  _HTTPS-01, HTTPS-02, HTTPS-04, HTTPS-05_

### 3. Test Local HTTPS
- [x] Start with docker-compose.https.yml
- [x] Verify self-signed certificate generated
- [x] Test MCP connection via https://localhost/mcp
- [x] Verify HTTP redirects to HTTPS (308 redirect)
  _HTTPS-03_

### 4. Test Production HTTPS (Optional)
- [ ] Deploy with real domain
- [ ] Verify Let's Encrypt certificate provisioned
- [ ] Test MCP connection via https://domain/mcp
- [ ] Verify certificate auto-renewal works
  _HTTPS-01, HTTPS-02_

### 5. Update Documentation
- [x] Add HTTPS section to README
  - [x] Quick start for local HTTPS
  - [x] Production deployment with domain
  - [x] Environment variables reference
  - [x] MCP client configuration for HTTPS
  - [x] How it works section
  _HTTPS-04, HTTPS-05_

### 6. Verify Backward Compatibility
- [x] Confirm docker-compose.yml still works (HTTP only)
- [x] Confirm both can't run simultaneously (port conflict - different ports)
  _HTTPS-05_

## Git Workflow

Branch: `feature/docker-https`
