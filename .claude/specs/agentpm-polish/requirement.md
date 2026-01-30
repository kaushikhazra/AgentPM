# AgentPM Polish & Additional Methodologies - Requirements

## Overview
Polish the system for production use, add comprehensive error handling, improve documentation, and implement additional methodologies beyond Classic Agile.

## Dependencies
- Requires: agentpm-foundation, agentpm-graph, agentpm-core, agentpm-cli, agentpm-mcp

## User Stories

### US-1: Spec-Driven Methodology
As a user following Kiro-style spec-driven development, I want a methodology that models the spec → design → implementation → validation flow.

**Acceptance Criteria:**
- Node types: spec, design, implementation, validation
- Gated workflow: each phase requires approval before next
- Validation can fail and loop back to implementation
- Proper state machine with approval transitions
- Works with both CLI and MCP

### US-2: Error Messages
As a user, I want clear, helpful error messages so that I can understand and fix issues quickly.

**Acceptance Criteria:**
- All errors include context (what entity, what operation)
- Validation errors list all issues, not just the first
- Suggestions for common mistakes
- No stack traces in user-facing output (unless --verbose)

### US-3: CLI Help Text
As a user, I want comprehensive help text so that I can learn the CLI.

**Acceptance Criteria:**
- All commands have descriptive help
- Examples in help text for complex commands
- Global help shows command overview
- `apm --help` is informative for new users

### US-4: README Documentation
As a user, I want clear documentation so that I can set up and use AgentPM.

**Acceptance Criteria:**
- Installation instructions (pip install)
- Quick start guide
- CLI command reference
- MCP setup for Claude Desktop
- MCP setup for Claude Code
- Example workflows

### US-5: Database Backup
As a user, I want to back up my database so that I don't lose data.

**Acceptance Criteria:**
- `apm backup` command creates timestamped backup
- `apm backup --output <path>` for custom location
- Backup is a simple file copy (SQLite is single file)
- List existing backups

### US-6: Data Export
As a user, I want to export my data so that I can use it elsewhere.

**Acceptance Criteria:**
- `apm export` exports all data as JSON
- `apm export --project <id>` exports single project
- Export includes all related data (nodes, edges, time entries)
- Human-readable format

### US-7: Performance Testing
As a developer, I want performance tests so that I know the system handles realistic loads.

**Acceptance Criteria:**
- Test with 100+ projects
- Test with 1000+ nodes
- Test with 10000+ time entries
- Dashboard query < 100ms
- Search query < 200ms

### US-8: Methodology Extensibility
As a developer, I want clear patterns for adding new methodologies.

**Acceptance Criteria:**
- Documentation on creating new methodology
- Example methodology template
- Test helpers for methodology validation
- Registration process documented

### US-9: BMAD Methodology (Optional)
As a user following agent-centric development, I want a BMAD methodology.

**Acceptance Criteria:**
- Node types: orchestrator, agent, artifact
- Edge types: delegates, produces
- Agents are trackable entities with time logging
- Supports parallel agent work patterns

### US-10: PIV Loop Methodology (Optional)
As a user following iterative cycles, I want a PIV Loop methodology.

**Acceptance Criteria:**
- Node types: plan, implement, validate
- Cyclical workflow support
- Iteration tracking (PIV cycle count)
- Validate can loop back to plan or implement
