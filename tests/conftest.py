"""Pytest fixtures for Tkinter MCP Server tests."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_tk_root() -> MagicMock:
    """Create a mock Tkinter root window."""
    root = MagicMock()
    root.winfo_x.return_value = 100
    root.winfo_y.return_value = 100
    root.winfo_rootx.return_value = 100
    root.winfo_rooty.return_value = 100
    root.winfo_width.return_value = 800
    root.winfo_height.return_value = 600
    root.winfo_id.return_value = 12345
    root.winfo_name.return_value = "."
    root.winfo_class.return_value = "Tk"
    root.winfo_ismapped.return_value = 1
    root.winfo_children.return_value = []
    root.title.return_value = "Test Window"
    root.update_idletasks = MagicMock()
    return root


@pytest.fixture
def mock_button_widget() -> MagicMock:
    """Create a mock Tkinter Button widget."""
    widget = MagicMock()
    widget.winfo_x.return_value = 10
    widget.winfo_y.return_value = 20
    widget.winfo_width.return_value = 100
    widget.winfo_height.return_value = 30
    widget.winfo_id.return_value = 67890
    widget.winfo_name.return_value = "button1"
    widget.winfo_class.return_value = "Button"
    widget.winfo_ismapped.return_value = 1
    widget.winfo_children.return_value = []
    widget.cget.return_value = "Click Me"
    widget.update_idletasks = MagicMock()
    return widget


@pytest.fixture
def mock_entry_widget() -> MagicMock:
    """Create a mock Tkinter Entry widget."""
    widget = MagicMock()
    widget.winfo_x.return_value = 50
    widget.winfo_y.return_value = 60
    widget.winfo_width.return_value = 200
    widget.winfo_height.return_value = 25
    widget.winfo_id.return_value = 11111
    widget.winfo_name.return_value = "entry1"
    widget.winfo_class.return_value = "Entry"
    widget.winfo_ismapped.return_value = 1
    widget.winfo_children.return_value = []
    widget.cget.side_effect = Exception("no text option")
    widget.get.return_value = "test input"
    widget.update_idletasks = MagicMock()
    return widget


@pytest.fixture
def mock_label_widget() -> MagicMock:
    """Create a mock Tkinter Label widget."""
    widget = MagicMock()
    widget.winfo_x.return_value = 0
    widget.winfo_y.return_value = 0
    widget.winfo_width.return_value = 150
    widget.winfo_height.return_value = 20
    widget.winfo_id.return_value = 22222
    widget.winfo_name.return_value = "label1"
    widget.winfo_class.return_value = "Label"
    widget.winfo_ismapped.return_value = 1
    widget.winfo_children.return_value = []
    widget.cget.return_value = "Hello World"
    widget.update_idletasks = MagicMock()
    return widget
