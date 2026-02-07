/* Taskyn TypeScript types — mirrors backend Pydantic models & MCP responses. */

// ============================================================
// Entity Type (Lifecycle Stages)
// ============================================================

export const ENTITY_TYPES = ['discovery', 'potential', 'matured', 'engaged', 'active', 'dormant'] as const;
export type EntityType = typeof ENTITY_TYPES[number];

// Fixed colors (theme-independent)
export const ENTITY_TYPE_COLORS: Record<EntityType, string> = {
  discovery: '#0077B6',  // Ocean Blue
  potential: '#FFD60A',  // Chrome Yellow
  matured: '#2A9D8F',    // Ocean Green
  engaged: '#606C38',    // Moss Green
  active: '#E63946',     // Coral Red
  dormant: '#6C757D',    // Grey
};

// ============================================================
// Companies
// ============================================================

export interface Company {
  id: string;
  name: string;
  description: string | null;
  type: EntityType;
  created_at: string;
  updated_at: string;
  stats?: CompanyStats;
}

export interface CompanyStats {
  total_projects: number;
  total_nodes: number;
  completed_nodes: number;
  completion_percentage: number;
  total_time_minutes: number;
}

export interface CompanyCreate {
  name: string;
  description?: string;
  type?: EntityType;
}

// ============================================================
// Projects
// ============================================================

export interface Project {
  id: string;
  name: string;
  company_id: string | null;
  methodology: string;
  description: string | null;
  type: EntityType;
  status: string;
  created_at: string;
  updated_at: string;
  stats?: ProjectStats;
}

export interface ProjectStats {
  total_nodes: Record<string, number>;
  nodes_by_status: Record<string, number>;
  completion_percentage: number;
  time_total: number;
}

export interface ProjectCreate {
  company_id: string;
  name: string;
  methodology?: string;
  description?: string;
  type?: EntityType;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  status?: string;
  type?: EntityType;
  methodology?: string;
}

// ============================================================
// Nodes
// ============================================================

export interface Node {
  id: string;
  project_id: string;
  node_type: string;
  title: string;
  description: string | null;
  status: string;
  assignee: string | null;
  priority: string | null;
  milestone_id: string | null;
  properties: Record<string, unknown> | null;
  blocked_reason: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  parent_id?: string | null;
  // Composite fields from pm_get_node
  edges?: Edge[];
  outgoing_edges?: Edge[];
  incoming_edges?: Edge[];
  time_entries?: TimeEntry[];
  rollup?: NodeRollup;
}

export interface NodeCreate {
  project_id: string;
  node_type: string;
  title: string;
  description?: string;
  assignee?: string;
  priority?: string;
  milestone_id?: string;
  parent_id?: string;
}

export interface NodeUpdate {
  title?: string;
  description?: string;
  status?: string;
  assignee?: string;
  priority?: string;
  milestone_id?: string;
}

export interface NodeRollup {
  total_children: number;
  completed_children: number;
  total_time_minutes: number;
  statuses: Record<string, number>;
}

// ============================================================
// Edges
// ============================================================

export interface Edge {
  id: string;
  source_id: string;
  target_id: string;
  edge_type: string;
  created_at: string;
}

export interface EdgeCreate {
  source_id: string;
  target_id: string;
  edge_type: string;
}

// ============================================================
// Milestones
// ============================================================

export interface Milestone {
  id: string;
  project_id: string;
  name: string;
  description: string | null;
  target_date: string | null;
  status: string;
  completed_at: string | null;
  created_at: string;
}

export interface MilestoneCreate {
  project_id: string;
  name: string;
  target_date?: string;
  description?: string;
}

export interface MilestoneUpdate {
  name?: string;
  description?: string;
  target_date?: string;
}

// ============================================================
// Tags
// ============================================================

export interface Tag {
  id: string;
  name: string;
  color: string | null;
}

export interface TagCreate {
  name: string;
  color?: string;
}

export interface TagUsage {
  tag_name: string;
  usage_count: number;
}

export interface TagDeleteResult {
  deleted: boolean;
  usage_count: number;
}

// ============================================================
// Time Tracking
// ============================================================

export interface TimeEntry {
  id: string;
  node_id: string;
  duration_minutes: number | null;
  notes: string | null;
  started_at: string;
  stopped_at: string | null;
}

export interface TimeEntryCreate {
  node_id: string;
  duration_minutes: number;
  notes?: string;
}

export interface ActiveTimer {
  id: string;
  node_id: string;
  notes: string | null;
  started_at: string;
}

// ============================================================
// Dashboard & Reporting
// ============================================================

export interface Dashboard {
  total_companies: number;
  total_projects: number;
  total_nodes: number;
  nodes_by_status: Record<string, number>;
  recent_activity: ActivityEntry[];
}

export interface ActivityEntry {
  id: string;
  entity_type: string;
  entity_id: string;
  node_type: string | null;
  action: string;
  old_value: string | null;
  new_value: string | null;
  actor: string;
  notes: string | null;
  created_at: string;
}

export interface SearchResult {
  entity_type: string;
  entity_id: string;
  title: string;
  snippet: string | null;
  score: number;
}

// ============================================================
// Methodology
// ============================================================

export interface MethodologyInfo {
  name: string;
  node_types: string[];
  statuses: string[];
  transitions: Record<string, string[]>;
  hierarchy: Record<string, string[]>;
}

// ============================================================
// Auth
// ============================================================

export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface TokenResponse {
  accessToken: string;
}
