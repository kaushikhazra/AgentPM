"""Tests for CLI commands."""

import pytest
from typer.testing import CliRunner

from agentpm.cli.main import app

runner = CliRunner()


# Company tests

def test_company_list(temp_db):
    """Test company list command."""
    result = runner.invoke(app, ["company", "list"])
    assert result.exit_code == 0


def test_company_create(temp_db):
    """Test company create command."""
    result = runner.invoke(app, ["company", "create", "Test Company"])
    assert result.exit_code == 0
    assert "Created company" in result.stdout
    assert "Test Company" in result.stdout


def test_company_create_with_description(temp_db):
    """Test company create with description."""
    result = runner.invoke(app, ["company", "create", "Test Co", "-d", "A test company"])
    assert result.exit_code == 0
    assert "Created company" in result.stdout


def test_company_list_json(temp_db):
    """Test company list with JSON output."""
    runner.invoke(app, ["company", "create", "Test Company"])
    result = runner.invoke(app, ["--json", "company", "list"])
    assert result.exit_code == 0
    assert "[" in result.stdout  # JSON array


# Project tests

def test_project_list(temp_db):
    """Test project list command."""
    result = runner.invoke(app, ["project", "list"])
    assert result.exit_code == 0


def test_project_create(temp_db):
    """Test project create command."""
    # First create a company
    result = runner.invoke(app, ["--json", "company", "create", "Test Company"])
    assert result.exit_code == 0
    import json
    company = json.loads(result.stdout)

    # Then create project
    result = runner.invoke(app, ["project", "create", company["id"], "Test Project"])
    assert result.exit_code == 0
    assert "Created project" in result.stdout


def test_project_create_with_methodology(temp_db):
    """Test project create with methodology."""
    result = runner.invoke(app, ["--json", "company", "create", "Test Company"])
    import json
    company = json.loads(result.stdout)

    result = runner.invoke(app, [
        "project", "create", company["id"], "Test Project",
        "-m", "classic_agile"
    ])
    assert result.exit_code == 0
    assert "classic_agile" in result.stdout


# Node tests

def test_node_list(temp_db):
    """Test node list command."""
    result = runner.invoke(app, ["node", "list"])
    assert result.exit_code == 0


def test_node_create(temp_db):
    """Test node create command."""
    # Setup
    result = runner.invoke(app, ["--json", "company", "create", "Test Company"])
    import json
    company = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "project", "create", company["id"], "Test Project"])
    project = json.loads(result.stdout)

    # Create node
    result = runner.invoke(app, ["node", "create", project["id"], "story", "Test Story"])
    assert result.exit_code == 0
    assert "Created story" in result.stdout


def test_node_workflow(temp_db):
    """Test node start and done commands."""
    # Setup
    import json
    result = runner.invoke(app, ["--json", "company", "create", "Test Company"])
    company = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "project", "create", company["id"], "Test Project"])
    project = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "node", "create", project["id"], "task", "Test Task"])
    task = json.loads(result.stdout)

    # Start
    result = runner.invoke(app, ["node", "start", task["id"]])
    assert result.exit_code == 0
    assert "Started" in result.stdout

    # Complete
    result = runner.invoke(app, ["node", "done", task["id"]])
    assert result.exit_code == 0
    assert "Completed" in result.stdout


# Story/Task shortcuts

def test_story_create(temp_db):
    """Test story create shortcut."""
    import json
    result = runner.invoke(app, ["--json", "company", "create", "Test Company"])
    company = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "project", "create", company["id"], "Test Project"])
    project = json.loads(result.stdout)

    result = runner.invoke(app, ["story", "create", project["id"], "Test Story"])
    assert result.exit_code == 0
    assert "Created story" in result.stdout


def test_task_create(temp_db):
    """Test task create shortcut."""
    import json
    result = runner.invoke(app, ["--json", "company", "create", "Test Company"])
    company = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "project", "create", company["id"], "Test Project"])
    project = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "story", "create", project["id"], "Test Story"])
    story = json.loads(result.stdout)

    result = runner.invoke(app, ["task", "create", story["id"], "Test Task"])
    assert result.exit_code == 0
    assert "Created task" in result.stdout


