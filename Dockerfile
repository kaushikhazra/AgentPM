# =============================================================================
# AgentPM Docker Image
# Multi-stage build for minimal runtime image
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# Install build dependencies and create virtual environment
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install package (production dependencies only)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# -----------------------------------------------------------------------------
# Stage 2: Runtime
# Minimal image with only production dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim

# Create non-root user for security
RUN groupadd --gid 1000 agentpm && \
    useradd --uid 1000 --gid 1000 --create-home agentpm

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create data directory for SQLite database
RUN mkdir -p /data && chown agentpm:agentpm /data

# Set working directory
WORKDIR /app

# Environment variables with defaults
ENV AGENTPM_DB="/data/agentpm.db" \
    AGENTPM_ACTOR="mcp" \
    AGENTPM_MCP_HOST="0.0.0.0" \
    AGENTPM_MCP_PORT="8020"

# Switch to non-root user
USER agentpm

# Expose MCP server port
EXPOSE 8020

# Health check for MCP server (checks if uvicorn is responding)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.settimeout(5); s.connect(('localhost',8020)); s.close()" || exit 1

# Run MCP server with streamable-http transport
ENTRYPOINT ["python", "-m", "agentpm.mcp"]
CMD ["--transport", "streamable-http"]
