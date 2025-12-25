"""Dataclasses for widget introspection data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WidgetGeometry:
    """Represents widget position and dimensions."""

    x: int
    y: int
    width: int
    height: int

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary representation.

        Returns:
            Dictionary with x, y, width, height keys
        """
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> WidgetGeometry:
        """Create from dictionary."""
        return cls(
            x=data["x"],
            y=data["y"],
            width=data["width"],
            height=data["height"],
        )


@dataclass
class WidgetInfo:
    """Represents introspected widget information.

    Args:
        widget_class: The Tkinter widget class name (e.g., 'Button', 'Label')
        widget_id: Unique identifier from winfo_id()
        name: Widget name from winfo_name()
        geometry: Position and dimensions
        state: Widget state (normal, disabled, etc.)
        text: Text content if applicable
        is_mapped: Whether widget is currently visible
        children: List of child WidgetInfo objects
    """

    widget_class: str
    widget_id: int
    name: str
    geometry: WidgetGeometry
    state: str = "normal"
    text: str | None = None
    is_mapped: bool = True
    children: list[WidgetInfo] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of widget info
        """
        return {
            "class": self.widget_class,
            "id": self.widget_id,
            "name": self.name,
            "geometry": self.geometry.to_dict(),
            "state": self.state,
            "text": self.text,
            "is_mapped": self.is_mapped,
            "children": [child.to_dict() for child in self.children],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WidgetInfo:
        """Create from dictionary."""
        return cls(
            widget_class=data["class"],
            widget_id=data["id"],
            name=data["name"],
            geometry=WidgetGeometry.from_dict(data["geometry"]),
            state=data.get("state", "normal"),
            text=data.get("text"),
            is_mapped=data.get("is_mapped", True),
            children=[cls.from_dict(c) for c in data.get("children", [])],
        )


@dataclass
class UILayout:
    """Represents the complete UI layout.

    Args:
        window_title: Title of the main window
        root: Root widget info with nested children
        timestamp: ISO format timestamp of capture
    """

    window_title: str
    root: WidgetInfo
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of UI layout
        """
        return {
            "window_title": self.window_title,
            "root": self.root.to_dict(),
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UILayout:
        """Create from dictionary."""
        return cls(
            window_title=data["window_title"],
            root=WidgetInfo.from_dict(data["root"]),
            timestamp=data["timestamp"],
        )
