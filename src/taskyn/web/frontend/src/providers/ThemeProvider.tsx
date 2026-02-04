import { createContext, useCallback, useEffect, useState, type ReactNode } from 'react';

export type ThemeMode = 'dark' | 'light';
export type ThemeAccent = 'amber' | 'wine' | 'ocean' | 'forest';

const STORAGE_KEY_MODE = 'taskyn-mode';
const STORAGE_KEY_THEME = 'taskyn-theme';

export interface ThemeContextValue {
  mode: ThemeMode;
  accent: ThemeAccent;
  setMode: (mode: ThemeMode) => void;
  setAccent: (accent: ThemeAccent) => void;
  toggleMode: () => void;
}

export const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(
    () => (localStorage.getItem(STORAGE_KEY_MODE) as ThemeMode) || 'dark',
  );
  const [accent, setAccentState] = useState<ThemeAccent>(
    () => (localStorage.getItem(STORAGE_KEY_THEME) as ThemeAccent) || 'amber',
  );

  // Apply to DOM
  useEffect(() => {
    document.documentElement.setAttribute('data-mode', mode);
    localStorage.setItem(STORAGE_KEY_MODE, mode);
  }, [mode]);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', accent);
    localStorage.setItem(STORAGE_KEY_THEME, accent);
  }, [accent]);

  const setMode = useCallback((m: ThemeMode) => setModeState(m), []);
  const setAccent = useCallback((a: ThemeAccent) => setAccentState(a), []);
  const toggleMode = useCallback(
    () => setModeState((prev) => (prev === 'dark' ? 'light' : 'dark')),
    [],
  );

  return (
    <ThemeContext.Provider value={{ mode, accent, setMode, setAccent, toggleMode }}>
      {children}
    </ThemeContext.Provider>
  );
}
