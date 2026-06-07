# P21 API Documentation MCP Server

A [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that gives AI agents **expert knowledge** of the [Epicor Prophet 21 (P21)](https://www.epicor.com/en-us/erp-systems/prophet-21/) API system.

Documentation is fetched live from [mrwuss/p21-api-documentation](https://github.com/mrwuss/p21-api-documentation) and served via **Streamable HTTP** transport — no local docs to maintain.

> **Disclaimer:** This project is not affiliated with, endorsed by, or supported by Epicor Software Corporation.

---

## What It Does

This MCP server exposes **5 tools**, **11 resources**, and **2 prompts** that allow AI agents to:

- 🔍 **Search** across all P21 API documentation for specific topics
- 📖 **Retrieve** complete documentation for any API type
- 💻 **Get code examples** — working Python samples for every API
- 🗺️ **Compare APIs** — overview table to pick the right API for the job
- 🔗 **Look up endpoints** — exact URL patterns, HTTP methods, and entities

### Covered APIs

| API | Type | Use Case |
|-----|------|----------|
| **OData** | Read-only | Reporting, lookups, data exports |
| **Transaction** | Bulk CRUD | Bulk creates, external integrations |
| **Interactive** | Stateful | Window workflows with business logic |
| **Entity** | Simple CRUD | Basic record operations |
| **Inventory REST** | Inventory | Item CRUD, multi-company |
| **Production & Labor** | Manufacturing | Work orders, time tracking |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Internet access (docs are fetched from GitHub)

### Install

```bash
# Clone the repository
git clone https://github.com/your-username/P21-API-MCP.git
cd P21-API-MCP

# Create a virtual environment
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Run the Server

```bash
# Start with HTTP transport (default)
python -m src.server

# Custom port
python -m src.server --port 9000

# Local-only binding
python -m src.server --host 127.0.0.1

# stdio mode (for Claude Desktop)
python -m src.server --transport stdio
```

The server will:
1. Fetch all P21 API documentation from GitHub
2. Parse it into searchable sections
3. Start listening on `http://0.0.0.0:8000/mcp`

---

## Connect Your MCP Client

### Claude Code / Cursor / VS Code

Add to your MCP config file:

```json
{
  "mcpServers": {
    "p21-api-docs": {
      "type": "streamable-http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Claude Desktop (stdio bridge)

```json
{
  "mcpServers": {
    "p21-api-docs": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8000/mcp"]
    }
  }
}
```

### Config File Locations

| Client | Path |
|--------|------|
| Claude Desktop (Win) | `%APPDATA%\Claude\claude_desktop_config.json` |
| Cursor | `~/.cursor/mcp.json` |
| VS Code | `.vscode/mcp.json` |
| Claude Code | `~/.claude/mcp.json` |

---

## Available Tools

| Tool | Description |
|------|-------------|
| `get_p21_api_overview` | High-level comparison of all P21 APIs + selection guide |
| `search_p21_docs` | Search across all docs for specific topics |
| `get_p21_api_documentation` | Retrieve the full docs for a specific API type |
| `get_p21_code_examples` | Get Python code examples for a specific API |
| `get_p21_endpoint_reference` | URL patterns, HTTP methods, and entities |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_HOST` | `0.0.0.0` | Host to bind to |
| `MCP_PORT` | `8000` | Port to listen on |
| `MCP_TRANSPORT` | `streamable-http` | Transport mode |

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v
```

---

## License

MIT

## Credits

- P21 API documentation by [mrwuss/p21-api-documentation](https://github.com/mrwuss/p21-api-documentation)
- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Powered by the [Model Context Protocol](https://modelcontextprotocol.io/)
