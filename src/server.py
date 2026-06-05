"""
P21 API Documentation MCP Server

An MCP server that provides AI agents with expert knowledge of the
Epicor Prophet 21 (P21) API. Documentation is fetched live from GitHub
and served via Streamable HTTP transport.

Usage:
    # HTTP mode (default)
    python -m src.server

    # HTTP mode with custom port
    python -m src.server --port 9000

    # stdio mode (for Claude Desktop / local tools)
    python -m src.server --transport stdio

The server exposes 5 tools, 11 resources, and 2 prompts covering
all P21 API types: OData, Transaction, Interactive, Entity,
Inventory REST, and Production & Labor.
"""

from __future__ import annotations

import argparse
import os
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from fastmcp.server import FastMCP

from src.docs_loader import DocsIndex
from src.search import DocsSearchEngine


# ── Application state ────────────────────────────────────────────────────────

@dataclass
class AppState:
    """Shared application state initialized at startup."""

    docs_index: DocsIndex
    search_engine: DocsSearchEngine


# ── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppState]:
    """
    Startup: Fetch all P21 documentation from GitHub and build the
    search index. This runs once when the server starts.
    """
    print("=" * 60)
    print("P21 API Documentation MCP Server")
    print("=" * 60)
    print("\nFetching documentation from GitHub...")

    docs_index = await DocsIndex.fetch_from_github()

    doc_count = len(docs_index.documents)
    section_count = len(docs_index.sections)
    example_count = sum(len(v) for v in docs_index.examples.values())

    print(f"  * Loaded {doc_count} documents")
    print(f"  * Parsed {section_count} sections")
    print(f"  * Extracted {example_count} code examples")
    print()

    # Build search index
    print("Building search index...")
    search_engine = DocsSearchEngine(docs_index.sections)
    print(f"  * Indexed {section_count} sections for search")
    print()
    print("Server is ready!")
    print("=" * 60)

    yield AppState(docs_index=docs_index, search_engine=search_engine)

    print("\nServer shutting down. Goodbye!")


# ── Server creation ──────────────────────────────────────────────────────────

mcp = FastMCP(
    name="P21-API-Docs",
    instructions=(
        "You are connected to the P21 API Documentation server. "
        "This server provides expert knowledge of the Epicor Prophet 21 (P21) "
        "ERP system APIs including OData, Transaction, Interactive, Entity, "
        "Inventory REST, and Production & Labor APIs.\n\n"
        "Available tools:\n"
        "- get_p21_api_overview: Start here — get the API comparison table\n"
        "- search_p21_docs: Search for specific topics across all docs\n"
        "- get_p21_api_documentation: Get the full docs for a specific API\n"
        "- get_p21_code_examples: Get code examples for a specific API\n"
        "- get_p21_endpoint_reference: Get URL patterns and HTTP methods\n\n"
        "Always use these tools to look up information rather than guessing."
    ),
    lifespan=app_lifespan,
)

# Register tools, resources, and prompts
from src.tools import register_tools  # noqa: E402
from src.resources import register_resources  # noqa: E402
from src.prompts import register_prompts  # noqa: E402

register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)


# ── CLI entry point ──────────────────────────────────────────────────────────

def main() -> None:
    """CLI entry point for the P21 MCP server."""
    parser = argparse.ArgumentParser(
        description="P21 API Documentation MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m src.server                          # HTTP on 0.0.0.0:8000\n"
            "  python -m src.server --port 9000              # HTTP on custom port\n"
            "  python -m src.server --host 127.0.0.1         # Local only\n"
            "  python -m src.server --transport stdio        # stdio mode\n"
        ),
    )
    parser.add_argument(
        "--transport",
        choices=["streamable-http", "stdio"],
        default=os.environ.get("MCP_TRANSPORT", "streamable-http"),
        help="Transport mode (default: streamable-http)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MCP_HOST", "0.0.0.0"),
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", "8000")),
        help="Port to listen on (default: 8000)",
    )
    args = parser.parse_args()

    if args.transport == "streamable-http":
        print(f"\nStarting HTTP server on {args.host}:{args.port}")
        print(f"MCP endpoint: http://{args.host}:{args.port}/mcp\n")

    mcp.run(
        transport=args.transport,
        host=args.host,
        port=args.port,
    )


if __name__ == "__main__":
    main()
