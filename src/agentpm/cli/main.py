"""AgentPM CLI main entry point."""

import functools
from typing import Optional

import typer
from rich.console import Console

from agentpm.exceptions import AgentPMError, NotFoundError, ValidationError

app = typer.Typer(
    name="apm",
    help="AgentPM - AI-first Project Management",
    no_args_is_help=True,
)

console = Console()


class State:
    """Global CLI state."""

    db_path: str | None = None
    json_output: bool = False
    verbose: bool = False


state = State()


def handle_errors(func):
    """Decorator for consistent error handling."""

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
        except Exception as e:
            if state.verbose:
                console.print_exception()
            else:
                console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    return wrapper


@app.callback()
def main(
    db: Optional[str] = typer.Option(None, "--db", help="Database path"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """AgentPM - AI-first Project Management CLI"""
    state.db_path = db
    state.json_output = json_output
    state.verbose = verbose

    if db:
        from agentpm.db.connection import set_database_path

        set_database_path(db)


# Import and register subcommands
from agentpm.cli import company, project, milestone, node, story, task, timer, tag
from agentpm.cli import dashboard as dashboard_mod
from agentpm.cli import stats as stats_mod
from agentpm.cli import search as search_mod
from agentpm.cli import activity as activity_mod

app.add_typer(company.app, name="company", help="Company management")
app.add_typer(project.app, name="project", help="Project management")
app.add_typer(milestone.app, name="milestone", help="Milestone management")
app.add_typer(node.app, name="node", help="Node (story/task) management")
app.add_typer(story.app, name="story", help="Story shortcuts")
app.add_typer(task.app, name="task", help="Task shortcuts")
app.add_typer(timer.app, name="timer", help="Time tracking")
app.add_typer(tag.app, name="tag", help="Tag management")

app.command(name="dashboard")(dashboard_mod.dashboard)
app.command(name="stats")(stats_mod.stats)
app.command(name="search")(search_mod.search_cmd)
app.command(name="activity")(activity_mod.activity)


if __name__ == "__main__":
    app()
