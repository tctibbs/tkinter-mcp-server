"""JSON-RPC style protocol for agent-server communication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_PORT = 9999
DEFAULT_HOST = "127.0.0.1"


@dataclass
class Request:
    """A request from MCP server to agent."""

    id: int
    method: str
    params: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "method": self.method,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Request:
        return cls(
            id=data["id"],
            method=data["method"],
            params=data.get("params", {}),
        )


@dataclass
class Response:
    """A response from agent to MCP server."""

    id: int
    result: Any | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "result": self.result,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Response:
        return cls(
            id=data["id"],
            result=data.get("result"),
            error=data.get("error"),
        )


# Method names
GET_UI_LAYOUT = "get_ui_layout"
CAPTURE_SCREENSHOT = "capture_screenshot"
GET_WINDOW_GEOMETRY = "get_window_geometry"
CLICK_WIDGET = "click_widget"
TYPE_TEXT = "type_text"
FIND_WIDGET_BY_TEXT = "find_widget_by_text"
CLOSE_APP = "close_app"
FOCUS_WIDGET = "focus_widget"
GET_FOCUSED_WIDGET = "get_focused_widget"
GET_WIDGET_VALUE = "get_widget_value"
SET_WIDGET_VALUE = "set_widget_value"
GET_WIDGET_OPTIONS = "get_widget_options"
DRAG_WIDGET = "drag_widget"
