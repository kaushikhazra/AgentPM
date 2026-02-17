import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useProjects } from '@/hooks/queries/useProjects';
import { useNodes } from '@/hooks/queries/useNodes';
import { useEdges } from '@/hooks/queries/useEdges';
import { useCreateNode, useStartNode, useCompleteNode } from '@/hooks/mutations/useNodeMutations';
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
  if (status === 'done') return 'done';
  if (status === 'in_progress' || status === 'active') return 'progress';
  if (status === 'blocked') return 'blocked';
  if (status === 'cancelled') return 'blocked';
  if (status === 'backlog' || status === 'draft' || status === 'todo') return 'backlog';
  if (status === 'ready') return 'ready';
  if (status === 'review' || status === 'in_review') return 'review';
  return 'backlog';
}

function buildTree(nodes: Node[], edges: Edge[]): TreeNode[] {
  const childMap = new Map<string, string[]>();
  edges.forEach((e) => {
    if (e.edge_type === 'parent') {
      const children = childMap.get(e.target_id) ?? [];
      children.push(e.source_id);
      childMap.set(e.target_id, children);
    }
  });
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  const hasParent = new Set(edges.filter((e) => e.edge_type === 'parent').map((e) => e.source_id));

  function buildChildren(parentId: string): TreeNode[] {
    const childIds = childMap.get(parentId) ?? [];
    return childIds
      .map((id) => { const node = nodeMap.get(id); if (!node) return null; return { node, children: buildChildren(id) }; })
      .filter((t): t is TreeNode => t !== null);
  }

  const roots = nodes.filter((n) => !hasParent.has(n.id));
  return roots.map((n) => ({ node: n, children: buildChildren(n.id) }));
}

