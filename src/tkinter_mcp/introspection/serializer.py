"""Widget tree serialization for introspection."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from tkinter_mcp.introspection.models import UILayout, WidgetGeometry, WidgetInfo

if TYPE_CHECKING:
    import tkinter as tk


def get_widget_class_name(widget: tk.Widget) -> str:
    """Extract the class name from a Tkinter widget.

    Args:
        widget: A Tkinter widget instance

    Returns:
        The widget class name (e.g., 'Button', 'Label', 'Frame')
    """
    return widget.winfo_class()


def get_widget_text(widget: tk.Widget) -> str | None:
    """Extract text content from a widget if applicable.

    Args:
        widget: A Tkinter widget instance

    Returns:
        Text content or None if widget has no text
    """
    try:
        return widget.cget("text")  # type: ignore[union-attr]
    except Exception:
        pass

    try:
        if hasattr(widget, "get"):
            text = widget.get("1.0", "end-1c")  # type: ignore[union-attr]
            if text:
                return text
    except Exception:
        pass

    try:
        if hasattr(widget, "get"):
            text = widget.get()  # type: ignore[union-attr]
            if text:
                return text
    except Exception:
        pass

    return None


def get_widget_state(widget: tk.Widget) -> str:
    """Get the current state of a widget.

    Args:
        widget: A Tkinter widget instance

    Returns:
        Widget state string (e.g., 'normal', 'disabled')
    """
    try:
        state = widget.cget("state")  # type: ignore[union-attr]
        return str(state) if state else "normal"
    except Exception:
        return "normal"


def serialize_widget(widget: tk.Widget) -> WidgetInfo:
    """Serialize a single widget and its children recursively.

    Args:
        widget: A Tkinter widget instance

    Returns:
        WidgetInfo containing widget data and nested children
    """
    widget.update_idletasks()

    geometry = WidgetGeometry(
        x=widget.winfo_x(),
        y=widget.winfo_y(),
        width=widget.winfo_width(),
        height=widget.winfo_height(),
    )

    children = [serialize_widget(child) for child in widget.winfo_children()]

    return WidgetInfo(
        widget_class=get_widget_class_name(widget),
        widget_id=widget.winfo_id(),
        name=widget.winfo_name(),
        geometry=geometry,
        state=get_widget_state(widget),
        text=get_widget_text(widget),
        is_mapped=widget.winfo_ismapped() == 1,
        children=children,
    )


def serialize_widget_tree(root: tk.Tk) -> UILayout:
    """Serialize the complete widget tree from root.

    Args:
        root: The Tkinter root window

    Returns:
        UILayout containing the full widget hierarchy
    """
    root.update_idletasks()

    return UILayout(
        window_title=root.title(),
        root=serialize_widget(root),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def find_widget_by_id(root: tk.Widget, widget_id: int) -> tk.Widget | None:
    """Find a widget by its winfo_id.

    Args:
        root: The root widget to search from
        widget_id: The widget ID to find

    Returns:
        The widget if found, None otherwise
    """
    if root.winfo_id() == widget_id:
        return root

    for child in root.winfo_children():
        result = find_widget_by_id(child, widget_id)
        if result is not None:
            return result

    return None


def find_widget_by_text(root: tk.Widget, text: str) -> tk.Widget | None:
    """Find a widget by its text content.

    Args:
        root: The root widget to search from
        text: The text to search for

    Returns:
        The first widget with matching text, or None
    """
    widget_text = get_widget_text(root)
    if isinstance(widget_text, str) and text in widget_text:
        return root

    for child in root.winfo_children():
        result = find_widget_by_text(child, text)
        if result is not None:
            return result

    return None
