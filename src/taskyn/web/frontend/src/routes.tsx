import { lazy, Suspense, useEffect, type ReactNode } from 'react';
import { useNavigate, type RouteObject } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { AppShell } from '@/components/templates/AppShell';
import { ErrorBoundary } from '@/components/organisms';

/* ============================================================
   Eager imports — auth pages load instantly, no async gates
   ============================================================ */
import { LoginPage } from '@/pages/LoginPage';
import { SignupPage } from '@/pages/SignupPage';
import { OnboardingPage } from '@/pages/OnboardingPage';

/* ============================================================
   Lazy-loaded pages — behind ProtectedRoute auth gate anyway
   ============================================================ */
const DashboardPage = lazy(() => import('@/pages/DashboardPage').then((m) => ({ default: m.DashboardPage })));
const CompaniesPage = lazy(() => import('@/pages/CompaniesPage').then((m) => ({ default: m.CompaniesPage })));
const ProjectsPage = lazy(() => import('@/pages/ProjectsPage').then((m) => ({ default: m.ProjectsPage })));
const ProjectDetailPage = lazy(() => import('@/pages/ProjectDetailPage').then((m) => ({ default: m.ProjectDetailPage })));
const NodeDetailPage = lazy(() => import('@/pages/NodeDetailPage').then((m) => ({ default: m.NodeDetailPage })));
const KanbanPage = lazy(() => import('@/pages/KanbanPage').then((m) => ({ default: m.KanbanPage })));
const PlannerPage = lazy(() => import('@/pages/PlannerPage').then((m) => ({ default: m.PlannerPage })));
const TrackerPage = lazy(() => import('@/pages/TrackerPage').then((m) => ({ default: m.TrackerPage })));
const SettingsPage = lazy(() => import('@/pages/SettingsPage').then((m) => ({ default: m.SettingsPage })));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage').then((m) => ({ default: m.NotFoundPage })));

/* ============================================================
   Loading fallback
   ============================================================ */
function LoadingFallback() {
  return (
    <div className="auth-layout">
      <p className="text-secondary">Loading...</p>
    </div>
  );
}

/* ============================================================
   Redirect — hard navigation via window.location.
   React Router v7's createBrowserRouter transitions are
   unreliable for cross-route redirects triggered by state
   changes. A full page navigation is simple and bulletproof.
   ============================================================ */
function Redirect({ to }: { to: string }) {
  useEffect(() => {
    window.location.replace(to);
  }, [to]);
  return <LoadingFallback />;
}

/* ============================================================
   Protected Route — waits for auth, hard-redirects to login
   ============================================================ */
function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) return <LoadingFallback />;
  if (!user) return <Redirect to="/login" />;

  return (
    <AppShell>
      <ErrorBoundary>
        <Suspense fallback={<LoadingFallback />}>{children}</Suspense>
      </ErrorBoundary>
    </AppShell>
  );
}

/* ============================================================
   Guest Route — renders immediately, no loading gate.
   Redirects only when auth confirms a logged-in user.
   ============================================================ */
function GuestRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && user) {
      navigate('/dashboard', { replace: true });
    }
  }, [loading, user, navigate]);

  return <ErrorBoundary>{children}</ErrorBoundary>;
}

/* ============================================================
   Root redirect — auth-aware, no blind redirect chain
   ============================================================ */
function RootRedirect() {
  const { user, loading } = useAuth();

  if (loading) return <LoadingFallback />;
  return <Redirect to={user ? '/dashboard' : '/login'} />;
}

/* ============================================================
   Route definitions
   ============================================================ */
export const routes: RouteObject[] = [
  {
    path: '/login',
    element: (
      <GuestRoute>
        <LoginPage />
      </GuestRoute>
    ),
  },
  {
    path: '/signup',
    element: (
      <GuestRoute>
        <SignupPage />
      </GuestRoute>
    ),
  },
  {
    path: '/onboarding',
    element: (
      <GuestRoute>
        <OnboardingPage />
      </GuestRoute>
    ),
  },
  {
    path: '/dashboard',
    element: (
      <ProtectedRoute>
        <DashboardPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/companies',
    element: (
      <ProtectedRoute>
        <CompaniesPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/projects',
    element: (
      <ProtectedRoute>
        <ProjectsPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/projects/:projectId',
    element: (
      <ProtectedRoute>
        <ProjectDetailPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/nodes/:nodeId',
    element: (
      <ProtectedRoute>
        <NodeDetailPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/kanban',
    element: (
      <ProtectedRoute>
        <KanbanPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/kanban/:projectId',
    element: (
      <ProtectedRoute>
        <KanbanPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/planner',
    element: (
      <ProtectedRoute>
        <PlannerPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/planner/:projectId',
    element: (
      <ProtectedRoute>
        <PlannerPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/tracker',
    element: (
      <ProtectedRoute>
        <TrackerPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/settings',
    element: (
      <ProtectedRoute>
        <SettingsPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/',
    element: <RootRedirect />,
  },
  {
    path: '*',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <NotFoundPage />
      </Suspense>
    ),
  },
];
