"""Streamlit application bootstrap and configuration.

Main entry point for the ERPNext Test Automation Meta-Framework frontend,
implementing constitutional requirements for NON-NEGOTIABLE Streamlit UI.
"""

import logging
from typing import Any
from typing import Dict
from typing import Optional

try:
    import streamlit as st
    import requests
    from requests.exceptions import ConnectionError
    from requests.exceptions import RequestException
except ImportError as e:
    # Dependencies not installed yet - expected during initial setup
    print(f"Streamlit dependencies not installed: {e}")
    print("Run 'pip install -r requirements.txt' in frontend directory")

from .components.sidebar import render_sidebar
from .components.header import render_header
from .pages.dashboard import show_dashboard
from .pages.personas import show_personas
from .pages.activities import show_activities
from .pages.journeys import show_journeys
from .pages.test_generation import show_test_generation
from .services.api_client import APIClient


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def configure_page() -> None:
    """Configure Streamlit page settings and layout.
    
    Sets up constitutional compliance metadata and page configuration
    following Streamlit best practices.
    """
    st.set_page_config(
        page_title="ERPNext Test Automation Meta-Framework",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://github.com/assegura/erpnext-test-automation",
            "Report a bug": "https://github.com/assegura/erpnext-test-automation/issues",
            "About": (
                "ERPNext Test Automation Meta-Framework v1.0.0\n\n"
                "Constitutional Compliance:\n"
                "✓ DDD Architecture\n"
                "✓ Python 3.11+\n"
                "✓ NON-NEGOTIABLE Streamlit UI\n"
                "✓ Robot Framework Testing\n"
                "✓ Git Workflow"
            )
        }
    )


def initialize_session_state() -> None:
    """Initialize Streamlit session state variables.
    
    Sets up session state for navigation, API connection status,
    and user authentication (placeholder for future implementation).
    """
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"
    
    if "api_connected" not in st.session_state:
        st.session_state.api_connected = False
    
    if "api_client" not in st.session_state:
        st.session_state.api_client = None
    
    if "user_authenticated" not in st.session_state:
        st.session_state.user_authenticated = False
    
    if "selected_persona" not in st.session_state:
        st.session_state.selected_persona = None
    
    if "selected_activity" not in st.session_state:
        st.session_state.selected_activity = None
    
    if "selected_journey" not in st.session_state:
        st.session_state.selected_journey = None


def check_api_connection() -> bool:
    """Check connection to FastAPI backend.
    
    Returns:
        True if API is accessible, False otherwise
    """
    try:
        api_client = APIClient()
        health_data = api_client.get_health()
        
        if health_data and health_data.get("status") == "healthy":
            st.session_state.api_connected = True
            st.session_state.api_client = api_client
            return True
        else:
            st.session_state.api_connected = False
            return False
    
    except (ConnectionError, RequestException) as e:
        logger.warning(f"API connection failed: {e}")
        st.session_state.api_connected = False
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking API: {e}")
        st.session_state.api_connected = False
        return False


def show_api_connection_status() -> None:
    """Display API connection status in the UI.
    
    Shows connection status with appropriate styling and allows
    for manual reconnection attempts.
    """
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.session_state.api_connected:
            st.success("🟢 API Connected")
        else:
            st.error("🔴 API Disconnected")
    
    with col2:
        if st.button("🔄 Reconnect", help="Check API connection"):
            with st.spinner("Checking connection..."):
                check_api_connection()
                st.rerun()
    
    with col3:
        if not st.session_state.api_connected:
            st.warning("Start the backend API server to enable full functionality")


def render_navigation() -> str:
    """Render navigation and return selected page.
    
    Returns:
        Selected page name from navigation
    """
    pages = {
        "🏠 Dashboard": "Dashboard",
        "👥 Test Personas": "Personas", 
        "⚡ Business Activities": "Activities",
        "🗺️ User Journeys": "Journeys",
        "🤖 Test Generation": "Test Generation"
    }
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        
        selected = st.radio(
            "Go to:",
            options=list(pages.keys()),
            index=list(pages.values()).index(st.session_state.current_page) 
            if st.session_state.current_page in pages.values() else 0,
            label_visibility="collapsed"
        )
        
        selected_page = pages[selected]
        st.session_state.current_page = selected_page
        
        # Render sidebar components
        render_sidebar()
    
    return selected_page


def main() -> None:
    """Main application entry point.
    
    Orchestrates the Streamlit application flow following constitutional
    requirements and DDD architecture principles.
    """
    try:
        # Configure page
        configure_page()
        
        # Initialize session state
        initialize_session_state()
        
        # Check API connection
        check_api_connection()
        
        # Render header
        render_header()
        
        # Show API connection status
        show_api_connection_status()
        
        # Add spacing
        st.markdown("---")
        
        # Render navigation and get selected page
        selected_page = render_navigation()
        
        # Render selected page content
        if selected_page == "Dashboard":
            show_dashboard()
        elif selected_page == "Personas":
            show_personas()
        elif selected_page == "Activities":
            show_activities()
        elif selected_page == "Journeys":
            show_journeys()
        elif selected_page == "Test Generation":
            show_test_generation()
        else:
            st.error(f"Unknown page: {selected_page}")
            show_dashboard()
    
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        st.error("An unexpected error occurred. Please check the logs and try again.")
        
        # Show error details in expander for debugging
        with st.expander("Error Details (for debugging)"):
            st.exception(e)


if __name__ == "__main__":
    # Run the Streamlit application
    # Use: streamlit run frontend/src/main.py
    main()