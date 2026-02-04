import type { ReactNode } from 'react';
import { TopNav } from '@/components/organisms/TopNav';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <>
      <TopNav />
      <main className="main-content">
        {children}
      </main>
    </>
  );
}
