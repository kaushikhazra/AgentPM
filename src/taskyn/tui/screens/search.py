"""Search screen for Taskyn TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static


# Entity type options
TYPE_OPTIONS = [
    ("All Types", ""),
    ("Tasks", "task"),
    ("Stories", "story"),
    ("Projects", "project"),
    ("Milestones", "milestone"),
    ("Companies", "company"),
]

# Status options
STATUS_OPTIONS = [
    ("All Statuses", ""),
    ("Backlog", "backlog"),
    ("Ready", "ready"),
    ("In Progress", "in_progress"),
    ("Done", "done"),
    ("Blocked", "blocked"),
]


class SearchScreen(Screen):
    """Full search screen with filters."""

    BINDINGS = [
        Binding("escape", "pop_screen", "Back", show=True),
        Binding("enter", "do_search", "Search", show=False),
        Binding("1", "go_dashboard", "Dashboard", show=False),
    ]

    def __init__(self, initial_query: str = "") -> None:
        super().__init__()
        self.initial_query = initial_query
        self._results = []

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="search-header"):
            yield Static("Search", id="search-title")

            with Horizontal(id="search-input-row"):
                yield Input(
                    value=self.initial_query,
                    placeholder="Search tasks, projects, milestones...",
                    id="search-input",
                )
                yield Button("Search", variant="primary", id="search-btn")

            with Horizontal(id="filter-row"):
                yield Label("Type:", classes="filter-label")
                yield Select(
                    options=TYPE_OPTIONS,
                    value="",
                    id="type-filter",
                    classes="filter-select",
                )
                yield Label("Status:", classes="filter-label")
                yield Select(
                    options=STATUS_OPTIONS,
                    value="",
                    id="status-filter",
                    classes="filter-select",
                )

        yield VerticalScroll(id="search-content")
        yield Footer()

    def on_mount(self) -> None:
        """Focus search input and run initial search if query provided."""
        self.query_one("#search-input", Input).focus()
        if self.initial_query:
            self._do_search()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "search-btn":
            self._do_search()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter in search input."""
        if event.input.id == "search-input":
            self._do_search()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Re-search when filters change."""
        query = self.query_one("#search-input", Input).value.strip()
        if query:
            self._do_search()

    def action_do_search(self) -> None:
        """Trigger search from keybinding."""
        self._do_search()

    def _do_search(self) -> None:
        """Perform the search."""
        query = self.query_one("#search-input", Input).value.strip()
        type_filter = self.query_one("#type-filter", Select).value
        status_filter = self.query_one("#status-filter", Select).value

        content = self.query_one("#search-content", VerticalScroll)
        content.remove_children()

        if not query:
            content.mount(Static("Enter a search term to begin", classes="no-results"))
            return

        try:
            from taskyn.db.connection import get_db
            from taskyn.core.reporting import search
            from taskyn.core.company import list_companies
            from taskyn.core.project import list_projects
            from taskyn.core.milestone import list_milestones
            from taskyn.graph.nodes import list_nodes

            with get_db() as db:
                self._results = []

                # Search based on type filter
                search_types = []
                if not type_filter:
                    search_types = ["task", "story", "project", "milestone", "company"]
                else:
                    search_types = [type_filter]

                query_lower = query.lower()

                # Search companies
                if "company" in search_types:
                    companies = list_companies(db)
                    for company in companies:
                        if query_lower in company.name.lower() or (
                            company.description and query_lower in company.description.lower()
                        ):
                            self._results.append({
                                "type": "company",
                                "id": company.id,
                                "title": company.name,
                                "description": company.description,
                                "status": None,
                            })

                # Search projects
                if "project" in search_types:
                    projects = list_projects(db)
                    for project in projects:
                        if status_filter and project.status != status_filter:
                            continue
                        if query_lower in project.name.lower() or (
                            project.description and query_lower in project.description.lower()
                        ):
                            self._results.append({
                                "type": "project",
                                "id": project.id,
                                "title": project.name,
                                "description": project.description,
                                "status": project.status,
                            })

                # Search milestones
                if "milestone" in search_types:
                    milestones = list_milestones(db)
                    for ms in milestones:
                        if status_filter and ms.status != status_filter:
                            continue
                        if query_lower in ms.name.lower() or (
                            ms.description and query_lower in ms.description.lower()
                        ):
                            self._results.append({
                                "type": "milestone",
                                "id": ms.id,
                                "title": ms.name,
                                "description": ms.description,
                                "status": ms.status,
                            })

                # Search nodes (tasks/stories)
                if "task" in search_types or "story" in search_types:
                    nodes = list_nodes(db)
                    for node in nodes:
                        if node.node_type not in search_types:
                            continue
                        if status_filter and node.status != status_filter:
                            continue
                        if query_lower in node.title.lower() or (
                            node.description and query_lower in node.description.lower()
                        ):
                            self._results.append({
                                "type": node.node_type,
                                "id": node.id,
                                "title": node.title,
                                "description": node.description,
                                "status": node.status,
                            })

                self._render_results()

        except Exception as e:
            content.mount(Static(f"[red]Search error: {e}[/red]", classes="no-results"))

    def _render_results(self) -> None:
        """Render search results."""
        content = self.query_one("#search-content", VerticalScroll)
        content.remove_children()

        if not self._results:
            content.mount(Static("No results found", classes="no-results"))
            return

        content.mount(Static(f"Found {len(self._results)} results", classes="result-count"))

        type_icons = {
            "company": "🏢",
            "project": "📁",
            "milestone": "🎯",
            "story": "📖",
            "task": "✓",
        }

        status_icons = {
            "backlog": "○",
            "ready": "●",
            "in_progress": "◐",
            "done": "✓",
            "blocked": "✗",
            "active": "●",
            "on_hold": "◐",
            "completed": "✓",
            "archived": "○",
            "open": "○",
        }

        for result in self._results[:50]:  # Limit to 50 results
            icon = type_icons.get(result["type"], "•")
            status = result.get("status")
            status_icon = status_icons.get(status, "") if status else ""

            with Vertical(classes="result-item"):
                content.mount(
                    Static(f"{icon} {result['title']}", classes="result-title")
                )
                content.mount(
                    Static(
                        f"{result['type'].upper()} {status_icon} {status or ''}",
                        classes="result-type",
                    )
                )
                if result.get("description"):
                    desc = result["description"][:100]
                    if len(result["description"]) > 100:
                        desc += "..."
                    content.mount(Static(f"[dim]{desc}[/dim]", classes="result-meta"))

    def action_go_dashboard(self) -> None:
        """Go back to dashboard."""
        self.app.pop_screen()
