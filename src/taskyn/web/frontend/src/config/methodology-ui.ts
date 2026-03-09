/* Methodology UI configuration — maps methodology node types to display metadata. */

export interface NodeTypeUI {
  displayName: string;
  plural: string;
  icon: string; // emoji or icon name
  color: string; // CSS variable name
}

export interface MethodologyUI {
  displayName: string;
  nodeTypes: Record<string, NodeTypeUI>;
  statusLabels: Record<string, string>;
}

/** Defines the parent → child hierarchy for each methodology.
 * Only node types that can be parents are listed.
 * If a node type is not listed, it cannot have children (leaf node).
 * Values can be a single string or an array of strings for parents with multiple child types.
 */
export const METHODOLOGY_HIERARCHY: Record<string, Record<string, string | string[]>> = {
  classic_agile: {
    epic: 'story',    // Epic's child is Story
    story: 'task',    // Story's child is Task
    // task and bug are leaf nodes - they cannot have children per edge validation
  },
  spec_driven: {
    spec: ['requirement', 'design', 'task'],  // Spec can have Requirement, Design, or Task children
    requirement: 'todo',                       // Requirement's child is Todo
    design: 'todo',                            // Design's child is Todo
    task: 'todo',                              // Task's child is Todo
    // todo is a leaf node
  },
  learning: {
    subject: 'topic',    // Subject's child is Topic
    topic: 'activity',   // Topic's child is Activity
    // activity is a leaf node
  },
};

export const METHODOLOGY_UI: Record<string, MethodologyUI> = {
  classic_agile: {
    displayName: 'Classic Agile',
    nodeTypes: {
      epic: {
        displayName: 'Epic',
        plural: 'Epics',
        icon: 'E',
        color: 'var(--accent-lavender)',
      },
      story: {
        displayName: 'Story',
        plural: 'Stories',
        icon: 'S',
        color: 'var(--accent-sky)',
      },
      task: {
        displayName: 'Task',
        plural: 'Tasks',
        icon: 'T',
        color: 'var(--accent-mint)',
      },
      bug: {
        displayName: 'Bug',
        plural: 'Bugs',
        icon: 'B',
        color: 'var(--accent-blush)',
      },
    },
    statusLabels: {
      backlog: 'Backlog',
      ready: 'Ready',
      in_progress: 'In Progress',
      in_review: 'In Review',
      done: 'Done',
      blocked: 'Blocked',
      cancelled: 'Cancelled',
    },
  },
  spec_driven: {
    displayName: 'Spec Driven',
    nodeTypes: {
      spec: {
        displayName: 'Spec',
        plural: 'Specs',
        icon: 'SP',
        color: 'var(--accent-lavender)',
      },
      requirement: {
        displayName: 'Requirement',
        plural: 'Requirements',
        icon: 'R',
        color: 'var(--accent-peach)',
      },
      design: {
        displayName: 'Design',
        plural: 'Designs',
        icon: 'D',
        color: 'var(--accent-sky)',
      },
      task: {
        displayName: 'Task',
        plural: 'Tasks',
        icon: 'T',
        color: 'var(--accent-mint)',
      },
      todo: {
        displayName: 'Todo',
        plural: 'Todos',
        icon: 'TD',
        color: 'var(--accent-blush)',
      },
    },
    statusLabels: {
      draft: 'Draft',
      active: 'Active',
      todo: 'To Do',
      in_progress: 'In Progress',
      done: 'Done',
      cancelled: 'Cancelled',
    },
  },
  learning: {
    displayName: 'Learning',
    nodeTypes: {
      subject: {
        displayName: 'Subject',
        plural: 'Subjects',
        icon: 'SB',
        color: 'var(--accent-lavender)',
      },
      topic: {
        displayName: 'Topic',
        plural: 'Topics',
        icon: 'TP',
        color: 'var(--accent-sky)',
      },
      activity: {
        displayName: 'Activity',
        plural: 'Activities',
        icon: 'A',
        color: 'var(--accent-mint)',
      },
    },
    statusLabels: {
      planned: 'Planned',
      active: 'Active',
      researching: 'Researching',
      practicing: 'Practicing',
      documenting: 'Documenting',
      completed: 'Completed',
      archived: 'Archived',
      todo: 'To Do',
      in_progress: 'In Progress',
      done: 'Done',
      cancelled: 'Cancelled',
    },
  },
};

/** Get UI config for a node type within a methodology. */
export function getNodeTypeUI(
  methodology: string,
  nodeType: string,
): NodeTypeUI {
  return (
    METHODOLOGY_UI[methodology]?.nodeTypes[nodeType] ?? {
      displayName: nodeType,
      plural: `${nodeType}s`,
      icon: nodeType[0]?.toUpperCase() ?? '?',
      color: 'var(--text-secondary)',
    }
  );
}

/** Get human-readable status label. */
export function getStatusLabel(methodology: string, status: string): string {
  return METHODOLOGY_UI[methodology]?.statusLabels[status] ?? status;
}

/** Get all valid child types for a parent node type.
 * Returns an empty array if the parent node type cannot have children.
 */
export function getChildTypes(methodology: string, parentNodeType: string): string[] {
  const entry = METHODOLOGY_HIERARCHY[methodology]?.[parentNodeType];
  if (!entry) return [];
  return Array.isArray(entry) ? entry : [entry];
}

/** Get the primary child type for a parent node type.
 * Returns null if the parent node type cannot have children.
 * When multiple child types exist, returns the first one.
 */
export function getChildType(methodology: string, parentNodeType: string): string | null {
  const types = getChildTypes(methodology, parentNodeType);
  return types[0] ?? null;
}

/** Check if a node type can have children. */
export function canHaveChildren(methodology: string, nodeType: string): boolean {
  return METHODOLOGY_HIERARCHY[methodology]?.[nodeType] !== undefined;
}
