"""Shared Streamlit components library.

Provides reusable UI components for the ERPNext Test Automation Meta-Framework
frontend with consistent styling and behavior across all pages.
"""

import logging
from collections.abc import Callable
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

logger = logging.getLogger(__name__)


def success_message(message: str, icon: str = "✅") -> None:
    """Display a success message with consistent styling.

    Args:
        message: Success message to display
        icon: Icon to show alongside message
    """
    st.success(f"{icon} {message}")


def error_message(message: str, icon: str = "❌") -> None:
    """Display an error message with consistent styling.

    Args:
        message: Error message to display
        icon: Icon to show alongside message
    """
    st.error(f"{icon} {message}")


def warning_message(message: str, icon: str = "⚠️") -> None:
    """Display a warning message with consistent styling.

    Args:
        message: Warning message to display
        icon: Icon to show alongside message
    """
    st.warning(f"{icon} {message}")


def info_message(message: str, icon: str = "ℹ️") -> None:
    """Display an info message with consistent styling.

    Args:
        message: Info message to display
        icon: Icon to show alongside message
    """
    st.info(f"{icon} {message}")


def loading_spinner(text: str = "Loading...") -> Any:
    """Create a loading spinner with custom text.

    Args:
        text: Loading text to display

    Returns:
        Streamlit spinner context manager
    """
    return st.spinner(text)


def confirmation_dialog(
    message: str,
    confirm_text: str = "Confirm",
    cancel_text: str = "Cancel",
    key: Optional[str] = None,
) -> Optional[bool]:
    """Display a confirmation dialog with Yes/No buttons.

    Args:
        message: Confirmation message
        confirm_text: Text for confirm button
        cancel_text: Text for cancel button
        key: Unique key for the dialog

    Returns:
        True if confirmed, False if cancelled, None if no action
    """
    st.write(message)

    col1, col2 = st.columns(2)

    confirmed = None
    with col1:
        if st.button(confirm_text, key=f"{key}_confirm" if key else None):
            confirmed = True

    with col2:
        if st.button(cancel_text, key=f"{key}_cancel" if key else None):
            confirmed = False

    return confirmed


def data_table(
    data: list[dict[str, Any]],
    columns: Optional[list[str]] = None,
    sortable: bool = True,
    selectable: bool = False,
    key: Optional[str] = None,
) -> Optional[list[int]]:
    """Display a data table with optional sorting and selection.

    Args:
        data: List of dictionaries to display
        columns: Column names to display (if None, uses all keys)
        sortable: Whether to enable column sorting
        selectable: Whether to enable row selection
        key: Unique key for the table

    Returns:
        List of selected row indices if selectable, None otherwise
    """
    if not data:
        st.write("No data to display")
        return None

    # Create DataFrame
    import pandas as pd

    df = pd.DataFrame(data)

    if columns:
        df = df[columns]

    if selectable:
        # Add selection column
        selected_rows = st.multiselect(
            "Select rows:",
            options=range(len(df)),
            format_func=lambda x: f"Row {x + 1}",
            key=key,
        )

        if selected_rows:
            st.write("Selected data:")
            st.dataframe(df.iloc[selected_rows])

        return selected_rows
    else:
        st.dataframe(df, use_container_width=True)
        return None


def form_field(
    label: str,
    field_type: str = "text",
    value: Any = None,
    options: Optional[list[Any]] = None,
    required: bool = False,
    help_text: Optional[str] = None,
    key: Optional[str] = None,
    **kwargs,
) -> Any:
    """Create a form field with consistent styling and validation.

    Args:
        label: Field label
        field_type: Type of field (text, number, select, multiselect, checkbox, date)
        value: Default value
        options: Options for select/multiselect fields
        required: Whether field is required
        help_text: Help text to display
        key: Unique key for the field
        **kwargs: Additional arguments for the field

    Returns:
        Field value
    """
    label_text = f"{label} {'*' if required else ''}"

    if field_type == "text":
        return st.text_input(
            label_text, value=value or "", help=help_text, key=key, **kwargs
        )
    elif field_type == "textarea":
        return st.text_area(
            label_text, value=value or "", help=help_text, key=key, **kwargs
        )
    elif field_type == "number":
        return st.number_input(
            label_text, value=value or 0, help=help_text, key=key, **kwargs
        )
    elif field_type == "select":
        return st.selectbox(
            label_text,
            options=options or [],
            index=0
            if value is None
            else options.index(value)
            if value in options
            else 0,
            help=help_text,
            key=key,
            **kwargs,
        )
    elif field_type == "multiselect":
        return st.multiselect(
            label_text,
            options=options or [],
            default=value or [],
            help=help_text,
            key=key,
            **kwargs,
        )
    elif field_type == "checkbox":
        return st.checkbox(
            label_text, value=bool(value), help=help_text, key=key, **kwargs
        )
    elif field_type == "date":
        return st.date_input(
            label_text,
            value=value or datetime.now().date(),
            help=help_text,
            key=key,
            **kwargs,
        )
    elif field_type == "file":
        return st.file_uploader(label_text, help=help_text, key=key, **kwargs)
    else:
        st.error(f"Unknown field type: {field_type}")
        return None


