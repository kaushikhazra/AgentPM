# Taskyn Rename - Requirements

## Overview
Rename the project from "AgentPM" to "Taskyn" across the entire codebase.

## User Stories

### TRN-PKG-01: Package Identity
**As a** developer installing the package
**I want** to run `pip install taskyn`
**So that** I can install the project management tool with its new identity

**Acceptance Criteria:**
- PyPI package name is `taskyn`
- Package installs successfully with `pip install taskyn`
- Package version remains unchanged

---

### TRN-CLI-01: CLI Command
**As a** user of the CLI
**I want** to run `taskyn` command instead of `apm`
**So that** I can access all project management features with the new command name

**Acceptance Criteria:**
- `taskyn --help` displays help with "Taskyn" branding
- All subcommands work: `taskyn company`, `taskyn project`, `taskyn node`, etc.
- Help text shows "Taskyn - AI-first Project Management"

---

### TRN-MCP-01: MCP Server Identity
**As a** Claude Desktop user
**I want** the MCP server to identify as "taskyn"
**So that** tools are properly namespaced and branded

**Acceptance Criteria:**
- MCP server name is "taskyn"
- Server instructions reference "Taskyn"
- `python -m taskyn.mcp` starts the server
- Tool names maintain `pm_` prefix (no change to tool interface)

---

### TRN-ENV-01: Environment Variables
**As a** system administrator
**I want** to configure Taskyn using `TASKYN_*` environment variables
**So that** configuration is consistent with the new branding

**Acceptance Criteria:**
- `TASKYN_DB` sets database path
- `TASKYN_ACTOR` sets default actor
- `TASKYN_MCP_HOST` sets MCP host
- `TASKYN_MCP_PORT` sets MCP port
- Old `AGENTPM_*` variables no longer work (clean break)

---

### TRN-DB-01: Database Location
**As a** user with existing data
**I want** the default database location to be `~/.taskyn/taskyn.db`
**So that** the data storage aligns with the new identity

**Acceptance Criteria:**
- Default database directory is `~/.taskyn/`
- Default database file is `taskyn.db`
- Existing `~/.agentpm/` data requires manual migration (documented)

---

### TRN-DOC-01: Docker Deployment
**As a** DevOps engineer
**I want** Docker images and services named "taskyn"
**So that** container orchestration reflects the new branding

**Acceptance Criteria:**
- Docker image builds as `taskyn:latest`
- Service name in docker-compose is `taskyn`
- Container name is `taskyn`
- Internal user is `taskyn` (not `agentpm`)

---

### TRN-DOC-02: Documentation
**As a** new user reading documentation
**I want** all docs to reference "Taskyn"
**So that** I understand the correct project name and commands

**Acceptance Criteria:**
- README.md shows "Taskyn" throughout
- CLAUDE.md updated with new name
- All examples use `taskyn` command
- MCP configuration examples updated

---

### TRN-IMP-01: Import Paths
**As a** developer extending Taskyn
**I want** to import from `taskyn` package
**So that** my code uses the correct module paths

**Acceptance Criteria:**
- `from taskyn.core import ...` works
- `from taskyn.db import ...` works
- `from taskyn.mcp import ...` works
- All internal imports updated

---

## Non-Functional Requirements

### TRN-NFR-01: Backward Compatibility
- This is a **breaking change** - no backward compatibility with `agentpm` imports
- Clear migration documentation required
- Version bump to indicate breaking change

### TRN-NFR-02: Test Coverage
- All existing tests must pass after rename
- No reduction in test coverage

### TRN-NFR-03: Git History
- Single feature branch for all rename changes
- Atomic commits by category (structure, code, docs, etc.)
