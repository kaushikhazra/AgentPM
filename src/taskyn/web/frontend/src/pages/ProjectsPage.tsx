import { useEffect, useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { companiesApi } from '@/api/companies';
import { projectsApi } from '@/api/projects';
import { Button } from '@/components/atoms';
import { StatCard } from '@/components/molecules';
import { Modal } from '@/components/organisms';
import type { Company, Project } from '@/types';

const GRADIENTS = [
  'var(--gradient-primary)',
  'var(--gradient-secondary)',
  'linear-gradient(135deg, var(--accent-mint), var(--accent-sage))',
  'linear-gradient(135deg, var(--accent-sky), var(--accent-primary))',
  'linear-gradient(135deg, var(--accent-peach), var(--accent-blush))',
  'linear-gradient(135deg, var(--accent-butter), var(--accent-mint))',
];

export function ProjectsPage() {
  const navigate = useNavigate();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<string>('all');
  const [filterOpen, setFilterOpen] = useState(false);
  const [error, setError] = useState('');
  const filterRef = useRef<HTMLDivElement>(null);

  // Create modal
  const [showCreate, setShowCreate] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createCompanyId, setCreateCompanyId] = useState('');
  const [createMethodology, setCreateMethodology] = useState('classic_agile');
  const [createDesc, setCreateDesc] = useState('');
  const [creating, setCreating] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [companyList, projectList] = await Promise.all([
        companiesApi.list(),
        projectsApi.list({ include_stats: true }),
      ]);
      setCompanies(companyList);
      setProjects(projectList);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (filterRef.current && !filterRef.current.contains(e.target as HTMLElement)) {
        setFilterOpen(false);
      }
    };
    document.addEventListener('click', handler);
    return () => document.removeEventListener('click', handler);
  }, []);

  const handleCreate = async () => {
    if (!createName.trim() || !createCompanyId) return;
    setCreating(true);
    try {
      await projectsApi.create({
        name: createName.trim(),
        company_id: createCompanyId,
        methodology: createMethodology,
        description: createDesc.trim() || undefined,
      });
      setShowCreate(false);
      setCreateName('');
      setCreateDesc('');
      setCreateCompanyId('');
      await loadData();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to create');
    } finally {
      setCreating(false);
    }
  };

  const filtered = selectedCompany === 'all'
    ? projects
    : projects.filter((p) => p.company_id === selectedCompany);

  const companyName = (id: string | null) =>
    companies.find((c) => c.id === id)?.name ?? '';

  const selectedLabel = selectedCompany === 'all'
    ? 'all companies'
    : companies.find((c) => c.id === selectedCompany)?.name?.toLowerCase() ?? 'all';

  const activeCount = filtered.filter((p) => p.status === 'active').length;
  const totalNodes = filtered.reduce((sum, p) => {
    const nodeTotal = p.stats?.total_nodes
      ? Object.values(p.stats.total_nodes).reduce((a, b) => a + b, 0)
      : 0;
    return sum + nodeTotal;
  }, 0);

  return (
    <div className="content-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Projects</h1>
          <div className="subtitle-with-filter">
            <span>from</span>
            <div
              ref={filterRef}
              className={`filter-badge${filterOpen ? ' open' : ''}`}
              onClick={() => setFilterOpen(!filterOpen)}
            >
              <span className="filter-badge-text">{selectedLabel}</span>
              <svg className="filter-badge-icon" viewBox="0 0 24 24">
                <polyline points="6 9 12 15 18 9" />
              </svg>
              <div className="filter-dropdown">
                <div
                  className={`filter-dropdown-item${selectedCompany === 'all' ? ' selected' : ''}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedCompany('all');
                    setFilterOpen(false);
                  }}
                >
                  <div
                    className="filter-dropdown-icon"
                    style={{ background: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}
                  >
                    *
                  </div>
                  <span className="filter-dropdown-label">All Companies</span>
                  <span className="filter-dropdown-count">{projects.length}</span>
                </div>
                {companies.map((c, idx) => (
                  <div
                    key={c.id}
                    className={`filter-dropdown-item${selectedCompany === c.id ? ' selected' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedCompany(c.id);
                      setFilterOpen(false);
                    }}
                  >
                    <div
                      className="filter-dropdown-icon"
                      style={{ background: GRADIENTS[idx % GRADIENTS.length] }}
                    >
                      {c.name[0]?.toUpperCase()}
                    </div>
                    <span className="filter-dropdown-label">{c.name}</span>
                    <span className="filter-dropdown-count">
                      {projects.filter((p) => p.company_id === c.id).length}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
        <Button variant="primary" onClick={() => setShowCreate(true)}>
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" strokeWidth="2">
            <path d="M12 5v14" /><path d="M5 12h14" />
          </svg>
          New Project
        </Button>
      </div>

      {error && <p style={{ color: 'var(--status-blocked)', marginBottom: 16 }}>{error}</p>}

      <div className="stats-grid">
        <StatCard label="Total Projects" value={filtered.length} />
        <StatCard label="Active" value={activeCount} />
        <StatCard label="Total Tasks" value={totalNodes} />
        <StatCard
          label="Avg Progress"
          value={
            filtered.length > 0
              ? `${Math.round(filtered.reduce((s, p) => s + (p.stats?.completion_percentage ?? 0), 0) / filtered.length)}%`
              : '0%'
          }
        />
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <svg viewBox="0 0 24 24">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <div className="empty-state-title">No projects yet</div>
          <div className="empty-state-text">Create your first project to get started</div>
          <Button variant="primary" onClick={() => setShowCreate(true)}>New Project</Button>
        </div>
      ) : (
        <div className="projects-grid">
          {filtered.map((project, idx) => {
            const pct = project.stats?.completion_percentage ?? 0;
            const nodesByType = project.stats?.total_nodes ?? {};
            return (
              <div
                key={project.id}
                className="project-card"
                onClick={() => navigate(`/projects/${project.id}`)}
              >
                <div className="project-card-header">
                  <div
                    className="project-icon"
                    style={{ background: GRADIENTS[idx % GRADIENTS.length] }}
                  >
                    {project.name[0]?.toUpperCase()}
                  </div>
                  <div>
                    <div className="project-name">{project.name}</div>
                    <div className="project-company">{companyName(project.company_id)}</div>
                  </div>
                </div>
                {project.description && (
                  <p className="project-desc">{project.description}</p>
                )}
                <div className="project-stats">
                  {Object.entries(nodesByType).map(([type, count]) => (
                    <span key={type} className="project-stat">
                      {count} {type}{count !== 1 ? 's' : ''}
                    </span>
                  ))}
                </div>
                <div className="project-progress">
                  <div className="project-progress-bar">
                    <div className="project-progress-fill" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="project-progress-text">{pct}%</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Project Modal */}
      <Modal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title="New Project"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button variant="primary" onClick={handleCreate} disabled={creating}>
              {creating ? 'Creating...' : 'Create Project'}
            </Button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label">Project Name</label>
          <input
            className="form-input"
            placeholder="e.g., Website Redesign, Mobile App"
            value={createName}
            onChange={(e) => setCreateName(e.target.value)}
            autoFocus
          />
        </div>
        <div className="form-group">
          <label className="form-label">Company</label>
          <select
            className="form-select"
            value={createCompanyId}
            onChange={(e) => setCreateCompanyId(e.target.value)}
          >
            <option value="">Select a company...</option>
            {companies.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <p className="form-hint">Which company does this project belong to?</p>
        </div>
        <div className="form-group">
          <label className="form-label">Methodology</label>
          <select
            className="form-select"
            value={createMethodology}
            onChange={(e) => setCreateMethodology(e.target.value)}
          >
            <option value="classic_agile">Classic Agile</option>
            <option value="spec_driven">Spec Driven</option>
          </select>
          <p className="form-hint">Defines the workflow: node types, statuses, and transitions.</p>
        </div>
        <div className="form-group">
          <label className="form-label">Description</label>
          <textarea
            className="form-input"
            placeholder="What is this project about?"
            value={createDesc}
            onChange={(e) => setCreateDesc(e.target.value)}
          />
        </div>
      </Modal>
    </div>
  );
}
