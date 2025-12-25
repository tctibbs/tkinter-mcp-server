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
TOGGLE_CHECKBOX = "toggle_checkbox"
GET_CHECKBOX_STATE = "get_checkbox_state"
SELECT_RADIO = "select_radio"
GET_RADIO_VALUE = "get_radio_value"
SELECT_COMBOBOX = "select_combobox"
GET_COMBOBOX_VALUE = "get_combobox_value"
GET_COMBOBOX_OPTIONS = "get_combobox_options"
SELECT_LISTBOX_ITEM = "select_listbox_item"
GET_LISTBOX_ITEMS = "get_listbox_items"
GET_LISTBOX_SELECTION = "get_listbox_selection"
