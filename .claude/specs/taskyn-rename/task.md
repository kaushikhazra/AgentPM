# Taskyn Rename - Tasks

## Phase 1: Setup & Structure

- [x] Create feature branch `feature/taskyn-rename`
  _TRN-NFR-03_

- [x] Rename folder `src/agentpm` to `src/taskyn`
  _TRN-IMP-01_

## Phase 2: Configuration Files

- [x] Update `pyproject.toml`
  - [x] Change `name = "agentpm"` to `name = "taskyn"`
  - [x] Change CLI entry point `apm` to `taskyn`
  - [x] Update packages path to `src/taskyn`
  - [x] Update pytest coverage path
  _TRN-PKG-01, TRN-CLI-01_

- [x] Update `Dockerfile`
  - [x] Change user/group from `agentpm` to `taskyn`
  - [x] Update ENTRYPOINT module path
  - [x] Update environment variable names
  _TRN-DOC-01, TRN-ENV-01_

- [x] Update `docker-compose.yml`
  - [x] Change service name to `taskyn`
  - [x] Change image name to `taskyn:latest`
  - [x] Change container name to `taskyn`
  - [x] Update environment variable names
  _TRN-DOC-01, TRN-ENV-01_

- [x] Update `docker-compose.https.yml`
  - [x] Same changes as docker-compose.yml
  _TRN-DOC-01, TRN-ENV-01_

- [x] Update `Caddyfile`
  - [x] Change reverse_proxy target to `taskyn:8020`
  _TRN-DOC-01_

## Phase 3: Python Source Code

- [x] Update `src/taskyn/__init__.py`
  - [x] Update docstring to "Taskyn"
  _TRN-IMP-01_

- [x] Update `src/taskyn/config.py`
  - [x] Update docstring
  - [x] Change `DEFAULT_DB_DIR` to `.taskyn`
  - [x] Change `DEFAULT_DB_PATH` to `taskyn.db`
  - [x] Rename env vars to `TASKYN_*`
  _TRN-ENV-01, TRN-DB-01_

- [x] Update `src/taskyn/exceptions.py`
  - [x] Rename `AgentPMError` to `TaskynError`
  - [x] Update docstring
  _TRN-IMP-01_

- [x] Update all imports in `src/taskyn/db/*.py`
  - [x] Replace `from agentpm.` with `from taskyn.`
  - [x] Update docstrings
  _TRN-IMP-01_

- [x] Update all imports in `src/taskyn/graph/*.py`
  - [x] Replace `from agentpm.` with `from taskyn.`
  - [x] Update docstrings
  _TRN-IMP-01_

- [x] Update all imports in `src/taskyn/core/*.py`
  - [x] Replace `from agentpm.` with `from taskyn.`
  - [x] Update docstrings
  - [x] Replace `AgentPMError` with `TaskynError`
  _TRN-IMP-01_

- [x] Update all imports in `src/taskyn/methodologies/*.py`
  - [x] Replace `from agentpm.` with `from taskyn.`
  - [x] Update docstrings
  _TRN-IMP-01_

- [x] Update `src/taskyn/cli/main.py`
  - [x] Change app name to "taskyn"
  - [x] Update help text to "Taskyn"
  - [x] Update imports and exception references
  _TRN-CLI-01, TRN-IMP-01_

- [x] Update all imports in `src/taskyn/cli/*.py`
  - [x] Replace `from agentpm.` with `from taskyn.`
  - [x] Update docstrings
  _TRN-IMP-01_

- [x] Update `src/taskyn/mcp/server.py`
  - [x] Change FastMCP name to "taskyn"
  - [x] Update instructions to reference "Taskyn"
  - [x] Update environment variable names
  - [x] Update imports
  _TRN-MCP-01, TRN-ENV-01, TRN-IMP-01_

- [x] Update `src/taskyn/mcp/__main__.py`
  - [x] Update argparse description
  - [x] Update environment variable names
  - [x] Update imports
  _TRN-MCP-01, TRN-ENV-01_

## Phase 4: Test Files

- [x] Update `tests/conftest.py`
  - [x] Replace all `from agentpm.` imports
  _TRN-NFR-02_

- [x] Update all `tests/test_*.py` files
  - [x] Replace all `from agentpm.` imports
  - [x] Replace `AgentPMError` with `TaskynError`
  _TRN-NFR-02_

## Phase 5: Documentation

- [x] Update `README.md`
  - [x] Change title to "Taskyn"
  - [x] Update installation command to `pip install taskyn`
  - [x] Update all CLI examples to use `taskyn`
  - [x] Update MCP configuration examples
  - [x] Update environment variable documentation
  - [x] Update Docker examples
  _TRN-DOC-02_

- [x] Update `CLAUDE.md`
  - [x] Change project name to "Taskyn"
  - [x] Update CLI entry point to `taskyn`
  - [x] Update MCP server command
  _TRN-DOC-02_

- [x] Update `scripts/mcp_test_client.py`
  - [x] Update module references
  - [x] Update environment variable names
  _TRN-ENV-01_

## Phase 6: Verification

- [x] Run `pytest` - all tests pass (229 passed)
  _TRN-NFR-02_

- [x] Verify CLI: `taskyn --help`
  _TRN-CLI-01_

- [x] Verify MCP: `python -m taskyn.mcp --help`
  _TRN-MCP-01_

- [x] Verify imports: `python -c "from taskyn import __version__"`
  _TRN-IMP-01_

- [x] Grep verification: `grep -ri "agentpm" src/ tests/` returns empty
  _TRN-NFR-01_

- [ ] Docker build: `docker build -t taskyn:latest .`
  _TRN-DOC-01_

## Phase 7: Git Workflow

- [x] Stage and commit changes
  _TRN-NFR-03_

- [ ] Create PR to develop branch
  _TRN-NFR-03_
