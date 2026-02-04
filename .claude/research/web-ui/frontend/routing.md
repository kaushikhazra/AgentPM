# Routing

This document defines the routing strategy for Taskyn's React frontend.

---

## Router Choice: React Router v6

**Why React Router:**
- Industry standard for React SPAs
- Supports nested routes (matches our AppShell pattern)
- Built-in route guards via loaders
- Dynamic route parameters for nodes

---

## Route Structure

```
/                           → Redirect to /dashboard (if auth) or /login
/login                      → LoginPage
/signup                     → SignupPage
/onboarding                 → OnboardingPage

/dashboard                  → DashboardPage (protected)
/companies                  → CompaniesPage (protected)
/projects                   → ProjectsPage (protected)
/projects/:projectId        → ProjectDetailPage (protected)
/nodes/:nodeId              → NodeDetailPage (protected, generic)
/kanban/:projectId          → KanbanPage (protected)
/planner                    → PlannerPage (protected)
/tracker                    → TrackerPage (protected)
/settings                   → SettingsPage (protected)
```

### Key Design Decisions

1. **Generic `/nodes/:nodeId` route** - Handles all node types (epic, story, task, spec, design, etc.)
2. **No methodology-specific routes** - `/nodes/abc123` works regardless of node type
3. **Project context via nodeId** - Node lookup provides project context

---

## Route Configuration

```tsx
// src/routes.tsx
import { createBrowserRouter, Navigate } from 'react-router-dom';

export const router = createBrowserRouter([
  // Public routes
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

  // Protected routes (wrapped in AppShell)
  {
    path: '/',
    element: <ProtectedRoute><AppShell /></ProtectedRoute>,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'companies', element: <CompaniesPage /> },
      { path: 'projects', element: <ProjectsPage /> },
      { path: 'projects/:projectId', element: <ProjectDetailPage /> },
      { path: 'nodes/:nodeId', element: <NodeDetailPage /> },
      { path: 'kanban/:projectId', element: <KanbanPage /> },
      { path: 'planner', element: <PlannerPage /> },
      { path: 'tracker', element: <TrackerPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },

  // Catch-all
  { path: '*', element: <Navigate to="/" replace /> },
]);
```

---

## Protected Route Component

```tsx
// src/components/ProtectedRoute.tsx
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingSpinner />; // Or skeleton
  }

  if (!isAuthenticated) {
    // Redirect to login, preserving intended destination
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
```

---

## Navigation Patterns

### Programmatic Navigation

```tsx
import { useNavigate } from 'react-router-dom';

function SomeComponent() {
  const navigate = useNavigate();

  const handleCreateNode = (nodeId: string) => {
    navigate(`/nodes/${nodeId}`);
  };

  const handleBack = () => {
    navigate(-1); // Go back
  };
}
```

### Link Components

```tsx
import { Link } from 'react-router-dom';

// In NodeCard
<Link to={`/nodes/${node.id}`}>
  {node.title}
</Link>

// In Breadcrumb
<Link to={`/projects/${project.id}`}>
  {project.name}
</Link>
```

---

## Dynamic Node Routes

The `/nodes/:nodeId` route is methodology-agnostic:

```tsx
// NodeDetailPage.tsx
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';

export function NodeDetailPage() {
  const { nodeId } = useParams<{ nodeId: string }>();

  const { data: node, isLoading } = useQuery({
    queryKey: ['nodes', nodeId],
    queryFn: () => api.nodes.get(nodeId),
  });

  const { data: project } = useQuery({
    queryKey: ['projects', node?.projectId],
    queryFn: () => api.projects.get(node!.projectId),
    enabled: !!node?.projectId,
  });

  if (isLoading) return <DetailSkeleton />;
  if (!node) return <NotFound />;

  // Get UI config based on methodology
  const uiConfig = METHODOLOGY_UI[project.methodology];
  const nodeTypeUI = uiConfig.nodeTypes[node.nodeType];

  return (
    <DetailLayout>
      <Breadcrumb nodeId={nodeId} />
      <PageHeader
        title={node.title}
        icon={nodeTypeUI.icon}
        badge={<StatusBadge status={node.status} />}
      />
      <NodeChildren nodeId={nodeId} />
    </DetailLayout>
  );
}
```

---

## Breadcrumb Navigation

Breadcrumbs are built by traversing parent edges:

```tsx
// Breadcrumb.tsx
export function Breadcrumb({ nodeId }: { nodeId: string }) {
  const { data: ancestors } = useQuery({
    queryKey: ['node-ancestors', nodeId],
    queryFn: () => api.nodes.getAncestors(nodeId),
  });

  // ancestors = [project, epic, story] (ordered root to parent)

  return (
    <nav className="breadcrumb">
      {ancestors?.map((item, i) => (
        <Fragment key={item.id}>
          {i > 0 && <span className="separator">/</span>}
          <Link to={item.type === 'project' ? `/projects/${item.id}` : `/nodes/${item.id}`}>
            {item.title}
          </Link>
        </Fragment>
      ))}
    </nav>
  );
}
```

---

## URL State (Query Parameters)

Some UI state can be preserved in URL:

```tsx
// KanbanPage with filter state in URL
import { useSearchParams } from 'react-router-dom';

export function KanbanPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const statusFilter = searchParams.get('status') || 'all';
  const assigneeFilter = searchParams.get('assignee') || 'all';

  const setFilter = (key: string, value: string) => {
    setSearchParams(params => {
      if (value === 'all') {
        params.delete(key);
      } else {
        params.set(key, value);
      }
      return params;
    });
  };

  // URL: /kanban/abc123?status=in_progress&assignee=user1
}
```

---

## Post-Login Redirect

After successful login, redirect to intended destination:

```tsx
// LoginPage.tsx
import { useLocation, useNavigate } from 'react-router-dom';

export function LoginPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { login } = useAuth();

  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (credentials) => {
    await login(credentials);
    navigate(from, { replace: true });
  };
}
```

---

## Route-Based Code Splitting (Future)

For performance, lazy load pages:

```tsx
import { lazy, Suspense } from 'react';

const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const KanbanPage = lazy(() => import('./pages/KanbanPage'));

// In router
{
  path: 'dashboard',
  element: (
    <Suspense fallback={<PageSkeleton />}>
      <DashboardPage />
    </Suspense>
  ),
}
```

---

## Decisions

- [x] **React Router v6** - Industry standard, supports our patterns
- [x] **Generic `/nodes/:nodeId` route** - One route for all node types
- [x] **ProtectedRoute wrapper** - Simple auth guard pattern
- [x] **Preserve intended destination** - Redirect after login to original URL
- [ ] **Code splitting** - Defer to optimization phase

---

## Summary

| Route | Page | Auth Required |
|-------|------|---------------|
| `/login` | LoginPage | No |
| `/signup` | SignupPage | No |
| `/onboarding` | OnboardingPage | No |
| `/dashboard` | DashboardPage | Yes |
| `/companies` | CompaniesPage | Yes |
| `/projects` | ProjectsPage | Yes |
| `/projects/:id` | ProjectDetailPage | Yes |
| `/nodes/:id` | NodeDetailPage | Yes |
| `/kanban/:projectId` | KanbanPage | Yes |
| `/planner` | PlannerPage | Yes |
| `/tracker` | TrackerPage | Yes |
| `/settings` | SettingsPage | Yes |

