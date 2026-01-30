# AgentPM Polish & Additional Methodologies - Design

## Spec-Driven Methodology

### Node Types

```python
# agentpm/methodologies/spec_driven.py

class SpecDrivenMethodology(BaseMethodology):
    name = "spec_driven"
    display_name = "Spec-Driven (Kiro-style)"

    @property
    def node_types(self):
        return {
            "spec": NodeTypeDefinition(
                name="spec",
                valid_statuses=["draft", "approved", "in_progress", "done", "cancelled"],
                initial_status="draft",
                terminal_statuses={"done", "cancelled"},
                allowed_transitions={
                    "draft": ["approved", "cancelled"],
                    "approved": ["in_progress", "draft", "cancelled"],
                    "in_progress": ["done", "draft", "cancelled"],
                    "done": [],
                    "cancelled": [],
                },
                required_properties=["requirements"],
                optional_properties=["acceptance_criteria", "approver"],
            ),
            "design": NodeTypeDefinition(
                name="design",
                valid_statuses=["draft", "in_review", "approved", "rejected"],
                initial_status="draft",
                terminal_statuses={"approved"},
                allowed_transitions={
                    "draft": ["in_review", "rejected"],
                    "in_review": ["approved", "rejected"],
                    "approved": [],
                    "rejected": ["draft"],
                },
                required_properties=[],
                optional_properties=["design_doc", "reviewer"],
            ),
            "implementation": NodeTypeDefinition(
                name="implementation",
                valid_statuses=["todo", "in_progress", "in_review", "done", "rework"],
                initial_status="todo",
                terminal_statuses={"done"},
                allowed_transitions={
                    "todo": ["in_progress"],
                    "in_progress": ["in_review", "rework"],
                    "in_review": ["done", "rework"],
                    "done": [],
                    "rework": ["in_progress"],
                },
            ),
            "validation": NodeTypeDefinition(
                name="validation",
                valid_statuses=["pending", "in_progress", "passed", "failed"],
                initial_status="pending",
                terminal_statuses={"passed"},
                allowed_transitions={
                    "pending": ["in_progress"],
                    "in_progress": ["passed", "failed"],
                    "passed": [],
                    "failed": ["pending"],  # Can retry
                },
                optional_properties=["test_results", "validator"],
            ),
        }

    @property
    def edge_types(self):
        return {
            "gates": EdgeTypeDefinition(
                name="gates",
                source_types=["design", "implementation", "validation"],
                target_types=["spec", "design", "implementation"],
                max_per_source=1,  # Each phase gates one predecessor
                allows_cycles=False,
            ),
            "validates": EdgeTypeDefinition(
                name="validates",
                source_types=["validation"],
                target_types=["implementation"],
                max_per_source=1,
                allows_cycles=False,
            ),
        }

    def get_story_type(self) -> str:
        return "spec"

    def get_task_type(self) -> str:
        return "implementation"
```

### Typical Workflow

```
1. Create Spec (draft)
   └── Approve Spec → status: approved

2. Create Design (draft) → gates Spec
   └── Submit for Review → status: in_review
   └── Approve → status: approved

3. Create Implementation (todo) → gates Design
   └── Start → status: in_progress
   └── Submit for Review → status: in_review
   └── Done → status: done

4. Create Validation (pending) → validates Implementation
   └── Start → status: in_progress
   └── Pass → status: passed
   └── OR Fail → status: failed → Implementation goes to rework
```

## Error Handling Enhancement

### Error Message Format

```python
class AgentPMError(Exception):
    """Base error with context"""
    def __init__(self, message: str, context: dict = None, suggestions: list = None):
        self.message = message
        self.context = context or {}
        self.suggestions = suggestions or []
        super().__init__(self.format())

    def format(self) -> str:
        msg = self.message
        if self.context:
            ctx = ", ".join(f"{k}={v}" for k, v in self.context.items())
            msg = f"{msg} ({ctx})"
        if self.suggestions:
            msg += "\n\nSuggestions:\n" + "\n".join(f"  - {s}" for s in self.suggestions)
        return msg

class InvalidTransitionError(ValidationError):
    def __init__(self, node_type: str, current: str, target: str, allowed: list):
        super().__init__(
            f"Cannot transition {node_type} from '{current}' to '{target}'",
            context={"node_type": node_type, "current_status": current, "target_status": target},
            suggestions=[
                f"Valid transitions from '{current}': {', '.join(allowed) or 'none'}",
                "Use pm_get_methodology_info to see all valid transitions",
            ]
        )
```

## Backup & Export

### Backup Command

