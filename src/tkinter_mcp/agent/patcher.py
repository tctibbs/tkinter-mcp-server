"""Monkey-patch tkinter.Tk to auto-start the inspection agent."""

from __future__ import annotations

import sys
import tkinter as tk
from typing import Any

from tkinter_mcp.agent.socket_server import AgentServer
from tkinter_mcp.bridge.protocol import DEFAULT_HOST, DEFAULT_PORT

_original_tk_init = tk.Tk.__init__
_agents: dict[int, AgentServer] = {}
_patched = False


def _patched_tk_init(self: tk.Tk, *args: Any, **kwargs: Any) -> None:
    """Patched Tk.__init__ that auto-starts the agent."""
    _original_tk_init(self, *args, **kwargs)

    agent = AgentServer(
        root=self,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
    )
    agent.start()

    _agents[id(self)] = agent

    sys.stderr.write(f"[tkinter-mcp] Agent started on {DEFAULT_HOST}:{DEFAULT_PORT}\n")


def patch_tkinter() -> None:
    """Apply the monkey-patch to tkinter.Tk."""
    global _patched
    if _patched:
        return

    tk.Tk.__init__ = _patched_tk_init
    _patched = True


def unpatch_tkinter() -> None:
    """Remove the monkey-patch from tkinter.Tk."""
    global _patched
    if not _patched:
        return

    tk.Tk.__init__ = _original_tk_init
    _patched = False


def get_agent(root: tk.Tk) -> AgentServer | None:
    """Get the agent for a given root window."""
    return _agents.get(id(root))
