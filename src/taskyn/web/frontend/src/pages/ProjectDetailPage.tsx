import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useProject } from '@/hooks/queries/useProjects';
import { useCompany } from '@/hooks/queries/useCompanies';
import { useNodes } from '@/hooks/queries/useNodes';
import { useCreateNode } from '@/hooks/mutations/useNodeMutations';
import { useUpdateProject, useDeleteProject } from '@/hooks/mutations/useProjectMutations';
import { Button, Icon } from '@/components/atoms';
import { StatCard } from '@/components/molecules';
import { DetailLayout } from '@/components/templates/DetailLayout';
import { Section, Modal } from '@/components/organisms';
import { METHODOLOGY_UI, getNodeTypeUI, getStatusLabel, getChildTypes } from '@/config/methodology-ui';
import { ENTITY_TYPES, ENTITY_TYPE_COLORS, type EntityType } from '@/types';
import type { Node } from '@/types';
import { formatDuration } from '@/utils/formatDuration';

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

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { data: project } = useProject(projectId);
  const { data: company } = useCompany(project?.company_id ?? undefined);
  const { data: nodes = [] } = useNodes(projectId ? { project_id: projectId } : undefined);

  const createNode = useCreateNode();
  const updateProject = useUpdateProject();
  const deleteProject = useDeleteProject();

  const [tab, setTab] = useState('all');
  const [showCreate, setShowCreate] = useState(false);
  const [createTitle, setCreateTitle] = useState('');
  const [createType, setCreateType] = useState('');
  const [createDesc, setCreateDesc] = useState('');
  const [showDelete, setShowDelete] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editStatus, setEditStatus] = useState('');
  const [editType, setEditType] = useState<EntityType>('discovery');
  const [editMethodology, setEditMethodology] = useState('');

  if (!project || !project.methodology) {
    return (
      <div className="content-wrapper">
        <p className="text-secondary">Loading...</p>
      </div>
    );
  }

  const methodology = project.methodology;
  const methUI = METHODOLOGY_UI[methodology];
  const rootType = (methUI ? Object.keys(methUI.nodeTypes)[0] : undefined) ?? 'node';
  const rootTypeUI = getNodeTypeUI(methodology, rootType);

  // Set default create type if not set
  if (!createType && methUI) {
    const firstType = Object.keys(methUI.nodeTypes)[0];
    if (firstType) setCreateType(firstType);
  }

  const rootNodes = nodes.filter((n: Node) => n.node_type === rootType);

  const filteredNodes = tab === 'all'
    ? rootNodes
    : tab === 'progress'
      ? rootNodes.filter((n: Node) => n.status === 'in_progress')
      : rootNodes.filter((n: Node) => n.status === 'done');

  const nodesByType: Record<string, number> = {};
  nodes.forEach((n: Node) => {
    nodesByType[n.node_type] = (nodesByType[n.node_type] ?? 0) + 1;
  });
  const totalDone = nodes.filter((n: Node) => n.status === 'done').length;
  const pct = nodes.length > 0 ? Math.round((totalDone / nodes.length) * 100) : 0;

  const breadcrumbs = [
    ...(company ? [{ label: company.name, to: '/companies' }] : []),
    { label: project.name },
  ];

  const nodeTypes = methUI ? Object.keys(methUI.nodeTypes) : [];

  const handleCreate = async () => {
    if (!createTitle.trim() || !projectId) return;
    createNode.mutate(
      {
        project_id: projectId,
        node_type: createType,
        title: createTitle.trim(),
        description: createDesc.trim() || undefined,
      },
      {
        onSuccess: () => {
          setShowCreate(false);
          setCreateTitle('');
          setCreateDesc('');
        },
      },
    );
  };

  const handleDelete = async () => {
    if (!projectId) return;
    deleteProject.mutate(projectId, {
      onSuccess: () => navigate('/projects'),
    });
  };

  const openEdit = () => {
    if (!project) return;
    setEditName(project.name);
    setEditDesc(project.description ?? '');
    setEditStatus(project.status);
    setEditType(project.type ?? 'discovery');
    setEditMethodology(project.methodology);
    setShowEdit(true);
  };

  const handleUpdate = async () => {
    if (!projectId || !editName.trim()) return;
    updateProject.mutate(
      {
        id: projectId,
        data: {
          name: editName.trim(),
          description: editDesc.trim() || undefined,
          status: editStatus,
          type: editType,
          ...(nodes.length === 0 ? { methodology: editMethodology } : {}),
        },
      },
      { onSuccess: () => setShowEdit(false) },
    );
  };

  return (
    <DetailLayout
      breadcrumbs={breadcrumbs}
      title={project.name}
      subtitle={project.description ?? undefined}
      headerAction={
        <div className="header-actions">
          <Button variant="ghost" onClick={() => setShowDelete(true)}>
            <Icon name="trash" size={18} />
          </Button>
          <Button variant="secondary" onClick={openEdit}>
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" strokeWidth="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
            Edit
          </Button>
          <Button variant="primary" onClick={() => setShowCreate(true)}>
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" strokeWidth="2">
              <path d="M12 5v14" /><path d="M5 12h14" />
            </svg>
            New {rootTypeUI.displayName}
          </Button>
        </div>
      }
    >
      <div className="stats-grid">
        {nodeTypes.slice(0, 3).map((nt) => {
          const ui = getNodeTypeUI(methodology, nt);
          return (
            <StatCard key={nt} label={ui.plural} value={nodesByType[nt] ?? 0} />
          );
        })}
        <StatCard label="Progress" value={`${pct}%`} />
      </div>

      <Section
        title={rootTypeUI.plural}
        action={
          <div className="section-tabs">
            <button className={`section-tab${tab === 'all' ? ' active' : ''}`} onClick={() => setTab('all')}>All</button>
            <button className={`section-tab${tab === 'progress' ? ' active' : ''}`} onClick={() => setTab('progress')}>In Progress</button>
            <button className={`section-tab${tab === 'done' ? ' active' : ''}`} onClick={() => setTab('done')}>Completed</button>
          </div>
        }
      >
        {filteredNodes.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">
              <svg viewBox="0 0 24 24">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <div className="empty-state-title">No {rootTypeUI.plural.toLowerCase()} yet</div>
            <div className="empty-state-text">Create your first {rootTypeUI.displayName.toLowerCase()} to get started</div>
            <Button variant="primary" onClick={() => setShowCreate(true)}>
              New {rootTypeUI.displayName}
            </Button>
          </div>
        ) : (
          <div className="work-item-list">
            {filteredNodes.map((node: Node) => {
              const nodeRollup = node.rollup;
              const childTotal = nodeRollup?.total_children ?? 0;
              const childDone = nodeRollup?.completed_children ?? 0;
              const nodePct = childTotal > 0 ? Math.round((childDone / childTotal) * 100) : 0;
              const childTypeList = getChildTypes(methodology, node.node_type);
              const directChildren = nodes.filter((n: Node) => n.parent_id === node.id);
              // Per-type counts for direct children
              const childCounts = childTypeList.map((ct) => {
                const count = directChildren.filter((c: Node) => c.node_type === ct).length;
                const ui = getNodeTypeUI(methodology, ct);
                return { type: ct, count, label: count === 1 ? ui.displayName.toLowerCase() : ui.plural.toLowerCase() };
              });
              // Grandchild: find todo-level types (children of any child type)
              const grandchildTypes = new Set(childTypeList.flatMap((ct) => getChildTypes(methodology, ct)));
              const grandchildCount = grandchildTypes.size > 0
                ? nodes.filter((n: Node) => grandchildTypes.has(n.node_type) && directChildren.some((c: Node) => c.id === n.parent_id)).length
                : 0;
              const grandchildTypeUI = grandchildTypes.size > 0
                ? getNodeTypeUI(methodology, [...grandchildTypes][0]!)
                : null;

              return (
                <div key={node.id} className="work-item-card" onClick={() => navigate(`/nodes/${node.id}`)}>
                  <div className="work-item-header">
                    <span className="work-item-title">{node.title}</span>
                    <span className="work-item-id">{node.id.slice(0, 8)}</span>
                  </div>
                  <div className="work-item-meta">
                    {childCounts.map((cc) => (
                      <span key={cc.type}>{cc.count} {cc.label}</span>
                    ))}
                    {grandchildTypeUI && (
                      <span>{grandchildCount} {grandchildCount === 1 ? grandchildTypeUI.displayName.toLowerCase() : grandchildTypeUI.plural.toLowerCase()}</span>
                    )}
                    {node.actual_time > 0 && (
                      <span className="work-item-time">{formatDuration(node.actual_time)}</span>
                    )}
                    <div className="work-item-progress">
                      <div className="work-item-progress-bar">
                        <div className="work-item-progress-fill" style={{ width: `${nodePct}%` }} />
                      </div>
                      <span>{nodePct}%</span>
                    </div>
                    <span className={`status-badge ${statusClass(node.status)}`}>
                      {getStatusLabel(methodology, node.status)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Section>

      <Modal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title={`New ${getNodeTypeUI(methodology, createType).displayName}`}
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button variant="primary" onClick={handleCreate} disabled={createNode.isPending}>
              {createNode.isPending ? 'Creating...' : 'Create'}
            </Button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label">Type</label>
          <select className="form-select" value={createType} onChange={(e) => setCreateType(e.target.value)}>
            {nodeTypes.map((nt) => (
              <option key={nt} value={nt}>{getNodeTypeUI(methodology, nt).displayName}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Title</label>
          <input className="form-input" placeholder={`e.g., ${rootTypeUI.displayName} title`} value={createTitle} onChange={(e) => setCreateTitle(e.target.value)} autoFocus />
        </div>
        <div className="form-group">
          <label className="form-label">Description</label>
          <textarea className="form-input" placeholder="Describe the work item..." value={createDesc} onChange={(e) => setCreateDesc(e.target.value)} />
        </div>
      </Modal>

      <Modal
        open={showDelete}
        onClose={() => setShowDelete(false)}
        title="Delete Project"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowDelete(false)}>Cancel</Button>
            <Button variant="danger" onClick={handleDelete} disabled={deleteProject.isPending}>
              {deleteProject.isPending ? 'Deleting...' : 'Delete Project'}
            </Button>
          </>
        }
      >
        <p style={{ marginBottom: 16 }}>
          Are you sure you want to delete <strong>{project.name}</strong>?
        </p>
        <p className="text-secondary">
          This will permanently delete all {nodes.length} work items and their time entries.
          This action cannot be undone.
        </p>
      </Modal>
      {/* Edit Project Modal */}
      <Modal
        open={showEdit}
        onClose={() => setShowEdit(false)}
        title="Edit Project"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowEdit(false)}>Cancel</Button>
            <Button variant="primary" onClick={handleUpdate} disabled={updateProject.isPending}>
              {updateProject.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label">Project Name</label>
          <input
            className="form-input"
            placeholder="e.g., Website Redesign, Mobile App"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            autoFocus
          />
        </div>
        <div className="form-group">
          <label className="form-label">Status</label>
          <select
            className="form-select"
            value={editStatus}
            onChange={(e) => setEditStatus(e.target.value)}
          >
            <option value="active">Active</option>
            <option value="on_hold">On Hold</option>
            <option value="completed">Completed</option>
            <option value="archived">Archived</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Methodology</label>
          <select
            className="form-select"
            value={editMethodology}
            onChange={(e) => setEditMethodology(e.target.value)}
            disabled={nodes.length > 0}
          >
            <option value="classic_agile">Classic Agile</option>
            <option value="spec_driven">Spec Driven</option>
          </select>
          {nodes.length > 0 && (
            <p className="form-hint">Cannot change methodology: project has {nodes.length} existing node(s).</p>
          )}
        </div>
        <div className="form-group">
          <label className="form-label">Lifecycle Stage</label>
          <div className="color-picker">
            {ENTITY_TYPES.map((type) => (
              <div
                key={type}
                className={`color-option${editType === type ? ' selected' : ''}`}
                style={{ background: ENTITY_TYPE_COLORS[type] }}
                onClick={() => setEditType(type)}
                title={type.charAt(0).toUpperCase() + type.slice(1)}
              />
            ))}
          </div>
        </div>
        <div className="form-group">
          <label className="form-label">Description</label>
          <textarea
            className="form-input"
            placeholder="What is this project about?"
            value={editDesc}
            onChange={(e) => setEditDesc(e.target.value)}
          />
        </div>
      </Modal>
    </DetailLayout>
  );
}
