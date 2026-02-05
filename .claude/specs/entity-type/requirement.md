# Entity Type Feature - Requirements

## Overview
Add a `type` field to Company and Project entities in the core system. The UI will interpret this type as a visual color indicator.

## User Stories

### US-1: Categorize Companies by Type
**As a** user
**I want to** assign a type/category to my companies
**So that** I can visually distinguish between different kinds of organizations (personal, client, internal, etc.)

**Acceptance Criteria:**
- [ ] Can select a type when creating a company
- [ ] Can change a company's type after creation
- [ ] Type is persisted and retrieved with company data
- [ ] Type is displayed visually as a color in the UI

### US-2: Categorize Projects by Type
**As a** user
**I want to** assign a type/category to my projects
**So that** I can visually distinguish between different kinds of projects

**Acceptance Criteria:**
- [ ] Can select a type when creating a project
- [ ] Can change a project's type after creation
- [ ] Type is persisted and retrieved with project data
- [ ] Type is displayed visually as a color in the UI

### US-3: Default Type Assignment
**As a** user
**I want** a sensible default type assigned when I don't specify one
**So that** existing data and quick creation still works

**Acceptance Criteria:**
- [ ] Type defaults to "default" (or index 0) if not specified
- [ ] Existing companies/projects without type show default color

## Type Values (Lifecycle Stages)
The system supports the following lifecycle stages (with fixed colors):

| Type | Meaning | Color | Hex |
|------|---------|-------|-----|
| `discovery` | Early exploration phase | Ocean Blue | `#0077B6` |
| `potential` | Promising, has potential | Chrome Yellow | `#FFD60A` |
| `matured` | Well-established | Ocean Green | `#2A9D8F` |
| `engaged` | Actively being worked on | Moss Green | `#606C38` |
| `active` | Hot/urgent priority | Coral Red | `#E63946` |
| `dormant` | Inactive/paused | Grey | `#6C757D` |

Note: Colors are fixed and do not change with theme switching.
