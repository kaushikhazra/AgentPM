# AgentPM Polish & Additional Methodologies - Tasks

## Spec-Driven Methodology
- [ ] Create methodologies/spec_driven.py
  _POL-1: Spec-Driven Methodology_
  - [ ] Define spec node type with approval workflow
  - [ ] Define design node type with review workflow
  - [ ] Define implementation node type with rework support
  - [ ] Define validation node type with pass/fail
  - [ ] Define gates edge type
  - [ ] Define validates edge type
- [ ] Implement helper methods (get_story_type, etc.)
  _POL-1: Spec-Driven Methodology_
- [ ] Register in methodologies/__init__.py
  _POL-1: Spec-Driven Methodology_
- [ ] Write tests for spec-driven workflow
  _POL-1: Spec-Driven Methodology_
- [ ] Test with CLI and MCP
  _POL-1: Spec-Driven Methodology_

## Error Messages
- [ ] Enhance AgentPMError with context and suggestions
  _POL-2: Error Messages_
- [ ] Update InvalidTransitionError with helpful message
  _POL-2: Error Messages_
- [ ] Update NotFoundError with entity type context
  _POL-2: Error Messages_
- [ ] Update ValidationError to list all issues
  _POL-2: Error Messages_
- [ ] Review all error raises for helpful messages
  _POL-2: Error Messages_
- [ ] Test error messages are user-friendly
  _POL-2: Error Messages_

## CLI Help Text
- [ ] Add examples to all command help text
  _POL-3: CLI Help Text_
- [ ] Improve --help output for main command
  _POL-3: CLI Help Text_
- [ ] Add epilog with common workflows
  _POL-3: CLI Help Text_
- [ ] Review help text for clarity
  _POL-3: CLI Help Text_

## README Documentation
- [ ] Write installation section
  _POL-4: README Documentation_
- [ ] Write quick start guide
  _POL-4: README Documentation_
- [ ] Document CLI commands with examples
  _POL-4: README Documentation_
- [ ] Document MCP setup for Claude Desktop
  _POL-4: README Documentation_
- [ ] Document MCP setup for Claude Code
  _POL-4: README Documentation_
- [ ] Add example workflows section
  _POL-4: README Documentation_
- [ ] Add methodology comparison section
  _POL-4: README Documentation_

## Database Backup
- [ ] Create cli/backup.py
  _POL-5: Database Backup_
  - [ ] backup command with --output option
  - [ ] list command to show backups
  - [ ] Default backup location (~/.agentpm/backups/)
- [ ] Register backup commands in main.py
  _POL-5: Database Backup_
- [ ] Write tests for backup functionality
  _POL-5: Database Backup_

## Data Export
- [ ] Create cli/export.py
  _POL-6: Data Export_
  - [ ] export command with --output option
  - [ ] --project filter for single project
  - [ ] Include all related data
  - [ ] JSON format with version info
- [ ] Register export command in main.py
  _POL-6: Data Export_
- [ ] Write tests for export functionality
  _POL-6: Data Export_

## Performance Testing
- [ ] Create tests/test_performance.py
  _POL-7: Performance Testing_
  - [ ] large_dataset fixture (100 projects, 6000 nodes)
  - [ ] test_dashboard_performance (<100ms)
  - [ ] test_search_performance (<200ms)
  - [ ] test_list_nodes_performance
  - [ ] test_rollup_performance
- [ ] Add indexes if performance tests fail
  _POL-7: Performance Testing_
- [ ] Document performance characteristics
  _POL-7: Performance Testing_

## Methodology Documentation
- [ ] Create methodologies/_template.py with full example
  _POL-8: Methodology Extensibility_
- [ ] Document methodology creation process
  _POL-8: Methodology Extensibility_
- [ ] Create test helpers for methodology validation
  _POL-8: Methodology Extensibility_
- [ ] Add methodology section to README
  _POL-8: Methodology Extensibility_

## BMAD Methodology (Optional)
- [ ] Create methodologies/bmad.py
  _POL-9: BMAD Methodology_
  - [ ] Define orchestrator node type
  - [ ] Define agent node type
  - [ ] Define artifact node type
  - [ ] Define delegates edge type
  - [ ] Define produces edge type
- [ ] Register in methodologies/__init__.py
  _POL-9: BMAD Methodology_
- [ ] Write tests for BMAD workflow
  _POL-9: BMAD Methodology_

## PIV Loop Methodology (Optional)
- [ ] Create methodologies/piv_loop.py
  _POL-10: PIV Loop Methodology_
  - [ ] Define plan node type
  - [ ] Define implement node type
  - [ ] Define validate node type
  - [ ] Define iterates edge type (allows cycles)
  - [ ] Track iteration count in properties
- [ ] Register in methodologies/__init__.py
  _POL-10: PIV Loop Methodology_
- [ ] Write tests for PIV Loop workflow
  _POL-10: PIV Loop Methodology_

## Final Review
- [ ] Run full test suite
  _POL-2: Error Messages_
- [ ] Manual testing of CLI workflows
  _POL-3: CLI Help Text_
- [ ] Manual testing with Claude Code via MCP
  _POL-1: Spec-Driven Methodology_
- [ ] Code review for consistency
  _POL-2: Error Messages_
- [ ] Update CLAUDE.md with final architecture
  _POL-4: README Documentation_
