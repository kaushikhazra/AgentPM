import { useEffect, useState, useCallback } from 'react';
import { nodesApi } from '@/api/nodes';
import { timerApi } from '@/api/timer';
import { Button } from '@/components/atoms';
import { StatCard } from '@/components/molecules';
import { Section, Modal } from '@/components/organisms';
import { TimerWidget } from '@/components/organisms/TimerWidget';
import type { Node, TimeEntry } from '@/types';

function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}h ${m.toString().padStart(2, '0')}m`;
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

function isToday(iso: string): boolean {
  const d = new Date(iso);
  const now = new Date();
  return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate();
}

function isYesterday(iso: string): boolean {
  const d = new Date(iso);
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  return d.getFullYear() === yesterday.getFullYear() && d.getMonth() === yesterday.getMonth() && d.getDate() === yesterday.getDate();
}

interface TimeEntryWithNode extends TimeEntry {
  nodeTitle?: string;
}

export function TrackerPage() {
  const [entries, setEntries] = useState<TimeEntryWithNode[]>([]);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('today');

  // Manual entry modal
  const [showManual, setShowManual] = useState(false);
  const [manualNodeId, setManualNodeId] = useState('');
  const [manualDuration, setManualDuration] = useState('60');
  const [manualNotes, setManualNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [allNodes, setAllNodes] = useState<Node[]>([]);

  // Delete confirmation modal
  const [showDelete, setShowDelete] = useState(false);
  const [deleteEntryId, setDeleteEntryId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const loadData = useCallback(async () => {
    try {
      // Load all nodes to get time entries from them
      const nodeList = await nodesApi.list();
      setAllNodes(nodeList);

      // Collect all time entries from all nodes
      const allEntries: TimeEntryWithNode[] = [];
      for (const node of nodeList) {
        if (node.time_entries && node.time_entries.length > 0) {
          node.time_entries.forEach((te) => {
            allEntries.push({ ...te, nodeTitle: node.title });
          });
        }
      }

      // Sort by started_at descending
      allEntries.sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime());
      setEntries(allEntries);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleManualEntry = async () => {
    if (!manualNodeId || !manualDuration) return;
    setSaving(true);
    try {
      await timerApi.logTime({
        node_id: manualNodeId,
        duration_minutes: parseInt(manualDuration, 10),
        notes: manualNotes.trim() || undefined,
      });
      setShowManual(false);
      setManualNodeId('');
      setManualDuration('60');
      setManualNotes('');
      await loadData();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteEntry = async () => {
    if (!deleteEntryId) return;
    setDeleting(true);
    try {
      await timerApi.deleteTimeEntry(deleteEntryId);
      setShowDelete(false);
      setDeleteEntryId(null);
      await loadData();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to delete');
    } finally {
      setDeleting(false);
    }
  };

  const openDeleteConfirm = (entryId: string) => {
    setDeleteEntryId(entryId);
    setShowDelete(true);
  };

  // Filter entries by tab
  const filteredEntries = entries.filter((e) => {
    if (tab === 'today') return isToday(e.started_at);
    if (tab === 'yesterday') return isYesterday(e.started_at);
    return true; // weekly — show all
  });

  // Stats
  const todayMinutes = entries
    .filter((e) => isToday(e.started_at))
    .reduce((sum, e) => sum + (e.duration_minutes ?? 0), 0);

  const weekAgo = new Date();
  weekAgo.setDate(weekAgo.getDate() - 7);
  const weekMinutes = entries
    .filter((e) => new Date(e.started_at) >= weekAgo)
    .reduce((sum, e) => sum + (e.duration_minutes ?? 0), 0);

  const totalMinutes = entries.reduce((sum, e) => sum + (e.duration_minutes ?? 0), 0);

  // Group weekly entries by day
  const dayGroups: { label: string; entries: TimeEntryWithNode[] }[] = [];
  if (tab === 'weekly') {
    const grouped = new Map<string, TimeEntryWithNode[]>();
    filteredEntries.forEach((e) => {
      const key = formatDate(e.started_at);
      const arr = grouped.get(key) ?? [];
      arr.push(e);
      grouped.set(key, arr);
    });
    grouped.forEach((ents, label) => {
      dayGroups.push({ label, entries: ents });
    });
  }

  return (
    <div className="content-wrapper">
      <div className="page-header">
        <div>
          <h1 className="page-title">Time Log</h1>
          <p className="page-subtitle">Track and review your time entries</p>
        </div>
        <Button variant="primary" onClick={() => setShowManual(true)}>
          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" strokeWidth="2">
            <path d="M12 5v14" /><path d="M5 12h14" />
          </svg>
          Manual Entry
        </Button>
      </div>

      {error && <p style={{ color: 'var(--status-blocked)', marginBottom: 16 }}>{error}</p>}

      <div className="stats-grid">
        <StatCard label="Today" value={formatDuration(todayMinutes)} />
        <StatCard label="This Week" value={formatDuration(weekMinutes)} />
        <StatCard label="Total" value={formatDuration(totalMinutes)} />
        <StatCard label="Entries" value={entries.length} />
      </div>

      <div className="content-grid">
        <div>
          {/* Timer widget */}
          <div className="mb-lg">
            <TimerWidget />
          </div>

          {/* Time Entries */}
          <Section
            title="Time Entries"
            action={
              <div className="section-tabs">
                <button
                  className={`section-tab${tab === 'today' ? ' active' : ''}`}
                  onClick={() => setTab('today')}
                >Today</button>
                <button
                  className={`section-tab${tab === 'yesterday' ? ' active' : ''}`}
                  onClick={() => setTab('yesterday')}
                >Yesterday</button>
                <button
                  className={`section-tab${tab === 'weekly' ? ' active' : ''}`}
                  onClick={() => setTab('weekly')}
                >This Week</button>
              </div>
            }
          >
            {tab !== 'weekly' ? (
              filteredEntries.length === 0 ? (
                <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-tertiary)' }}>
                  No time entries {tab === 'today' ? 'today' : 'yesterday'}
                </div>
              ) : (
                filteredEntries.map((entry) => {
                  const dur = entry.duration_minutes ?? 0;
                  const isRunning = !entry.stopped_at;
                  return (
                    <div
                      key={entry.id}
                      className={`time-entry-item${isRunning ? ' time-entry-active' : ''}`}
                    >
                      <div className={`time-entry-dot${isRunning ? ' active' : ''}`} />
                      <div className="time-entry-content">
                        <div className="time-entry-title">{entry.nodeTitle ?? entry.node_id.slice(0, 8)}</div>
                        <div className="time-entry-meta">
                          {formatTime(entry.started_at)}
                          {entry.stopped_at ? ` - ${formatTime(entry.stopped_at)}` : ' - Running'}
                          {entry.notes ? ` • ${entry.notes}` : ''}
                        </div>
                      </div>
                      <div className={`time-entry-duration${isRunning ? ' active' : ''}`}>
                        {formatDuration(dur)}
                      </div>
                      {!isRunning && (
                        <button
                          className="time-entry-delete"
                          onClick={() => openDeleteConfirm(entry.id)}
                          aria-label="Delete time entry"
                        >
                          <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" strokeWidth="2">
                            <path d="M3 6h18" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" /><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                          </svg>
                        </button>
                      )}
                    </div>
                  );
                })
              )
            ) : (
              dayGroups.length === 0 ? (
                <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-tertiary)' }}>
                  No time entries this week
                </div>
              ) : (
                dayGroups.map((group) => (
                  <div key={group.label} className="time-entry-day-group">
                    <div className="time-entry-day-header">{group.label}</div>
                    {group.entries.map((entry) => {
                      const isRunning = !entry.stopped_at;
                      return (
                        <div key={entry.id} className="time-entry-item">
                          <div className="time-entry-dot" />
                          <div className="time-entry-content">
                            <div className="time-entry-title">{entry.nodeTitle ?? entry.node_id.slice(0, 8)}</div>
                            <div className="time-entry-meta">{entry.notes ?? ''}</div>
                          </div>
                          <div className="time-entry-duration">
                            {formatDuration(entry.duration_minutes ?? 0)}
                          </div>
                          {!isRunning && (
                            <button
                              className="time-entry-delete"
                              onClick={() => openDeleteConfirm(entry.id)}
                              aria-label="Delete time entry"
                            >
                              <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" strokeWidth="2">
                                <path d="M3 6h18" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" /><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                              </svg>
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ))
              )
            )}
          </Section>
        </div>

        {/* Right sidebar — will show weekly overview */}
        <div>
          <Section title="Summary">
            <div style={{ padding: '8px 0', color: 'var(--text-secondary)', fontSize: 13 }}>
              <div style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span>Today</span>
                  <span style={{ fontWeight: 600 }}>{formatDuration(todayMinutes)}</span>
                </div>
                <div className="project-time-bar">
                  <div
                    className="project-time-fill"
                    style={{ width: `${Math.min(100, (todayMinutes / 480) * 100)}%` }}
                  />
                </div>
              </div>
              <div style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span>This Week</span>
                  <span style={{ fontWeight: 600 }}>{formatDuration(weekMinutes)}</span>
                </div>
                <div className="project-time-bar">
                  <div
                    className="project-time-fill"
                    style={{ width: `${Math.min(100, (weekMinutes / 2400) * 100)}%` }}
                  />
                </div>
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span>Total</span>
                  <span style={{ fontWeight: 600 }}>{formatDuration(totalMinutes)}</span>
                </div>
                <div className="project-time-bar">
                  <div className="project-time-fill" style={{ width: '100%' }} />
                </div>
              </div>
            </div>
          </Section>
        </div>
      </div>

      {/* Manual Entry Modal */}
      <Modal
        open={showManual}
        onClose={() => setShowManual(false)}
        title="Add Time Entry"
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowManual(false)}>Cancel</Button>
            <Button variant="primary" onClick={handleManualEntry} disabled={saving}>
              {saving ? 'Saving...' : 'Save Entry'}
            </Button>
          </>
        }
      >
        <div className="form-group">
          <label className="form-label">Task</label>
          <select
            className="form-select"
            value={manualNodeId}
            onChange={(e) => setManualNodeId(e.target.value)}
          >
            <option value="">Select a task...</option>
            {allNodes.map((n) => (
              <option key={n.id} value={n.id}>{n.title}</option>
            ))}
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Duration (minutes)</label>
          <input
            className="form-input"
            type="number"
            min="1"
            value={manualDuration}
            onChange={(e) => setManualDuration(e.target.value)}
          />
        </div>
        <div className="form-group">
          <label className="form-label">Notes (optional)</label>
          <textarea
            className="form-input"
            placeholder="Add any additional notes..."
            value={manualNotes}
            onChange={(e) => setManualNotes(e.target.value)}
          />
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        open={showDelete}
        onClose={() => { setShowDelete(false); setDeleteEntryId(null); }}
        title="Delete Time Entry"
        footer={
          <>
            <Button variant="secondary" onClick={() => { setShowDelete(false); setDeleteEntryId(null); }}>Cancel</Button>
            <Button variant="danger" onClick={handleDeleteEntry} disabled={deleting}>
              {deleting ? 'Deleting...' : 'Delete Entry'}
            </Button>
          </>
        }
      >
        <p style={{ marginBottom: 16 }}>
          Are you sure you want to delete this time entry?
        </p>
        <p className="text-secondary">
          This action cannot be undone.
        </p>
      </Modal>
    </div>
  );
}
