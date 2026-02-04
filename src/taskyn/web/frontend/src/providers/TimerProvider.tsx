import {
  createContext,
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { timerApi } from '@/api/timer';
import type { ActiveTimer } from '@/types';

export interface TimerContextValue {
  activeTimer: ActiveTimer | null;
  elapsed: number; // seconds since start
  loading: boolean;
  start: (nodeId: string, notes?: string) => Promise<void>;
  stop: () => Promise<void>;
  refresh: () => Promise<void>;
}

export const TimerContext = createContext<TimerContextValue | null>(null);

export function TimerProvider({ children }: { children: ReactNode }) {
  const [activeTimer, setActiveTimer] = useState<ActiveTimer | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [loading, setLoading] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const calcElapsed = useCallback((startedAt: string): number => {
    return Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000);
  }, []);

  const startTicking = useCallback(
    (startedAt: string) => {
      if (intervalRef.current) clearInterval(intervalRef.current);
      setElapsed(calcElapsed(startedAt));
      intervalRef.current = setInterval(() => {
        setElapsed(calcElapsed(startedAt));
      }, 1000);
    },
    [calcElapsed],
  );

  const stopTicking = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setElapsed(0);
  }, []);

  const refresh = useCallback(async () => {
    try {
      const timer = await timerApi.getCurrent();
      setActiveTimer(timer);
      if (timer) {
        startTicking(timer.started_at);
      } else {
        stopTicking();
      }
    } catch {
      setActiveTimer(null);
      stopTicking();
    }
  }, [startTicking, stopTicking]);

  // Poll on mount
  useEffect(() => {
    void refresh();
    return () => stopTicking();
  }, [refresh, stopTicking]);

  const start = useCallback(
    async (nodeId: string, notes?: string) => {
      setLoading(true);
      try {
        await timerApi.start(nodeId, notes);
        await refresh();
      } finally {
        setLoading(false);
      }
    },
    [refresh],
  );

  const stop = useCallback(async () => {
    setLoading(true);
    try {
      await timerApi.stop();
      setActiveTimer(null);
      stopTicking();
    } finally {
      setLoading(false);
    }
  }, [stopTicking]);

  return (
    <TimerContext.Provider
      value={{ activeTimer, elapsed, loading, start, stop, refresh }}
    >
      {children}
    </TimerContext.Provider>
  );
}
