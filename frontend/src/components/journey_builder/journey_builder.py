"""
Journey Builder Component

Main component for building and editing test journeys in the ERPNext test
automation framework. Provides a drag-and-drop interface for creating
step-by-step test scenarios with action selection and parameter configuration.
"""

import streamlit as st
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from ...services.journey_service import JourneyAPIClient
from ...services.action_service import ActionAPIClient
from .action_selector import ActionSelector
from .step_sequence import StepSequence
from ..shared.error_handler import handle_api_error
from ..shared.loading_spinner import show_loading_spinner


class JourneyBuilder:
    """Journey builder component for creating and editing journeys."""

    def __init__(self):
        self.journey_service = JourneyAPIClient()
        self.action_service = ActionAPIClient()
        
        # Initialize session state
        if "journey_builder_data" not in st.session_state:
            st.session_state.journey_builder_data = {
                "current_journey": None,
                "journey_steps": [],
                "selected_action": None,
                "validation_results": None,
                "is_editing": False,
                "unsaved_changes": False
            }

    def render(self, journey_id: Optional[str] = None, activity_id: Optional[str] = None, persona_id: Optional[str] = None):
        """
        Render the journey builder interface.
        
        Args:
            journey_id: Optional existing journey ID to edit
            activity_id: Required activity ID for new journeys
            persona_id: Required persona ID for new journeys
        """
        st.title("🗺️ Journey Builder")
        
        # Load existing journey if editing
        if journey_id and not st.session_state.journey_builder_data["current_journey"]:
            self._load_journey(journey_id)
        
        # Main builder interface
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self._render_journey_details(activity_id, persona_id)
            self._render_step_builder()
            
        with col2:
            self._render_journey_properties()
            self._render_validation_panel()
            
        # Bottom action bar
        self._render_action_bar(journey_id, activity_id, persona_id)

    def _render_journey_details(self, activity_id: Optional[str], persona_id: Optional[str]):
        """Render journey basic details form."""
        st.subheader("Journey Details")
        
        with st.form("journey_details"):
            journey_data = st.session_state.journey_builder_data["current_journey"] or {}
            
            name = st.text_input(
                "Journey Name*",
                value=journey_data.get("name", ""),
                placeholder="Enter a descriptive name for this journey"
            )
            
            description = st.text_area(
                "Description*",
                value=journey_data.get("description", ""),
                placeholder="Describe what this journey accomplishes",
                height=100
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                complexity_level = st.selectbox(
                    "Complexity Level",
                    ["simple", "medium", "complex", "advanced"],
                    index=["simple", "medium", "complex", "advanced"].index(
                        journey_data.get("complexity_level", "medium")
                    )
                )
                
                estimated_duration = st.number_input(
                    "Estimated Duration (minutes)",
                    min_value=1,
                    max_value=1440,
                    value=journey_data.get("estimated_duration_minutes", 30)
                )
            
            with col2:
                is_active = st.checkbox(
                    "Active Journey",
                    value=journey_data.get("is_active", True)
                )
                
                execution_status = st.selectbox(
                    "Execution Status",
                    ["not_started", "ready", "running", "completed", "failed", "cancelled"],
                    index=0
                )
            
            # Prerequisites
            st.write("Prerequisites")
            prerequisites = st.text_area(
                "Prerequisites (one per line)",
                value="\\n".join(journey_data.get("prerequisites", [])),
                placeholder="List any prerequisites or setup requirements",
                height=80
            )
            
            # Expected outcomes  
            st.write("Expected Outcomes")
            expected_outcomes = st.text_area(
                "Expected Outcomes (one per line)",
                value="\\n".join(journey_data.get("expected_outcomes", [])),
                placeholder="List the expected results or outcomes",
                height=80
            )
            
            # Update journey data when form is submitted
            if st.form_submit_button("Update Journey Details"):
                self._update_journey_details({
                    "name": name,
                    "description": description,
                    "complexity_level": complexity_level,
                    "estimated_duration_minutes": estimated_duration,
                    "is_active": is_active,
                    "execution_status": execution_status,
                    "prerequisites": [p.strip() for p in prerequisites.split("\\n") if p.strip()],
                    "expected_outcomes": [o.strip() for o in expected_outcomes.split("\\n") if o.strip()],
                    "activity_id": activity_id,
                    "persona_id": persona_id
                })

    def _render_step_builder(self):
        """Render the step builder interface."""
        st.subheader("Journey Steps")
        
        # Action selector for adding new steps
        if st.button("➕ Add Step"):
            st.session_state.journey_builder_data["show_action_selector"] = True
        
        # Show action selector modal
        if st.session_state.journey_builder_data.get("show_action_selector"):
            self._render_action_selector()
        
        # Render existing steps
        step_sequence = StepSequence()
        step_sequence.render(st.session_state.journey_builder_data["journey_steps"])

    def _render_action_selector(self):
        """Render the action selector modal."""
        with st.container():
            st.write("### Select Action")
            
            action_selector = ActionSelector()
            selected_action = action_selector.render()
            
            if selected_action:
                self._add_step_to_journey(selected_action)
                st.session_state.journey_builder_data["show_action_selector"] = False
                st.rerun()
            
            if st.button("Cancel"):
                st.session_state.journey_builder_data["show_action_selector"] = False
                st.rerun()

    def _render_journey_properties(self):
        """Render journey properties and metadata panel."""
        st.subheader("Journey Properties")
        
        journey_data = st.session_state.journey_builder_data["current_journey"] or {}
        
        # Journey statistics
        steps = st.session_state.journey_builder_data["journey_steps"]
        
        st.metric("Total Steps", len(steps))
        
        if steps:
            action_types = {}
            for step in steps:
                action_type = step.get("action_type", "unknown")
                action_types[action_type] = action_types.get(action_type, 0) + 1
            
            st.write("**Step Distribution:**")
            for action_type, count in action_types.items():
                st.write(f"- {action_type.title()}: {count}")
        
        # Journey metadata
        st.write("**Metadata:**")
        metadata = journey_data.get("metadata", {})
        
        # Allow editing metadata
        with st.expander("Edit Metadata"):
            tags = st.text_input(
                "Tags (comma-separated)",
                value=", ".join(metadata.get("tags", []))
            )
            
            category = st.selectbox(
                "Category",
                ["functional", "integration", "regression", "smoke", "performance"],
                index=0
            )
            
            priority = st.selectbox(
                "Priority",
                ["low", "medium", "high", "critical"],
                index=1
            )
            
            if st.button("Update Metadata"):
                new_metadata = {
                    "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
                    "category": category,
                    "priority": priority,
                    **metadata
                }
                self._update_journey_metadata(new_metadata)

    def _render_validation_panel(self):
        """Render journey validation results panel."""
        st.subheader("Validation")
        
        validation_results = st.session_state.journey_builder_data.get("validation_results")
        
        if st.button("🔍 Validate Journey"):
            self._validate_journey()
        
        if validation_results:
            can_execute = validation_results.get("can_execute", False)
            
            if can_execute:
                st.success("✅ Journey is valid and can be executed")
            else:
                st.error("❌ Journey has validation errors")
            
            # Show validation details
            error_count = validation_results.get("error_count", 0)
            warning_count = validation_results.get("warning_count", 0)
            
            if error_count > 0:
                st.error(f"Errors: {error_count}")
            
            if warning_count > 0:
                st.warning(f"Warnings: {warning_count}")
            
            # Show detailed results
            with st.expander("Validation Details"):
                for result in validation_results.get("results", []):
                    severity = result.get("severity", "info")
                    message = result.get("message", "")
                    
                    if severity == "error":
                        st.error(f"🔴 {message}")
                    elif severity == "warning":
                        st.warning(f"🟡 {message}")
                    else:
                        st.info(f"🔵 {message}")

    def _render_action_bar(self, journey_id: Optional[str], activity_id: Optional[str], persona_id: Optional[str]):
        """Render the bottom action bar."""
        st.divider()
        
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.button("💾 Save Journey", type="primary"):
                self._save_journey(journey_id, activity_id, persona_id)
        
        with col2:
            if st.button("🎮 Test Run"):
                self._test_run_journey()
        
        with col3:
            if st.button("📋 Preview"):
                self._preview_journey()
        
        with col4:
            if st.button("🗑️ Clear All"):
                self._clear_journey()
        
        # Show unsaved changes indicator
        if st.session_state.journey_builder_data.get("unsaved_changes"):
            st.warning("⚠️ You have unsaved changes")

    def _load_journey(self, journey_id: str):
        """Load an existing journey for editing."""
        try:
            with show_loading_spinner("Loading journey..."):
                journey = self.journey_service.get_journey(journey_id)
                
                st.session_state.journey_builder_data.update({
                    "current_journey": journey,
                    "journey_steps": journey.get("steps", []),
                    "is_editing": True,
                    "unsaved_changes": False
                })
                
        except Exception as e:
            handle_api_error(e, "Failed to load journey")

    def _update_journey_details(self, details: Dict[str, Any]):
        """Update journey details."""
        current_journey = st.session_state.journey_builder_data.get("current_journey", {})
        current_journey.update(details)
        
        st.session_state.journey_builder_data["current_journey"] = current_journey
        st.session_state.journey_builder_data["unsaved_changes"] = True
        
        st.success("Journey details updated")

    def _update_journey_metadata(self, metadata: Dict[str, Any]):
        """Update journey metadata."""
        current_journey = st.session_state.journey_builder_data.get("current_journey", {})
        current_journey["metadata"] = metadata
        
        st.session_state.journey_builder_data["current_journey"] = current_journey
        st.session_state.journey_builder_data["unsaved_changes"] = True
        
        st.success("Metadata updated")

    def _add_step_to_journey(self, action: Dict[str, Any]):
        """Add a new step to the journey."""
        steps = st.session_state.journey_builder_data["journey_steps"]
        
        new_step = {
            "step_number": len(steps) + 1,
            "action_id": action["id"],
            "action_name": action["name"],
            "action_type": action["action_type"],
            "step_description": f"Step {len(steps) + 1}: {action['name']}",
            "parameters": {},
            "expected_outputs": {},
            "timeout_override": None,
            "retry_override": None,
            "depends_on_steps": [],
            "can_run_parallel": False,
            "is_critical": False
        }
        
        steps.append(new_step)
        st.session_state.journey_builder_data["journey_steps"] = steps
        st.session_state.journey_builder_data["unsaved_changes"] = True

    def _validate_journey(self):
        """Validate the current journey."""
        try:
            journey_data = self._prepare_journey_data()
            
            with show_loading_spinner("Validating journey..."):
                validation_results = self.journey_service.validate_journey(journey_data)
                st.session_state.journey_builder_data["validation_results"] = validation_results
                
        except Exception as e:
            handle_api_error(e, "Failed to validate journey")

    def _save_journey(self, journey_id: Optional[str], activity_id: Optional[str], persona_id: Optional[str]):
        """Save the current journey."""
        try:
            journey_data = self._prepare_journey_data(activity_id, persona_id)
            
            with show_loading_spinner("Saving journey..."):
                if journey_id:
                    # Update existing journey
                    result = self.journey_service.update_journey(journey_id, journey_data)
                else:
                    # Create new journey
                    result = self.journey_service.create_journey(journey_data)
                
                st.session_state.journey_builder_data["unsaved_changes"] = False
                st.success("Journey saved successfully!")
                
                return result
                
        except Exception as e:
            handle_api_error(e, "Failed to save journey")

    def _test_run_journey(self):
        """Test run the current journey."""
        st.info("🧪 Test run functionality coming soon...")

    def _preview_journey(self):
        """Preview the journey in a modal."""
        journey_data = self._prepare_journey_data()
        
        with st.expander("Journey Preview", expanded=True):
            st.json(journey_data)

    def _clear_journey(self):
        """Clear all journey data."""
        if st.button("Confirm Clear All", key="confirm_clear"):
            st.session_state.journey_builder_data = {
                "current_journey": None,
                "journey_steps": [],
                "selected_action": None,
                "validation_results": None,
                "is_editing": False,
                "unsaved_changes": False
            }
            st.success("Journey cleared")
            st.rerun()

    def _prepare_journey_data(self, activity_id: Optional[str] = None, persona_id: Optional[str] = None) -> Dict[str, Any]:
        """Prepare journey data for API submission."""
        current_journey = st.session_state.journey_builder_data.get("current_journey", {})
        steps = st.session_state.journey_builder_data["journey_steps"]
        
        return {
            "name": current_journey.get("name", ""),
            "description": current_journey.get("description", ""),
            "persona_id": persona_id or current_journey.get("persona_id"),
            "activity_id": activity_id or current_journey.get("activity_id"),
            "complexity_level": current_journey.get("complexity_level", "medium"),
            "estimated_duration_minutes": current_journey.get("estimated_duration_minutes", 30),
            "is_active": current_journey.get("is_active", True),
            "prerequisites": current_journey.get("prerequisites", []),
            "expected_outcomes": current_journey.get("expected_outcomes", []),
            "metadata": current_journey.get("metadata", {}),
            "steps": steps
        }


def render_journey_builder(journey_id: Optional[str] = None, activity_id: Optional[str] = None, persona_id: Optional[str] = None):
    """
    Render the journey builder component.
    
    Args:
        journey_id: Optional existing journey ID to edit
        activity_id: Required activity ID for new journeys  
        persona_id: Required persona ID for new journeys
    """
    builder = JourneyBuilder()
    builder.render(journey_id, activity_id, persona_id)