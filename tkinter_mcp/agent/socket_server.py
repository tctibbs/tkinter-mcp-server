"""Socket server that runs in the Tkinter app process."""

from __future__ import annotations

import contextlib
import json
import socket
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from tkinter_mcp.bridge.protocol import (
    CAPTURE_SCREENSHOT,
    CLICK_WIDGET,
    CLOSE_APP,
    DEFAULT_HOST,
    DEFAULT_PORT,
    FIND_WIDGET_BY_TEXT,
    GET_CHECKBOX_STATE,
    GET_UI_LAYOUT,
    GET_WINDOW_GEOMETRY,
    TOGGLE_CHECKBOX,
    TYPE_TEXT,
    Request,
    Response,
)
from tkinter_mcp.bridge.thread_safe import execute_on_main_thread
from tkinter_mcp.introspection.screenshot import capture_window_screenshot
from tkinter_mcp.introspection.serializer import (
    find_widget_by_id,
    find_widget_by_text,
    serialize_widget_tree,
)

if TYPE_CHECKING:
    import tkinter as tk


class AgentServer:
    """Socket server for receiving commands from MCP server.

    Runs in a background thread and executes commands on the main Tkinter thread.
    """

    def __init__(
        self,
        root: tk.Tk,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
    ) -> None:
        self._root = root
        self._host = host
        self._port = port
        self._server_socket: socket.socket | None = None
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the agent server in a background thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._run_server,
            daemon=True,
            name="TkinterMCP-Agent",
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the agent server."""
        self._running = False
        if self._server_socket:
            with contextlib.suppress(OSError):
                self._server_socket.close()

    def _run_server(self) -> None:
        """Main server loop."""
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self._server_socket.bind((self._host, self._port))
            self._server_socket.listen(1)
            self._server_socket.settimeout(1.0)

            while self._running:
                try:
                    client, _ = self._server_socket.accept()
                    self._handle_client(client)
                except TimeoutError:
                    continue
                except OSError:
                    break
        finally:
            if self._server_socket:
                self._server_socket.close()

    def _handle_client(self, client: socket.socket) -> None:
        """Handle a connected client."""
        client.settimeout(60.0)  # Long timeout for idle connections
        buffer = b""

        try:
            while self._running:
                try:
                    data = client.recv(4096)
                    if not data:
                        break

                    buffer += data

                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        if line:
                            response = self._handle_request(line.decode("utf-8"))
                            client.sendall(response.encode("utf-8") + b"\n")
                except TimeoutError:
                    continue
                except (ConnectionResetError, BrokenPipeError):
                    break
        finally:
            client.close()

    def _handle_request(self, data: str) -> str:
        """Parse and handle a single request."""
        try:
            request = Request.from_dict(json.loads(data))
            result = self._dispatch(request)
            response = Response(id=request.id, result=result)
        except Exception as e:
            response = Response(id=0, error=str(e))

        return json.dumps(response.to_dict())

    def _dispatch(self, request: Request) -> Any:
        """Dispatch a request to the appropriate handler."""
        handlers: dict[str, Callable[..., Any]] = {
            GET_UI_LAYOUT: self._get_ui_layout,
            CAPTURE_SCREENSHOT: self._capture_screenshot,
            GET_WINDOW_GEOMETRY: self._get_window_geometry,
            CLICK_WIDGET: self._click_widget,
            TYPE_TEXT: self._type_text,
            FIND_WIDGET_BY_TEXT: self._find_widget_by_text,
            CLOSE_APP: self._close_app,
            TOGGLE_CHECKBOX: self._toggle_checkbox,
            GET_CHECKBOX_STATE: self._get_checkbox_state,
        }

        handler = handlers.get(request.method)
        if handler is None:
            raise ValueError(f"Unknown method: {request.method}")

        return handler(**request.params)

    def _get_ui_layout(self) -> dict[str, Any]:
        """Get UI layout on main thread."""
        layout = execute_on_main_thread(
            self._root,
            lambda: serialize_widget_tree(self._root),
        )
        return layout.to_dict()

    def _capture_screenshot(self) -> str:
        """Capture screenshot on main thread."""
        screenshot = execute_on_main_thread(
            self._root,
            lambda: capture_window_screenshot(self._root),
        )
        return screenshot.decode("utf-8")

    def _get_window_geometry(self) -> dict[str, int]:
        """Get window geometry on main thread."""

        def _get() -> dict[str, int]:
            self._root.update_idletasks()
            return {
                "x": self._root.winfo_x(),
                "y": self._root.winfo_y(),
                "width": self._root.winfo_width(),
                "height": self._root.winfo_height(),
            }

        return execute_on_main_thread(self._root, _get)

    def _click_widget(self, widget_id: int) -> bool:
        """Click a widget on main thread."""

        def _click() -> bool:
            widget = find_widget_by_id(self._root, widget_id)
            if widget is None:
                return False

            if hasattr(widget, "invoke"):
                widget.invoke()
                return True

            widget.event_generate("<Button-1>")
            widget.event_generate("<ButtonRelease-1>")
            return True

        return execute_on_main_thread(self._root, _click)

    def _type_text(self, widget_id: int, text: str) -> bool:
        """Type text into widget on main thread."""

        def _type() -> bool:
            widget = find_widget_by_id(self._root, widget_id)
            if widget is None:
                return False

            widget_class = widget.winfo_class()

            if widget_class == "Entry":
                widget.delete(0, "end")
                widget.insert(0, text)
                return True

            if widget_class == "Text":
                widget.delete("1.0", "end")
                widget.insert("1.0", text)
                return True

            return False

        return execute_on_main_thread(self._root, _type)

    def _find_widget_by_text(self, text: str) -> int | None:
        """Find widget by text on main thread."""

        def _find() -> int | None:
            widget = find_widget_by_text(self._root, text)
            return widget.winfo_id() if widget else None

        return execute_on_main_thread(self._root, _find)

    def _close_app(self) -> bool:
        """Close the application."""

        def _close() -> bool:
            self._root.quit()
            self._root.destroy()
            return True

        try:
            execute_on_main_thread(self._root, _close)
            return True
        except Exception:
            return False

    def _toggle_checkbox(self, widget_id: int) -> bool:
        """Toggle a Checkbutton widget."""

        def _toggle() -> bool:
            widget = find_widget_by_id(self._root, widget_id)
            if widget is None:
                return False

            widget_class = widget.winfo_class()
            if widget_class not in ("Checkbutton", "TCheckbutton"):
                return False

            widget.invoke()
            return True

        return execute_on_main_thread(self._root, _toggle)

    def _get_checkbox_state(self, widget_id: int) -> bool | None:
        """Get the current state of a Checkbutton widget."""

        def _get_state() -> bool | None:
            widget = find_widget_by_id(self._root, widget_id)
            if widget is None:
                return None

            widget_class = widget.winfo_class()
            if widget_class not in ("Checkbutton", "TCheckbutton"):
                return None

            # Try to get the variable value
            try:
                var = widget.cget("variable")
                if var:
                    # Get the variable from the widget's master
                    value = widget.getvar(var)
                    # Handle different variable types
                    if isinstance(value, bool):
                        return value
                    if isinstance(value, int):
                        return value == 1
                    if isinstance(value, str):
                        return value in ("1", "true", "True", "yes", "on")
            except Exception:
                pass

            # Fallback: check instate for ttk
            try:
                if hasattr(widget, "instate"):
                    return widget.instate(["selected"])
            except Exception:
                pass

            return None

        return execute_on_main_thread(self._root, _get_state)
