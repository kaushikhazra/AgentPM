# Project Editing Capability — Requirements

## Overview

Users can create and delete projects from the Web UI, but cannot edit existing projects. This spec adds edit capability to ProjectDetailPage.

## User Stories

### US-1: Edit project name and description
**As a** project manager,
**I want to** edit a project's name and description after creation,
**So that** I can correct mistakes or update details as the project evolves.

**Acceptance Criteria:**
- An "Edit" button is visible on the ProjectDetailPage header
- Clicking "Edit" opens a modal pre-filled with current project values
- User can modify the name (required, max 255 chars) and description (optional, max 2000 chars)
- On save, the UI reflects the updated values immediately
- A success toast confirms the update

### US-2: Change lifecycle stage
**As a** project manager,
**I want to** change a project's lifecycle stage (entity type) after creation,
**So that** the project's visual indicator reflects its current phase.

**Acceptance Criteria:**
- The edit modal includes the same color-picker for lifecycle stage used in the create modal
- Changing the stage updates the project icon color across all views (detail, list, cards)

### US-3: Change project status
**As a** project manager,
**I want to** change a project's status (active, on_hold, completed, archived),
**So that** I can manage the project lifecycle.

**Acceptance Criteria:**
- The edit modal includes a status dropdown with valid options: active, on_hold, completed, archived
- Changing status is reflected across all views

### US-4: Change methodology (conditional)
**As a** project manager,
**I want to** change a project's methodology when it has no work items,
**So that** I can correct a wrong methodology choice before work begins.

**Acceptance Criteria:**
- The edit modal includes a methodology dropdown (classic_agile, spec_driven)
- If the project has existing nodes, the methodology field is **disabled** with a hint explaining why
- If the project has zero nodes, the field is enabled and editable
- Backend enforces this constraint (ValidationError if nodes exist)

## Out of Scope
- Changing company assignment (would require re-parenting)
- Bulk editing multiple projects
- Inline editing on the projects list page
