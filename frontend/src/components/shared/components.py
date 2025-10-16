"""Shared UI components for Streamlit frontend.

This module provides reusable UI components and utility functions
for displaying messages, confirmations, and common interface elements.
"""

import streamlit as st
from typing import Any, Optional


def show_error_message(message: str) -> None:
    """Display an error message to the user.
    
    Args:
        message: Error message to display
    """
    st.error(message)


def show_success_message(message: str) -> None:
    """Display a success message to the user.
    
    Args:
        message: Success message to display
    """
    st.success(message)


def show_warning_message(message: str) -> None:
    """Display a warning message to the user.
    
    Args:
        message: Warning message to display
    """
    st.warning(message)


def show_info_message(message: str) -> None:
    """Display an info message to the user.
    
    Args:
        message: Info message to display
    """
    st.info(message)


def confirm_action(message: str, key: Optional[str] = None) -> bool:
    """Display a confirmation dialog and return user choice.
    
    Args:
        message: Confirmation message to display
        key: Unique key for the widget
        
    Returns:
        True if user confirms, False otherwise
    """
    if key is None:
        key = f"confirm_{hash(message)}"
    
    return st.button(f"Confirm: {message}", key=key, type="secondary")