"""Tests for spec-driven methodology v2.

Tests cover:
- 8 node types and their status workflows
- Parent pair validation (strict hierarchy)
- Verification cascade on failure
- Re-verification gating
- Time tracking enforcement
- Rollup through 5-level hierarchy
"""

import pytest

from taskyn.db.enums import Methodology
from taskyn.methodologies import get_methodology, list_methodologies
from taskyn.core import create_company, create_project
from taskyn.core.time_entry import start_timer, stop_timer, log_time
from taskyn.graph import create_node, create_edge, update_node
from taskyn.exceptions import ValidationError


# ============================================================
# Methodology Registration
# ============================================================


def test_spec_driven_methodology_registered():
    """Test that spec_driven methodology is registered."""
    methodology = get_methodology("spec_driven")
    assert methodology is not None
    assert methodology.name == "spec_driven"
    assert methodology.display_name == "Spec-Driven"


def test_spec_driven_in_list():
    """Test spec_driven appears in methodology list."""
    methodologies = list_methodologies()
    names = [m.name for m in methodologies]
    assert "spec_driven" in names
    assert "classic_agile" in names


# ============================================================
# Node Types
# ============================================================


def test_spec_driven_node_types():
    """Test spec_driven has all 8 node types."""
    methodology = get_methodology("spec_driven")
    node_types = methodology.node_types

    expected = [
        "spec", "requirement", "design", "implementation", "task",
        "e2e_verification", "functional_verification", "unit_verification",
    ]
    for nt in expected:
        assert nt in node_types, f"Missing node type: {nt}"
    assert len(node_types) == 8


def test_spec_driven_edge_types():
    """Test spec_driven has correct edge types (no gates/validates)."""
    methodology = get_methodology("spec_driven")
    edge_types = methodology.edge_types

    assert "parent" in edge_types
    assert "depends_on" in edge_types
    assert "blocks" in edge_types
    # Removed in v2
    assert "gates" not in edge_types
    assert "validates" not in edge_types


# ============================================================
# Status Workflows
# ============================================================


def test_spec_workflow(temp_db):
    """Test spec: draft → approved → in_progress → done."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    spec = create_node(project.id, "spec", "Feature X")
    assert spec.status == "draft"

    spec = update_node(spec.id, status="approved")
    assert spec.status == "approved"

    spec = update_node(spec.id, status="in_progress")
    assert spec.status == "in_progress"

    spec = update_node(spec.id, status="done")
    assert spec.status == "done"


def test_requirement_workflow(temp_db):
    """Test requirement: draft → approved → in_progress → done."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    req = create_node(project.id, "requirement", "User can login")
    assert req.status == "draft"

    req = update_node(req.id, status="approved")
    req = update_node(req.id, status="in_progress")
    req = update_node(req.id, status="done")
    assert req.status == "done"


def test_requirement_rework(temp_db):
    """Test requirement rework loop: in_progress → rework → in_progress."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    req = create_node(project.id, "requirement", "User can login")
    req = update_node(req.id, status="approved")
    req = update_node(req.id, status="in_progress")
    req = update_node(req.id, status="rework")
    assert req.status == "rework"

    req = update_node(req.id, status="in_progress")
    req = update_node(req.id, status="done")
    assert req.status == "done"


def test_design_workflow(temp_db):
    """Test design: draft → in_review → approved."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    design = create_node(project.id, "design", "Auth Design")
    assert design.status == "draft"

    design = update_node(design.id, status="in_review")
    design = update_node(design.id, status="approved")
    assert design.status == "approved"


def test_design_rejection_workflow(temp_db):
    """Test design rejection and revision."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    design = create_node(project.id, "design", "Auth Design")
    design = update_node(design.id, status="in_review")
    design = update_node(design.id, status="rejected")
    assert design.status == "rejected"

    design = update_node(design.id, status="draft")
    assert design.status == "draft"


def test_implementation_workflow(temp_db):
    """Test implementation: todo → in_progress → in_review → done, with rework."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    impl = create_node(project.id, "implementation", "Implement Auth")
    assert impl.status == "todo"

    impl = update_node(impl.id, status="in_progress")
    impl = update_node(impl.id, status="in_review")
    impl = update_node(impl.id, status="rework")
    impl = update_node(impl.id, status="in_progress")
    impl = update_node(impl.id, status="in_review")
    impl = update_node(impl.id, status="done")
    assert impl.status == "done"


