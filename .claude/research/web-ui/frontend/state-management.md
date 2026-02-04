# State Management

This document defines the state management strategy for Taskyn's React frontend.

---

## Types of State

| Type | Description | Examples | Update Frequency |
|------|-------------|----------|------------------|
| **Server State** | Data from API | Projects, nodes, companies, time entries | On fetch, mutation |
| **Auth State** | User session | User info, token, permissions | On login/logout |
| **Theme State** | Visual preferences | Theme (amber/wine), mode (dark/light) | Rarely |
| **Timer State** | Active time tracking | Current timer, elapsed seconds | Every second |
| **Modal State** | Modal visibility | Which modal, modal props | On open/close |
| **Toast State** | Notifications | Queue of messages | On events |
| **Form State** | Input values | Form fields, validation errors | On typing |
| **UI State** | Local UI toggles | Dropdown open, sidebar collapsed | On interaction |

---

## State Categories & Solutions

### 1. Server State → TanStack Query (React Query)

**Why TanStack Query:**
- Automatic caching & background refetching
- Loading/error states built-in
- Optimistic updates for mutations
- Cache invalidation on mutations
- Deduplication of requests

```tsx
// Example: Fetching nodes
const { data: nodes, isLoading } = useQuery({
  queryKey: ['nodes', projectId],
  queryFn: () => api.nodes.list(projectId),
});

// Example: Creating a node
const createNode = useMutation({
  mutationFn: api.nodes.create,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['nodes'] });
    toast.success('Node created');
  },
});
```

**Server state includes:**
- Companies
- Projects
- Nodes (epics, stories, tasks, specs, etc.)
- Edges (relationships)
- Time entries
- Activity log
- Methodology definitions

### 2. Auth State → React Context

**Why Context:**
- Needed app-wide
- Changes infrequently
- Simple structure

```tsx
// AuthProvider.tsx
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextValue>(null);

export function AuthProvider({ children }) {
  const [state, setState] = useState<AuthState>(initialState);

  const login = async (credentials) => { /* ... */ };
  const logout = () => { /* ... */ };

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook
export const useAuth = () => useContext(AuthContext);
```

### 3. Theme State → React Context + localStorage

**Why Context + localStorage:**
- Persists across sessions
- Needs to be available before React hydrates (avoid flash)

```tsx
// ThemeProvider.tsx
interface ThemeState {
  mode: 'dark' | 'light';
  theme: 'amber' | 'wine' | 'ocean' | 'forest';
}

export function ThemeProvider({ children }) {
  const [state, setState] = useState<ThemeState>(() => {
    // Read from localStorage on init
    return loadFromStorage() || { mode: 'dark', theme: 'amber' };
  });

  const setMode = (mode) => { /* update + persist */ };
  const setTheme = (theme) => { /* update + persist */ };

  // Apply to document
  useEffect(() => {
    document.documentElement.setAttribute('data-mode', state.mode);
    document.documentElement.setAttribute('data-theme', state.theme);
  }, [state]);

  return (
    <ThemeContext.Provider value={{ ...state, setMode, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
```

### 4. Timer State → React Context (or Zustand)

**Why dedicated solution:**
- Global (accessible from any page)
- Updates frequently (every second)
- Needs to persist across navigation

```tsx
// TimerProvider.tsx
interface TimerState {
  isRunning: boolean;
  nodeId: string | null;
  startTime: Date | null;
  elapsed: number; // seconds
}

export function TimerProvider({ children }) {
  const [state, setState] = useState<TimerState>(initialState);

  // Tick every second when running
  useEffect(() => {
    if (!state.isRunning) return;
    const interval = setInterval(() => {
      setState(s => ({ ...s, elapsed: s.elapsed + 1 }));
    }, 1000);
    return () => clearInterval(interval);
  }, [state.isRunning]);

  const start = (nodeId: string) => { /* ... */ };
  const pause = () => { /* ... */ };
  const stop = () => { /* save to API, reset */ };

  return (
    <TimerContext.Provider value={{ ...state, start, pause, stop }}>
      {children}
    </TimerContext.Provider>
  );
}
```

### 5. Modal State → React Context

**Why Context:**
- Central manager (one modal at a time)
- Any component can trigger modals