export function PlannerPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { data: projects = [] } = useProjects();
  const [selectedId, setSelectedId] = useState(projectId ?? '');
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const initialExpandDone = useRef(false);

  const { data: nodes = [] } = useNodes(selectedId ? { project_id: selectedId } : undefined);
  const { data: edges = [] } = useEdges(selectedId ? { project_id: selectedId } : undefined);

  const createNodeMutation = useCreateNode();
  const startNodeMutation = useStartNode();
  const completeNodeMutation = useCompleteNode();

  const [showCreate, setShowCreate] = useState(false);
  const [createTitle, setCreateTitle] = useState('');
  const [createType, setCreateType] = useState('');
  const [createParent, setCreateParent] = useState('');
  const [createDesc, setCreateDesc] = useState('');

  // Auto-select first project
  useEffect(() => {
    if (!selectedId && projects.length > 0) setSelectedId(projects[0]!.id);
  }, [selectedId, projects]);

  // Auto-expand root nodes on first load
  useEffect(() => {
    if (nodes.length > 0 && !initialExpandDone.current) {
      initialExpandDone.current = true;
      const methUI = METHODOLOGY_UI[projects.find((p: Project) => p.id === selectedId)?.methodology ?? ''];
      const rootType = methUI ? Object.keys(methUI.nodeTypes)[0] : undefined;
      const rootIds = nodes
        .filter((n: Node) => rootType ? n.node_type === rootType : true)
        .map((n: Node) => n.id);
      setExpanded(new Set(rootIds));
    }
  }, [nodes, projects, selectedId]);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as HTMLElement)) setDropdownOpen(false);
    }
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, []);

  const selectedProject = projects.find((p: Project) => p.id === selectedId);
  const methodology = selectedProject?.methodology ?? 'classic_agile';
  const methUI = METHODOLOGY_UI[methodology];
  const nodeTypes = methUI ? Object.keys(methUI.nodeTypes) : [];
  const tree = buildTree(nodes, edges);

  const toggleExpand = (id: string) => {
    setExpanded((prev) => { const next = new Set(prev); if (next.has(id)) next.delete(id); else next.add(id); return next; });
  };

  const selectProject = (id: string) => {
    setSelectedId(id);
    setDropdownOpen(false);
    setExpanded(new Set());
    initialExpandDone.current = false;
    navigate(`/planner/${id}`, { replace: true });
  };

  const handleCreate = async () => {
    if (!createTitle.trim() || !selectedId) return;
    createNodeMutation.mutate(
      { project_id: selectedId, node_type: createType, title: createTitle.trim(), description: createDesc.trim() || undefined, parent_id: createParent || undefined },
      { onSuccess: () => { setShowCreate(false); setCreateTitle(''); setCreateDesc(''); setCreateParent(''); } },
    );
  };

  const handleToggleStatus = async (node: Node) => {
    if (node.status === 'done') return;
    if (node.status === 'in_progress') completeNodeMutation.mutate(node.id);
    else startNodeMutation.mutate(node.id);
  };

  const openCreate = () => {
    if (!createType && nodeTypes.length > 0) setCreateType(nodeTypes[0]!);
    setShowCreate(true);
  };

  function renderTreeNode(treeNode: TreeNode, depth: number) {
    const { node, children } = treeNode;
    const isExpanded = expanded.has(node.id);
    const hasChildren = children.length > 0;
    const rollup = node.rollup;
    const totalChildren = rollup?.total_children ?? children.length;
    const completedChildren = rollup?.completed_children ?? children.filter((c) => c.node.status === 'done').length;
    const pct = totalChildren > 0 ? Math.round((completedChildren / totalChildren) * 100) : 0;
    const isDone = node.status === 'done';

    if (depth === 0) {
      return (
        <div key={node.id} className={`epic-item${isExpanded ? ' expanded' : ''}`}>
          <div className="epic-header" onClick={() => toggleExpand(node.id)}>
            <div className="accordion-toggle"><svg viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6" /></svg></div>
            <div className="epic-icon">{node.title.charAt(0).toUpperCase()}</div>
            <div className="epic-info">
              <div className="epic-title">{node.title}</div>
              <div className="epic-meta">{node.id.slice(0, 8)} &bull; {totalChildren} children</div>
            </div>
            <div className="epic-progress"><div className="progress-bar"><div className="progress-fill" style={{ width: `${pct}%` }} /></div><span className="progress-text">{pct}%</span></div>
            <span className={`status-badge ${statusClass(node.status)}`}>{getStatusLabel(methodology, node.status)}</span>
          </div>
          <div className="epic-content">{hasChildren && <div className="story-list">{children.map((c) => renderTreeNode(c, depth + 1))}</div>}</div>
        </div>
      );
    }

    if (depth === 1) {
      return (
        <div key={node.id} className={`story-item${isExpanded ? ' expanded' : ''}`}>
          <div className="story-header" onClick={() => toggleExpand(node.id)}>
            <div className="accordion-toggle"><svg viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6" /></svg></div>
            <div className="story-icon"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg></div>
            <div className="story-info">
              <div className="story-title-text">{node.title}</div>
              <div className="story-meta">{node.id.slice(0, 8)} &bull; {totalChildren} children</div>
            </div>
            <div className="epic-progress"><div className="progress-bar"><div className="progress-fill" style={{ width: `${pct}%` }} /></div><span className="progress-text">{pct}%</span></div>
            <span className={`status-badge ${statusClass(node.status)}`}>{getStatusLabel(methodology, node.status)}</span>
          </div>
          <div className="story-content">{hasChildren && <div className="planner-task-list">{children.map((c) => renderTreeNode(c, depth + 1))}</div>}</div>
        </div>
      );
    }

    return (
      <div key={node.id} className={`planner-task-item${isDone ? ' completed' : ''}`} onClick={() => navigate(`/nodes/${node.id}`)}>
        <div className={`planner-task-checkbox${isDone ? ' checked' : ''}`} onClick={(e) => { e.stopPropagation(); handleToggleStatus(node); }}>
          {isDone && <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12" /></svg>}
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
        <Button variant="primary" onClick={openCreate}>
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" strokeWidth="2"><path d="M12 5v14" /><path d="M5 12h14" /></svg>
          Add Item
        </Button>
      </div>

      <div className="planner-tree">
        {tree.length === 0 ? (
          <div className="empty-state"><div className="empty-state-title">No items yet</div><div className="empty-state-text">Create your first item to get started</div><Button variant="primary" onClick={openCreate}>Add Item</Button></div>
        ) : tree.map((t) => renderTreeNode(t, 0))}
      </div>

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title={`New ${createType ? getNodeTypeUI(methodology, createType).displayName : 'Item'}`}
        footer={<><Button variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button><Button variant="primary" onClick={handleCreate} disabled={createNodeMutation.isPending}>{createNodeMutation.isPending ? 'Creating...' : 'Create'}</Button></>}
      >
        <div className="form-group"><label className="form-label">Type</label><select className="form-select" value={createType} onChange={(e) => setCreateType(e.target.value)}>{nodeTypes.map((nt) => (<option key={nt} value={nt}>{getNodeTypeUI(methodology, nt).displayName}</option>))}</select></div>
        <div className="form-group"><label className="form-label">Parent</label><select className="form-select" value={createParent} onChange={(e) => setCreateParent(e.target.value)}><option value="">No parent (top-level)</option>{nodes.map((n: Node) => (<option key={n.id} value={n.id}>{getNodeTypeUI(methodology, n.node_type).displayName}: {n.title}</option>))}</select></div>
        <div className="form-group"><label className="form-label">Title</label><input className="form-input" placeholder="Enter title..." value={createTitle} onChange={(e) => setCreateTitle(e.target.value)} autoFocus /></div>
        <div className="form-group"><label className="form-label">Description</label><textarea className="form-input" placeholder="Describe the item..." value={createDesc} onChange={(e) => setCreateDesc(e.target.value)} /></div>
      </Modal>
    </div>
  );
}
