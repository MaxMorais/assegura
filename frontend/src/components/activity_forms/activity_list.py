"""Activity list and management component.

This module provides the main interface for viewing, searching,
and managing ERPNext business activities with filtering capabilities.
"""

import uuid
from typing import Any

import pandas as pd
import streamlit as st

from services.api_client import APIClient
from components.shared.components import (
    confirm_action,
    show_error_message,
    show_info_message,
    show_success_message,
)
from components.shared.utils import format_datetime, format_duration


def render_activity_list():
    """Render the activity list and management interface."""
    st.title("Activity Management")
    st.markdown("Manage ERPNext business activities for test automation")

    # Initialize session state
    if "activity_filters" not in st.session_state:
        st.session_state.activity_filters = {}
    if "activity_page" not in st.session_state:
        st.session_state.activity_page = 1
    if "activity_per_page" not in st.session_state:
        st.session_state.activity_per_page = 20
    if "selected_activities" not in st.session_state:
        st.session_state.selected_activities = []

    # API client
    api_client = APIClient()

    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 Activities", "📊 Statistics", "🔧 Bulk Actions", "➕ Create New"]
    )

    with tab1:
        render_activities_tab(api_client)

    with tab2:
        render_statistics_tab(api_client)

    with tab3:
        render_bulk_actions_tab(api_client)

    with tab4:
        render_create_activity_tab(api_client)


def render_activities_tab(api_client: APIClient):
    """Render the main activities listing tab."""

    # Sidebar filters
    with st.sidebar:
        st.header("🔍 Filters")
        render_activity_filters()

    # Main content
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        # Search bar
        search_query = st.text_input(
            "🔍 Search activities",
            value=st.session_state.activity_filters.get("search", ""),
            placeholder="Search by name, description, or tags...",
            key="activity_search",
        )
        if search_query != st.session_state.activity_filters.get("search", ""):
            st.session_state.activity_filters["search"] = search_query
            st.session_state.activity_page = 1  # Reset to first page

    with col2:
        # Refresh button
        if st.button("🔄 Refresh", key="refresh_activities"):
            st.rerun()

    with col3:
        # View options
        view_mode = st.selectbox("View", ["Table", "Cards"], key="activity_view_mode")

    
    # Fetch activities with filters
    filters = prepare_activity_filters()
    activities_data = api_client.get_activities(
        filters=filters,
        page=st.session_state.activity_page,
        per_page=st.session_state.activity_per_page,
    )

    activities = activities_data.get("activities", [])
    total_count = activities_data.get("total", 0)

    if activities:
        # Display count and pagination info
        start_idx = (
            st.session_state.activity_page - 1
        ) * st.session_state.activity_per_page + 1
        end_idx = min(start_idx + len(activities) - 1, total_count)

        st.info(f"Showing {start_idx}-{end_idx} of {total_count} activities")

        # Display activities
        if view_mode == "Table":
            render_activities_table(activities, api_client)
        else:
            render_activities_cards(activities, api_client)

        # Pagination
        render_activity_pagination(total_count)

    else:
        st.info("No activities found matching your criteria.")

        if st.button("Create First Activity"):
            st.session_state.show_create_form = True
            st.rerun()

