"""FastMCP server for Tkinter GUI introspection."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from fastmcp import FastMCP

from tkinter_mcp.bridge.protocol import DEFAULT_HOST, DEFAULT_PORT
from tkinter_mcp.bridge.remote import RemoteBridge, RemoteBridgeError


def create_mcp_server() -> FastMCP:
    """Create and configure the standalone MCP server.

    Returns:
        Configured FastMCP server instance
    """
    mcp = FastMCP(name="Tkinter MCP Server")

    # Shared state
    bridge: RemoteBridge | None = None
    app_process: subprocess.Popen | None = None

    def get_bridge() -> RemoteBridge:
        """Get connected bridge or raise error."""
        nonlocal bridge
        if bridge is None or not bridge.is_connected():
            raise RemoteBridgeError("No app connected. Use launch_app first.")
        return bridge

    @mcp.tool
    def launch_app(script_path: str) -> str:
        """Launch a Tkinter application with inspection enabled.

        Starts the script with automatic Tkinter patching. The app
        will be inspectable via the other tools once launched.

        Args:
            script_path: Path to the Python script to run

        Returns:
            JSON with success status and message
        """
        nonlocal bridge, app_process

        path = Path(script_path).resolve()
        if not path.exists():
            return json.dumps(
                {
                    "success": False,
                    "message": f"Script not found: {script_path}",
                }
            )

        # Close existing app if any
        if app_process is not None:
            try:
                app_process.terminate()
                app_process.wait(timeout=2)
            except Exception:
                pass

        if bridge is not None:
            bridge.disconnect()
            bridge = None

        # Launch the app with our launcher
        app_process = subprocess.Popen(
            [sys.executable, "-m", "tkinter_mcp.launcher", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for agent to start and connect
        bridge = RemoteBridge(host=DEFAULT_HOST, port=DEFAULT_PORT)

        for _ in range(50):  # 5 second timeout
            if bridge.connect(timeout=0.1):
                return json.dumps(
                    {
                        "success": True,
                        "message": f"Launched {path.name}",
                        "pid": app_process.pid,
                    }
                )
            time.sleep(0.1)

        # Cleanup on failure
        app_process.terminate()
        app_process = None
        bridge = None

        return json.dumps(
            {
                "success": False,
                "message": "Failed to connect to app agent",
            }
        )

    @mcp.tool
    def get_ui_layout() -> str:
        """Get the current UI layout as hierarchical JSON.

        Returns a JSON structure containing the complete widget tree with:
        - widget class names (Button, Label, Frame, etc.)
        - unique widget IDs
        - geometry (x, y, width, height)
        - widget state (normal, disabled)
        - text content where applicable
        - nested children

        Use this to understand the current state of the GUI.
        """
        try:
            layout = get_bridge().get_ui_layout()
            return json.dumps(layout.to_dict(), indent=2)
        except RemoteBridgeError as e:
            return json.dumps({"error": str(e)})

    @mcp.tool
    def view_application(max_size: int = 800, quality: int = 70) -> str:
        """Take a screenshot of the application window.

        Returns a base64-encoded JPEG image of the current window state.
        Use this to visually inspect the GUI appearance.

        Args:
            max_size: Maximum width/height in pixels (default 800)
            quality: JPEG quality 1-100 (default 70)

        Returns:
            Base64-encoded JPEG string prefixed with data URI scheme.
        """
        try:
            screenshot_b64 = get_bridge().capture_screenshot(max_size, quality)
            return f"data:image/jpeg;base64,{screenshot_b64.decode('utf-8')}"
        except RemoteBridgeError as e:
            return json.dumps({"error": str(e)})

    @mcp.tool
    def view_application_thumbnail() -> str:
        """Take a small thumbnail screenshot of the application window.

        Returns a low-resolution preview for quick UI state checks.
        Use view_application for detailed inspection.

        Returns:
            Base64-encoded JPEG string prefixed with data URI scheme.
        """
        try:
            screenshot_b64 = get_bridge().capture_screenshot(400, 30)
            return f"data:image/jpeg;base64,{screenshot_b64.decode('utf-8')}"
        except RemoteBridgeError as e:
            return json.dumps({"error": str(e)})

    @mcp.tool
    def get_window_info() -> str:
        """Get basic information about the application window.

        Returns JSON with window position and dimensions:
        - x, y: Window position on screen
        - width, height: Window dimensions in pixels

        Useful for understanding window placement.
        """
        try:
            geometry = get_bridge().get_window_geometry()
            return json.dumps(geometry, indent=2)
        except RemoteBridgeError as e:
            return json.dumps({"error": str(e)})

    @mcp.tool
    def click_widget(
        widget_id: int,
        button: str = "left",
        double: bool = False,
    ) -> str:
        """Click a widget by its ID.

        Finds the widget with the given ID and triggers a click action.
        For buttons, this invokes the button command.
        For other widgets, this generates a click event.

        Args:
            widget_id: The widget ID from get_ui_layout()
            button: Mouse button - "left", "right", or "middle"
            double: If True, perform a double-click

        Returns:
            JSON with success status and message
        """
        try:
            success = get_bridge().click_widget(widget_id, button, double)
            return json.dumps(
                {
                    "success": success,
                    "message": "Widget clicked" if success else "Widget not found",
                }
            )
        except RemoteBridgeError as e:
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool
    def type_text(widget_id: int, text: str) -> str:
        """Type text into an Entry or Text widget.

        Clears the current content and inserts the new text.
        Only works with Entry and Text widgets.

        Args:
            widget_id: The widget ID from get_ui_layout()
            text: The text to type into the widget

        Returns:
            JSON with success status and message
        """
        try:
            success = get_bridge().type_text(widget_id, text)
            msg = "Text entered" if success else "Widget not found or not editable"
            return json.dumps({"success": success, "message": msg})
        except RemoteBridgeError as e:
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool
    def get_widget_by_text(text: str) -> str:
        """Find a widget by its text content.

        Searches the widget tree for a widget containing the specified text.
        Returns the widget ID if found.

        Args:
            text: The text to search for

        Returns:
            JSON with widget_id if found, or null if not found
        """
        try:
            widget_id = get_bridge().find_widget_id_by_text(text)
            return json.dumps(
                {
                    "found": widget_id is not None,
                    "widget_id": widget_id,
                }
            )
        except RemoteBridgeError as e:
            return json.dumps({"found": False, "error": str(e)})

    @mcp.tool
    def close_app() -> str:
        """Close the currently running Tkinter application.

        Terminates the app gracefully.

        Returns:
            JSON with success status
        """
        nonlocal bridge, app_process

        try:
            if bridge is not None:
                bridge.close_app()
                bridge = None

            if app_process is not None:
                try:
                    app_process.terminate()
                    app_process.wait(timeout=2)
                except Exception:
                    app_process.kill()
                app_process = None

            return json.dumps({"success": True, "message": "App closed"})
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool
    def is_connected() -> str:
        """Check if an app is currently connected.

        Returns:
            JSON with connection status
        """
        connected = bridge is not None and bridge.is_connected()
        return json.dumps(
            {
                "connected": connected,
                "pid": app_process.pid if app_process else None,
            }
        )

    @mcp.tool
    def focus_widget(widget_id: int) -> str:
        """Set keyboard focus to a widget.

        Args:
            widget_id: The widget ID from get_ui_layout()

        Returns:
            JSON with success status and message
        """
        try:
            success = get_bridge().focus_widget(widget_id)
            msg = "Widget focused" if success else "Widget not found"
            return json.dumps({"success": success, "message": msg})
        except RemoteBridgeError as e:
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool
    def get_focused_widget() -> str:
        """Get the currently focused widget.

        Returns:
            JSON with the focused widget's ID or null if no widget has focus
        """
        try:
            widget_id = get_bridge().get_focused_widget()
            return json.dumps(
                {
                    "has_focus": widget_id is not None,
                    "widget_id": widget_id,
                }
            )
        except RemoteBridgeError as e:
            return json.dumps({"has_focus": False, "error": str(e)})

    @mcp.tool
    def get_widget_value(widget_id: int) -> str:
        """Get the value of a widget based on its type.

        Returns the appropriate value for the widget type:
        - Entry/Text: text content
        - Scale: numeric value
        - Combobox: selected text
        - Checkbutton: boolean (checked/unchecked)
        - Radiobutton: variable value
        - Listbox: list of selected item texts
        - Spinbox: current value

        Args:
            widget_id: The widget ID from get_ui_layout()

        Returns:
            JSON with the widget value or null
        """
        try:
            value = get_bridge().get_widget_value(widget_id)
            return json.dumps(
                {
                    "found": value is not None,
                    "value": value,
                }
            )
        except RemoteBridgeError as e:
            return json.dumps({"found": False, "error": str(e)})

    @mcp.tool
    def set_widget_value(widget_id: int, value: str) -> str:
        """Set the value of a widget based on its type.

        Sets the appropriate value for the widget type:
        - Entry/Text: sets text content
        - Scale: sets numeric value (e.g., "50.0")
        - Combobox: sets selected text
        - Checkbutton: sets checked state ("true"/"false")
        - Radiobutton: selects this radio button (value ignored)
        - Listbox: selects item by index (e.g., "0", "1")
        - Spinbox: sets value

        Args:
            widget_id: The widget ID from get_ui_layout()
            value: The value to set (converted appropriately for widget type)

        Returns:
            JSON with success status and message
        """
        try:
            success = get_bridge().set_widget_value(widget_id, value)
            msg = "Value set" if success else "Widget not found or not settable"
            return json.dumps({"success": success, "message": msg})
        except RemoteBridgeError as e:
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool
    def get_widget_options(widget_id: int) -> str:
        """Get available options for a Combobox or Listbox widget.

        Returns the list of selectable options/items.

        Args:
            widget_id: The widget ID from get_ui_layout()

        Returns:
            JSON with list of options or null if not a Combobox/Listbox
        """
        try:
            options = get_bridge().get_widget_options(widget_id)
            return json.dumps(
                {
                    "found": options is not None,
                    "options": options,
                }
            )
        except RemoteBridgeError as e:
            return json.dumps({"found": False, "error": str(e)})

    @mcp.tool
    def drag_widget(start_widget_id: int, end_widget_id: int) -> str:
        """Perform drag and drop between two widgets.

        Simulates dragging from one widget to another. Useful for
        drag-and-drop interfaces like chess boards, sortable lists, etc.

        Args:
            start_widget_id: The widget ID to drag from
            end_widget_id: The widget ID to drag to

        Returns:
            JSON with success status and message
        """
        try:
            success = get_bridge().drag_widget(start_widget_id, end_widget_id)
            msg = "Drag completed" if success else "Widget not found"
            return json.dumps({"success": success, "message": msg})
        except RemoteBridgeError as e:
            return json.dumps({"success": False, "error": str(e)})

    return mcp
