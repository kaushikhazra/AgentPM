# AgentPM Foundation - Tasks

## Project Setup
- [ ] Create pyproject.toml with project metadata and dependencies
  _US-1: Project Setup_
- [ ] Create src/agentpm package structure with __init__.py files
  _US-1: Project Setup_
- [ ] Configure pytest in pyproject.toml
  _US-1: Project Setup_
- [ ] Create tests/ directory with conftest.py
  _US-1: Project Setup_

## Configuration
- [ ] Create config.py with database path configuration
  _US-2: Database Initialization_
- [ ] Support AGENTPM_DB environment variable
  _US-2: Database Initialization_
- [ ] Create default directory (~/.agentpm/) if needed
  _US-2: Database Initialization_

## Database Layer
- [ ] Create db/schema.sql with full schema
  _US-2: Database Initialization_
- [ ] Create db/connection.py with connection management
  _US-2: Database Initialization_
  - [ ] get_connection() function
  - [ ] Enable foreign keys pragma
  - [ ] Initialize schema on first connect
- [ ] Write tests for database initialization
  _US-2: Database Initialization_

## Pydantic Models
- [ ] Create db/models.py with all Pydantic models
  _US-6: Pydantic Models_
  - [ ] Company model
  - [ ] Project model
  - [ ] Milestone model
  - [ ] Node model (generic)
  - [ ] Edge model
  - [ ] TimeEntry model
  - [ ] Tag model
  - [ ] ActivityLog model
- [ ] Write tests for model validation
  _US-6: Pydantic Models_

## Methodology System
- [ ] Create methodologies/base.py with BaseMethodology ABC
  _US-5: Methodology System_
  - [ ] NodeTypeDefinition dataclass
  - [ ] EdgeTypeDefinition dataclass
  - [ ] Abstract properties and methods
- [ ] Create methodologies/classic_agile.py
  _US-5: Methodology System_
  - [ ] Define story node type with statuses
  - [ ] Define task node type with statuses
  - [ ] Define parent edge type
  - [ ] Define depends_on edge type
- [ ] Create methodologies/__init__.py with registry
  _US-5: Methodology System_
  - [ ] get_methodology(name) function
  - [ ] list_methodologies() function
- [ ] Write tests for methodology validation
  _US-5: Methodology System_

## Company CRUD
- [ ] Create core/company.py
  _US-3: Company Management_
  - [ ] create_company(name, description) -> Company
  - [ ] get_company(id) -> Company
  - [ ] list_companies() -> List[Company]
  - [ ] update_company(id, name?, description?) -> Company
  - [ ] delete_company(id) -> bool
- [ ] Write tests for company operations
  _US-3: Company Management_

## Project CRUD
- [ ] Create core/project.py
  _US-4: Project Management with Methodology_
  - [ ] create_project(company_id, name, methodology, description) -> Project
  - [ ] get_project(id) -> Project
  - [ ] list_projects(company_id?, status?) -> List[Project]
  - [ ] update_project(id, status?, name?, description?) -> Project
  - [ ] delete_project(id) -> bool
- [ ] Validate methodology exists on project creation
  _US-4: Project Management with Methodology_
- [ ] Write tests for project operations
  _US-4: Project Management with Methodology_

## Integration Test
- [ ] Write end-to-end test: create company → create project → verify methodology
  _US-4: Project Management with Methodology_
