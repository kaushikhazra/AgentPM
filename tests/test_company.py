"""Tests for company operations."""

import pytest

from agentpm.core import (
    create_company,
    get_company,
    list_companies,
    update_company,
    delete_company,
)


def test_create_company(temp_db):
    """Test creating a company."""
    company = create_company("Test Company", "A test company")

    assert company.id is not None
    assert company.name == "Test Company"
    assert company.description == "A test company"
    assert company.created_at is not None
    assert company.updated_at is not None


def test_create_company_minimal(temp_db):
    """Test creating a company with minimal fields."""
    company = create_company("Minimal Company")

    assert company.id is not None
    assert company.name == "Minimal Company"
    assert company.description is None


def test_get_company(temp_db):
    """Test getting a company by ID."""
    created = create_company("Get Test", "Description")

    retrieved = get_company(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.name == "Get Test"
    assert retrieved.description == "Description"


def test_get_company_not_found(temp_db):
    """Test getting a non-existent company."""
    result = get_company("nonexistent")
    assert result is None


def test_list_companies(temp_db):
    """Test listing companies."""
    create_company("Company A")
    create_company("Company B")
    create_company("Company C")

    companies = list_companies()

    assert len(companies) == 3
    names = [c.name for c in companies]
    assert "Company A" in names
    assert "Company B" in names
    assert "Company C" in names


def test_list_companies_empty(temp_db):
    """Test listing companies when none exist."""
    companies = list_companies()
    assert len(companies) == 0


def test_update_company(temp_db):
    """Test updating a company."""
    company = create_company("Original Name", "Original description")

    updated = update_company(
        company.id,
        name="Updated Name",
        description="Updated description",
    )

    assert updated is not None
    assert updated.name == "Updated Name"
    assert updated.description == "Updated description"
    assert updated.updated_at >= company.updated_at


def test_update_company_partial(temp_db):
    """Test partially updating a company."""
    company = create_company("Original", "Description")

    updated = update_company(company.id, name="New Name")

    assert updated is not None
    assert updated.name == "New Name"
    assert updated.description == "Description"


def test_update_company_not_found(temp_db):
    """Test updating a non-existent company."""
    result = update_company("nonexistent", name="New Name")
    assert result is None


def test_delete_company(temp_db):
    """Test deleting a company."""
    company = create_company("To Delete")

    result = delete_company(company.id)

    assert result is True
    assert get_company(company.id) is None


def test_delete_company_not_found(temp_db):
    """Test deleting a non-existent company."""
    result = delete_company("nonexistent")
    assert result is False
