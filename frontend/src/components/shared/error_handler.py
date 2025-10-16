"""
Shared error handling utilities for the frontend application.
"""

import streamlit as st
from typing import Any, Optional


def handle_api_error(error: Exception, message: str = "An error occurred") -> None:
    """
    Handle API errors with user-friendly messages.

    Args:
        error: The exception that occurred
        message: Custom error message
    """
    st.error(f"{message}: {str(error)}")


def handle_validation_error(errors: dict[str, str]) -> None:
    """
    Handle validation errors by displaying them to the user.

    Args:
        errors: Dictionary of field names to error messages
    """
    for field, message in errors.items():
        st.error(f"{field}: {message}")


def show_error_alert(message: str, details: Optional[str] = None) -> None:
    """
    Show an error alert with optional details.

    Args:
        message: Main error message
        details: Optional detailed error information
    """
    with st.container():
        st.error(message)
        if details:
            with st.expander("Error Details"):
                st.code(details)