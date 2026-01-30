# AgentPM CLI - Requirements

## Overview
Implement a command-line interface using Typer and Rich for interacting with AgentPM. The CLI is the secondary interface (after MCP) for quick interactions and scripting.

## Dependencies
- Requires: agentpm-foundation, agentpm-graph, agentpm-core

## User Stories

### CLI-1: CLI Framework
As a user, I want a well-structured CLI so that commands are intuitive and discoverable.

**Acceptance Criteria:**
- Main command `apm` with subcommands
- Global options: --db, --json, --verbose
- All commands have --help with examples
- Tab completion support (via Typer)
- Consistent error messages

### CLI-2: Company Commands
As a user, I want CLI commands for company management.

**Acceptance Criteria:**
- `apm company list` - list all companies
- `apm company create <name>` - create company
- `apm company show <id>` - show company details
- `apm company delete <id>` - delete company (with confirmation)

### CLI-3: Project Commands
As a user, I want CLI commands for project management.

**Acceptance Criteria:**
- `apm project list` - list projects with optional filters
- `apm project create <company_id> <name>` - create project
- `apm project show <id>` - show project with stats
- `apm project update <id>` - update project status
- `apm project delete <id>` - delete project (with confirmation)
- `--methodology` flag on create

### CLI-4: Milestone Commands
As a user, I want CLI commands for milestone management.

**Acceptance Criteria:**
- `apm milestone list <project_id>` - list milestones
- `apm milestone create <project_id> <name>` - create milestone
- `apm milestone show <id>` - show milestone with progress
- `apm milestone complete <id>` - mark complete

### CLI-5: Node Commands
As a user, I want CLI commands for working with nodes (stories, tasks, etc.).

**Acceptance Criteria:**
- `apm node list` - list nodes with filters
- `apm node create <project_id> <type> <title>` - create node
- `apm node show <id>` - show node with edges and time
- `apm node update <id>` - update node fields
- `apm node start <id>` - start work (status + timer)
- `apm node done <id>` - complete work
- `apm node block <id> <reason>` - block with reason
- `apm node delete <id>` - delete node

### CLI-6: Story/Task Shortcuts
As a user, I want convenience commands for common node types.

**Acceptance Criteria:**
- `apm story list` - list stories
- `apm story create <project_id> <title>` - create story
- `apm story show <id>` - show story with tasks
- `apm task list` - list tasks
- `apm task create <story_id> <title>` - create task under story
- `apm task start/done/block` - workflow shortcuts

### CLI-7: Timer Commands
As a user, I want CLI commands for time tracking.

**Acceptance Criteria:**
- `apm timer start <node_id>` - start timer
- `apm timer stop` - stop active timer
- `apm timer status` - show active timer
- `apm time log <node_id> <minutes>` - manual entry

### CLI-8: Dashboard Command
As a user, I want a dashboard command for quick status overview.

**Acceptance Criteria:**
- `apm dashboard` - show formatted dashboard
- Active timer with duration
- In-progress items
- Blockers
- Today's time total
- Rich formatting with panels and colors

### CLI-9: Stats Command
As a user, I want a stats command for project analytics.

**Acceptance Criteria:**
- `apm stats <project_id>` - show project statistics
- Node counts by type and status
- Time this week/month
- Velocity metric
- Milestone progress

### CLI-10: Search Command
As a user, I want a search command to find items quickly.

**Acceptance Criteria:**
- `apm search <query>` - search across entities
- `--type` filter for entity type
- `--project` filter for project scope
- Show context snippets in results

### CLI-11: Activity Command
As a user, I want to view recent activity.

**Acceptance Criteria:**
- `apm activity` - show recent activity
- `--limit` to control count
- `--entity` to filter by entity
- Formatted timeline view

### CLI-12: Tag Commands
As a user, I want CLI commands for tag management.

**Acceptance Criteria:**
- `apm tag list` - list all tags
- `apm tag create <name>` - create tag
- `apm tag add <node_id> <tag>` - add tag to node
- `apm tag remove <node_id> <tag>` - remove tag

### CLI-13: JSON Output
As a user, I want JSON output for scripting.

**Acceptance Criteria:**
- `--json` flag on all list/show commands
- Valid JSON output
- Consistent schema across commands
- No Rich formatting in JSON mode
