"""Persona form components for ERPNext Test Automation Meta-Framework.

Provides comprehensive Streamlit components for creating and editing personas
with rich validation, ERPNext role selection, and user-friendly interfaces.
"""

import logging
from typing import Any, Optional

import streamlit as st
from streamlit import session_state as ss
from streamlit.delta_generator import DeltaGenerator

from components.shared.validation import (
    ValidationError,
    display_validation_errors,
    validate_required_field,
    validate_text_length,
)
from services.api_client import APIClient

logger = logging.getLogger(__name__)


class PersonaFormState:
    """Manages persona form state and validation."""

    def __init__(self, form_key: str = "persona_form"):
        """Initialize form state manager.

        Args:
            form_key: Unique key for this form instance
        """
        self.form_key = form_key
        self.errors_key = f"{form_key}_errors"
        self.warnings_key = f"{form_key}_warnings"

        # Initialize session state
        if self.form_key not in ss:
            ss[self.form_key] = self._get_default_form_data()
        if self.errors_key not in ss:
            ss[self.errors_key] = {}
        if self.warnings_key not in ss:
            ss[self.warnings_key] = {}

    def _get_default_form_data(self) -> dict[str, Any]:
        """Get default form data structure."""
        return {
            "name": "",
            "description": "",
            "erpnext_roles": [],
            "permissions": "",
            "is_active": True,
            "validation_pending": False,
            "last_validated": None,
        }

    def get_data(self) -> dict[str, Any]:
        """Get current form data."""
        return ss[self.form_key].copy()

    def set_data(self, data: dict[str, Any]) -> None:
        """Set form data."""
        ss[self.form_key].update(data)

    def clear(self) -> None:
        """Clear all form data."""
        ss[self.form_key] = self._get_default_form_data()
        ss[self.errors_key] = {}
        ss[self.warnings_key] = {}

    def add_error(self, field: str, message: str) -> None:
        """Add validation error."""
        ss[self.errors_key][field] = message

    def clear_errors(self, field: Optional[str] = None) -> None:
        """Clear validation errors."""
        if field:
            ss[self.errors_key].pop(field, None)
        else:
            ss[self.errors_key] = {}

    def get_errors(self) -> dict[str, str]:
        """Get current validation errors."""
        return ss[self.errors_key].copy()

    def has_errors(self) -> bool:
        """Check if form has validation errors."""
        return bool(ss[self.errors_key])


