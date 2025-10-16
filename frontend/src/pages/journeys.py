"""
Journeys Page - Journey Management Interface

Main page for managing test journeys in the ERPNext test automation framework.
Provides comprehensive journey CRUD operations, builder interface, and
journey execution capabilities.
"""

import streamlit as st
from typing import Any, Dict, List, Optional
import uuid

from ..components.journey_builder.journey_builder import render_journey_builder
from ..services.journey_service import JourneyAPIClient
from ..services.activity_service import ActivityAPIClient
from ..services.persona_service import PersonaAPIClient
from ..components.shared.error_handler import handle_api_error
from ..components.shared.loading_spinner import show_loading_spinner


def show_journeys() -> None:
    """Display journeys management interface."""
    st.title("🗺️ Test Journeys")
    
    # Initialize services
    journey_service = JourneyAPIClient()
    activity_service = ActivityAPIClient()
    persona_service = PersonaAPIClient()
    
    # Initialize session state
    if "journeys_page_data" not in st.session_state:
        st.session_state.journeys_page_data = {
            "current_tab": "list",
            "selected_journey": None,
            "editing_journey": None,
            "filter_activity": None,
            "filter_persona": None,
            "search_term": "",
            "journeys_list": [],
            "activities_list": [],
            "personas_list": [],
            "data_loaded": False
        }
    
    # Load initial data
    if not st.session_state.journeys_page_data["data_loaded"]:
        _load_initial_data(journey_service, activity_service, persona_service)
    
    # Tab navigation
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Journey List", "🆕 Create Journey", "✏️ Edit Journey", "📊 Analytics"])
    
    with tab1:
        _render_journey_list(journey_service, activity_service, persona_service)
    
    with tab2:
        _render_create_journey(activity_service, persona_service)
    
    with tab3:
        _render_edit_journey()
    
    with tab4:
        _render_journey_analytics(journey_service)


def _load_initial_data(journey_service: JourneyAPIClient, activity_service: ActivityAPIClient, persona_service: PersonaAPIClient):
    """Load initial data for the page."""
    try:
        with show_loading_spinner("Loading journeys data..."):
            # Load journeys
            journeys_response = journey_service.list_journeys(limit=1000)
            journeys = journeys_response.get("items", [])
            
            # Load activities
            activities_response = activity_service.list_activities(limit=1000)
            activities = activities_response.get("items", [])
            
            # Load personas
            personas_response = persona_service.list_personas(limit=1000)
            personas = personas_response.get("items", [])
            
            st.session_state.journeys_page_data.update({
                "journeys_list": journeys,
                "activities_list": activities,
                "personas_list": personas,
                "data_loaded": True
            })
            
    except Exception as e:
        handle_api_error(e, "Failed to load initial data")
        st.session_state.journeys_page_data["data_loaded"] = True


def _render_journey_list(journey_service: JourneyAPIClient, activity_service: ActivityAPIClient, persona_service: PersonaAPIClient):
    """Render the journey list tab."""
    st.subheader("Journey List")
    
    # Filters and search
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_term = st.text_input(
            "🔍 Search Journeys",
            value=st.session_state.journeys_page_data["search_term"],
            placeholder="Search by name or description"
        )
    
    with col2:
        activities = st.session_state.journeys_page_data["activities_list"]
        activity_options = ["All Activities"] + [f"{a['name']} ({a['id'][:8]})" for a in activities]
        selected_activity = st.selectbox("Filter by Activity", activity_options)
    
    with col3:
        personas = st.session_state.journeys_page_data["personas_list"]
        persona_options = ["All Personas"] + [f"{p['name']} ({p['id'][:8]})" for p in personas]
        selected_persona = st.selectbox("Filter by Persona", persona_options)
    
    with col4:
        status_options = ["All Statuses", "not_started", "ready", "running", "completed", "failed", "cancelled"]
        selected_status = st.selectbox("Filter by Status", status_options)
    
    # Apply filters
    filtered_journeys = _apply_journey_filters(
        st.session_state.journeys_page_data["journeys_list"],
        search_term,
        selected_activity,
        selected_persona,
        selected_status
    )
    
    # Journey list display
    if not filtered_journeys:
        st.info("No journeys found matching the current filters.")
        return
    
    st.write(f"**Found {len(filtered_journeys)} journeys**")
    
    # Journey cards
    for journey in filtered_journeys:
        _render_journey_card(journey, journey_service)


