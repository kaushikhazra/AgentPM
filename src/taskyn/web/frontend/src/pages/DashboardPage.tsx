import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useTimer } from '@/hooks/useTimer';
import { dashboardApi } from '@/api/dashboard';
import { nodesApi } from '@/api/nodes';
import { activityApi } from '@/api/activity';
import { projectsApi } from '@/api/projects';
import { Section, TimerWidget, ActivityFeed } from '@/components/organisms';
import { StatCard, TaskItem } from '@/components/molecules';
import type { Dashboard, Node, ActivityEntry, Project } from '@/types';

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 18) return 'Good afternoon';
  return 'Good evening';
}

function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m}m`;
  return `${h}h ${m.toString().padStart(2, '0')}m`;
}

export function DashboardPage() {
  const { user } = useAuth();
  const { elapsed } = useTimer();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [tasks, setTasks] = useState<Node[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [activity, setActivity] = useState<ActivityEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set());

  const loadData = useCallback(async () => {
    try {
      const [dash, nodeList, actList, projList] = await Promise.all([
        dashboardApi.get(),
        nodesApi.list({ status: 'in_progress' }),
        activityApi.list({ limit: 5 }),
        projectsApi.list(),
      ]);
      setDashboard(dash);
      setTasks(nodeList);
      setActivity(actList);
      setProjects(projList);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleTaskComplete = async (nodeId: string, checked: boolean) => {
    if (checked) {
      // Optimistic update
      setCompletedIds((prev) => new Set(prev).add(nodeId));
      try {
        await nodesApi.complete(nodeId);
        // Refresh tasks list
        const updated = await nodesApi.list({ status: 'in_progress' });
        setTasks(updated);
        setCompletedIds((prev) => {
          const next = new Set(prev);
          next.delete(nodeId);
          return next;
        });
      } catch (e: unknown) {
        setCompletedIds((prev) => {
          const next = new Set(prev);
          next.delete(nodeId);
          return next;
        });
        setError(e instanceof Error ? e.message : 'Failed to complete task');
      }
    }
  };

  const getProjectName = (projectId: string): string => {
    const project = projects.find((p) => p.id === projectId);
    return project?.name ?? 'Project';
  };

  const firstName = user?.name?.split(' ')[0] ?? 'there';
  const inProgress = dashboard?.nodes_by_status?.in_progress ?? 0;
  const done = dashboard?.nodes_by_status?.done ?? 0;

  // Calculate time tracked today (use timer elapsed as a simple approximation)
  const timeTrackedMinutes = Math.floor(elapsed / 60);

  return (
    <div className="content-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">{getGreeting()}, {firstName}</h1>
          <p className="page-subtitle">
            {tasks.length > 0
              ? `You have ${tasks.length} task${tasks.length === 1 ? '' : 's'} due today`
              : 'No tasks due today'}
          </p>
        </div>
      </div>

      {error && <p style={{ color: 'var(--status-blocked)' }}>{error}</p>}

      {loading && <p className="text-secondary">Loading dashboard...</p>}

      <div className="stats-grid">
        <StatCard label="Tasks Due Today" value={tasks.length} />
        <StatCard label="In Progress" value={inProgress} />
        <StatCard label="Completed This Week" value={done} />
        <StatCard label="Time Tracked Today" value={formatDuration(timeTrackedMinutes)} />
      </div>

      <div className="content-grid">
        <Section
          title="Today's Tasks"
          action={
            <span
              className="section-action"
              style={{ cursor: 'pointer' }}
              onClick={() => navigate('/planner')}
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
              <div className="empty-state-text">No tasks due today</div>
            </div>
          ) : (
            tasks.map((node) => (
              <TaskItem
                key={node.id}
                title={node.title}
                meta={`${getProjectName(node.project_id)} • Due today`}
                priority={
                  node.priority === 'high' ? 'high' :
                  node.priority === 'low' ? 'low' : 'medium'
                }
                checked={completedIds.has(node.id)}
                onCheck={(checked) => handleTaskComplete(node.id, checked)}
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
