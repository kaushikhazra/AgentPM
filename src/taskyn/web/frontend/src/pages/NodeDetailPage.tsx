import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { nodesApi } from '@/api/nodes';
import { projectsApi } from '@/api/projects';
import { companiesApi } from '@/api/companies';
import { Button } from '@/components/atoms';
import { StatCard } from '@/components/molecules';
import { DetailLayout } from '@/components/templates/DetailLayout';
import { Section, Modal } from '@/components/organisms';
import { getNodeTypeUI, getStatusLabel, getChildType, canHaveChildren } from '@/config/methodology-ui';
import { useToast } from '@/hooks/useToast';
import type { Node, Project, Company } from '@/types';

function statusClass(status: string): string {
  if (status === 'done' || status === 'approved') return 'done';
  if (status === 'in_progress') return 'progress';
  if (status === 'blocked') return 'blocked';
  if (status === 'backlog' || status === 'draft') return 'backlog';
  if (status === 'ready') return 'ready';
  if (status === 'review' || status === 'in_review') return 'review';
  return 'backlog';
}

function formatTime(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

export function NodeDetailPage() {
  const { nodeId } = useParams<{ nodeId: string }>();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [node, setNode] = useState<Node | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [company, setCompany] = useState<Company | null>(null);
  const [ancestors, setAncestors] = useState<Node[]>([]);
  const [children, setChildren] = useState<Node[]>([]);
  const [error, setError] = useState('');

  // Create child modal
  const [showCreate, setShowCreate] = useState(false);
  const [createTitle, setCreateTitle] = useState('');
  const [createDesc, setCreateDesc] = useState('');
  const [creating, setCreating] = useState(false);

  // Delete confirmation modal
  const [showDelete, setShowDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const loadData = useCallback(async () => {
    if (!nodeId) return;
    try {
      const nodeData = await nodesApi.get(nodeId);
      setNode(nodeData);

      const [proj, ancestorList, descendantList] = await Promise.all([
        projectsApi.get(nodeData.project_id),
        nodesApi.getAncestors(nodeId),
        nodesApi.getDescendants(nodeId),
      ]);
      setProject(proj);
      setAncestors(ancestorList);
      // Filter to only show direct children of the expected type
      // Methodology enforces strict hierarchy (e.g., Epic → Story → Task),
      // so descendants of the expected child type are direct children
      const expectedChildType = getChildType(proj.methodology, nodeData.node_type);
      const directChildren = expectedChildType
        ? descendantList.filter(d => d.node_type === expectedChildType)
        : [];
      setChildren(directChildren);

      if (proj.company_id) {
        const comp = await companiesApi.get(proj.company_id);
        setCompany(comp);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    }
  }, [nodeId]);

  useEffect(() => { loadData(); }, [loadData]);

  const handleStatusAction = async () => {
    if (!node) return;
    try {
      if (node.status === 'backlog' || node.status === 'ready' || node.status === 'draft') {
        await nodesApi.start(node.id);
        addToast('success', 'Started');
      } else if (node.status === 'in_progress') {
        await nodesApi.complete(node.id);
        addToast('success', 'Marked as complete');
      }
      await loadData();
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to update status';
      setError(errorMessage);
      addToast('error', errorMessage);
      console.error('Failed to update node status:', e);
    }
  };

  const handleCreateChild = async () => {
    if (!createTitle.trim() || !node || !project) return;
    const childType = getChildType(project.methodology, node.node_type);
    if (!childType) return; // Node type cannot have children
    setCreating(true);
    try {
      await nodesApi.create({
        project_id: project.id,
        node_type: childType,
        title: createTitle.trim(),
        description: createDesc.trim() || undefined,
        parent_id: node.id,
      });
      setShowCreate(false);
      setCreateTitle('');
      setCreateDesc('');
      addToast('success', `${getNodeTypeUI(project.methodology, childType).displayName} created successfully`);
      await loadData();
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to create';
      setError(errorMessage);
      addToast('error', errorMessage);
      console.error('Failed to create child node:', e);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async () => {
    if (!node || !project) return;
    setDeleting(true);
    try {
      await nodesApi.delete(node.id);
      addToast('success', `${getNodeTypeUI(project.methodology, node.node_type).displayName} deleted successfully`);
      // Navigate to parent if exists, otherwise to project
      const parentNode = ancestors[ancestors.length - 1];
      if (parentNode) {
        navigate(`/nodes/${parentNode.id}`);
      } else {
        navigate(`/projects/${project.id}`);
      }
    } catch (e: unknown) {
      const errorMessage = e instanceof Error ? e.message : 'Failed to delete';
      setError(errorMessage);
      addToast('error', errorMessage);
      console.error('Failed to delete node:', e);
      setShowDelete(false);
    } finally {
      setDeleting(false);
    }
  };

  if (!node || !project) {
    return (
      <div className="content-wrapper">
        {error ? (
          <p style={{ color: 'var(--status-blocked)' }}>{error}</p>
        ) : (
          <p className="text-secondary">Loading...</p>
        )}
      </div>
    );
  }

  const methodology = project.methodology;
  const typeUI = getNodeTypeUI(methodology, node.node_type);
  const childNodeType = getChildType(methodology, node.node_type);
  const allowsChildren = canHaveChildren(methodology, node.node_type);
  const childTypeUI = childNodeType ? getNodeTypeUI(methodology, childNodeType) : null;
  const rollup = node.rollup;
  const totalChildren = rollup?.total_children ?? children.length;
  const completedChildren = rollup?.completed_children ?? children.filter((c) => c.status === 'done' || c.status === 'approved').length;
  const totalTime = rollup?.total_time_minutes ?? 0;
  const pct = totalChildren > 0 ? Math.round((completedChildren / totalChildren) * 100) : 0;

  // Build breadcrumbs from ancestors
  const breadcrumbs = [
    ...(company ? [{ label: company.name, to: '/companies' }] : []),
    { label: project.name, to: `/projects/${project.id}` },
    ...ancestors.map((a) => ({
      label: a.title,
      to: `/nodes/${a.id}`,
    })),
    { label: node.title },
  ];

  const statusLabel = getStatusLabel(methodology, node.status);
  const isInProgress = node.status === 'in_progress';
  const canStart = node.status === 'backlog' || node.status === 'ready' || node.status === 'draft';

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
      {error && <p style={{ color: 'var(--status-blocked)', marginBottom: 16 }}>{error}</p>}

      {/* Description */}
      {node.description && (
        <div className="story-description">
          <h3>{typeUI.displayName} Description</h3>
          <p>{node.description}</p>
        </div>
      )}

      <div className="stats-grid">
        <StatCard label="Total Children" value={totalChildren} />
        <StatCard label="Completed" value={completedChildren} />
        <StatCard label="Time Tracked" value={formatTime(totalTime)} />
        <StatCard label="Progress" value={`${pct}%`} />
      </div>

      {allowsChildren && childTypeUI && (
        <Section
          title={childTypeUI.plural}
          action={
            <span
              className="section-action"
              style={{ cursor: 'pointer' }}
              onClick={() => setShowCreate(true)}
            >
              + Add {childTypeUI.displayName}
            </span>
          }
        >
          {children.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">
                <svg viewBox="0 0 24 24">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <div className="empty-state-title">No {childTypeUI.plural.toLowerCase()} yet</div>
              <div className="empty-state-text">Break this {typeUI.displayName.toLowerCase()} into {childTypeUI.plural.toLowerCase()}</div>
              <Button variant="primary" onClick={() => setShowCreate(true)}>Add {childTypeUI.displayName}</Button>
            </div>
          ) : (
            <div className="task-checklist">
              {children.map((child) => {
                const childDone = child.status === 'done' || child.status === 'approved';
                const childTime = child.time_entries?.reduce(
                  (sum, te) => sum + (te.duration_minutes ?? 0), 0
                ) ?? 0;
                return (
                  <div
                    key={child.id}
                    className={`task-check-item${childDone ? ' completed' : ''}`}
                    onClick={() => navigate(`/nodes/${child.id}`)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="task-check-content">
                      <div className="task-check-title">{child.title}</div>
                      <div className="task-check-meta">
                        {getStatusLabel(methodology, child.status)}
                      </div>
                    </div>
                    <div className="task-check-right">
                      {childTime > 0 && (
                        <span className="task-time-badge">{formatTime(childTime)}</span>
                      )}
                      {!childDone && (
                        <span className={`status-badge ${statusClass(child.status)}`}>
                          {getStatusLabel(methodology, child.status)}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Section>
      )}

      {/* Create Child Modal */}
      {allowsChildren && childTypeUI && (
        <Modal
          open={showCreate}
          onClose={() => setShowCreate(false)}
          title={`New ${childTypeUI.displayName}`}
          footer={
            <>
              <Button variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button variant="primary" onClick={handleCreateChild} disabled={creating}>
                {creating ? 'Creating...' : 'Create'}
              </Button>
            </>
          }
        >
          <div className="form-group">
            <label className="form-label">Title</label>
            <input
              className="form-input"
              placeholder="Title for the new work item"
              value={createTitle}
              onChange={(e) => setCreateTitle(e.target.value)}
              autoFocus
            />
          </div>
          <div className="form-group">
            <label className="form-label">Description</label>
            <textarea
              className="form-input"
              placeholder="Describe the work item..."
              value={createDesc}
              onChange={(e) => setCreateDesc(e.target.value)}
            />
          </div>
        </Modal>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        open={showDelete}
        onClose={() => setShowDelete(false)}
        title={`Delete ${typeUI.displayName}`}
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowDelete(false)}>Cancel</Button>
            <Button variant="danger" onClick={handleDelete} disabled={deleting}>
              {deleting ? 'Deleting...' : `Delete ${typeUI.displayName}`}
            </Button>
          </>
        }
      >
        <p style={{ marginBottom: 16 }}>
          Are you sure you want to delete <strong>{node.title}</strong>?
        </p>
        <p className="text-secondary">
          This will permanently delete {children.length > 0 ? `all ${children.length} children and their` : 'any associated'} time entries.
          This action cannot be undone.
        </p>
      </Modal>
    </DetailLayout>
  );
}
