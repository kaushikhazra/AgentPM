import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectsApi } from '@/api/projects';
import { nodesApi } from '@/api/nodes';
import { edgesApi } from '@/api/edges';
import { Button } from '@/components/atoms';
import { Modal } from '@/components/organisms';
import { METHODOLOGY_UI, getNodeTypeUI, getStatusLabel } from '@/config/methodology-ui';
import type { Project, Node, Edge } from '@/types';

const GRADIENTS = [
  'var(--gradient-primary)',
  'var(--gradient-secondary)',
  'linear-gradient(135deg, var(--accent-mint), var(--accent-sage))',
  'linear-gradient(135deg, var(--accent-peach), var(--accent-blush))',
];

interface TreeNode {
  node: Node;
  children: TreeNode[];
}

function statusClass(status: string): string {
  if (status === 'done' || status === 'approved') return 'done';
  if (status === 'in_progress') return 'progress';
  if (status === 'blocked') return 'blocked';
  if (status === 'backlog' || status === 'draft') return 'backlog';
  if (status === 'ready') return 'ready';
  if (status === 'review' || status === 'in_review') return 'review';
  return 'backlog';
}

function buildTree(nodes: Node[], edges: Edge[]): TreeNode[] {
  const childMap = new Map<string, string[]>();
  edges.forEach((e) => {
    if (e.edge_type === 'parent') {
      const children = childMap.get(e.source_id) ?? [];
      children.push(e.target_id);
      childMap.set(e.source_id, children);
    }
  });

  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  const hasParent = new Set(edges.filter((e) => e.edge_type === 'parent').map((e) => e.target_id));

  function buildChildren(parentId: string): TreeNode[] {
    const childIds = childMap.get(parentId) ?? [];
    return childIds
      .map((id) => {
        const node = nodeMap.get(id);
        if (!node) return null;
        return { node, children: buildChildren(id) };
      })
      .filter((t): t is TreeNode => t !== null);
  }

  // Root nodes: nodes that are not children of any other node
  const roots = nodes.filter((n) => !hasParent.has(n.id));
  return roots.map((n) => ({ node: n, children: buildChildren(n.id) }));
}

