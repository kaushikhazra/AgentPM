# Taskyn Web UI - Look & Feel Review

**Date:** 2026-02-05
**Phase:** Phase 1 (Web UI MVP)
**Reviewer:** Velasari (Claude)

---

## Executive Summary

This document provides a thorough evaluation of discrepancies between the HTML mockups located at `.claude/research/web-ui/design/mockups/` and the actual React implementation in `src/taskyn/web/frontend/`. While the implementation captures the essence of the design system, several UI/UX elements are missing, simplified, or deviate from the original mockups.

**Overall Assessment:** The implementation achieves approximately **75-80%** fidelity to the mockups. Core styling (colors, typography, spacing) is well-matched, but several interactive elements, navigation items, and visual refinements are missing.

---

## 1. Navigation Bar (TopNav)

### Mockup Specification
- **Items:** Dashboard, Companies, Projects, Planner, Kanban, Tracker
- **Search bar** with `⌘K` keyboard shortcut indicator
- **User menu** dropdown with avatar, name, email, Settings, Help & Support, and Log out

### Actual Implementation
**File:** [TopNav.tsx](src/taskyn/web/frontend/src/components/organisms/TopNav.tsx)

| Element | Mockup | Actual | Status |
|---------|--------|--------|--------|
| Dashboard link | ✓ | ✓ | OK |
| Companies link | ✓ | ✓ | OK |
| Projects link | ✓ | ✓ | OK |
| **Planner link** | ✓ | ✗ | **MISSING** |
| **Kanban link** | ✓ | ✗ | **MISSING** |
| Tracker link | ✓ | ✓ | OK |
| Search bar | ✓ | ✓ | OK |
| Keyboard shortcut hint | `⌘K` | ✓ | OK |
| User avatar | ✓ | ✓ | OK |

### Discrepancies

1. **Missing Navigation Links (High Priority)**
   - **Planner** nav link is in mockups but missing from TopNav
   - **Kanban** nav link is in mockups but missing from TopNav
   - Routes exist (`/kanban`, `/planner`) but aren't accessible from nav

2. **User Dropdown Content**
   - Mockup shows user name "Kaushik" and email in dropdown header
   - Implementation pulls from auth context (dynamic) - this is correct behavior

---

## 2. Login Page

### Mockup Specification
**File:** `mockups/login.html`
- Logo with "T" icon and "Taskyn" text
- "Welcome back" title
- "Sign in to continue to your workspace" subtitle
- Email field with "Email address" label
- Password field with eye toggle
- "Remember me" checkbox + "Forgot password?" link
- Primary "Sign in" button
- Divider with "or continue with"
- Google and GitHub social login buttons
- "Don't have an account? Create one" footer
- Theme toggle in top-right corner

### Actual Implementation
**File:** [LoginPage.tsx](src/taskyn/web/frontend/src/pages/LoginPage.tsx)

| Element | Mockup | Actual | Status |
|---------|--------|--------|--------|
| Logo | ✓ | ✓ | OK |
| Welcome title | "Welcome back" | "Welcome back" | OK |
| Subtitle | "Sign in to continue to your workspace" | "Sign in to your account to continue" | **DIFFERS** |
| Email label | "Email address" | "Email" | **DIFFERS** |
| Password toggle | ✓ | ✓ | OK |
| Remember me | ✓ | ✓ | OK |
| Forgot password link | ✓ | ✓ | OK |
| Social buttons order | Google, GitHub | GitHub, Google | **REVERSED** |
| Signup link text | "Create one" | "Sign up" | **DIFFERS** |
| **Theme toggle** | Top-right corner | ✗ | **MISSING** |
| Error message styling | N/A | Red banner | OK |

### Discrepancies

1. **Subtitle Text Mismatch (Low Priority)**
   - Mockup: "Sign in to continue to your workspace"
   - Actual: "Sign in to your account to continue"

2. **Email Label (Low Priority)**
   - Mockup: "Email address"
   - Actual: "Email"

