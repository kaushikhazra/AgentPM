"""Project tree widget for Taskyn TUI."""

from textual.message import Message
from textual.widgets import Tree
from textual.widgets.tree import TreeNode


# Node type icons
NODE_ICONS = {
    "company": "🏢",
    "project": "📁",
    "milestone": "🎯",
    "story": "📖",
    "task": "✓",
    "spec": "📋",
    "design": "📐",
    "implementation": "⚙",
    "validation": "✅",
}


class ProjectTree(Tree):
    """Hierarchical view of projects and tasks."""

    class NodeSelected(Message):
        """Posted when a node is selected."""

        def __init__(self, node_id: str, node_type: str, node_name: str) -> None:
            super().__init__()
            self.node_id = node_id
            self.node_type = node_type
            self.node_name = node_name

    def __init__(self) -> None:
        super().__init__("Workspace", id="project-tree")
        self.show_root = False

    def on_mount(self) -> None:
        """Load project hierarchy when mounted."""
        self.root.expand()
        self.load_hierarchy()

    def load_hierarchy(self) -> None:
        """Load project hierarchy from database."""
        try:
            from taskyn.db.connection import get_db
            from taskyn.graph.nodes import list_nodes
            from taskyn.graph.edges import get_children
            from taskyn.core.company import list_companies
            from taskyn.core.project import list_projects
            from taskyn.core.milestone import list_milestones

            with get_db() as db:
                # Get companies, projects, milestones from core layer
                companies = list_companies(db)
                projects = list_projects(db)
                milestones = list_milestones(db)

                # Get all work item nodes
                nodes = list_nodes(db)
                nodes_by_id = {n.id: n for n in nodes}

                # Build lookup maps
                projects_by_company = {}
                for proj in projects:
                    if proj.company_id not in projects_by_company:
                        projects_by_company[proj.company_id] = []
                    projects_by_company[proj.company_id].append(proj)

                milestones_by_project = {}
                for ms in milestones:
                    if ms.project_id not in milestones_by_project:
                        milestones_by_project[ms.project_id] = []
                    milestones_by_project[ms.project_id].append(ms)

                nodes_by_project = {}
                nodes_by_milestone = {}
                orphan_nodes = []

                for node in nodes:
                    if node.milestone_id:
                        if node.milestone_id not in nodes_by_milestone:
                            nodes_by_milestone[node.milestone_id] = []
                        nodes_by_milestone[node.milestone_id].append(node)
                    elif node.project_id:
                        if node.project_id not in nodes_by_project:
                            nodes_by_project[node.project_id] = []
                        nodes_by_project[node.project_id].append(node)
                    else:
                        # Orphan node (no project or milestone)
                        orphan_nodes.append(node)

                has_content = False

                # Add companies with their projects
                for company in sorted(companies, key=lambda c: c.name):
                    has_content = True
                    company_projects = projects_by_company.get(company.id, [])

                    company_data = {
                        "id": company.id,
                        "type": "company",
                        "name": company.name,
                        "status": None,
                    }

                    if company_projects:
                        company_node = self.root.add(
                            f"{NODE_ICONS['company']} {company.name}",
                            data=company_data,
                            expand=False,
                        )
                        for proj in sorted(company_projects, key=lambda p: p.name):
                            self._add_project_to_tree(
                                db, company_node, proj,
                                milestones_by_project, nodes_by_project,
                                nodes_by_milestone, nodes_by_id
                            )
                    else:
                        self.root.add_leaf(
                            f"{NODE_ICONS['company']} {company.name}",
                            data=company_data,
                        )

                # Add orphan projects (no company)
                for proj in projects:
                    if not proj.company_id:
                        has_content = True
                        self._add_project_to_tree(
                            db, self.root, proj,
                            milestones_by_project, nodes_by_project,
                            nodes_by_milestone, nodes_by_id
                        )

                # Add orphan nodes (no project)
                if orphan_nodes:
                    has_content = True
                    type_order = {"story": 0, "task": 1}
                    orphan_nodes.sort(key=lambda n: (type_order.get(n.node_type, 99), n.title))
                    for node in orphan_nodes:
                        self._add_work_node_to_tree(db, self.root, node, nodes_by_id)

                if not has_content:
                    self.root.add_leaf(
                        "No projects yet",
                        data={"id": None, "type": None, "name": "empty"},
                    )

        except Exception as e:
            # Database might not exist or be empty
            self.root.add_leaf(
                "No projects yet",
                data={"id": None, "type": None, "name": "empty"},
            )

    def _add_project_to_tree(
        self, db, parent_tree_node: TreeNode, project,
        milestones_by_project: dict, nodes_by_project: dict,
        nodes_by_milestone: dict, nodes_by_id: dict
    ) -> None:
        """Add a project and its children to the tree."""
        project_data = {
            "id": project.id,
            "type": "project",
            "name": project.name,
            "status": project.status,
        }

        project_milestones = milestones_by_project.get(project.id, [])
        project_nodes = nodes_by_project.get(project.id, [])

        if project_milestones or project_nodes:
            project_node = parent_tree_node.add(
                f"{NODE_ICONS['project']} {project.name}",
                data=project_data,
                expand=False,
            )

            # Add milestones
            for ms in sorted(project_milestones, key=lambda m: m.name):
                self._add_milestone_to_tree(
                    db, project_node, ms, nodes_by_milestone, nodes_by_id
                )

            # Add direct project nodes (no milestone)
            type_order = {"story": 0, "task": 1}
            for node in sorted(project_nodes, key=lambda n: (type_order.get(n.node_type, 99), n.title)):
                self._add_work_node_to_tree(db, project_node, node, nodes_by_id)
        else:
            parent_tree_node.add_leaf(
                f"{NODE_ICONS['project']} {project.name}",
                data=project_data,
            )

    def _add_milestone_to_tree(
        self, db, parent_tree_node: TreeNode, milestone,
        nodes_by_milestone: dict, nodes_by_id: dict
    ) -> None:
        """Add a milestone and its tasks to the tree."""
        milestone_data = {
            "id": milestone.id,
            "type": "milestone",
            "name": milestone.name,
            "status": milestone.status,
        }

        milestone_nodes = nodes_by_milestone.get(milestone.id, [])

        if milestone_nodes:
            milestone_node = parent_tree_node.add(
                f"{NODE_ICONS['milestone']} {milestone.name}",
                data=milestone_data,
                expand=False,
            )

            type_order = {"story": 0, "task": 1}
            for node in sorted(milestone_nodes, key=lambda n: (type_order.get(n.node_type, 99), n.title)):
                self._add_work_node_to_tree(db, milestone_node, node, nodes_by_id)
        else:
            parent_tree_node.add_leaf(
                f"{NODE_ICONS['milestone']} {milestone.name}",
                data=milestone_data,
            )

    def _add_work_node_to_tree(
        self, db, parent_tree_node: TreeNode, node, nodes_by_id: dict
    ) -> None:
        """Add a work item node (task/story) and its children to the tree."""
        from taskyn.graph.edges import get_children

        icon = NODE_ICONS.get(node.node_type, "•")
        label = f"{icon} {node.title}"

        # Get children (subtasks)
        child_edges = get_children(db, node.id, "parent")
        child_nodes = []
        for edge in child_edges:
            child = nodes_by_id.get(edge.to_node_id)
            if child:
                child_nodes.append(child)

        node_data = {
            "id": node.id,
            "type": node.node_type,
            "name": node.title,
            "status": node.status,
        }

        if child_nodes:
            tree_node = parent_tree_node.add(label, data=node_data, expand=False)
            type_order = {"story": 0, "task": 1}
            for child in sorted(child_nodes, key=lambda n: (type_order.get(n.node_type, 99), n.title)):
                self._add_work_node_to_tree(db, tree_node, child, nodes_by_id)
        else:
            parent_tree_node.add_leaf(label, data=node_data)

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle node selection."""
        node_data = event.node.data
        if node_data and node_data.get("id"):
            self.post_message(
                self.NodeSelected(
                    node_id=node_data["id"],
                    node_type=node_data["type"],
                    node_name=node_data["name"],
                )
            )

    def refresh_tree(self) -> None:
        """Refresh the tree from database."""
        self.root.remove_children()
        self.load_hierarchy()
