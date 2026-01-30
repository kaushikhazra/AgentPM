"""Tests for tag operations."""

import pytest

from agentpm.core import (
    create_company,
    create_project,
    create_tag,
    get_tag,
    get_tag_by_name,
    list_tags,
    delete_tag,
    tag_node,
    untag_node,
    get_node_tags,
    list_nodes_by_tag,
)
from agentpm.graph import create_node
from agentpm.exceptions import NotFoundError, ValidationError


@pytest.fixture
def project(temp_db):
    """Create a test project."""
    company = create_company("Test Company")
    return create_project(company.id, "Test Project")


def test_create_tag(temp_db):
    """Test creating a tag."""
    tag = create_tag("bug", color="#ff0000")

    assert tag.id is not None
    assert tag.name == "bug"
    assert tag.color == "#ff0000"


def test_create_duplicate_tag(temp_db):
    """Test creating a duplicate tag."""
    create_tag("bug")

    with pytest.raises(ValidationError):
        create_tag("bug")


def test_get_tag(temp_db):
    """Test getting a tag by ID."""
    created = create_tag("test")

    retrieved = get_tag(created.id)

    assert retrieved is not None
    assert retrieved.name == "test"


def test_get_tag_by_name(temp_db):
    """Test getting a tag by name."""
    create_tag("feature")

    tag = get_tag_by_name("feature")

    assert tag is not None
    assert tag.name == "feature"


def test_list_tags(temp_db):
    """Test listing all tags."""
    create_tag("bug")
    create_tag("feature")
    create_tag("enhancement")

    tags = list_tags()

    assert len(tags) == 3
    names = [t.name for t in tags]
    assert "bug" in names
    assert "feature" in names
    assert "enhancement" in names


def test_delete_tag(temp_db):
    """Test deleting a tag."""
    tag = create_tag("to-delete")

    result = delete_tag(tag.id)

    assert result is True
    assert get_tag(tag.id) is None


def test_tag_node(project):
    """Test tagging a node."""
    node = create_node(project.id, node_type="task", title="Test Task")

    tag_node(node.id, "bug")

    tags = get_node_tags(node.id)
    assert len(tags) == 1
    assert tags[0].name == "bug"


def test_tag_node_creates_tag(project):
    """Test that tagging with non-existent tag creates it."""
    node = create_node(project.id, node_type="task", title="Test Task")

    tag_node(node.id, "new-tag")

    tag = get_tag_by_name("new-tag")
    assert tag is not None


def test_tag_node_invalid_node(temp_db):
    """Test tagging an invalid node."""
    with pytest.raises(NotFoundError):
        tag_node("nonexistent", "bug")


def test_untag_node(project):
    """Test removing a tag from a node."""
    node = create_node(project.id, node_type="task", title="Test Task")
    tag_node(node.id, "bug")

    untag_node(node.id, "bug")

    tags = get_node_tags(node.id)
    assert len(tags) == 0


def test_get_node_tags(project):
    """Test getting all tags for a node."""
    node = create_node(project.id, node_type="task", title="Test Task")
    tag_node(node.id, "bug")
    tag_node(node.id, "urgent")
    tag_node(node.id, "backend")

    tags = get_node_tags(node.id)

    assert len(tags) == 3
    names = [t.name for t in tags]
    assert "bug" in names
    assert "urgent" in names
    assert "backend" in names


def test_list_nodes_by_tag(project):
    """Test listing nodes with a specific tag."""
    task1 = create_node(project.id, node_type="task", title="Bug Task 1")
    task2 = create_node(project.id, node_type="task", title="Bug Task 2")
    task3 = create_node(project.id, node_type="task", title="Feature Task")

    tag_node(task1.id, "bug")
    tag_node(task2.id, "bug")
    tag_node(task3.id, "feature")

    bug_nodes = list_nodes_by_tag("bug")

    assert len(bug_nodes) == 2
    node_ids = [n.id for n in bug_nodes]
    assert task1.id in node_ids
    assert task2.id in node_ids
    assert task3.id not in node_ids


def test_list_nodes_by_nonexistent_tag(temp_db):
    """Test listing nodes by a tag that doesn't exist."""
    nodes = list_nodes_by_tag("nonexistent")
    assert len(nodes) == 0
