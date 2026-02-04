import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Avatar, Icon } from '@/components/atoms';
import { useAuth } from '@/hooks/useAuth';

export function UserMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const handleClickOutside = useCallback((e: MouseEvent) => {
    if (ref.current && !ref.current.contains(e.target as globalThis.Node)) {
      setOpen(false);
    }
  }, []);

  useEffect(() => {
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [handleClickOutside]);

  const handleLogout = async () => {
    setOpen(false);
    await logout();
    navigate('/login');
  };

  if (!user) return null;

  return (
    <div ref={ref} className={`user-menu ${open ? 'open' : ''}`}>
      <div onClick={() => setOpen((v) => !v)}>
        <Avatar name={user.name} />
      </div>
      <div className="user-dropdown">
        <div className="user-dropdown-header">
          <div className="user-dropdown-name">{user.name}</div>
          <div className="user-dropdown-email">{user.email}</div>
        </div>
        <div className="user-dropdown-menu">
          <button
            className="user-dropdown-item"
            onClick={() => { setOpen(false); navigate('/settings'); }}
          >
            <Icon name="settings" size={16} />
            Settings
          </button>
          <button
            className="user-dropdown-item"
            onClick={() => { setOpen(false); navigate('/help'); }}
          >
            <Icon name="help" size={16} />
            Help & Support
          </button>
          <div className="user-dropdown-divider" />
          <button className="user-dropdown-item danger" onClick={handleLogout}>
            <Icon name="logout" size={16} />
            Log out
          </button>
        </div>
      </div>
    </div>
  );
}
