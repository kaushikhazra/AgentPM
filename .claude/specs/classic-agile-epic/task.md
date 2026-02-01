# Epic Support - Tasks

## Implementation Tasks

- [x] Add epic node type to ClassicAgileMethodology
  - Add NodeTypeDefinition for epic with draft/ready/in_progress/done/cancelled statuses
  - Set can_track_time=False (use rollup)
  - Set can_have_assignee=True
  _EPIC-CREATE, EPIC-WORKFLOW_

- [x] Update parent edge type to support story → epic
  - Add "story" to source_types
  - Add "epic" to target_types
  _EPIC-HIERARCHY_

- [x] Update depends_on edge type to include epic
  - Add "epic" to source_types
  - Add "epic" to target_types
  _EPIC-HIERARCHY_

- [x] Add get_epic_type() helper method
  - Return "epic" string
  _EPIC-MCP_

- [x] Update docstring to reflect new hierarchy
  - Epic → Story → Task
  _EPIC-CREATE_

## Testing Tasks

- [x] Test epic node creation with valid statuses
  _EPIC-CREATE_

- [x] Test epic status transitions
  _EPIC-WORKFLOW_

- [x] Test story can have epic as parent
  _EPIC-HIERARCHY_

- [x] Test task cannot have epic as direct parent (must go through story)
  _EPIC-HIERARCHY_

- [x] Test epic in depends_on relationships
  _EPIC-HIERARCHY_

- [x] Test get_epic_type() returns "epic"
  _EPIC-MCP_