class PersonaFormComponent:
    """Streamlit component for persona creation and editing."""

    def __init__(self, api_client: APIClient, form_key: str = "persona_form"):
        """Initialize persona form component.

        Args:
            api_client: API client for backend communication
            form_key: Unique identifier for form state
        """
        self.api_client = api_client
        self.form_state = PersonaFormState(form_key)
        self.erpnext_roles = self._load_erpnext_roles()

    def _load_erpnext_roles(self) -> list[str]:
        """Load available ERPNext roles from backend or cache."""
        # In production, this would fetch from the backend API
        # For now, using a comprehensive static list
        return [
            # Core System Roles
            "Administrator",
            "System Manager",
            "User",
            "Guest",
            # Sales Roles
            "Sales Manager",
            "Sales Master Manager",
            "Sales User",
            # Purchase Roles
            "Purchase Manager",
            "Purchase Master Manager",
            "Purchase User",
            # Stock/Inventory Roles
            "Stock Manager",
            "Stock User",
            "Item Manager",
            # Accounts/Finance Roles
            "Accounts Manager",
            "Accounts User",
            "Auditor",
            "Invoice Manager",
            # HR Roles
            "HR Manager",
            "HR User",
            "Employee",
            "Leave Approver",
            # Manufacturing Roles
            "Manufacturing Manager",
            "Manufacturing User",
            # Projects Roles
            "Projects Manager",
            "Projects User",
            # CRM Roles
            "Customer",
            "Supplier",
            "Lead",
            # Support Roles
            "Support Team",
            "Maintenance Manager",
            "Maintenance User",
            # Website Roles
            "Website Manager",
            "Blogger",
            # Quality Roles
            "Quality Manager",
        ]

    def render_creation_form(
        self, container: Optional[DeltaGenerator] = None, show_title: bool = True
    ) -> tuple[bool, Optional[dict[str, Any]]]:
        """Render persona creation form.

        Args:
            container: Optional Streamlit container to render in
            show_title: Whether to show form title

        Returns:
            Tuple of (form_submitted, form_data or None)
        """
        if container is None:
            container = st

        # Use context manager only if container is not the main st module
        if container is st:
            # Render directly in main area
            if show_title:
                st.subheader("📝 Create New Persona")
                st.markdown(
                    "Define a new test persona with specific ERPNext roles and permissions."
                )
        else:
            with container:
                if show_title:
                    st.subheader("📝 Create New Persona")
                    st.markdown(
                        "Define a new test persona with specific ERPNext roles and permissions."
                    )

            # Display any existing errors
            if self.form_state.has_errors():
                display_validation_errors(self.form_state.get_errors())

            with st.form("create_persona_form", clear_on_submit=False):
                # Basic Information
                st.markdown("### 📋 Basic Information")

                form_data = self.form_state.get_data()

                name = st.text_input(
                    "Persona Name *",
                    value=form_data.get("name", ""),
                    placeholder="e.g., Sales Manager, Purchase Officer, Stock Keeper",
                    help="A descriptive name for this persona. Must be unique within your workspace.",
                )

                description = st.text_area(
                    "Description",
                    value=form_data.get("description", ""),
                    placeholder="Describe the role, responsibilities, and context for this persona...",
                    help="Detailed description of the persona's purpose and context in test scenarios.",
                    height=100,
                )

                # ERPNext Roles Section
                st.markdown("### 🎭 ERPNext Roles")
                st.markdown("Select the ERPNext roles this persona should have:")

                selected_roles = st.multiselect(
                    "ERPNext Roles *",
                    options=self.erpnext_roles,
                    default=form_data.get("erpnext_roles", []),
                    help="Choose one or more ERPNext roles. These determine the persona's base permissions.",
                    placeholder="Select ERPNext roles...",
                )

                # Show role descriptions for selected roles
                if selected_roles:
                    with st.expander("ℹ️ Selected Roles Information"):
                        for role in selected_roles:
                            st.markdown(
                                f"**{role}**: {self._get_role_description(role)}"
                            )

                # Additional Permissions
                st.markdown("### 🔐 Additional Permissions")
                permissions = st.text_area(
                    "Custom Permissions (Optional)",
                    value=form_data.get("permissions", ""),
                    placeholder="read_customer,write_sales_order,delete_item",
                    help="Additional specific permissions beyond role defaults. Use comma-separated format.",
                    height=80,
                )

                # Status
                st.markdown("### ⚙️ Settings")
                col1, col2 = st.columns(2)

                with col1:
                    is_active = st.checkbox(
                        "Active Persona",
                        value=form_data.get("is_active", True),
                        help="Active personas can be used in test generation. Inactive personas are for drafts.",
                    )

                with col2:
                    validate_now = st.checkbox(
                        "Validate on Submit",
                        value=True,
                        help="Validate persona data with ERPNext before creating.",
                    )

                # Submit Section
                st.markdown("---")
                col1, col2, col3 = st.columns([2, 1, 1])

                with col2:
                    validate_only = st.form_submit_button(
                        "🔍 Validate Only", help="Check persona data without creating"
                    )

                with col3:
                    create_persona = st.form_submit_button(
                        "✅ Create Persona",
                        type="primary",
                        help="Create the new persona",
                    )

                # Handle form submission
                if validate_only or create_persona:
                    # Clear previous errors
                    self.form_state.clear_errors()

                    # Client-side validation
                    validation_success = self._validate_form_data(
                        {
                            "name": name,
                            "description": description,
                            "erpnext_roles": selected_roles,
                            "permissions": permissions,
                            "is_active": is_active,
                        }
                    )

                    if validation_success:
                        # Update form state
                        self.form_state.set_data(
                            {
                                "name": name,
                                "description": description,
                                "erpnext_roles": selected_roles,
                                "permissions": permissions,
                                "is_active": is_active,
                            }
                        )

                        if validate_only:
                            return self._handle_validation_only()
                        elif create_persona:
                            return self._handle_creation_submit(validate_now)
                    else:
                        st.rerun()  # Refresh to show validation errors

        return False, None

    def render_edit_form(
        self,
        persona_data: dict[str, Any],
        container: Optional[DeltaGenerator] = None,
        show_title: bool = True,
    ) -> tuple[bool, Optional[dict[str, Any]]]:
        """Render persona editing form.

        Args:
            persona_data: Existing persona data to edit
            container: Optional Streamlit container to render in
            show_title: Whether to show form title

        Returns:
            Tuple of (form_submitted, updated_data or None)
        """
        if container is None:
            # Render directly in current context
            if show_title:
                st.subheader(f"✏️ Edit Persona: {persona_data.get('name', 'Unknown')}")
                st.markdown("Modify persona information and settings.")

            # Initialize form with existing data
            if not self.form_state.get_data().get("name"):
                self.form_state.set_data(
                    {
                        "name": persona_data.get("name", ""),
                        "description": persona_data.get("description", ""),
                        "erpnext_roles": persona_data.get("erpnext_roles_list", []),
                        "permissions": persona_data.get("permissions", ""),
                        "is_active": persona_data.get("is_active", True),
                    }
                )
        else:
            with container:
                if show_title:
                    st.subheader(f"✏️ Edit Persona: {persona_data.get('name', 'Unknown')}")
                    st.markdown("Modify persona information and settings.")

                # Initialize form with existing data
                if not self.form_state.get_data().get("name"):
                    self.form_state.set_data(
                        {
                            "name": persona_data.get("name", ""),
                            "description": persona_data.get("description", ""),
                            "erpnext_roles": persona_data.get("erpnext_roles_list", []),
                            "permissions": persona_data.get("permissions", ""),
                            "is_active": persona_data.get("is_active", True),
                        }
                    )

        # Display any existing errors
        if self.form_state.has_errors():
            display_validation_errors(self.form_state.get_errors())

        return self.render_creation_form(container, show_title=False)

    def _validate_form_data(self, data: dict[str, Any]) -> bool:
        """Validate form data on client side.

        Args:
            data: Form data to validate

        Returns:
            True if validation passes, False otherwise
        """
        is_valid = True

        # Required field validation
        if not validate_required_field(
            data.get("name", ""), "Persona name is required"
        ):
            self.form_state.add_error("name", "Persona name is required")
            is_valid = False

        # Name length validation
        name = data.get("name", "")
        if name and not validate_text_length(name, min_length=2, max_length=100):
            self.form_state.add_error(
                "name", "Persona name must be 2-100 characters long"
            )
            is_valid = False

        # ERPNext roles validation
        roles = data.get("erpnext_roles", [])
        if not roles:
            self.form_state.add_error(
                "erpnext_roles", "At least one ERPNext role is required"
            )
            is_valid = False

        # Description length validation
        description = data.get("description", "")
        if description and len(description) > 1000:
            self.form_state.add_error(
                "description", "Description cannot exceed 1000 characters"
            )
            is_valid = False

        # Permissions format validation
        permissions = data.get("permissions", "")
        if permissions and not self._validate_permissions_format(permissions):
            self.form_state.add_error(
                "permissions", "Invalid permissions format. Use comma-separated values."
            )
            is_valid = False

        return is_valid

    def _validate_permissions_format(self, permissions: str) -> bool:
        """Validate permissions format.

        Args:
            permissions: Comma-separated permissions string

        Returns:
            True if format is valid, False otherwise
        """
        if not permissions.strip():
            return True

        # Check for valid permission format (alphanumeric, underscore, comma, space)
        import re

        pattern = r"^[a-zA-Z0-9_,\s]+$"
        return bool(re.match(pattern, permissions))

    def _handle_validation_only(self) -> tuple[bool, Optional[dict[str, Any]]]:
        """Handle validation-only form submission.

        Returns:
            Tuple indicating validation was requested
        """
        try:
            form_data = self.form_state.get_data()

            # Call backend validation API
            validation_result = self.api_client.validate_persona_data(
                {
                    "name": form_data["name"],
                    "description": form_data["description"],
                    "erpnext_roles": ",".join(form_data["erpnext_roles"]),
                    "permissions": form_data["permissions"],
                    "is_active": form_data["is_active"],
                }
            )

            if validation_result.get("is_valid", False):
                st.success("✅ Persona data is valid!")

                # Show warnings if any
                warnings = validation_result.get("warnings", [])
                if warnings:
                    st.warning("⚠️ Validation Warnings:")
                    for warning in warnings:
                        st.markdown(
                            f"- **{warning.get('field', 'General')}**: {warning.get('message', '')}"
                        )

                # Show suggestions if any
                suggestions = validation_result.get("suggestions", [])
                if suggestions:
                    st.info("💡 Suggestions:")
                    for suggestion in suggestions:
                        st.markdown(
                            f"- **{suggestion.get('field', 'General')}**: {suggestion.get('message', '')}"
                        )
            else:
                st.error("❌ Persona data has validation errors:")
                errors = validation_result.get("errors", [])
                for error in errors:
                    st.markdown(
                        f"- **{error.get('field', 'General')}**: {error.get('message', '')}"
                    )

        except Exception as e:
            logger.error(f"Validation error: {e}")
            st.error(f"Validation failed: {str(e)}")

        return False, None

    def _handle_creation_submit(
        self, validate_first: bool = True
    ) -> tuple[bool, Optional[dict[str, Any]]]:
        """Handle persona creation form submission.

        Args:
            validate_first: Whether to validate before creating

        Returns:
            Tuple of (success, created_persona_data or None)
        """
        try:
            form_data = self.form_state.get_data()

            # Optional server-side validation first
            if validate_first:
                validation_result = self.api_client.validate_persona_data(
                    {
                        "name": form_data["name"],
                        "description": form_data["description"],
                        "erpnext_roles": ",".join(form_data["erpnext_roles"]),
                        "permissions": form_data["permissions"],
                        "is_active": form_data["is_active"],
                    }
                )

                if not validation_result.get("is_valid", False):
                    st.error("❌ Cannot create persona - validation failed:")
                    errors = validation_result.get("errors", [])
                    for error in errors:
                        st.markdown(
                            f"- **{error.get('field', 'General')}**: {error.get('message', '')}"
                        )
                    return False, None

            # Create persona via API
            created_persona = self.api_client.create_persona(
                {
                    "name": form_data["name"],
                    "description": form_data["description"],
                    "erpnext_roles": ",".join(form_data["erpnext_roles"]),
                    "permissions": form_data["permissions"],
                    "is_active": form_data["is_active"],
                }
            )

            st.success(f"✅ Successfully created persona '{created_persona['name']}'!")

            # Clear form state
            self.form_state.clear()

            return True, created_persona

        except Exception as e:
            logger.error(f"Error creating persona: {e}")
            st.error(f"Failed to create persona: {str(e)}")
            return False, None

    def _get_role_description(self, role: str) -> str:
        """Get description for an ERPNext role.

        Args:
            role: ERPNext role name

        Returns:
            Role description
        """
        role_descriptions = {
            "Administrator": "Full system access with all permissions",
            "System Manager": "System configuration and user management",
            "Sales Manager": "Manage sales operations, orders, and customers",
            "Sales User": "Create and process sales orders and quotations",
            "Purchase Manager": "Manage procurement, suppliers, and purchase orders",
            "Purchase User": "Create and process purchase orders and requests",
            "Stock Manager": "Manage inventory, warehouses, and stock movements",
            "Stock User": "Process stock transactions and movements",
            "Item Manager": "Manage item master data and categories",
            "Accounts Manager": "Manage financial transactions and reports",
            "Accounts User": "Process payments, invoices, and journal entries",
            "HR Manager": "Manage employees, payroll, and HR processes",
            "HR User": "Process attendance, leave, and employee data",
            "Customer": "External customer access with limited permissions",
            "Supplier": "External supplier access for order management",
        }

        return role_descriptions.get(
            role, "Standard ERPNext role with module-specific permissions"
        )


def render_persona_form(
    api_client: APIClient,
    mode: str = "create",
    persona_data: Optional[dict[str, Any]] = None,
    container: Optional[DeltaGenerator] = None,
) -> tuple[bool, Optional[dict[str, Any]]]:
    """Convenience function to render persona forms.

    Args:
        api_client: API client instance
        mode: Form mode - 'create' or 'edit'
        persona_data: Existing persona data for edit mode
        container: Optional Streamlit container

    Returns:
        Tuple of (form_submitted, form_result or None)
    """
    form_component = PersonaFormComponent(api_client)

    if mode == "create":
        return form_component.render_creation_form(container)
    elif mode == "edit" and persona_data:
        return form_component.render_edit_form(persona_data, container)
    else:
        st.error("Invalid form mode or missing persona data for edit mode")
        return False, None
