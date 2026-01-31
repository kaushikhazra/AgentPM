# Feature Test Plan

Comprehensive CLI feature testing.

## Setup
```bash
cd C:\Projects\AgentPM
pip install -e .
# Use a fresh test database (PowerShell)
$env:AGENTPM_DB = "test_manual.db"
# Or for cmd.exe: set AGENTPM_DB=test_manual.db
```

---

## 1. Company Management

### 1.1 Create Company
```bash
apm company create "Acme Corp" -d "Test company"
```
**Expected**: Company created with ID, name, description shown

### 1.2 List Companies
```bash
apm company list
```
**Expected**: Table showing Acme Corp
<!--
K: The date is not showing in local date.
It is showing in UTC
-->

### 1.3 Show Company
```bash
apm company show <company_id>
```
**Expected**: Company details with project count (0)

### 1.4 JSON Output
```bash
apm --json company list
```
**Expected**: Valid JSON array
<!--
K: JSON is showing fine, but all dates are in UTC, 
not in local time.
-->
---

## 2. Project Management

### 2.1 Create Project (Classic Agile)
```bash
apm project create <company_id> "Web Redesign"
```
**Expected**: Project created with methodology "classic_agile"

### 2.2 Create Project (Spec-Driven)
```bash
apm project create <company_id> "Mobile App" -m spec_driven
```
**Expected**: Project created with methodology "spec_driven"

### 2.3 List Projects
```bash
apm project list
```
**Expected**: Both projects listed

### 2.4 Show Project
```bash
apm project show <project_id>
```
**Expected**: Project details with stats (0 nodes)

### 2.5 Update Project
```bash
apm project update <project_id> --status on_hold
```
**Expected**: Status updated to on_hold

---

## 3. Milestone Management

### 3.1 Create Milestone
```bash
apm milestone create <project_id> "Sprint 1" --target 2025-03-01
```
**Expected**: Milestone created with target date
<!--
K: The system took same milestone name with same target date without
flagging any error. This can be confusing. We should not allow user
to create a milestone that is already exist.
-->
### 3.2 List Milestones
```bash
apm milestone list <project_id>
```
**Expected**: Sprint 1 shown

### 3.3 Complete Milestone
```bash
apm milestone complete <milestone_id>
```
**Expected**: Status changed to "completed"

---

## 4. Story & Task (Classic Agile)

Use the "Web Redesign" project (classic_agile).

### 4.1 Create Story
```bash
apm story create <project_id> "User Login"
```
**Expected**: Story created with status "backlog"

### 4.2 Create Tasks
```bash
apm task create <story_id> "Design login form"
apm task create <story_id> "Implement backend"
```
**Expected**: Tasks created, linked to story

### 4.3 List Stories
```bash
apm story list --project <project_id>
```
**Expected**: "User Login" shown

### 4.4 Show Story with Tasks
```bash
apm story show <story_id>
```
**Expected**: Story details + child tasks listed

### 4.5 Start Task
```bash
apm task start <task_id>
```
**Expected**: Status → in_progress, timer started

### 4.6 Complete Task
```bash
apm task done <task_id>
```
**Expected**: Status → done, timer stopped, duration shown

### 4.7 Block Task
```bash
apm task block <task2_id> "Waiting for API docs"
```
**Expected**: Status → blocked, reason shown

---

## 5. Spec-Driven Workflow

Use the "Mobile App" project (spec_driven).

### 5.1 Create Spec
```bash
apm node create <project_id> spec "Authentication Spec"
```
**Expected**: Status "draft"

### 5.2 Approve Spec
```bash
apm node update <spec_id> --status approved
```
**Expected**: Status → approved

### 5.3 Create Design
```bash
apm node create <spec_id> design "Auth Design Doc"
```
**Expected**: Status "draft", Parent shown as the spec

### 5.4 Design Review Flow
```bash
apm node update <design_id> --status in_review
apm node update <design_id> --status approved
```
**Expected**: Status transitions correctly

### 5.5 Create Implementation
```bash
apm node create <design_id> implementation "Implement Auth"
```
**Expected**: Status "todo", Parent shown as the design

### 5.6 Implementation Workflow
```bash
apm node start <impl_id>
apm node update <impl_id> --status in_review
apm node done <impl_id>
```
**Expected**: todo → in_progress → in_review → done

### 5.7 Create Validation
```bash
apm node create <impl_id> validation "Auth Tests"
```
**Expected**: Status "pending", Parent shown as the implementation

### 5.8 Validation Pass/Fail
```bash
apm node start <validation_id>
apm node update <validation_id> --status failed
apm node update <validation_id> --status pending
apm node start <validation_id>
apm node update <validation_id> --status passed
```
**Expected**: Can fail and retry, ends in "passed"

---

## 6. Time Tracking

### 6.1 Start Timer
```bash
apm timer start <task_id>
```
**Expected**: Timer started message

### 6.2 Check Status
```bash
apm timer status
```
**Expected**: Shows active timer with node info

### 6.3 Stop Timer
```bash
apm timer stop
```
**Expected**: Timer stopped, duration shown

### 6.4 Log Manual Time
```bash
apm timer log <task_id> 45 --notes "Code review"
```
**Expected**: 45 minutes logged

---

## 7. Tags

### 7.1 Create Tag
```bash
apm tag create "bug" --color red
apm tag create "urgent"
```
**Expected**: Tags created

### 7.2 List Tags
```bash
apm tag list
```
**Expected**: Both tags shown

### 7.3 Tag Node
```bash
apm tag add <task_id> bug
apm tag add <task_id> urgent
```
**Expected**: Tags added to node

### 7.4 Remove Tag
```bash
apm tag remove <task_id> urgent
```
**Expected**: Tag removed

---

## 8. Search & Reporting

### 8.1 Search
```bash
apm search "Login"
```
**Expected**: Finds "User Login" story and related items

### 8.2 Dashboard
```bash
apm dashboard
```
**Expected**: Shows active timer (if any), in-progress items, blockers

### 8.3 Stats
```bash
apm stats <project_id>
```
**Expected**: Project statistics displayed

### 8.4 Activity
```bash
apm activity --limit 10
```
**Expected**: Recent activity log

---

## 9. Backup & Export

### 9.1 Create Backup
```bash
apm backup create
```
**Expected**: Backup file created in ~/.agentpm/backups/

### 9.2 List Backups
```bash
apm backup list
```
**Expected**: Backup listed with size and date

### 9.3 Export All
```bash
apm export json -o full_export.json
```
**Expected**: JSON file with all data

### 9.4 Export Project
```bash
apm export json --project <project_id> -o project_export.json
```
**Expected**: JSON file with single project data

---

## Feature Test Checklist

### Company & Project
- [ ] Create/list/show company
- [ ] Create project with both methodologies
- [ ] Update project status

### Work Items
- [ ] Create story and tasks (classic_agile)
- [ ] Task start/done/block workflow
- [ ] Spec-driven full workflow (spec → design → impl → validation)
- [ ] Status transitions work correctly

### Time Tracking
- [ ] Timer start/stop
- [ ] Manual time logging
- [ ] Timer status shows correctly

### Tags
- [ ] Create tags
- [ ] Add/remove tags from nodes

### Reporting
- [ ] Search finds items
- [ ] Dashboard displays correctly
- [ ] Stats show project metrics
- [ ] Activity log works

### Backup & Export
- [ ] Backup creates file
- [ ] Export generates valid JSON
