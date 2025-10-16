"""Activity detail component for viewing individual activities.

This module provides detailed view of activities with all metadata,
relationships, and action capabilities.
"""

import streamlit as st
from typing import Dict, Any, Optional
import json

from ...services.api_client import APIClient
from ..shared.components import (
    show_success_message,
    show_error_message,
    show_info_message,
    confirm_action
)
from ..shared.utils import format_duration, format_datetime


def render_activity_detail(activity_id: str, api_client: APIClient):
    """Render detailed view of a specific activity."""
    
    try:
        # Load activity data
        activity = api_client.get_activity(activity_id)
        
        # Header with action buttons
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            status_emoji = "✅" if activity['is_active'] else "❌"
            st.title(f"{status_emoji} {activity['name']}")
        
        with col2:
            if st.button("✏️ Edit", key="edit_activity"):
                st.session_state.edit_activity_id = activity_id
                st.switch_page("pages/activity_edit.py")
        
        with col3:
            if st.button("🔄 Toggle Status", key="toggle_status"):
                toggle_activity_status(activity_id, not activity['is_active'], api_client)
        
        with col4:
            if st.button("🗑️ Delete", key="delete_activity", type="secondary"):
                if confirm_action(f"Delete activity '{activity['name']}'?"):
                    delete_activity(activity_id, api_client)
        
        # Tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Overview", "⚙️ Configuration", "🔗 Relationships", 
            "📊 Analysis", "🧪 Testing"
        ])
        
        with tab1:
            render_activity_overview(activity)
        
        with tab2:
            render_activity_configuration(activity)
        
        with tab3:
            render_activity_relationships(activity_id, api_client)
        
        with tab4:
            render_activity_analysis(activity_id, api_client)
        
        with tab5:
            render_activity_testing(activity)
    
    except Exception as e:
        show_error_message(f"Error loading activity: {str(e)}")


def render_activity_overview(activity: Dict[str, Any]):
    """Render activity overview tab."""
    
    # Basic information
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Basic Information")
        
        st.write(f"**Name:** {activity['name']}")
        st.write(f"**Version:** {activity['version']}")
        st.write(f"**Status:** {'✅ Active' if activity['is_active'] else '❌ Inactive'}")
        st.write(f"**Created:** {format_datetime(activity['created_at'])}")
        st.write(f"**Updated:** {format_datetime(activity['updated_at'])}")
        
        # Tags
        if activity.get('tags'):
            st.write("**Tags:**")
            for tag in activity['tags']:
                st.markdown(f"`{tag}`")
    
    with col2:
        st.subheader("🔧 ERPNext Context")
        
        st.write(f"**Module:** {activity['erpnext_module']}")
        st.write(f"**Action Type:** {activity['action_type']}")
        st.write(f"**Target DocType:** {activity['target_doctype']}")
        
        # Execution metadata
        st.subheader("⏱️ Execution Metadata")
        
        complexity_stars = "⭐" * activity['complexity_score']
        st.write(f"**Complexity:** {complexity_stars} ({activity['complexity_score']}/5)")
        st.write(f"**Estimated Duration:** {format_duration(activity['estimated_duration'])}")
    
    # Description
    st.subheader("📄 Description")
    st.write(activity['description'])
    
    # Required Fields
    if activity.get('required_fields'):
        st.subheader("📋 Required Fields")
        for field in activity['required_fields']:
            st.markdown(f"• `{field}`")
    
    # Success Criteria
    if activity.get('success_criteria'):
        st.subheader("✅ Success Criteria")
        for criteria in activity['success_criteria']:
            st.markdown(f"• {criteria}")


def render_activity_configuration(activity: Dict[str, Any]):
    """Render activity configuration tab."""
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Prerequisites
        st.subheader("📋 Prerequisites")
        if activity.get('prerequisites'):
            for prereq in activity['prerequisites']:
                st.markdown(f"• {prereq}")
        else:
            st.write("*No prerequisites defined*")
        
        # Validation Rules
        st.subheader("🔍 Validation Rules")
        if activity.get('validation_rules'):
            st.json(activity['validation_rules'])
        else:
            st.write("*No validation rules defined*")
    
    with col2:
        # Postconditions
        st.subheader("📋 Postconditions")
        if activity.get('postconditions'):
            for postcond in activity['postconditions']:
                st.markdown(f"• {postcond}")
        else:
            st.write("*No postconditions defined*")
        
        # Test Data Requirements
        st.subheader("🧪 Test Data Requirements")
        if activity.get('test_data_requirements'):
            st.json(activity['test_data_requirements'])
        else:
            st.write("*No test data requirements defined*")


