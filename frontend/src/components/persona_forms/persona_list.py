"""Persona list display components for ERPNext Test Automation Meta-Framework.

Provides comprehensive Streamlit components for displaying, filtering,
and managing lists of personas with rich interactions and bulk operations.
"""

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any, Optional

import streamlit as st
from streamlit import session_state as ss
from streamlit.delta_generator import DeltaGenerator

from services.api_client import APIClient

logger = logging.getLogger(__name__)


class PersonaListState:
    """Manages persona list state and pagination."""

    def __init__(self, list_key: str = "persona_list"):
        """Initialize list state manager.

        Args:
            list_key: Unique key for this list instance
        """
        self.list_key = list_key
        self.filters_key = f"{list_key}_filters"
        self.selection_key = f"{list_key}_selection"

        # Initialize session state
        if self.list_key not in ss:
            ss[self.list_key] = {
                "personas": [],
                "total": 0,
                "limit": 50,
                "offset": 0,
                "has_more": False,
                "loading": False,
                "last_updated": None,
            }

        if self.filters_key not in ss:
            ss[self.filters_key] = {
                "search": "",
                "is_active": None,
                "erpnext_role": None,
                "sort_by": "updated_at",
                "sort_order": "desc",
            }

        if self.selection_key not in ss:
            ss[self.selection_key] = {"selected_personas": [], "select_all": False}

    def get_list_data(self) -> dict[str, Any]:
        """Get current list data."""
        return ss[self.list_key].copy()

    def set_list_data(self, data: dict[str, Any]) -> None:
        """Set list data."""
        ss[self.list_key].update(data)

    def get_filters(self) -> dict[str, Any]:
        """Get current filters."""
        return ss[self.filters_key].copy()

    def set_filters(self, filters: dict[str, Any]) -> None:
        """Set filters."""
        ss[self.filters_key].update(filters)

    def get_selection(self) -> dict[str, Any]:
        """Get current selection."""
        return ss[self.selection_key].copy()

    def set_selection(self, selection: dict[str, Any]) -> None:
        """Set selection."""
        ss[self.selection_key].update(selection)

    def clear_selection(self) -> None:
        """Clear all selections."""
        ss[self.selection_key] = {"selected_personas": [], "select_all": False}


