"""Shared form components for Streamlit frontend.

This module provides reusable form input components with consistent
styling and validation across the application.
"""

import streamlit as st
from typing import Any, Dict, List, Optional, Union


def render_text_input(
    label: str,
    value: str = "",
    placeholder: str = "",
    help: Optional[str] = None,
    key: Optional[str] = None,
    disabled: bool = False,
    max_chars: Optional[int] = None,
    required: bool = False,
) -> str:
    """Render a text input field.
    
    Args:
        label: Input label
        value: Default value
        placeholder: Placeholder text
        help: Help text
        key: Unique key for the widget
        disabled: Whether the input is disabled
        max_chars: Maximum number of characters
        required: Whether the field is required (visual indicator only)
        
    Returns:
        User input value
    """
    # Add asterisk for required fields
    display_label = f"{label} *" if required else label
    
    return st.text_input(
        label=display_label,
        value=value,
        placeholder=placeholder,
        help=help,
        key=key,
        disabled=disabled,
        max_chars=max_chars,
    )


def render_text_area(
    label: str,
    value: str = "",
    placeholder: str = "",
    help: Optional[str] = None,
    key: Optional[str] = None,
    disabled: bool = False,
    height: Optional[int] = None,
    max_chars: Optional[int] = None,
    required: bool = False,
) -> str:
    """Render a text area input field.
    
    Args:
        label: Input label
        value: Default value
        placeholder: Placeholder text
        help: Help text
        key: Unique key for the widget
        disabled: Whether the input is disabled
        height: Height in pixels
        max_chars: Maximum number of characters
        required: Whether the field is required (visual indicator only)
        
    Returns:
        User input value
    """
    # Add asterisk for required fields
    display_label = f"{label} *" if required else label
    
    return st.text_area(
        label=display_label,
        value=value,
        placeholder=placeholder,
        help=help,
        key=key,
        disabled=disabled,
        height=height,
        max_chars=max_chars,
    )


def render_number_input(
    label: str,
    value: Union[int, float] = 0,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    step: Union[int, float] = 1,
    help: Optional[str] = None,
    key: Optional[str] = None,
    disabled: bool = False,
    required: bool = False,
) -> Union[int, float]:
    """Render a number input field.
    
    Args:
        label: Input label
        value: Default value
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        step: Step size
        help: Help text
        key: Unique key for the widget
        disabled: Whether the input is disabled
        required: Whether the field is required (visual indicator only)
        
    Returns:
        User input value
    """
    # Add asterisk for required fields
    display_label = f"{label} *" if required else label
    
    return st.number_input(
        label=display_label,
        value=value,
        min_value=min_value,
        max_value=max_value,
        step=step,
        help=help,
        key=key,
        disabled=disabled,
    )


def render_select_box(
    label: str,
    options: List[Any],
    index: int = 0,
    value: Optional[Any] = None,
    help: Optional[str] = None,
    key: Optional[str] = None,
    disabled: bool = False,
    required: bool = False,
) -> Any:
    """Render a select box input field.
    
    Args:
        label: Input label
        options: List of options to choose from
        index: Default selected index
        value: Default selected value (overrides index if provided)
        help: Help text
        key: Unique key for the widget
        disabled: Whether the input is disabled
        required: Whether the field is required (visual indicator only)
        
    Returns:
        Selected option value
    """
    # Add asterisk for required fields
    display_label = f"{label} *" if required else label
    
    # If value is provided, find its index in options
    if value is not None and value in options:
        index = options.index(value)
    
    return st.selectbox(
        label=display_label,
        options=options,
        index=index,
        help=help,
        key=key,
        disabled=disabled,
    )


def render_multiselect(
    label: str,
    options: List[Any],
    default: Optional[List[Any]] = None,
    help: Optional[str] = None,
    key: Optional[str] = None,
    disabled: bool = False,
) -> List[Any]:
    """Render a multiselect input field.
    
    Args:
        label: Input label
        options: List of options to choose from
        default: Default selected values
        help: Help text
        key: Unique key for the widget
        disabled: Whether the input is disabled
        
    Returns:
        List of selected values
    """
    return st.multiselect(
        label=label,
        options=options,
        default=default or [],
        help=help,
        key=key,
        disabled=disabled,
    )


def render_checkbox(
    label: str,
    value: bool = False,
    help: Optional[str] = None,
    key: Optional[str] = None,
    disabled: bool = False,
) -> bool:
    """Render a checkbox input field.
    
    Args:
        label: Input label
        value: Default value
        help: Help text
        key: Unique key for the widget
        disabled: Whether the input is disabled
        
    Returns:
        Checkbox state
    """
    return st.checkbox(
        label=label,
        value=value,
        help=help,
        key=key,
        disabled=disabled,
    )