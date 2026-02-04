import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { dashboardApi } from '@/api/dashboard';
import { nodesApi } from '@/api/nodes';
import { activityApi } from '@/api/activity';
import { Section, TimerWidget, ActivityFeed } from '@/components/organisms';
import { StatCard, TaskItem } from '@/components/molecules';
import type { Dashboard, Node, ActivityEntry } from '@/types';

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 18) return 'Good afternoon';
  return 'Good evening';
}

export function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [tasks, setTasks] = useState<Node[]>([]);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const [dash, nodeList, actList] = await Promise.all([
          dashboardApi.get(),
          nodesApi.list({ status: 'in_progress' }),
          activityApi.list({ limit: 5 }),
        ]);
        setDashboard(dash);
        setTasks(nodeList);
        setActivity(actList);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : 'Failed to load dashboard');
      }
    })();
  }, []);

  const firstName = user?.name?.split(' ')[0] ?? 'there';
  const inProgress = dashboard?.nodes_by_status?.in_progress ?? 0;
  const done = dashboard?.nodes_by_status?.done ?? 0;

  return (
    <div className="content-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">{getGreeting()}, {firstName}</h1>
          <p className="page-subtitle">
            {tasks.length > 0
              ? `You have ${tasks.length} task${tasks.length === 1 ? '' : 's'} in progress`
              : 'No tasks in progress'}
          </p>
        </div>
      </div>

      {error && <p style={{ color: 'var(--status-blocked)' }}>{error}</p>}

      <div className="stats-grid">
        <StatCard label="Total Tasks" value={dashboard?.total_nodes ?? 0} />
        <StatCard label="In Progress" value={inProgress} />
        <StatCard label="Completed" value={done} />
        <StatCard label="Projects" value={dashboard?.total_projects ?? 0} />
      </div>

      <div className="content-grid">
        <Section
          title="In Progress"
          action={
            <span
              className="section-action"
              style={{ cursor: 'pointer' }}
              onClick={() => navigate('/projects')}
            >
              View all
            </span>
          }
          noPadding
        >
          {tasks.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">
                <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12" /></svg>
              </div>
              <div className="empty-state-title">All caught up!</div>
              <div className="empty-state-text">No tasks in progress right now</div>
            </div>
          ) : (
            tasks.map((node) => (
              <TaskItem
                key={node.id}
                title={node.title}
                meta={`${node.node_type} • ${node.status}`}
                priority={
                  node.priority === 'high' ? 'high' :
                  node.priority === 'low' ? 'low' : 'medium'
                }
                onClick={() => navigate(`/nodes/${node.id}`)}
              />
            ))
          )}
        </Section>

        <div>
          <TimerWidget />
          <Section title="Recent Activity">
            <ActivityFeed entries={activity} emptyText="No recent activity" />
          </Section>
        </div>
      </div>
    </div>
  );
}
