import { Navigate, type RouteObject } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import type { ReactNode } from 'react';

/* ============================================================
   Placeholder pages — will be replaced in Phase 5-9
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

function LoginPage() {
  return <Placeholder title="Login" />;
}
function SignupPage() {
  return <Placeholder title="Sign Up" />;
}
function DashboardPage() {
  return <Placeholder title="Dashboard" />;
}
function CompaniesPage() {
  return <Placeholder title="Companies" />;
}
function ProjectsPage() {
  return <Placeholder title="Projects" />;
}
function ProjectDetailPage() {
  return <Placeholder title="Project Detail" />;
}
function NodeDetailPage() {
  return <Placeholder title="Node Detail" />;
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

  return <>{children}</>;
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
