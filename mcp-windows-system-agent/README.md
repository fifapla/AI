# MCP Windows System Agent

A lightweight Model Context Protocol (MCP) server that exposes native Windows OS metrics and system diagnostic tools to AI assistants (Claude Desktop, AI Agents).

## Features
- **STDIO Communication Protocol**: Fully compliant with MCP specification.
- **Real-time System Metrics**: Exposes CPU usage, Memory consumption, and OS metadata.
- **Extensible**: Easily add new native Windows control capabilities.

## Usage
```bash
pip install psutil
python mcp_server.py