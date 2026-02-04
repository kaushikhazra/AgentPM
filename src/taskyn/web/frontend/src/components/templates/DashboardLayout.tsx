import type { ReactNode } from 'react';
import { StatCard } from '@/components/molecules/StatCard';

interface Stat {
  label: string;
  value: string | number;
}

interface DashboardLayoutProps {
  title: string;
  subtitle?: string;
  headerAction?: ReactNode;
  stats?: Stat[];
  children: ReactNode;
}

export function DashboardLayout({
  title,
  subtitle,
  headerAction,
  stats,
  children,
}: DashboardLayoutProps) {
  return (
    <div className="content-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">{title}</h1>
          {subtitle && <p className="page-subtitle">{subtitle}</p>}
        </div>
        {headerAction}
      </div>

      {stats && stats.length > 0 && (
        <div className="stats-grid">
          {stats.map((s) => (
            <StatCard key={s.label} label={s.label} value={s.value} />
          ))}
        </div>
      )}

      <div className="content-grid">{children}</div>
    </div>
  );
}
