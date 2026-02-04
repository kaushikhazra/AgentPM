import { Icon, type IconName } from '@/components/atoms';

type ActivityType = 'complete' | 'create' | 'update' | 'time';

interface ActivityItemProps {
  type: ActivityType;
  text: string;
  highlight?: string;
  time: string;
}

const iconMap: Record<ActivityType, IconName> = {
  complete: 'check',
  create: 'plus',
  update: 'edit',
  time: 'tracker',
};

export function ActivityItem({ type, text, highlight, time }: ActivityItemProps) {
  return (
    <div className="activity-item">
      <div className={`activity-icon ${type}`}>
        <Icon name={iconMap[type]} size={16} />
      </div>
      <div className="activity-content">
        <div className="activity-text">
          {text} {highlight && <strong>{highlight}</strong>}
        </div>
        <div className="activity-time">{time}</div>
      </div>
    </div>
  );
}
