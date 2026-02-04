import type { ReactNode } from 'react';
import { Breadcrumb, type BreadcrumbItem } from '@/components/molecules/Breadcrumb';

interface DetailLayoutProps {
  breadcrumbs: BreadcrumbItem[];
  title: string;
  subtitle?: string;
  headerAction?: ReactNode;
  badge?: ReactNode;
  children: ReactNode;
}

export function DetailLayout({
  breadcrumbs,
  title,
  subtitle,
  headerAction,
  badge,
  children,
}: DetailLayoutProps) {
  return (
    <div className="content-wrapper">
      <Breadcrumb items={breadcrumbs} />
      <div className="page-header">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <h1 className="page-title">{title}</h1>
            {badge}
          </div>
          {subtitle && <p className="page-subtitle">{subtitle}</p>}
        </div>
        {headerAction}
      </div>
      {children}
    </div>
  );
}