def render_activity_relationships(activity_id: str, api_client: APIClient):
    """Render activity relationships tab."""
    
    # Personas linked to this activity
    st.subheader("👤 Linked Personas")
    
    try:
        personas = api_client.get_activity_personas(activity_id)
        
        if personas:
            for persona_link in personas:
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.write(f"**{persona_link.get('persona_name', 'Unknown Persona')}**")
                    if persona_link.get('notes'):
                        st.write(f"*{persona_link['notes']}*")
                
                with col2:
                    priority_colors = {
                        'critical': '🔴',
                        'high': '🟠',
                        'medium': '🟡',
                        'low': '🟢'
                    }
                    priority_emoji = priority_colors.get(persona_link.get('priority', 'medium'), '🟡')
                    st.write(f"{priority_emoji} {persona_link.get('priority', 'medium').title()}")
                
                with col3:
                    if persona_link.get('is_primary'):
                        st.write("⭐ Primary")
                    else:
                        st.write("")
                
                with col4:
                    if st.button("🗑️", key=f"unlink_{persona_link['id']}", help="Unlink persona"):
                        if confirm_action("Unlink this persona from the activity?"):
                            unlink_persona(activity_id, persona_link['persona_id'], api_client)
                
                st.divider()
        else:
            st.info("No personas linked to this activity yet.")
            
            if st.button("🔗 Link Persona"):
                st.session_state.show_link_persona_modal = True
    
    except Exception as e:
        show_error_message(f"Error loading persona relationships: {str(e)}")
    
    # Similar Activities
    st.subheader("🔍 Similar Activities")
    
    try:
        similar_activities = api_client.find_similar_activities(activity_id)
        
        if similar_activities:
            for similar in similar_activities:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{similar['name']}**")
                    st.write(f"*{similar['erpnext_module']} - {similar['action_type']}*")
                
                with col2:
                    similarity_percentage = similar.get('similarity_score', 0) * 100
                    st.write(f"📊 {similarity_percentage:.1f}% similar")
                
                with col3:
                    if st.button("👁️ View", key=f"view_similar_{similar['id']}"):
                        st.session_state.view_activity_id = similar['id']
                        st.rerun()
        else:
            st.info("No similar activities found.")
    
    except Exception as e:
        show_error_message(f"Error loading similar activities: {str(e)}")


def render_activity_analysis(activity_id: str, api_client: APIClient):
    """Render activity analysis tab."""
    
    # Compatibility Analysis
    st.subheader("🔗 Compatibility Analysis")
    
    compatibility_activity_id = st.text_input(
        "Enter another activity ID to check compatibility:",
        placeholder="Activity ID..."
    )
    
    if compatibility_activity_id and st.button("🔍 Check Compatibility"):
        try:
            compatibility = api_client.check_activity_compatibility(activity_id, compatibility_activity_id)
            
            if compatibility.get('compatible', False):
                st.success("✅ Activities are compatible for sequence execution")
                
                if compatibility.get('compatibility_score'):
                    score = compatibility['compatibility_score'] * 100
                    st.write(f"**Compatibility Score:** {score:.1f}%")
                
                if compatibility.get('suggestions'):
                    st.write("**Suggestions:**")
                    for suggestion in compatibility['suggestions']:
                        st.write(f"• {suggestion}")
            else:
                st.error("❌ Activities are not compatible for sequence execution")
                
                if compatibility.get('issues'):
                    st.write("**Issues:**")
                    for issue in compatibility['issues']:
                        st.write(f"• {issue}")
        
        except Exception as e:
            show_error_message(f"Error checking compatibility: {str(e)}")
    
    # Validation Results
    st.subheader("✅ Validation Results")
    
    if st.button("🔍 Validate Activity Configuration"):
        try:
            validation_result = api_client.validate_activity(activity_id)
            
            if validation_result.get('is_valid', False):
                st.success("✅ Activity configuration is valid")
            else:
                st.warning("⚠️ Activity configuration has issues")
            
            if validation_result.get('warnings'):
                st.write("**Warnings:**")
                for warning in validation_result['warnings']:
                    st.warning(f"• {warning}")
            
            if validation_result.get('errors'):
                st.write("**Errors:**")
                for error in validation_result['errors']:
                    st.error(f"• {error}")
            
            if validation_result.get('suggestions'):
                st.write("**Suggestions:**")
                for suggestion in validation_result['suggestions']:
                    st.info(f"• {suggestion}")
        
        except Exception as e:
            show_error_message(f"Error validating activity: {str(e)}")


