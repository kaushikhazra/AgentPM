# Methodology Update — Tasks

- [x] Create feature branch `feature/methodology-update` from develop
  _Setup_

- [x] Add `Methodology` enum to `src/taskyn/db/enums.py`
  - [x] Define enum with CLASSIC_AGILE and SPEC_DRIVEN values
  _US-MU-04_

- [x] Update `Project` model in `src/taskyn/db/models.py` to use `Methodology` enum
  _US-MU-04_

- [x] Update `create_project()` in `src/taskyn/core/project.py` to use `Methodology` enum
  - [x] Change parameter type from `str` to `Methodology`
  - [x] Store as `methodology.value` in SQL
  _US-MU-04_

- [x] Add `methodology` parameter to `update_project()` in `src/taskyn/core/project.py`
  - [x] Add parameter to function signature as `Methodology | None`
  - [x] Add node count safety check (reject if > 0)
  - [x] Add to SQL UPDATE clause with `.value`
  - [x] Add activity log entry for `methodology_changed`
  _US-MU-01, US-MU-02, US-MU-03_

- [x] Update `pm_create_project()` in `src/taskyn/mcp/server.py` to convert string to enum
  _US-MU-04_

- [x] Expose `methodology` in MCP tool `pm_update_project()` in `src/taskyn/mcp/server.py`
  - [x] Add string parameter and convert to `Methodology` enum
  - [x] Pass through to core function
  - [x] Update docstring
  _US-MU-01_

- [x] Add tests in `tests/test_project.py`
  - [x] `test_update_project_methodology` — success on empty project
  - [x] `test_update_project_methodology_invalid` — reject unknown methodology
  - [x] `test_update_project_methodology_with_nodes` — reject when nodes exist
  - [x] `test_update_project_methodology_same_noop` — no-op when value unchanged
  _US-MU-01, US-MU-02, US-MU-03_

- [x] Run tests and verify (`pytest tests/test_project.py` + full suite)
  _Verification_

- [x] Deploy to Docker and test via HTTP MCP interface
  - [x] Build and start Docker container
  - [x] Use MCP test skill to verify `pm_update_project` with methodology parameter
  - [x] Change Taskyn project methodology to `spec_driven`
  _US-MU-01, Verification_

- [-] Commit, push, and merge feature branch
  _Delivery_
