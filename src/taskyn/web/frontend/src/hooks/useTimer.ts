import { useContext } from 'react';
import { TimerContext, type TimerContextValue } from '@/providers/TimerProvider';

export function useTimer(): TimerContextValue {
  const ctx = useContext(TimerContext);
  if (!ctx) throw new Error('useTimer must be used within TimerProvider');
  return ctx;
}
