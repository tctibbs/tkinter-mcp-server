"""Bridge between MCP server and Tkinter application."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from tkinter_mcp.bridge.thread_safe import execute_on_main_thread, is_main_thread
from tkinter_mcp.introspection.models import UILayout
from tkinter_mcp.introspection.screenshot import capture_window_screenshot
from tkinter_mcp.introspection.serializer import (
    find_widget_by_id,
    find_widget_by_text,
    serialize_widget_tree,
)

if TYPE_CHECKING:
    import tkinter as tk


class AppBridge:
    """Thread-safe bridge for accessing Tkinter application from MCP server.

    This class provides a safe interface for the MCP server (running in a
    background thread) to introspect and interact with the Tkinter application
    (running in the main thread).

    Args:
        root: The Tkinter root window reference
    """

    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._lock = threading.Lock()

    @property
    def root(self) -> tk.Tk:
        """Access to root window (for main thread operations)."""
        return self._root

    def get_ui_layout(self) -> UILayout:
        """Get the current UI layout as structured data.

        Thread-safe method that captures the widget hierarchy.

        Returns:
            UILayout containing the complete widget tree
        """
        if is_main_thread():
            return serialize_widget_tree(self._root)

        return execute_on_main_thread(
            self._root,
            lambda: serialize_widget_tree(self._root),
        )

    def capture_screenshot(self) -> bytes:
        """Capture a screenshot of the application window.

        Thread-safe method that takes a screenshot and returns PNG bytes.

        Returns:
            Base64-encoded PNG image data as bytes
        """
        if is_main_thread():
            return capture_window_screenshot(self._root)

        return execute_on_main_thread(
            self._root,
            lambda: capture_window_screenshot(self._root),
        )

    def get_window_geometry(self) -> dict[str, int]:
        """Get the current window position and size.

        Returns:
            Dictionary with x, y, width, height keys
        """

        def _get_geometry() -> dict[str, int]:
            self._root.update_idletasks()
            return {
                "x": self._root.winfo_x(),
                "y": self._root.winfo_y(),
                "width": self._root.winfo_width(),
                "height": self._root.winfo_height(),
            }

        if is_main_thread():
            return _get_geometry()

        return execute_on_main_thread(self._root, _get_geometry)

    def click_widget(self, widget_id: int) -> bool:
        """Click a widget by its ID.

        Thread-safe method that finds a widget and invokes its click action.

        Args:
            widget_id: The winfo_id() of the widget to click

        Returns:
            True if widget was found and clicked, False otherwise
        """

        def _click() -> bool:
            widget = find_widget_by_id(self._root, widget_id)
            if widget is None:
                return False

            if hasattr(widget, "invoke"):
                widget.invoke()  # type: ignore[union-attr]
                return True

            widget.event_generate("<Button-1>")
            widget.event_generate("<ButtonRelease-1>")
            return True

        if is_main_thread():
            return _click()

        return execute_on_main_thread(self._root, _click)

    def type_text(self, widget_id: int, text: str) -> bool:
        """Type text into an Entry or Text widget.

        Thread-safe method that finds a widget and inserts text.

        Args:
            widget_id: The winfo_id() of the widget
            text: The text to type

        Returns:
            True if widget was found and text was typed, False otherwise
        """

        def _type() -> bool:
            widget = find_widget_by_id(self._root, widget_id)
            if widget is None:
                return False

            widget_class = widget.winfo_class()

            if widget_class == "Entry":
                widget.delete(0, "end")  # type: ignore[union-attr]
                widget.insert(0, text)  # type: ignore[union-attr]
                return True

            if widget_class == "Text":
                widget.delete("1.0", "end")  # type: ignore[union-attr]
                widget.insert("1.0", text)  # type: ignore[union-attr]
                return True

            return False

        if is_main_thread():
            return _type()

        return execute_on_main_thread(self._root, _type)

    def find_widget_id_by_text(self, text: str) -> int | None:
        """Find a widget by its text content.

        Thread-safe method that searches the widget tree for matching text.

        Args:
            text: The text to search for

        Returns:
            The widget ID if found, None otherwise
        """

        def _find() -> int | None:
            widget = find_widget_by_text(self._root, text)
            if widget is not None:
                return widget.winfo_id()
            return None

        if is_main_thread():
            return _find()

        return execute_on_main_thread(self._root, _find)