def test_task_workflow(temp_db):
    """Test task start/done shortcuts."""
    import json
    result = runner.invoke(app, ["--json", "company", "create", "Test Company"])
    company = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "project", "create", company["id"], "Test Project"])
    project = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "story", "create", project["id"], "Test Story"])
    story = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "task", "create", story["id"], "Test Task"])
    task = json.loads(result.stdout)

    # Start
    result = runner.invoke(app, ["task", "start", task["id"]])
    assert result.exit_code == 0
    assert "Started" in result.stdout

    # Done
    result = runner.invoke(app, ["task", "done", task["id"]])
    assert result.exit_code == 0
    assert "Completed" in result.stdout


# Timer tests

def test_timer_status_no_active(temp_db):
    """Test timer status with no active timer."""
    result = runner.invoke(app, ["timer", "status"])
    assert result.exit_code == 0
    assert "No active timer" in result.stdout


def test_timer_start_stop(temp_db):
    """Test timer start and stop."""
    import json
    result = runner.invoke(app, ["--json", "company", "create", "Test Company"])
    company = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "project", "create", company["id"], "Test Project"])
    project = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "node", "create", project["id"], "task", "Test Task"])
    task = json.loads(result.stdout)

    # Start timer
    result = runner.invoke(app, ["timer", "start", task["id"]])
    assert result.exit_code == 0
    assert "Timer started" in result.stdout

    # Check status
    result = runner.invoke(app, ["timer", "status"])
    assert result.exit_code == 0
    assert "Active Timer" in result.stdout

    # Stop timer
    result = runner.invoke(app, ["timer", "stop"])
    assert result.exit_code == 0
    assert "Timer stopped" in result.stdout


def test_timer_log(temp_db):
    """Test manual time logging."""
    import json
    result = runner.invoke(app, ["--json", "company", "create", "Test Company"])
    company = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "project", "create", company["id"], "Test Project"])
    project = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "node", "create", project["id"], "task", "Test Task"])
    task = json.loads(result.stdout)

    result = runner.invoke(app, ["timer", "log", task["id"], "30"])
    assert result.exit_code == 0
    assert "Logged" in result.stdout


# Dashboard test

def test_dashboard(temp_db):
    """Test dashboard command."""
    result = runner.invoke(app, ["dashboard"])
    assert result.exit_code == 0
    assert "Dashboard" in result.stdout


# Search test

def test_search(temp_db):
    """Test search command."""
    import json
    result = runner.invoke(app, ["--json", "company", "create", "Test Company"])
    company = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "project", "create", company["id"], "Test Project"])
    project = json.loads(result.stdout)

    result = runner.invoke(app, ["story", "create", project["id"], "Login Feature"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["search", "Login"])
    assert result.exit_code == 0
    assert "Login" in result.stdout


# Activity test

def test_activity(temp_db):
    """Test activity command."""
    import json
    result = runner.invoke(app, ["--json", "company", "create", "Test Company"])
    company = json.loads(result.stdout)

    result = runner.invoke(app, ["activity"])
    assert result.exit_code == 0
    # Should show the company creation activity


# Tag tests

def test_tag_create_and_list(temp_db):
    """Test tag create and list commands."""
    result = runner.invoke(app, ["tag", "create", "bug"])
    assert result.exit_code == 0
    assert "Created tag" in result.stdout

    result = runner.invoke(app, ["tag", "list"])
    assert result.exit_code == 0
    assert "bug" in result.stdout


def test_tag_add_remove(temp_db):
    """Test adding and removing tags from nodes."""
    import json
    result = runner.invoke(app, ["--json", "company", "create", "Test Company"])
    company = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "project", "create", company["id"], "Test Project"])
    project = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "node", "create", project["id"], "task", "Test Task"])
    task = json.loads(result.stdout)

    # Add tag
    result = runner.invoke(app, ["tag", "add", task["id"], "urgent"])
    assert result.exit_code == 0
    assert "Added tag" in result.stdout

    # Remove tag
    result = runner.invoke(app, ["tag", "remove", task["id"], "urgent"])
    assert result.exit_code == 0
    assert "Removed tag" in result.stdout


