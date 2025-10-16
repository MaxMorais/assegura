"""Unit tests for persona domain logic.

Tests the core persona domain entities, services, and business rules
without external dependencies like databases or APIs.
"""

import uuid

import pytest

from src.domain.personas.erpnext_roles import ERPNextRole
from src.domain.personas.exceptions import (
    PersonaAlreadyExistsError,
    PersonaMultipleValidationError,
    PersonaNotFoundError,
    PersonaValidationError,
)
from src.domain.personas.persona import Persona
from src.domain.personas.persona_service import PersonaService as PersonaDomainService


class TestPersonaDomainEntity:
    """Test the Persona domain entity."""

    def test_persona_creation_valid_data(self):
        """Test creating a persona with valid data."""
        persona = Persona(
            name="Sales Manager",
            description="Manages sales operations",
            erpnext_roles=["Sales Manager", "Customer"],
            permissions="read_sales_order,write_sales_order",
            is_active=True,
        )

        assert persona.name == "Sales Manager"
        assert persona.description == "Manages sales operations"
        assert persona.erpnext_roles == ["Sales Manager", "Customer"]
        assert persona.permissions == "read_sales_order,write_sales_order"
        assert persona.is_active is True
        assert persona.id is not None
        assert isinstance(persona.id, uuid.UUID)
        assert persona.created_at is not None
        assert persona.updated_at is not None
        assert persona.version == 1

    def test_persona_creation_minimal_data(self):
        """Test creating a persona with minimal required data."""
        persona = Persona(name="Basic User", description="A basic user persona", erpnext_roles=["Sales User"])

        assert persona.name == "Basic User"
        assert persona.description == "A basic user persona"
        assert persona.erpnext_roles == ["Sales User"]
        assert persona.permissions is None
        assert persona.is_active is True  # Default value

    def test_persona_validation_empty_name(self):
        """Test persona validation with empty name."""
        with pytest.raises(PersonaValidationError) as exc_info:
            Persona(name="", description="Test description", erpnext_roles=["Sales User"])

        assert "Persona name is required" in str(exc_info.value)

    def test_persona_validation_empty_roles(self):
        """Test persona validation with empty roles."""
        with pytest.raises(PersonaValidationError) as exc_info:
            Persona(name="Test User", description="Test description", erpnext_roles=[])

        assert "At least one ERPNext role is required" in str(exc_info.value)

    def test_persona_validation_invalid_role(self):
        """Test persona validation with invalid ERPNext role."""
        with pytest.raises(PersonaValidationError) as exc_info:
            Persona(name="Test User", description="Test description", erpnext_roles=["Invalid Role"])

        assert "Invalid ERPNext role" in str(exc_info.value)

    def test_persona_name_length_validation(self):
        """Test persona name length validation."""
        # Name too short
        with pytest.raises(PersonaValidationError):
            Persona(name="A", description="Test description", erpnext_roles=["Sales User"])

        # Name too long
        long_name = "A" * 256  # Max length is 255
        with pytest.raises(PersonaValidationError):
            Persona(name=long_name, description="Test description", erpnext_roles=["Sales User"])

    def test_persona_erpnext_roles_property(self):
        """Test ERPNext roles property conversions."""
        persona = Persona(
            name="Test User",
            description="Test user with multiple roles",
            erpnext_roles=["Sales Manager", "Customer", "Item Manager"],
        )

        # Test list access
        assert persona.erpnext_roles == ["Sales Manager", "Customer", "Item Manager"]

        # Test string representation
        roles_str = persona.erpnext_roles_str
        assert "Sales Manager" in roles_str
        assert "Customer" in roles_str
        assert "Item Manager" in roles_str

    def test_persona_permissions_property(self):
        """Test permissions property conversions."""
        persona = Persona(
            name="Test User",
            description="Test user with permissions",
            erpnext_roles=["Sales User"],
            permissions="read_customer,write_customer,read_item",
        )

        # Test string access
        assert persona.permissions == "read_customer,write_customer,read_item"

        # Test list access
        perms_list = persona.permissions_list
        assert perms_list == ["read_customer", "write_customer", "read_item"]

    def test_persona_get_effective_permissions(self):
        """Test calculation of effective permissions."""
        persona = Persona(
            name="Sales Manager",
            erpnext_roles=["Sales Manager", "Customer"],
            permissions="read_supplier,write_purchase_order",
        )

        effective_perms = persona.get_effective_permissions()

        # Should include role-based permissions plus explicit permissions
        assert isinstance(effective_perms, list)
        assert len(effective_perms) > 0

        # Should include explicit permissions
        assert "read_supplier" in effective_perms
        assert "write_purchase_order" in effective_perms

    def test_persona_update_name(self):
        """Test updating persona name."""
        persona = Persona(name="Original Name", erpnext_roles=["Sales User"])
        original_updated_at = persona.updated_at

        # Small delay to ensure timestamp difference
        import time

        time.sleep(0.01)

        persona.update_name("New Name")

        assert persona.name == "New Name"
        assert persona.updated_at > original_updated_at
        assert persona.version == 2

    def test_persona_update_description(self):
        """Test updating persona description."""
        persona = Persona(
            name="Test User", erpnext_roles=["Sales User"], description="Original description"
        )

        persona.update_description("New description")

        assert persona.description == "New description"
        assert persona.version == 2

    def test_persona_add_erpnext_role(self):
        """Test adding ERPNext role to persona."""
        persona = Persona(name="Test User", erpnext_roles=["Sales User"])

        persona.add_erpnext_role("Sales Manager")

        assert "Sales Manager" in persona.erpnext_roles
        assert len(persona.erpnext_roles) == 2
        assert persona.version == 2

    def test_persona_remove_erpnext_role(self):
        """Test removing ERPNext role from persona."""
        persona = Persona(
            name="Test User", erpnext_roles=["Sales User", "Sales Manager", "Customer"]
        )

        persona.remove_erpnext_role("Sales Manager")

        assert "Sales Manager" not in persona.erpnext_roles
        assert len(persona.erpnext_roles) == 2
        assert persona.version == 2

    def test_persona_remove_erpnext_role_validation(self):
        """Test validation when removing ERPNext role."""
        persona = Persona(name="Test User", erpnext_roles=["Sales User"])  # Only one role

        # Should not allow removing the last role
        with pytest.raises(PersonaValidationError):
            persona.remove_erpnext_role("Sales User")

    def test_persona_activate_deactivate(self):
        """Test persona activation and deactivation."""
        persona = Persona(name="Test User", erpnext_roles=["Sales User"], is_active=False)

        # Test activation
        persona.activate()
        assert persona.is_active is True
        assert persona.version == 2

        # Test deactivation
        persona.deactivate()
        assert persona.is_active is False
        assert persona.version == 3

    def test_persona_equality(self):
        """Test persona equality comparison."""
        persona1 = Persona(name="Test User", erpnext_roles=["Sales User"])

        persona2 = Persona(name="Test User", erpnext_roles=["Sales User"])

        # Different instances with same data should not be equal (different IDs)
        assert persona1 != persona2

        # Same instance should be equal to itself
        assert persona1 == persona1

    def test_persona_string_representation(self):
        """Test persona string representation."""
        persona = Persona(
            name="Sales Manager", erpnext_roles=["Sales Manager", "Customer"]
        )

        str_repr = str(persona)
        assert "Sales Manager" in str_repr
        assert str(persona.id) in str_repr


