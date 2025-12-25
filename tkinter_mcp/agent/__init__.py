"""Agent module for auto-injecting inspection into Tkinter apps."""

from __future__ import annotations

from tkinter_mcp.agent.patcher import get_agent, patch_tkinter, unpatch_tkinter
from tkinter_mcp.agent.socket_server import AgentServer

__all__ = [
    "AgentServer",
    "get_agent",
    "patch_tkinter",
    "unpatch_tkinter",
]
