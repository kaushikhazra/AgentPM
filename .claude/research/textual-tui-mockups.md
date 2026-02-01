# Taskyn TUI Mockups

**Date:** 2026-02-01
**Purpose:** Visual mockups for Taskyn Terminal User Interface

---

## 1. Main Dashboard (Default View)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  Taskyn                                                          12:30 PM  ●REC  │
├──────────────────────────────────────────────────────────────────────────────────┤
│ ┌─ Projects ──────────┐ ┌─ Tasks ─────────────────────────────────────────────┐  │
│ │ ▼ Acme Corp         │ │ Status │ Title                    │ Priority │ Due   │  │
│ │   ▼ Taskyn          │ ├────────┼──────────────────────────┼──────────┼───────┤  │
│ │     ▶ v1.0 Release  │ │ ● TODO │ Implement TUI dashboard  │ HIGH     │ Feb 5 │  │
│ │     ▶ v1.1 Features │ │ ● PROG │ Create project tree      │ HIGH     │ Feb 3 │  │
│ │   ▶ Website Redesign│ │ ✓ DONE │ Research Textual library │ HIGH     │ Feb 1 │  │
│ │ ▶ Personal          │ │ ○ BACK │ Add export functionality │ MED      │ Feb 10│  │
│ │   ▶ Side Projects   │ │ ○ BACK │ Write documentation      │ LOW      │ Feb 15│  │
│ │                     │ │        │                          │          │       │  │
│ └─────────────────────┘ └────────────────────────────────────────────────────────┘  │
│ ┌─ Stats ─────────────────────────────┐ ┌─ Active Timer ──────────────────────┐  │
│ │  Progress: 12/20 tasks (60%)        │ │                                     │  │
│ │  ████████████░░░░░░░░               │ │      01:23:45                       │  │
│ │                                     │ │                                     │  │
│ │  Today: 3 completed, 2 in progress  │ │  Task: Implement TUI dashboard      │  │
│ │  Sprint: 8 days remaining           │ │  [■ Pause]  [□ Stop]                │  │
│ └─────────────────────────────────────┘ └─────────────────────────────────────┘  │
│ ┌─ Activity ────────────────────────────────────────────────────────────────────┐  │
│ │ 12:25  You created task "Implement TUI dashboard"                            │  │
│ │ 12:20  You completed "Research Textual library"                              │  │
│ │ 12:15  You started timer on "Create project tree"                            │  │
│ │ 11:45  You moved "Add validation" to IN_PROGRESS                             │  │
│ └───────────────────────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────────────────┤
│  n New Task  │  t Timer  │  / Search  │  ? Help  │  1-4 Views  │  q Quit        │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Task Detail View (When Task Selected)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  Taskyn > Acme Corp > Taskyn > v1.0 Release                      12:35 PM       │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─ Task Details ───────────────────────────────────────────────────────────┐   │
│  │                                                                           │   │
│  │  TASK-42: Implement TUI dashboard                                         │   │
│  │  ─────────────────────────────────────────                                │   │
│  │                                                                           │   │
│  │  Status:    ● IN_PROGRESS          Priority:  ▲ HIGH                     │   │
│  │  Assignee:  Kaushik                Due Date:  2026-02-05                 │   │
│  │  Estimate:  4h                     Logged:    1h 23m                     │   │
│  │                                                                           │   │
│  │  ─────────────────────────────────────────                                │   │
│  │  Description:                                                             │   │
│  │                                                                           │   │
│  │  Create the main dashboard view for Taskyn TUI using Textual library.    │   │
│  │  Should include:                                                          │   │
│  │  - Project tree sidebar                                                   │   │
│  │  - Task list with sorting/filtering                                       │   │
│  │  - Stats panel with progress                                              │   │
│  │  - Active timer display                                                   │   │
│  │                                                                           │   │
│  │  ─────────────────────────────────────────                                │   │
│  │  Tags:  [tui] [frontend] [v1.0]                                          │   │
│  │                                                                           │   │
│  │  ─────────────────────────────────────────                                │   │
│  │  Subtasks:                                                                │   │
│  │  ✓ Design layout mockups                                                  │   │
│  │  ● Implement sidebar tree                                                 │   │
│  │  ○ Implement task table                                                   │   │
│  │  ○ Add keyboard navigation                                                │   │
│  │                                                                           │   │
│  └───────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─ Time Entries ───────────────────────────────────────────────────────────┐   │
│  │  2026-02-01  09:00 - 10:23  (1h 23m)  "Initial implementation"           │   │
│  └───────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│  e Edit  │  s Status  │  t Timer  │  c Comment  │  Esc Back  │  d Delete        │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. New Task Modal

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  Taskyn                                                          12:40 PM       │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                   ┌─ New Task ─────────────────────────────────┐                │
│                   │                                             │                │
│                   │  Title:                                     │                │
│                   │  ┌─────────────────────────────────────────┐│                │
│                   │  │ Implement user authentication           ││                │
│                   │  └─────────────────────────────────────────┘│                │
│                   │                                             │                │
│                   │  Project:           Type:                   │                │
│                   │  ┌──────────────┐   ┌──────────────┐        │                │
│                   │  │ Taskyn     ▼ │   │ Task       ▼ │        │                │
│                   │  └──────────────┘   └──────────────┘        │                │
│                   │                                             │                │
│                   │  Priority:          Status:                 │                │
│                   │  ┌──────────────┐   ┌──────────────┐        │                │
│                   │  │ High       ▼ │   │ Backlog    ▼ │        │                │
│                   │  └──────────────┘   └──────────────┘        │                │
│                   │                                             │                │
│                   │  Description:                               │                │
│                   │  ┌─────────────────────────────────────────┐│                │
│                   │  │ Add OAuth2 support for user login.     ││                │
│                   │  │ Include Google and GitHub providers.   ││                │
│                   │  │                                         ││                │
│                   │  └─────────────────────────────────────────┘│                │
│                   │                                             │                │
│                   │  Due Date:          Estimate:               │                │
│                   │  ┌──────────────┐   ┌──────────────┐        │                │
│                   │  │ 2026-02-10   │   │ 4h           │        │                │
│                   │  └──────────────┘   └──────────────┘        │                │
│                   │                                             │                │
│                   │       [ Create Task ]    [ Cancel ]         │                │
│                   │                                             │                │
│                   └─────────────────────────────────────────────┘                │
│                                                                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│  Tab Next Field  │  Shift+Tab Previous  │  Enter Submit  │  Esc Cancel          │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Command Palette (Search)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  Taskyn                                                          12:45 PM       │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│            ┌─ Command Palette ──────────────────────────────────────┐           │
│            │  > implement                                            │           │
│            ├─────────────────────────────────────────────────────────┤           │
│            │  ▶ TASK  Implement TUI dashboard           Taskyn/v1.0  │           │
│            │    TASK  Implement user authentication     Taskyn/v1.0  │           │
│            │    TASK  Implement export to CSV           Taskyn/v1.1  │           │
│            │  ──────────────────────────────────────────────────────  │           │
│            │    CMD   New Task                          Ctrl+N       │           │
│            │    CMD   Toggle Dark Mode                  Ctrl+D       │           │
│            │    CMD   Open Settings                     Ctrl+,       │           │
│            └─────────────────────────────────────────────────────────┘           │
│                                                                                  │
│  ┌─ Projects ──────────┐ ┌─ Tasks ─────────────────────────────────────────────┐│
│  │ ▼ Acme Corp         │ │ Status │ Title                    │ Priority │ Due   ││
│  │   ▼ Taskyn          │ ├────────┼──────────────────────────┼──────────┼───────┤│
│  │     ▶ v1.0 Release  │ │ ● TODO │ Implement TUI dashboard  │ HIGH     │ Feb 5 ││
│  │                     │ │        │                          │          │       ││
│  └─────────────────────┘ └────────────────────────────────────────────────────────┘│
│                                                                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│  ↑↓ Navigate  │  Enter Select  │  Esc Close                                     │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Project View (Tabbed Interface)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  Taskyn > Acme Corp > Taskyn                                     12:50 PM       │
├──────────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────┬───────────┬────────────┬──────────┬────────────┐                  │
│  │ Overview │  Backlog  │ ● Sprint   │ Timeline │  Settings  │                  │
│  └──────────┴───────────┴────────────┴──────────┴────────────┘                  │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                           SPRINT 3 - Week 2                               │  │
│  │                         Feb 1 - Feb 14, 2026                              │  │
│  ├───────────────────────────────────────────────────────────────────────────┤  │
│  │                                                                           │  │
│  │  BACKLOG (2)        TODO (3)           IN PROGRESS (2)      DONE (5)     │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐│  │
│  │  │             │    │ TASK-45     │    │ TASK-42     │    │ TASK-38     ││  │
│  │  │ TASK-50     │    │ Add filters │    │ TUI dashbrd │    │ Research    ││  │
│  │  │ Export CSV  │    │ ▲ HIGH      │    │ ▲ HIGH      │    │ ✓ DONE      ││  │
│  │  │ ─ MED       │    │ Feb 8       │    │ Feb 5       │    │             ││  │
│  │  │             │    └─────────────┘    │ 1h 23m      │    └─────────────┘│  │
│  │  └─────────────┘    ┌─────────────┐    └─────────────┘    ┌─────────────┐│  │
│  │  ┌─────────────┐    │ TASK-46     │    ┌─────────────┐    │ TASK-39     ││  │
│  │  │ TASK-51     │    │ Unit tests  │    │ TASK-43     │    │ Setup repo  ││  │
│  │  │ Documenta.. │    │ ─ MED       │    │ Project tre │    │ ✓ DONE      ││  │
│  │  │ ▼ LOW       │    │ Feb 10      │    │ ▲ HIGH      │    │             ││  │
│  │  └─────────────┘    └─────────────┘    │ Feb 3       │    └─────────────┘│  │
│  │                     ┌─────────────┐    └─────────────┘    ┌─────────────┐│  │
│  │                     │ TASK-47     │                       │ (3 more...) ││  │
│  │                     │ CSS styling │                       │             ││  │
│  │                     │ ─ MED       │                       └─────────────┘│  │
│  │                     └─────────────┘                                      │  │
│  │                                                                           │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  Sprint Progress: 5/12 (42%)  ████████░░░░░░░░░░░░                              │
│                                                                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│  n New Task  │  ←→ Move Column  │  Enter Details  │  f Filter  │  Esc Back      │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Timer View (Focused Mode)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  Taskyn - Focus Mode                                             12:55 PM       │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                                                                                  │
│                                                                                  │
│                          ┌─────────────────────────────┐                        │
│                          │                             │                        │
│                          │      ██████╗  ███╗          │                        │
│                          │     ██╔═══██╗████║          │                        │
│                          │     ██║   ██║╚═██║          │                        │
│                          │     ██║   ██║ ╚██║          │                        │
│                          │     ╚██████╔╝  ██║          │                        │
│                          │      ╚═════╝   ╚═╝          │                        │
│                          │                             │                        │
│                          │      :  23  :  45           │                        │
│                          │                             │                        │
│                          │   ●  RECORDING              │                        │
│                          │                             │                        │
│                          └─────────────────────────────┘                        │
│                                                                                  │
│                    Task: Implement TUI dashboard                                │
│                    Project: Taskyn > v1.0 Release                               │
│                                                                                  │
│                    Today's Total: 3h 45m                                        │
│                                                                                  │
│                                                                                  │
│                     [ ■ Pause ]      [ □ Stop ]                                 │
│                                                                                  │
│                                                                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│  Space Pause/Resume  │  s Stop & Save  │  Esc Back to Dashboard                 │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Settings Screen

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  Taskyn - Settings                                               1:00 PM        │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─ Appearance ─────────────────────────────────────────────────────────────┐   │
│  │                                                                           │   │
│  │  Theme:              ┌──────────────────────────┐                        │   │
│  │                      │ ● Dark                    │                        │   │
│  │                      │ ○ Light                   │                        │   │
│  │                      │ ○ System                  │                        │   │
│  │                      └──────────────────────────┘                        │   │
│  │                                                                           │   │
│  │  Accent Color:       [████] Blue                                         │   │
│  │                                                                           │   │
│  └───────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─ Default Project Settings ───────────────────────────────────────────────┐   │
│  │                                                                           │   │
│  │  Methodology:        ┌──────────────────────────┐                        │   │
│  │                      │ Classic Agile          ▼ │                        │   │
│  │                      └──────────────────────────┘                        │   │
│  │                                                                           │   │
│  │  Default View:       ┌──────────────────────────┐                        │   │
│  │                      │ Dashboard              ▼ │                        │   │
│  │                      └──────────────────────────┘                        │   │
│  │                                                                           │   │
│  └───────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─ Database ───────────────────────────────────────────────────────────────┐   │
│  │                                                                           │   │
│  │  Location:    ~/.taskyn/taskyn.db                                        │   │
│  │  Size:        2.4 MB                                                     │   │
│  │                                                                           │   │
│  │  [ Backup Now ]    [ Export Data ]    [ Reset Database ]                 │   │
│  │                                                                           │   │
│  └───────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│  Tab Navigate  │  Enter Select  │  Esc Back                                     │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Confirm Dialog

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  Taskyn                                                          1:05 PM        │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─ Projects ──────────┐ ┌─ Tasks ─────────────────────────────────────────────┐│
│  │ ▼ Acme Corp         │ │ Status │ Title                    │ Priority │ Due   ││
│  │   ▼ Taskyn ┌─────────────────────────────────────────────┐│          │       ││
│  │     ▶ v1.0 │                                             ││──────────┼───────┤│
│  │     ▶ v1.1 │   ⚠ Delete Task?                           ││ HIGH     │ Feb 5 ││
│  │   ▶ Website│                                             ││ HIGH     │ Feb 3 ││
│  │ ▶ Personal │   Are you sure you want to delete:         ││ HIGH     │ Feb 1 ││
│  │            │   "Implement TUI dashboard"?                ││ MED      │ Feb 10││
│  │            │                                             ││ LOW      │ Feb 15││
│  │            │   This action cannot be undone.             ││          │       ││
│  │            │                                             ││──────────────────┘│
│  │            │        [ Yes, Delete ]    [ Cancel ]        │                   │
│  │            │                                             │                   │
│  │            └─────────────────────────────────────────────┘                   │
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│  y Yes  │  n No  │  Esc Cancel                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Status Indicators Legend

