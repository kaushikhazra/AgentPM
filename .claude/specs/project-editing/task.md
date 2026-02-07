# Project Editing Capability — Tasks

## Backend Changes
- [x] Add `methodology` field to `ProjectUpdate` schema in `schemas/projects.py`
  _US-4: Change methodology (conditional)_
- [x] Add methodology enum-to-string conversion in `routes/projects.py` update handler
  _US-4: Change methodology (conditional)_

## Frontend Type Changes
- [x] Add `methodology?: string` to `ProjectUpdate` interface in `types/index.ts`
  _US-4: Change methodology (conditional)_

## ProjectDetailPage Edit Modal
- [x] Add edit modal state variables and `useUpdateProject` hook
  _US-1: Edit project name and description_
- [x] Add "Edit" button to header actions
  _US-1: Edit project name and description_
- [x] Add `openEdit()` to pre-fill form from current project
  _US-1: Edit project name and description_
- [x] Add edit modal with name, description, status, methodology, lifecycle stage fields
  _US-1, US-2, US-3, US-4_
- [x] Conditionally disable methodology field when project has nodes
  _US-4: Change methodology (conditional)_
- [x] Add `handleUpdate()` to submit changes via mutation
  _US-1: Edit project name and description_

## Validation
- [x] Build check (vite build, no TypeScript errors)
- [x] Docker deploy and manual test via puppeteer
  - [x] Edit name + description on a project
  - [x] Change lifecycle stage
  - [x] Change status
  - [x] Verify methodology disabled when project has nodes
  - [x] Verify methodology editable when project has no nodes
