# Methodology Update — Design

## Approach
1. Create a `Methodology` enum in `enums.py` (following `EntityType` pattern)
2. Replace raw string methodology usage with the enum across core, model, and MCP layers
3. Thread a new `methodology` parameter through the update pipeline: core -> MCP

No new modules, no schema changes (DB stores string values via `enum.value`), no new dependencies.

## Safety Rule
Only allow methodology change when the project has **zero nodes**. Node types and statuses differ significantly between methodologies (e.g., epic/story/task vs spec/design/implementation/validation), so changing with existing nodes would break data integrity. Migration support can be added in a future spec if needed.

## Layer Changes

### Enum: `src/taskyn/db/enums.py`
Add `Methodology` enum following the `EntityType` pattern:
```python
class Methodology(str, Enum):
    CLASSIC_AGILE = "classic_agile"
    SPEC_DRIVEN = "spec_driven"
```
Inheriting from `str, Enum` ensures `.value` returns the string for DB storage — same pattern as `EntityType`.

### Model: `src/taskyn/db/models.py`
Change `methodology: str = "classic_agile"` to `methodology: Methodology = Methodology.CLASSIC_AGILE` in the `Project` model. Since `Methodology` extends `str`, Pydantic serialization works transparently.

### Core Layer: `src/taskyn/core/project.py`

**`create_project()`:** Change `methodology: str = "classic_agile"` to `methodology: Methodology = Methodology.CLASSIC_AGILE`. Store as `methodology.value` in SQL (same pattern as `type.value` for EntityType).

**`update_project()`:** Add `methodology: Methodology | None = None` parameter. Logic:
1. If `methodology` is not None and differs from current:
   - Query `SELECT COUNT(*) FROM nodes WHERE project_id = ?`
   - If count > 0, raise `ValidationError` with clear message
2. In the updates-building section:
   - Append `methodology = ?` to SQL UPDATE clause with `methodology.value`
   - Insert activity log entry with `action="methodology_changed"` using inline pattern (matching `status_changed` at lines 163-170)

Note: Enum validation replaces `methodology_exists()` call — invalid values are caught by Python's enum constructor. The `methodology_exists()` function and registry still work since they key on string values.

### MCP Layer: `src/taskyn/mcp/server.py`

**`pm_create_project()`:** Change `methodology: str = "classic_agile"` to accept string, convert to enum: `Methodology(methodology)`.

**`pm_update_project()`:** Add `methodology: str | None = None` parameter (string at MCP boundary for LLM compatibility), convert to enum before passing to core: `Methodology(methodology) if methodology else None`.

### Test Layer: `tests/test_project.py`
4 new test cases following existing patterns:
- Success case on empty project
- Invalid methodology rejection
- Nodes-exist rejection (uses `create_node` from graph layer)
- Same-value no-op

## Migration Note
No database migration is required. The DB column is `methodology TEXT NOT NULL DEFAULT 'classic_agile'` and stores plain strings. The `Methodology` enum extends `str, Enum`, so `Methodology.CLASSIC_AGILE.value` produces `"classic_agile"` — identical to what is already stored. This is a Python-side type safety change only; the database sees the same strings it always has. Existing data is fully compatible on deploy without any transformation.

## What Does NOT Change
- `src/taskyn/db/schema.sql` — Column stores TEXT, enum `.value` produces the same strings
- `src/taskyn/core/__init__.py` — `update_project` already exported
- `src/taskyn/methodologies/__init__.py` — Registry keys on string values, remains compatible
- `src/taskyn/cli/project.py` — Out of scope for this spec
