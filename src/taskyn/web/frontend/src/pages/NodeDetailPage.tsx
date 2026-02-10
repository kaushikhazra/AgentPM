import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useNode, useNodeAncestors, useNodeDescendants } from '@/hooks/queries/useNodes';
import { useProject } from '@/hooks/queries/useProjects';
import { useCompany } from '@/hooks/queries/useCompanies';
import { useCreateNode, useStartNode, useCompleteNode, useDeleteNode } from '@/hooks/mutations/useNodeMutations';
import { Button, MarkdownRenderer } from '@/components/atoms';
import { StatCard } from '@/components/molecules';
import { DetailLayout } from '@/components/templates/DetailLayout';
import { Section, Modal } from '@/components/organisms';
import { getNodeTypeUI, getStatusLabel, getChildType, canHaveChildren } from '@/config/methodology-ui';
import { formatDuration } from '@/utils/formatDuration';

function statusClass(status: string): string {
  if (status === 'done' || status === 'approved') return 'done';
  if (status === 'in_progress') return 'progress';
  if (status === 'blocked') return 'blocked';
  if (status === 'backlog' || status === 'draft') return 'backlog';
  if (status === 'ready') return 'ready';
  if (status === 'review' || status === 'in_review') return 'review';
  return 'backlog';
}

