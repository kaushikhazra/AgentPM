import { NavLink as RouterNavLink } from 'react-router-dom';
import { Icon, type IconName } from '@/components/atoms';

interface NavLinkProps {
  to: string;
  icon: IconName;
  label: string;
}

export function NavLink({ to, icon, label }: NavLinkProps) {
  return (
    <RouterNavLink
      to={to}
      className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
    >
      <Icon name={icon} />
      {label}
    </RouterNavLink>
  );
}
