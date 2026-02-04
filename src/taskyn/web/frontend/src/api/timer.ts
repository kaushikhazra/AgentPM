import { api } from './client';
import type { ActiveTimer, TimeEntry, TimeEntryCreate } from '@/types';

export const timerApi = {
  start: (nodeId: string, notes?: string) =>
    api.post<TimeEntry>('/timer/start', { node_id: nodeId, notes }),

  stop: (entryId?: string) =>
    api.post<TimeEntry>('/timer/stop', entryId ? { entry_id: entryId } : {}),

  getCurrent: () =>
    api.get<ActiveTimer | null>('/timer/current'),

  logTime: (data: TimeEntryCreate) =>
    api.post<TimeEntry>('/time-entries', data),
};