class TestPersonaDomainService:
    """Test the PersonaDomainService business logic."""

    def test_validate_persona_creation_success(self):
        """Test successful persona creation validation."""
        service = PersonaDomainService()

        persona = Persona(
            name="Valid Persona",
            description="Valid description",
            erpnext_roles=["Sales Manager", "Customer"],
            permissions="read_sales_order,write_sales_order",
            is_active=True,
        )

        # Should not raise any exception
        service.validate_persona_creation(persona)

    def test_validate_persona_creation_invalid_data(self):
        """Test persona creation validation with invalid data."""
        service = PersonaDomainService()

        # Test with invalid role
        with pytest.raises(PersonaValidationError):
            persona = Persona(name="Invalid Persona", erpnext_roles=["Invalid Role"])
            service.validate_persona_creation(persona)

    def test_validate_persona_update_success(self):
        """Test successful persona update validation."""
        service = PersonaDomainService()

        original_persona = Persona(name="Original Name", erpnext_roles=["Sales User"])

        updated_persona = Persona(
            name="Updated Name", erpnext_roles=["Sales User", "Sales Manager"]
        )
        updated_persona.id = original_persona.id  # Same ID

        # Should not raise any exception
        service.validate_persona_update(original_persona, updated_persona)

    def test_calculate_persona_similarity_identical(self):
        """Test similarity calculation for identical personas."""
        service = PersonaDomainService()

        persona1 = Persona(
            name="Sales Manager",
            description="Manages sales operations",
            erpnext_roles=["Sales Manager", "Customer"],
            permissions="read_sales_order,write_sales_order",
        )

        persona2 = Persona(
            name="Sales Manager",
            description="Manages sales operations",
            erpnext_roles=["Sales Manager", "Customer"],
            permissions="read_sales_order,write_sales_order",
        )

        similarity = service.calculate_persona_similarity(persona1, persona2)

        # Should be very high similarity (close to 1.0)
        assert similarity > 0.9

    def test_calculate_persona_similarity_different(self):
        """Test similarity calculation for different personas."""
        service = PersonaDomainService()

        persona1 = Persona(
            name="Sales Manager",
            description="Manages sales operations",
            erpnext_roles=["Sales Manager", "Customer"],
            permissions="read_sales_order,write_sales_order",
        )

        persona2 = Persona(
            name="HR Manager",
            description="Manages human resources",
            erpnext_roles=["HR Manager", "Employee"],
            permissions="read_employee,write_employee",
        )

        similarity = service.calculate_persona_similarity(persona1, persona2)

        # Should be low similarity
        assert similarity < 0.5

    def test_find_similar_personas(self):
        """Test finding similar personas."""
        service = PersonaDomainService()

        target_persona = Persona(
            name="Senior Sales Manager",
            description="Senior sales manager with team leadership",
            erpnext_roles=["Sales Manager", "Customer", "Item Manager"],
            permissions="read_sales_order,write_sales_order,read_customer",
        )

        all_personas = [
            Persona(
                name="Sales Manager",
                description="Manages sales operations",
                erpnext_roles=["Sales Manager", "Customer"],
                permissions="read_sales_order,write_sales_order",
            ),
            Persona(
                name="Sales Representative",
                description="Individual sales contributor",
                erpnext_roles=["Sales User"],
                permissions="read_sales_order",
            ),
            Persona(
                name="HR Manager",
                description="Manages human resources",
                erpnext_roles=["HR Manager"],
                permissions="read_employee,write_employee",
            ),
        ]

        similar_personas = service.find_similar_personas(
            target_persona, all_personas, similarity_threshold=0.3
        )

        # Should find at least the sales-related personas
        assert len(similar_personas) >= 2

        # Results should be sorted by similarity (highest first)
        similarities = [result["similarity"] for result in similar_personas]
        assert similarities == sorted(similarities, reverse=True)

        # All results should meet the threshold
        assert all(result["similarity"] >= 0.3 for result in similar_personas)

    def test_generate_persona_suggestions(self):
        """Test generating persona suggestions based on context."""
        service = PersonaDomainService()

        context = "I need to test sales order creation and customer management"
        erpnext_modules = ["Sales", "CRM"]

        suggestions = service.generate_persona_suggestions(context, erpnext_modules)

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

        # Check that suggestions are relevant to sales context
        sales_related_found = False
        for suggestion in suggestions:
            assert "name" in suggestion
            assert "erpnext_roles" in suggestion
            assert "confidence" in suggestion

            if "sales" in suggestion["name"].lower():
                sales_related_found = True

        assert sales_related_found

    def test_validate_persona_permissions(self):
        """Test validation of persona permissions."""
        service = PersonaDomainService()

        # Valid permissions
        valid_permissions = ["read_sales_order", "write_sales_order", "read_customer"]
        assert service.validate_persona_permissions(valid_permissions) is True

        # Invalid permissions (hypothetical invalid ones)
        invalid_permissions = ["invalid_permission", "read_nonexistent"]
        result = service.validate_persona_permissions(invalid_permissions)

        # Should return False or raise exception depending on implementation
        assert result is False or isinstance(
            result, dict
        )  # Could return validation details

    def test_get_role_based_permissions(self):
        """Test getting permissions based on ERPNext roles."""
        service = PersonaDomainService()

        roles = ["Sales Manager", "Customer"]
        role_permissions = service.get_role_based_permissions(roles)

        assert isinstance(role_permissions, list)
        assert len(role_permissions) > 0

        # Should include sales-related permissions
        sales_perms_found = any("sales" in perm.lower() for perm in role_permissions)
        assert sales_perms_found

    def test_merge_personas(self):
        """Test merging two personas."""
        service = PersonaDomainService()

        persona1 = Persona(
            name="Sales Manager A",
            description="First sales manager",
            erpnext_roles=["Sales Manager", "Customer"],
            permissions="read_sales_order,write_sales_order",
        )

        persona2 = Persona(
            name="Sales Manager B",
            description="Second sales manager",
            erpnext_roles=["Sales Manager", "Item Manager"],
            permissions="read_item,write_item",
        )

        merged_persona = service.merge_personas(
            persona1, persona2, "Merged Sales Manager"
        )

        assert merged_persona.name == "Merged Sales Manager"

        # Should have combined roles (unique)
        expected_roles = {"Sales Manager", "Customer", "Item Manager"}
        assert set(merged_persona.erpnext_roles) == expected_roles

        # Should have combined permissions
        assert "read_sales_order" in merged_persona.permissions_list
        assert "read_item" in merged_persona.permissions_list


