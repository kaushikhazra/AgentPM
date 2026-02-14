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
    spec: 'requirement',              // Spec's child is Requirement
    requirement: 'design',            // Requirement's child is Design
    design: 'implementation',         // Design's child is Implementation
    implementation: 'task',           // Implementation's child is Task
    // task and verification nodes are leaf nodes
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
      implementation: {
        displayName: 'Implementation',
        plural: 'Implementations',
        icon: 'I',
        color: 'var(--accent-mint)',
      },
      task: {
        displayName: 'Task',
        plural: 'Tasks',
        icon: 'T',
        color: 'var(--accent-blush)',
      },
      e2e_verification: {
        displayName: 'E2E Verification',
        plural: 'E2E Verifications',
        icon: 'EV',
        color: 'var(--accent-mint)',
      },
      functional_verification: {
        displayName: 'Functional Verification',
        plural: 'Functional Verifications',
        icon: 'FV',
        color: 'var(--accent-mint)',
      },
      unit_verification: {
        displayName: 'Unit Verification',
        plural: 'Unit Verifications',
        icon: 'UV',
        color: 'var(--accent-mint)',
      },
    },
    statusLabels: {
      draft: 'Draft',
      approved: 'Approved',
      in_progress: 'In Progress',
      done: 'Done',
      cancelled: 'Cancelled',
      rework: 'Rework',
      in_review: 'In Review',
      rejected: 'Rejected',
      todo: 'To Do',
      pending: 'Pending',
      passed: 'Passed',
      failed: 'Failed',
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
