interface AvatarProps {
  name: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Avatar({ name, size = 'md', className = '' }: AvatarProps) {
  const initial = name.charAt(0).toUpperCase();
  const sizeClass = size === 'lg' ? 'user-avatar--lg' : '';
  return (
    <div className={`user-avatar ${sizeClass} ${className}`}>
      {initial}
    </div>
  );
}