class TestERPNextRoleValidator:
    """Test ERPNext role validation."""

    def test_valid_roles(self):
        """Test validation of valid ERPNext roles."""
        valid_roles = [
            "Administrator",
            "System Manager",
            "Sales Manager", 
            "Sales User",
            "Purchase Manager",
            "Stock Manager",
            "Accounts Manager",
            "HR Manager",
            "Customer",
            "Supplier",
        ]

        for role in valid_roles:
            assert ERPNextRole.is_valid_role(role) is True

    def test_invalid_roles(self):
        """Test validation of invalid ERPNext roles."""
        invalid_roles = [
            "Invalid Role",
            "Non Existent Role",
            "",
            "admin",  # Case sensitive
            "sales manager",  # Case sensitive
        ]

        for role in invalid_roles:
            assert ERPNextRole.is_valid_role(role) is False

    def test_get_all_roles(self):
        """Test getting all available ERPNext roles."""
        all_roles = ERPNextRole.get_all_roles()

        assert isinstance(all_roles, list)
        assert len(all_roles) > 0
        assert "Administrator" in all_roles
        assert "Sales Manager" in all_roles
        assert "HR Manager" in all_roles

    def test_get_roles_by_module(self):
        """Test getting roles filtered by ERPNext module."""
        sales_roles = ERPNextRole.get_module_roles("Sales")

        assert isinstance(sales_roles, list)
        assert len(sales_roles) > 0
        assert "Sales Manager" in sales_roles
        assert "Sales User" in sales_roles

    def test_get_role_permissions(self):
        """Test getting permissions for a specific role."""
        sales_manager_perms = ERPNextRole.get_role_permissions("Sales Manager")

        assert isinstance(sales_manager_perms, list)
        assert len(sales_manager_perms) > 0

        # Should include sales-related permissions
        sales_perms_found = any("sales" in perm.lower() for perm in sales_manager_perms)
        assert sales_perms_found


