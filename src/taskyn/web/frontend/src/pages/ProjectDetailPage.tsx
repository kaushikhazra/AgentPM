import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useProject } from '@/hooks/queries/useProjects';
import { useCompany } from '@/hooks/queries/useCompanies';
import { useNodes } from '@/hooks/queries/useNodes';
import { useCreateNode } from '@/hooks/mutations/useNodeMutations';
import { useDeleteProject } from '@/hooks/mutations/useProjectMutations';
import { Button } from '@/components/atoms';
import { StatCard } from '@/components/molecules';
import { DetailLayout } from '@/components/templates/DetailLayout';
import { Section, Modal } from '@/components/organisms';
import { METHODOLOGY_UI, getNodeTypeUI, getStatusLabel, getChildType } from '@/config/methodology-ui';
import type { Node } from '@/types';

function statusClass(status: string): string {
  if (status === 'done' || status === 'approved') return 'done';
  if (status === 'in_progress') return 'progress';
  if (status === 'blocked') return 'blocked';
  if (status === 'backlog' || status === 'draft') return 'backlog';
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
  const deleteProject = useDeleteProject();

  const [tab, setTab] = useState('all');
  const [showCreate, setShowCreate] = useState(false);
  const [createTitle, setCreateTitle] = useState('');
  const [createType, setCreateType] = useState('');
  const [createDesc, setCreateDesc] = useState('');
  const [showDelete, setShowDelete] = useState(false);

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
      : rootNodes.filter((n: Node) => n.status === 'done' || n.status === 'approved');

  const nodesByType: Record<string, number> = {};
  nodes.forEach((n: Node) => {
    nodesByType[n.node_type] = (nodesByType[n.node_type] ?? 0) + 1;
  });
  const totalDone = nodes.filter((n: Node) => n.status === 'done' || n.status === 'approved').length;
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

  return (
    <DetailLayout
      breadcrumbs={breadcrumbs}
      title={project.name}
      subtitle={project.description ?? undefined}
      headerAction={
        <div className="header-actions">
          <Button variant="secondary" onClick={() => setShowDelete(true)}>
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" strokeWidth="2">
              <path d="M3 6h18" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" /><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            </svg>
            Delete
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
              const childType = getChildType(methodology, node.node_type);
              const childTypeUI = childType ? getNodeTypeUI(methodology, childType) : null;
              const grandchildType = childType ? getChildType(methodology, childType) : null;
              const grandchildTypeUI = grandchildType ? getNodeTypeUI(methodology, grandchildType) : null;
              const directChildren = nodes.filter((n: Node) => n.parent_id === node.id);
              const childCount = directChildren.length;
              const grandchildCount = grandchildType
                ? nodes.filter((n: Node) => n.node_type === grandchildType && directChildren.some((c: Node) => c.id === n.parent_id)).length
                : 0;

              return (
                <div key={node.id} className="work-item-card" onClick={() => navigate(`/nodes/${node.id}`)}>
                  <div className="work-item-header">
                    <span className="work-item-title">{node.title}</span>
                    <span className="work-item-id">{node.id.slice(0, 8)}</span>
                  </div>
                  <div className="work-item-meta">
                    {childTypeUI && (
                      <span>{childCount} {childCount === 1 ? childTypeUI.displayName.toLowerCase() : childTypeUI.plural.toLowerCase()}</span>
                    )}
                    {grandchildTypeUI && (
                      <span>{grandchildCount} {grandchildCount === 1 ? grandchildTypeUI.displayName.toLowerCase() : grandchildTypeUI.plural.toLowerCase()}</span>
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
    </DetailLayout>
  );
}
