# AgentPM CLI - Design

## Technology Stack
- **Typer**: CLI framework with type hints
- **Rich**: Terminal formatting (tables, panels, colors)
- **Click**: Underlying CLI (via Typer)

## Module Structure

```
src/agentpm/
└── cli/
    ├── __init__.py
    ├── main.py           # Typer app entry point, global options
    ├── company.py        # Company commands
    ├── project.py        # Project commands
    ├── milestone.py      # Milestone commands
    ├── node.py           # Generic node commands
    ├── story.py          # Story shortcuts
    ├── task.py           # Task shortcuts
    ├── timer.py          # Time tracking commands
    ├── dashboard.py      # Dashboard command
    ├── stats.py          # Stats command
    ├── search.py         # Search command
    ├── activity.py       # Activity command
    ├── tag.py            # Tag commands
    └── formatting.py     # Rich output helpers
```

## Entry Point (cli/main.py)

```python
import typer
from rich.console import Console

app = typer.Typer(
    name="apm",
    help="AgentPM - AI-first Project Management",
    no_args_is_help=True,
)

console = Console()

# Global state
class State:
    db_path: str | None = None
    json_output: bool = False
    verbose: bool = False

state = State()

@app.callback()
def main(
    db: str = typer.Option(None, "--db", help="Database path"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """AgentPM - AI-first Project Management CLI"""
    state.db_path = db
    state.json_output = json_output
    state.verbose = verbose

    if db:
        set_database_path(db)

# Register subcommands
from . import company, project, milestone, node, story, task, timer, tag
from . import dashboard, stats, search, activity

app.add_typer(company.app, name="company")
app.add_typer(project.app, name="project")
app.add_typer(milestone.app, name="milestone")
app.add_typer(node.app, name="node")
app.add_typer(story.app, name="story")
app.add_typer(task.app, name="task")
app.add_typer(timer.app, name="timer")
app.add_typer(tag.app, name="tag")

app.command()(dashboard.dashboard)
app.command()(stats.stats)
app.command()(search.search)
app.command()(activity.activity)

if __name__ == "__main__":
    app()
```

## Command Patterns

### List Commands

```python
# cli/project.py
app = typer.Typer(help="Project management")

@app.command("list")
def list_projects(
    company: str = typer.Option(None, "--company", "-c", help="Filter by company"),
    status: str = typer.Option(None, "--status", "-s", help="Filter by status"),
):
    """List all projects"""
    from agentpm.core import list_projects as _list_projects

    projects = _list_projects(company_id=company, status=status)

    if state.json_output:
        console.print_json(data=[p.model_dump() for p in projects])
    else:
        table = create_projects_table(projects)
        console.print(table)
```

### Create Commands

```python
@app.command("create")
def create_project(
    company_id: str = typer.Argument(..., help="Company ID"),
    name: str = typer.Argument(..., help="Project name"),
    description: str = typer.Option(None, "--description", "-d"),
    methodology: str = typer.Option("classic_agile", "--methodology", "-m"),
):
    """Create a new project"""
    from agentpm.core import create_project as _create_project

    try:
        project = _create_project(
            company_id=company_id,
            name=name,
            description=description,
            methodology=methodology,
        )

        if state.json_output:
            console.print_json(data=project.model_dump())
        else:
            console.print(f"[green]✓[/green] Created project: {project.name}")
            console.print(f"  ID: {project.id}")
            console.print(f"  Methodology: {project.methodology}")

    except ValidationError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
```

### Workflow Commands

```python
# cli/task.py
@app.command("start")
def start_task(
    task_id: str = typer.Argument(..., help="Task ID"),
):
    """Start working on a task (sets in_progress + starts timer)"""
    from agentpm.core import start_node

    task = start_node(task_id, actor="cli")

    if state.json_output:
        console.print_json(data=task.model_dump())
    else:
        console.print(f"[green]✓[/green] Started task: {task.title}")
        console.print("  Timer running...")

@app.command("done")
def complete_task(
    task_id: str = typer.Argument(..., help="Task ID"),
):
    """Complete a task (stops timer + sets done)"""
    from agentpm.core import complete_node, get_time_total

    task = complete_node(task_id, actor="cli")
    time_spent = get_time_total(task_id)

    if state.json_output:
        console.print_json(data=task.model_dump())
    else:
        console.print(f"[green]✓[/green] Completed task: {task.title}")
        console.print(f"  Time logged: {time_spent} minutes")
```

## Formatting Helpers (cli/formatting.py)

```python
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

def create_nodes_table(nodes: List[Node]) -> Table:
    table = Table(title="Nodes")
    table.add_column("ID", style="dim")
    table.add_column("Type")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Assignee")

    for node in nodes:
        status_style = get_status_style(node.status)
        table.add_row(
            node.id[:8],
            node.node_type,
            node.title,
            Text(node.status, style=status_style),
            node.assignee or "-",
        )

    return table

def get_status_style(status: str) -> str:
    styles = {
        "todo": "white",
        "in_progress": "yellow",
        "blocked": "red",
        "in_review": "cyan",
        "done": "green",
        "cancelled": "dim",
    }
    return styles.get(status, "white")

def format_duration(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m" if mins else f"{hours}h"

def create_dashboard_panel(dashboard: Dashboard) -> Panel:
    # Build rich panel with dashboard info
    ...
```

## Dashboard Output

```
╭─ AgentPM Dashboard ─────────────────────────────────────╮
│                                                         │
│  🔥 Active Task: Implement MCP server                   │
│     Project: AgentPM → Story: Core Infrastructure       │
│     Timer: 1h 23m running                               │
│                                                         │
│  📊 Today: 3h 45m tracked                               │
│                                                         │
│  🚧 Blockers: 1                                         │
│     - "Waiting for API access" on Data fetcher          │
│                                                         │
│  📋 In Progress: 3 items                                │
│                                                         │
╰─────────────────────────────────────────────────────────╯
```

## Error Handling

```python
def handle_errors(func):
    """Decorator for consistent error handling"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NotFoundError as e:
            console.print(f"[red]Not found:[/red] {e}")
            raise typer.Exit(1)
        except ValidationError as e:
            console.print(f"[red]Validation error:[/red] {e}")
            raise typer.Exit(1)
        except AgentPMError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
    return wrapper
```

## Installation Entry Point

In `pyproject.toml`:

```toml
[project.scripts]
apm = "agentpm.cli.main:app"
```
