import { Navigate, type RouteObject } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import type { ReactNode } from 'react';
import { AppShell } from '@/components/templates/AppShell';
import { LoginPage } from '@/pages/LoginPage';
import { SignupPage } from '@/pages/SignupPage';
import { OnboardingPage } from '@/pages/OnboardingPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { CompaniesPage } from '@/pages/CompaniesPage';
import { ProjectsPage } from '@/pages/ProjectsPage';
import { ProjectDetailPage } from '@/pages/ProjectDetailPage';
import { NodeDetailPage } from '@/pages/NodeDetailPage';

/* ============================================================
   Placeholder pages — will be replaced in Phase 9
   ============================================================ */
function Placeholder({ title }: { title: string }) {
  return (
    <div className="content-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">{title}</h1>
          <p className="page-subtitle">Coming soon</p>
        </div>
      </div>
    </div>
  );
}
function KanbanPage() {
  return <Placeholder title="Kanban" />;
}
function PlannerPage() {
  return <Placeholder title="Planner" />;
}
function TrackerPage() {
  return <Placeholder title="Tracker" />;
}
function SettingsPage() {
  return <Placeholder title="Settings" />;
}

/* ============================================================
   Protected Route wrapper
   ============================================================ */
function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="auth-layout">
        <p className="text-secondary">Loading...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <AppShell>{children}</AppShell>;
}

/* ============================================================
   Route definitions
   ============================================================ */
export const routes: RouteObject[] = [
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/signup',
    element: <SignupPage />,
  },
  {
    path: '/onboarding',
    element: <OnboardingPage />,
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
    path: '/kanban/:projectId',
    element: (
      <ProtectedRoute>
        <KanbanPage />
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
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
];