export function PlannerPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState(projectId ?? '');
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [error, setError] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Create node modal
  const [showCreate, setShowCreate] = useState(false);
  const [createTitle, setCreateTitle] = useState('');
  const [createType, setCreateType] = useState('');
  const [createParent, setCreateParent] = useState('');
  const [createDesc, setCreateDesc] = useState('');
  const [creating, setCreating] = useState(false);

  const loadProjects = useCallback(async () => {
    try {
      const list = await projectsApi.list();
      setProjects(list);
      if (!selectedId && list.length > 0) {
        setSelectedId(list[0]!.id);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    }
  }, [selectedId]);

  const loadData = useCallback(async () => {
    if (!selectedId) return;
    try {
      const [nodeList, edgeList] = await Promise.all([
        nodesApi.list({ project_id: selectedId }),
        edgesApi.list({ project_id: selectedId }),
      ]);
      setNodes(nodeList);
      setEdges(edgeList);

      // Auto-expand root nodes on first load
      if (expanded.size === 0) {
        const methUI = METHODOLOGY_UI[projects.find((p) => p.id === selectedId)?.methodology ?? ''];
        const rootType = methUI ? Object.keys(methUI.nodeTypes)[0] : undefined;
        const rootIds = nodeList
          .filter((n) => rootType ? n.node_type === rootType : true)
          .map((n) => n.id);
        setExpanded(new Set(rootIds));
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    }
  }, [selectedId, projects, expanded.size]);

  useEffect(() => { loadProjects(); }, [loadProjects]);
  useEffect(() => { loadData(); }, [loadData]);

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
  const nodeTypes = methUI ? Object.keys(methUI.nodeTypes) : [];
  const tree = buildTree(nodes, edges);

  const toggleExpand = (id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectProject = (id: string) => {
    setSelectedId(id);
    setDropdownOpen(false);
    setExpanded(new Set());
    navigate(`/planner/${id}`, { replace: true });
  };

  const handleCreate = async () => {
    if (!createTitle.trim() || !selectedId) return;
    setCreating(true);
    try {
      await nodesApi.create({
        project_id: selectedId,
        node_type: createType,
        title: createTitle.trim(),
        description: createDesc.trim() || undefined,
        parent_id: createParent || undefined,
      });
      setShowCreate(false);
      setCreateTitle('');
      setCreateDesc('');
      setCreateParent('');
      await loadData();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to create');
    } finally {
      setCreating(false);
    }
  };

  const handleToggleStatus = async (node: Node) => {
    try {
      if (node.status === 'done' || node.status === 'approved') return;
      if (node.status === 'in_progress') {
        await nodesApi.complete(node.id);
      } else {
        await nodesApi.start(node.id);
      }
      await loadData();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to update');
    }
  };

  // Set default create type
  const openCreate = () => {
    if (!createType && nodeTypes.length > 0) {
      setCreateType(nodeTypes[0]!);
    }
    setShowCreate(true);
  };

  function renderTreeNode(treeNode: TreeNode, depth: number) {
    const { node, children } = treeNode;
    const isExpanded = expanded.has(node.id);
    const hasChildren = children.length > 0;
    const rollup = node.rollup;
    const totalChildren = rollup?.total_children ?? children.length;
    const completedChildren = rollup?.completed_children ?? children.filter((c) => c.node.status === 'done' || c.node.status === 'approved').length;
    const pct = totalChildren > 0 ? Math.round((completedChildren / totalChildren) * 100) : 0;
    const isDone = node.status === 'done' || node.status === 'approved';

    if (depth === 0) {
      // Root level — epic style
      return (
        <div key={node.id} className={`epic-item${isExpanded ? ' expanded' : ''}`}>
          <div className="epic-header" onClick={() => toggleExpand(node.id)}>
            <div className="accordion-toggle">
              <svg viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6" /></svg>
            </div>
            <div className="epic-icon">{node.title.charAt(0).toUpperCase()}</div>
            <div className="epic-info">
              <div className="epic-title">{node.title}</div>
              <div className="epic-meta">
                {node.id.slice(0, 8)} &bull; {totalChildren} children
              </div>
            </div>
            <div className="epic-progress">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${pct}%` }} />
              </div>
              <span className="progress-text">{pct}%</span>
            </div>
            <span className={`status-badge ${statusClass(node.status)}`}>
              {getStatusLabel(methodology, node.status)}
            </span>
          </div>
          <div className="epic-content">
            {hasChildren && (
              <div className="story-list">
                {children.map((c) => renderTreeNode(c, depth + 1))}
              </div>
            )}
          </div>
        </div>
      );
    }

    if (depth === 1) {
      // Second level — story style
      return (
        <div key={node.id} className={`story-item${isExpanded ? ' expanded' : ''}`}>
          <div className="story-header" onClick={() => toggleExpand(node.id)}>
            <div className="accordion-toggle">
              <svg viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6" /></svg>
            </div>
            <div className="story-icon">
              <svg viewBox="0 0 24 24">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <div className="story-info">
              <div className="story-title-text">{node.title}</div>
              <div className="story-meta">{node.id.slice(0, 8)} &bull; {totalChildren} children</div>
            </div>
            <div className="epic-progress">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${pct}%` }} />
              </div>
              <span className="progress-text">{pct}%</span>
            </div>
            <span className={`status-badge ${statusClass(node.status)}`}>
              {getStatusLabel(methodology, node.status)}
            </span>
          </div>
          <div className="story-content">
            {hasChildren && (
              <div className="planner-task-list">
                {children.map((c) => renderTreeNode(c, depth + 1))}
              </div>
            )}
          </div>
        </div>
      );
    }

    // Leaf level — task style
    return (
      <div
        key={node.id}
        className={`planner-task-item${isDone ? ' completed' : ''}`}
        onClick={() => navigate(`/nodes/${node.id}`)}
      >
        <div
          className={`planner-task-checkbox${isDone ? ' checked' : ''}`}
          onClick={(e) => { e.stopPropagation(); handleToggleStatus(node); }}
        >
          {isDone && (
            <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12" /></svg>
          )}
        </div>
        <span className="planner-task-title">{node.title}</span>
        <span className="planner-task-id">{node.id.slice(0, 8)}</span>
      </div>
    );
  }

  return (
    <div className="content-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Planner</h1>
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
        <Button variant="primary" onClick={openCreate}>
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" strokeWidth="2">
            <path d="M12 5v14" /><path d="M5 12h14" />
          </svg>
          Add Item
        </Button>
      </div>

      {error && <p style={{ color: 'var(--status-blocked)', marginBottom: 16 }}>{error}</p>}

      <div className="planner-tree">
        {tree.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-title">No items yet</div>
            <div className="empty-state-text">Create your first item to get started</div>
            <Button variant="primary" onClick={openCreate}>Add Item</Button>
          </div>
        ) : (
          tree.map((t) => renderTreeNode(t, 0))
        )}
      </div>

      {/* Create Node Modal */}
      <Modal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title={`New ${createType ? getNodeTypeUI(methodology, createType).displayName : 'Item'}`}
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button variant="primary" onClick={handleCreate} disabled={creating}>
              {creating ? 'Creating...' : 'Create'}
            </Button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label">Type</label>
          <select
            className="form-select"
            value={createType}
            onChange={(e) => setCreateType(e.target.value)}
          >
            {nodeTypes.map((nt) => (
              <option key={nt} value={nt}>{getNodeTypeUI(methodology, nt).displayName}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Parent</label>
          <select
            className="form-select"
            value={createParent}
            onChange={(e) => setCreateParent(e.target.value)}
          >
            <option value="">No parent (top-level)</option>
            {nodes.map((n) => (
              <option key={n.id} value={n.id}>
                {getNodeTypeUI(methodology, n.node_type).displayName}: {n.title}
              </option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Title</label>
          <input
            className="form-input"
            placeholder="Enter title..."
            value={createTitle}
            onChange={(e) => setCreateTitle(e.target.value)}
            autoFocus
          />
        </div>
        <div className="form-group">
          <label className="form-label">Description</label>
          <textarea
            className="form-input"
            placeholder="Describe the item..."
            value={createDesc}
            onChange={(e) => setCreateDesc(e.target.value)}
          />
        </div>
      </Modal>
    </div>
  );
}
