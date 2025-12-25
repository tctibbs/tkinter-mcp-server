# tkinter-mcp

MCP server for inspecting and automating Tkinter GUI applications.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://modelcontextprotocol.io)

## Overview

An MCP server that enables AI agents to launch, inspect, and interact with Tkinter applications. The server auto-injects an inspection agent via monkey-patching. No modifications to target apps required.

## Tools

| Tool | Description |
|------|-------------|
| `launch_app` | Start a Tkinter app with inspection enabled |
| `get_ui_layout` | Get the widget tree as structured JSON |
| `view_application` | Capture a screenshot of the window |
| `click_widget` | Click a widget by its ID |
| `type_text` | Type text into Entry or Text widgets |
| `get_widget_by_text` | Find a widget by its text content |
| `get_window_info` | Get window position and dimensions |
| `close_app` | Terminate the application |

## Installation

Clone the repository and install:

```bash
git clone https://github.com/YOUR_USERNAME/tkinter-mcp.git
cd tkinter-mcp
pip install -e .
```

Then add to your MCP client configuration:

```json
{
  "mcpServers": {
    "tkinter": {
      "command": "python",
      "args": ["-m", "tkinter_mcp.main"],
      "cwd": "/path/to/tkinter-mcp"
    }
  }
}
```

## How It Works

The server launches Tkinter apps through a custom launcher that patches `tkinter.Tk.__init__`. This injects an agent that communicates over a local socket, enabling thread-safe inspection and control of the GUI.

```
MCP Client ←→ MCP Server ←→ Socket ←→ Agent ←→ Tkinter App
```

## Requirements

- Python 3.10+
- macOS, Windows, or Linux

## Roadmap

- [ ] Publish to PyPI for simpler installation
- [ ] Add to MCP registry for one-command setup
- [ ] Support for additional widget types (Listbox, Canvas, etc.)

## License

MIT