```tsx
// ModalProvider.tsx
interface ModalState {
  isOpen: boolean;
  type: ModalType | null;
  props: Record<string, any>;
}

type ModalType =
  | 'createNode'
  | 'editNode'
  | 'deleteConfirm'
  | 'createProject'
  | /* ... */;

export function ModalProvider({ children }) {
  const [state, setState] = useState<ModalState>({ isOpen: false, type: null, props: {} });

  const open = (type: ModalType, props = {}) => setState({ isOpen: true, type, props });
  const close = () => setState({ isOpen: false, type: null, props: {} });

  return (
    <ModalContext.Provider value={{ ...state, open, close }}>
      {children}
      <ModalRenderer /> {/* Renders current modal via portal */}
    </ModalContext.Provider>
  );
}

// Usage anywhere
const { open } = useModal();
<Button onClick={() => open('createNode', { projectId })}>New Node</Button>
```

### 6. Toast State → React Context

```tsx
// ToastProvider.tsx
interface Toast {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const show = (type, message) => {
    const id = uuid();
    setToasts(t => [...t, { id, type, message }]);
    setTimeout(() => dismiss(id), 5000); // Auto-dismiss
  };

  const dismiss = (id) => setToasts(t => t.filter(x => x.id !== id));

  return (
    <ToastContext.Provider value={{ show, dismiss }}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

// Convenience hooks
export const useToast = () => {
  const { show } = useContext(ToastContext);
  return {
    success: (msg) => show('success', msg),
    error: (msg) => show('error', msg),
    info: (msg) => show('info', msg),
  };
};
```

### 7. Form State → Local (useState or React Hook Form)

**Why local:**
- Scoped to component
- No need to share
- High update frequency (every keystroke)

```tsx
// Simple form
const [title, setTitle] = useState('');
const [description, setDescription] = useState('');

// Or with React Hook Form for complex forms
const { register, handleSubmit, errors } = useForm<CreateNodeForm>();
```

### 8. UI State → Local (useState)

**Why local:**
- Component-specific
- Doesn't need sharing

```tsx
const [isDropdownOpen, setDropdownOpen] = useState(false);
const [isSidebarCollapsed, setSidebarCollapsed] = useState(false);
```

---

## Summary: Where State Lives

```
App
├── AuthProvider (Context)
│   └── user, token, isAuthenticated
│
├── ThemeProvider (Context + localStorage)
│   └── mode, theme
│
├── TimerProvider (Context)
│   └── isRunning, nodeId, elapsed
│
├── ModalProvider (Context)
│   └── isOpen, type, props
│
├── ToastProvider (Context)
│   └── toasts[]
│
├── QueryClientProvider (TanStack Query)
│   └── All server state cached here
│
└── Components
    └── Local state (useState, useForm)
```

---

## Data Flow

### Fetching Data

```
Component
  → useQuery({ queryKey, queryFn })
    → TanStack Query checks cache
      → If fresh: return cached
      → If stale: return cached + refetch in background
      → If missing: fetch from API
```

### Mutating Data

```
Component
  → useMutation({ mutationFn, onSuccess })
    → Call API
      → On success: invalidate queries, show toast
      → On error: show error toast
```

### Example Flow: Creating a Node

```tsx
function CreateNodeModal({ projectId }) {
  const { close } = useModal();
  const toast = useToast();
  const queryClient = useQueryClient();

  const createNode = useMutation({
    mutationFn: (data) => api.nodes.create({ ...data, projectId }),
    onSuccess: (newNode) => {
      queryClient.invalidateQueries({ queryKey: ['nodes', projectId] });
      toast.success(`${nodeTypeUI.displayName} created`);
      close();
    },
    onError: (err) => {
      toast.error(err.message);
    },
  });

  const onSubmit = (data) => createNode.mutate(data);

  return <Form onSubmit={onSubmit} isLoading={createNode.isPending} />;
}
```

---

## Decisions

- [x] **TanStack Query for server state** - Caching, refetching, mutations
- [x] **React Context for app-wide UI state** - Auth, theme, timer, modal, toast
- [x] **Local state for component UI** - Forms, dropdowns, toggles
- [x] **No Redux** - Overkill for this app, Context + TanStack Query covers needs
- [ ] **Consider Zustand** - If Context becomes unwieldy for timer (frequent updates)

---

## Libraries

| Purpose | Library | Why |
|---------|---------|-----|
| Server state | `@tanstack/react-query` | Best-in-class caching |
| Forms | `react-hook-form` | Performant, validation |
| Validation | `zod` | Type-safe schemas |

