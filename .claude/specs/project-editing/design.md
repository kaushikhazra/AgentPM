# Project Editing Capability — Design

## UX Pattern: Edit Modal

Follow the proven pattern from CompaniesPage — a modal dialog opened via an "Edit" button in the page header.

### UI Flow
1. User lands on ProjectDetailPage
2. Header actions show: **Edit** | Delete | New [NodeType]
3. User clicks "Edit" → modal opens pre-filled with current project values
4. User modifies fields → clicks "Save"
5. Modal closes, cache invalidates, toast confirms success
6. If error (e.g., methodology change blocked), error toast appears, modal stays open

### Edit Modal Layout

```
┌─────────────────────────────────────┐
│  Edit Project                    ✕  │
├─────────────────────────────────────┤
│  Project Name                       │
│  ┌─────────────────────────────┐    │
│  │ Current project name        │    │
│  └─────────────────────────────┘    │
│                                     │
│  Status                             │
│  ┌──────────────────────── ▼ ──┐    │
│  │ active                      │    │
│  └─────────────────────────────┘    │
│                                     │
│  Methodology                        │
│  ┌──────────────────────── ▼ ──┐    │
│  │ spec_driven  (disabled*)    │    │
│  └─────────────────────────────┘    │
│  * Cannot change: project has nodes │
│                                     │
│  Lifecycle Stage                    │
│  ○ ○ ● ○ ○ ○  (color picker)       │
│                                     │
│  Description                        │
│  ┌─────────────────────────────┐    │
│  │ Current description...      │    │
│  │                             │    │
│  └─────────────────────────────┘    │
│                                     │
│            [Cancel]  [Save Changes] │
└─────────────────────────────────────┘
```

## Technical Changes

### Backend Schema (`schemas/projects.py`)
Add `methodology` field to `ProjectUpdate`:
```python
methodology: Methodology | None = Field(default=None)
```

### Backend Route (`routes/projects.py`)
Add methodology enum-to-string conversion in `update_project` handler (same pattern as `type`).

### Frontend Type (`types/index.ts`)
Add `methodology` to `ProjectUpdate`:
```typescript
export interface ProjectUpdate {
  name?: string;
  description?: string;
  status?: string;
  type?: EntityType;
  methodology?: string;  // NEW
}
```

### Frontend Page (`ProjectDetailPage.tsx`)
- Add `useUpdateProject` import
- Add edit modal state (`showEdit`, `editName`, `editDesc`, `editType`, `editStatus`, `editMethodology`)
- Add "Edit" button in header actions (pencil icon + "Edit" text)
- Add `openEdit()` to populate form from `project` object
- Add `handleUpdate()` to call mutation
- Methodology field: disabled when `nodes.length > 0` (already fetched)
- Reuse: Modal, Button, form CSS classes, color picker pattern

### Existing Infrastructure (no changes needed)
- `projectsApi.update(id, data)` — API client already exists
- `useUpdateProject()` — mutation hook already exists with cache invalidation + toast
- `Modal` component — ready to use
- Form CSS classes — already in global styles
