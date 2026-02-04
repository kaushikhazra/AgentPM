import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectsApi } from '@/api/projects';
import { nodesApi } from '@/api/nodes';
import { METHODOLOGY_UI, getStatusLabel } from '@/config/methodology-ui';
import type { Project, Node } from '@/types';

const GRADIENTS = [
  'var(--gradient-primary)',
  'var(--gradient-secondary)',
  'linear-gradient(135deg, var(--accent-mint), var(--accent-sage))',
  'linear-gradient(135deg, var(--accent-peach), var(--accent-blush))',
];

export function KanbanPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState(projectId ?? '');
  const [nodes, setNodes] = useState<Node[]>([]);
  const [error, setError] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

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
          <div key={col.status} className="kanban-column">
            <div className="kanban-column-header">
              <div className="kanban-column-title">
                <span style={{ color: col.color }}>●</span>
                {col.label}
              </div>
              <span className="kanban-column-count">{col.nodes.length}</span>
            </div>
            <div className="kanban-column-content">
              {col.nodes.map((node) => (
                <div
                  key={node.id}
                  className={`kanban-card${col.status === 'done' ? ' done-card' : ''}`}
                  onClick={() => navigate(`/nodes/${node.id}`)}
                >
                  <div className="kanban-card-title">{node.title}</div>
                  <div className="kanban-card-meta">
                    <span>{node.node_type}</span>
                    <span>{node.id.slice(0, 8)}</span>
                  </div>
                </div>
              ))}
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
