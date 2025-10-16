"""
Step Sequence Component

Component for managing the sequence of steps in a journey. Provides
drag-and-drop reordering, step editing, and dependency management
for building comprehensive test scenarios.
"""

import streamlit as st
from typing import Any, Dict, List, Optional

from ..shared.error_handler import handle_api_error


class StepSequence:
    """Step sequence component for managing journey steps."""

    def __init__(self):
        # Initialize session state
        if "step_sequence_data" not in st.session_state:
            st.session_state.step_sequence_data = {
                "editing_step": None,
                "step_parameters": {},
                "show_dependencies": False
            }

    def render(self, steps: List[Dict[str, Any]]):
        """
        Render the step sequence interface.
        
        Args:
            steps: List of journey steps to display and manage
        """
        if not steps:
            st.info("No steps added yet. Use 'Add Step' to build your journey.")
            return
        
        st.write(f"**Journey Steps ({len(steps)})**")
        
        # Step sequence controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Reorder Steps"):
                self._show_reorder_interface(steps)
        
        with col2:
            show_deps = st.checkbox(
                "Show Dependencies",
                value=st.session_state.step_sequence_data["show_dependencies"]
            )
            st.session_state.step_sequence_data["show_dependencies"] = show_deps
        
        with col3:
            if st.button("🧹 Clean Empty Steps"):
                self._clean_empty_steps(steps)
        
        st.divider()
        
        # Render individual steps
        for i, step in enumerate(steps):
            self._render_step(i, step, steps)

    def _render_step(self, index: int, step: Dict[str, Any], all_steps: List[Dict[str, Any]]):
        """Render an individual step in the sequence."""
        step_number = step.get("step_number", index + 1)
        action_name = step.get("action_name", "Unknown Action")
        action_type = step.get("action_type", "unknown")
        
        # Step container with border
        with st.container():
            # Step header
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.write(f"**Step {step_number}: {action_name}**")
                step_desc = step.get("step_description", "")
                if step_desc:
                    st.caption(step_desc)
            
            with col2:
                # Action type badge
                type_colors = {
                    "given": "primary",
                    "when": "secondary", 
                    "then": "success"
                }
                st.badge(action_type.upper(), type=type_colors.get(action_type, "secondary"))
            
            with col3:
                # Step controls
                if st.button("✏️", key=f"edit_step_{index}", help="Edit step"):
                    self._edit_step(index, step)
                
                if st.button("🗑️", key=f"delete_step_{index}", help="Delete step"):
                    self._delete_step(index, all_steps)
            
            with col4:
                # Move controls
                col_up, col_down = st.columns(2)
                with col_up:
                    if index > 0 and st.button("⬆️", key=f"move_up_{index}", help="Move up"):
                        self._move_step(index, index - 1, all_steps)
                
                with col_down:
                    if index < len(all_steps) - 1 and st.button("⬇️", key=f"move_down_{index}", help="Move down"):
                        self._move_step(index, index + 1, all_steps)
            
            # Step details
            if st.session_state.step_sequence_data.get("editing_step") == index:
                self._render_step_editor(index, step)
            else:
                self._render_step_summary(step)
            
            # Dependencies (if enabled)
            if st.session_state.step_sequence_data["show_dependencies"]:
                self._render_step_dependencies(index, step, all_steps)
            
            st.divider()

    def _render_step_summary(self, step: Dict[str, Any]):
        """Render a summary view of the step."""
        col1, col2 = st.columns(2)
        
        with col1:
            # Parameters summary
            parameters = step.get("parameters", {})
            if parameters:
                st.write("**Parameters:**")
                for key, value in parameters.items():
                    st.caption(f"• {key}: {value}")
            else:
                st.caption("No parameters configured")
        
        with col2:
            # Configuration summary
            config_items = []
            
            if step.get("timeout_override"):
                config_items.append(f"Timeout: {step['timeout_override']}s")
            
            if step.get("retry_override") is not None:
                config_items.append(f"Retries: {step['retry_override']}")
            
            if step.get("can_run_parallel"):
                config_items.append("Can run in parallel")
            
            if step.get("is_critical"):
                config_items.append("Critical step")
            
            if config_items:
                st.write("**Configuration:**")
                for item in config_items:
                    st.caption(f"• {item}")
            else:
                st.caption("Default configuration")

    def _render_step_editor(self, index: int, step: Dict[str, Any]):
        """Render the step editor interface."""
        st.write("### Edit Step")
        
        with st.form(f"edit_step_form_{index}"):
            # Basic step information
            step_description = st.text_area(
                "Step Description",
                value=step.get("step_description", ""),
                placeholder="Describe what this step does"
            )
            
            # Parameters
            st.write("**Parameters**")
            parameters = step.get("parameters", {})
            
            # Simple parameter editor (could be enhanced with schema-based editing)
            param_text = "\\n".join([f"{k}={v}" for k, v in parameters.items()])
            param_input = st.text_area(
                "Parameters (key=value, one per line)",
                value=param_text,
                placeholder="parameter_name=parameter_value"
            )
            
            # Expected outputs
            st.write("**Expected Outputs**")
            expected_outputs = step.get("expected_outputs", {})
            output_text = "\\n".join([f"{k}={v}" for k, v in expected_outputs.items()])
            output_input = st.text_area(
                "Expected Outputs (key=value, one per line)",
                value=output_text,
                placeholder="output_name=expected_value"
            )
            
            # Advanced configuration
            col1, col2 = st.columns(2)
            
            with col1:
                timeout_override = st.number_input(
                    "Timeout Override (seconds)",
                    min_value=1,
                    max_value=3600,
                    value=step.get("timeout_override") or 30,
                    help="Override default timeout for this step"
                )
                
                retry_override = st.number_input(
                    "Retry Override",
                    min_value=0,
                    max_value=10,
                    value=step.get("retry_override") or 0,
                    help="Override default retry count for this step"
                )
            
            with col2:
                can_run_parallel = st.checkbox(
                    "Can run in parallel",
                    value=step.get("can_run_parallel", False),
                    help="Whether this step can run in parallel with others"
                )
                
                is_critical = st.checkbox(
                    "Critical step",
                    value=step.get("is_critical", False),
                    help="Whether this step is critical for journey success"
                )
            
            # Form submission buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.form_submit_button("💾 Save Changes", type="primary"):
                    self._save_step_changes(index, {
                        "step_description": step_description,
                        "parameters": self._parse_key_value_pairs(param_input),
                        "expected_outputs": self._parse_key_value_pairs(output_input),
                        "timeout_override": timeout_override if timeout_override != 30 else None,
                        "retry_override": retry_override if retry_override != 0 else None,
                        "can_run_parallel": can_run_parallel,
                        "is_critical": is_critical
                    })
            
            with col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.step_sequence_data["editing_step"] = None
                    st.rerun()

    def _render_step_dependencies(self, index: int, step: Dict[str, Any], all_steps: List[Dict[str, Any]]):
        """Render step dependencies interface."""
        depends_on = step.get("depends_on_steps", [])
        
        st.write("**Dependencies:**")
        
        if depends_on:
            for dep_step in depends_on:
                if dep_step < len(all_steps):
                    dep_name = all_steps[dep_step - 1].get("action_name", f"Step {dep_step}")
                    st.caption(f"• Depends on Step {dep_step}: {dep_name}")
        else:
            st.caption("No dependencies")
        
        # Add dependency interface
        with st.expander("Manage Dependencies"):
            available_steps = [i + 1 for i in range(index)]  # Only previous steps
            
            if available_steps:
                selected_deps = st.multiselect(
                    "Depends on steps:",
                    options=available_steps,
                    default=depends_on,
                    format_func=lambda x: f"Step {x}: {all_steps[x-1].get('action_name', 'Unknown')}"
                )
                
                if st.button(f"Update Dependencies", key=f"update_deps_{index}"):
                    self._update_step_dependencies(index, selected_deps)
            else:
                st.info("No previous steps available for dependencies")

    def _edit_step(self, index: int, step: Dict[str, Any]):
        """Start editing a step."""
        st.session_state.step_sequence_data["editing_step"] = index
        st.rerun()

    def _delete_step(self, index: int, all_steps: List[Dict[str, Any]]):
        """Delete a step from the sequence."""
        if st.button(f"Confirm Delete Step {index + 1}", key=f"confirm_delete_{index}"):
            all_steps.pop(index)
            
            # Renumber remaining steps
            for i, step in enumerate(all_steps):
                step["step_number"] = i + 1
            
            # Update session state
            st.session_state.journey_builder_data["journey_steps"] = all_steps
            st.session_state.journey_builder_data["unsaved_changes"] = True
            
            st.success(f"Step {index + 1} deleted")
            st.rerun()

    def _move_step(self, from_index: int, to_index: int, all_steps: List[Dict[str, Any]]):
        """Move a step to a different position."""
        # Swap steps
        all_steps[from_index], all_steps[to_index] = all_steps[to_index], all_steps[from_index]
        
        # Renumber steps
        for i, step in enumerate(all_steps):
            step["step_number"] = i + 1
        
        # Update session state
        st.session_state.journey_builder_data["journey_steps"] = all_steps
        st.session_state.journey_builder_data["unsaved_changes"] = True
        
        st.rerun()

    def _save_step_changes(self, index: int, changes: Dict[str, Any]):
        """Save changes to a step."""
        steps = st.session_state.journey_builder_data["journey_steps"]
        
        # Update step with changes
        steps[index].update(changes)
        
        # Update session state
        st.session_state.journey_builder_data["journey_steps"] = steps
        st.session_state.journey_builder_data["editing_step"] = None
        st.session_state.journey_builder_data["unsaved_changes"] = True
        
        st.success("Step updated successfully")
        st.rerun()

    def _update_step_dependencies(self, index: int, dependencies: List[int]):
        """Update step dependencies."""
        steps = st.session_state.journey_builder_data["journey_steps"]
        steps[index]["depends_on_steps"] = dependencies
        
        # Update session state
        st.session_state.journey_builder_data["journey_steps"] = steps
        st.session_state.journey_builder_data["unsaved_changes"] = True
        
        st.success("Dependencies updated")
        st.rerun()

    def _parse_key_value_pairs(self, text: str) -> Dict[str, str]:
        """Parse key=value pairs from text input."""
        pairs = {}
        
        for line in text.split("\\n"):
            line = line.strip()
            if "=" in line:
                key, value = line.split("=", 1)
                pairs[key.strip()] = value.strip()
        
        return pairs

    def _show_reorder_interface(self, steps: List[Dict[str, Any]]):
        """Show step reordering interface."""
        st.info("🔄 Drag and drop functionality coming soon. Use the ⬆️⬇️ buttons for now.")

    def _clean_empty_steps(self, steps: List[Dict[str, Any]]):
        """Clean up empty or invalid steps."""
        original_count = len(steps)
        
        # Remove steps without action_id
        cleaned_steps = [step for step in steps if step.get("action_id")]
        
        # Renumber steps
        for i, step in enumerate(cleaned_steps):
            step["step_number"] = i + 1
        
        # Update session state
        st.session_state.journey_builder_data["journey_steps"] = cleaned_steps
        
        removed_count = original_count - len(cleaned_steps)
        if removed_count > 0:
            st.session_state.journey_builder_data["unsaved_changes"] = True
            st.success(f"Removed {removed_count} empty steps")
            st.rerun()
        else:
            st.info("No empty steps found")


def render_step_sequence(steps: List[Dict[str, Any]]):
    """
    Render the step sequence component.
    
    Args:
        steps: List of journey steps to display and manage
    """
    sequence = StepSequence()
    sequence.render(steps)