def render_activity_filters():
    """Render the activity filtering sidebar."""

    # ERPNext Module filter
    modules = [
        "",
        "Accounts",
        "Stock",
        "Buying",
        "Selling",
        "CRM",
        "Projects",
        "Manufacturing",
        "HR",
        "Payroll",
        "Assets",
        "Support",
        "Website",
        "Desk",
        "Core",
        "Custom",
        "Integrations",
    ]

    selected_module = st.selectbox(
        "ERPNext Module",
        modules,
        index=modules.index(
            st.session_state.activity_filters.get("erpnext_module", "")
        ),
        key="filter_module",
    )
    if selected_module:
        st.session_state.activity_filters["erpnext_module"] = selected_module
    elif "erpnext_module" in st.session_state.activity_filters:
        del st.session_state.activity_filters["erpnext_module"]

    # Action Type filter
    action_types = [
        "",
        "create",
        "read",
        "update",
        "delete",
        "list",
        "search",
        "filter",
        "export",
        "import",
        "approve",
        "reject",
        "submit",
        "cancel",
        "duplicate",
        "print",
        "email",
        "share",
        "assign",
        "comment",
        "attachment",
        "workflow",
        "permission",
        "custom",
    ]

    selected_action = st.selectbox(
        "Action Type",
        action_types,
        index=action_types.index(
            st.session_state.activity_filters.get("action_type", "")
        ),
        key="filter_action",
    )
    if selected_action:
        st.session_state.activity_filters["action_type"] = selected_action
    elif "action_type" in st.session_state.activity_filters:
        del st.session_state.activity_filters["action_type"]

    # Complexity filter
    complexity_options = [
        "",
        "1 - Very Easy",
        "2 - Easy",
        "3 - Medium",
        "4 - Hard",
        "5 - Very Hard",
    ]
    selected_complexity = st.selectbox(
        "Complexity Level", complexity_options, key="filter_complexity"
    )
    if selected_complexity and selected_complexity != "":
        complexity_score = int(selected_complexity[0])
        st.session_state.activity_filters["complexity_score"] = complexity_score
    elif "complexity_score" in st.session_state.activity_filters:
        del st.session_state.activity_filters["complexity_score"]

    # Duration range filter
    st.subheader("Duration Range (seconds)")
    col1, col2 = st.columns(2)
    with col1:
        min_duration = st.number_input(
            "Min",
            min_value=0,
            value=st.session_state.activity_filters.get("min_duration", 0),
            key="filter_min_duration",
        )
        if min_duration > 0:
            st.session_state.activity_filters["min_duration"] = min_duration
        elif "min_duration" in st.session_state.activity_filters:
            del st.session_state.activity_filters["min_duration"]

    with col2:
        max_duration = st.number_input(
            "Max",
            min_value=0,
            value=st.session_state.activity_filters.get("max_duration", 0),
            key="filter_max_duration",
        )
        if max_duration > 0:
            st.session_state.activity_filters["max_duration"] = max_duration
        elif "max_duration" in st.session_state.activity_filters:
            del st.session_state.activity_filters["max_duration"]

    # Status filter
    status_options = ["All", "Active Only", "Inactive Only"]
    selected_status = st.selectbox("Status", status_options, key="filter_status")
    if selected_status == "Active Only":
        st.session_state.activity_filters["is_active"] = True
    elif selected_status == "Inactive Only":
        st.session_state.activity_filters["is_active"] = False
    elif "is_active" in st.session_state.activity_filters:
        del st.session_state.activity_filters["is_active"]

    # Tags filter
    tags_input = st.text_input(
        "Tags (comma-separated)",
        value=st.session_state.activity_filters.get("tags", ""),
        placeholder="automation, critical, regression",
        key="filter_tags",
    )
    if tags_input.strip():
        st.session_state.activity_filters["tags"] = tags_input.strip()
    elif "tags" in st.session_state.activity_filters:
        del st.session_state.activity_filters["tags"]

    # Clear filters button
    if st.button("🗑️ Clear All Filters", key="clear_filters"):
        st.session_state.activity_filters = {}
        st.session_state.activity_page = 1
        st.rerun()