def test_task_workflow(temp_db):
    """Test task: todo → in_progress → done."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    task = create_node(project.id, "task", "Write login handler")
    assert task.status == "todo"

    task = update_node(task.id, status="in_progress")
    task = update_node(task.id, status="done")
    assert task.status == "done"


def test_verification_workflow(temp_db):
    """Test verification: pending → in_progress → passed."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    for vtype in ["e2e_verification", "functional_verification", "unit_verification"]:
        v = create_node(project.id, vtype, f"Test {vtype}")
        assert v.status == "pending"

        v = update_node(v.id, status="in_progress")
        v = update_node(v.id, status="passed")
        assert v.status == "passed"


def test_verification_failure(temp_db):
    """Test verification failure: pending → in_progress → failed."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    v = create_node(project.id, "unit_verification", "Unit tests")
    v = update_node(v.id, status="in_progress")
    v = update_node(v.id, status="failed")
    assert v.status == "failed"


def test_invalid_transition_rejected(temp_db):
    """Test that invalid transitions are rejected."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    task = create_node(project.id, "task", "Write tests")
    assert task.status == "todo"

    # Cannot go directly from todo to done
    with pytest.raises(ValidationError):
        update_node(task.id, status="done")


# ============================================================
# Parent Pair Validation
# ============================================================


def test_valid_parent_pairs():
    """Test valid_parent_pairs property."""
    methodology = get_methodology("spec_driven")
    pairs = methodology.valid_parent_pairs

    assert pairs["requirement"] == ["spec"]
    assert pairs["design"] == ["requirement"]
    assert pairs["implementation"] == ["design"]
    assert pairs["task"] == ["implementation"]
    assert pairs["e2e_verification"] == ["requirement"]
    assert pairs["functional_verification"] == ["design"]
    assert pairs["unit_verification"] == ["implementation"]


def test_parent_edge_valid(temp_db):
    """Test creating valid parent edges through the hierarchy."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    spec = create_node(project.id, "spec", "Feature X")
    req = create_node(project.id, "requirement", "User can login")
    design = create_node(project.id, "design", "Auth Design")
    impl = create_node(project.id, "implementation", "Implement Auth")
    task = create_node(project.id, "task", "Write handler")

    # Build the hierarchy
    edge1 = create_edge(req.id, spec.id, "parent")
    assert edge1.edge_type == "parent"

    edge2 = create_edge(design.id, req.id, "parent")
    assert edge2.edge_type == "parent"

    edge3 = create_edge(impl.id, design.id, "parent")
    assert edge3.edge_type == "parent"

    edge4 = create_edge(task.id, impl.id, "parent")
    assert edge4.edge_type == "parent"


def test_verification_parent_edges(temp_db):
    """Test verification nodes parent under correct levels."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    req = create_node(project.id, "requirement", "User can login")
    design = create_node(project.id, "design", "Auth Design")
    impl = create_node(project.id, "implementation", "Implement Auth")

    e2e = create_node(project.id, "e2e_verification", "E2E tests")
    func = create_node(project.id, "functional_verification", "Functional tests")
    unit = create_node(project.id, "unit_verification", "Unit tests")

    # Valid parents
    create_edge(e2e.id, req.id, "parent")
    create_edge(func.id, design.id, "parent")
    create_edge(unit.id, impl.id, "parent")


def test_invalid_parent_pair_rejected(temp_db):
    """Test that misplaced parent edges are rejected."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    spec = create_node(project.id, "spec", "Feature X")
    task = create_node(project.id, "task", "Write handler")

    # task cannot parent under spec (must be under implementation)
    with pytest.raises(ValidationError):
        create_edge(task.id, spec.id, "parent")


def test_verification_wrong_parent_rejected(temp_db):
    """Test that verification nodes under wrong parent are rejected."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    spec = create_node(project.id, "spec", "Feature X")
    unit = create_node(project.id, "unit_verification", "Unit tests")

    # unit_verification cannot parent under spec (must be under implementation)
    with pytest.raises(ValidationError):
        create_edge(unit.id, spec.id, "parent")


