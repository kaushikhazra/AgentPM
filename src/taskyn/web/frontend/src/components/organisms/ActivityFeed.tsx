import { ActivityItem } from '@/components/molecules/ActivityItem';
import type { ActivityEntry } from '@/types';

interface ActivityFeedProps {
  entries: ActivityEntry[];
  emptyText?: string;
}

function getActivityType(action: string): 'complete' | 'create' | 'update' | 'time' {
  if (action.includes('complete') || action.includes('done')) return 'complete';
  if (action.includes('create') || action.includes('add')) return 'create';
  if (action.includes('time') || action.includes('timer')) return 'time';
  return 'update';
}

function formatRelativeTime(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins} minute${mins === 1 ? '' : 's'} ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? '' : 's'} ago`;
}

export function ActivityFeed({ entries, emptyText = 'No recent activity' }: ActivityFeedProps) {
  if (entries.length === 0) {
    return (
      <div className="empty-state">
        <p className="empty-state-desc">{emptyText}</p>
      </div>
    );
  }

  return (
    <>
      {entries.map((entry, i) => (
        <ActivityItem
          key={i}
          type={getActivityType(entry.action)}
          text={entry.action}
          highlight={entry.entity_type}
          time={formatRelativeTime(entry.created_at)}
        />
      ))}
    </>
  );
}
