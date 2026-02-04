# Component Architecture

This document maps our HTML mockups to a React component tree.

---

## Component Hierarchy Overview

```
App
├── ThemeProvider (context for theme/mode)
├── AuthProvider (context for user state)
├── TimerProvider (context for global timer state)
├── ModalManager (portal-based, central modal system)
├── ToastProvider (notification system)
│
├── Routes
│   ├── PublicRoutes
│   │   ├── LoginPage
│   │   ├── SignupPage
│   │   └── OnboardingPage
│   │
│   └── ProtectedRoutes
│       └── AppShell
│           ├── TopNav
│           └── PageContent
│               ├── DashboardPage
│               ├── CompaniesPage
│               ├── ProjectsPage
│               ├── ProjectDetailPage
│               ├── NodeDetailPage      ← Generic, methodology-aware
│               ├── KanbanPage
│               ├── PlannerPage
│               ├── TrackerPage
│               └── SettingsPage
```

### Global Providers (App Level)

| Provider | Purpose |
|----------|---------|
| `ThemeProvider` | Theme (amber/wine/ocean/forest) and mode (dark/light) |
| `AuthProvider` | User authentication state, login/logout |
| `TimerProvider` | Active timer state, persists across navigation |
| `ModalManager` | Central modal rendering via portal |
| `ToastProvider` | Toast notifications queue and display |

---

## Methodology-Aware UI Architecture

### The Problem
Taskyn supports multiple methodologies with different node types:
- **Classic Agile**: Epic → Story → Task
- **Spec Driven**: Spec → Design → Implementation → Validation
- **Future**: PIV (Plan → Implement → Verify), etc.

Creating separate pages for each node type (EpicDetailPage, StoryDetailPage, SpecDetailPage...) violates DRY.

### The Solution: Generic Node-Based Components

**One generic page** that adapts based on methodology:

```
NodeDetailPage (nodeId)
  → fetches node
  → gets project.methodology
  → renders using methodology UI config
```

### Separation of Concerns

| Layer | Responsibility | Location |
|-------|---------------|----------|
| **Python Backend** | Data model, validation, statuses, transitions | `src/taskyn/methodologies/` |
| **React Frontend** | Display names, icons, colors | `src/config/methodology-ui.ts` |

**Backend stays pure** - no UI concerns.
**Frontend owns presentation** - maps node types to visuals.

### Methodology UI Config (Frontend)

```typescript
// src/config/methodology-ui.ts
export const METHODOLOGY_UI = {
  classic_agile: {
    displayName: "Classic Agile",
    nodeTypes: {
      epic:  { displayName: "Epic",  plural: "Epics",  icon: "layers", color: "lavender" },
      story: { displayName: "Story", plural: "Stories", icon: "book",   color: "mint" },
      task:  { displayName: "Task",  plural: "Tasks",  icon: "check",  color: "sky" },
    },
    statusColors: {
      draft: "gray", backlog: "gray", todo: "gray",
      ready: "sky", in_progress: "amber",
      in_review: "peach", blocked: "coral",
      done: "mint", cancelled: "gray",
    }
  },
  spec_driven: {
    displayName: "Spec-Driven",
    nodeTypes: {
      spec:           { displayName: "Spec",           plural: "Specs",           icon: "document", color: "peach" },
      design:         { displayName: "Design",         plural: "Designs",         icon: "pencil",   color: "lavender" },
      implementation: { displayName: "Implementation", plural: "Implementations", icon: "code",     color: "mint" },
      validation:     { displayName: "Validation",     plural: "Validations",     icon: "shield",   color: "sky" },
    },
    statusColors: { /* ... */ }
  }
};
```

### How Generic Components Use It

```tsx
// NodeDetailPage.tsx
const node = useNode(nodeId);
const project = useProject(node.projectId);
const uiConfig = METHODOLOGY_UI[project.methodology];
const nodeTypeUI = uiConfig.nodeTypes[node.nodeType];

return (
  <DetailLayout>
    <Breadcrumb /> {/* Built from parent edges */}
    <PageHeader
      title={node.title}
      icon={nodeTypeUI.icon}
      badge={<StatusBadge status={node.status} colors={uiConfig.statusColors} />}
    />
    <NodeChildren nodeId={nodeId} /> {/* Lists children based on edge definitions */}
  </DetailLayout>
);
```