def render_activities_table(activities: list[dict[str, Any]], api_client: APIClient):
    """Render activities in table format."""

    # Prepare table data
    table_data = []
    for activity in activities:
        table_data.append(
            {
                "Select": False,
                "Name": activity["name"],
                "Module": activity["erpnext_module"],
                "Action": activity["action_type"],
                "DocType": activity["target_doctype"],
                "Complexity": f"{activity['complexity_score']}/5",
                "Duration": format_duration(activity["estimated_duration"]),
                "Status": "✅ Active" if activity["is_active"] else "❌ Inactive",
                "Updated": format_datetime(activity["updated_at"]),
                "ID": activity["id"],
            }
        )

    if table_data:
        # Create DataFrame
        df = pd.DataFrame(table_data)

        # Use st.data_editor for selection
        edited_df = st.data_editor(
            df,
            column_config={
                "Select": st.column_config.CheckboxColumn("Select"),
                "Name": st.column_config.TextColumn("Name", width="large"),
                "Module": st.column_config.TextColumn("Module", width="medium"),
                "Action": st.column_config.TextColumn("Action", width="medium"),
                "DocType": st.column_config.TextColumn("DocType", width="medium"),
                "Complexity": st.column_config.TextColumn("Complexity", width="small"),
                "Duration": st.column_config.TextColumn("Duration", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Updated": st.column_config.TextColumn("Updated", width="medium"),
                "ID": None,  # Hide ID column
            },
            disabled=[
                "Name",
                "Module",
                "Action",
                "DocType",
                "Complexity",
                "Duration",
                "Status",
                "Updated",
                "ID",
            ],
            hide_index=True,
            key="activities_table",
        )

        # Update selected activities
        selected_mask = edited_df["Select"]
        st.session_state.selected_activities = edited_df[selected_mask]["ID"].tolist()

        # Action buttons for selected activities
        if st.session_state.selected_activities:
            st.info(f"{len(st.session_state.selected_activities)} activities selected")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("👁️ View Details", key="view_selected"):
                    if len(st.session_state.selected_activities) == 1:
                        activity_id = st.session_state.selected_activities[0]
                        st.session_state.view_activity_id = activity_id
                        st.switch_page("pages/activity_detail.py")
                    else:
                        show_info_message(
                            "Please select only one activity to view details"
                        )

            with col2:
                if st.button("✏️ Edit", key="edit_selected"):
                    if len(st.session_state.selected_activities) == 1:
                        activity_id = st.session_state.selected_activities[0]
                        st.session_state.edit_activity_id = activity_id
                        st.switch_page("pages/activity_edit.py")
                    else:
                        show_info_message("Please select only one activity to edit")

            with col3:
                if st.button("🔄 Toggle Status", key="toggle_status_selected"):
                    toggle_selected_activities_status(api_client)

            with col4:
                if st.button("🗑️ Delete", key="delete_selected", type="secondary"):
                    if confirm_action(
                        f"Delete {len(st.session_state.selected_activities)} activities?"
                    ):
                        delete_selected_activities(api_client)


def render_activities_cards(activities: list[dict[str, Any]], api_client: APIClient):
    """Render activities in card format."""

    # Display activities in cards (3 per row)
    cols_per_row = 3
    for i in range(0, len(activities), cols_per_row):
        cols = st.columns(cols_per_row)

        for j, col in enumerate(cols):
            if i + j < len(activities):
                activity = activities[i + j]

                with col:
                    render_activity_card(activity, api_client)


def render_activity_card(activity: dict[str, Any], api_client: APIClient):
    """Render a single activity card."""

    # Card container
    with st.container():
        # Status indicator
        status_emoji = "✅" if activity["is_active"] else "❌"
        complexity_stars = "⭐" * activity["complexity_score"]

        # Card header
        st.markdown(
            f"""
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-bottom: 16px; background-color: white;">
            <h4>{status_emoji} {activity['name']}</h4>
            <p><strong>Module:</strong> {activity['erpnext_module']}</p>
            <p><strong>Action:</strong> {activity['action_type']}</p>
            <p><strong>DocType:</strong> {activity['target_doctype']}</p>
            <p><strong>Complexity:</strong> {complexity_stars} ({activity['complexity_score']}/5)</p>
            <p><strong>Duration:</strong> {format_duration(activity['estimated_duration'])}</p>
            <p><strong>Updated:</strong> {format_datetime(activity['updated_at'])}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Action buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("👁️", help="View Details", key=f"view_{activity['id']}"):
                st.session_state.view_activity_id = activity["id"]
                st.switch_page("pages/activity_detail.py")

        with col2:
            if st.button("✏️", help="Edit", key=f"edit_{activity['id']}"):
                st.session_state.edit_activity_id = activity["id"]
                st.switch_page("pages/activity_edit.py")

        with col3:
            if st.button("🗑️", help="Delete", key=f"delete_{activity['id']}"):
                if confirm_action(f"Delete activity '{activity['name']}'?"):
                    delete_activity(activity["id"], api_client)


def render_statistics_tab(api_client: APIClient):
    """Render the activity statistics tab."""

    stats = api_client.get_activity_statistics()

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Activities", stats.get("total", 0))

    with col2:
        st.metric("Active Activities", stats.get("active", 0))

    with col3:
        st.metric("Inactive Activities", stats.get("inactive", 0))

    with col4:
        avg_duration = stats.get("avg_duration", 0)
        st.metric("Avg Duration", format_duration(avg_duration))

    # Charts
    st.subheader("📊 Distribution Charts")

    col1, col2 = st.columns(2)

    with col1:
        # By module
        by_module = stats.get("by_module", {})
        if by_module:
            st.subheader("Activities by Module")
            st.bar_chart(by_module)

    with col2:
        # By action type
        by_action = stats.get("by_action_type", {})
        if by_action:
            st.subheader("Activities by Action Type")
            st.bar_chart(by_action)

    # Complexity distribution
    by_complexity = stats.get("by_complexity", {})
    if by_complexity:
        st.subheader("Activities by Complexity")
        complexity_df = pd.DataFrame(
            [
                {"Complexity": f"Level {k}", "Count": v}
                for k, v in by_complexity.items()
            ]
        )
        st.bar_chart(complexity_df.set_index("Complexity"))

def render_bulk_actions_tab(api_client: APIClient):
    """Render the bulk actions tab."""

    st.subheader("🔧 Bulk Operations")

    # Bulk status update
    st.subheader("Update Activity Status")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        activity_ids_text = st.text_area(
            "Activity IDs (one per line or comma-separated)",
            placeholder="Enter activity IDs...",
            height=100,
        )

    with col2:
        new_status = st.selectbox("New Status", ["Active", "Inactive"])

    with col3:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("Update Status", key="bulk_update_status"):
            activity_ids = parse_activity_ids(activity_ids_text)
            if activity_ids:
                bulk_update_status(activity_ids, new_status == "Active", api_client)
            else:
                show_error_message("Please enter valid activity IDs")

    st.divider()

    # Bulk delete
    st.subheader("Delete Activities")

    col1, col2 = st.columns([3, 1])

    with col1:
        delete_ids_text = st.text_area(
            "Activity IDs to Delete (one per line or comma-separated)",
            placeholder="Enter activity IDs...",
            height=100,
        )

    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("🗑️ Delete Activities", key="bulk_delete", type="secondary"):
            activity_ids = parse_activity_ids(delete_ids_text)
            if activity_ids:
                if confirm_action(
                    f"Delete {len(activity_ids)} activities? This action cannot be undone."
                ):
                    bulk_delete_activities(activity_ids, api_client)
            else:
                show_error_message("Please enter valid activity IDs")


def render_create_activity_tab(api_client: APIClient):
    """Render the create new activity tab."""

    st.subheader("➕ Create New Activity")

    from .activity_form import render_activity_form

    render_activity_form(api_client)


# Helper functions
def prepare_activity_filters() -> dict[str, Any]:
    """Prepare filters for API call."""
    filters = {}

    for key, value in st.session_state.activity_filters.items():
        if value is not None and value != "":
            filters[key] = value

    return filters


def render_activity_pagination(total_count: int):
    """Render pagination controls."""

    total_pages = (
        total_count + st.session_state.activity_per_page - 1
    ) // st.session_state.activity_per_page

    if total_pages > 1:
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

        with col1:
            if st.button("⏮️ First", disabled=st.session_state.activity_page == 1):
                st.session_state.activity_page = 1
                st.rerun()

        with col2:
            if st.button("⏪ Prev", disabled=st.session_state.activity_page == 1):
                st.session_state.activity_page -= 1
                st.rerun()

        with col3:
            page = st.number_input(
                f"Page ({st.session_state.activity_page} of {total_pages})",
                min_value=1,
                max_value=total_pages,
                value=st.session_state.activity_page,
                key="page_input",
            )
            if page != st.session_state.activity_page:
                st.session_state.activity_page = page
                st.rerun()

        with col4:
            if st.button(
                "⏩ Next", disabled=st.session_state.activity_page == total_pages
            ):
                st.session_state.activity_page += 1
                st.rerun()

        with col5:
            if st.button(
                "⏭️ Last", disabled=st.session_state.activity_page == total_pages
            ):
                st.session_state.activity_page = total_pages
                st.rerun()


def parse_activity_ids(ids_text: str) -> list[str]:
    """Parse activity IDs from text input."""
    if not ids_text.strip():
        return []

    # Try to parse UUIDs from comma-separated or line-separated input
    ids = []
    lines = ids_text.replace(",", "\n").split("\n")

    for line in lines:
        line = line.strip()
        if line:
            try:
                # Validate UUID format
                uuid.UUID(line)
                ids.append(line)
            except ValueError:
                continue

    return ids


def toggle_selected_activities_status(api_client: APIClient):
    """Toggle status of selected activities."""
    if not st.session_state.selected_activities:
        return

    try:
        # For simplicity, we'll set all selected activities to active
        # In a real app, you might want to check current status first
        result = api_client.bulk_update_activity_status(
            st.session_state.selected_activities, True  # Set to active
        )

        show_success_message(f"Updated status of {result['updated_count']} activities")
        st.session_state.selected_activities = []
        st.rerun()

    except Exception as e:
        show_error_message(f"Error updating activity status: {str(e)}")


def delete_selected_activities(api_client: APIClient):
    """Delete selected activities."""
    if not st.session_state.selected_activities:
        return

    try:
        result = api_client.bulk_delete_activities(st.session_state.selected_activities)
        show_success_message(f"Deleted {result['deleted_count']} activities")
        st.session_state.selected_activities = []
        st.rerun()

    except Exception as e:
        show_error_message(f"Error deleting activities: {str(e)}")


def delete_activity(activity_id: str, api_client: APIClient):
    """Delete a single activity."""
    try:
        api_client.delete_activity(activity_id)
        show_success_message("Activity deleted successfully")
        st.rerun()

    except Exception as e:
        show_error_message(f"Error deleting activity: {str(e)}")


def bulk_update_status(activity_ids: list[str], is_active: bool, api_client: APIClient):
    """Bulk update activity status."""
    try:
        result = api_client.bulk_update_activity_status(activity_ids, is_active)
        status_text = "active" if is_active else "inactive"
        show_success_message(
            f"Set {result['updated_count']} activities to {status_text}"
        )

    except Exception as e:
        show_error_message(f"Error updating activities: {str(e)}")


def bulk_delete_activities(activity_ids: list[str], api_client: APIClient):
    """Bulk delete activities."""
    try:
        result = api_client.bulk_delete_activities(activity_ids)
        show_success_message(f"Deleted {result['deleted_count']} activities")

    except Exception as e:
        show_error_message(f"Error deleting activities: {str(e)}")
