import { useState, useMemo, type ReactNode } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { TopNav } from '@/components/organisms/TopNav';
import { ShortcutBar } from '@/components/organisms/ShortcutBar';
import { SearchModal } from '@/components/organisms/SearchModal';
import { useHotkeys, type Shortcut } from '@/hooks/useHotkeys';

interface AppShellProps {
  children: ReactNode;
}

/** Shortcut hints shown in the footer bar, keyed by page context. */
const SHORTCUT_HINTS: Record<string, { key: string; label: string }[]> = {
  dashboard: [
    { key: 'C', label: 'New Company' },
    { key: 'P', label: 'New Project' },
    { key: '/', label: 'Search' },
    { key: '?', label: 'Help' },
  ],
  companies: [
    { key: 'C', label: 'New Company' },
    { key: '/', label: 'Search' },
    { key: '?', label: 'Help' },
  ],
  projects: [
    { key: 'P', label: 'New Project' },
    { key: '/', label: 'Search' },
    { key: '?', label: 'Help' },
  ],
  project: [
    { key: 'N', label: 'New Item' },
    { key: 'B', label: 'Back' },
    { key: '/', label: 'Search' },
  ],
  node: [
    { key: 'N', label: 'New Child' },
    { key: 'B', label: 'Back' },
    { key: '/', label: 'Search' },
  ],
  kanban: [
    { key: 'B', label: 'Back' },
    { key: '/', label: 'Search' },
  ],
  planner: [
    { key: 'A', label: 'Add Item' },
    { key: 'E', label: 'Expand All' },
    { key: 'B', label: 'Back' },
    { key: '/', label: 'Search' },
  ],
  tracker: [
    { key: 'N', label: 'New Entry' },
    { key: '/', label: 'Search' },
  ],
  settings: [
    { key: 'B', label: 'Back' },
    { key: '/', label: 'Search' },
  ],
};

function getContext(pathname: string): string {
  if (pathname.startsWith('/kanban')) return 'kanban';
  if (pathname.startsWith('/planner')) return 'planner';
  if (pathname.startsWith('/tracker')) return 'tracker';
  if (pathname.startsWith('/settings')) return 'settings';
  if (pathname.startsWith('/nodes/')) return 'node';
  if (pathname.match(/^\/projects\/[^/]+$/)) return 'project';
  if (pathname === '/projects') return 'projects';
  if (pathname === '/companies') return 'companies';
  return 'dashboard';
}

export function AppShell({ children }: AppShellProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchOpen, setSearchOpen] = useState(false);

  const context = getContext(location.pathname);
  const hints = SHORTCUT_HINTS[context] ?? SHORTCUT_HINTS.dashboard!;

  // Build action-mapped shortcuts for useHotkeys
  const shortcuts: Shortcut[] = useMemo(
    () => [
      {
        key: 'Ctrl+K',
        label: 'Search',
        action: () => setSearchOpen(true),
      },
      {
        key: '/',
        label: 'Search',
        action: () => setSearchOpen(true),
      },
      {
        key: 'B',
        label: 'Back',
        action: () => navigate(-1),
      },
      {
        key: '?',
        label: 'Help',
        action: () => navigate('/settings'),
      },
    ],
    [navigate],
  );

  useHotkeys(shortcuts);

  return (
    <>
      <TopNav onSearchClick={() => setSearchOpen(true)} />
      <main className="main-content">
        {children}
      </main>
      <ShortcutBar shortcuts={hints} />
      <SearchModal open={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
}
