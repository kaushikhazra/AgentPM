"""Tests for spec-driven methodology."""

import pytest

from agentpm.methodologies import get_methodology, list_methodologies
from agentpm.core import create_company, create_project
from agentpm.graph import create_node, create_edge, update_node


def test_spec_driven_methodology_registered():
    """Test that spec_driven methodology is registered."""
    methodology = get_methodology("spec_driven")
    assert methodology is not None
    assert methodology.name == "spec_driven"
    assert methodology.display_name == "Spec-Driven (Kiro-style)"


def test_spec_driven_in_list():
    """Test spec_driven appears in methodology list."""
    methodologies = list_methodologies()
    names = [m.name for m in methodologies]
    assert "spec_driven" in names
    assert "classic_agile" in names


def test_spec_driven_node_types():
    """Test spec_driven has correct node types."""
    methodology = get_methodology("spec_driven")
    node_types = methodology.node_types

    assert "spec" in node_types
    assert "design" in node_types
    assert "implementation" in node_types
    assert "validation" in node_types


def test_spec_driven_edge_types():
    """Test spec_driven has correct edge types."""
    methodology = get_methodology("spec_driven")
    edge_types = methodology.edge_types

    assert "gates" in edge_types
    assert "validates" in edge_types
    assert "depends_on" in edge_types


def test_create_spec_project(temp_db):
    """Test creating a project with spec_driven methodology."""
    company = create_company("Test Co")
    project = create_project(company.id, "Spec Project", "spec_driven")

    assert project.methodology == "spec_driven"


def test_create_spec_node(temp_db):
    """Test creating a spec node."""
    company = create_company("Test Co")
    project = create_project(company.id, "Spec Project", "spec_driven")

    spec = create_node(project.id, "spec", "User Authentication")
    assert spec.node_type == "spec"
    assert spec.status == "draft"


def test_spec_approval_workflow(temp_db):
    """Test the spec approval workflow."""
    company = create_company("Test Co")
    project = create_project(company.id, "Spec Project", "spec_driven")

    spec = create_node(project.id, "spec", "User Authentication")
    assert spec.status == "draft"

    # Approve spec
    spec = update_node(spec.id, status="approved")
    assert spec.status == "approved"

    # Start work
    spec = update_node(spec.id, status="in_progress")
    assert spec.status == "in_progress"

    # Complete
    spec = update_node(spec.id, status="done")
    assert spec.status == "done"


def test_design_review_workflow(temp_db):
    """Test the design review workflow."""
    company = create_company("Test Co")
    project = create_project(company.id, "Spec Project", "spec_driven")

    design = create_node(project.id, "design", "Auth Design Doc")
    assert design.status == "draft"

    # Submit for review
    design = update_node(design.id, status="in_review")
    assert design.status == "in_review"

    # Approve
    design = update_node(design.id, status="approved")
    assert design.status == "approved"


def test_design_rejection_workflow(temp_db):
    """Test design rejection and revision."""
    company = create_company("Test Co")
    project = create_project(company.id, "Spec Project", "spec_driven")

    design = create_node(project.id, "design", "Auth Design Doc")

    # Submit for review
    design = update_node(design.id, status="in_review")

    # Reject
    design = update_node(design.id, status="rejected")
    assert design.status == "rejected"

    # Revise (back to draft)
    design = update_node(design.id, status="draft")
    assert design.status == "draft"


def test_implementation_workflow(temp_db):
    """Test implementation workflow with rework."""
    company = create_company("Test Co")
    project = create_project(company.id, "Spec Project", "spec_driven")

    impl = create_node(project.id, "implementation", "Implement Auth")
    assert impl.status == "todo"

    # Start
    impl = update_node(impl.id, status="in_progress")
    assert impl.status == "in_progress"

    # Submit for review
    impl = update_node(impl.id, status="in_review")
    assert impl.status == "in_review"

    # Needs rework
    impl = update_node(impl.id, status="rework")
    assert impl.status == "rework"

    # Fix and resubmit
    impl = update_node(impl.id, status="in_progress")
    impl = update_node(impl.id, status="in_review")

    # Done
    impl = update_node(impl.id, status="done")
    assert impl.status == "done"


def test_validation_workflow(temp_db):
    """Test validation pass/fail workflow."""
    company = create_company("Test Co")
    project = create_project(company.id, "Spec Project", "spec_driven")

    validation = create_node(project.id, "validation", "Auth Validation")
    assert validation.status == "pending"

    # Start validation
    validation = update_node(validation.id, status="in_progress")
    assert validation.status == "in_progress"

    # Fail
    validation = update_node(validation.id, status="failed")
    assert validation.status == "failed"

    # Retry
    validation = update_node(validation.id, status="pending")
    validation = update_node(validation.id, status="in_progress")

    # Pass
    validation = update_node(validation.id, status="passed")
    assert validation.status == "passed"


def test_gates_edge(temp_db):
    """Test creating gates edge between phases."""
    company = create_company("Test Co")
    project = create_project(company.id, "Spec Project", "spec_driven")

    spec = create_node(project.id, "spec", "User Auth Spec")
    design = create_node(project.id, "design", "Auth Design")

    # Design gates spec
    edge = create_edge(design.id, spec.id, "gates")
    assert edge.edge_type == "gates"


def test_validates_edge(temp_db):
    """Test creating validates edge."""
    company = create_company("Test Co")
    project = create_project(company.id, "Spec Project", "spec_driven")

    impl = create_node(project.id, "implementation", "Implement Auth")
    validation = create_node(project.id, "validation", "Auth Tests")

    # Validation validates implementation
    edge = create_edge(validation.id, impl.id, "validates")
    assert edge.edge_type == "validates"


def test_get_story_type():
    """Test get_story_type returns spec."""
    methodology = get_methodology("spec_driven")
    assert methodology.get_story_type() == "spec"


def test_get_task_type():
    """Test get_task_type returns implementation."""
    methodology = get_methodology("spec_driven")
    assert methodology.get_task_type() == "implementation"


def test_get_in_progress_status():
    """Test get_in_progress_status for different node types."""
    methodology = get_methodology("spec_driven")

    assert methodology.get_in_progress_status("spec") == "in_progress"
    assert methodology.get_in_progress_status("design") == "in_review"
    assert methodology.get_in_progress_status("implementation") == "in_progress"
    assert methodology.get_in_progress_status("validation") == "in_progress"


def test_get_done_status():
    """Test get_done_status for different node types."""
    methodology = get_methodology("spec_driven")

    assert methodology.get_done_status("spec") == "done"
    assert methodology.get_done_status("design") == "approved"
    assert methodology.get_done_status("implementation") == "done"
    assert methodology.get_done_status("validation") == "passed"
