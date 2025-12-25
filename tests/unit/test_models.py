"""Unit tests for introspection models."""

from tkinter_mcp.introspection.models import UILayout, WidgetGeometry, WidgetInfo


class TestWidgetGeometry:
    """Tests for WidgetGeometry dataclass."""

    def test_to_dict(self) -> None:
        geometry = WidgetGeometry(x=10, y=20, width=100, height=50)

        result = geometry.to_dict()

        assert result == {"x": 10, "y": 20, "width": 100, "height": 50}

    def test_default_values(self) -> None:
        geometry = WidgetGeometry(x=0, y=0, width=0, height=0)

        assert geometry.x == 0
        assert geometry.y == 0
        assert geometry.width == 0
        assert geometry.height == 0


class TestWidgetInfo:
    """Tests for WidgetInfo dataclass."""

    def test_to_dict_minimal(self) -> None:
        geometry = WidgetGeometry(x=0, y=0, width=100, height=100)
        info = WidgetInfo(
            widget_class="Button",
            widget_id=123,
            name="btn1",
            geometry=geometry,
        )

        result = info.to_dict()

        assert result["class"] == "Button"
        assert result["id"] == 123
        assert result["name"] == "btn1"
        assert result["state"] == "normal"
        assert result["text"] is None
        assert result["is_mapped"] is True
        assert result["children"] == []

    def test_to_dict_with_text(self) -> None:
        geometry = WidgetGeometry(x=10, y=20, width=80, height=30)
        info = WidgetInfo(
            widget_class="Label",
            widget_id=456,
            name="lbl1",
            geometry=geometry,
            text="Hello World",
        )

        result = info.to_dict()

        assert result["text"] == "Hello World"

    def test_to_dict_with_children(self) -> None:
        child_geo = WidgetGeometry(x=5, y=5, width=50, height=25)
        child = WidgetInfo(
            widget_class="Label",
            widget_id=456,
            name="lbl1",
            geometry=child_geo,
            text="Child Label",
        )

        parent_geo = WidgetGeometry(x=0, y=0, width=100, height=100)
        parent = WidgetInfo(
            widget_class="Frame",
            widget_id=123,
            name="frame1",
            geometry=parent_geo,
            children=[child],
        )

        result = parent.to_dict()

        assert len(result["children"]) == 1
        assert result["children"][0]["class"] == "Label"
        assert result["children"][0]["text"] == "Child Label"

    def test_to_dict_disabled_state(self) -> None:
        geometry = WidgetGeometry(x=0, y=0, width=100, height=30)
        info = WidgetInfo(
            widget_class="Button",
            widget_id=789,
            name="btn_disabled",
            geometry=geometry,
            state="disabled",
        )

        result = info.to_dict()

        assert result["state"] == "disabled"

    def test_to_dict_unmapped(self) -> None:
        geometry = WidgetGeometry(x=0, y=0, width=100, height=30)
        info = WidgetInfo(
            widget_class="Button",
            widget_id=999,
            name="hidden_btn",
            geometry=geometry,
            is_mapped=False,
        )

        result = info.to_dict()

        assert result["is_mapped"] is False


class TestUILayout:
    """Tests for UILayout dataclass."""

    def test_to_dict(self) -> None:
        root_geo = WidgetGeometry(x=0, y=0, width=800, height=600)
        root_info = WidgetInfo(
            widget_class="Tk",
            widget_id=1,
            name=".",
            geometry=root_geo,
        )
        layout = UILayout(
            window_title="Test App",
            root=root_info,
            timestamp="2024-01-01T00:00:00+00:00",
        )

        result = layout.to_dict()

        assert result["window_title"] == "Test App"
        assert result["timestamp"] == "2024-01-01T00:00:00+00:00"
        assert result["root"]["class"] == "Tk"
        assert result["root"]["geometry"]["width"] == 800

    def test_nested_hierarchy(self) -> None:
        button_geo = WidgetGeometry(x=10, y=10, width=80, height=30)
        button = WidgetInfo(
            widget_class="Button",
            widget_id=3,
            name="submit",
            geometry=button_geo,
            text="Submit",
        )

        frame_geo = WidgetGeometry(x=0, y=0, width=200, height=100)
        frame = WidgetInfo(
            widget_class="Frame",
            widget_id=2,
            name="main_frame",
            geometry=frame_geo,
            children=[button],
        )

        root_geo = WidgetGeometry(x=0, y=0, width=800, height=600)
        root = WidgetInfo(
            widget_class="Tk",
            widget_id=1,
            name=".",
            geometry=root_geo,
            children=[frame],
        )

        layout = UILayout(
            window_title="Nested Test",
            root=root,
            timestamp="2024-01-01T00:00:00+00:00",
        )

        result = layout.to_dict()

        assert len(result["root"]["children"]) == 1
        frame_dict = result["root"]["children"][0]
        assert frame_dict["class"] == "Frame"
        assert len(frame_dict["children"]) == 1
        assert frame_dict["children"][0]["text"] == "Submit"
