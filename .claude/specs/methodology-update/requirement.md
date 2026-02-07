# Methodology Update — Requirements

## Overview
Allow updating a project's methodology after creation, with safety guardrails to prevent data integrity issues. Introduce a `Methodology` enum to replace raw string usage across the codebase.

## User Stories

### US-MU-01: Update methodology on empty project
As a project manager, I want to change a project's methodology so that I can switch approaches (e.g., from classic_agile to spec_driven) before work begins.

**Acceptance Criteria:**
- Can update methodology via core API and MCP tool
- Methodology is validated against the `Methodology` enum
- Updated project reflects the new methodology
- Activity is logged with old and new methodology values

### US-MU-02: Prevent methodology change on project with nodes
As a project manager, I want the system to reject methodology changes when a project already has nodes, so that existing work items are not orphaned with invalid types/statuses.

**Acceptance Criteria:**
- System checks node count before allowing methodology change
- Returns clear error message with node count and guidance
- Existing nodes remain unaffected

### US-MU-03: No-op on same methodology
As a user, I expect that setting the methodology to its current value does not trigger unnecessary updates or activity logs.

**Acceptance Criteria:**
- No SQL UPDATE executed when methodology matches current value
- No activity log entry created
- Returns project unchanged

### US-MU-04: Methodology enum
As a developer, I want methodology values defined as an enum so that typos are prevented, values are discoverable, and there is a single source of truth.

**Acceptance Criteria:**
- `Methodology` enum defined in `src/taskyn/db/enums.py` (alongside `EntityType`)
- Enum used in `create_project`, `update_project`, Project model, and MCP tools
- Existing raw string usage replaced with enum
- Methodology registry (`methodology_exists`, `get_methodology`) works with enum values
