import { Navigate, type RouteObject } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import type { ReactNode } from 'react';
import { Button, Input, Checkbox, Badge, Avatar, StatusDot, Kbd, Icon } from '@/components/atoms';
import { StatCard, TaskItem, ActivityItem, Breadcrumb, SearchBar } from '@/components/molecules';
import { useState } from 'react';

/* ============================================================
   Placeholder pages — will be replaced in Phase 7-9
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

/** Temporary component showcase — replaced in Phase 8 */
function DashboardPage() {
  const [checked, setChecked] = useState(false);
  return (
    <div className="content-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Component Showcase</p>
        </div>
        <Button variant="primary" icon={<Icon name="plus" size={16} />}>New Task</Button>
      </div>

      {/* Stats */}
      <div className="stats-grid" data-testid="stats-grid">
        <StatCard label="Tasks Due Today" value={5} />
        <StatCard label="In Progress" value={3} />
        <StatCard label="Completed" value={12} />
        <StatCard label="Time Tracked" value="4h 30m" />
      </div>

      <div className="content-grid">
        <div>
          {/* Buttons */}
          <div className="section mb-lg" data-testid="buttons-section">
            <div className="section-header">
              <h3 className="section-title">Buttons</h3>
            </div>
            <div className="section-content" style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
              <Button variant="primary">Primary</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="danger">Danger</Button>
              <Button variant="primary" size="sm">Small</Button>
              <Button variant="primary" disabled>Disabled</Button>
            </div>
          </div>

          {/* Task Items */}
          <div className="section mb-lg" data-testid="tasks-section">
            <div className="section-header">
              <h3 className="section-title">Today's Tasks</h3>
            </div>
            <TaskItem title="Implement FastAPI endpoints" meta="Taskyn Dev - Due today" priority="high" />
            <TaskItem title="Write unit tests" meta="Taskyn Dev - Due tomorrow" priority="medium" />
            <TaskItem title="Update documentation" meta="Taskyn Dev - No due date" priority="low" checked />
          </div>

          {/* Inputs */}
          <div className="section mb-lg" data-testid="inputs-section">
            <div className="section-header">
              <h3 className="section-title">Form Inputs</h3>
            </div>
            <div className="section-content">
              <Input label="Email" type="email" placeholder="you@example.com" />
              <Input label="Password" isPassword placeholder="Enter your password" />
              <Input label="With Error" error="This field is required" />
              <Checkbox checked={checked} onChange={setChecked} label="Accept terms and conditions" />
            </div>
          </div>
        </div>

        <div>
          {/* Badges & Status */}
          <div className="section mb-lg" data-testid="badges-section">
            <div className="section-header">
              <h3 className="section-title">Badges & Status</h3>
            </div>
            <div className="section-content" style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
              <Badge>Default</Badge>
              <StatusDot status="backlog" /> <span className="text-secondary">Backlog</span>
              <StatusDot status="ready" /> <span className="text-secondary">Ready</span>
              <StatusDot status="in_progress" /> <span className="text-secondary">In Progress</span>
              <StatusDot status="done" /> <span className="text-secondary">Done</span>
              <StatusDot status="blocked" /> <span className="text-secondary">Blocked</span>
            </div>
            <div className="section-content" style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
              <Avatar name="Kaushik" />
              <Avatar name="Velasari" size="lg" />
              <Kbd>Ctrl+K</Kbd>
              <SearchBar />
            </div>
          </div>

          {/* Breadcrumb */}
          <div className="section mb-lg" data-testid="breadcrumb-section">
            <div className="section-header">
              <h3 className="section-title">Breadcrumb</h3>
            </div>
            <div className="section-content">
              <Breadcrumb items={[
                { label: 'Companies', to: '/companies' },
                { label: 'Taskyn Corp', to: '/companies' },
                { label: 'Web UI Project' },
              ]} />
            </div>
          </div>

          {/* Activity */}
          <div className="section mb-lg" data-testid="activity-section">
            <div className="section-header">
              <h3 className="section-title">Recent Activity</h3>
            </div>
            <div className="section-content">
              <ActivityItem type="complete" text="Completed" highlight="Research UI templates" time="2 minutes ago" />
              <ActivityItem type="time" text="Tracked 45m on" highlight="FastAPI endpoints" time="1 hour ago" />
              <ActivityItem type="create" text="Created" highlight="New milestone" time="3 hours ago" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
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
