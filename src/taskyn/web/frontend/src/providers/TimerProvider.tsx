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
import { useActiveTimers } from '@/hooks/queries/useTimerQuery';
import type { ActiveTimer } from '@/types';

export interface TimerContextValue {
  /** All active timers across all actors (from /timer/active). */
  activeTimers: ActiveTimer[];
  /** Map of timer id → elapsed seconds for all active timers. */
  elapsedMap: Record<string, number>;
  loading: boolean;
  start: (nodeId: string, notes?: string) => Promise<void>;
  stop: (entryId?: string) => Promise<void>;
  refresh: () => Promise<void>;
}

export const TimerContext = createContext<TimerContextValue | null>(null);

export function TimerProvider({ children }: { children: ReactNode }) {
  const { user, loading: authLoading } = useAuth();
  const queryClient = useQueryClient();

  const isAuthenticated = !authLoading && !!user;

  // Single poll for all active timers — 1s refetchInterval when authenticated
  const { data: activeTimers = [], isPending } = useActiveTimers({
    enabled: isAuthenticated,
    refetchInterval: isAuthenticated ? 1_000 : undefined,
  });

  const [elapsedMap, setElapsedMap] = useState<Record<string, number>>({});
  const [mutating, setMutating] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const calcElapsed = useCallback((startedAt: string): number => {
    return Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000);
  }, []);

  // Manage the elapsed tick interval for all active timers
  useEffect(() => {
    const tick = () => {
      const map: Record<string, number> = {};
      for (const t of activeTimers) {
        map[t.id] = calcElapsed(t.started_at);
      }
      setElapsedMap(map);
    };

    tick();
    intervalRef.current = setInterval(tick, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [activeTimers, calcElapsed]);

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

  const stop = useCallback(async (entryId?: string) => {
    setMutating(true);
    try {
      await timerApi.stop(entryId);
      await queryClient.invalidateQueries({ queryKey: queryKeys.timer.all() });
      await queryClient.invalidateQueries({ queryKey: queryKeys.nodes.all() });
    } finally {
      setMutating(false);
    }
  }, [queryClient]);

  const loading = (isPending && isAuthenticated) || mutating;

  return (
    <TimerContext.Provider
      value={{ activeTimers, elapsedMap, loading, start, stop, refresh }}
    >
      {children}
    </TimerContext.Provider>
  );
}