```python
# cli/backup.py

@app.command()
def backup(
    output: str = typer.Option(
        None, "--output", "-o",
        help="Output path (default: ~/.agentpm/backups/agentpm_YYYYMMDD_HHMMSS.db)"
    ),
):
    """Create a backup of the database"""
    import shutil
    from datetime import datetime

    db_path = get_database_path()
    if not output:
        backup_dir = Path.home() / ".agentpm" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = backup_dir / f"agentpm_{timestamp}.db"

    shutil.copy2(db_path, output)
    console.print(f"[green]✓[/green] Backup created: {output}")

@app.command("list")
def list_backups():
    """List existing backups"""
    backup_dir = Path.home() / ".agentpm" / "backups"
    if not backup_dir.exists():
        console.print("No backups found")
        return

    backups = sorted(backup_dir.glob("agentpm_*.db"), reverse=True)
    for b in backups:
        size = b.stat().st_size / 1024  # KB
        console.print(f"  {b.name} ({size:.1f} KB)")
```

### Export Command

```python
# cli/export.py

@app.command()
def export(
    output: str = typer.Option(
        "agentpm_export.json", "--output", "-o",
        help="Output file path"
    ),
    project: str = typer.Option(
        None, "--project", "-p",
        help="Export only this project"
    ),
):
    """Export data as JSON"""
    data = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "companies": [],
        "projects": [],
        "milestones": [],
        "nodes": [],
        "edges": [],
        "time_entries": [],
        "tags": [],
    }

    if project:
        # Export single project
        p = get_project(project)
        data["projects"] = [p.model_dump()]
        data["nodes"] = [n.model_dump() for n in list_nodes(project_id=project)]
        # ... etc
    else:
        # Export everything
        data["companies"] = [c.model_dump() for c in list_companies()]
        data["projects"] = [p.model_dump() for p in list_projects()]
        # ... etc

    with open(output, "w") as f:
        json.dump(data, f, indent=2, default=str)

    console.print(f"[green]✓[/green] Exported to: {output}")
```

## Performance Testing

### Test Fixtures

```python
# tests/test_performance.py

import pytest
import time

@pytest.fixture
def large_dataset(db):
    """Create realistic dataset for performance testing"""
    # Create 10 companies
    companies = [create_company(f"Company {i}") for i in range(10)]

    # Create 10 projects per company
    projects = []
    for company in companies:
        for i in range(10):
            p = create_project(company.id, f"Project {i}", "classic_agile")
            projects.append(p)

    # Create 10 stories per project, 5 tasks per story
    for project in projects:
        for i in range(10):
            story = create_node(project.id, "story", f"Story {i}")
            for j in range(5):
                task = create_node(project.id, "task", f"Task {j}")
                create_edge(task.id, story.id, "parent")
                # Add some time entries
                for _ in range(10):
                    log_time(task.id, 30)

    return {
        "companies": len(companies),  # 10
        "projects": len(projects),    # 100
        "nodes": 100 * (10 + 50),     # 6000
        "time_entries": 100 * 50 * 10 # 50000
    }

def test_dashboard_performance(large_dataset):
    start = time.time()
    dashboard = get_dashboard()
    elapsed = (time.time() - start) * 1000
    assert elapsed < 100, f"Dashboard took {elapsed}ms (limit: 100ms)"

def test_search_performance(large_dataset):
    start = time.time()
    results = search("Story")
    elapsed = (time.time() - start) * 1000
    assert elapsed < 200, f"Search took {elapsed}ms (limit: 200ms)"
```

## Methodology Template

```python
# agentpm/methodologies/_template.py
"""
Template for creating new methodologies.

To create a new methodology:
1. Copy this file to agentpm/methodologies/your_methodology.py
2. Rename the class and update name/display_name
3. Define your node_types and edge_types
4. Implement helper methods
5. Register in agentpm/methodologies/__init__.py
"""

from .base import BaseMethodology, NodeTypeDefinition, EdgeTypeDefinition

class YourMethodology(BaseMethodology):
    name = "your_methodology"  # Used in project.methodology field
    display_name = "Your Methodology Name"

    @property
    def node_types(self):
        return {
            # Define your node types here
            "item": NodeTypeDefinition(
                name="item",
                valid_statuses=["todo", "done"],
                initial_status="todo",
                terminal_statuses={"done"},
                allowed_transitions={
                    "todo": ["done"],
                    "done": [],
                },
            ),
        }

    @property
    def edge_types(self):
        return {
            # Define your edge types here
            "parent": EdgeTypeDefinition(
                name="parent",
                source_types=["item"],
                target_types=["item"],
                max_per_source=1,
                allows_cycles=False,
            ),
        }

    def get_story_type(self) -> str:
        """Return the top-level work item type"""
        return "item"

    def get_task_type(self) -> str:
        """Return the child work item type"""
        return "item"
```
