# AgentPM Foundation - Tasks

## Project Setup
- [x] Create pyproject.toml with project metadata and dependencies
  _FND-1: Project Setup_
- [x] Create src/agentpm package structure with __init__.py files
  _FND-1: Project Setup_
- [x] Configure pytest in pyproject.toml
  _FND-1: Project Setup_
- [x] Create tests/ directory with conftest.py
  _FND-1: Project Setup_

## Configuration
- [x] Create config.py with database path configuration
  _FND-2: Database Initialization_
- [x] Support AGENTPM_DB environment variable
  _FND-2: Database Initialization_
- [x] Create default directory (~/.agentpm/) if needed
  _FND-2: Database Initialization_

## Database Layer
- [x] Create db/schema.sql with full schema
  _FND-2: Database Initialization_
- [x] Create db/connection.py with connection management
  _FND-2: Database Initialization_
  - [x] get_connection() function
  - [x] Enable foreign keys pragma
  - [x] Initialize schema on first connect
- [x] Write tests for database initialization
  _FND-2: Database Initialization_

## Pydantic Models
- [x] Create db/models.py with all Pydantic models
  _FND-6: Pydantic Models_
  - [x] Company model
  - [x] Project model
  - [x] Milestone model
  - [x] Node model (generic)
  - [x] Edge model
  - [x] TimeEntry model
  - [x] Tag model
  - [x] ActivityLog model
- [x] Write tests for model validation
  _FND-6: Pydantic Models_

## Methodology System
- [x] Create methodologies/base.py with BaseMethodology ABC
  _FND-5: Methodology System_
  - [x] NodeTypeDefinition dataclass
  - [x] EdgeTypeDefinition dataclass
  - [x] Abstract properties and methods
- [x] Create methodologies/classic_agile.py
  _FND-5: Methodology System_
  - [x] Define story node type with statuses
  - [x] Define task node type with statuses
  - [x] Define parent edge type
  - [x] Define depends_on edge type
- [x] Create methodologies/__init__.py with registry
  _FND-5: Methodology System_
  - [x] get_methodology(name) function
  - [x] list_methodologies() function
- [x] Write tests for methodology validation
  _FND-5: Methodology System_

## Company CRUD
- [x] Create core/company.py
  _FND-3: Company Management_
  - [x] create_company(name, description) -> Company
  - [x] get_company(id) -> Company
  - [x] list_companies() -> List[Company]
  - [x] update_company(id, name?, description?) -> Company
  - [x] delete_company(id) -> bool
- [x] Write tests for company operations
  _FND-3: Company Management_

## Project CRUD
- [x] Create core/project.py
  _FND-4: Project Management with Methodology_
  - [x] create_project(company_id, name, methodology, description) -> Project
  - [x] get_project(id) -> Project
  - [x] list_projects(company_id?, status?) -> List[Project]
  - [x] update_project(id, status?, name?, description?) -> Project
  - [x] delete_project(id) -> bool
- [x] Validate methodology exists on project creation
  _FND-4: Project Management with Methodology_
- [x] Write tests for project operations
  _FND-4: Project Management with Methodology_

## Integration Test
- [x] Write end-to-end test: create company → create project → verify methodology
  _FND-4: Project Management with Methodology_
