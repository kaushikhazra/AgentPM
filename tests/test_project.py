"""Tests for project operations."""

import pytest

from taskyn.core import (
    create_company,
    create_project,
    get_project,
    list_projects,
    update_project,
    delete_project,
    ValidationError,
)
from taskyn.db.enums import Methodology
from taskyn.methodologies import get_methodology


@pytest.fixture
def company(temp_db):
    """Create a test company."""
    return create_company("Test Company")


def test_create_project(company):
    """Test creating a project."""
    project = create_project(
        company.id,
        "Test Project",
        description="A test project",
    )

    assert project.id is not None
    assert project.company_id == company.id
    assert project.name == "Test Project"
    assert project.description == "A test project"
    assert project.methodology == "classic_agile"
    assert project.status == "active"


def test_create_project_with_methodology(company):
    """Test creating a project with specific methodology."""
    project = create_project(
        company.id,
        "Agile Project",
        methodology=Methodology.CLASSIC_AGILE,
    )

    assert project.methodology == Methodology.CLASSIC_AGILE


def test_create_project_invalid_methodology(company):
    """Test creating a project with invalid methodology."""
    with pytest.raises(ValueError):
        create_project(company.id, "Bad Project", methodology=Methodology("invalid"))


def test_create_project_invalid_company(temp_db):
    """Test creating a project with invalid company."""
    with pytest.raises(ValidationError) as exc_info:
        create_project("nonexistent", "Bad Project")

    assert "Company not found" in str(exc_info.value)


def test_get_project(company):
    """Test getting a project by ID."""
    created = create_project(company.id, "Get Test")

    retrieved = get_project(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.name == "Get Test"


def test_get_project_not_found(temp_db):
    """Test getting a non-existent project."""
    result = get_project("nonexistent")
    assert result is None


def test_list_projects(company):
    """Test listing projects."""
    create_project(company.id, "Project A")
    create_project(company.id, "Project B")

    projects = list_projects()

    assert len(projects) == 2


def test_list_projects_by_company(temp_db):
    """Test listing projects filtered by company."""
    company1 = create_company("Company 1")
    company2 = create_company("Company 2")

    create_project(company1.id, "Project 1A")
    create_project(company1.id, "Project 1B")
    create_project(company2.id, "Project 2A")

    projects = list_projects(company_id=company1.id)

    assert len(projects) == 2
    names = [p.name for p in projects]
    assert "Project 1A" in names
    assert "Project 1B" in names


def test_list_projects_by_status(company):
    """Test listing projects filtered by status."""
    p1 = create_project(company.id, "Active Project")
    p2 = create_project(company.id, "Archived Project")
    update_project(p2.id, status="archived")

    active_projects = list_projects(status="active")
    archived_projects = list_projects(status="archived")

    assert len(active_projects) == 1
    assert len(archived_projects) == 1


def test_update_project(company):
    """Test updating a project."""
    project = create_project(company.id, "Original")

    updated = update_project(
        project.id,
        name="Updated",
        description="New description",
        status="on_hold",
    )

    assert updated is not None
    assert updated.name == "Updated"
    assert updated.description == "New description"
    assert updated.status == "on_hold"


def test_update_project_invalid_status(company):
    """Test updating a project with invalid status."""
    project = create_project(company.id, "Test")

    with pytest.raises(ValidationError) as exc_info:
        update_project(project.id, status="invalid")

    assert "Invalid status" in str(exc_info.value)


def test_update_project_methodology(company):
    """Test updating a project's methodology when it has no nodes."""
    project = create_project(company.id, "Agile Project")

    updated = update_project(project.id, methodology=Methodology.SPEC_DRIVEN)

    assert updated is not None
    assert updated.methodology == Methodology.SPEC_DRIVEN


def test_update_project_methodology_invalid(company):
    """Test updating a project with invalid methodology."""
    project = create_project(company.id, "Test Project")

    with pytest.raises(ValueError):
        update_project(project.id, methodology=Methodology("nonexistent"))


def test_update_project_methodology_with_nodes(company):
    """Test that methodology change is rejected when project has nodes."""
    from taskyn.graph.nodes import create_node

    project = create_project(company.id, "Has Nodes")
    create_node(project.id, "task", "Some task")

    with pytest.raises(ValidationError) as exc_info:
        update_project(project.id, methodology=Methodology.SPEC_DRIVEN)

    assert "Cannot change methodology" in str(exc_info.value)


def test_update_project_methodology_same_noop(company):
    """Test that setting methodology to current value is a no-op."""
    project = create_project(company.id, "Same Method")

    updated = update_project(project.id, methodology=Methodology.CLASSIC_AGILE)

    assert updated is not None
    assert updated.methodology == Methodology.CLASSIC_AGILE


def test_delete_project(company):
    """Test deleting a project."""
    project = create_project(company.id, "To Delete")

    result = delete_project(project.id)

    assert result is True
    assert get_project(project.id) is None


def test_project_has_correct_methodology(company):
    """Test that project has correct methodology attached."""
    project = create_project(company.id, "Agile Project", methodology=Methodology.CLASSIC_AGILE)

    methodology = get_methodology(project.methodology)

    assert methodology is not None
    assert methodology.name == "classic_agile"
    assert "story" in methodology.node_types
    assert "task" in methodology.node_types
