"""
Shared loading spinner utilities for the frontend application.
"""

import streamlit as st
from contextlib import contextmanager
from typing import Any, Iterator, Optional


@contextmanager
def show_loading_spinner(message: str = "Loading...") -> Iterator[None]:
    """
    Context manager for showing a loading spinner during operations.

    Args:
        message: Message to display with the spinner

    Usage:
        with show_loading_spinner("Processing..."):
            do_something()
    """
    with st.spinner(message):
        yield


def show_progress_bar(current: int, total: int, text: str = "Progress") -> None:
    """
    Show a progress bar.

    Args:
        current: Current progress value
        total: Total progress value
        text: Text to display with progress bar
    """
    progress = min(current / total, 1.0) if total > 0 else 0
    st.progress(progress, text=f"{text}: {current}/{total}")


def show_status_message(message: str, status: str = "info") -> None:
    """
    Show a status message.

    Args:
        message: Message to display
        status: Status type ('info', 'success', 'warning', 'error')
    """
    if status == "success":
        st.success(message)
    elif status == "warning":
        st.warning(message)
    elif status == "error":
        st.error(message)
    else:
        st.info(message)