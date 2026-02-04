import type { ReactNode } from 'react';

interface SectionProps {
  title: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  noPadding?: boolean;
}

export function Section({ title, action, children, className = '', noPadding }: SectionProps) {
  return (
    <div className={`section ${className}`}>
      <div className="section-header">
        <h3 className="section-title">{title}</h3>
        {action}
      </div>
      {noPadding ? children : <div className="section-content">{children}</div>}
    </div>
  );
}
