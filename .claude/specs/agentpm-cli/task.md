# AgentPM CLI - Tasks

## Framework Setup
- [x] Add typer and rich to dependencies in pyproject.toml
  _CLI-1: CLI Framework_
- [x] Create cli/main.py with Typer app and global options
  _CLI-1: CLI Framework_
- [x] Create cli/formatting.py with Rich helpers
  _CLI-1: CLI Framework_
  - [x] create_table() generic helper
  - [x] get_status_style()
  - [x] format_duration()
- [x] Add entry point in pyproject.toml
  _CLI-1: CLI Framework_
- [x] Create error handling decorator
  _CLI-1: CLI Framework_

## Company Commands
- [x] Create cli/company.py
  _CLI-2: Company Commands_
  - [x] list command
  - [x] create command
  - [x] show command
  - [x] delete command with confirmation
- [x] Write CLI tests for company commands
  _CLI-2: Company Commands_

## Project Commands
- [x] Create cli/project.py
  _CLI-3: Project Commands_
  - [x] list command with filters
  - [x] create command with --methodology
  - [x] show command with stats
  - [x] update command
  - [x] delete command with confirmation
- [x] Write CLI tests for project commands
  _CLI-3: Project Commands_

## Milestone Commands
- [x] Create cli/milestone.py
  _CLI-4: Milestone Commands_
  - [x] list command
  - [x] create command with --target
  - [x] show command with progress
  - [x] complete command
- [x] Write CLI tests for milestone commands
  _CLI-4: Milestone Commands_

## Node Commands
- [x] Create cli/node.py
  _CLI-5: Node Commands_
  - [x] list command with filters
  - [x] create command
  - [x] show command with edges/time
  - [x] update command
  - [x] start command (workflow)
  - [x] done command (workflow)
  - [x] block command
  - [x] delete command
- [x] Write CLI tests for node commands
  _CLI-5: Node Commands_

## Story/Task Shortcuts
- [x] Create cli/story.py
  _CLI-6: Story/Task Shortcuts_
  - [x] list command
  - [x] create command
  - [x] show command with tasks
- [x] Create cli/task.py
  _CLI-6: Story/Task Shortcuts_
  - [x] list command
  - [x] create command (auto parent edge)
  - [x] start/done/block shortcuts
- [x] Write CLI tests for shortcuts
  _CLI-6: Story/Task Shortcuts_

## Timer Commands
- [x] Create cli/timer.py
  _CLI-7: Timer Commands_
  - [x] start command
  - [x] stop command
  - [x] status command
- [x] Add `apm time log` command
  _CLI-7: Timer Commands_
- [x] Write CLI tests for timer commands
  _CLI-7: Timer Commands_

## Dashboard Command
- [x] Create cli/dashboard.py
  _CLI-8: Dashboard Command_
  - [x] dashboard command
  - [x] create_dashboard_panel() in formatting.py
- [x] Write CLI tests for dashboard
  _CLI-8: Dashboard Command_

## Stats Command
- [x] Create cli/stats.py
  _CLI-9: Stats Command_
  - [x] stats command
  - [x] Format stats with tables/panels
- [x] Write CLI tests for stats
  _CLI-9: Stats Command_

## Search Command
- [x] Create cli/search.py
  _CLI-10: Search Command_
  - [x] search command
  - [x] --type and --project filters
  - [x] Format results with context
- [x] Write CLI tests for search
  _CLI-10: Search Command_

## Activity Command
- [x] Create cli/activity.py
  _CLI-11: Activity Command_
  - [x] activity command
  - [x] --limit and --entity filters
  - [x] Timeline formatting
- [x] Write CLI tests for activity
  _CLI-11: Activity Command_

## Tag Commands
- [x] Create cli/tag.py
  _CLI-12: Tag Commands_
  - [x] list command
  - [x] create command with --color
  - [x] add command
  - [x] remove command
- [x] Write CLI tests for tag commands
  _CLI-12: Tag Commands_

## JSON Output
- [x] Implement --json flag handling in all list/show commands
  _CLI-13: JSON Output_
- [x] Test JSON output schema consistency
  _CLI-13: JSON Output_

## Integration Tests
- [x] Test full workflow via CLI: create company → project → story → task → start → done
  _CLI-6: Story/Task Shortcuts_
- [x] Test dashboard shows correct state
  _CLI-8: Dashboard Command_
- [x] Test timer start/stop via CLI
  _CLI-7: Timer Commands_
