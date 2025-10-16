"""Activity form component for creating and editing activities.

This module provides forms for creating new activities and editing existing ones
with comprehensive validation and ERPNext integration features.
"""

import json
from typing import Any, Optional

import streamlit as st

from ...services.api_client import APIClient
from ..shared.components import (
    show_error_message,
    show_success_message,
    show_warning_message,
)
from ..shared.forms import (
    render_number_input,
    render_select_box,
    render_text_area,
    render_text_input,
)


def render_activity_form(api_client: APIClient, activity_id: Optional[str] = None):
    """Render activity creation/editing form."""

    is_edit_mode = activity_id is not None

    if is_edit_mode:
        st.subheader("✏️ Edit Activity")

        # Load existing activity data
        try:
            activity_data = api_client.get_activity(activity_id)
        except Exception as e:
            show_error_message(f"Error loading activity: {str(e)}")
            return
    else:
        st.subheader("➕ Create New Activity")
        activity_data = None

    # Form
    with st.form("activity_form"):
        # Basic Information
        st.subheader("📝 Basic Information")

        col1, col2 = st.columns(2)

        with col1:
            name = render_text_input(
                "Activity Name",
                value=activity_data.get("name", "") if activity_data else "",
                placeholder="E.g., Create Sales Invoice",
                help="Unique name for this activity",
                required=True,
            )

        with col2:
            version = render_text_input(
                "Version",
                value=activity_data.get("version", "1.0.0")
                if activity_data
                else "1.0.0",
                placeholder="1.0.0",
                help="Semantic version number",
            )

        description = render_text_area(
            "Description",
            value=activity_data.get("description", "") if activity_data else "",
            placeholder="Detailed description of what this activity does...",
            help="Comprehensive description of the activity",
            height=100,
            required=True,
        )

        # ERPNext Configuration
        st.subheader("🔧 ERPNext Configuration")

        col1, col2, col3 = st.columns(3)

        with col1:
            erpnext_modules = [
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

            erpnext_module = render_select_box(
                "ERPNext Module",
                options=erpnext_modules,
                value=activity_data.get("erpnext_module", "") if activity_data else "",
                help="Which ERPNext module this activity belongs to",
                required=True,
            )

        with col2:
            action_types = [
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

            action_type = render_select_box(
                "Action Type",
                options=action_types,
                value=activity_data.get("action_type", "") if activity_data else "",
                help="What type of action this activity performs",
                required=True,
            )

        with col3:
            target_doctype = render_text_input(
                "Target DocType",
                value=activity_data.get("target_doctype", "") if activity_data else "",
                placeholder="E.g., Sales Invoice",
                help="ERPNext DocType this activity operates on",
                required=True,
            )

        # Activity Configuration
        st.subheader("⚙️ Activity Configuration")

        col1, col2 = st.columns(2)

        with col1:
            complexity_score = render_number_input(
                "Complexity Score",
                min_value=1,
                max_value=5,
                value=activity_data.get("complexity_score", 3) if activity_data else 3,
                help="1=Very Easy, 2=Easy, 3=Medium, 4=Hard, 5=Very Hard",
                required=True,
            )

        with col2:
            estimated_duration = render_number_input(
                "Estimated Duration (seconds)",
                min_value=1,
                value=activity_data.get("estimated_duration", 60)
                if activity_data
                else 60,
                help="Expected time to complete this activity",
                required=True,
            )

        # Required Fields
        required_fields_text = st.text_area(
            "Required Fields (comma-separated)",
            value=", ".join(activity_data.get("required_fields", []))
            if activity_data
            else "",
            placeholder="customer, item_code, qty, rate",
            help="Fields that must be provided for this activity",
            height=60,
        )

        # Success Criteria
        success_criteria_text = st.text_area(
            "Success Criteria (comma-separated)",
            value=", ".join(activity_data.get("success_criteria", []))
            if activity_data
            else "",
            placeholder="Document created successfully, Status is Draft, No validation errors",
            help="Criteria that define successful completion",
            height=60,
        )

        # Prerequisites and Postconditions
        col1, col2 = st.columns(2)

        with col1:
            prerequisites_text = st.text_area(
                "Prerequisites (comma-separated)",
                value=", ".join(activity_data.get("prerequisites", []))
                if activity_data
                else "",
                placeholder="Customer exists, Item is active, Price List configured",
                help="Conditions that must exist before running this activity",
                height=80,
            )

        with col2:
            postconditions_text = st.text_area(
                "Postconditions (comma-separated)",
                value=", ".join(activity_data.get("postconditions", []))
                if activity_data
                else "",
                placeholder="Document saved, Workflow updated, Notification sent",
                help="Expected state after activity completion",
                height=80,
            )

        # Advanced Configuration
        with st.expander("🔬 Advanced Configuration"):
            # Validation Rules (JSON)
            st.subheader("Validation Rules")
            validation_rules_text = st.text_area(
                "Validation Rules (JSON)",
                value=json.dumps(activity_data.get("validation_rules", {}), indent=2)
                if activity_data
                else "{}",
                placeholder='{"field_name": {"required": true, "min_length": 3}}',
                help="JSON object defining validation rules for fields",
                height=100,
            )

            # Test Data Requirements (JSON)
            st.subheader("Test Data Requirements")
            test_data_text = st.text_area(
                "Test Data Requirements (JSON)",
                value=json.dumps(
                    activity_data.get("test_data_requirements", {}), indent=2
                )
                if activity_data
                else "{}",
                placeholder='{"customer": "sample_customer", "items": ["item1", "item2"]}',
                help="JSON object defining test data requirements",
                height=100,
            )

        # Tags and Status
        col1, col2 = st.columns(2)

        with col1:
            tags_text = st.text_input(
                "Tags (comma-separated)",
                value=", ".join(activity_data.get("tags", [])) if activity_data else "",
                placeholder="automation, regression, critical, ui",
                help="Tags for organizing and filtering activities",
            )

        with col2:
            is_active = st.checkbox(
                "Active",
                value=activity_data.get("is_active", True) if activity_data else True,
                help="Whether this activity is currently active",
            )

        # Form submission
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            submit_button = st.form_submit_button(
                "💾 Update Activity" if is_edit_mode else "➕ Create Activity",
                type="primary",
            )

        with col2:
            if is_edit_mode and st.form_submit_button("🗑️ Delete", type="secondary"):
                if st.session_state.get("confirm_delete", False):
                    try:
                        api_client.delete_activity(activity_id)
                        show_success_message("Activity deleted successfully")
                        st.switch_page("pages/activities.py")
                    except Exception as e:
                        show_error_message(f"Error deleting activity: {str(e)}")
                else:
                    st.session_state.confirm_delete = True
                    show_warning_message("Click delete again to confirm")

        with col3:
            if st.form_submit_button("🔍 Preview/Validate"):
                preview_activity_data(
                    name,
                    description,
                    erpnext_module,
                    action_type,
                    target_doctype,
                    complexity_score,
                    estimated_duration,
                    required_fields_text,
                    success_criteria_text,
                    prerequisites_text,
                    postconditions_text,
                    validation_rules_text,
                    test_data_text,
                    tags_text,
                    is_active,
                )

    # Handle form submission
    if submit_button:
        try:
            # Prepare activity data
            activity_data = prepare_activity_data(
                name,
                description,
                erpnext_module,
                action_type,
                target_doctype,
                complexity_score,
                estimated_duration,
                required_fields_text,
                success_criteria_text,
                prerequisites_text,
                postconditions_text,
                validation_rules_text,
                test_data_text,
                tags_text,
                is_active,
                version,
            )

            if is_edit_mode:
                # Update existing activity
                result = api_client.update_activity(activity_id, activity_data)
                show_success_message(
                    f"Activity '{result['name']}' updated successfully!"
                )
            else:
                # Create new activity
                result = api_client.create_activity(activity_data)
                show_success_message(
                    f"Activity '{result['name']}' created successfully!"
                )

                # Clear form by redirecting to activities list
                st.switch_page("pages/activities.py")

        except Exception as e:
            show_error_message(
                f"Error {'updating' if is_edit_mode else 'creating'} activity: {str(e)}"
            )


def prepare_activity_data(
    name: str,
    description: str,
    erpnext_module: str,
    action_type: str,
    target_doctype: str,
    complexity_score: int,
    estimated_duration: int,
    required_fields_text: str,
    success_criteria_text: str,
    prerequisites_text: str,
    postconditions_text: str,
    validation_rules_text: str,
    test_data_text: str,
    tags_text: str,
    is_active: bool,
    version: str,
) -> dict[str, Any]:
    """Prepare activity data for API submission."""

    # Parse comma-separated lists
    required_fields = [f.strip() for f in required_fields_text.split(",") if f.strip()]
    success_criteria = [
        c.strip() for c in success_criteria_text.split(",") if c.strip()
    ]
    prerequisites = [p.strip() for p in prerequisites_text.split(",") if p.strip()]
    postconditions = [p.strip() for p in postconditions_text.split(",") if p.strip()]
    tags = [t.strip() for t in tags_text.split(",") if t.strip()]

    # Parse JSON fields
    try:
        validation_rules = (
            json.loads(validation_rules_text) if validation_rules_text.strip() else {}
        )
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON in validation rules")

    try:
        test_data_requirements = (
            json.loads(test_data_text) if test_data_text.strip() else {}
        )
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON in test data requirements")

    return {
        "name": name,
        "description": description,
        "erpnext_module": erpnext_module,
        "action_type": action_type,
        "target_doctype": target_doctype,
        "required_fields": required_fields,
        "validation_rules": validation_rules,
        "success_criteria": success_criteria,
        "complexity_score": complexity_score,
        "estimated_duration": estimated_duration,
        "prerequisites": prerequisites,
        "postconditions": postconditions,
        "test_data_requirements": test_data_requirements,
        "tags": tags,
        "is_active": is_active,
        "version": version,
    }


def preview_activity_data(
    name: str,
    description: str,
    erpnext_module: str,
    action_type: str,
    target_doctype: str,
    complexity_score: int,
    estimated_duration: int,
    required_fields_text: str,
    success_criteria_text: str,
    prerequisites_text: str,
    postconditions_text: str,
    validation_rules_text: str,
    test_data_text: str,
    tags_text: str,
    is_active: bool,
):
    """Preview and validate activity data."""

    st.subheader("🔍 Activity Preview")

    # Validation
    validation_errors = []

    if not name.strip():
        validation_errors.append("Activity name is required")

    if not description.strip():
        validation_errors.append("Description is required")

    if not erpnext_module:
        validation_errors.append("ERPNext module is required")

    if not action_type:
        validation_errors.append("Action type is required")

    if not target_doctype.strip():
        validation_errors.append("Target DocType is required")

    if complexity_score < 1 or complexity_score > 5:
        validation_errors.append("Complexity score must be between 1 and 5")

    if estimated_duration < 1:
        validation_errors.append("Estimated duration must be greater than 0")

    # Validate JSON fields
    try:
        json.loads(validation_rules_text) if validation_rules_text.strip() else {}
    except json.JSONDecodeError:
        validation_errors.append("Invalid JSON in validation rules")

    try:
        json.loads(test_data_text) if test_data_text.strip() else {}
    except json.JSONDecodeError:
        validation_errors.append("Invalid JSON in test data requirements")

    # Display validation results
    if validation_errors:
        st.error("❌ Validation Errors:")
        for error in validation_errors:
            st.write(f"• {error}")
    else:
        st.success("✅ Activity data is valid")

    # Display preview
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Basic Information:**")
        st.write(f"• **Name:** {name}")
        st.write(f"• **Module:** {erpnext_module}")
        st.write(f"• **Action:** {action_type}")
        st.write(f"• **DocType:** {target_doctype}")
        st.write(f"• **Complexity:** {complexity_score}/5")
        st.write(f"• **Duration:** {estimated_duration}s")
        st.write(f"• **Status:** {'Active' if is_active else 'Inactive'}")

    with col2:
        st.write("**Configuration:**")

        required_fields = [
            f.strip() for f in required_fields_text.split(",") if f.strip()
        ]
        if required_fields:
            st.write(f"• **Required Fields:** {len(required_fields)} fields")

        success_criteria = [
            c.strip() for c in success_criteria_text.split(",") if c.strip()
        ]
        if success_criteria:
            st.write(f"• **Success Criteria:** {len(success_criteria)} criteria")

        prerequisites = [p.strip() for p in prerequisites_text.split(",") if p.strip()]
        if prerequisites:
            st.write(f"• **Prerequisites:** {len(prerequisites)} items")

        postconditions = [
            p.strip() for p in postconditions_text.split(",") if p.strip()
        ]
        if postconditions:
            st.write(f"• **Postconditions:** {len(postconditions)} items")

        tags = [t.strip() for t in tags_text.split(",") if t.strip()]
        if tags:
            st.write(
                f"• **Tags:** {', '.join(tags[:3])}{'...' if len(tags) > 3 else ''}"
            )

    # Description preview
    if description.strip():
        st.write("**Description:**")
        st.write(description)


def render_activity_quick_form(api_client: APIClient):
    """Render a simplified quick activity creation form."""

    st.subheader("🚀 Quick Create Activity")

    with st.form("quick_activity_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("Activity Name*", placeholder="E.g., Create Customer")
            erpnext_module = st.selectbox(
                "Module*",
                [
                    "Accounts",
                    "Stock",
                    "Buying",
                    "Selling",
                    "CRM",
                    "Projects",
                    "Manufacturing",
                    "HR",
                ],
            )
            action_type = st.selectbox(
                "Action*",
                [
                    "create",
                    "read",
                    "update",
                    "delete",
                    "list",
                    "search",
                    "approve",
                    "submit",
                ],
            )

        with col2:
            target_doctype = st.text_input(
                "Target DocType*", placeholder="E.g., Customer"
            )
            complexity_score = st.slider("Complexity", 1, 5, 3)
            estimated_duration = st.number_input(
                "Duration (seconds)", min_value=1, value=60
            )

        description = st.text_area(
            "Description*", placeholder="Brief description...", height=80
        )

        if st.form_submit_button("➕ Create Activity", type="primary"):
            if (
                name
                and erpnext_module
                and action_type
                and target_doctype
                and description
            ):
                try:
                    activity_data = {
                        "name": name,
                        "description": description,
                        "erpnext_module": erpnext_module,
                        "action_type": action_type,
                        "target_doctype": target_doctype,
                        "complexity_score": complexity_score,
                        "estimated_duration": estimated_duration,
                        "required_fields": [],
                        "validation_rules": {},
                        "success_criteria": [],
                        "prerequisites": [],
                        "postconditions": [],
                        "test_data_requirements": {},
                        "tags": [],
                        "is_active": True,
                        "version": "1.0.0",
                    }

                    result = api_client.create_activity(activity_data)
                    show_success_message(
                        f"Activity '{result['name']}' created successfully!"
                    )
                    st.rerun()

                except Exception as e:
                    show_error_message(f"Error creating activity: {str(e)}")
            else:
                show_error_message("Please fill in all required fields marked with *")