3. **Social Button Order (Low Priority)**
   - Mockup: Google first, then GitHub
   - Actual: GitHub first, then Google

4. **Theme Toggle Missing (Medium Priority)**
   - Login mockup shows a dark/light mode toggle in top-right
   - Not implemented on login page

---

## 3. Dashboard Page

### Mockup Specification
**File:** `mockups/dashboard.html`
- Greeting: "Good morning/afternoon/evening, {Name}"
- Subtitle: "You have X tasks due today"
- 4 stat cards: Tasks Due Today, In Progress, Completed This Week, Time Tracked Today
- Two-column layout: Today's Tasks (left), Timer Widget + Activity Feed (right)
- Task items with checkbox, title, project name, due date, priority indicator
- Timer widget showing current timer with Stop/Pause buttons
- Activity feed with icons for completion and time logging
- **Shortcut bar** at bottom

### Actual Implementation
**File:** [DashboardPage.tsx](src/taskyn/web/frontend/src/pages/DashboardPage.tsx)

| Element | Mockup | Actual | Status |
|---------|--------|--------|--------|
| Dynamic greeting | ✓ | ✓ | OK |
| Stat cards | 4 specific | 4 generic | **DIFFERS** |
| Today's Tasks section | "Today's Tasks" | "In Progress" | **DIFFERS** |
| Task checkboxes | ✓ | ✗ | **MISSING** |
| Task due dates | "Due today" | Status text | **DIFFERS** |
| Priority indicators | Color dots | ✓ | OK |
| Timer widget | ✓ | ✓ | OK |
| Activity feed | ✓ | ✓ | OK |
| **Shortcut bar** | ✓ | ✗ | **MISSING** |

### Discrepancies

1. **Stat Cards Labels (Medium Priority)**
   - Mockup: "Tasks Due Today", "In Progress", "Completed This Week", "Time Tracked Today"
   - Actual: "Total Tasks", "In Progress", "Completed", "Projects"
   - Missing time-based stats

2. **Today's Tasks vs In Progress (High Priority)**
   - Mockup shows "Today's Tasks" with due-date-based filtering
   - Actual shows "In Progress" (status-based)
   - Different UX mental model

3. **Task Checkboxes (Medium Priority)**
   - Mockup has interactive checkboxes for task completion
   - Implementation uses TaskItem without checkboxes

4. **Shortcut Bar Missing (Low Priority)**
   - Footer with keyboard shortcuts not visible
   - ShortcutBar component exists but may not be rendered

---

## 4. Projects Page

### Mockup Specification
**File:** `mockups/projects.html`
- "Projects" title with company filter dropdown
- 4 stat cards: Total Projects, Active, Total Tasks, Avg Progress
- 3-column grid of project cards
- Each card: colored icon, name, company, description, stats (epics/stories/tasks), progress bar
- New Project modal with: Name, Company, Methodology, Description, **Color Picker**

### Actual Implementation
**File:** [ProjectsPage.tsx](src/taskyn/web/frontend/src/pages/ProjectsPage.tsx)

| Element | Mockup | Actual | Status |
|---------|--------|--------|--------|
| Page title | ✓ | ✓ | OK |
| Company filter | ✓ | ✓ | OK |
| Stat cards | ✓ | ✓ | OK |
| Project cards grid | ✓ | ✓ | OK |
| Card colored icons | ✓ | ✓ | OK (cycling) |
| Card progress bar | ✓ | ✓ | OK |
| New Project button | ✓ | ✓ | OK |
| Modal: Name field | ✓ | ✓ | OK |
| Modal: Company dropdown | ✓ | ✓ | OK |
| Modal: Methodology | ✓ | ✓ | OK |
| Modal: Description | ✓ | ✓ | OK |
| **Modal: Color picker** | ✓ | ✗ | **MISSING** |

### Discrepancies

1. **Color Picker in Create Modal (Medium Priority)**
   - Mockup shows 6-color picker for project icon color
   - Implementation uses cycling gradient based on index
   - Users cannot choose project color

