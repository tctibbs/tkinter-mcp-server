"""Remote bridge - socket client for MCP server to communicate with agent."""

from __future__ import annotations

import contextlib
import json
import socket
from typing import Any

from tkinter_mcp.bridge.protocol import (
    CAPTURE_SCREENSHOT,
    CLICK_WIDGET,
    CLOSE_APP,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DRAG_WIDGET,
    FIND_WIDGET_BY_TEXT,
    FOCUS_WIDGET,
    GET_FOCUSED_WIDGET,
    GET_UI_LAYOUT,
    GET_WIDGET_OPTIONS,
    GET_WIDGET_VALUE,
    GET_WINDOW_GEOMETRY,
    SET_WIDGET_VALUE,
    TYPE_TEXT,
    Request,
    Response,
)
from tkinter_mcp.introspection.models import UILayout


class RemoteBridgeError(Exception):
    """Error communicating with remote agent."""


class RemoteBridge:
    """Bridge that communicates with agent via socket.

    This is used by the MCP server to interact with a Tkinter app
    running in a separate process.
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
    ) -> None:
        self._host = host
        self._port = port
        self._socket: socket.socket | None = None
        self._request_id = 0

    def connect(self, timeout: float = 5.0) -> bool:
        """Connect to the agent.

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if connected, False otherwise
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(timeout)
            self._socket.connect((self._host, self._port))
            # Set longer timeout for actual operations
            self._socket.settimeout(30.0)
            return True
        except (OSError, TimeoutError):
            self._socket = None
            return False

    def disconnect(self) -> None:
        """Disconnect from the agent."""
        if self._socket:
            with contextlib.suppress(OSError):
                self._socket.close()
            self._socket = None

    def is_connected(self) -> bool:
        """Check if connected to agent."""
        return self._socket is not None

    def _send_request(self, method: str, **params: Any) -> Any:
        """Send a request and get response."""
        if not self._socket:
            raise RemoteBridgeError("Not connected to agent")

        self._request_id += 1
        request = Request(id=self._request_id, method=method, params=params)

        try:
            data = json.dumps(request.to_dict()) + "\n"
            self._socket.sendall(data.encode("utf-8"))

            buffer = b""
            while b"\n" not in buffer:
                chunk = self._socket.recv(65536)
                if not chunk:
                    raise RemoteBridgeError("Connection closed")
                buffer += chunk

            line = buffer.split(b"\n")[0]
            response = Response.from_dict(json.loads(line.decode("utf-8")))

            if response.error:
                raise RemoteBridgeError(response.error)

            return response.result

        except (OSError, TimeoutError) as e:
            self.disconnect()
            raise RemoteBridgeError(f"Communication error: {e}") from e

    def get_ui_layout(self) -> UILayout:
        """Get the current UI layout."""
        data = self._send_request(GET_UI_LAYOUT)
        return UILayout.from_dict(data)

    def capture_screenshot(
        self,
        max_dimension: int = 800,
        quality: int = 70,
    ) -> bytes:
        """Capture a screenshot of the window."""
        data = self._send_request(
            CAPTURE_SCREENSHOT,
            max_dimension=max_dimension,
            quality=quality,
        )
        return data.encode("utf-8")

    def get_window_geometry(self) -> dict[str, int]:
        """Get window position and size."""
        return self._send_request(GET_WINDOW_GEOMETRY)

    def click_widget(
        self,
        widget_id: int,
        button: str = "left",
        double: bool = False,
    ) -> bool:
        """Click a widget by ID.

        Args:
            widget_id: The widget ID to click
            button: Mouse button - "left", "right", or "middle"
            double: If True, perform a double-click
        """
        return self._send_request(
            CLICK_WIDGET,
            widget_id=widget_id,
            button=button,
            double=double,
        )

    def type_text(self, widget_id: int, text: str) -> bool:
        """Type text into a widget."""
        return self._send_request(TYPE_TEXT, widget_id=widget_id, text=text)

    def find_widget_id_by_text(self, text: str) -> int | None:
        """Find a widget by its text content."""
        return self._send_request(FIND_WIDGET_BY_TEXT, text=text)

    def close_app(self) -> bool:
        """Close the application."""
        try:
            result = self._send_request(CLOSE_APP)
            self.disconnect()
            return result
        except RemoteBridgeError:
            return False

    def focus_widget(self, widget_id: int) -> bool:
        """Set focus to a widget."""
        return self._send_request(FOCUS_WIDGET, widget_id=widget_id)

    def get_focused_widget(self) -> int | None:
        """Get the currently focused widget's ID."""
        return self._send_request(GET_FOCUSED_WIDGET)

    def get_widget_value(self, widget_id: int) -> Any:
        """Get the value of a widget based on its type."""
        return self._send_request(GET_WIDGET_VALUE, widget_id=widget_id)

    def set_widget_value(self, widget_id: int, value: Any) -> bool:
        """Set the value of a widget based on its type."""
        return self._send_request(SET_WIDGET_VALUE, widget_id=widget_id, value=value)

    def get_widget_options(self, widget_id: int) -> list[str] | None:
        """Get the available options for a widget (Combobox, Listbox)."""
        return self._send_request(GET_WIDGET_OPTIONS, widget_id=widget_id)

    def drag_widget(self, start_widget_id: int, end_widget_id: int) -> bool:
        """Drag from one widget to another."""
        return self._send_request(
            DRAG_WIDGET,
            start_widget_id=start_widget_id,
            end_widget_id=end_widget_id,
        )
