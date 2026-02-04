import { Link } from 'react-router-dom';
import { NavLink } from '@/components/molecules/NavLink';
import { SearchBar } from '@/components/molecules/SearchBar';
import { UserMenu } from '@/components/molecules/UserMenu';

interface TopNavProps {
  onSearchClick?: () => void;
}

export function TopNav({ onSearchClick }: TopNavProps) {
  return (
    <nav className="top-nav">
      <Link to="/dashboard" className="logo">
        <div className="logo-icon">T</div>
        <span className="logo-text">Taskyn</span>
      </Link>

      <div className="main-nav">
        <NavLink to="/dashboard" icon="dashboard" label="Dashboard" />
        <NavLink to="/companies" icon="companies" label="Companies" />
        <NavLink to="/projects" icon="projects" label="Projects" />
        <NavLink to="/tracker" icon="tracker" label="Tracker" />
      </div>

      <div className="nav-right">
        <SearchBar onClick={onSearchClick} />
        <UserMenu />
      </div>
    </nav>
  );
}
