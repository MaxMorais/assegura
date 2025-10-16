"""Personas management page for ERPNext Test Automation Meta-Framework.

Comprehensive interface for creating, editing, viewing, and managing test personas
with full CRUD operations and advanced filtering capabilities.
"""

import logging
from typing import Any, Optional

import streamlit as st
from streamlit import session_state as ss

from components.persona_forms.persona_form import PersonaFormComponent
from components.persona_forms.persona_list import PersonaListComponent
from services.api_client import APIClient, api_client

logger = logging.getLogger(__name__)


class PersonaPageState:
    """Manages persona page state and navigation."""

    def __init__(self):
        """Initialize page state manager."""
        if "persona_page_state" not in ss:
            ss.persona_page_state = {
                "current_view": "list",  # 'list', 'create', 'edit', 'view'
                "selected_persona": None,
                "show_confirmation": False,
                "confirmation_action": None,
                "confirmation_data": None,
            }

    def set_view(
        self, view: str, persona_data: Optional[dict[str, Any]] = None
    ) -> None:
        """Set current view and optional persona data."""
        ss.persona_page_state["current_view"] = view
        ss.persona_page_state["selected_persona"] = persona_data

    def get_view(self) -> str:
        """Get current view."""
        return ss.persona_page_state.get("current_view", "list")

    def get_selected_persona(self) -> Optional[dict[str, Any]]:
        """Get currently selected persona."""
        return ss.persona_page_state.get("selected_persona")

    def set_confirmation(self, action: str, data: Any = None) -> None:
        """Set confirmation dialog state."""
        ss.persona_page_state.update(
            {
                "show_confirmation": True,
                "confirmation_action": action,
                "confirmation_data": data,
            }
        )

    def clear_confirmation(self) -> None:
        """Clear confirmation dialog state."""
        ss.persona_page_state.update(
            {
                "show_confirmation": False,
                "confirmation_action": None,
                "confirmation_data": None,
            }
        )

    def get_confirmation(self) -> tuple:
        """Get confirmation dialog state."""
        return (
            ss.persona_page_state.get("show_confirmation", False),
            ss.persona_page_state.get("confirmation_action"),
            ss.persona_page_state.get("confirmation_data"),
        )


