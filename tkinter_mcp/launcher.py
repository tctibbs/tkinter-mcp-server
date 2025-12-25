"""Launcher that patches tkinter and runs target script.

Usage:
    python -m tkinter_mcp.launcher script.py [args...]

This patches tkinter.Tk to auto-start the inspection agent before
executing the target script. Any Tkinter app will be automatically
inspectable via the MCP server.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

from tkinter_mcp.agent.patcher import patch_tkinter


def main() -> None:
    """Entry point for the launcher."""
    if len(sys.argv) < 2:
        print("Usage: python -m tkinter_mcp.launcher <script.py> [args...]")
        print()
        print("Launches a Python script with Tkinter inspection enabled.")
        print("Any Tkinter app will be automatically inspectable via MCP.")
        sys.exit(1)

    script_path = Path(sys.argv[1]).resolve()

    if not script_path.exists():
        print(f"Error: Script not found: {script_path}")
        sys.exit(1)

    # Patch tkinter before running the script
    patch_tkinter()

    # Adjust sys.argv so the script sees correct arguments
    sys.argv = sys.argv[1:]

    # Add script's directory to path so imports work
    script_dir = str(script_path.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    # Run the script
    runpy.run_path(str(script_path), run_name="__main__")


if __name__ == "__main__":
    main()
