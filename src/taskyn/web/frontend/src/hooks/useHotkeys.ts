import { useEffect, useRef } from 'react';

export interface Shortcut {
  key: string;
  label: string;
  action: () => void;
}

/**
 * Global keyboard shortcut hook.
 * Ignores keypresses when focus is inside input/textarea/select elements.
 * Supports Ctrl+K as a special combo (always fires, even in inputs).
 *
 * Uses a ref for shortcuts to avoid listener churn (CR-32).
 */
export function useHotkeys(shortcuts: Shortcut[]) {
  const shortcutsRef = useRef(shortcuts);
  shortcutsRef.current = shortcuts;

  useEffect(() => {
    function handler(e: KeyboardEvent) {
      const current = shortcutsRef.current;

      // Ctrl+K — always fires (search)
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const match = current.find((s) => s.key === 'Ctrl+K');
        if (match) match.action();
        return;
      }

      // Skip when user is typing in an input
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      if ((e.target as HTMLElement).isContentEditable) return;

      // Skip if modifier keys are held (except Shift for ?)
      if (e.ctrlKey || e.metaKey || e.altKey) return;

      const match = current.find((s) => s.key === e.key.toUpperCase() || s.key === e.key);
      if (match) {
        e.preventDefault();
        match.action();
      }
    }

    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, []);
}
