import { TaskItem } from '@/components/molecules/TaskItem';
import type { Node } from '@/types';

interface TaskListProps {
  nodes: Node[];
  onCheck?: (nodeId: string, checked: boolean) => void;
  onClick?: (nodeId: string) => void;
  emptyText?: string;
}

function getPriority(node: Node): 'high' | 'medium' | 'low' | undefined {
  const p = node.priority;
  if (p === 'high' || p === 'urgent') return 'high';
  if (p === 'medium' || p === 'normal') return 'medium';
  if (p === 'low') return 'low';
  return undefined;
}

export function TaskList({ nodes, onCheck, onClick, emptyText = 'No tasks' }: TaskListProps) {
  if (nodes.length === 0) {
    return (
      <div className="empty-state">
        <p className="empty-state-desc">{emptyText}</p>
      </div>
    );
  }

  return (
    <>
      {nodes.map((node) => (
        <TaskItem
          key={node.id}
          title={node.title}
          meta={node.project_id ?? ''}
          priority={getPriority(node)}
          checked={node.status === 'done'}
          onCheck={onCheck ? (checked) => onCheck(node.id, checked) : undefined}
          onClick={onClick ? () => onClick(node.id) : undefined}
        />
      ))}
    </>
  );
}
