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
            FOCUS_WIDGET: self._focus_widget,
            GET_FOCUSED_WIDGET: self._get_focused_widget,
            GET_WIDGET_VALUE: self._get_widget_value,
            SET_WIDGET_VALUE: self._set_widget_value,
            GET_WIDGET_OPTIONS: self._get_widget_options,
            DRAG_WIDGET: self._drag_widget,
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

    def _capture_screenshot(
        self,
        max_dimension: int = 800,
        quality: int = 70,
    ) -> str:
        """Capture screenshot on main thread."""
        screenshot = execute_on_main_thread(
            self._root,
            lambda: capture_window_screenshot(self._root, max_dimension, quality),
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

    def _click_widget(
        self,
        widget_id: int,
        button: str = "left",
        double: bool = False,
    ) -> bool:
        """Click a widget on main thread.

        Args:
            widget_id: The widget ID to click
            button: Mouse button - "left", "right", or "middle"
            double: If True, perform a double-click
        """

        def _click() -> bool:
            widget = find_widget_by_id(self._root, widget_id)
            if widget is None:
                return False

            # Map button name to Tkinter button number
            button_map = {"left": 1, "middle": 2, "right": 3}
            btn_num = button_map.get(button, 1)

            # For left single-click, try invoke() first (works for buttons)
            if button == "left" and not double and hasattr(widget, "invoke"):
                widget.invoke()
                return True

            # Generate click events
            btn_event = f"<Button-{btn_num}>"
            release_event = f"<ButtonRelease-{btn_num}>"

            widget.event_generate(btn_event)
            widget.event_generate(release_event)

            if double:
                # Generate second click pair for double-click
                widget.event_generate(btn_event)
                widget.event_generate(release_event)

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

    def _focus_widget(self, widget_id: int) -> bool:
        """Set focus to a widget."""

        def _focus() -> bool:
            widget = find_widget_by_id(self._root, widget_id)
            if widget is None:
                return False

            try:
                widget.focus_set()
                return True
            except Exception:
                return False

        return execute_on_main_thread(self._root, _focus)

    def _get_focused_widget(self) -> int | None:
        """Get the currently focused widget's ID."""

        def _get_focus() -> int | None:
            try:
                focused = self._root.focus_get()
                if focused is not None:
                    return focused.winfo_id()
            except Exception:
                pass
            return None

        return execute_on_main_thread(self._root, _get_focus)

    def _get_widget_value(self, widget_id: int) -> Any:
        """Get the value of a widget based on its type."""

        def _get_value() -> Any:
            widget = find_widget_by_id(self._root, widget_id)
            if widget is None:
                return None

            widget_class = widget.winfo_class()

            # Entry widget
            if widget_class == "Entry":
                return widget.get()

            # Text widget
            if widget_class == "Text":
                return widget.get("1.0", "end-1c")

            # Scale widget
            if widget_class in ("Scale", "TScale"):
                return float(widget.get())

            # Combobox
            if widget_class == "TCombobox":
                return widget.get()

            # Spinbox
            if widget_class in ("Spinbox", "TSpinbox"):
                return widget.get()

            # Checkbutton - return True/False
            if widget_class in ("Checkbutton", "TCheckbutton"):
                try:
                    var = widget.cget("variable")
                    if var:
                        value = widget.getvar(var)
                        if isinstance(value, bool):
                            return value
                        if isinstance(value, int):
                            return value == 1
                        if isinstance(value, str):
                            return value in ("1", "true", "True", "yes", "on")
                except Exception:
                    pass
                return None

            # Radiobutton - return the variable value
            if widget_class in ("Radiobutton", "TRadiobutton"):
                try:
                    var = widget.cget("variable")
                    if var:
                        return str(widget.getvar(var))
                except Exception:
                    pass
                return None

            # Listbox - return selected items
            if widget_class == "Listbox":
                try:
                    selection = widget.curselection()
                    if selection:
                        return [widget.get(i) for i in selection]
                    return []
                except Exception:
                    return None

            # Try generic get() method
            if hasattr(widget, "get"):
                try:
                    return widget.get()
                except Exception:
                    pass

            # Try cget("text")
            try:
                return widget.cget("text")
            except Exception:
                pass

            return None

        return execute_on_main_thread(self._root, _get_value)

    def _set_widget_value(self, widget_id: int, value: Any) -> bool:
        """Set the value of a widget based on its type."""

        def _set_value() -> bool:
            widget = find_widget_by_id(self._root, widget_id)
            if widget is None:
                return False

            widget_class = widget.winfo_class()

            # Entry widget
            if widget_class == "Entry":
                widget.delete(0, "end")
                widget.insert(0, str(value))
                return True

            # Text widget
            if widget_class == "Text":
                widget.delete("1.0", "end")
                widget.insert("1.0", str(value))
                return True

            # Scale widget
            if widget_class in ("Scale", "TScale"):
                widget.set(float(value))
                return True

            # Combobox
            if widget_class == "TCombobox":
                widget.set(str(value))
                widget.event_generate("<<ComboboxSelected>>")
                return True

            # Spinbox
            if widget_class in ("Spinbox", "TSpinbox"):
                widget.delete(0, "end")
                widget.insert(0, str(value))
                return True

            # Checkbutton - toggle or set state
            if widget_class in ("Checkbutton", "TCheckbutton"):
                # Interpret value as boolean
                str_val = str(value).lower()
                target_state = str_val in ("true", "1", "yes", "on")

                # Get current state
                try:
                    var = widget.cget("variable")
                    if var:
                        current = widget.getvar(var)
                        if isinstance(current, int):
                            current_state = current == 1
                        elif isinstance(current, str):
                            current_state = current in ("1", "true", "yes", "on")
                        else:
                            current_state = bool(current)

                        # Toggle if needed
                        if current_state != target_state:
                            widget.invoke()
                        return True
                except Exception:
                    pass
                return False

            # Radiobutton - select this radio button
            if widget_class in ("Radiobutton", "TRadiobutton"):
                widget.invoke()
                return True

            # Listbox - select by index
            if widget_class == "Listbox":
                try:
                    index = int(value)
                    widget.selection_clear(0, "end")
                    widget.selection_set(index)
                    widget.activate(index)
                    widget.event_generate("<<ListboxSelect>>")
                    return True
                except (ValueError, TypeError):
                    return False

            # Try generic set() method
            if hasattr(widget, "set"):
                try:
                    widget.set(value)
                    return True
                except Exception:
                    pass

            return False

        return execute_on_main_thread(self._root, _set_value)

    def _get_widget_options(self, widget_id: int) -> list[str] | None:
        """Get the available options for a widget (Combobox, Listbox)."""

        def _get_options() -> list[str] | None:
            widget = find_widget_by_id(self._root, widget_id)
            if widget is None:
                return None

            widget_class = widget.winfo_class()

            # Combobox options
            if widget_class == "TCombobox":
                try:
                    values = widget.cget("values")
                    if values:
                        return list(values)
                    return []
                except Exception:
                    return None

            # Listbox items
            if widget_class == "Listbox":
                try:
                    return list(widget.get(0, "end"))
                except Exception:
                    return None

            return None

        return execute_on_main_thread(self._root, _get_options)

    def _drag_widget(self, start_widget_id: int, end_widget_id: int) -> bool:
        """Drag from one widget to another on main thread.

        Args:
            start_widget_id: The widget ID to drag from
            end_widget_id: The widget ID to drag to
        """

        def _drag() -> bool:
            start_widget = find_widget_by_id(self._root, start_widget_id)
            end_widget = find_widget_by_id(self._root, end_widget_id)

            if start_widget is None or end_widget is None:
                return False

            # Get center coordinates of each widget
            start_x = start_widget.winfo_width() // 2
            start_y = start_widget.winfo_height() // 2
            end_x = end_widget.winfo_width() // 2
            end_y = end_widget.winfo_height() // 2

            # Generate drag sequence
            # 1. Press button on start widget
            start_widget.event_generate("<Button-1>", x=start_x, y=start_y)

            # 2. Motion event (some apps need this)
            start_widget.event_generate("<B1-Motion>", x=start_x, y=start_y)

            # 3. Release on end widget
            end_widget.event_generate("<ButtonRelease-1>", x=end_x, y=end_y)

            return True

        return execute_on_main_thread(self._root, _drag)
