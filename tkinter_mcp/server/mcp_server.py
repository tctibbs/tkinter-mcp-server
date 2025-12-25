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
    def view_application() -> str:
        """Take a screenshot of the application window.

        Returns a base64-encoded PNG image of the current window state.
        Use this to visually inspect the GUI appearance.

        Returns:
            Base64-encoded PNG string prefixed with data URI scheme.
        """
        try:
            screenshot_b64 = get_bridge().capture_screenshot()
            return f"data:image/png;base64,{screenshot_b64.decode('utf-8')}"
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
    def click_widget(widget_id: int) -> str:
        """Click a widget by its ID.

        Finds the widget with the given ID and triggers a click action.
        For buttons, this invokes the button command.
        For other widgets, this generates a click event.

        Args:
            widget_id: The widget ID from get_ui_layout()

        Returns:
            JSON with success status and message
        """
        try:
            success = get_bridge().click_widget(widget_id)
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
    def toggle_checkbox(widget_id: int) -> str:
        """Toggle a Checkbutton widget on or off.

        Finds the Checkbutton with the given ID and toggles its state.
        Works with both standard tk.Checkbutton and ttk.Checkbutton.

        Args:
            widget_id: The widget ID from get_ui_layout()

        Returns:
            JSON with success status and message
        """
        try:
            success = get_bridge().toggle_checkbox(widget_id)
            msg = "Checkbox toggled" if success else "Not found or not a checkbox"
            return json.dumps({"success": success, "message": msg})
        except RemoteBridgeError as e:
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool
    def get_checkbox_state(widget_id: int) -> str:
        """Get the current checked state of a Checkbutton.

        Returns whether the checkbox is currently checked (True) or unchecked (False).

        Args:
            widget_id: The widget ID from get_ui_layout()

        Returns:
            JSON with checked state (true/false) or null if not a checkbox
        """
        try:
            state = get_bridge().get_checkbox_state(widget_id)
            return json.dumps(
                {
                    "found": state is not None,
                    "checked": state,
                }
            )
        except RemoteBridgeError as e:
            return json.dumps({"found": False, "error": str(e)})

    @mcp.tool
    def select_radio(widget_id: int) -> str:
        """Select a Radiobutton widget.

        Finds the Radiobutton with the given ID and selects it.
        Works with both standard tk.Radiobutton and ttk.Radiobutton.

        Args:
            widget_id: The widget ID from get_ui_layout()

        Returns:
            JSON with success status and message
        """
        try:
            success = get_bridge().select_radio(widget_id)
            msg = "Radio selected" if success else "Not found or not a radiobutton"
            return json.dumps({"success": success, "message": msg})
        except RemoteBridgeError as e:
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool
    def get_radio_value(widget_id: int) -> str:
        """Get the current value of the variable associated with a Radiobutton.

        Returns the current value of the shared variable, indicating which
        radio button in the group is selected.

        Args:
            widget_id: The widget ID from get_ui_layout()

        Returns:
            JSON with the current value or null if not a radiobutton
        """
        try:
            value = get_bridge().get_radio_value(widget_id)
            return json.dumps(
                {
                    "found": value is not None,
                    "value": value,
                }
            )
        except RemoteBridgeError as e:
            return json.dumps({"found": False, "error": str(e)})

    @mcp.tool
    def select_combobox(widget_id: int, value: str) -> str:
        """Select a value in a Combobox (dropdown) widget.

        Sets the Combobox to the specified value. Works with ttk.Combobox.

        Args:
            widget_id: The widget ID from get_ui_layout()
            value: The value to select (must be one of the available options)

        Returns:
            JSON with success status and message
        """
        try:
            success = get_bridge().select_combobox(widget_id, value)
            msg = "Combobox value set" if success else "Not found or not a combobox"
            return json.dumps({"success": success, "message": msg})
        except RemoteBridgeError as e:
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool
    def get_combobox_value(widget_id: int) -> str:
        """Get the current value of a Combobox widget.

        Args:
            widget_id: The widget ID from get_ui_layout()

        Returns:
            JSON with the current value or null if not a combobox
        """
        try:
            value = get_bridge().get_combobox_value(widget_id)
            return json.dumps(
                {
                    "found": value is not None,
                    "value": value,
                }
            )
        except RemoteBridgeError as e:
            return json.dumps({"found": False, "error": str(e)})

    @mcp.tool
    def get_combobox_options(widget_id: int) -> str:
        """Get the available options in a Combobox widget.

        Args:
            widget_id: The widget ID from get_ui_layout()

        Returns:
            JSON with list of available options or null if not a combobox
        """
        try:
            options = get_bridge().get_combobox_options(widget_id)
            return json.dumps(
                {
                    "found": options is not None,
                    "options": options,
                }
            )
        except RemoteBridgeError as e:
            return json.dumps({"found": False, "error": str(e)})

    return mcp