export function NodeDetailPage() {
  const { nodeId } = useParams<{ nodeId: string }>();
  const navigate = useNavigate();

  const { data: node } = useNode(nodeId);
  const { data: project } = useProject(node?.project_id);
  const { data: company } = useCompany(project?.company_id ?? undefined);
  const { data: ancestors = [] } = useNodeAncestors(nodeId);
  const { data: allDescendants = [] } = useNodeDescendants(nodeId);

  const createNode = useCreateNode();
  const startNode = useStartNode();
  const completeNode = useCompleteNode();
  const deleteNode = useDeleteNode();

  const [showCreate, setShowCreate] = useState(false);
  const [createTitle, setCreateTitle] = useState('');
  const [createDesc, setCreateDesc] = useState('');
  const [showDelete, setShowDelete] = useState(false);

  if (!node || !project) {
    return (
      <div className="content-wrapper">
        <p className="text-secondary">Loading...</p>
      </div>
    );
  }

  const methodology = project.methodology;
  const typeUI = getNodeTypeUI(methodology, node.node_type);
  const childNodeType = getChildType(methodology, node.node_type);
  const allowsChildren = canHaveChildren(methodology, node.node_type);
  const childTypeUI = childNodeType ? getNodeTypeUI(methodology, childNodeType) : null;

  // Filter descendants to direct children of the expected type
  const children = childNodeType
    ? allDescendants.filter(d => d.node_type === childNodeType)
    : [];

  const rollup = node.rollup;
  const totalChildren = rollup?.total_children ?? children.length;
  const completedChildren = rollup?.completed_children ?? children.filter((c) => c.status === 'done' || c.status === 'approved').length;
  const pct = totalChildren > 0 ? Math.round((completedChildren / totalChildren) * 100) : 0;

  const breadcrumbs = [
    ...(company ? [{ label: company.name, to: '/companies' }] : []),
    { label: project.name, to: `/projects/${project.id}` },
    ...ancestors.map((a) => ({ label: a.title, to: `/nodes/${a.id}` })),
    { label: node.title },
  ];

  const statusLabel = getStatusLabel(methodology, node.status);
  const isInProgress = node.status === 'in_progress';
  const canStart = node.status === 'backlog' || node.status === 'ready' || node.status === 'draft';

  const handleStatusAction = async () => {
    if (canStart) startNode.mutate(node.id);
    else if (isInProgress) completeNode.mutate(node.id);
  };

  const handleCreateChild = async () => {
    if (!createTitle.trim() || !childNodeType) return;
    createNode.mutate(
      {
        project_id: project.id,
        node_type: childNodeType,
        title: createTitle.trim(),
        description: createDesc.trim() || undefined,
        parent_id: node.id,
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
    const parentNode = ancestors[ancestors.length - 1];
    deleteNode.mutate(node.id, {
      onSuccess: () => {
        if (parentNode) navigate(`/nodes/${parentNode.id}`);
        else navigate(`/projects/${project.id}`);
      },
    });
  };

  return (
    <DetailLayout
      breadcrumbs={breadcrumbs}
      title={node.title}
      subtitle={`${node.id.slice(0, 8)} \u2022 ${completedChildren} of ${totalChildren} children completed`}
      badge={
        <span className={`status-badge ${statusClass(node.status)}`}>
          {statusLabel}
        </span>
      }
      headerAction={
        <div className="header-actions">
          <Button variant="secondary" onClick={() => setShowDelete(true)}>
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" strokeWidth="2">
              <path d="M3 6h18" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" /><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            </svg>
            Delete
          </Button>
          {canStart && (
            <Button variant="secondary" onClick={handleStatusAction}>Start</Button>
          )}
          {isInProgress && (
            <Button variant="secondary" onClick={handleStatusAction}>Complete</Button>
          )}
          {allowsChildren && childTypeUI && (
            <Button variant="primary" onClick={() => setShowCreate(true)}>
              <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" strokeWidth="2">
                <path d="M12 5v14" /><path d="M5 12h14" />
              </svg>
              New {childTypeUI.displayName}
            </Button>
          )}
        </div>
      }
    >
      {node.description && (
        <div className="story-description">
          <h3>{typeUI.displayName} Description</h3>
          <MarkdownRenderer content={node.description} />
        </div>
      )}

      <div className="stats-grid">
        <StatCard label="Total Children" value={totalChildren} />
        <StatCard label="Completed" value={completedChildren} />
        <StatCard label="Time Tracked" value={formatDuration(node.actual_time) || '—'} />
        <StatCard label="Progress" value={`${pct}%`} />
      </div>

      {allowsChildren && childTypeUI && (
        <Section
          title={childTypeUI.plural}
          action={
            <span className="section-action" style={{ cursor: 'pointer' }} onClick={() => setShowCreate(true)}>
              + Add {childTypeUI.displayName}
            </span>
          }
        >
          {children.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">
                <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12" /></svg>
              </div>
              <div className="empty-state-title">No {childTypeUI.plural.toLowerCase()} yet</div>
              <div className="empty-state-text">Break this {typeUI.displayName.toLowerCase()} into {childTypeUI.plural.toLowerCase()}</div>
              <Button variant="primary" onClick={() => setShowCreate(true)}>Add {childTypeUI.displayName}</Button>
            </div>
          ) : (
            <div className="work-item-list">
              {children.map((child) => {
                const childDone = child.status === 'done' || child.status === 'approved';
                const grandchildType = getChildType(methodology, child.node_type);
                const grandchildTypeUI = grandchildType ? getNodeTypeUI(methodology, grandchildType) : null;
                const grandchildCount = child.rollup?.total_children ?? 0;
                const grandchildCompleted = child.rollup?.completed_children ?? 0;
                const childPct = grandchildCount > 0 ? Math.round((grandchildCompleted / grandchildCount) * 100) : 0;
                return (
                  <div key={child.id} className={`work-item-card${childDone ? ' completed' : ''}`} onClick={() => navigate(`/nodes/${child.id}`)} style={{ cursor: 'pointer' }}>
                    <div className="work-item-header">
                      <span className="work-item-title">{child.title}</span>
                      <span className="work-item-id">{child.id.slice(0, 8)}</span>
                    </div>
                    <div className="work-item-meta">
                      {grandchildTypeUI && (
                        <span>{grandchildCount} {grandchildCount === 1 ? grandchildTypeUI.displayName.toLowerCase() : grandchildTypeUI.plural.toLowerCase()}</span>
                      )}
                      {child.actual_time > 0 && (
                        <span className="work-item-time">{formatDuration(child.actual_time)}</span>
                      )}
                      <div className="work-item-progress">
                        <div className="work-item-progress-bar">
                          <div className="work-item-progress-fill" style={{ width: `${childPct}%` }} />
                        </div>
                        <span>{childPct}%</span>
                      </div>
                      <span className={`status-badge ${statusClass(child.status)}`}>
                        {getStatusLabel(methodology, child.status)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Section>
      )}

      {allowsChildren && childTypeUI && (
        <Modal open={showCreate} onClose={() => setShowCreate(false)} title={`New ${childTypeUI.displayName}`}
          footer={<><Button variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button><Button variant="primary" onClick={handleCreateChild} disabled={createNode.isPending}>{createNode.isPending ? 'Creating...' : 'Create'}</Button></>}
        >
          <div className="form-group"><label className="form-label">Title</label><input className="form-input" placeholder="Title for the new work item" value={createTitle} onChange={(e) => setCreateTitle(e.target.value)} autoFocus /></div>
          <div className="form-group"><label className="form-label">Description</label><textarea className="form-input" placeholder="Describe the work item..." value={createDesc} onChange={(e) => setCreateDesc(e.target.value)} /></div>
        </Modal>
      )}

      <Modal open={showDelete} onClose={() => setShowDelete(false)} title={`Delete ${typeUI.displayName}`}
        footer={<><Button variant="secondary" onClick={() => setShowDelete(false)}>Cancel</Button><Button variant="danger" onClick={handleDelete} disabled={deleteNode.isPending}>{deleteNode.isPending ? 'Deleting...' : `Delete ${typeUI.displayName}`}</Button></>}
      >
        <p style={{ marginBottom: 16 }}>Are you sure you want to delete <strong>{node.title}</strong>?</p>
        <p className="text-secondary">This will permanently delete {children.length > 0 ? `all ${children.length} children and their` : 'any associated'} time entries. This action cannot be undone.</p>
      </Modal>
    </DetailLayout>
  );
}