def test_design_cannot_parent_under_spec(temp_db):
    """Test that design cannot parent directly under spec."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    spec = create_node(project.id, "spec", "Feature X")
    design = create_node(project.id, "design", "Auth Design")

    # design must parent under requirement, not spec
    with pytest.raises(ValidationError):
        create_edge(design.id, spec.id, "parent")


# ============================================================
# Verification Cascade
# ============================================================


def test_unit_verification_cascades_implementation(temp_db):
    """Test: unit_verification fails → implementation cascades to rework."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    impl = create_node(project.id, "implementation", "Implement Auth")
    unit = create_node(project.id, "unit_verification", "Unit tests")
    create_edge(unit.id, impl.id, "parent")

    # Get implementation to done
    impl = update_node(impl.id, status="in_progress")
    impl = update_node(impl.id, status="in_review")
    impl = update_node(impl.id, status="done")
    assert impl.status == "done"

    # Verification fails → implementation should cascade to rework
    unit = update_node(unit.id, status="in_progress")
    unit = update_node(unit.id, status="failed")

    from taskyn.graph.nodes import get_node
    impl = get_node(impl.id)
    assert impl.status == "rework"


def test_functional_verification_cascades_design(temp_db):
    """Test: functional_verification fails → design cascades to draft."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    design = create_node(project.id, "design", "Auth Design")
    func = create_node(project.id, "functional_verification", "Functional tests")
    create_edge(func.id, design.id, "parent")

    # Get design to approved
    design = update_node(design.id, status="in_review")
    design = update_node(design.id, status="approved")
    assert design.status == "approved"

    # Verification fails → design should cascade to draft (via rejected)
    func = update_node(func.id, status="in_progress")
    func = update_node(func.id, status="failed")

    from taskyn.graph.nodes import get_node
    design = get_node(design.id)
    assert design.status == "draft"


def test_e2e_verification_cascades_requirement(temp_db):
    """Test: e2e_verification fails → requirement cascades to rework."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    req = create_node(project.id, "requirement", "User can login")
    e2e = create_node(project.id, "e2e_verification", "E2E tests")
    create_edge(e2e.id, req.id, "parent")

    # Get requirement to in_progress
    req = update_node(req.id, status="approved")
    req = update_node(req.id, status="in_progress")
    assert req.status == "in_progress"

    # Verification fails → requirement should cascade to rework
    e2e = update_node(e2e.id, status="in_progress")
    e2e = update_node(e2e.id, status="failed")

    from taskyn.graph.nodes import get_node
    req = get_node(req.id)
    assert req.status == "rework"


# ============================================================
# Re-verification Gating
# ============================================================


def test_reverification_blocked_when_parent_not_terminal(temp_db):
    """Test: cannot retry verification when parent is in rework state."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    impl = create_node(project.id, "implementation", "Implement Auth")
    unit = create_node(project.id, "unit_verification", "Unit tests")
    create_edge(unit.id, impl.id, "parent")

    # Get implementation to done
    impl = update_node(impl.id, status="in_progress")
    impl = update_node(impl.id, status="in_review")
    impl = update_node(impl.id, status="done")

    # Fail verification → cascades implementation to rework
    unit = update_node(unit.id, status="in_progress")
    unit = update_node(unit.id, status="failed")

    # Cannot retry while implementation is in rework
    with pytest.raises(ValidationError, match="terminal state"):
        update_node(unit.id, status="pending")


def test_reverification_allowed_after_parent_fixed(temp_db):
    """Test: can retry verification after parent is back to terminal state."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    impl = create_node(project.id, "implementation", "Implement Auth")
    unit = create_node(project.id, "unit_verification", "Unit tests")
    create_edge(unit.id, impl.id, "parent")

    # Get implementation to done
    impl = update_node(impl.id, status="in_progress")
    impl = update_node(impl.id, status="in_review")
    impl = update_node(impl.id, status="done")

    # Fail → cascades to rework
    unit = update_node(unit.id, status="in_progress")
    unit = update_node(unit.id, status="failed")

    # Fix implementation: rework → in_progress → in_review → done
    impl = update_node(impl.id, status="in_progress")
    impl = update_node(impl.id, status="in_review")
    impl = update_node(impl.id, status="done")

    # Now retry should work
    unit = update_node(unit.id, status="pending")
    assert unit.status == "pending"

    unit = update_node(unit.id, status="in_progress")
    unit = update_node(unit.id, status="passed")
    assert unit.status == "passed"


