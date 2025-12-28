# tkinter-mcp

MCP server for inspecting and automating Tkinter GUI applications.

[![PyPI](https://img.shields.io/pypi/v/tkinter-mcp-server.svg)](https://pypi.org/project/tkinter-mcp-server/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://modelcontextprotocol.io)

## Overview

An MCP server that enables AI agents to launch, inspect, and interact with Tkinter applications. The server auto-injects an inspection agent via monkey-patching. No modifications to target apps required.

![Demo](assets/demo.gif)

## Tools

| Tool | Description |
|------|-------------|
| `launch_app` | Start a Tkinter app with inspection enabled |
| `is_connected` | Check if an app is currently connected |
| `get_ui_layout` | Get the widget tree as structured JSON |
| `view_application` | Capture a high-quality JPEG screenshot |
| `view_application_thumbnail` | Capture a small thumbnail screenshot |
| `get_window_info` | Get window position and dimensions |
| `click_widget` | Click a widget (left/right/middle, single/double) |
| `type_text` | Type text into Entry or Text widgets |
| `get_widget_by_text` | Find a widget by its text content |
| `focus_widget` | Set keyboard focus to a widget |
| `get_focused_widget` | Get the currently focused widget |
| `get_widget_value` | Get widget value (Entry, Text, Scale, Checkbox, etc.) |
| `set_widget_value` | Set widget value based on widget type |
| `get_widget_options` | Get options for Combobox or Listbox |
| `drag_widget` | Drag and drop between two widgets |
| `close_app` | Terminate the application |

## Installation

### uvx (Quick Start)

```bash
claude mcp add tkinter-mcp-server -- uvx tkinter-mcp-server
```

> **Note:** Apps using PIL/ImageTk may have compatibility issues with uvx. Use pip install instead.

### pip (Recommended for PIL apps)

```bash
pip install tkinter-mcp-server
claude mcp add tkinter-mcp-server -- tkinter-mcp-server
```

### Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "tkinter": {
      "command": "tkinter-mcp-server"
    }
  }
}
```

For uvx: use `"command": "uvx"` with `"args": ["tkinter-mcp-server"]`

## How It Works

The server launches Tkinter apps through a custom launcher that patches `tkinter.Tk.__init__`. This injects an agent that communicates over a local socket, enabling thread-safe inspection and control of the GUI.

```mermaid
flowchart LR
    A[MCP Client] <--> B[MCP Server]
    B <--> C[Socket]
    C <--> D[Agent]
    D <--> E[Tkinter App]
```

## Requirements

- Python 3.10+
- macOS, Windows, or Linux

## License

MIT