def _render_journey_card(journey: Dict[str, Any], journey_service: JourneyAPIClient):
    """Render a journey card in the list."""
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
        
        with col1:
            st.write(f"**{journey.get('name', 'Unnamed Journey')}**")
            st.caption(journey.get('description', 'No description'))
            
            # Journey metadata
            step_count = journey.get('step_count', 0)
            complexity = journey.get('complexity_level', 'medium')
            st.caption(f"Steps: {step_count} | Complexity: {complexity}")
        
        with col2:
            # Status badge
            status = journey.get('execution_status', 'not_started')
            status_colors = {
                'not_started': 'secondary',
                'ready': 'primary',
                'running': 'warning',
                'completed': 'success',
                'failed': 'error',
                'cancelled': 'secondary'
            }
            st.badge(status.upper(), type=status_colors.get(status, 'secondary'))
        
        with col3:
            # Journey properties
            is_active = journey.get('is_active', True)
            is_complete = journey.get('is_complete_scenario', False)
            
            if is_active:
                st.success("✅ Active")
            else:
                st.warning("⏸️ Inactive")
            
            if is_complete:
                st.info("🎯 Complete BDD")
        
        with col4:
            # Action buttons
            col_view, col_edit, col_copy, col_delete = st.columns(4)
            
            with col_view:
                if st.button("👁️", key=f"view_{journey['id']}", help="View journey"):
                    _view_journey(journey)
            
            with col_edit:
                if st.button("✏️", key=f"edit_{journey['id']}", help="Edit journey"):
                    _edit_journey(journey)
            
            with col_copy:
                if st.button("📋", key=f"copy_{journey['id']}", help="Copy journey"):
                    _copy_journey(journey)
            
            with col_delete:
                if st.button("�️", key=f"delete_{journey['id']}", help="Delete journey"):
                    _delete_journey(journey, journey_service)
        
        st.divider()


def _render_create_journey(activity_service: ActivityAPIClient, persona_service: PersonaAPIClient):
    """Render the create journey tab."""
    st.subheader("Create New Journey")
    
    # Activity and persona selection
    col1, col2 = st.columns(2)
    
    with col1:
        activities = st.session_state.journeys_page_data["activities_list"]
        if not activities:
            st.error("No activities available. Please create an activity first.")
            return
        
        activity_options = [f"{a['name']} ({a['id'][:8]})" for a in activities]
        selected_activity_idx = st.selectbox(
            "Select Activity*",
            range(len(activity_options)),
            format_func=lambda x: activity_options[x]
        )
        
        selected_activity = activities[selected_activity_idx]
    
    with col2:
        personas = st.session_state.journeys_page_data["personas_list"]
        if not personas:
            st.error("No personas available. Please create a persona first.")
            return
        
        persona_options = [f"{p['name']} ({p['id'][:8]})" for p in personas]
        selected_persona_idx = st.selectbox(
            "Select Persona*",
            range(len(persona_options)),
            format_func=lambda x: persona_options[x]
        )
        
        selected_persona = personas[selected_persona_idx]
    
    # Journey builder
    st.write("### Journey Builder")
    render_journey_builder(
        journey_id=None,
        activity_id=selected_activity['id'],
        persona_id=selected_persona['id']
    )


def _render_edit_journey():
    """Render the edit journey tab."""
    st.subheader("Edit Journey")
    
    editing_journey = st.session_state.journeys_page_data.get("editing_journey")
    
    if not editing_journey:
        st.info("Select a journey from the list to edit it.")
        return
    
    # Journey builder for editing
    render_journey_builder(
        journey_id=editing_journey['id'],
        activity_id=editing_journey['activity_id'],
        persona_id=editing_journey['persona_id']
    )


