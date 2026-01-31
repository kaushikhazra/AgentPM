# HTTPS Support Design

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Host Machine                                 │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    Docker Network                               │ │
│  │                                                                 │ │
│  │   ┌─────────────────────┐      ┌─────────────────────────────┐ │ │
│  │   │       Caddy         │      │        AgentPM              │ │ │
│  │   │                     │      │                             │ │ │
│  │   │  :443 (HTTPS) ──────┼──────▶ :8020 (HTTP)               │ │ │
│  │   │  :80  (redirect)    │      │                             │ │ │
│  │   │                     │      │  MCP Server                 │ │ │
│  │   │  TLS Termination    │      │  (streamable-http)          │ │ │
│  │   │  Auto Certs         │      │                             │ │ │
│  │   └─────────────────────┘      └─────────────────────────────┘ │ │
│  │            │                              │                     │ │
│  └────────────│──────────────────────────────│─────────────────────┘ │
│               │                              │                       │
│               ▼                              ▼                       │
│   ┌───────────────────────┐      ┌───────────────────────────────┐  │
│   │   ./caddy_data        │      │   ./data                      │  │
│   │   (certificates)      │      │   (agentpm.db)                │  │
│   └───────────────────────┘      └───────────────────────────────┘  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## Why Caddy?

| Feature | Caddy | nginx | traefik |
|---------|-------|-------|---------|
| Auto HTTPS | Built-in | Manual/certbot | Plugin |
| Config complexity | Minimal | Moderate | Moderate |
| Image size | ~40MB | ~20MB | ~100MB |
| Let's Encrypt | Native | External | Native |
| Self-signed fallback | Automatic | Manual | Manual |

Caddy wins on simplicity and automatic certificate management.

## File Structure

```
AgentPM/
├── docker-compose.yml          # HTTP only (unchanged)
├── docker-compose.https.yml    # HTTPS with Caddy
├── Caddyfile                   # Caddy configuration
└── data/
    └── agentpm.db
```

## Caddy Configuration

### Production (Let's Encrypt)

```
# Caddyfile
{$DOMAIN} {
    reverse_proxy agentpm:8020

    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
    }
}
```

### Local Development (Self-signed)

```
# Caddyfile.local
:443 {
    tls internal
    reverse_proxy agentpm:8020
}
```

## Docker Compose Configuration

### docker-compose.https.yml

```yaml
services:
  agentpm:
    build: .
    image: agentpm:latest
    container_name: agentpm
    expose:
      - "8020"
    volumes:
      - ./data:/data
    environment:
      - AGENTPM_DB=/data/agentpm.db
      - AGENTPM_ACTOR=mcp
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; s=socket.socket(); s.settimeout(5); s.connect(('localhost',8020)); s.close()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

  caddy:
    image: caddy:2-alpine
    container_name: agentpm-caddy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    environment:
      - DOMAIN=${DOMAIN:-localhost}
      - EMAIL=${EMAIL:-}
    depends_on:
      agentpm:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "caddy", "validate", "--config", "/etc/caddy/Caddyfile"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  caddy_data:
  caddy_config:
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DOMAIN` | Yes (prod) | `localhost` | Domain for certificate |
| `EMAIL` | No | - | Email for Let's Encrypt notifications |

## Caddyfile with Environment Variables

```
{$DOMAIN:localhost} {
    # Use internal CA for localhost, Let's Encrypt for real domains
    @localhost host localhost
    tls {$EMAIL:internal}

    reverse_proxy agentpm:8020

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
    }

    log {
        output stdout
        format console
    }
}
```

## Usage

### Production Deployment

```bash
# Set domain and optional email
export DOMAIN=mcp.example.com
export EMAIL=admin@example.com

# Start with HTTPS
docker-compose -f docker-compose.https.yml up -d
```

MCP client config:
```json
{
  "mcpServers": {
    "agentpm": {
      "transport": "streamable-http",
      "url": "https://mcp.example.com/mcp"
    }
  }
}
```

### Local Development

```bash
# Uses self-signed cert for localhost
docker-compose -f docker-compose.https.yml up -d
```

Access: `https://localhost/mcp` (accept self-signed cert warning)

## Security Considerations

1. **TLS Configuration**: Caddy uses secure defaults (TLS 1.2+, strong ciphers)
2. **Certificate Storage**: Certificates stored in Docker volume, not exposed
3. **HTTP Redirect**: Port 80 automatically redirects to 443
4. **HSTS**: Strict-Transport-Security header prevents downgrade attacks
5. **Internal Network**: AgentPM only exposed internally, not to host

## Rollback

If HTTPS causes issues, users can:
1. Stop HTTPS: `docker-compose -f docker-compose.https.yml down`
2. Start HTTP: `docker-compose up -d`
