"""
Action Selector Component

Component for selecting actions from the action library when building journeys.
Provides filtering, search, and categorization capabilities to help users
find and select appropriate actions for their test scenarios.
"""

import streamlit as st
from typing import Any, Dict, List, Optional

from ...services.action_service import ActionAPIClient
from ..shared.error_handler import handle_api_error
from ..shared.loading_spinner import show_loading_spinner


class ActionSelector:
    """Action selector component for choosing actions from the library."""

    def __init__(self):
        self.action_service = ActionAPIClient()
        
        # Initialize session state
        if "action_selector_data" not in st.session_state:
            st.session_state.action_selector_data = {
                "available_actions": [],
                "filtered_actions": [],
                "search_term": "",
                "selected_type": "all",
                "selected_module": "all",
                "selected_implementation": "all",
                "selected_action": None,
                "actions_loaded": False
            }

    def render(self) -> Optional[Dict[str, Any]]:
        """
        Render the action selector interface.
        
        Returns:
            Selected action data or None if no action selected
        """
        # Load actions if not already loaded
        if not st.session_state.action_selector_data["actions_loaded"]:
            self._load_actions()
        
        # Search and filter interface
        self._render_search_filters()
        
        # Action list
        self._render_action_list()
        
        # Action details
        selected_action = self._render_action_details()
        
        return selected_action

    def _load_actions(self):
        """Load available actions from the action library."""
        try:
            with show_loading_spinner("Loading actions..."):
                actions = self.action_service.list_actions(limit=1000)
                
                st.session_state.action_selector_data.update({
                    "available_actions": actions.get("items", []),
                    "filtered_actions": actions.get("items", []),
                    "actions_loaded": True
                })
                
        except Exception as e:
            handle_api_error(e, "Failed to load actions")
            st.session_state.action_selector_data["actions_loaded"] = True

    def _render_search_filters(self):
        """Render search and filter interface."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            search_term = st.text_input(
                "🔍 Search Actions",
                value=st.session_state.action_selector_data["search_term"],
                placeholder="Search by name or description"
            )
        
        with col2:
            action_types = ["all", "given", "when", "then"]
            selected_type = st.selectbox(
                "Action Type",
                action_types,
                index=action_types.index(st.session_state.action_selector_data["selected_type"])
            )
        
        with col3:
            # Get unique modules from actions
            actions = st.session_state.action_selector_data["available_actions"]
            modules = ["all"] + list(set(action.get("erpnext_module", "unknown") for action in actions))
            
            selected_module = st.selectbox(
                "ERPNext Module",
                modules,
                index=modules.index(st.session_state.action_selector_data["selected_module"]) if st.session_state.action_selector_data["selected_module"] in modules else 0
            )
        
        with col4:
            implementation_types = ["all", "ui_interaction", "api_call", "verification", "data_setup", "cleanup"]
            selected_implementation = st.selectbox(
                "Implementation",
                implementation_types,
                index=implementation_types.index(st.session_state.action_selector_data["selected_implementation"])
            )
        
        # Update filters if changed
        if (search_term != st.session_state.action_selector_data["search_term"] or
            selected_type != st.session_state.action_selector_data["selected_type"] or
            selected_module != st.session_state.action_selector_data["selected_module"] or
            selected_implementation != st.session_state.action_selector_data["selected_implementation"]):
            
            st.session_state.action_selector_data.update({
                "search_term": search_term,
                "selected_type": selected_type,
                "selected_module": selected_module,
                "selected_implementation": selected_implementation
            })
            
            self._apply_filters()

    def _apply_filters(self):
        """Apply current filters to the action list."""
        actions = st.session_state.action_selector_data["available_actions"]
        search_term = st.session_state.action_selector_data["search_term"].lower()
        selected_type = st.session_state.action_selector_data["selected_type"]
        selected_module = st.session_state.action_selector_data["selected_module"]
        selected_implementation = st.session_state.action_selector_data["selected_implementation"]
        
        filtered_actions = actions
        
        # Apply search filter
        if search_term:
            filtered_actions = [
                action for action in filtered_actions
                if (search_term in action.get("name", "").lower() or
                    search_term in action.get("description", "").lower())
            ]
        
        # Apply type filter
        if selected_type != "all":
            filtered_actions = [
                action for action in filtered_actions
                if action.get("action_type", "").lower() == selected_type
            ]
        
        # Apply module filter
        if selected_module != "all":
            filtered_actions = [
                action for action in filtered_actions
                if action.get("erpnext_module", "") == selected_module
            ]
        
        # Apply implementation filter
        if selected_implementation != "all":
            filtered_actions = [
                action for action in filtered_actions
                if action.get("implementation_type", "").lower() == selected_implementation
            ]
        
        st.session_state.action_selector_data["filtered_actions"] = filtered_actions

    def _render_action_list(self):
        """Render the filtered action list."""
        filtered_actions = st.session_state.action_selector_data["filtered_actions"]
        
        st.write(f"**Available Actions ({len(filtered_actions)})**")
        
        if not filtered_actions:
            st.info("No actions match the current filters.")
            return
        
        # Create action selection interface
        for i, action in enumerate(filtered_actions):
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    # Action name and description
                    st.write(f"**{action.get('name', 'Unnamed Action')}**")
                    st.write(action.get('description', 'No description available'))
                
                with col2:
                    # Action metadata
                    action_type = action.get('action_type', 'unknown')
                    st.badge(action_type.upper(), type="secondary")
                    
                    module = action.get('erpnext_module', 'unknown')
                    st.caption(f"Module: {module}")
                
                with col3:
                    # Select button
                    if st.button(f"Select", key=f"select_action_{i}"):
                        st.session_state.action_selector_data["selected_action"] = action
                        return action
                
                st.divider()

    def _render_action_details(self) -> Optional[Dict[str, Any]]:
        """Render details for the selected action."""
        selected_action = st.session_state.action_selector_data.get("selected_action")
        
        if not selected_action:
            return None
        
        st.subheader("Selected Action Details")
        
        with st.container():
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Name:** {selected_action.get('name', 'N/A')}")
                st.write(f"**Type:** {selected_action.get('action_type', 'N/A').upper()}")
                st.write(f"**Module:** {selected_action.get('erpnext_module', 'N/A')}")
                st.write(f"**Implementation:** {selected_action.get('implementation_type', 'N/A')}")
            
            with col2:
                st.write(f"**System Action:** {'Yes' if selected_action.get('is_system_action', False) else 'No'}")
                st.write(f"**Created:** {selected_action.get('created_at', 'N/A')}")
                st.write(f"**Updated:** {selected_action.get('updated_at', 'N/A')}")
            
            # Description
            st.write("**Description:**")
            st.write(selected_action.get('description', 'No description available'))
            
            # Parameters
            parameters = selected_action.get('parameters', [])
            if parameters:
                st.write("**Parameters:**")
                for param in parameters:
                    param_name = param.get('name', 'Unknown')
                    param_type = param.get('param_type', 'string')
                    required = "Required" if param.get('required', True) else "Optional"
                    param_desc = param.get('description', 'No description')
                    
                    st.write(f"- **{param_name}** ({param_type}) - {required}")
                    st.caption(f"  {param_desc}")
            
            # Expected outputs
            outputs = selected_action.get('outputs', [])
            if outputs:
                st.write("**Expected Outputs:**")
                for output in outputs:
                    output_name = output.get('name', 'Unknown')
                    output_type = output.get('output_type', 'boolean')
                    output_desc = output.get('description', 'No description')
                    
                    st.write(f"- **{output_name}** ({output_type})")
                    st.caption(f"  {output_desc}")
            
            # Action buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Confirm Selection", type="primary"):
                    return selected_action
            
            with col2:
                if st.button("❌ Cancel Selection"):
                    st.session_state.action_selector_data["selected_action"] = None
                    st.rerun()
        
        return None


def render_action_selector() -> Optional[Dict[str, Any]]:
    """
    Render the action selector component.
    
    Returns:
        Selected action data or None if no action selected
    """
    selector = ActionSelector()
    return selector.render()