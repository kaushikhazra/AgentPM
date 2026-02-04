import { Icon, Kbd } from '@/components/atoms';

interface SearchBarProps {
  onClick?: () => void;
}

export function SearchBar({ onClick }: SearchBarProps) {
  return (
    <div className="nav-search" onClick={onClick} role="button" tabIndex={0}>
      <Icon name="search" size={16} />
      Search...
      <Kbd>Ctrl+K</Kbd>
    </div>
  );
}