def render_personas_page():
    """Render the personas management page with full functionality."""
    # Configure page
    st.set_page_config(
        page_title="Personas - ERPNext Test Framework",
        page_icon="🎭",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize components
    # Use global api_client from services module (already configured with environment)
    page_state = PersonaPageState()

    # Page title and navigation
    st.markdown("Create and manage test personas that represent different user types in your ERPNext system.")

    # Handle confirmation dialogs
    _handle_confirmation_dialogs(api_client, page_state)

    # Route to appropriate view
    current_view = page_state.get_view()
    if current_view == "list":
        _render_personas_list_view(api_client, page_state)
    elif current_view == "create":
        _render_create_persona_view(api_client, page_state)
    elif current_view == "edit":
        _render_edit_persona_view(api_client, page_state)
    elif current_view == "view":
        _render_view_persona_view(api_client, page_state)


def _render_personas_list_view(api_client: APIClient, page_state: PersonaPageState):
    """Render the main personas list view."""
    # Quick stats
    try:
        stats = api_client.get_persona_statistics()
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Personas", stats.get("total_personas", 0))
        with col2:
            st.metric("Active", stats.get("active_personas", 0))
        with col3:
            st.metric("Inactive", stats.get("inactive_personas", 0))
        with col4:
            st.metric("Total Activities", stats.get("total_activities", 0))
    except Exception as e:
        logger.warning(f"Could not load statistics: {e}")

    # Initialize list component
    list_component = PersonaListComponent(api_client, "main_persona_list")

    # Load personas
    if not list_component.load_personas():
        st.error("Failed to load personas. Please try refreshing the page.")
        return

    # Render list with callbacks
    action = list_component.render_persona_list(
        show_title=True,  # Show the create button and title
        on_persona_click=lambda p: page_state.set_view("view", p),
        on_persona_edit=lambda p: page_state.set_view("edit", p),
        on_persona_delete=lambda p: page_state.set_confirmation("delete_persona", p),
    )

    # Handle actions
    if action == "create_new":
        page_state.set_view("create")
        st.rerun()
    elif action == "refresh":
        list_component.load_personas(force_refresh=True)
        st.rerun()
    elif (
        action == "filters_changed"
        or action == "page_changed"
        or action == "page_size_changed"
    ):
        list_component.load_personas(force_refresh=True)
        st.rerun()


def _render_create_persona_view(api_client: APIClient, page_state: PersonaPageState):
    """Render the create persona view."""
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("⬅️ Back to List"):
            page_state.set_view("list")
            st.rerun()

    # Create form
    form_component = PersonaFormComponent(api_client, "create_persona_form")
    form_submitted, result = form_component.render_creation_form()

    if form_submitted and result:
        st.success(f"✅ Successfully created persona '{result['name']}'!")
        page_state.set_view("list")
        st.rerun()


def _render_edit_persona_view(api_client: APIClient, page_state: PersonaPageState):
    """Render the edit persona view."""
    selected_persona = page_state.get_selected_persona()

    if not selected_persona:
        st.error("No persona selected for editing.")
        page_state.set_view("list")
        st.rerun()
        return

    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("⬅️ Back to List"):
            page_state.set_view("list")
            st.rerun()

    with col3:
        if st.button("👁️ View Mode"):
            page_state.set_view("view", selected_persona)
            st.rerun()

    # Edit form
    form_component = PersonaFormComponent(api_client, "edit_persona_form")
    form_submitted, result = form_component.render_edit_form(selected_persona)

    if form_submitted and result:
        st.success(f"✅ Successfully updated persona '{result['name']}'!")
        page_state.set_view("view", result)
        st.rerun()


def _render_view_persona_view(api_client: APIClient, page_state: PersonaPageState):
    """Render the view persona details view."""
    selected_persona = page_state.get_selected_persona()

    if not selected_persona:
        st.error("No persona selected for viewing.")
        page_state.set_view("list")
        st.rerun()
        return

    col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
    with col1:
        if st.button("⬅️ Back to List"):
            page_state.set_view("list")
            st.rerun()

    with col2:
        st.markdown(f"### {selected_persona.get('name', 'Unknown Persona')}")

    with col3:
        if st.button("✏️ Edit"):
            page_state.set_view("edit", selected_persona)
            st.rerun()

    with col4:
        if st.button("🗑️ Delete", type="secondary"):
            page_state.set_confirmation("delete_persona", selected_persona)
            st.rerun()

    # Persona details
    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📋 Basic Information")
        st.markdown(f"**Name:** {selected_persona.get('name', 'N/A')}")
        st.markdown(
            f"**Description:** {selected_persona.get('description', 'No description provided')}"
        )

        st.subheader("🎭 ERPNext Roles")
        roles = selected_persona.get("erpnext_roles_list", [])
        if roles:
            for role in roles:
                st.markdown(f"• `{role}`")
        else:
            st.markdown("_No roles assigned_")

    with col2:
        st.subheader("ℹ️ Status & Metadata")

        status = "✅ Active" if selected_persona.get("is_active") else "⚠️ Inactive"
        st.markdown(f"**Status:** {status}")

        created_at = selected_persona.get("created_at")
        if created_at:
            st.markdown(f"**Created:** {created_at}")


def _handle_confirmation_dialogs(api_client: APIClient, page_state: PersonaPageState):
    """Handle confirmation dialogs for destructive actions."""
    show_confirmation, action, data = page_state.get_confirmation()

    if not show_confirmation:
        return

    if action == "delete_persona":
        persona = data

        with st.container():
            st.error("🗑️ **Confirm Deletion**")
            st.markdown(
                f"Are you sure you want to delete persona **{persona.get('name')}**?"
            )
            st.markdown("⚠️ This action cannot be undone.")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ Yes, Delete", type="primary"):
                    try:
                        api_client.delete_persona(persona["id"])
                        st.success(f"Deleted persona '{persona['name']}'")
                        page_state.clear_confirmation()
                        page_state.set_view("list")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to delete persona: {str(e)}")
                        page_state.clear_confirmation()
                        st.rerun()

            with col2:
                if st.button("❌ Cancel"):
                    page_state.clear_confirmation()
                    st.rerun()


# Compatibility function for existing imports
def show_personas() -> None:
    """Legacy function for compatibility."""
    render_personas_page()


if __name__ == "__main__":
    render_personas_page()
