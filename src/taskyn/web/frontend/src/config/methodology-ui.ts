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