class TestPersonaExceptions:
    """Test persona-related exceptions."""

    def test_persona_validation_error(self):
        """Test PersonaValidationError exception."""
        error = PersonaValidationError("name", "Name is required")

        assert str(error) == "Name is required"
        assert error.field == "name"
        assert error.message == "Name is required"

    def test_persona_multiple_validation_error(self):
        """Test PersonaMultipleValidationError exception."""
        errors = [
            PersonaValidationError("name", "Name is required"),
            PersonaValidationError("erpnext_roles", "At least one role is required"),
        ]

        multi_error = PersonaMultipleValidationError(errors)

        assert len(multi_error.errors) == 2
        assert "Name is required" in str(multi_error)
        assert "At least one role is required" in str(multi_error)

    def test_persona_not_found_error(self):
        """Test PersonaNotFoundError exception."""
        persona_id = str(uuid.uuid4())
        error = PersonaNotFoundError(persona_id)

        assert persona_id in str(error)

    def test_persona_already_exists_error(self):
        """Test PersonaAlreadyExistsError exception."""
        error = PersonaAlreadyExistsError("name", "Sales Manager")

        assert error.field == "name"
        assert error.value == "Sales Manager"
        assert "Sales Manager" in str(error)


if __name__ == "__main__":
    pytest.main([__file__])
