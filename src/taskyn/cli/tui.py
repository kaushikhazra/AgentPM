"""TUI launch commands for Taskyn CLI."""

import typer

tui_app = typer.Typer(help="Terminal User Interface commands")


@tui_app.command("launch")
def launch(
    dark: bool = typer.Option(True, "--dark/--light", help="Start in dark or light mode"),
    project: str | None = typer.Option(None, "--project", "-p", help="Open specific project"),
) -> None:
    """Launch the Taskyn TUI."""
    from taskyn.tui.app import TaskynTUI

    app = TaskynTUI(dark_mode=dark)
    app.run()


@tui_app.callback(invoke_without_command=True)
def tui_default(ctx: typer.Context) -> None:
    """Launch TUI if no subcommand given."""
    if ctx.invoked_subcommand is None:
        launch(dark=True, project=None)
