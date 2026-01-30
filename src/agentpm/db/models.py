"""Pydantic models for AgentPM entities."""

from datetime import datetime, date
from typing import Any

from pydantic import BaseModel, Field


class Company(BaseModel):
    """Company model - top-level container for projects."""

    id: str
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class Project(BaseModel):
    """Project model - belongs to a company, uses a methodology."""

    id: str
    company_id: str
    name: str
    description: str | None = None
    methodology: str = "classic_agile"
    status: str = "active"
    config: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class Milestone(BaseModel):
    """Milestone model - optional grouping within a project."""

    id: str
    project_id: str
    name: str
    description: str | None = None
    target_date: date | None = None
    status: str = "open"
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class Node(BaseModel):
    """Node model - generic work item in the graph."""

    id: str
    project_id: str
    milestone_id: str | None = None
    node_type: str
    title: str
    description: str | None = None
    status: str
    assignee: str | None = None
    estimated_minutes: int | None = None
    story_points: int | None = None
    priority: str = "medium"
    blocked_reason: str | None = None
    properties: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class Edge(BaseModel):
    """Edge model - relationship between nodes."""

    id: str
    project_id: str
    source_id: str
    target_id: str
    edge_type: str
    properties: dict[str, Any] | None = None
    created_at: datetime


class TimeEntry(BaseModel):
    """TimeEntry model - time tracked on a node."""

    id: str
    node_id: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_minutes: int | None = None
    notes: str | None = None
    source: str = "manual"
    created_at: datetime


class Tag(BaseModel):
    """Tag model - label that can be attached to nodes."""

    id: str
    name: str
    color: str | None = None


class ActivityLog(BaseModel):
    """ActivityLog model - audit trail of changes."""

    id: str
    entity_type: str
    entity_id: str
    node_type: str | None = None
    action: str
    old_value: str | None = None
    new_value: str | None = None
    actor: str | None = None
    notes: str | None = None
    created_at: datetime