### User Experience by Methodology

| What user sees | Classic Agile | Spec Driven |
|----------------|---------------|-------------|
| Nav item | "Epics" | "Specs" |
| Breadcrumb | Project → Epic → Story | Project → Spec → Design |
| Create button | "New Story" | "New Implementation" |
| Page title | "My Epic Title" | "My Spec Title" |

**Same code, different experience.**

---

## Atomic Design Mapping

We'll organize components using **Atomic Design** principles:

### Atoms (smallest, reusable)
Basic building blocks that can't be broken down further.

| Component | Description | Used In |
|-----------|-------------|---------|
| `Button` | Primary, secondary, ghost variants | Everywhere |
| `Input` | Text input with label | Forms |
| `Checkbox` | Task checkbox | TaskItem |
| `Badge` | Status/count indicator | Nav, Cards |
| `Avatar` | User avatar with initials | TopNav, Activity |
| `Icon` | SVG icon wrapper | Everywhere |
| `StatusDot` | Priority/status indicator | TaskItem, Cards |
| `Kbd` | Keyboard shortcut display | Search, ShortcutBar |

### Molecules (combinations of atoms)
Groups of atoms functioning together as a unit.

| Component | Atoms Used | Description |
|-----------|------------|-------------|
| `NavLink` | Icon, Badge | Navigation item |
| `SearchBar` | Icon, Input | Simple search input |
| `UserMenu` | Avatar, Dropdown | User dropdown |
| `TaskItem` | Checkbox, StatusDot | Single task row |
| `StatCard` | Text elements | Metric display |
| `ActivityItem` | Avatar/Icon, Text | Activity feed row |
| `Breadcrumb` | Links, Separator | Navigation trail |
| `FilterBadge` | Icon, Text, Dropdown | Company/project filter |
| `DatePicker` | Input, Calendar | Date selection |
| `TimePicker` | Input, TimeList | Time selection |

### Organisms (complex components)
Relatively complex UI components composed of molecules and atoms.

| Component | Molecules Used | Description |
|-----------|----------------|-------------|
| `TopNav` | Logo, NavLink[], SearchBar, UserMenu | Main navigation |
| `Section` | Header, Content slot | Card container |
| `TaskList` | TaskItem[] | List of tasks |
| `TimerWidget` | Display, Controls | Active timer |
| `ActivityFeed` | ActivityItem[] | Recent activity |
| `KanbanColumn` | Header, KanbanCard[] | Single column |
| `KanbanBoard` | KanbanColumn[] | Full board |
| `NodeCard` | Title, Meta, Progress | Generic node card (adapts to methodology) |
| `NodeList` | NodeCard[] | List of nodes (adapts to methodology) |
| `NodeChildren` | NodeList | Children of a node (based on edge definitions) |
| `SettingsSection` | Header, Form fields | Settings group |
| `Modal` | Overlay, Content, Actions | Reusable modal shell |
| `Toast` | Icon, Message, Action | Single notification |

### Templates (page layouts)
Page-level layouts that arrange organisms.

| Template | Description |
|----------|-------------|
| `AuthLayout` | Centered card for login/signup |
| `AppShell` | TopNav + main content area |
| `DashboardLayout` | Stats grid + 2-column content |
| `DetailLayout` | Breadcrumb + header + content |
| `FullWidthLayout` | Edge-to-edge (Kanban) |

### Pages
Specific instances of templates with real content.

