interface TaskItemProps {
  title: string;
  meta?: string;
  priority?: 'high' | 'medium' | 'low';
  checked?: boolean;
  onCheck?: (checked: boolean) => void;
  onClick?: () => void;
}

export function TaskItem({
  title,
  meta,
  priority,
  checked = false,
  onCheck,
  onClick,
}: TaskItemProps) {
  return (
    <div className="task-item" onClick={onClick}>
      <div
        className={`task-checkbox ${checked ? 'checked' : ''}`}
        onClick={(e) => {
          e.stopPropagation();
          onCheck?.(!checked);
        }}
        role="checkbox"
        aria-checked={checked}
      >
        {checked && (
          <svg viewBox="0 0 24 24">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        )}
      </div>
      <div className="task-content">
        <div className="task-title">{title}</div>
        {meta && <div className="task-meta">{meta}</div>}
      </div>
      {priority && <div className={`task-priority priority-${priority}`} />}
    </div>
  );
}