```
Status Icons:
  ○  BACKLOG    - Not started, in queue
  ●  TODO       - Ready to work on
  ◐  PROGRESS   - Currently in progress
  ✓  DONE       - Completed
  ✗  BLOCKED    - Blocked by dependency

Priority Icons:
  ▲  HIGH       - Urgent/Critical
  ─  MEDIUM     - Normal priority
  ▼  LOW        - Can wait

Timer States:
  ●REC          - Timer recording
  ⏸             - Timer paused
  ○             - No active timer

Node Type Icons:
  🏢  Company
  📁  Project
  🎯  Milestone
  📖  Story
  ✓   Task
  📋  Spec (spec-driven methodology)
```

---

## 10. Keyboard Shortcuts Reference

```
┌─ Global ────────────────────────────────────────────────────────────────────────┐
│  Ctrl+N      New Task                 Ctrl+P      Command Palette              │
│  Ctrl+F      Search                   Ctrl+D      Toggle Dark Mode             │
│  1-4         Switch View Tabs         Ctrl+,      Settings                     │
│  ?           Help                     q           Quit                         │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─ Navigation ────────────────────────────────────────────────────────────────────┐
│  ↑/↓/j/k     Move up/down             ←/→/h/l     Collapse/Expand tree        │
│  Enter       Select/Open              Esc         Back/Cancel                  │
│  Tab         Next element             Shift+Tab   Previous element             │
│  Home        First item               End         Last item                    │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─ Task Actions ──────────────────────────────────────────────────────────────────┐
│  e           Edit task                d           Delete task                  │
│  s           Change status            p           Change priority              │
│  t           Start/Stop timer         c           Add comment                  │
│  m           Move to project          Space       Toggle done                  │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─ Timer ─────────────────────────────────────────────────────────────────────────┐
│  Space       Pause/Resume             s           Stop and save                │
│  Esc         Back to dashboard                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Responsive Considerations

The TUI should adapt to terminal size:

**Minimum (80x24):**
- Hide sidebar, show task list only
- Collapsed stats panel
- Footer shows essential shortcuts only

**Medium (120x40):**
- Sidebar visible
- Stats panel visible
- Full footer

**Large (160x50+):**
- All panels visible
- Activity log expanded
- Detailed task cards