| Page | Template | Key Organisms |
|------|----------|---------------|
| `LoginPage` | AuthLayout | LoginForm |
| `SignupPage` | AuthLayout | SignupForm |
| `OnboardingPage` | AuthLayout | OnboardingWizard |
| `DashboardPage` | DashboardLayout | StatCard[], TaskList, TimerWidget, ActivityFeed |
| `CompaniesPage` | AppShell | CompanyList |
| `ProjectsPage` | AppShell | ProjectGrid |
| `ProjectDetailPage` | DetailLayout | NodeList (root nodes for methodology) |
| `NodeDetailPage` | DetailLayout | NodeChildren, NodeDetails (generic, methodology-aware) |
| `KanbanPage` | FullWidthLayout | KanbanBoard |
| `PlannerPage` | AppShell | PlannerView |
| `TrackerPage` | AppShell | TimeEntryList, TimerWidget |
| `SettingsPage` | AppShell | SettingsSection[] |

---

## Project Structure

### Overall Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  React UI   │ ───► │  FastAPI    │ ───► │ MCP Server  │ ───► │ Taskyn Core │
│  (Browser)  │ HTTP │  (REST)     │      │ (Tools)     │      │ (Python)    │
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
     frontend            backend              mcp/                 core/
```

**Single Interface Concept**: FastAPI talks to MCP server, which is the single interface to Taskyn core. No business logic duplication.

### Folder Structure

```
src/taskyn/
├── db/                       # existing - database layer
├── graph/                    # existing - graph layer
├── core/                     # existing - business logic
├── methodologies/            # existing - PM methodologies
├── cli/                      # existing - CLI interface
├── mcp/                      # existing - MCP server interface
├── exceptions.py             # existing
│
└── web/                      # NEW - web interface package
    ├── __init__.py
    │
    ├── backend/              # FastAPI REST API
    │   ├── __init__.py
    │   ├── main.py           # FastAPI app entry
    │   ├── routes/
    │   │   ├── __init__.py
    │   │   ├── auth.py
    │   │   ├── projects.py
    │   │   ├── tasks.py
    │   │   ├── timer.py
    │   │   └── ...
    │   ├── schemas/          # Pydantic models for API
    │   └── deps.py           # Dependencies (MCP client, auth)
    │
    └── frontend/             # React application
        ├── package.json
        ├── vite.config.ts
        ├── index.html
        │
        └── src/
            ├── App.tsx
            ├── main.tsx
            │
            ├── config/               # Configuration
            │   └── methodology-ui.ts # UI metadata for each methodology
            │
            ├── api/              # API client layer
            │   ├── client.ts     # Axios/fetch setup
            │   ├── projects.ts
            │   ├── nodes.ts      # Generic node operations
            │   └── ...
            │
            ├── providers/
            │   ├── ThemeProvider.tsx
            │   ├── AuthProvider.tsx
            │   ├── TimerProvider.tsx
            │   ├── ModalProvider.tsx
            │   └── ToastProvider.tsx
            │
            ├── hooks/
            │   ├── useTheme.ts
            │   ├── useAuth.ts
            │   ├── useTimer.ts
            │   ├── useModal.ts
            │   ├── useToast.ts
            │   └── useHotkeys.ts
            │
            ├── components/
            │   ├── atoms/
            │   │   ├── Button.tsx
            │   │   ├── Input.tsx
            │   │   ├── Checkbox.tsx
            │   │   ├── Badge.tsx
            │   │   ├── Avatar.tsx
            │   │   ├── Icon.tsx
            │   │   └── StatusDot.tsx
            │   │
            │   ├── molecules/
            │   │   ├── NavLink.tsx
            │   │   ├── SearchBar.tsx
            │   │   ├── UserMenu.tsx
            │   │   ├── TaskItem.tsx
            │   │   ├── StatCard.tsx
            │   │   ├── ActivityItem.tsx
            │   │   ├── Breadcrumb.tsx
            │   │   ├── FilterBadge.tsx
            │   │   ├── DatePicker.tsx
            │   │   └── TimePicker.tsx
            │   │
            │   ├── organisms/
            │   │   ├── TopNav.tsx
            │   │   ├── Section.tsx
            │   │   ├── TaskList.tsx
            │   │   ├── TimerWidget.tsx
            │   │   ├── ActivityFeed.tsx
            │   │   ├── KanbanColumn.tsx
            │   │   ├── KanbanBoard.tsx
            │   │   ├── WorkItemCard.tsx
            │   │   ├── WorkItemList.tsx
            │   │   ├── SettingsSection.tsx
            │   │   ├── Modal.tsx
            │   │   └── Toast.tsx
            │   │
            │   └── templates/
            │       ├── AuthLayout.tsx
            │       ├── AppShell.tsx
            │       ├── DashboardLayout.tsx
            │       ├── DetailLayout.tsx
            │       └── FullWidthLayout.tsx
            │
            ├── pages/
            │   ├── LoginPage.tsx
            │   ├── SignupPage.tsx
            │   ├── OnboardingPage.tsx
            │   ├── DashboardPage.tsx
            │   ├── CompaniesPage.tsx
            │   ├── ProjectsPage.tsx
            │   ├── ProjectDetailPage.tsx
            │   ├── NodeDetailPage.tsx    # Generic, handles all node types
            │   ├── KanbanPage.tsx
            │   ├── PlannerPage.tsx
            │   ├── TrackerPage.tsx
            │   └── SettingsPage.tsx
            │
            └── styles/
                ├── themes.css
                └── base.css
