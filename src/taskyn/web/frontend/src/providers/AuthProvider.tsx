import {
  createContext,
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { api, setAccessToken, ensureToken } from '@/api/client';
import type { LoginRequest, RegisterRequest, TokenResponse, User } from '@/types';

export interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

/** Max time (ms) to wait for auth init before showing the app as unauthenticated. */
const AUTH_INIT_TIMEOUT_MS = 8_000;

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const initCalled = useRef(false);

  /** Fetch current user on mount (uses refresh cookie). */
  useEffect(() => {
    // Guard against double-invocation in StrictMode dev mode
    if (initCalled.current) return;
    initCalled.current = true;

    let settled = false;
    const settle = () => {
      if (!settled) {
        settled = true;
        setLoading(false);
      }
    };

    // Safety timeout — if init hasn't completed, force loading off
    const timeout = setTimeout(settle, AUTH_INIT_TIMEOUT_MS);

    async function init() {
      try {
        const token = await ensureToken();
        if (!token) {
          setUser(null);
          return;
        }
        const me = await api.get<User>('/auth/me');
        setUser(me);
      } catch {
        setAccessToken(null);
        setUser(null);
      } finally {
        settle();
        clearTimeout(timeout);
      }
    }
    void init();
  }, []);

  const login = useCallback(async (data: LoginRequest) => {
    const res = await api.post<TokenResponse>('/auth/login', data);
    setAccessToken(res.accessToken);
    const me = await api.get<User>('/auth/me');
    setUser(me);
  }, []);

  const register = useCallback(async (data: RegisterRequest) => {
    await api.post('/auth/register', data);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      setAccessToken(null);
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
