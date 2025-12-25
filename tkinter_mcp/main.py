"""Entry point for Tkinter MCP Server."""

from __future__ import annotations

from tkinter_mcp.server.mcp_server import create_mcp_server


def main() -> None:
    """Run the standalone MCP server."""
    mcp = create_mcp_server()
    mcp.run()


if __name__ == "__main__":
    main()
