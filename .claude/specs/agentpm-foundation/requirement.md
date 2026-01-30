# AgentPM Foundation - Requirements

## Overview
Establish the foundational infrastructure for AgentPM: database layer, Pydantic models, and the methodology system that enables the graph-based architecture.

## User Stories

### FND-1: Project Setup
As a developer, I want a properly structured Python project so that I can build AgentPM with modern tooling.

**Acceptance Criteria:**
- pyproject.toml configured with dependencies (pydantic, sqlite3)
- src/agentpm package structure created
- pytest configured for testing
- Project installable via `pip install -e .`

### FND-2: Database Initialization
As a user, I want the database to be automatically created and initialized so that I can start using AgentPM immediately.

**Acceptance Criteria:**
- SQLite database created at configurable path (default: ~/.agentpm/agentpm.db)
- All tables created per schema (companies, projects, milestones, nodes, edges, time_entries, tags, node_tags, activity_log)
- All indexes created for performance
- Idempotent initialization (safe to run multiple times)

### FND-3: Company Management
As a user, I want to create and manage companies so that I can organize my projects under different contexts.

**Acceptance Criteria:**
- Create company with name and optional description
- List all companies
- Get company by ID with project count
- Update company name/description
- Delete company (cascades to projects)

### FND-4: Project Management with Methodology
As a user, I want to create projects with a specified methodology so that the system validates work items according to that methodology's rules.

**Acceptance Criteria:**
- Create project under a company with name, description, and methodology (default: classic_agile)
- List projects with optional filters (company, status)
- Get project by ID with methodology info
- Update project status (active, on_hold, completed, archived)
- Delete project (cascades to milestones, nodes, edges)

### FND-5: Methodology System
As a developer, I want a pluggable methodology system so that different PM approaches can be supported.

**Acceptance Criteria:**
- BaseMethodology abstract class with required interface
- ClassicAgileMethodology implemented with Story and Task node types
- Node type definitions include valid statuses, transitions, properties
- Edge type definitions include source/target constraints
- Methodology registry for lookup by name
- Validation methods for nodes and edges

### FND-6: Pydantic Models
As a developer, I want Pydantic models for all entities so that data is validated and serializable.

**Acceptance Criteria:**
- Company model
- Project model (includes methodology field)
- Milestone model
- Node model (generic, with node_type and properties)
- Edge model (with edge_type and properties)
- TimeEntry model
- Tag model
- ActivityLog model
- All models support JSON serialization
