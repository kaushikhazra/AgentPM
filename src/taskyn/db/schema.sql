-- Taskyn Database Schema
-- Graph-based methodology-agnostic project management

-- ============================================================
-- ANCHOR LAYER: Stable across all methodologies
-- ============================================================

-- Companies act as top-level containers/contexts
CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    type TEXT DEFAULT 'discovery' CHECK (type IN ('discovery', 'potential', 'matured', 'engaged', 'active', 'dormant')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects belong to a company and specify their methodology
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    type TEXT DEFAULT 'discovery' CHECK (type IN ('discovery', 'potential', 'matured', 'engaged', 'active', 'dormant')),
    methodology TEXT NOT NULL DEFAULT 'classic_agile',
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'on_hold', 'completed', 'archived')),
    config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Milestones remain universal (optional groupings within a project)
CREATE TABLE IF NOT EXISTS milestones (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    target_date DATE,
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'completed')),
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- GRAPH LAYER: Methodology-defined nodes and edges
-- ============================================================

-- Generic work items (nodes in the graph)
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    milestone_id TEXT REFERENCES milestones(id) ON DELETE SET NULL,

    -- Type system (validated by methodology)
    node_type TEXT NOT NULL,

    -- Common fields (all nodes have these)
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    assignee TEXT,

    -- Effort tracking (optional, depends on node_type)
    estimated_minutes INTEGER,
    story_points INTEGER,
    actual_time INTEGER DEFAULT 0,

    -- Metadata
    priority TEXT DEFAULT 'medium',
    blocked_reason TEXT,

    -- Extensible properties (methodology-specific fields)
    properties JSON,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Relationships between nodes (edges in the graph)
CREATE TABLE IF NOT EXISTS edges (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- The relationship
    source_id TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    target_id TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    edge_type TEXT NOT NULL,

    -- Edge metadata
    properties JSON,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Prevent duplicate edges of same type between same nodes
    UNIQUE(source_id, target_id, edge_type)
);

-- ============================================================
-- TRACKING LAYER: Universal, attaches to any node
-- ============================================================

-- Time entries attach to any node
CREATE TABLE IF NOT EXISTS time_entries (
    id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    duration_minutes INTEGER,
    notes TEXT,
    source TEXT DEFAULT 'manual',
    actor TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tags can attach to any node
CREATE TABLE IF NOT EXISTS tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    color TEXT
);

CREATE TABLE IF NOT EXISTS node_tags (
    node_id TEXT REFERENCES nodes(id) ON DELETE CASCADE,
    tag_id TEXT REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (node_id, tag_id)
);

-- Activity log tracks all changes
CREATE TABLE IF NOT EXISTS activity_log (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    node_type TEXT,
    action TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    actor TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- INDEXES
-- ============================================================

-- Anchor layer
CREATE INDEX IF NOT EXISTS idx_projects_company ON projects(company_id);
CREATE INDEX IF NOT EXISTS idx_projects_methodology ON projects(methodology);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_milestones_project ON milestones(project_id);
CREATE INDEX IF NOT EXISTS idx_milestones_status ON milestones(status);

-- Graph layer
CREATE INDEX IF NOT EXISTS idx_nodes_project ON nodes(project_id);
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_nodes_status ON nodes(status);
CREATE INDEX IF NOT EXISTS idx_nodes_assignee ON nodes(assignee);
CREATE INDEX IF NOT EXISTS idx_nodes_milestone ON nodes(milestone_id);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(edge_type);
CREATE INDEX IF NOT EXISTS idx_edges_project ON edges(project_id);

-- Tracking layer
CREATE INDEX IF NOT EXISTS idx_time_entries_node ON time_entries(node_id);
CREATE INDEX IF NOT EXISTS idx_time_entries_started ON time_entries(started_at);
-- idx_time_entries_actor_active created in connection.py migration (after actor column exists)
CREATE INDEX IF NOT EXISTS idx_activity_log_entity ON activity_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_node_type ON activity_log(node_type);
CREATE INDEX IF NOT EXISTS idx_activity_log_created ON activity_log(created_at);
CREATE INDEX IF NOT EXISTS idx_activity_log_actor ON activity_log(actor);