def render_activity_testing(activity: Dict[str, Any]):
    """Render activity testing tab."""
    
    st.subheader("🧪 Test Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Test Readiness Checklist:**")
        
        # Check various aspects
        has_description = bool(activity.get('description', '').strip())
        has_required_fields = bool(activity.get('required_fields'))
        has_success_criteria = bool(activity.get('success_criteria'))
        has_test_data = bool(activity.get('test_data_requirements'))
        has_validation_rules = bool(activity.get('validation_rules'))
        
        st.write(f"{'✅' if has_description else '❌'} Has description")
        st.write(f"{'✅' if has_required_fields else '❌'} Has required fields defined")
        st.write(f"{'✅' if has_success_criteria else '❌'} Has success criteria")
        st.write(f"{'✅' if has_test_data else '❌'} Has test data requirements")
        st.write(f"{'✅' if has_validation_rules else '❌'} Has validation rules")
        
        # Overall readiness score
        total_checks = 5
        passed_checks = sum([has_description, has_required_fields, has_success_criteria, has_test_data, has_validation_rules])
        readiness_score = (passed_checks / total_checks) * 100
        
        st.metric("Test Readiness Score", f"{readiness_score:.0f}%")
    
    with col2:
        st.write("**Recommended Test Types:**")
        
        # Based on action type, suggest test types
        action_type = activity.get('action_type', '')
        
        if action_type in ['create', 'update']:
            st.write("• Data validation tests")
            st.write("• Field requirement tests")
            st.write("• Business rule tests")
        
        if action_type in ['read', 'list', 'search']:
            st.write("• Data retrieval tests")
            st.write("• Filter accuracy tests")
            st.write("• Performance tests")
        
        if action_type == 'delete':
            st.write("• Cascade deletion tests")
            st.write("• Permission tests")
            st.write("• Data integrity tests")
        
        if action_type in ['approve', 'reject', 'submit']:
            st.write("• Workflow state tests")
            st.write("• Permission tests")
            st.write("• Notification tests")
        
        st.write("• UI interaction tests")
        st.write("• Error handling tests")
    
    # Test Data Preview
    if activity.get('test_data_requirements'):
        st.subheader("📋 Test Data Preview")
        st.json(activity['test_data_requirements'])
    
    # Generate Test Cases Button
    if st.button("🚀 Generate Test Cases"):
        st.info("Test case generation would be implemented here...")
        # This would integrate with the test generation system


# Helper functions
def toggle_activity_status(activity_id: str, new_status: bool, api_client: APIClient):
    """Toggle activity status."""
    try:
        result = api_client.bulk_update_activity_status([activity_id], new_status)
        status_text = "active" if new_status else "inactive"
        show_success_message(f"Activity status changed to {status_text}")
        st.rerun()
    except Exception as e:
        show_error_message(f"Error updating activity status: {str(e)}")


def delete_activity(activity_id: str, api_client: APIClient):
    """Delete an activity."""
    try:
        api_client.delete_activity(activity_id)
        show_success_message("Activity deleted successfully")
        st.switch_page("pages/activities.py")
    except Exception as e:
        show_error_message(f"Error deleting activity: {str(e)}")


def unlink_persona(activity_id: str, persona_id: str, api_client: APIClient):
    """Unlink a persona from an activity."""
    try:
        api_client.unlink_activity_from_persona(activity_id, persona_id)
        show_success_message("Persona unlinked successfully")
        st.rerun()
    except Exception as e:
        show_error_message(f"Error unlinking persona: {str(e)}")