def action_buttons(
    actions: list[dict[str, Any]], key: Optional[str] = None
) -> Optional[str]:
    """Create a row of action buttons.

    Args:
        actions: List of action dictionaries with 'label', 'key', and optional 'type'
        key: Base key for the buttons

    Returns:
        Key of the clicked button, None if no button clicked
    """
    if not actions:
        return None

    cols = st.columns(len(actions))

    for i, action in enumerate(actions):
        with cols[i]:
            button_type = action.get("type", "primary")
            if button_type == "primary":
                if st.button(
                    action["label"],
                    key=f"{key}_{action['key']}" if key else action["key"],
                ):
                    return action["key"]
            elif button_type == "secondary":
                if st.button(
                    action["label"],
                    key=f"{key}_{action['key']}" if key else action["key"],
                    type="secondary",
                ):
                    return action["key"]

    return None


def status_badge(status: str, color_map: Optional[dict[str, str]] = None) -> None:
    """Display a status badge with color coding.

    Args:
        status: Status text
        color_map: Mapping of status to colors (default provides common statuses)
    """
    default_colors = {
        "active": "green",
        "inactive": "red",
        "pending": "orange",
        "completed": "green",
        "failed": "red",
        "running": "blue",
        "draft": "gray",
    }

    colors = color_map or default_colors
    color = colors.get(status.lower(), "gray")

    # Create colored badge using HTML
    st.markdown(
        f'<span style="background-color: {color}; color: white; padding: 2px 8px; '
        f'border-radius: 12px; font-size: 12px; font-weight: bold;">{status}</span>',
        unsafe_allow_html=True,
    )


def progress_bar(
    current: int, total: int, label: str = "", show_percentage: bool = True
) -> None:
    """Display a progress bar with optional label and percentage.

    Args:
        current: Current progress value
        total: Total value
        label: Progress label
        show_percentage: Whether to show percentage text
    """
    progress = current / total if total > 0 else 0

    if label:
        st.write(label)

    st.progress(progress)

    if show_percentage:
        st.write(f"{current}/{total} ({progress:.1%})")


def expandable_section(
    title: str,
    content_func: Callable[[], None],
    expanded: bool = False,
    key: Optional[str] = None,
) -> None:
    """Create an expandable section with custom content.

    Args:
        title: Section title
        content_func: Function that renders the content when expanded
        expanded: Whether section is expanded by default
        key: Unique key for the expander
    """
    with st.expander(title, expanded=expanded, key=key):
        content_func()


def metric_card(
    title: str, value: str, delta: Optional[str] = None, delta_color: str = "normal"
) -> None:
    """Display a metric card with title, value, and optional delta.

    Args:
        title: Metric title
        value: Current value
        delta: Change value (optional)
        delta_color: Color for delta (normal, inverse)
    """
    st.metric(label=title, value=value, delta=delta, delta_color=delta_color)


def tabs_container(tabs: list[dict[str, Any]], key: Optional[str] = None) -> None:
    """Create a tabbed container with multiple content sections.

    Args:
        tabs: List of tab dictionaries with 'title' and 'content_func'
        key: Unique key for the tabs
    """
    if not tabs:
        return

    tab_titles = [tab["title"] for tab in tabs]
    tab_objects = st.tabs(tab_titles)

    for i, (tab_obj, tab_config) in enumerate(zip(tab_objects, tabs)):
        with tab_obj:
            tab_config["content_func"]()


# CSS styling for enhanced UI
def apply_custom_css() -> None:
    """Apply custom CSS styling to the Streamlit app."""
    st.markdown(
        """
    <style>
    /* Custom button styling */
    .stButton > button {
        border-radius: 8px;
        border: 1px solid #ddd;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    /* Form styling */
    .stTextInput > div > div > input {
        border-radius: 6px;
    }

    .stSelectbox > div > div > select {
        border-radius: 6px;
    }

    /* Table styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Success/Error message styling */
    .stAlert {
        border-radius: 8px;
        border-left: 4px solid;
    }

    /* Sidebar styling */
    .css-1d391kg {
        padding-top: 1rem;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )
