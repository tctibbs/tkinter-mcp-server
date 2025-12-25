"""Thread-safe bridge between MCP server and Tkinter application."""

from __future__ import annotations

from tkinter_mcp.bridge.remote import RemoteBridge, RemoteBridgeError

__all__ = [
    "RemoteBridge",
    "RemoteBridgeError",
]
