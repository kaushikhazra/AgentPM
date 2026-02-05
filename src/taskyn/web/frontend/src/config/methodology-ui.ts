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
 */
export const METHODOLOGY_HIERARCHY: Record<string, Record<string, string>> = {
  classic_agile: {
    epic: 'story',    // Epic's child is Story
    story: 'task',    // Story's child is Task
    // task and bug are leaf nodes - they cannot have children per edge validation
  },
  spec_driven: {
    spec: 'design',           // Spec's child is Design
    design: 'implementation', // Design's child is Implementation
    // implementation and validation are leaf nodes
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
      design: {
        displayName: 'Design',
        plural: 'Designs',
        icon: 'D',
        color: 'var(--accent-peach)',
      },
      implementation: {
        displayName: 'Implementation',
        plural: 'Implementations',
        icon: 'I',
        color: 'var(--accent-sky)',
      },
      validation: {
        displayName: 'Validation',
        plural: 'Validations',
        icon: 'V',
        color: 'var(--accent-mint)',
      },
    },
    statusLabels: {
      draft: 'Draft',
      in_progress: 'In Progress',
      review: 'Review',
      approved: 'Approved',
      rejected: 'Rejected',
      blocked: 'Blocked',
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

/** Get the appropriate child type for a parent node type.
 * Returns null if the parent node type cannot have children.
 */
export function getChildType(methodology: string, parentNodeType: string): string | null {
  return METHODOLOGY_HIERARCHY[methodology]?.[parentNodeType] ?? null;
}

/** Check if a node type can have children. */
export function canHaveChildren(methodology: string, nodeType: string): boolean {
  return METHODOLOGY_HIERARCHY[methodology]?.[nodeType] !== undefined;
}
