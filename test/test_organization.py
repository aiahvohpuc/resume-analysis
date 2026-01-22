"""Tests for organization data management (Phase 2)."""

import pytest
from src.data.organization_manager import OrganizationManager, OrganizationNotFoundError


class TestOrganizationManager:
    """Test cases for OrganizationManager."""

    @pytest.fixture
    def manager(self) -> OrganizationManager:
        """Create organization manager instance."""
        return OrganizationManager()

    def test_list_organizations(self, manager: OrganizationManager):
        """Test listing all available organizations."""
        orgs = manager.list_organizations()
        assert isinstance(orgs, list)
        assert "NHIS" in orgs
        assert "HIRA" in orgs
        assert "NPS" in orgs

    def test_get_organization_nhis(self, manager: OrganizationManager):
        """Test getting NHIS organization data."""
        org = manager.get_organization("NHIS")
        assert org["code"] == "NHIS"
        assert org["name"] == "국민건강보험공단"
        assert "keywords" in org
        assert "core_values" in org
        assert "positions" in org
        assert isinstance(org["keywords"], list)

    def test_get_organization_hira(self, manager: OrganizationManager):
        """Test getting HIRA organization data."""
        org = manager.get_organization("HIRA")
        assert org["code"] == "HIRA"
        assert org["name"] == "건강보험심사평가원"

    def test_get_organization_nps(self, manager: OrganizationManager):
        """Test getting NPS organization data."""
        org = manager.get_organization("NPS")
        assert org["code"] == "NPS"
        assert org["name"] == "국민연금공단"

    def test_get_organization_not_found(self, manager: OrganizationManager):
        """Test that unknown organization raises error."""
        with pytest.raises(OrganizationNotFoundError):
            manager.get_organization("UNKNOWN_ORG")

    def test_get_organization_case_insensitive(self, manager: OrganizationManager):
        """Test that organization lookup is case insensitive."""
        org_upper = manager.get_organization("NHIS")
        org_lower = manager.get_organization("nhis")
        assert org_upper["code"] == org_lower["code"]

    def test_organization_keywords_not_empty(self, manager: OrganizationManager):
        """Test that organization has keywords."""
        org = manager.get_organization("NHIS")
        assert len(org["keywords"]) > 0

    def test_organization_core_values_not_empty(self, manager: OrganizationManager):
        """Test that organization has core values."""
        org = manager.get_organization("NHIS")
        assert len(org["core_values"]) > 0

    def test_manager_caches_data(self, manager: OrganizationManager):
        """Test that organization data is cached."""
        # First call loads data
        org1 = manager.get_organization("NHIS")
        # Second call should return cached data
        org2 = manager.get_organization("NHIS")
        assert org1 is org2  # Same object reference (cached)
