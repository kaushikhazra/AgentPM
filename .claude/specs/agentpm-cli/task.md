# AgentPM CLI - Tasks

## Framework Setup
- [ ] Add typer and rich to dependencies in pyproject.toml
  _CLI-1: CLI Framework_
- [ ] Create cli/main.py with Typer app and global options
  _CLI-1: CLI Framework_
- [ ] Create cli/formatting.py with Rich helpers
  _CLI-1: CLI Framework_
  - [ ] create_table() generic helper
  - [ ] get_status_style()
  - [ ] format_duration()
- [ ] Add entry point in pyproject.toml
  _CLI-1: CLI Framework_
- [ ] Create error handling decorator
  _CLI-1: CLI Framework_

## Company Commands
- [ ] Create cli/company.py
  _CLI-2: Company Commands_
  - [ ] list command
  - [ ] create command
  - [ ] show command
  - [ ] delete command with confirmation
- [ ] Write CLI tests for company commands
  _CLI-2: Company Commands_

## Project Commands
- [ ] Create cli/project.py
  _CLI-3: Project Commands_
  - [ ] list command with filters
  - [ ] create command with --methodology
  - [ ] show command with stats
  - [ ] update command
  - [ ] delete command with confirmation
- [ ] Write CLI tests for project commands
  _CLI-3: Project Commands_

## Milestone Commands
- [ ] Create cli/milestone.py
  _CLI-4: Milestone Commands_
  - [ ] list command
  - [ ] create command with --target
  - [ ] show command with progress
  - [ ] complete command
- [ ] Write CLI tests for milestone commands
  _CLI-4: Milestone Commands_

## Node Commands
- [ ] Create cli/node.py
  _CLI-5: Node Commands_
  - [ ] list command with filters
  - [ ] create command
  - [ ] show command with edges/time
  - [ ] update command
  - [ ] start command (workflow)
  - [ ] done command (workflow)
  - [ ] block command
  - [ ] delete command
- [ ] Write CLI tests for node commands
  _CLI-5: Node Commands_

## Story/Task Shortcuts
- [ ] Create cli/story.py
  _CLI-6: Story/Task Shortcuts_
  - [ ] list command
  - [ ] create command
  - [ ] show command with tasks
- [ ] Create cli/task.py
  _CLI-6: Story/Task Shortcuts_
  - [ ] list command
  - [ ] create command (auto parent edge)
  - [ ] start/done/block shortcuts
- [ ] Write CLI tests for shortcuts
  _CLI-6: Story/Task Shortcuts_

## Timer Commands
- [ ] Create cli/timer.py
  _CLI-7: Timer Commands_
  - [ ] start command
  - [ ] stop command
  - [ ] status command
- [ ] Add `apm time log` command
  _CLI-7: Timer Commands_
- [ ] Write CLI tests for timer commands
  _CLI-7: Timer Commands_

## Dashboard Command
- [ ] Create cli/dashboard.py
  _CLI-8: Dashboard Command_
  - [ ] dashboard command
  - [ ] create_dashboard_panel() in formatting.py
- [ ] Write CLI tests for dashboard
  _CLI-8: Dashboard Command_

## Stats Command
- [ ] Create cli/stats.py
  _CLI-9: Stats Command_
  - [ ] stats command
  - [ ] Format stats with tables/panels
- [ ] Write CLI tests for stats
  _CLI-9: Stats Command_

## Search Command
- [ ] Create cli/search.py
  _CLI-10: Search Command_
  - [ ] search command
  - [ ] --type and --project filters
  - [ ] Format results with context
- [ ] Write CLI tests for search
  _CLI-10: Search Command_

## Activity Command
- [ ] Create cli/activity.py
  _CLI-11: Activity Command_
  - [ ] activity command
  - [ ] --limit and --entity filters
  - [ ] Timeline formatting
- [ ] Write CLI tests for activity
  _CLI-11: Activity Command_

## Tag Commands
- [ ] Create cli/tag.py
  _CLI-12: Tag Commands_
  - [ ] list command
  - [ ] create command with --color
  - [ ] add command
  - [ ] remove command
- [ ] Write CLI tests for tag commands
  _CLI-12: Tag Commands_

## JSON Output
- [ ] Implement --json flag handling in all list/show commands
  _CLI-13: JSON Output_
- [ ] Test JSON output schema consistency
  _CLI-13: JSON Output_

## Integration Tests
- [ ] Test full workflow via CLI: create company → project → story → task → start → done
  _CLI-6: Story/Task Shortcuts_
- [ ] Test dashboard shows correct state
  _CLI-8: Dashboard Command_
- [ ] Test timer start/stop via CLI
  _CLI-7: Timer Commands_
