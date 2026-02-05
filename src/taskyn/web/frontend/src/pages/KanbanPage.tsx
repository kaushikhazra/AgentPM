import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectsApi } from '@/api/projects';
import { nodesApi } from '@/api/nodes';
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
  // Since nodes don't have due_date field, we use created_at as a proxy
  // In a real implementation, this would check the due_date field
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
  const { activeTimer, elapsed } = useTimer();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState(projectId ?? '');
  const [nodes, setNodes] = useState<Node[]>([]);
  const [error, setError] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Drag-and-drop state
  const [dragNodeId, setDragNodeId] = useState<string | null>(null);
  const [dropTarget, setDropTarget] = useState<string | null>(null);

  const loadProjects = useCallback(async () => {
    try {
      const list = await projectsApi.list();
      setProjects(list);
      if (!selectedId && list.length > 0) {
        setSelectedId(list[0]!.id);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load projects');
    }
  }, [selectedId]);

  const loadNodes = useCallback(async () => {
    if (!selectedId) return;
    try {
      const list = await nodesApi.list({ project_id: selectedId });
      setNodes(list);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load nodes');
    }
  }, [selectedId]);

  useEffect(() => { loadProjects(); }, [loadProjects]);
  useEffect(() => { loadNodes(); }, [loadNodes]);

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

  const selectedProject = projects.find((p) => p.id === selectedId);
  const methodology = selectedProject?.methodology ?? 'classic_agile';
  const methUI = METHODOLOGY_UI[methodology];
  const statuses = methUI ? Object.keys(methUI.statusLabels) : ['backlog', 'ready', 'in_progress', 'done'];

  // Status color map
  const statusColors: Record<string, string> = {
    backlog: 'var(--status-backlog)',
    draft: 'var(--status-backlog)',
    ready: 'var(--status-ready)',
    in_progress: 'var(--status-progress)',
    in_review: 'var(--status-review)',
    review: 'var(--status-review)',
    done: 'var(--status-done)',
    approved: 'var(--status-done)',
    blocked: 'var(--status-blocked)',
  };

  // Group nodes by status
  const columns = statuses.map((status) => ({
    status,
    label: getStatusLabel(methodology, status),
    color: statusColors[status] ?? 'var(--text-tertiary)',
    nodes: nodes.filter((n) => n.status === status),
  }));

  const selectProject = (id: string) => {
    setSelectedId(id);
    setDropdownOpen(false);
    navigate(`/kanban/${id}`, { replace: true });
  };

  // Drag handlers
  const handleDragStart = (nodeId: string) => {
    setDragNodeId(nodeId);
  };

  const handleDragOver = (e: React.DragEvent, status: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDropTarget(status);
  };

  const handleDragLeave = () => {
    setDropTarget(null);
  };

  const handleDrop = async (e: React.DragEvent, targetStatus: string) => {
    e.preventDefault();
    setDropTarget(null);

    if (!dragNodeId) return;

    const node = nodes.find((n) => n.id === dragNodeId);
    if (!node || node.status === targetStatus) {
      setDragNodeId(null);
      return;
    }

    // Optimistic update
    setNodes((prev) =>
      prev.map((n) => (n.id === dragNodeId ? { ...n, status: targetStatus } : n)),
    );
    setDragNodeId(null);

    try {
      await nodesApi.update(dragNodeId, { status: targetStatus });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to move card');
      // Revert on failure
      await loadNodes();
    }
  };

  const handleDragEnd = () => {
    setDragNodeId(null);
    setDropTarget(null);
  };

  const isNodeTracking = (nodeId: string): boolean => {
    return activeTimer?.node_id === nodeId;
  };

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
            <div
              className={`filter-badge${dropdownOpen ? ' open' : ''}`}
              ref={dropdownRef}
              onClick={() => setDropdownOpen(!dropdownOpen)}
            >
              <div
                className="filter-badge-icon-box"
                style={{ background: GRADIENTS[projects.indexOf(selectedProject!) % GRADIENTS.length] ?? GRADIENTS[0] }}
              >
                {selectedProject?.name.charAt(0).toUpperCase() ?? '?'}
              </div>
              <span className="filter-badge-text">{selectedProject?.name ?? 'Select project'}</span>
              <svg className="filter-badge-arrow" viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9" /></svg>
              <div className="filter-dropdown">
                {projects.map((p, i) => (
                  <div
                    key={p.id}
                    className={`filter-dropdown-item${p.id === selectedId ? ' selected' : ''}`}
                    onClick={(e) => { e.stopPropagation(); selectProject(p.id); }}
                  >
                    <div className="filter-dropdown-icon" style={{ background: GRADIENTS[i % GRADIENTS.length] }}>
                      {p.name.charAt(0).toUpperCase()}
                    </div>
                    <span className="filter-dropdown-label">{p.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {error && <p style={{ color: 'var(--status-blocked)', marginBottom: 16 }}>{error}</p>}

      <div className="kanban-board">
        {columns.map((col) => (
          <div
            key={col.status}
            className={`kanban-column${dropTarget === col.status ? ' drag-over' : ''}`}
            onDragOver={(e) => handleDragOver(e, col.status)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e, col.status)}
          >
            <div className="kanban-column-header">
              <div className="kanban-column-title">
                <span style={{ color: col.color }}>●</span>
                {col.label}
              </div>
              <span className="kanban-column-count">{col.nodes.length}</span>
            </div>
            <div className="kanban-column-content">
              {col.nodes.map((node) => {
                const isTracking = isNodeTracking(node.id);
                return (
                  <div
                    key={node.id}
                    className={`kanban-card${col.status === 'done' ? ' done-card' : ''}${dragNodeId === node.id ? ' dragging' : ''}${isTracking ? ' tracking' : ''}`}
                    style={isTracking ? { borderLeft: '3px solid var(--accent-primary)' } : undefined}
                    draggable
                    onDragStart={() => handleDragStart(node.id)}
                    onDragEnd={handleDragEnd}
                    onClick={() => navigate(`/nodes/${node.id}`)}
                  >
                    <div className="kanban-card-title">{node.title}</div>
                    <div className="kanban-card-meta">
                      <span>{getDueDateLabel(node)}</span>
                      <span className={`task-priority ${getPriorityClass(node.priority)}`} />
                    </div>
                    {isTracking && (
                      <div className="kanban-card-timer">
                        ⏱ {formatTimerDuration(elapsed)} tracking
                      </div>
                    )}
                  </div>
                );
              })}
              {col.nodes.length === 0 && (
                <div style={{ padding: 16, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
                  No items
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
