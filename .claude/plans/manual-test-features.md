# Feature Test Plan

Comprehensive CLI feature testing.

## Setup
```bash
cd C:\Projects\Taskyn
pip install -e .
# Use a fresh test database (PowerShell)
$env:TASKYN_DB = "test_manual.db"
# Or for cmd.exe: set TASKYN_DB=test_manual.db
```

---

## 1. Company Management

### 1.1 Create Company
```bash
taskyn company create "Acme Corp" -d "Test company"
```
**Expected**: Company created with ID, name, description shown

### 1.2 List Companies
```bash
taskyn company list
```
**Expected**: Table showing Acme Corp (dates in local time)

### 1.3 Show Company
```bash
taskyn company show <company_id>
```
**Expected**: Company details with project count (0)

### 1.4 JSON Output
```bash
taskyn --json company list
```
**Expected**: Valid JSON array (note: JSON dates are in UTC for interoperability)

---

## 2. Project Management

### 2.1 Create Project (Classic Agile)
```bash
taskyn project create <company_id> "Web Redesign"
```
**Expected**: Project created with methodology "classic_agile"

### 2.2 Create Project (Spec-Driven)
```bash
taskyn project create <company_id> "Mobile App" -m spec_driven
```
**Expected**: Project created with methodology "spec_driven"

### 2.3 List Projects
```bash
taskyn project list
```
**Expected**: Both projects listed

### 2.4 Show Project
```bash
taskyn project show <project_id>
```
**Expected**: Project details with stats (0 nodes)

### 2.5 Update Project
```bash
taskyn project update <project_id> --status on_hold
```
**Expected**: Status updated to on_hold

---

## 3. Milestone Management

### 3.1 Create Milestone
```bash
taskyn milestone create <project_id> "Sprint 1" --target 2025-03-01
```
**Expected**: Milestone created with target date (duplicate names are now rejected)

### 3.2 List Milestones
```bash
taskyn milestone list <project_id>
```
**Expected**: Sprint 1 shown

### 3.3 Complete Milestone
```bash
taskyn milestone complete <milestone_id>
```
**Expected**: Status changed to "completed"

---

## 4. Story & Task (Classic Agile)

Use the "Web Redesign" project (classic_agile).

### 4.1 Create Story
```bash
taskyn story create <project_id> "User Login"
```
**Expected**: Story created with status "backlog"

### 4.2 Create Tasks
```bash
taskyn task create <story_id> "Design login form"
taskyn task create <story_id> "Implement backend"
```
**Expected**: Tasks created, linked to story

### 4.3 List Stories
```bash
taskyn story list --project <project_id>
```
**Expected**: "User Login" shown

### 4.4 Show Story with Tasks
```bash
taskyn story show <story_id>
```
**Expected**: Story details + child tasks listed

### 4.5 Start Task
```bash
taskyn task start <task_id>
```
**Expected**: Status → in_progress, timer started

### 4.6 Complete Task
```bash
taskyn task done <task_id>
```
**Expected**: Status → done, timer stopped, duration shown

### 4.7 Block Task
```bash
taskyn task block <task2_id> "Waiting for API docs"
```
**Expected**: Status → blocked, reason shown

---

## 5. Spec-Driven Workflow

Use the "Mobile App" project (spec_driven).

### 5.1 Create Spec
```bash
taskyn node create <project_id> spec "Authentication Spec"
```
**Expected**: Status "draft"

### 5.2 Approve Spec
```bash
taskyn node update <spec_id> --status approved
```
**Expected**: Status → approved

### 5.3 Create Design
```bash
taskyn node create <spec_id> design "Auth Design Doc"
```
**Expected**: Status "draft", Parent shown as the spec

### 5.4 Design Review Flow
```bash
taskyn node update <design_id> --status in_review
taskyn node update <design_id> --status approved
```
**Expected**: Status transitions correctly

### 5.5 Create Implementation
```bash
taskyn node create <design_id> implementation "Implement Auth"
```
**Expected**: Status "todo", Parent shown as the design

### 5.6 Implementation Workflow
```bash
taskyn node start <impl_id>
taskyn node update <impl_id> --status in_review
taskyn node done <impl_id>
```
**Expected**: todo → in_progress → in_review → done

### 5.7 Create Validation
```bash
taskyn node create <impl_id> validation "Auth Tests"
```
**Expected**: Status "pending", Parent shown as the implementation

### 5.8 Validation Pass/Fail
```bash
taskyn node start <validation_id>
taskyn node update <validation_id> --status failed
taskyn node update <validation_id> --status pending
taskyn node start <validation_id>
taskyn node update <validation_id> --status passed
```
**Expected**: Can fail and retry, ends in "passed"

---

## 6. Time Tracking

### 6.1 Start Timer
```bash
taskyn timer start <task_id>
```
**Expected**: Timer started message

### 6.2 Check Status
```bash
taskyn timer status
```
**Expected**: Shows active timer with node info

### 6.3 Stop Timer
```bash
taskyn timer stop
```
**Expected**: Timer stopped, duration shown

### 6.4 Log Manual Time
```bash
taskyn timer log <task_id> 45 --notes "Code review"
```
**Expected**: 45 minutes logged

---

## 7. Tags

### 7.1 Create Tag
```bash
taskyn tag create "bug" --color red
taskyn tag create "urgent"
```
**Expected**: Tags created

### 7.2 List Tags
```bash
taskyn tag list
```
**Expected**: Both tags shown

### 7.3 Tag Node
```bash
taskyn tag add <task_id> bug
taskyn tag add <task_id> urgent
```
**Expected**: Tags added to node

### 7.4 Remove Tag
```bash
taskyn tag remove <task_id> urgent
```
**Expected**: Tag removed

---

## 8. Search & Reporting

### 8.1 Search
```bash
taskyn search "Login"
```
**Expected**: Finds "User Login" story and related items

### 8.2 Dashboard
```bash
taskyn dashboard
```
**Expected**: Shows active timer (if any), in-progress items, blockers

### 8.3 Stats
```bash
taskyn stats <project_id>
```
**Expected**: Project statistics displayed

### 8.4 Activity
```bash
taskyn activity --limit 10
```
**Expected**: Recent activity log

---

## 9. Backup & Export

### 9.1 Create Backup
```bash
taskyn backup create
```
**Expected**: Backup file created in ~/.taskyn/backups/

### 9.2 List Backups
```bash
taskyn backup list
```
**Expected**: Backup listed with size and date

### 9.3 Export All
```bash
taskyn export json -o full_export.json
```
**Expected**: JSON file with all data

### 9.4 Export Project
```bash
taskyn export json --project <project_id> -o project_export.json
```
**Expected**: JSON file with single project data

---

## Feature Test Checklist

### Company & Project
- [x] Create/list/show company
- [x] Create project with both methodologies
- [x] Update project status

### Work Items
- [x] Create story and tasks (classic_agile)
- [x] Task start/done/block workflow
- [x] Spec-driven full workflow (spec → design → impl → validation)
- [x] Status transitions work correctly

### Time Tracking
- [x] Timer start/stop
- [x] Manual time logging
- [x] Timer status shows correctly

### Tags
- [x] Create tags
- [x] Add/remove tags from nodes

### Reporting
- [x] Search finds items
- [x] Dashboard displays correctly
- [x] Stats show project metrics
- [x] Activity log works

### Backup & Export
- [x] Backup creates file
- [x] Export generates valid JSON
