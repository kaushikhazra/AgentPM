import type { ReactNode } from 'react';

interface FullWidthLayoutProps {
  title: string;
  subtitle?: ReactNode;
  headerAction?: ReactNode;
  children: ReactNode;
}

export function FullWidthLayout({
  title,
  subtitle,
  headerAction,
  children,
}: FullWidthLayoutProps) {
  return (
    <div className="content-wrapper--full">
      <div className="page-header">
        <div>
          <h1 className="page-title">{title}</h1>
          {subtitle && <div className="page-subtitle">{subtitle}</div>}
        </div>
        {headerAction}
      </div>
      {children}
    </div>
  );
}
