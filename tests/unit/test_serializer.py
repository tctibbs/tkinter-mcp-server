"""Unit tests for widget serialization."""

from unittest.mock import MagicMock

from tkinter_mcp.introspection.serializer import (
    find_widget_by_id,
    find_widget_by_text,
    get_widget_class_name,
    get_widget_state,
    get_widget_text,
    serialize_widget,
)


class TestGetWidgetClassName:
    """Tests for get_widget_class_name function."""

    def test_returns_widget_class(self, mock_button_widget: MagicMock) -> None:
        result = get_widget_class_name(mock_button_widget)

        assert result == "Button"
        mock_button_widget.winfo_class.assert_called_once()

    def test_returns_label_class(self, mock_label_widget: MagicMock) -> None:
        result = get_widget_class_name(mock_label_widget)

        assert result == "Label"


class TestGetWidgetText:
    """Tests for get_widget_text function."""

    def test_returns_text_from_cget(self, mock_button_widget: MagicMock) -> None:
        result = get_widget_text(mock_button_widget)

        assert result == "Click Me"

    def test_returns_text_from_get_method(self, mock_entry_widget: MagicMock) -> None:
        result = get_widget_text(mock_entry_widget)

        assert result == "test input"

    def test_returns_none_when_no_text(self) -> None:
        widget = MagicMock()
        widget.cget.side_effect = Exception("no text")
        widget.get.side_effect = Exception("no get method")

        result = get_widget_text(widget)

        assert result is None


class TestGetWidgetState:
    """Tests for get_widget_state function."""

    def test_returns_normal_state(self, mock_button_widget: MagicMock) -> None:
        mock_button_widget.cget.return_value = "normal"

        result = get_widget_state(mock_button_widget)

        assert result == "normal"

    def test_returns_disabled_state(self, mock_button_widget: MagicMock) -> None:
        mock_button_widget.cget.return_value = "disabled"

        result = get_widget_state(mock_button_widget)

        assert result == "disabled"

    def test_returns_normal_on_exception(self) -> None:
        widget = MagicMock()
        widget.cget.side_effect = Exception("no state")

        result = get_widget_state(widget)

        assert result == "normal"

    def test_returns_normal_when_state_is_none(self) -> None:
        widget = MagicMock()
        widget.cget.return_value = None

        result = get_widget_state(widget)

        assert result == "normal"


class TestSerializeWidget:
    """Tests for serialize_widget function."""

    def test_serializes_button(self, mock_button_widget: MagicMock) -> None:
        result = serialize_widget(mock_button_widget)

        assert result.widget_class == "Button"
        assert result.widget_id == 67890
        assert result.name == "button1"
        assert result.geometry.x == 10
        assert result.geometry.y == 20
        assert result.geometry.width == 100
        assert result.geometry.height == 30
        assert result.text == "Click Me"
        assert result.is_mapped is True
        assert result.children == []

    def test_serializes_with_children(self, mock_tk_root: MagicMock) -> None:
        child = MagicMock()
        child.winfo_x.return_value = 5
        child.winfo_y.return_value = 5
        child.winfo_width.return_value = 50
        child.winfo_height.return_value = 25
        child.winfo_id.return_value = 99999
        child.winfo_name.return_value = "child1"
        child.winfo_class.return_value = "Label"
        child.winfo_ismapped.return_value = 1
        child.winfo_children.return_value = []
        child.cget.return_value = "Child Label"
        child.update_idletasks = MagicMock()

        mock_tk_root.winfo_children.return_value = [child]

        result = serialize_widget(mock_tk_root)

        assert len(result.children) == 1
        assert result.children[0].widget_class == "Label"
        assert result.children[0].text == "Child Label"

    def test_serializes_unmapped_widget(self, mock_button_widget: MagicMock) -> None:
        mock_button_widget.winfo_ismapped.return_value = 0

        result = serialize_widget(mock_button_widget)

        assert result.is_mapped is False


class TestFindWidgetById:
    """Tests for find_widget_by_id function."""

    def test_finds_root_widget(self, mock_tk_root: MagicMock) -> None:
        result = find_widget_by_id(mock_tk_root, 12345)

        assert result is mock_tk_root

    def test_finds_child_widget(self, mock_tk_root: MagicMock) -> None:
        child = MagicMock()
        child.winfo_id.return_value = 55555
        child.winfo_children.return_value = []
        mock_tk_root.winfo_children.return_value = [child]

        result = find_widget_by_id(mock_tk_root, 55555)

        assert result is child

    def test_returns_none_when_not_found(self, mock_tk_root: MagicMock) -> None:
        result = find_widget_by_id(mock_tk_root, 99999)

        assert result is None

    def test_finds_deeply_nested_widget(self, mock_tk_root: MagicMock) -> None:
        grandchild = MagicMock()
        grandchild.winfo_id.return_value = 77777
        grandchild.winfo_children.return_value = []

        child = MagicMock()
        child.winfo_id.return_value = 66666
        child.winfo_children.return_value = [grandchild]

        mock_tk_root.winfo_children.return_value = [child]

        result = find_widget_by_id(mock_tk_root, 77777)

        assert result is grandchild


class TestFindWidgetByText:
    """Tests for find_widget_by_text function."""

    def test_finds_widget_with_exact_text(self, mock_label_widget: MagicMock) -> None:
        mock_label_widget.winfo_children.return_value = []

        result = find_widget_by_text(mock_label_widget, "Hello World")

        assert result is mock_label_widget

    def test_finds_widget_with_partial_text(self, mock_label_widget: MagicMock) -> None:
        mock_label_widget.winfo_children.return_value = []

        result = find_widget_by_text(mock_label_widget, "Hello")

        assert result is mock_label_widget

    def test_returns_none_when_not_found(self, mock_tk_root: MagicMock) -> None:
        mock_tk_root.cget.side_effect = Exception("no text")

        result = find_widget_by_text(mock_tk_root, "nonexistent")

        assert result is None

    def test_finds_child_with_text(self, mock_tk_root: MagicMock) -> None:
        mock_tk_root.cget.side_effect = Exception("no text")

        child = MagicMock()
        child.cget.return_value = "Find Me"
        child.winfo_children.return_value = []

        mock_tk_root.winfo_children.return_value = [child]

        result = find_widget_by_text(mock_tk_root, "Find Me")

        assert result is child
