import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/api/client';

interface StepState {
  companyName: string;
  companyId: string | null;
  projectName: string;
  projectId: string | null;
}

export function OnboardingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [activeStep, setActiveStep] = useState(0);
  const [state, setState] = useState<StepState>({
    companyName: '',
    companyId: null,
    projectName: '',
    projectId: null,
  });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const firstName = user?.name?.split(' ')[0] ?? 'there';

  async function handleCreateCompany(e: FormEvent) {
    e.preventDefault();
    setError('');
    if (!state.companyName.trim()) {
      setError('Please enter a company name.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post<{ id: string }>('/companies', {
        name: state.companyName.trim(),
      });
      setState((s) => ({ ...s, companyId: res.id }));
      setActiveStep(1);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Failed to create company.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCreateProject(e: FormEvent) {
    e.preventDefault();
    setError('');
    if (!state.projectName.trim()) {
      setError('Please enter a project name.');
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.post<{ id: string }>('/projects', {
        company_id: state.companyId,
        name: state.projectName.trim(),
        methodology: 'classic_agile',
      });
      setState((s) => ({ ...s, projectId: res.id }));
      setActiveStep(2);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Failed to create project.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  }

  function handleFinish() {
    navigate('/dashboard', { replace: true });
  }

  function handleSkip() {
    navigate('/dashboard', { replace: true });
  }

  const steps = [
    {
      title: 'Create your organization',
      desc: 'Set up your company or team workspace',
      action: state.companyId ? 'Completed' : 'Get started',
    },
    {
      title: 'Create your first project',
      desc: 'Organize your work into a project',
      action: state.projectId ? 'Completed' : 'Create project',
    },
    {
      title: 'Start working',
      desc: 'Add tasks and track your progress',
      action: 'Go to dashboard',
    },
  ];

  function getStepClass(idx: number) {
    if (idx < activeStep) return 'onboarding-step completed';
    if (idx === activeStep) return 'onboarding-step active';
    return 'onboarding-step';
  }

  function getProgressClass(idx: number) {
    if (idx < activeStep) return 'onboarding-progress-dot completed';
    if (idx === activeStep) return 'onboarding-progress-dot active';
    return 'onboarding-progress-dot';
  }

  return (
    <div className="onboarding-container">
      {/* Header */}
      <div className="onboarding-header">
        <div className="onboarding-icon">T</div>
        <h1 className="onboarding-title">Welcome, {firstName}!</h1>
        <p className="onboarding-subtitle">
          Let&apos;s get you set up in just a few steps.
          <br />
          You&apos;ll be managing projects in no time.
        </p>
      </div>

      {/* Progress dots */}
      <div className="onboarding-progress">
        {steps.map((_, idx) => (
          <div key={idx} className={getProgressClass(idx)} />
        ))}
      </div>

      {error && (
        <div className="login-error" style={{ marginBottom: 16 }}>
          {error}
        </div>
      )}

      {/* Steps */}
      <div className="onboarding-steps">
        {steps.map((step, idx) => (
          <div
            key={idx}
            className={getStepClass(idx)}
            onClick={() => {
              if (idx === activeStep && idx === 2) handleFinish();
            }}
          >
            <div className="onboarding-step-number">
              {idx < activeStep ? (
                <svg
                  viewBox="0 0 24 24"
                  width="16"
                  height="16"
                  stroke="currentColor"
                  fill="none"
                  strokeWidth="3"
                >
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              ) : (
                idx + 1
              )}
            </div>
            <div className="onboarding-step-content">
              <div className="onboarding-step-title">{step.title}</div>
              <div className="onboarding-step-desc">{step.desc}</div>
              {idx === activeStep && (
                <div className="onboarding-step-action">{step.action}</div>
              )}

              {/* Inline form for step 0: Create company */}
              {idx === 0 && activeStep === 0 && (
                <form
                  className="onboarding-inline-form"
                  onSubmit={handleCreateCompany}
                >
                  <div className="form-group">
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. Acme Corp"
                      value={state.companyName}
                      onChange={(e) =>
                        setState((s) => ({
                          ...s,
                          companyName: e.target.value,
                        }))
                      }
                      autoFocus
                    />
                  </div>
                  <button
                    type="submit"
                    className="login-button"
                    disabled={submitting}
                    style={{ padding: '10px 16px', fontSize: 13 }}
                  >
                    {submitting ? 'Creating...' : 'Create Organization'}
                  </button>
                </form>
              )}

              {/* Inline form for step 1: Create project */}
              {idx === 1 && activeStep === 1 && (
                <form
                  className="onboarding-inline-form"
                  onSubmit={handleCreateProject}
                >
                  <div className="form-group">
                    <input
                      type="text"
                      className="form-input"
                      placeholder="e.g. Website Redesign"
                      value={state.projectName}
                      onChange={(e) =>
                        setState((s) => ({
                          ...s,
                          projectName: e.target.value,
                        }))
                      }
                      autoFocus
                    />
                  </div>
                  <button
                    type="submit"
                    className="login-button"
                    disabled={submitting}
                    style={{ padding: '10px 16px', fontSize: 13 }}
                  >
                    {submitting ? 'Creating...' : 'Create Project'}
                  </button>
                </form>
              )}
            </div>
            <div className="onboarding-step-arrow">
              <svg viewBox="0 0 24 24">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </div>
          </div>
        ))}
      </div>

      {/* Skip link */}
      <div className="onboarding-skip">
        <button type="button" onClick={handleSkip}>
          Skip for now, I&apos;ll set up later
        </button>
      </div>
    </div>
  );
}