class PersonaListComponent:
    """Streamlit component for displaying persona lists with rich interactions."""

    def __init__(self, api_client: APIClient, list_key: str = "persona_list"):
        """Initialize persona list component.

        Args:
            api_client: API client for backend communication
            list_key: Unique identifier for list state
        """
        self.api_client = api_client
        self.list_state = PersonaListState(list_key)

    def render_persona_list(
        self,
        container: Optional[DeltaGenerator] = None,
        show_title: bool = True,
        show_filters: bool = True,
        show_actions: bool = True,
        on_persona_click: Optional[Callable[[dict[str, Any]], None]] = None,
        on_persona_edit: Optional[Callable[[dict[str, Any]], None]] = None,
        on_persona_delete: Optional[Callable[[dict[str, Any]], None]] = None,
    ) -> Optional[str]:
        """Render complete persona list with filters and actions.

        Args:
            container: Optional Streamlit container to render in
            show_title: Whether to show list title
            show_filters: Whether to show filter controls
            show_actions: Whether to show action buttons
            on_persona_click: Callback for persona click events
            on_persona_edit: Callback for edit button clicks
            on_persona_delete: Callback for delete button clicks

        Returns:
            Action taken if any ('refresh', 'create_new', etc.)
        """
        if container is None:
            container = st

        with container:
            action_taken = None

            # Title and summary
            if show_title:
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.subheader("👥 Test Personas")
                    list_data = self.list_state.get_list_data()
                    total = list_data.get("total", 0)
                    if total > 0:
                        st.caption(
                            f"Showing {len(list_data.get('personas', []))} of {total} personas"
                        )

                with col2:
                    if st.button("🔄 Refresh", help="Reload persona list"):
                        action_taken = "refresh"

                with col3:
                    if st.button(
                        "➕ Create New", type="primary", help="Create new persona"
                    ):
                        action_taken = "create_new"

            # Filters
            if show_filters:
                action_taken = self._render_filters() or action_taken

            # Bulk actions
            if show_actions:
                action_taken = self._render_bulk_actions() or action_taken

            # Persona list
            action_taken = (
                self._render_persona_table(
                    on_persona_click=on_persona_click,
                    on_persona_edit=on_persona_edit,
                    on_persona_delete=on_persona_delete,
                )
                or action_taken
            )

            # Pagination
            action_taken = self._render_pagination() or action_taken

            return action_taken

    def _render_filters(self) -> Optional[str]:
        """Render filter controls.

        Returns:
            Action taken if any
        """
        filters = self.list_state.get_filters()
        filters_changed = False

        with st.expander("🔍 Filters & Search", expanded=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                new_search = st.text_input(
                    "Search personas",
                    value=filters.get("search", ""),
                    placeholder="Search by name or description...",
                    key="persona_search_input",
                )
                if new_search != filters.get("search", ""):
                    filters["search"] = new_search
                    filters_changed = True

            with col2:
                status_options = {"All": None, "Active": True, "Inactive": False}
                status_labels = list(status_options.keys())
                current_status = "All"
                for label, value in status_options.items():
                    if value == filters.get("is_active"):
                        current_status = label
                        break

                new_status_label = st.selectbox(
                    "Status",
                    options=status_labels,
                    index=status_labels.index(current_status),
                    key="persona_status_filter",
                )

                new_status = status_options[new_status_label]
                if new_status != filters.get("is_active"):
                    filters["is_active"] = new_status
                    filters_changed = True

            with col3:
                role_options = ["All"] + self._get_available_roles()
                current_role_index = 0
                if filters.get("erpnext_role"):
                    try:
                        current_role_index = role_options.index(filters["erpnext_role"])
                    except ValueError:
                        pass

                new_role = st.selectbox(
                    "ERPNext Role",
                    options=role_options,
                    index=current_role_index,
                    key="persona_role_filter",
                )

                role_value = None if new_role == "All" else new_role
                if role_value != filters.get("erpnext_role"):
                    filters["erpnext_role"] = role_value
                    filters_changed = True

            # Sort options
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                sort_options = {
                    "Recently Updated": "updated_at",
                    "Recently Created": "created_at",
                    "Name (A-Z)": "name",
                    "Most Active": "last_used",
                }

                current_sort = "Recently Updated"
                for label, value in sort_options.items():
                    if value == filters.get("sort_by", "updated_at"):
                        current_sort = label
                        break

                new_sort_label = st.selectbox(
                    "Sort by",
                    options=list(sort_options.keys()),
                    index=list(sort_options.keys()).index(current_sort),
                    key="persona_sort_by",
                )

                new_sort = sort_options[new_sort_label]
                if new_sort != filters.get("sort_by"):
                    filters["sort_by"] = new_sort
                    filters_changed = True

            with col2:
                order_options = {"Descending": "desc", "Ascending": "asc"}
                current_order = "Descending"
                for label, value in order_options.items():
                    if value == filters.get("sort_order", "desc"):
                        current_order = label
                        break

                new_order_label = st.selectbox(
                    "Order",
                    options=list(order_options.keys()),
                    index=list(order_options.keys()).index(current_order),
                    key="persona_sort_order",
                )

                new_order = order_options[new_order_label]
                if new_order != filters.get("sort_order"):
                    filters["sort_order"] = new_order
                    filters_changed = True

            with col3:
                if st.button("🔄 Apply Filters", key="apply_persona_filters"):
                    filters_changed = True

        if filters_changed:
            self.list_state.set_filters(filters)
            # Reset pagination when filters change
            list_data = self.list_state.get_list_data()
            list_data["offset"] = 0
            self.list_state.set_list_data(list_data)
            return "filters_changed"

        return None

    def _render_bulk_actions(self) -> Optional[str]:
        """Render bulk action controls.

        Returns:
            Action taken if any
        """
        selection = self.list_state.get_selection()
        selected_personas = selection.get("selected_personas", [])

        if not selected_personas:
            return None

        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

        with col1:
            st.markdown(f"**{len(selected_personas)} personas selected**")

        with col2:
            if st.button("✅ Activate Selected", help="Activate selected personas"):
                return "bulk_activate"

        with col3:
            if st.button("❌ Deactivate Selected", help="Deactivate selected personas"):
                return "bulk_deactivate"

        with col4:
            if st.button("📋 Export Selected", help="Export selected personas"):
                return "bulk_export"

        with col5:
            if st.button(
                "🗑️ Delete Selected", help="Delete selected personas", type="secondary"
            ):
                return "bulk_delete"

        return None

    def _render_persona_table(
        self,
        on_persona_click: Optional[Callable[[dict[str, Any]], None]] = None,
        on_persona_edit: Optional[Callable[[dict[str, Any]], None]] = None,
        on_persona_delete: Optional[Callable[[dict[str, Any]], None]] = None,
    ) -> Optional[str]:
        """Render persona table with interactions.

        Args:
            on_persona_click: Callback for persona click events
            on_persona_edit: Callback for edit button clicks
            on_persona_delete: Callback for delete button clicks

        Returns:
            Action taken if any
        """
        list_data = self.list_state.get_list_data()
        personas = list_data.get("personas", [])

        if not personas:
            st.info("📭 No personas found. Create your first persona to get started!")
            return None

        # Table header with select all
        col1, col2, col3, col4, col5, col6 = st.columns([0.5, 2, 3, 2, 1.5, 1])

        with col1:
            selection = self.list_state.get_selection()
            select_all = st.checkbox(
                "", value=selection.get("select_all", False), key="select_all_personas"
            )
            if select_all != selection.get("select_all", False):
                new_selection = {"select_all": select_all}
                if select_all:
                    new_selection["selected_personas"] = [p["id"] for p in personas]
                else:
                    new_selection["selected_personas"] = []
                self.list_state.set_selection(new_selection)
                st.rerun()

        with col2:
            st.markdown("**Name**")
        with col3:
            st.markdown("**Description**")
        with col4:
            st.markdown("**ERPNext Roles**")
        with col5:
            st.markdown("**Status**")
        with col6:
            st.markdown("**Actions**")

        st.markdown("---")

        # Persona rows
        selection = self.list_state.get_selection()
        selected_ids = selection.get("selected_personas", [])
        action_taken = None

        for i, persona in enumerate(personas):
            col1, col2, col3, col4, col5, col6 = st.columns([0.5, 2, 3, 2, 1.5, 1])

            with col1:
                # Selection checkbox
                is_selected = persona["id"] in selected_ids
                selected = st.checkbox("", value=is_selected, key=f"select_persona_{i}")

                if selected != is_selected:
                    new_selected = selected_ids.copy()
                    if selected:
                        new_selected.append(persona["id"])
                    else:
                        new_selected.remove(persona["id"])
                    self.list_state.set_selection(
                        {"selected_personas": new_selected, "select_all": False}
                    )
                    st.rerun()

            with col2:
                # Persona name (clickable)
                if on_persona_click:
                    if st.button(
                        persona["name"],
                        key=f"persona_name_{i}",
                        help="Click to view details",
                    ):
                        on_persona_click(persona)
                        action_taken = "persona_clicked"
                else:
                    st.markdown(f"**{persona['name']}**")

            with col3:
                # Description (truncated)
                description = persona.get("description", "")
                if len(description) > 100:
                    description = description[:100] + "..."
                st.markdown(description or "_No description_")

            with col4:
                # ERPNext roles (show first few)
                roles = persona.get("erpnext_roles_list", [])
                if roles:
                    roles_text = ", ".join(roles[:2])
                    if len(roles) > 2:
                        roles_text += f" (+{len(roles)-2} more)"
                    st.markdown(f"`{roles_text}`")
                else:
                    st.markdown("_No roles_")

            with col5:
                # Status indicator
                is_active = persona.get("is_active", False)
                if is_active:
                    st.success("✅ Active")
                else:
                    st.warning("⚠️ Inactive")

            with col6:
                # Action buttons
                action_col1, action_col2 = st.columns(2)

                with action_col1:
                    if st.button("✏️", key=f"edit_persona_{i}", help="Edit persona"):
                        if on_persona_edit:
                            on_persona_edit(persona)
                            action_taken = "persona_edit"

                with action_col2:
                    if st.button(
                        "🗑️", key=f"delete_persona_{i}", help="Delete persona"
                    ):
                        if on_persona_delete:
                            on_persona_delete(persona)
                            action_taken = "persona_delete"

        return action_taken

    def _render_pagination(self) -> Optional[str]:
        """Render pagination controls.

        Returns:
            Action taken if any
        """
        list_data = self.list_state.get_list_data()
        total = list_data.get("total", 0)
        offset = list_data.get("offset", 0)
        limit = list_data.get("limit", 50)

        if total <= limit:
            return None  # No pagination needed

        st.markdown("---")

        # Pagination info and controls
        current_page = (offset // limit) + 1
        total_pages = (total + limit - 1) // limit
        start_item = offset + 1
        end_item = min(offset + limit, total)

        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            st.markdown(
                f"Page {current_page} of {total_pages} • Items {start_item}-{end_item} of {total}"
            )

        with col2:
            if st.button("⬅️ Previous", disabled=(current_page <= 1), key="prev_page"):
                new_offset = max(0, offset - limit)
                list_data["offset"] = new_offset
                self.list_state.set_list_data(list_data)
                return "page_changed"

        with col3:
            if st.button(
                "➡️ Next", disabled=(current_page >= total_pages), key="next_page"
            ):
                new_offset = offset + limit
                list_data["offset"] = new_offset
                self.list_state.set_list_data(list_data)
                return "page_changed"

        with col4:
            # Page size selector
            page_sizes = [25, 50, 100]
            current_size_index = page_sizes.index(limit) if limit in page_sizes else 1

            new_limit = st.selectbox(
                "Per page",
                options=page_sizes,
                index=current_size_index,
                key="page_size_select",
            )

            if new_limit != limit:
                list_data["limit"] = new_limit
                list_data["offset"] = 0  # Reset to first page
                self.list_state.set_list_data(list_data)
                return "page_size_changed"

        return None

    def _get_available_roles(self) -> list[str]:
        """Get list of available ERPNext roles for filtering."""
        # In production, this would be fetched from the backend
        return [
            "Administrator",
            "System Manager",
            "Sales Manager",
            "Sales User",
            "Purchase Manager",
            "Purchase User",
            "Stock Manager",
            "Stock User",
            "Item Manager",
            "Accounts Manager",
            "Accounts User",
            "HR Manager",
            "HR User",
            "Customer",
            "Supplier",
        ]

    def load_personas(self, force_refresh: bool = False) -> bool:
        """Load personas from API based on current filters and pagination.

        Args:
            force_refresh: Whether to force reload even if data exists

        Returns:
            True if load was successful, False otherwise
        """
        try:
            list_data = self.list_state.get_list_data()
            filters = self.list_state.get_filters()

            # Skip loading if data exists and not forcing refresh
            if (
                not force_refresh
                and list_data.get("personas")
                and list_data.get("last_updated")
            ):
                return True

            # Mark as loading
            list_data["loading"] = True
            self.list_state.set_list_data(list_data)

            # Build API parameters
            params = {
                "limit": list_data.get("limit", 50),
                "offset": list_data.get("offset", 0),
            }

            if filters.get("search"):
                params["search"] = filters["search"]
            if filters.get("is_active") is not None:
                params["is_active"] = filters["is_active"]
            if filters.get("erpnext_role"):
                params["erpnext_role"] = filters["erpnext_role"]

            # Call API
            result = self.api_client.list_personas(params)

            # Update list data
            list_data.update(
                {
                    "personas": result.get("personas", []),
                    "total": result.get("total", 0),
                    "has_more": result.get("has_more", False),
                    "loading": False,
                    "last_updated": datetime.now(),
                }
            )

            self.list_state.set_list_data(list_data)
            return True

        except Exception as e:
            logger.error(f"Error loading personas: {e}")
            list_data["loading"] = False
            self.list_state.set_list_data(list_data)
            st.error(f"Failed to load personas: {str(e)}")
            return False


def render_persona_list(
    api_client: APIClient, container: Optional[DeltaGenerator] = None, **kwargs
) -> tuple[Optional[str], Optional[dict[str, Any]]]:
    """Convenience function to render persona list.

    Args:
        api_client: API client instance
        container: Optional Streamlit container
        **kwargs: Additional arguments for render_persona_list

    Returns:
        Tuple of (action_taken, selected_persona or None)
    """
    list_component = PersonaListComponent(api_client)

    # Load personas if needed
    list_component.load_personas()

    action_taken = list_component.render_persona_list(container, **kwargs)

    # Return selected persona info if needed
    selection = list_component.list_state.get_selection()
    selected_ids = selection.get("selected_personas", [])

    selected_persona = None
    if len(selected_ids) == 1:
        # Return single selected persona
        list_data = list_component.list_state.get_list_data()
        personas = list_data.get("personas", [])
        for persona in personas:
            if persona["id"] == selected_ids[0]:
                selected_persona = persona
                break

    return action_taken, selected_persona