# Milestone tests

def test_milestone_create_and_list(temp_db):
    """Test milestone create and list commands."""
    import json
    result = runner.invoke(app, ["--json", "company", "create", "Test Company"])
    company = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "project", "create", company["id"], "Test Project"])
    project = json.loads(result.stdout)

    result = runner.invoke(app, ["milestone", "create", project["id"], "Sprint 1"])
    assert result.exit_code == 0
    assert "Created milestone" in result.stdout

    result = runner.invoke(app, ["milestone", "list", project["id"]])
    assert result.exit_code == 0
    assert "Sprint 1" in result.stdout


def test_milestone_with_target_date(temp_db):
    """Test milestone with target date."""
    import json
    result = runner.invoke(app, ["--json", "company", "create", "Test Company"])
    company = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "project", "create", company["id"], "Test Project"])
    project = json.loads(result.stdout)

    result = runner.invoke(app, [
        "milestone", "create", project["id"], "Sprint 1",
        "--target", "2025-06-01"
    ])
    assert result.exit_code == 0
    assert "Created milestone" in result.stdout


# JSON output tests

def test_json_output_company(temp_db):
    """Test JSON output for company commands."""
    import json

    result = runner.invoke(app, ["--json", "company", "create", "Test Company"])
    assert result.exit_code == 0

    data = json.loads(result.stdout)
    assert "id" in data
    assert data["name"] == "Test Company"


def test_json_output_node(temp_db):
    """Test JSON output for node commands."""
    import json

    result = runner.invoke(app, ["--json", "company", "create", "Test Company"])
    company = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "project", "create", company["id"], "Test Project"])
    project = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "node", "create", project["id"], "story", "Test Story"])
    assert result.exit_code == 0

    data = json.loads(result.stdout)
    assert "id" in data
    assert data["title"] == "Test Story"
    assert data["node_type"] == "story"


# Integration test

def test_full_workflow(temp_db):
    """Integration test: full workflow via CLI."""
    import json

    # Create company
    result = runner.invoke(app, ["--json", "company", "create", "ACME Corp"])
    assert result.exit_code == 0
    company = json.loads(result.stdout)

    # Create project
    result = runner.invoke(app, ["--json", "project", "create", company["id"], "Website Redesign"])
    assert result.exit_code == 0
    project = json.loads(result.stdout)

    # Create milestone
    result = runner.invoke(app, ["--json", "milestone", "create", project["id"], "Phase 1"])
    assert result.exit_code == 0
    milestone = json.loads(result.stdout)

    # Create story
    result = runner.invoke(app, ["--json", "story", "create", project["id"], "User Login"])
    assert result.exit_code == 0
    story = json.loads(result.stdout)

    # Create tasks
    result = runner.invoke(app, ["--json", "task", "create", story["id"], "Design login form"])
    assert result.exit_code == 0
    task1 = json.loads(result.stdout)

    result = runner.invoke(app, ["--json", "task", "create", story["id"], "Implement backend"])
    assert result.exit_code == 0
    task2 = json.loads(result.stdout)

    # Start task
    result = runner.invoke(app, ["task", "start", task1["id"]])
    assert result.exit_code == 0

    # Check dashboard
    result = runner.invoke(app, ["dashboard"])
    assert result.exit_code == 0
    assert "Design login form" in result.stdout or "Active" in result.stdout

    # Complete task
    result = runner.invoke(app, ["task", "done", task1["id"]])
    assert result.exit_code == 0

    # Show story with tasks
    result = runner.invoke(app, ["story", "show", story["id"]])
    assert result.exit_code == 0
    assert "User Login" in result.stdout
    assert "Design login form" in result.stdout

    # Check stats
    result = runner.invoke(app, ["stats", project["id"]])
    assert result.exit_code == 0
