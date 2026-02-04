import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { createPortal } from 'react-dom';
import { searchApi } from '@/api/search';
import type { SearchResult } from '@/types';

interface SearchModalProps {
  open: boolean;
  onClose: () => void;
}

const TYPE_ICONS: Record<string, string> = {
  company: 'C',
  project: 'P',
  node: 'N',
};

export function SearchModal({ open, onClose }: SearchModalProps) {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selected, setSelected] = useState(0);
  const [loading, setLoading] = useState(false);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setQuery('');
      setResults([]);
      setSelected(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await searchApi.search(query, { limit: 10 });
        setResults(res);
        setSelected(0);
      } catch {
        // silently ignore search errors
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [query]);

  const navigateToResult = useCallback(
    (result: SearchResult) => {
      onClose();
      if (result.entity_type === 'company') {
        navigate('/companies');
      } else if (result.entity_type === 'project') {
        navigate(`/projects/${result.entity_id}`);
      } else {
        navigate(`/nodes/${result.entity_id}`);
      }
    },
    [navigate, onClose],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelected((prev) => Math.min(prev + 1, results.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelected((prev) => Math.max(prev - 1, 0));
      } else if (e.key === 'Enter' && results[selected]) {
        navigateToResult(results[selected]);
      }
    },
    [onClose, results, selected, navigateToResult],
  );

  if (!open) return null;

  return createPortal(
    <div className="search-modal-overlay" onClick={onClose}>
      <div className="search-modal" onClick={(e) => e.stopPropagation()}>
        <div className="search-modal-input-wrapper">
          <svg className="search-modal-icon" viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" fill="none" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            ref={inputRef}
            className="search-modal-input"
            type="text"
            placeholder="Search companies, projects, nodes..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <kbd className="search-modal-esc">Esc</kbd>
        </div>
        {query.trim() && (
          <div className="search-modal-results">
            {loading ? (
              <div className="search-modal-empty">Searching...</div>
            ) : results.length === 0 ? (
              <div className="search-modal-empty">No results found</div>
            ) : (
              results.map((r, i) => (
                <div
                  key={r.entity_id}
                  className={`search-result-item${i === selected ? ' selected' : ''}`}
                  onClick={() => navigateToResult(r)}
                  onMouseEnter={() => setSelected(i)}
                >
                  <div className="search-result-type">{TYPE_ICONS[r.entity_type] ?? 'N'}</div>
                  <div className="search-result-content">
                    <div className="search-result-title">{r.title}</div>
                    <div className="search-result-meta">{r.entity_type}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>,
    document.body,
  );
}
