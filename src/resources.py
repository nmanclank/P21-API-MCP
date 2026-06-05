"""
MCP Resource definitions for the P21 API Documentation server.

Resources expose raw documentation as browseable, URI-addressable
content that MCP clients can discover and read.
"""

from __future__ import annotations

from fastmcp.server import Context, FastMCP

from src.docs_loader import DOC_FILES, ROOT_FILES


def register_resources(mcp: FastMCP) -> None:
    """Register all P21 documentation resources on the FastMCP server."""

    @mcp.resource(
        "docs://p21/overview",
        description="P21 API project overview, quick-start guide, and links to all API docs",
    )
    async def get_overview(ctx: Context) -> str:
        """Get the P21 API Documentation project overview (README)."""
        state = ctx.request_context.lifespan_context
        return state.docs_index.get_document("readme") or "Overview not available."

    @mcp.resource(
        "docs://p21/authentication",
        description="P21 API authentication guide — token generation, consumer keys, session management",
    )
    async def get_auth_docs(ctx: Context) -> str:
        """Get the P21 authentication documentation."""
        state = ctx.request_context.lifespan_context
        return state.docs_index.get_document("authentication") or "Authentication docs not available."

    @mcp.resource(
        "docs://p21/api-selection-guide",
        description="Decision guide for choosing the right P21 API type for your use case",
    )
    async def get_selection_guide(ctx: Context) -> str:
        """Get the P21 API selection guide."""
        state = ctx.request_context.lifespan_context
        return state.docs_index.get_document("api_selection_guide") or "Selection guide not available."

    @mcp.resource(
        "docs://p21/odata",
        description="OData API documentation — read-only data access using OData V4 protocol",
    )
    async def get_odata_docs(ctx: Context) -> str:
        """Get the OData API documentation."""
        state = ctx.request_context.lifespan_context
        return state.docs_index.get_document("odata") or "OData docs not available."

    @mcp.resource(
        "docs://p21/transaction",
        description="Transaction API documentation — stateless bulk data manipulation",
    )
    async def get_transaction_docs(ctx: Context) -> str:
        """Get the Transaction API documentation."""
        state = ctx.request_context.lifespan_context
        return state.docs_index.get_document("transaction") or "Transaction docs not available."

    @mcp.resource(
        "docs://p21/interactive",
        description="Interactive API documentation — stateful window-based workflows with business logic",
    )
    async def get_interactive_docs(ctx: Context) -> str:
        """Get the Interactive API documentation."""
        state = ctx.request_context.lifespan_context
        return state.docs_index.get_document("interactive") or "Interactive docs not available."

    @mcp.resource(
        "docs://p21/entity",
        description="Entity API documentation — simple CRUD on P21 business objects",
    )
    async def get_entity_docs(ctx: Context) -> str:
        """Get the Entity API documentation."""
        state = ctx.request_context.lifespan_context
        return state.docs_index.get_document("entity") or "Entity docs not available."

    @mcp.resource(
        "docs://p21/inventory-rest",
        description="Inventory REST API documentation — inventory CRUD with multi-company support",
    )
    async def get_inventory_docs(ctx: Context) -> str:
        """Get the Inventory REST API documentation."""
        state = ctx.request_context.lifespan_context
        return state.docs_index.get_document("inventory_rest") or "Inventory REST docs not available."

    @mcp.resource(
        "docs://p21/production-labor",
        description="Production & Labor API documentation — manufacturing workflows and labor tracking",
    )
    async def get_production_docs(ctx: Context) -> str:
        """Get the Production & Labor API documentation."""
        state = ctx.request_context.lifespan_context
        return state.docs_index.get_document("production_labor") or "Production & Labor docs not available."

    @mcp.resource(
        "docs://p21/changelog",
        description="P21 API documentation changelog — version history and recent updates",
    )
    async def get_changelog(ctx: Context) -> str:
        """Get the documentation changelog."""
        state = ctx.request_context.lifespan_context
        return state.docs_index.get_document("changelog") or "Changelog not available."

    @mcp.resource(
        "docs://p21/all-api-types",
        description="List of all available P21 API types with their keys for use with tools",
    )
    async def list_api_types(ctx: Context) -> str:
        """List all available API type keys."""
        state = ctx.request_context.lifespan_context
        types = state.docs_index.list_api_types()
        lines = ["# Available P21 API Types\n"]
        lines.append("Use these keys with the `get_p21_api_documentation` tool:\n")
        for t in types:
            doc = state.docs_index.get_document(t)
            size = f" ({len(doc):,} chars)" if doc else ""
            lines.append(f"- `{t}`{size}")
        return "\n".join(lines)
