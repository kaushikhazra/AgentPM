# Entity Type Feature - Tasks

## Database Layer
- [x] Create `src/taskyn/db/enums.py` with `EntityType` enum
  - _US-1, US-2: Type safety for entity categorization_
- [x] Add `type` column with CHECK constraint to `companies` table in schema.sql
  - _US-1: Categorize Companies by Type_
- [x] Add `type` column with CHECK constraint to `projects` table in schema.sql
  - _US-2: Categorize Projects by Type_
- [x] Add `type: EntityType` field to `Company` model in models.py
  - _US-1: Categorize Companies by Type_
- [x] Add `type: EntityType` field to `Project` model in models.py
  - _US-2: Categorize Projects by Type_

## Core Layer
- [x] Update `create_company()` to accept `EntityType` parameter
  - _US-1: Categorize Companies by Type_
- [x] Update `update_company()` to accept `EntityType` parameter
  - _US-1: Categorize Companies by Type_
- [x] Update `_row_to_company()` to read and convert `type` to enum
  - _US-1: Categorize Companies by Type_
- [x] Update `create_project()` to accept `EntityType` parameter
  - _US-2: Categorize Projects by Type_
- [x] Update `update_project()` to accept `EntityType` parameter
  - _US-2: Categorize Projects by Type_
- [x] Update `_row_to_project()` to read and convert `type` to enum
  - _US-2: Categorize Projects by Type_

## MCP Layer
- [x] Add `type` parameter to `pm_create_company()` with enum validation
  - _US-1: Categorize Companies by Type_
- [x] Add `type` parameter to `pm_update_company()` with enum validation
  - _US-1: Categorize Companies by Type_
- [x] Add `type` parameter to `pm_create_project()` with enum validation
  - _US-2: Categorize Projects by Type_
- [x] Add `type` parameter to `pm_update_project()` with enum validation
  - _US-2: Categorize Projects by Type_

## Web Backend Layer
- [x] Add `EntityType` enum to company schemas (Create, Update, Response)
  - _US-1: Categorize Companies by Type_
- [x] Update company routes to pass `type` to MCP tools
  - _US-1: Categorize Companies by Type_
- [x] Add `EntityType` enum to project schemas (Create, Update, Response)
  - _US-2: Categorize Projects by Type_
- [x] Update project routes to pass `type` to MCP tools
  - _US-2: Categorize Projects by Type_

## Frontend Layer
- [x] Add `ENTITY_TYPES` const array and `EntityType` union type to types/index.ts
  - _US-1, US-2: Type safety in frontend_
- [x] Add `type` field to Company and CompanyCreate interfaces
  - _US-1: Categorize Companies by Type_
- [x] Add `type` field to Project and ProjectCreate interfaces
  - _US-2: Categorize Projects by Type_
- [x] Create `ENTITY_TYPE_COLORS` mapping in types/index.ts
  - _US-1: Type is displayed visually as a color in the UI_
- [x] Update CompaniesPage to use `company.type` for color selection
  - _US-1: Type is displayed visually as a color in the UI_
- [x] Update CompaniesPage create handler to send `type` in API call
  - _US-1: Can select a type when creating a company_
- [ ] Update ProjectsPage for project type support (if applicable)
  - _US-2: Type is displayed visually as a color in the UI_

## Testing & Deployment
- [x] Run existing tests to verify no regressions
  - _All user stories_
- [x] Test company creation with type selection in UI
  - _US-1: Can select a type when creating a company_
- [x] Test invalid type rejection (enum validation)
  - _US-1, US-2: Type safety_
- [x] Verify existing companies display with default type
  - _US-3: Default Type Assignment_
- [x] Rebuild Docker containers and deploy
  - _All user stories_
