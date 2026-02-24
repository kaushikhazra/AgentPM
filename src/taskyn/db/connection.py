"""Database connection management for Taskyn."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from taskyn.config import get_database_path, ensure_db_directory

# Global connection (single-threaded use)
_connection: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    """Get the database connection, creating it if necessary."""
    global _connection

    if _connection is None:
        ensure_db_directory()
        db_path = get_database_path()
        _connection = sqlite3.connect(str(db_path), check_same_thread=False)
        _connection.row_factory = sqlite3.Row

        # Enable foreign keys
        _connection.execute("PRAGMA foreign_keys = ON")

        # Initialize schema (safe to run multiple times due to IF NOT EXISTS)
        _init_schema()

    return _connection


def _init_schema() -> None:
    """Initialize the database schema (internal use)."""
    global _connection

    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path) as f:
        schema_sql = f.read()

    _connection.executescript(schema_sql)
    _connection.commit()

    _run_migrations()


def _run_migrations() -> None:
    """Run schema migrations for existing databases."""
    global _connection

    # Migration: add type column to companies
    company_cols = [
        row[1] for row in _connection.execute("PRAGMA table_info(companies)").fetchall()
    ]
    if "type" not in company_cols:
        _connection.execute("ALTER TABLE companies ADD COLUMN type TEXT DEFAULT 'discovery'")
        _connection.commit()

    # Migration: add type column to projects
    project_cols = [
        row[1] for row in _connection.execute("PRAGMA table_info(projects)").fetchall()
    ]
    if "type" not in project_cols:
        _connection.execute("ALTER TABLE projects ADD COLUMN type TEXT DEFAULT 'discovery'")
        _connection.commit()

    # Migration: add actual_time column to nodes
    columns = [
        row[1] for row in _connection.execute("PRAGMA table_info(nodes)").fetchall()
    ]
    if "actual_time" not in columns:
        _connection.execute("ALTER TABLE nodes ADD COLUMN actual_time INTEGER DEFAULT 0")
        _connection.commit()
        _backfill_actual_time()

    # Migration: add actor column to time_entries
    te_cols = [
        row[1] for row in _connection.execute("PRAGMA table_info(time_entries)").fetchall()
    ]
    if "actor" not in te_cols:
        _connection.execute("ALTER TABLE time_entries ADD COLUMN actor TEXT")
        _connection.commit()

    # Migration: spec_driven v2 → v3 (re-parent, rename types, map statuses)
    _migrate_spec_driven_v3()


def _migrate_spec_driven_v3() -> None:
    """Migrate spec_driven v2 data to v3 structure.

    v2 hierarchy (5 levels, 8 node types):
        spec → requirement → design → implementation → task/verification
    v3 hierarchy (3 levels, 5 node types):
        spec → requirement/design/task → todo

    Changes:
        1. Re-parent design nodes: requirement → spec
        2. Re-parent implementation nodes: design → spec
        3. Re-parent validation/verification nodes: spec → task sibling
        4. Rename node types: task→todo, implementation→task, verification/validation→todo
        5. Map v2-only statuses to v3 equivalents
        6. Fix phase node statuses (e.g. implementation's 'todo' → task's 'draft')
    """
    global _connection

    # Guard: run if v1/v2 node types exist OR if invalid hierarchy detected
    # (e.g. a prior partial migration renamed types but didn't re-parent)
    v2_count = _connection.execute("""
        SELECT COUNT(*) FROM nodes n
        JOIN projects p ON n.project_id = p.id
        WHERE p.methodology = 'spec_driven'
          AND n.node_type IN ('implementation', 'validation',
                              'unit_verification', 'integration_verification',
                              'e2e_verification', 'functional_verification')
    """).fetchone()[0]

    invalid_parents = _connection.execute("""
        SELECT COUNT(*) FROM edges e
        JOIN nodes child ON e.source_id = child.id
        JOIN nodes parent ON e.target_id = parent.id
        JOIN projects p ON child.project_id = p.id
        WHERE p.methodology = 'spec_driven'
          AND e.edge_type = 'parent'
          AND child.node_type = 'todo'
          AND parent.node_type NOT IN ('requirement', 'design', 'task')
    """).fetchone()[0]

    if v2_count == 0 and invalid_parents == 0:
        return

    # Get all spec_driven project IDs
    project_ids = [
        row[0] for row in _connection.execute(
            "SELECT id FROM projects WHERE methodology = 'spec_driven'"
        ).fetchall()
    ]

    # --- Step 1 & 2: Re-parent design and implementation nodes to spec ---
    for project_id in project_ids:
        # Build parent map: node_id → (edge_id, parent_node_id)
        edges = _connection.execute("""
            SELECT id, source_id, target_id FROM edges
            WHERE project_id = ? AND edge_type = 'parent'
        """, (project_id,)).fetchall()

        parent_map = {}
        for edge in edges:
            parent_map[edge[1]] = (edge[0], edge[2])

        # Build node type map
        nodes = _connection.execute(
            "SELECT id, node_type FROM nodes WHERE project_id = ?",
            (project_id,),
        ).fetchall()
        node_types = {row[0]: row[1] for row in nodes}

        def find_spec_ancestor(node_id: str) -> str | None:
            """Walk up the parent chain until hitting a spec node."""
            current = node_id
            visited = set()
            while current in parent_map and current not in visited:
                visited.add(current)
                _, parent_id = parent_map[current]
                if node_types.get(parent_id) == "spec":
                    return parent_id
                current = parent_id
            return None

        # Re-parent design nodes (requirement → spec)
        for node_id, node_type in node_types.items():
            if node_type == "design" and node_id in parent_map:
                spec_id = find_spec_ancestor(node_id)
                if spec_id:
                    edge_id = parent_map[node_id][0]
                    _connection.execute(
                        "UPDATE edges SET target_id = ? WHERE id = ?",
                        (spec_id, edge_id),
                    )

        # Re-parent implementation nodes (design → spec)
        for node_id, node_type in node_types.items():
            if node_type == "implementation" and node_id in parent_map:
                spec_id = find_spec_ancestor(node_id)
                if spec_id:
                    edge_id = parent_map[node_id][0]
                    _connection.execute(
                        "UPDATE edges SET target_id = ? WHERE id = ?",
                        (spec_id, edge_id),
                    )

        # Re-parent leaf nodes that are direct children of spec.
        # In v3 these become todos which must be children of requirement/design/task.
        # Also handles already-migrated 'todo' nodes stuck under spec from partial runs.
        _LEAF_TYPES = {
            "task", "todo", "validation", "unit_verification",
            "integration_verification", "e2e_verification",
            "functional_verification",
        }
        # Valid parents for leaf/todo nodes in v3
        _VALID_TODO_PARENTS = {"requirement", "design", "task", "implementation"}
        for node_id, node_type in node_types.items():
            if node_type in _LEAF_TYPES and node_id in parent_map:
                _, parent_id = parent_map[node_id]
                parent_type = node_types.get(parent_id)
                if parent_type not in _VALID_TODO_PARENTS:
                    # Find the spec ancestor to locate valid siblings
                    spec_id = find_spec_ancestor(node_id)
                    if spec_id is None and parent_type == "spec":
                        spec_id = parent_id
                    if spec_id is None:
                        continue

                    # Find first design sibling under this spec
                    new_parent = None
                    for sib_id, sib_type in node_types.items():
                        if sib_id == node_id:
                            continue
                        if sib_type == "design" and sib_id in parent_map:
                            _, sib_parent = parent_map[sib_id]
                            if sib_parent == spec_id:
                                new_parent = sib_id
                                break
                    # Fallback: any implementation, task, or requirement sibling
                    if new_parent is None:
                        for sib_id, sib_type in node_types.items():
                            if sib_id == node_id:
                                continue
                            if sib_type in ("implementation", "task", "requirement") and sib_id in parent_map:
                                _, sib_parent = parent_map[sib_id]
                                if sib_parent == spec_id:
                                    new_parent = sib_id
                                    break
                    if new_parent:
                        edge_id = parent_map[node_id][0]
                        _connection.execute(
                            "UPDATE edges SET target_id = ? WHERE id = ?",
                            (new_parent, edge_id),
                        )
                        parent_map[node_id] = (edge_id, new_parent)

    # --- Step 3: Rename node types (order matters!) ---
    spec_driven_filter = (
        "project_id IN (SELECT id FROM projects WHERE methodology = 'spec_driven')"
    )

    # v2 'task' → 'todo' (must run before implementation → task)
    _connection.execute(f"""
        UPDATE nodes SET node_type = 'todo'
        WHERE node_type = 'task' AND {spec_driven_filter}
    """)

    # 'implementation' → 'task'
    _connection.execute(f"""
        UPDATE nodes SET node_type = 'task'
        WHERE node_type = 'implementation' AND {spec_driven_filter}
    """)

    # verification/validation types → 'todo'
    _connection.execute(f"""
        UPDATE nodes SET node_type = 'todo'
        WHERE node_type IN ('validation', 'unit_verification',
                            'integration_verification', 'e2e_verification',
                            'functional_verification')
          AND {spec_driven_filter}
    """)

    # --- Step 4: Map v2-only statuses to v3 equivalents ---
    v2_status_map = {
        "approved": "active",
        "pending": "todo",
        "rework": "active",
        "rejected": "draft",
        "passed": "done",
        "failed": "todo",
        "in_review": "active",
        "blocked": "draft",
    }
    for old_status, new_status in v2_status_map.items():
        _connection.execute(f"""
            UPDATE nodes SET status = ?
            WHERE status = ? AND {spec_driven_filter}
        """, (new_status, old_status))

    # --- Step 5: Fix phase node statuses ---
    # Phase nodes (spec, requirement, design, task) only allow: draft, active, done, cancelled
    # After step 3, former 'implementation' nodes are now 'task' type
    # and may have statuses like 'todo' or 'in_progress' which are invalid for phase nodes
    _connection.execute(f"""
        UPDATE nodes SET status = 'draft'
        WHERE status = 'todo'
          AND node_type IN ('spec', 'requirement', 'design', 'task')
          AND {spec_driven_filter}
    """)

    _connection.execute(f"""
        UPDATE nodes SET status = 'active'
        WHERE status = 'in_progress'
          AND node_type IN ('spec', 'requirement', 'design', 'task')
          AND {spec_driven_filter}
    """)

    _connection.execute(f"""
        UPDATE nodes SET status = 'draft'
        WHERE status IN ('backlog', 'ready')
          AND {spec_driven_filter}
    """)

    _connection.commit()


def _backfill_actual_time() -> None:
    """One-time backfill of actual_time for all existing nodes."""
    global _connection

    # Step 1: Calculate own time for all nodes from time_entries (seconds)
    _connection.execute("""
        UPDATE nodes SET actual_time = COALESCE((
            SELECT SUM(
                CASE
                    WHEN te.started_at = te.ended_at THEN te.duration_minutes * 60
                    WHEN te.ended_at IS NOT NULL THEN CAST((julianday(te.ended_at) - julianday(te.started_at)) * 86400 AS INTEGER)
                    ELSE 0
                END
            )
            FROM time_entries te
            WHERE te.node_id = nodes.id AND te.ended_at IS NOT NULL
        ), 0)
    """)
    _connection.commit()

    # Step 2: Propagate bottom-up through parent edges
    # Each pass recalculates parent = own_entries_time + sum(children.actual_time)
    # Repeat until stable (handles multi-level hierarchies)
    for _ in range(10):  # Max 10 levels deep (practically never more than 3-4)
        prev_sum = _connection.execute(
            "SELECT COALESCE(SUM(actual_time), 0) FROM nodes"
        ).fetchone()[0]

        _connection.execute("""
            UPDATE nodes SET actual_time = (
                COALESCE((
                    SELECT SUM(
                        CASE
                            WHEN te.started_at = te.ended_at THEN te.duration_minutes * 60
                            WHEN te.ended_at IS NOT NULL THEN CAST((julianday(te.ended_at) - julianday(te.started_at)) * 86400 AS INTEGER)
                            ELSE 0
                        END
                    )
                    FROM time_entries te
                    WHERE te.node_id = nodes.id AND te.ended_at IS NOT NULL
                ), 0)
                +
                COALESCE((
                    SELECT SUM(child.actual_time)
                    FROM nodes child
                    JOIN edges e ON e.source_id = child.id
                    WHERE e.target_id = nodes.id AND e.edge_type = 'parent'
                ), 0)
            )
            WHERE id IN (
                SELECT DISTINCT e.target_id
                FROM edges e
                WHERE e.edge_type = 'parent'
            )
        """)
        _connection.commit()

        new_sum = _connection.execute(
            "SELECT COALESCE(SUM(actual_time), 0) FROM nodes"
        ).fetchone()[0]
        if new_sum == prev_sum:
            break


def close_connection() -> None:
    """Close the database connection."""
    global _connection

    if _connection is not None:
        _connection.close()
        _connection = None


def init_database() -> None:
    """Initialize the database schema.

    Note: This is called automatically on first connection.
    Can be called explicitly to ensure schema exists.
    """
    get_connection()  # Schema init happens automatically on connection


@contextmanager
def transaction() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database transactions."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def execute(sql: str, params: tuple = ()) -> sqlite3.Cursor:
    """Execute a SQL statement and return the cursor."""
    conn = get_connection()
    return conn.execute(sql, params)


def executemany(sql: str, params_list: list[tuple]) -> sqlite3.Cursor:
    """Execute a SQL statement with multiple parameter sets."""
    conn = get_connection()
    return conn.executemany(sql, params_list)


def fetchone(sql: str, params: tuple = ()) -> sqlite3.Row | None:
    """Execute a SQL statement and fetch one result."""
    cursor = execute(sql, params)
    return cursor.fetchone()


def fetchall(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    """Execute a SQL statement and fetch all results."""
    cursor = execute(sql, params)
    return cursor.fetchall()


def commit() -> None:
    """Commit the current transaction."""
    conn = get_connection()
    conn.commit()
