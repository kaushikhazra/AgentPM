import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useProjects } from '@/hooks/queries/useProjects';
import { useNodes } from '@/hooks/queries/useNodes';
import { useOptimisticUpdateNode } from '@/hooks/mutations/useNodeMutations';
import { useTimer } from '@/hooks/useTimer';
import { METHODOLOGY_UI, getStatusLabel } from '@/config/methodology-ui';
import type { Project, Node } from '@/types';

const GRADIENTS = [
  'var(--gradient-primary)',
  'var(--gradient-secondary)',
  'linear-gradient(135deg, var(--accent-mint), var(--accent-sage))',
  'linear-gradient(135deg, var(--accent-peach), var(--accent-blush))',
];

function formatTimerDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

function getDueDateLabel(node: Node): string {
  const created = new Date(node.created_at);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  return 'Next week';
}

export function KanbanPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { activeTimers, elapsedMap } = useTimer();

  const { data: projects = [] } = useProjects();
  const [selectedId, setSelectedId] = useState(projectId ?? '');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [dragNodeId, setDragNodeId] = useState<string | null>(null);
  const [dropTarget, setDropTarget] = useState<string | null>(null);

  const { data: nodes = [] } = useNodes(selectedId ? { project_id: selectedId } : undefined);
  const updateNode = useOptimisticUpdateNode(selectedId);

  // Auto-select first project
  useEffect(() => {
    if (!selectedId && projects.length > 0) {
      setSelectedId(projects[0]!.id);
    }
  }, [selectedId, projects]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as HTMLElement)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, []);

  const selectedProject = projects.find((p: Project) => p.id === selectedId);
  const methodology = selectedProject?.methodology ?? 'classic_agile';
  const methUI = METHODOLOGY_UI[methodology];
  const statuses = methUI ? Object.keys(methUI.statusLabels) : ['backlog', 'ready', 'in_progress', 'done'];

  const statusColors: Record<string, string> = {
    backlog: 'var(--status-backlog)', draft: 'var(--status-backlog)',
    todo: 'var(--status-backlog)',
    ready: 'var(--status-ready)',
    active: 'var(--status-progress)', in_progress: 'var(--status-progress)',
    in_review: 'var(--status-review)', review: 'var(--status-review)',
    done: 'var(--status-done)',
    cancelled: 'var(--status-blocked)', blocked: 'var(--status-blocked)',
  };

  const columns = statuses.map((status) => ({
    status,
    label: getStatusLabel(methodology, status),
    color: statusColors[status] ?? 'var(--text-tertiary)',
    nodes: nodes.filter((n: Node) => n.status === status),
  }));

  const selectProject = (id: string) => {
    setSelectedId(id);
    setDropdownOpen(false);
    navigate(`/kanban/${id}`, { replace: true });
  };

  const handleDragStart = (nodeId: string) => setDragNodeId(nodeId);
  const handleDragOver = (e: React.DragEvent, status: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDropTarget(status);
  };
  const handleDragLeave = () => setDropTarget(null);
  const handleDragEnd = () => { setDragNodeId(null); setDropTarget(null); };

  const handleDrop = async (e: React.DragEvent, targetStatus: string) => {
    e.preventDefault();
    setDropTarget(null);
    if (!dragNodeId) return;
    const node = nodes.find((n: Node) => n.id === dragNodeId);
    if (!node || node.status === targetStatus) { setDragNodeId(null); return; }
    setDragNodeId(null);
    updateNode.mutate({ id: dragNodeId, data: { status: targetStatus } });
  };

  const getTrackingTimers = (nodeId: string) => activeTimers.filter((t) => t.node_id === nodeId);
  const isNodeTracking = (nodeId: string): boolean => getTrackingTimers(nodeId).length > 0;
  const getPriorityClass = (priority: string | null): string => {
    if (priority === 'high') return 'priority-high';
    if (priority === 'low') return 'priority-low';
    return 'priority-medium';
  };

  return (
    <div className="content-wrapper--wide">
      <div className="page-header">
        <div>
          <h1 className="page-title">Kanban Board</h1>
          <div className="subtitle-with-filter">
            <span>for</span>
            <div className={`filter-badge${dropdownOpen ? ' open' : ''}`} ref={dropdownRef} onClick={() => setDropdownOpen(!dropdownOpen)}>
              <div className="filter-badge-icon-box" style={{ background: GRADIENTS[projects.indexOf(selectedProject!) % GRADIENTS.length] ?? GRADIENTS[0] }}>
                {selectedProject?.name.charAt(0).toUpperCase() ?? '?'}
              </div>
              <span className="filter-badge-text">{selectedProject?.name ?? 'Select project'}</span>
              <svg className="filter-badge-arrow" viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9" /></svg>
              <div className="filter-dropdown">
                {projects.map((p: Project, i: number) => (
                  <div key={p.id} className={`filter-dropdown-item${p.id === selectedId ? ' selected' : ''}`} onClick={(e) => { e.stopPropagation(); selectProject(p.id); }}>
                    <div className="filter-dropdown-icon" style={{ background: GRADIENTS[i % GRADIENTS.length] }}>{p.name.charAt(0).toUpperCase()}</div>
                    <span className="filter-dropdown-label">{p.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="kanban-board">
        {columns.map((col) => (
          <div key={col.status} className={`kanban-column${dropTarget === col.status ? ' drag-over' : ''}`}
            onDragOver={(e) => handleDragOver(e, col.status)} onDragLeave={handleDragLeave} onDrop={(e) => handleDrop(e, col.status)}>
            <div className="kanban-column-header">
              <div className="kanban-column-title"><span style={{ color: col.color }}>●</span>{col.label}</div>
              <span className="kanban-column-count">{col.nodes.length}</span>
            </div>
            <div className="kanban-column-content">
              {col.nodes.map((node: Node) => {
                const isTracking = isNodeTracking(node.id);
                return (
                  <div key={node.id}
                    className={`kanban-card${col.status === 'done' ? ' done-card' : ''}${dragNodeId === node.id ? ' dragging' : ''}${isTracking ? ' tracking' : ''}`}
                    style={isTracking ? { borderLeft: '3px solid var(--accent-primary)' } : undefined}
                    draggable onDragStart={() => handleDragStart(node.id)} onDragEnd={handleDragEnd}
                    onClick={() => navigate(`/nodes/${node.id}`)}>
                    <div className="kanban-card-title">{node.title}</div>
                    <div className="kanban-card-meta">
                      <span>{getDueDateLabel(node)}</span>
                      <span className={`task-priority ${getPriorityClass(node.priority)}`} />
                    </div>
                    {isTracking && getTrackingTimers(node.id).map((t) => (
                      <div key={t.id} className="kanban-card-timer">⏱ {formatTimerDuration(elapsedMap[t.id] ?? 0)}{t.actor ? ` (${t.actor})` : ''}</div>
                    ))}
                  </div>
                );
              })}
              {col.nodes.length === 0 && (
                <div style={{ padding: 16, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>No items</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
