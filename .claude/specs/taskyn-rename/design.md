# Taskyn Rename - Design

## Rename Strategy

### Naming Convention

| Old Name | New Name | Context |
|----------|----------|---------|
| AgentPM | Taskyn | Project name, branding |
| agentpm | taskyn | Package name, imports, folders |
| apm | taskyn | CLI command |
| AGENTPM_* | TASKYN_* | Environment variables |
| ~/.agentpm/ | ~/.taskyn/ | Data directory |
| agentpm.db | taskyn.db | Database file |

### What Stays the Same

- **Tool prefix**: `pm_` prefix on MCP tools remains unchanged (e.g., `pm_create_node`)
- **Database schema**: No changes to table names or structure
- **API contracts**: All function signatures remain identical
- **Test structure**: Test file names stay as `test_*.py`

---

## File Change Categories

### Phase 1: Structural Changes (Folder/File Renames)

```
src/agentpm/           →  src/taskyn/
├── __init__.py             (content update)
├── config.py               (content update)
├── exceptions.py           (content update)
├── db/                     (all files: content update)
├── graph/                  (all files: content update)
├── core/                   (all files: content update)
├── cli/                    (all files: content update)
├── mcp/                    (all files: content update)
└── methodologies/          (all files: content update)
```

### Phase 2: Configuration Files

| File | Changes |
|------|---------|
| pyproject.toml | name, scripts, packages, pytest |
| Dockerfile | user, entrypoint, env vars |
| docker-compose.yml | service, image, container, env |
| docker-compose.https.yml | service, image, container, env |
| Caddyfile | reverse_proxy target |

### Phase 3: Source Code Updates

**Import Pattern Change:**
```python
# Before
from agentpm.core.project import create_project
from agentpm.exceptions import AgentPMError

# After
from taskyn.core.project import create_project
from taskyn.exceptions import TaskynError
```

**Exception Class Rename:**
```python
# Before
class AgentPMError(Exception):

# After
class TaskynError(Exception):
```

### Phase 4: Environment Variables

| Old Variable | New Variable | Files Affected |
|--------------|--------------|----------------|
| AGENTPM_DB | TASKYN_DB | config.py, mcp/server.py, Dockerfile, docker-compose.* |
| AGENTPM_ACTOR | TASKYN_ACTOR | config.py |
| AGENTPM_MCP_HOST | TASKYN_MCP_HOST | mcp/__main__.py, mcp/server.py |
| AGENTPM_MCP_PORT | TASKYN_MCP_PORT | mcp/__main__.py, mcp/server.py |

### Phase 5: Documentation

| File | Scope |
|------|-------|
| README.md | Full rebranding (~50 occurrences) |
| CLAUDE.md | Project overview, examples |
| .claude/specs/* | Folder names, content references |
| .claude/plans/* | File names, content references |

---

## Implementation Order

The rename must follow this specific order to avoid breaking the build:

1. **Create git branch** `feature/taskyn-rename`
2. **Rename folder** `src/agentpm` → `src/taskyn`
3. **Update pyproject.toml** (package name, paths)
4. **Update all imports** in src/taskyn/**/*.py
5. **Update all imports** in tests/**/*.py
6. **Update exception class** AgentPMError → TaskynError
7. **Update environment variables** in all files
8. **Update Docker configuration**
9. **Update documentation**
10. **Run tests** to verify
11. **Commit and create PR**

---

## Risk Mitigation

### Risk 1: Broken Imports
- **Mitigation**: Use search/replace with verification
- **Verification**: `pytest` must pass after Phase 4

### Risk 2: Missed References
- **Mitigation**: Grep for "agentpm", "AgentPM", "apm" after completion
- **Verification**: `grep -ri "agentpm" src/ tests/` returns empty

### Risk 3: Docker Build Failure
- **Mitigation**: Test Docker build after Phase 8
- **Verification**: `docker build -t taskyn:latest .`

### Risk 4: User Data Migration
- **Mitigation**: Document migration steps in README
- **Note**: Users must manually move `~/.agentpm/` to `~/.taskyn/`

---

## Testing Strategy

1. **Unit Tests**: All existing tests must pass
2. **CLI Smoke Test**: `taskyn --help` works
3. **MCP Smoke Test**: `python -m taskyn.mcp` starts
4. **Docker Build**: Image builds successfully
5. **Import Check**: `python -c "from taskyn import __version__"` works
