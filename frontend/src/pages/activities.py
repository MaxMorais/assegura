"""Activities management page.

Main page for managing ERPNext business activities including listing,
searching, creating, editing, and viewing detailed activity information.
"""

import sys
from pathlib import Path

import streamlit as st

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

#try:
from components.activity_forms import render_activity_list
from services.api_client import APIClient
#except ImportError:
#    st.error("Missing dependencies - please install requirements")


def show_activities() -> None:
    """Display business activities management interface."""
    main()


def main():
    """Main activities page."""

    st.set_page_config(
        page_title="Activity Management - ERPNext Test Framework",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS
    st.markdown(
        """
    <style>
    .main-header {
        padding: 2rem 0 1rem 0;
        border-bottom: 2px solid #f0f2f6;
        margin-bottom: 2rem;
    }
    .activity-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
    }
    .status-active {
        color: #28a745;
        font-weight: bold;
    }
    .status-inactive {
        color: #dc3545;
        font-weight: bold;
    }
    .complexity-indicator {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .complexity-1 { background-color: #d4edda; color: #155724; }
    .complexity-2 { background-color: #d1ecf1; color: #0c5460; }
    .complexity-3 { background-color: #fff3cd; color: #856404; }
    .complexity-4 { background-color: #f8d7da; color: #721c24; }
    .complexity-5 { background-color: #f5c6cb; color: #491217; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Navigation check - if coming from persona detail page
    if "view_activity_id" in st.session_state:
        # Show activity detail
        from components.activity_forms import render_activity_detail

        api_client = APIClient()
        render_activity_detail(st.session_state.view_activity_id, api_client)

        # Back button
        if st.button("⬅️ Back to Activities List"):
            del st.session_state.view_activity_id
            st.rerun()

    elif "edit_activity_id" in st.session_state:
        # Show activity edit form
        from components.activity_forms import render_activity_form

        api_client = APIClient()
        render_activity_form(api_client, st.session_state.edit_activity_id)

        # Back button
        if st.button("⬅️ Back to Activities List"):
            del st.session_state.edit_activity_id
            st.rerun()

    else:
        # Show main activities list
        try:
            render_activity_list()
        except NameError:
            st.error("Activity components not available")


if __name__ == "__main__":
    main()
