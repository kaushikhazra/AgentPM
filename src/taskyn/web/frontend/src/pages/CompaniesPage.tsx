import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCompanies } from '@/hooks/queries/useCompanies';
import { useProjects } from '@/hooks/queries/useProjects';
import { useCreateCompany, useUpdateCompany, useDeleteCompany } from '@/hooks/mutations/useCompanyMutations';
import { Button, Icon, MarkdownRenderer } from '@/components/atoms';
import { StatCard } from '@/components/molecules';
import { Modal } from '@/components/organisms';
import { ENTITY_TYPES, ENTITY_TYPE_COLORS, type EntityType, type Company } from '@/types';

function formatTime(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  return `${Math.round(minutes / 60)}h`;
}

function getTypeColor(type: EntityType | undefined): string {
  return ENTITY_TYPE_COLORS[type ?? 'discovery'];
}

export function CompaniesPage() {
  const navigate = useNavigate();
  const { data: companies = [], isLoading: loading, error: queryError } = useCompanies(true);
  const { data: projects = [] } = useProjects({ include_stats: true });

  const createCompany = useCreateCompany();
  const updateCompany = useUpdateCompany();
  const deleteCompany = useDeleteCompany();

  // Modal states
  const [showCreate, setShowCreate] = useState(false);
  const [showView, setShowView] = useState<Company | null>(null);
  const [showEdit, setShowEdit] = useState<Company | null>(null);
  const [createName, setCreateName] = useState('');
  const [createDesc, setCreateDesc] = useState('');
  const [createType, setCreateType] = useState<EntityType>('discovery');

  // Edit form states
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editType, setEditType] = useState<EntityType>('discovery');

  const error = queryError?.message ?? '';

  const handleCreate = async () => {
    if (!createName.trim()) return;
    createCompany.mutate(
      { name: createName.trim(), description: createDesc.trim() || undefined, type: createType },
      {
        onSuccess: () => {
          setShowCreate(false);
          setCreateName('');
          setCreateDesc('');
          setCreateType('discovery');
        },
      },
    );
  };

  const handleDelete = async (id: string) => {
    deleteCompany.mutate(id, {
      onSuccess: () => setShowView(null),
    });
  };

  const openEdit = (company: Company) => {
    setEditName(company.name);
    setEditDesc(company.description ?? '');
    setEditType(company.type ?? 'discovery');
    setShowView(null);
    setShowEdit(company);
  };

  const handleUpdate = async () => {
    if (!showEdit || !editName.trim()) return;
    updateCompany.mutate(
      { id: showEdit.id, data: { name: editName.trim(), description: editDesc.trim() || undefined, type: editType } },
      {
        onSuccess: () => setShowEdit(null),
      },
    );
  };

  const totalProjects = projects.length;
  const totalNodes = companies.reduce((sum, c) => sum + (c.stats?.total_nodes ?? 0), 0);
  const totalTime = companies.reduce((sum, c) => sum + (c.stats?.total_time_minutes ?? 0), 0);

  const companyProjects = (companyId: string) =>
    projects.filter((p) => p.company_id === companyId);

  return (
    <div className="content-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Companies</h1>
          <p className="page-subtitle">Manage your organizations and their projects</p>
        </div>
        <Button variant="primary" onClick={() => setShowCreate(true)}>
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" strokeWidth="2"><path d="M12 5v14" /><path d="M5 12h14" /></svg>
          New Company
        </Button>
      </div>

      {error && <p style={{ color: 'var(--status-blocked)', marginBottom: 16 }}>{error}</p>}

      {loading && <p className="text-secondary">Loading companies...</p>}

      <div className="stats-grid">
        <StatCard label="Total Companies" value={companies.length} />
        <StatCard label="Total Projects" value={totalProjects} />
        <StatCard label="Total Tasks" value={totalNodes} />
        <StatCard label="Time Tracked" value={formatTime(totalTime)} />
      </div>

      <div className="companies-grid">
        {companies.map((company) => {
          const cp = companyProjects(company.id);
          return (
            <div
              key={company.id}
              className="company-card"
              onClick={() => setShowView(company)}
            >
              <div className="company-card-header">
                <div className="company-icon" style={{ background: getTypeColor(company.type) }}>
                  {company.name[0]?.toUpperCase()}
                </div>
                <div className="company-info">
                  <h3 className="company-name">{company.name}</h3>
                  {company.description && (
                    <MarkdownRenderer content={company.description} className="company-description" />
                  )}
                </div>
              </div>
              <div className="company-stats">
                <div className="company-stat">
                  <div className="company-stat-value">{cp.length}</div>
                  <div className="company-stat-label">Projects</div>
                </div>
                <div className="company-stat">
                  <div className="company-stat-value">{company.stats?.total_nodes ?? 0}</div>
                  <div className="company-stat-label">Tasks</div>
                </div>
                <div className="company-stat">
                  <div className="company-stat-value">{formatTime(company.stats?.total_time_minutes ?? 0)}</div>
                  <div className="company-stat-label">Tracked</div>
                </div>
                <div className="company-stat">
                  <div className="company-stat-value">{company.stats?.completion_percentage ?? 0}%</div>
                  <div className="company-stat-label">Done</div>
                </div>
              </div>
              <div className="company-projects">
                {cp.slice(0, 3).map((p) => (
                  <span key={p.id} className="company-project-tag">
                    <span className="project-tag-dot" style={{ background: getTypeColor(p.type) }} />
                    {p.name}
                  </span>
                ))}
                {cp.length > 3 && (
                  <span className="company-project-tag">+{cp.length - 3} more</span>
                )}
              </div>
            </div>
          );
        })}

        <div className="add-company-card" onClick={() => setShowCreate(true)}>
          <div className="add-company-icon">
            <svg viewBox="0 0 24 24"><path d="M12 5v14" /><path d="M5 12h14" /></svg>
          </div>
          <span style={{ fontWeight: 500 }}>Add New Company</span>
          <span style={{ fontSize: 12, marginTop: 4 }}>Create a new organization</span>
        </div>
      </div>

      {/* Create Company Modal */}
      <Modal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title="New Company"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button variant="primary" onClick={handleCreate} disabled={createCompany.isPending}>
              {createCompany.isPending ? 'Creating...' : 'Create Company'}
            </Button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label">Company Name</label>
          <input
            className="form-input"
            placeholder="e.g., Personal Projects, Acme Corp"
            value={createName}
            onChange={(e) => setCreateName(e.target.value)}
            autoFocus
          />
        </div>
        <div className="form-group">
          <label className="form-label">Description</label>
          <textarea
            className="form-input"
            placeholder="What kind of projects will this company contain?"
            value={createDesc}
            onChange={(e) => setCreateDesc(e.target.value)}
          />
          <p className="form-hint">A brief description helps you organize your work.</p>
        </div>
        <div className="form-group">
          <label className="form-label">Lifecycle Stage</label>
          <div className="color-picker">
            {ENTITY_TYPES.map((type) => (
              <div
                key={type}
                className={`color-option${createType === type ? ' selected' : ''}`}
                style={{ background: ENTITY_TYPE_COLORS[type] }}
                onClick={() => setCreateType(type)}
                title={type.charAt(0).toUpperCase() + type.slice(1)}
              />
            ))}
          </div>
        </div>
      </Modal>

      {/* View Company Modal */}
      <Modal
        open={!!showView}
        onClose={() => setShowView(null)}
        title="Company Details"
        footer={
          <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
            <Button
              variant="ghost"
              onClick={() => showView && handleDelete(showView.id)}
            >
              <Icon name="trash" size={18} />
            </Button>
            <div style={{ display: 'flex', gap: 12 }}>
              <Button variant="secondary" onClick={() => setShowView(null)}>Close</Button>
              <Button
                variant="secondary"
                onClick={() => showView && openEdit(showView)}
              >
                <Icon name="edit" size={16} />
                Edit
              </Button>
              <Button
                variant="primary"
                onClick={() => {
                  setShowView(null);
                  navigate('/projects');
                }}
              >
                View Projects
              </Button>
            </div>
          </div>
        }
      >
        {showView && (
          <>
            <div className="company-detail-header">
              <div
                className="company-detail-icon"
                style={{ background: getTypeColor(showView.type) }}
              >
                {showView.name[0]?.toUpperCase()}
              </div>
              <div className="company-detail-info">
                <h2>{showView.name}</h2>
                {showView.description && <MarkdownRenderer content={showView.description} />}
              </div>
            </div>

            <div className="detail-stats">
              <div className="detail-stat">
                <div className="detail-stat-value">{companyProjects(showView.id).length}</div>
                <div className="detail-stat-label">Projects</div>
              </div>
              <div className="detail-stat">
                <div className="detail-stat-value">{showView.stats?.total_nodes ?? 0}</div>
                <div className="detail-stat-label">Tasks</div>
              </div>
              <div className="detail-stat">
                <div className="detail-stat-value">{formatTime(showView.stats?.total_time_minutes ?? 0)}</div>
                <div className="detail-stat-label">Tracked</div>
              </div>
              <div className="detail-stat">
                <div className="detail-stat-value">{showView.stats?.completion_percentage ?? 0}%</div>
                <div className="detail-stat-label">Complete</div>
              </div>
            </div>

            <div className="detail-section">
              <h4 className="detail-section-title">Projects</h4>
              <div className="project-list">
                {companyProjects(showView.id).length === 0 ? (
                  <p style={{ color: 'var(--text-tertiary)', fontSize: 13 }}>No projects yet</p>
                ) : (
                  companyProjects(showView.id).map((p) => (
                    <div
                      key={p.id}
                      className="project-list-item"
                      onClick={() => {
                        setShowView(null);
                        navigate(`/projects/${p.id}`);
                      }}
                    >
                      <div className="project-list-dot" style={{ background: getTypeColor(p.type) }} />
                      <div className="project-list-info">
                        <div className="project-list-name">{p.name}</div>
                        <div className="project-list-meta">{p.methodology}</div>
                      </div>
                      <div className="project-list-progress">
                        <div
                          className="project-list-progress-fill"
                          style={{ width: `${p.stats?.completion_percentage ?? 0}%` }}
                        />
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </>
        )}
      </Modal>

      {/* Edit Company Modal */}
      <Modal
        open={!!showEdit}
        onClose={() => setShowEdit(null)}
        title="Edit Company"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowEdit(null)}>Cancel</Button>
            <Button variant="primary" onClick={handleUpdate} disabled={updateCompany.isPending}>
              {updateCompany.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label">Company Name</label>
          <input
            className="form-input"
            placeholder="e.g., Personal Projects, Acme Corp"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            autoFocus
          />
        </div>
        <div className="form-group">
          <label className="form-label">Description</label>
          <textarea
            className="form-input"
            placeholder="What kind of projects will this company contain?"
            value={editDesc}
            onChange={(e) => setEditDesc(e.target.value)}
          />
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
      </Modal>
    </div>
  );
}