def _render_journey_analytics(journey_service: JourneyAPIClient):
    """Render the journey analytics tab."""
    st.subheader("Journey Analytics")
    
    try:
        with show_loading_spinner("Loading analytics..."):
            stats = journey_service.get_journey_statistics()
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Journeys", stats.get("total_journeys", 0))
        
        with col2:
            st.metric("Active Journeys", stats.get("active_journeys", 0))
        
        with col3:
            st.metric("Ready to Execute", stats.get("ready_journeys", 0))
        
        with col4:
            avg_steps = stats.get("avg_steps_per_journey", 0)
            st.metric("Avg Steps/Journey", f"{avg_steps:.1f}")
        
        # Complexity distribution
        complexity_dist = stats.get("complexity_distribution", {})
        if complexity_dist:
            st.subheader("Complexity Distribution")
            st.bar_chart(complexity_dist)
        
        # Most used modules
        most_used_modules = stats.get("most_used_modules", [])
        if most_used_modules:
            st.subheader("Most Used ERPNext Modules")
            for module, count in most_used_modules[:10]:
                st.write(f"• {module}: {count} journeys")
        
        # Recent execution activity
        recent_executions = stats.get("recent_executions", 0)
        st.metric("Recent Executions (7 days)", recent_executions)
        
    except Exception as e:
        handle_api_error(e, "Failed to load analytics")


def _apply_journey_filters(journeys: List[Dict[str, Any]], search_term: str, 
                          activity_filter: str, persona_filter: str, status_filter: str) -> List[Dict[str, Any]]:
    """Apply filters to the journey list."""
    filtered = journeys
    
    # Search filter
    if search_term:
        search_lower = search_term.lower()
        filtered = [
            j for j in filtered
            if (search_lower in j.get('name', '').lower() or
                search_lower in j.get('description', '').lower())
        ]
    
    # Activity filter
    if activity_filter != "All Activities":
        activity_id = activity_filter.split('(')[-1].rstrip(')')
        filtered = [j for j in filtered if j.get('activity_id', '').startswith(activity_id)]
    
    # Persona filter
    if persona_filter != "All Personas":
        persona_id = persona_filter.split('(')[-1].rstrip(')')
        filtered = [j for j in filtered if j.get('persona_id', '').startswith(persona_id)]
    
    # Status filter
    if status_filter != "All Statuses":
        filtered = [j for j in filtered if j.get('execution_status') == status_filter]
    
    return filtered


def _view_journey(journey: Dict[str, Any]):
    """View journey details."""
    st.session_state.journeys_page_data["selected_journey"] = journey
    
    with st.expander(f"Journey Details: {journey.get('name', 'Unnamed')}", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Basic Information**")
            st.write(f"Name: {journey.get('name', 'N/A')}")
            st.write(f"Description: {journey.get('description', 'N/A')}")
            st.write(f"Status: {journey.get('execution_status', 'N/A')}")
            st.write(f"Complexity: {journey.get('complexity_level', 'N/A')}")
            st.write(f"Steps: {journey.get('step_count', 0)}")
        
        with col2:
            st.write("**Configuration**")
            st.write(f"Active: {'Yes' if journey.get('is_active') else 'No'}")
            st.write(f"Complete BDD: {'Yes' if journey.get('is_complete_scenario') else 'No'}")
            duration = journey.get('estimated_duration_minutes')
            st.write(f"Duration: {duration} min" if duration else "Duration: Not set")
            st.write(f"Created: {journey.get('created_at', 'N/A')}")
            st.write(f"Updated: {journey.get('updated_at', 'N/A')}")


def _edit_journey(journey: Dict[str, Any]):
    """Set journey for editing."""
    st.session_state.journeys_page_data["editing_journey"] = journey
    st.session_state.journeys_page_data["current_tab"] = "edit"
    st.rerun()


def _copy_journey(journey: Dict[str, Any]):
    """Copy an existing journey."""
    st.info(f"📋 Copy functionality for '{journey.get('name')}' coming soon...")


def _delete_journey(journey: Dict[str, Any], journey_service: JourneyAPIClient):
    """Delete a journey."""
    journey_name = journey.get('name', 'Unknown Journey')
    
    if st.button(f"Confirm Delete '{journey_name}'", key=f"confirm_delete_{journey['id']}"):
        try:
            with show_loading_spinner(f"Deleting journey '{journey_name}'..."):
                journey_service.delete_journey(journey['id'])
            
            # Remove from local list
            journeys_list = st.session_state.journeys_page_data["journeys_list"]
            st.session_state.journeys_page_data["journeys_list"] = [
                j for j in journeys_list if j['id'] != journey['id']
            ]
            
            st.success(f"Journey '{journey_name}' deleted successfully")
            st.rerun()
            
        except Exception as e:
            handle_api_error(e, f"Failed to delete journey '{journey_name}'")
