import {
  createContext,
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { timerApi } from '@/api/timer';
import { queryKeys } from '@/api/queryKeys';
import { useAuth } from '@/hooks/useAuth';
import { useTimerCurrent } from '@/hooks/queries/useTimerQuery';
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
  const { user, loading: authLoading } = useAuth();
  const queryClient = useQueryClient();

  const isAuthenticated = !authLoading && !!user;

  // TanStack Query handles polling — 1s refetchInterval when authenticated
  const { data: activeTimer = null, isPending } = useTimerCurrent({
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 1_000 : undefined,
  });

  const [elapsed, setElapsed] = useState(0);
  const [mutating, setMutating] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const calcElapsed = useCallback((startedAt: string): number => {
    return Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000);
  }, []);

  // Manage the elapsed tick interval based on activeTimer state
  useEffect(() => {
    if (activeTimer?.started_at) {
      setElapsed(calcElapsed(activeTimer.started_at));
      intervalRef.current = setInterval(() => {
        setElapsed(calcElapsed(activeTimer.started_at));
      }, 1000);
    } else {
      setElapsed(0);
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [activeTimer, calcElapsed]);

  const refresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.timer.all() });
  }, [queryClient]);

  const start = useCallback(
    async (nodeId: string, notes?: string) => {
      setMutating(true);
      try {
        await timerApi.start(nodeId, notes);
        await refresh();
      } finally {
        setMutating(false);
      }
    },
    [refresh],
  );

  const stop = useCallback(async () => {
    setMutating(true);
    try {
      await timerApi.stop();
      await queryClient.invalidateQueries({ queryKey: queryKeys.timer.all() });
      await queryClient.invalidateQueries({ queryKey: queryKeys.nodes.all() });
    } finally {
      setMutating(false);
    }
  }, [queryClient]);

  const loading = (isPending && isAuthenticated) || mutating;

  return (
    <TimerContext.Provider
      value={{ activeTimer, elapsed, loading, start, stop, refresh }}
    >
      {children}
    </TimerContext.Provider>
  );
}