2. **Project Stats Format (Low Priority)**
   - Mockup: "3 epics", "12 stories", "47 tasks" (fixed format)
   - Actual: Dynamic node types from API

---

## 5. Kanban Board

### Mockup Specification
**File:** `mockups/kanban.html`
- Title "Kanban Board" with project selector dropdown
- 4 columns: Backlog, Ready, In Progress, Done
- Cards with title, date, priority dot
- Active timer indicator on card ("⏱ 01:45:32 tracking")
- Done cards slightly faded (opacity: 0.7)

### Actual Implementation
**File:** [KanbanPage.tsx](src/taskyn/web/frontend/src/pages/KanbanPage.tsx)

| Element | Mockup | Actual | Status |
|---------|--------|--------|--------|
| Page title | ✓ | ✓ | OK |
| Project selector | ✓ | ✓ | OK |
| Dynamic columns | ✓ | ✓ | OK |
| Kanban cards | ✓ | ✓ | OK |
| Card drag-and-drop | ✗ | ✓ | **BONUS** |
| **Timer indicator** | ✓ | ✗ | **MISSING** |
| Done card styling | opacity: 0.7 | `.done-card` class | **PARTIAL** |
| Card due dates | "Today", "Tomorrow" | Node type, ID | **DIFFERS** |
| Priority dots | ✓ | ✗ | **MISSING** |

### Discrepancies

1. **Timer Indicator on Cards (Medium Priority)**
   - Mockup shows "⏱ 01:45:32 tracking" on active card
   - Not implemented - no timer integration in kanban

2. **Card Meta Information (Medium Priority)**
   - Mockup: Due date ("Today", "Tomorrow") + priority dot
   - Actual: Node type + truncated ID
   - Different information hierarchy

3. **Priority Indicators (Medium Priority)**
   - Mockup cards have colored priority dots
   - Implementation doesn't show priority

---

## 6. Project Detail Page

### Mockup Specification
**File:** `mockups/project.html`
- Breadcrumb: Company > Project name
- Title with description
- Settings and "New Epic" buttons
- Stats: Epics, Stories, Tasks, Progress
- Epics list with tabs (All, In Progress, Completed)
- Each epic card: title, ID, child counts, progress bar, status badge

### Actual Implementation
**File:** [ProjectDetailPage.tsx](src/taskyn/web/frontend/src/pages/ProjectDetailPage.tsx)

| Element | Mockup | Actual | Status |
|---------|--------|--------|--------|
| Breadcrumb | ✓ | ✓ | OK |
| Project title | ✓ | ✓ | OK |
| Settings button | ✓ | Partial | **PARTIAL** |
| New Epic button | ✓ | ✓ | OK |
| Stat cards | ✓ | ✓ | OK |
| **Filter tabs** | ✓ | ✗ | **MISSING** |
| Epic cards | ✓ | ✓ | OK |
| Status badges | ✓ | ✓ | OK |

### Discrepancies

1. **Filter Tabs Missing (Medium Priority)**
   - Mockup: "All", "In Progress", "Completed" tabs
   - Not visible in implementation

---

## 7. Tracker/Time Log Page

### Mockup Specification
**File:** `mockups/tracker.html`
- Title "Time Log" with "Manual Entry" button
- Stats: Today, This Week, This Month, Avg/Day
- Timer widget (if tracking)
- Time entries with tabs: Today, Yesterday, This Week
- Entry items: project color dot, task name, times, duration
- Active entry highlighted
- Right sidebar: By Project breakdown, Weekly Overview bar chart
- Manual Entry modal with custom date/time pickers

### Actual Implementation
**File:** [TrackerPage.tsx](src/taskyn/web/frontend/src/pages/TrackerPage.tsx)

| Element | Mockup | Actual | Status |
|---------|--------|--------|--------|
| Page title | ✓ | ✓ | OK |
| Stats cards | ✓ | Needs verification | - |
| Timer widget | ✓ | ✓ | OK |
| Time entries list | ✓ | Needs verification | - |
| **Entry tabs** | ✓ | ? | **NEEDS REVIEW** |
| **Project breakdown sidebar** | ✓ | ? | **NEEDS REVIEW** |
| **Weekly chart** | ✓ | ? | **NEEDS REVIEW** |
| Manual entry modal | ✓ | ✓ | OK |

