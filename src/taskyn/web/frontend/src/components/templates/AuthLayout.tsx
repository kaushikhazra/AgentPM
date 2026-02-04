import type { ReactNode } from 'react';

interface AuthLayoutProps {
  children: ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="auth-layout">
      <div className="auth-card">
        <div className="auth-logo">
          <div className="logo-icon">T</div>
          <span className="logo-text">Taskyn</span>
        </div>
        {children}
      </div>
    </div>
  );
}
