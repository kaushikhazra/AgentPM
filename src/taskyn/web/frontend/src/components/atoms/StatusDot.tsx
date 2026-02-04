interface StatusDotProps {
  status: string;
  className?: string;
}

export function StatusDot({ status, className = '' }: StatusDotProps) {
  return <span className={`status-dot status-dot--${status} ${className}`} />;
}