# ============================================================
# Time Tracking Enforcement
# ============================================================


def test_time_tracking_allowed_on_task(temp_db):
    """Test that time tracking works on task nodes."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    task = create_node(project.id, "task", "Write handler")
    entry = start_timer(task.id)
    assert entry is not None

    stopped = stop_timer(entry_id=entry.id)
    assert stopped.ended_at is not None


def test_time_tracking_allowed_on_verification(temp_db):
    """Test that time tracking works on verification nodes."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    unit = create_node(project.id, "unit_verification", "Unit tests")
    entry = log_time(unit.id, duration_minutes=30)
    assert entry is not None
    assert entry.duration_minutes == 30


def test_time_tracking_rejected_on_spec(temp_db):
    """Test that time tracking is rejected on spec nodes."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    spec = create_node(project.id, "spec", "Feature X")
    with pytest.raises(ValidationError, match="not allowed"):
        start_timer(spec.id)


def test_time_tracking_rejected_on_requirement(temp_db):
    """Test that time tracking is rejected on requirement nodes."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    req = create_node(project.id, "requirement", "User can login")
    with pytest.raises(ValidationError, match="not allowed"):
        log_time(req.id, duration_minutes=60)


def test_time_tracking_rejected_on_design(temp_db):
    """Test that time tracking is rejected on design nodes."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    design = create_node(project.id, "design", "Auth Design")
    with pytest.raises(ValidationError, match="not allowed"):
        start_timer(design.id)


def test_time_tracking_rejected_on_implementation(temp_db):
    """Test that time tracking is rejected on implementation nodes."""
    company = create_company("Test Co")
    project = create_project(company.id, "P", Methodology.SPEC_DRIVEN)

    impl = create_node(project.id, "implementation", "Implement Auth")
    with pytest.raises(ValidationError, match="not allowed"):
        log_time(impl.id, duration_minutes=30)


# ============================================================
# Helper Methods
# ============================================================


def test_get_story_type():
    """Test get_story_type returns spec."""
    methodology = get_methodology("spec_driven")
    assert methodology.get_story_type() == "spec"


def test_get_task_type():
    """Test get_task_type returns task."""
    methodology = get_methodology("spec_driven")
    assert methodology.get_task_type() == "task"


def test_get_in_progress_status():
    """Test get_in_progress_status for all node types."""
    methodology = get_methodology("spec_driven")

    assert methodology.get_in_progress_status("spec") == "in_progress"
    assert methodology.get_in_progress_status("requirement") == "in_progress"
    assert methodology.get_in_progress_status("design") == "in_review"
    assert methodology.get_in_progress_status("implementation") == "in_progress"
    assert methodology.get_in_progress_status("task") == "in_progress"
    assert methodology.get_in_progress_status("e2e_verification") == "in_progress"
    assert methodology.get_in_progress_status("functional_verification") == "in_progress"
    assert methodology.get_in_progress_status("unit_verification") == "in_progress"


def test_get_done_status():
    """Test get_done_status for all node types."""
    methodology = get_methodology("spec_driven")

    assert methodology.get_done_status("spec") == "done"
    assert methodology.get_done_status("requirement") == "done"
    assert methodology.get_done_status("design") == "approved"
    assert methodology.get_done_status("implementation") == "done"
    assert methodology.get_done_status("task") == "done"
    assert methodology.get_done_status("e2e_verification") == "passed"
    assert methodology.get_done_status("functional_verification") == "passed"
    assert methodology.get_done_status("unit_verification") == "passed"


# ============================================================
# can_track_time flag
# ============================================================


def test_can_track_time_flags():
    """Test can_track_time is correctly set for all node types."""
    methodology = get_methodology("spec_driven")

    # Not trackable
    assert methodology.get_node_type("spec").can_track_time is False
    assert methodology.get_node_type("requirement").can_track_time is False
    assert methodology.get_node_type("design").can_track_time is False
    assert methodology.get_node_type("implementation").can_track_time is False

    # Trackable
    assert methodology.get_node_type("task").can_track_time is True
    assert methodology.get_node_type("e2e_verification").can_track_time is True
    assert methodology.get_node_type("functional_verification").can_track_time is True
    assert methodology.get_node_type("unit_verification").can_track_time is True
