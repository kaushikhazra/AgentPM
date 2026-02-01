"""Tests for edge operations."""

import pytest

from taskyn.core import create_company, create_project
from taskyn.graph import (
    create_node,
    create_edge,
    get_edge,
    list_edges,
    delete_edge,
    get_parents,
    get_children,
    get_ancestors,
    get_descendants,
)
from taskyn.exceptions import NotFoundError, ValidationError, CycleDetectedError, CardinalityError


@pytest.fixture
def project(temp_db):
    """Create a test project."""
    company = create_company("Test Company")
    return create_project(company.id, "Test Project")


def test_create_edge(project):
    """Test creating an edge."""
    story = create_node(project.id, node_type="story", title="Parent Story")
    task = create_node(project.id, node_type="task", title="Child Task")

    edge = create_edge(task.id, story.id, edge_type="parent")

    assert edge.id is not None
    assert edge.source_id == task.id
    assert edge.target_id == story.id
    assert edge.edge_type == "parent"


def test_create_edge_invalid_source(project):
    """Test creating an edge with invalid source."""
    story = create_node(project.id, node_type="story", title="Story")

    with pytest.raises(NotFoundError):
        create_edge("nonexistent", story.id, edge_type="parent")


def test_create_edge_invalid_target(project):
    """Test creating an edge with invalid target."""
    task = create_node(project.id, node_type="task", title="Task")

    with pytest.raises(NotFoundError):
        create_edge(task.id, "nonexistent", edge_type="parent")


def test_create_edge_invalid_type(project):
    """Test creating an edge with invalid source/target types."""
    epic = create_node(project.id, node_type="epic", title="Epic 1")
    story = create_node(project.id, node_type="story", title="Story 1")

    # parent edge: epic cannot be a source (only task/story can have parents)
    with pytest.raises(ValidationError):
        create_edge(epic.id, story.id, edge_type="parent")


def test_create_edge_cardinality_max_one(project):
    """Test cardinality constraint (task can only have one parent)."""
    story1 = create_node(project.id, node_type="story", title="Story 1")
    story2 = create_node(project.id, node_type="story", title="Story 2")
    task = create_node(project.id, node_type="task", title="Task")

    # First parent is OK
    create_edge(task.id, story1.id, edge_type="parent")

    # Second parent should fail
    with pytest.raises(CardinalityError):
        create_edge(task.id, story2.id, edge_type="parent")


def test_create_edge_cycle_detection(project):
    """Test that cycles are detected."""
    story = create_node(project.id, node_type="story", title="Story")
    task1 = create_node(project.id, node_type="task", title="Task 1")
    task2 = create_node(project.id, node_type="task", title="Task 2")

    # Create dependency chain: task1 depends on task2
    create_edge(task1.id, task2.id, edge_type="depends_on")

    # Creating task2 depends on task1 would create a cycle
    with pytest.raises(CycleDetectedError):
        create_edge(task2.id, task1.id, edge_type="depends_on")


def test_list_edges(project):
    """Test listing edges."""
    story = create_node(project.id, node_type="story", title="Story")
    task1 = create_node(project.id, node_type="task", title="Task 1")
    task2 = create_node(project.id, node_type="task", title="Task 2")

    create_edge(task1.id, story.id, edge_type="parent")
    create_edge(task2.id, story.id, edge_type="parent")

    # All edges
    edges = list_edges(project_id=project.id)
    assert len(edges) == 2

    # Edges from task1
    edges = list_edges(source_id=task1.id)
    assert len(edges) == 1

    # Edges to story
    edges = list_edges(target_id=story.id)
    assert len(edges) == 2


def test_delete_edge(project):
    """Test deleting an edge."""
    story = create_node(project.id, node_type="story", title="Story")
    task = create_node(project.id, node_type="task", title="Task")
    edge = create_edge(task.id, story.id, edge_type="parent")

    result = delete_edge(edge.id)

    assert result is True
    assert get_edge(edge.id) is None


def test_get_parents(project):
    """Test getting parents of a node."""
    story = create_node(project.id, node_type="story", title="Story")
    task = create_node(project.id, node_type="task", title="Task")
    create_edge(task.id, story.id, edge_type="parent")

    parents = get_parents(task.id)

    assert len(parents) == 1
    assert parents[0].id == story.id


def test_get_children(project):
    """Test getting children of a node."""
    story = create_node(project.id, node_type="story", title="Story")
    task1 = create_node(project.id, node_type="task", title="Task 1")
    task2 = create_node(project.id, node_type="task", title="Task 2")

    create_edge(task1.id, story.id, edge_type="parent")
    create_edge(task2.id, story.id, edge_type="parent")

    children = get_children(story.id)

    assert len(children) == 2
    child_ids = [c.id for c in children]
    assert task1.id in child_ids
    assert task2.id in child_ids


def test_get_ancestors_and_descendants(project):
    """Test traversing ancestors and descendants."""
    story = create_node(project.id, node_type="story", title="Story")
    task1 = create_node(project.id, node_type="task", title="Task 1")
    task2 = create_node(project.id, node_type="task", title="Task 2")

    # task1 -> story, task2 depends on task1
    create_edge(task1.id, story.id, edge_type="parent")
    create_edge(task2.id, task1.id, edge_type="depends_on")

    # task2's ancestors (via depends_on) should include task1
    ancestors = get_ancestors(task2.id, edge_type="depends_on")
    assert len(ancestors) == 1
    assert ancestors[0].id == task1.id

    # task1's descendants (via depends_on) should include task2
    descendants = get_descendants(task1.id, edge_type="depends_on")
    assert len(descendants) == 1
    assert descendants[0].id == task2.id


def test_story_with_tasks_integration(project):
    """Integration test: create story with tasks and verify relationships."""
    # Create story
    story = create_node(project.id, node_type="story", title="User Login Feature")

    # Create tasks under story
    task1 = create_node(project.id, node_type="task", title="Design login form")
    task2 = create_node(project.id, node_type="task", title="Implement authentication")
    task3 = create_node(project.id, node_type="task", title="Write tests")

    # Link tasks to story
    create_edge(task1.id, story.id, edge_type="parent")
    create_edge(task2.id, story.id, edge_type="parent")
    create_edge(task3.id, story.id, edge_type="parent")

    # task2 depends on task1
    create_edge(task2.id, task1.id, edge_type="depends_on")

    # Verify structure
    children = get_children(story.id)
    assert len(children) == 3

    task1_deps = get_descendants(task1.id, edge_type="depends_on")
    assert len(task1_deps) == 1
    assert task1_deps[0].id == task2.id
