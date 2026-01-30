# AgentPM Polish & Additional Methodologies - Tasks

## Spec-Driven Methodology
- [x] Create methodologies/spec_driven.py
  _POL-1: Spec-Driven Methodology_
  - [x] Define spec node type with approval workflow
  - [x] Define design node type with review workflow
  - [x] Define implementation node type with rework support
  - [x] Define validation node type with pass/fail
  - [x] Define gates edge type
  - [x] Define validates edge type
- [x] Implement helper methods (get_story_type, etc.)
  _POL-1: Spec-Driven Methodology_
- [x] Register in methodologies/__init__.py
  _POL-1: Spec-Driven Methodology_
- [x] Write tests for spec-driven workflow
  _POL-1: Spec-Driven Methodology_

## Database Backup
- [x] Create cli/backup.py
  _POL-5: Database Backup_
  - [x] backup create command with --output option
  - [x] backup list command to show backups
  - [x] backup restore command
  - [x] Default backup location (~/.agentpm/backups/)
- [x] Register backup commands in main.py
  _POL-5: Database Backup_

## Data Export
- [x] Create cli/export.py
  _POL-6: Data Export_
  - [x] export json command with --output option
  - [x] --project filter for single project
  - [x] Include all related data
  - [x] JSON format with version info
- [x] Register export command in main.py
  _POL-6: Data Export_

## README Documentation
- [x] Write installation section
  _POL-4: README Documentation_
- [x] Write quick start guide
  _POL-4: README Documentation_
- [x] Document CLI commands with examples
  _POL-4: README Documentation_
- [x] Document MCP setup for Claude Desktop
  _POL-4: README Documentation_
- [x] Document MCP setup for Claude Code
  _POL-4: README Documentation_
- [x] Add methodology comparison section
  _POL-4: README Documentation_

## CLAUDE.md Update
- [x] Update CLAUDE.md with final architecture
  _POL-4: README Documentation_

## Deferred Tasks (Optional)
- [ ] Error message enhancement (POL-2)
- [ ] CLI help text improvements (POL-3)
- [ ] Performance testing (POL-7)
- [ ] Methodology template (POL-8)
- [ ] BMAD Methodology (POL-9)
- [ ] PIV Loop Methodology (POL-10)