```

---

## Component-to-Mockup Mapping

| Mockup File | Page Component | Key Components |
|-------------|----------------|----------------|
| `login.html` | LoginPage | AuthLayout, Input, Button |
| `signup.html` | SignupPage | AuthLayout, Input, Button |
| `onboarding.html` | OnboardingPage | AuthLayout, OnboardingWizard |
| `dashboard.html` | DashboardPage | TopNav, StatCard, TaskList, TimerWidget, ActivityFeed |
| `company.html` | CompaniesPage | TopNav, CompanyCard, Section |
| `projects.html` | ProjectsPage | TopNav, FilterBadge, ProjectCard |
| `project.html` | ProjectDetailPage | TopNav, Breadcrumb, NodeList |
| `project-empty.html` | ProjectDetailPage | EmptyState |
| `epic.html` | NodeDetailPage | TopNav, Breadcrumb, NodeList (renders as "Epic" for classic_agile) |
| `story.html` | NodeDetailPage | TopNav, Breadcrumb, NodeList (renders as "Story" for classic_agile) |
| `kanban.html` | KanbanPage | TopNav, KanbanBoard |
| `planner.html` | PlannerPage | TopNav, PlannerView, DatePicker |
| `tracker.html` | TrackerPage | TopNav, TimerWidget, TimeEntryList |
| `settings.html` | SettingsPage | TopNav, SettingsSection, ThemeSwitcher |

**Note:** `epic.html` and `story.html` mockups represent how NodeDetailPage renders for Classic Agile methodology. For Spec Driven, the same NodeDetailPage would render "Spec", "Design", etc. based on the methodology UI config.

---

## Notes

1. **TopNav is always present** in authenticated routes - lives in AppShell
2. **TimerWidget state is global** - managed by TimerProvider, widget rendered on Dashboard/Tracker
3. **Theme/Mode controls** in Settings and QuickSettings bar - managed by ThemeProvider
4. **ShortcutBar** at bottom - context-sensitive, needs route awareness for hotkey hints
5. **All CRUD via modals** - ModalManager handles create/edit/delete flows
6. **Hotkeys** - implemented app-wide, no command palette needed

---

## Decisions

- [x] **TimerWidget state is global** - Timer persists across page navigation. Managed at app level.
- [x] **No command palette** - Using hotkeys instead. SearchBar is simple search only (remove ⌘K hint).
- [x] **Central ModalManager** - All CRUD operations and confirmations use modals. Single portal-based manager.
- [x] **Toast/Notification system** - For feedback (success, error, info messages).
- [x] **Generic Node-Based Pages** - One NodeDetailPage adapts to all methodologies. No EpicDetailPage, StoryDetailPage, etc.
- [x] **Frontend owns UI metadata** - Python backend stays pure (data/validation). Frontend defines display names, icons, colors in `methodology-ui.ts`.

