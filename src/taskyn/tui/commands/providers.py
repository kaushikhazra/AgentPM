"""Command palette providers for Taskyn TUI."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from textual.command import Hit, Hits, Provider

if TYPE_CHECKING:
    from taskyn.tui.app import TaskynTUI


class TaskSearchProvider(Provider):
    """Search tasks from the command palette."""

    @property
    def _app(self) -> "TaskynTUI":
        return self.app

    async def search(self, query: str) -> Hits:
        """Search tasks matching query."""
        if not query or len(query) < 2:
            return

        matcher = self.matcher(query)

        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.nodes import list_nodes
            from taskyn.graph.edges import get_parents

            with get_db() as db:
                nodes = list_nodes(db)
                tasks = [n for n in nodes if n.node_type in ("task", "story")]

                for task in tasks:
                    # Match against title
                    score = matcher.match(task.title)
                    if score > 0:
                        # Get parent project for context
                        context = ""
                        try:
                            parent_edges = get_parents(db, task.id, "parent")
                            if parent_edges:
                                parent = next(
                                    (n for n in nodes if n.id == parent_edges[0].from_node_id),
                                    None,
                                )
                                if parent:
                                    context = f" • {parent.title}"
                        except Exception:
                            pass

                        # Status icon
                        status_icons = {
                            "backlog": "○",
                            "todo": "●",
                            "ready": "●",
                            "in_progress": "◐",
                            "done": "✓",
                            "blocked": "✗",
                        }
                        icon = status_icons.get(task.status, "•")

                        yield Hit(
                            score,
                            matcher.highlight(f"{icon} {task.title}"),
                            partial(self._open_task, task.id),
                            help=f"{task.node_type.title()}{context}",
                        )

        except Exception:
            pass

    def _open_task(self, task_id: str) -> None:
        """Open task detail screen."""
        from taskyn.tui.screens.task_detail import TaskDetailScreen

        self._app.push_screen(TaskDetailScreen(task_id))


class ProjectSearchProvider(Provider):
    """Search projects from the command palette."""

    @property
    def _app(self) -> "TaskynTUI":
        return self.app

    async def search(self, query: str) -> Hits:
        """Search projects matching query."""
        if not query or len(query) < 2:
            return

        matcher = self.matcher(query)

        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.nodes import list_nodes

            with get_db() as db:
                nodes = list_nodes(db)
                projects = [n for n in nodes if n.node_type in ("project", "company", "milestone")]

                for proj in projects:
                    score = matcher.match(proj.title)
                    if score > 0:
                        # Type icons
                        type_icons = {
                            "company": "🏢",
                            "project": "📁",
                            "milestone": "🎯",
                        }
                        icon = type_icons.get(proj.node_type, "📁")

                        yield Hit(
                            score,
                            matcher.highlight(f"{icon} {proj.title}"),
                            partial(self._select_project, proj.id, proj.title),
                            help=proj.node_type.title(),
                        )

        except Exception:
            pass

    def _select_project(self, project_id: str, project_name: str) -> None:
        """Select project in tree."""
        self._app.notify(f"Selected: {project_name}", title="Project")


class CommandsProvider(Provider):
    """Provide system commands in command palette."""

    @property
    def _app(self) -> "TaskynTUI":
        return self.app

    async def search(self, query: str) -> Hits:
        """Search system commands."""
        matcher = self.matcher(query)

        commands = [
            # Create commands
            ("New Task", "Create a new task", "ctrl+n", self._app.action_new_task),
            ("New Company", "Create a new company", "c", self._app.action_new_company),
            ("New Project", "Create a new project", "p", self._app.action_new_project),
            ("New Milestone", "Create a new milestone", "m", self._app.action_new_milestone),
            ("New Story", "Create a new story", "s", self._app.action_new_story),
            # Navigation commands
            ("Dashboard", "Go to dashboard view", "1", self._app.action_view_dashboard),
            ("Kanban", "Go to Kanban board view", "2", self._app.action_view_projects),
            ("Settings", "Go to settings", "3", self._app.action_view_settings),
            ("Search", "Go to full search screen", "4", self._app.action_view_search),
            ("Activity", "Go to activity history", "5", self._app.action_view_activity),
            ("Statistics", "Go to project statistics", "6", self._app.action_view_statistics),
            # Utility commands
            ("Toggle Dark Mode", "Switch between dark and light theme", "d", self._app.action_toggle_dark),
            ("Help", "Show keyboard shortcuts", "?", self._app.action_help),
            ("Quit", "Exit Taskyn", "q", self._app.action_quit),
        ]

        for name, description, key, callback in commands:
            # Show all commands when query is empty, otherwise filter by match
            if not query:
                yield Hit(
                    1.0,
                    name,
                    callback,
                    help=f"{description} ({key})",
                )
            else:
                score = matcher.match(name)
                if score > 0:
                    yield Hit(
                        score,
                        matcher.highlight(name),
                        callback,
                        help=f"{description} ({key})",
                    )
                else:
                    # Also match against description
                    desc_score = matcher.match(description)
                    if desc_score > 0:
                        yield Hit(
                            desc_score,
                            matcher.highlight(name),
                            callback,
                            help=f"{description} ({key})",
                        )