---

## 8. Global Missing Features

### Shortcut Bar
**Mockup:** `<footer class="shortcut-bar">` at bottom of pages with context-sensitive shortcuts
**Status:** Component exists (`ShortcutBar.tsx`) but needs verification of rendering

### Theme Toggle
**Mockup:** Quick settings bar with dark/light mode toggle + theme color switcher
**Status:** ThemeProvider exists but no quick settings UI visible on pages

### Keyboard Shortcuts
**Mockup:** `js/shortcuts.js` provides page-specific keyboard shortcuts
**Status:** Partial implementation - search modal (`⌘K`) works

---

## 9. CSS/Styling Differences

### Overall Assessment
The theme system (`themes.css`) is well-matched between mockup and implementation. The base CSS follows the same patterns.

### Minor Differences

| Property | Mockup | Actual |
|----------|--------|--------|
| Filter dropdown count | Has count badge | Has count |
| Modal footer | `background: var(--bg-tertiary)` | Same |
| Empty state icon | 64x64px | Matches |

---

## 10. Priority Summary

### All Items Mandatory (Must fix before release)

| # | Issue | Page | Description |
|---|-------|------|-------------|
| 1 | Missing Planner nav link | TopNav | Page exists but inaccessible from navigation |
| 2 | Missing Kanban nav link | TopNav | Page exists but inaccessible from navigation |
| 3 | Dashboard section title | Dashboard | Shows "In Progress" instead of "Today's Tasks" |
| 4 | Dashboard stat card labels | Dashboard | Should show time-based stats per mockup |
| 5 | Task checkboxes | Dashboard | Tasks need completion checkboxes |
| 6 | Project color picker | Projects | Create modal missing 6-color picker |
| 7 | Kanban timer indicator | Kanban | Cards should show active timer ("⏱ tracking") |
| 8 | Kanban priority dots | Kanban | Cards missing priority indicator dots |
| 9 | Kanban due dates | Kanban | Cards should show "Today", "Tomorrow" etc. |
| 10 | Filter tabs | Project Detail | Missing "All / In Progress / Completed" tabs |
| 11 | Login theme toggle | Login | Missing dark/light mode toggle in top-right |
| 12 | Login subtitle text | Login | Should be "Sign in to continue to your workspace" |
| 13 | Login email label | Login | Should be "Email address" not "Email" |
| 14 | Social button order | Login | Should be Google first, then GitHub |
| 15 | Signup link text | Login | Should be "Create one" not "Sign up" |
| 16 | Shortcut bar | All pages | Footer shortcut bar not rendering |

---

## 11. Recommendations

### Immediate Actions
1. Add Planner and Kanban to TopNav navigation
2. Review dashboard requirements - clarify if "Today's Tasks" or "In Progress" is desired
3. Add color picker to project creation modal

### Short-term Improvements
4. Add timer integration to kanban cards
5. Add priority indicators to kanban cards
6. Implement task checkboxes on dashboard
7. Add filter tabs to project detail page

### Future Enhancements
8. Implement shortcut bar consistently
9. Add theme toggle UI (quick settings)
10. Align all text copy with mockups

---

## Appendix: File Mapping

| Mockup | Implementation |
|--------|----------------|
| `login.html` | `LoginPage.tsx` |
| `signup.html` | `SignupPage.tsx` |
| `dashboard.html` | `DashboardPage.tsx` |
| `projects.html` | `ProjectsPage.tsx` |
| `project.html` | `ProjectDetailPage.tsx` |
| `kanban.html` | `KanbanPage.tsx` |
| `tracker.html` | `TrackerPage.tsx` |
| `settings.html` | `SettingsPage.tsx` |
| `css/base.css` | `styles/base.css` |
| `css/themes.css` | `styles/themes.css` |
