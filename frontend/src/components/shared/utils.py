"""Shared utility functions for frontend components.

This module provides utility functions for formatting dates, times,
and other common data transformations used across the frontend.
"""

from datetime import datetime, timedelta
from typing import Any, Optional, Union


def format_datetime(dt: Optional[Union[datetime, str]]) -> str:
    """Format datetime for display.
    
    Args:
        dt: Datetime object or ISO string to format
        
    Returns:
        Formatted datetime string
    """
    if dt is None:
        return "Not set"
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return dt  # Return original string if parsing fails
    
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_duration(minutes: Optional[Union[int, float]]) -> str:
    """Format duration in minutes to human readable format.
    
    Args:
        minutes: Duration in minutes
        
    Returns:
        Formatted duration string
    """
    if minutes is None:
        return "Not set"
    
    if minutes < 60:
        return f"{int(minutes)} minutes"
    
    hours = int(minutes // 60)
    remaining_minutes = int(minutes % 60)
    
    if remaining_minutes == 0:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    
    return f"{hours}h {remaining_minutes}m"


def format_file_size(bytes_size: Optional[int]) -> str:
    """Format file size in bytes to human readable format.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted file size string
    """
    if bytes_size is None:
        return "Unknown"
    
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.1f} GB"


def truncate_text(text: Optional[str], max_length: int = 100) -> str:
    """Truncate text to maximum length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if text is None:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."