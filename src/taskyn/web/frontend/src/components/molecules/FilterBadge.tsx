import { useCallback, useEffect, useRef, useState } from 'react';
import { Icon } from '@/components/atoms';

export interface FilterOption {
  id: string;
  label: string;
  icon?: string;
  color?: string;
}

interface FilterBadgeProps {
  options: FilterOption[];
  selected: string;
  onSelect: (id: string) => void;
}

export function FilterBadge({ options, selected, onSelect }: FilterBadgeProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const current = options.find((o) => o.id === selected);

  const handleClickOutside = useCallback((e: MouseEvent) => {
    if (ref.current && !ref.current.contains(e.target as globalThis.Node)) {
      setOpen(false);
    }
  }, []);

  useEffect(() => {
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [handleClickOutside]);

  return (
    <div ref={ref} className={`filter-badge ${open ? 'open' : ''}`} onClick={() => setOpen((v) => !v)}>
      {current?.icon && (
        <div
          className="filter-badge-icon-box"
          style={{ background: current.color ?? 'var(--gradient-primary)' }}
        >
          {current.icon}
        </div>
      )}
      <span className="filter-badge-text">{current?.label ?? 'Select...'}</span>
      <Icon name="chevronDown" size={16} className="filter-badge-arrow" />

      <div className="filter-dropdown" onClick={(e) => e.stopPropagation()}>
        {options.map((opt) => (
          <div
            key={opt.id}
            className={`filter-dropdown-item ${opt.id === selected ? 'selected' : ''}`}
            onClick={() => {
              onSelect(opt.id);
              setOpen(false);
            }}
          >
            {opt.icon && (
              <div
                className="filter-dropdown-icon"
                style={{ background: opt.color ?? 'var(--gradient-primary)' }}
              >
                {opt.icon}
              </div>
            )}
            <span className="filter-dropdown-label">{opt.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
