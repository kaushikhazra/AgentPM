"""Dashboard CLI command."""

import typer

from taskyn.cli.formatting import console, create_dashboard_panel
from taskyn.cli.main import handle_errors, state


@handle_errors
def dashboard():
    """Show the Taskyn dashboard."""
    from taskyn.core import get_dashboard

    dash = get_dashboard()

    if state.json_output:
        data = {
            "active_timer": dash.active_timer.model_dump(mode="json") if dash.active_timer else None,
            "active_timer_node": dash.active_timer_node.model_dump(mode="json") if dash.active_timer_node else None,
            "in_progress_nodes": [n.model_dump(mode="json") for n in dash.in_progress_nodes],
            "blocked_nodes": [n.model_dump(mode="json") for n in dash.blocked_nodes],
            "today_time_minutes": dash.today_time_minutes,
            "recent_activity": [a.model_dump(mode="json") for a in dash.recent_activity],
        }
        console.print_json(data=data)
    else:
        panel = create_dashboard_panel(dash)
        console.print(panel)
