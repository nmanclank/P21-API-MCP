"""
MCP Tool definitions for the P21 API Documentation server.

These tools allow AI agents to query, search, and retrieve
documentation for all Epicor Prophet 21 API types.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp.server import Context, FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from src.docs_loader import DOC_FILES, DocsIndex
from src.search import DocsSearchEngine

# Valid API type literals for tool parameters
ApiType = Literal[
    "authentication",
    "api_selection_guide",
    "odata",
    "transaction",
    "interactive",
    "entity",
    "inventory_rest",
    "production_labor",
    "changelog",
]

VALID_API_TYPES = list(DOC_FILES.keys())


def _get_state(ctx: Context) -> tuple[DocsIndex, DocsSearchEngine]:
    """Extract the shared app state from the request context."""
    state = ctx.request_context.lifespan_context
    return state.docs_index, state.search_engine


def register_tools(mcp: FastMCP) -> None:
    """Register all P21 documentation tools on the FastMCP server."""

    @mcp.tool()
    async def get_p21_api_documentation(
        api_type: Annotated[
            ApiType,
            Field(
                description=(
                    "The P21 API type to retrieve documentation for. "
                    "Options: authentication, api_selection_guide, odata, "
                    "transaction, interactive, entity, inventory_rest, "
                    "production_labor, changelog"
                )
            ),
        ],
        ctx: Context,
    ) -> str:
        """Retrieve the COMPLETE documentation for a specific P21 API type.

        Use this tool when you need the full reference for an API, including
        endpoints, HTTP methods, parameters, request/response formats, and
        Python code examples.

        This returns the entire markdown document — use search_p21_docs
        instead if you only need a specific topic.
        """
        docs_index, _ = _get_state(ctx)
        doc = docs_index.get_document(api_type)
        if doc is None:
            raise ToolError(
                f"Unknown API type '{api_type}'. "
                f"Valid types: {', '.join(VALID_API_TYPES)}"
            )
        await ctx.info(f"Retrieved {api_type} documentation ({len(doc):,} chars)")
        return doc

    @mcp.tool()
    async def search_p21_docs(
        query: Annotated[
            str,
            Field(description="Free-text search query, e.g. 'filter OData by date' or 'session management'"),
        ],
        api_type: Annotated[
            ApiType | None,
            Field(
                description=(
                    "Optional: restrict search to a specific API type. "
                    "Leave empty to search across ALL documentation."
                ),
                default=None,
            ),
        ] = None,
        max_results: Annotated[
            int,
            Field(description="Maximum number of results to return (1-20)", ge=1, le=20, default=5),
        ] = 5,
        ctx: Context = None,
    ) -> str:
        """Search across ALL P21 API documentation for relevant sections.

        Use this tool when you have a specific question and need targeted
        answers — e.g., 'how do I paginate OData results', 'what is the
        authentication token endpoint', 'how to add a line item in
        Interactive API'.

        Returns ranked sections with snippets and code examples when available.
        """
        _, search_engine = _get_state(ctx)
        results = search_engine.search(query, api_type=api_type, max_results=max_results)

        if not results:
            return (
                f"No results found for '{query}'"
                + (f" in {api_type} docs" if api_type else "")
                + ". Try broader terms or a different api_type filter."
            )

        output_parts: list[str] = []
        output_parts.append(f"## Search Results for: \"{query}\"\n")

        for i, r in enumerate(results, 1):
            output_parts.append(f"### {i}. [{r.api_type}] {r.heading}")
            output_parts.append(f"**Relevance:** {r.score}")
            output_parts.append(f"\n{r.snippet}\n")
            if r.code_example:
                output_parts.append(f"**Code example:**\n```\n{r.code_example}\n```\n")
            output_parts.append("---")

        await ctx.info(f"Found {len(results)} results for '{query}'")
        return "\n".join(output_parts)

    @mcp.tool()
    async def get_p21_code_examples(
        api_type: Annotated[
            ApiType,
            Field(
                description=(
                    "The P21 API type to get code examples for. "
                    "Options: authentication, odata, transaction, interactive, "
                    "entity, inventory_rest, production_labor"
                )
            ),
        ],
        ctx: Context,
    ) -> str:
        """Retrieve ALL code examples from the documentation for a specific P21 API type.

        Use this tool when you need working Python code samples for a
        specific API — e.g., authentication token generation, OData queries,
        Interactive API session management, Entity CRUD operations.
        """
        docs_index, _ = _get_state(ctx)
        examples = docs_index.get_examples(api_type)

        if not examples:
            raise ToolError(
                f"No code examples found for '{api_type}'. "
                f"Try get_p21_api_documentation('{api_type}') for the full docs."
            )

        output_parts: list[str] = [
            f"## Code Examples: {api_type}\n",
            f"Found {len(examples)} code example(s):\n",
        ]
        for i, example in enumerate(examples, 1):
            output_parts.append(f"### Example {i}")
            output_parts.append(f"```python\n{example}\n```\n")

        await ctx.info(f"Retrieved {len(examples)} code examples for {api_type}")
        return "\n".join(output_parts)

    @mcp.tool()
    async def get_p21_api_overview(
        ctx: Context,
    ) -> str:
        """Get a high-level overview of ALL available P21 APIs and when to use each one.

        Use this tool FIRST when you need to understand the P21 API landscape
        or decide which API is right for a particular use case.

        Returns an API comparison table and the selection guide.
        """
        docs_index, _ = _get_state(ctx)

        parts: list[str] = []

        # Build the overview from the selection guide
        guide = docs_index.get_document("api_selection_guide")
        if guide:
            parts.append(guide)
        else:
            parts.append("# P21 API Overview\n")

        # Append the quick summary table
        parts.append("\n## Quick API Reference\n")
        parts.append("| API Type | Key | Purpose | State |")
        parts.append("|----------|-----|---------|-------|")
        parts.append("| OData | `odata` | Read-only data access (OData V4) | Stateless |")
        parts.append("| Transaction | `transaction` | Bulk data manipulation | Stateless |")
        parts.append("| Interactive | `interactive` | Window-like workflows with business logic | Stateful |")
        parts.append("| Entity | `entity` | Simple CRUD on business objects | Stateless |")
        parts.append("| Inventory REST | `inventory_rest` | Inventory CRUD, multi-company | Stateless |")
        parts.append("| Production & Labor | `production_labor` | Manufacturing workflows | Stateless |")
        parts.append("")
        parts.append("Use `get_p21_api_documentation(api_type)` to get the full docs for any API.")

        await ctx.info("Retrieved P21 API overview")
        return "\n".join(parts)

    @mcp.tool()
    async def get_p21_endpoint_reference(
        api_type: Annotated[
            Literal["odata", "transaction", "interactive", "entity", "inventory_rest", "production_labor"],
            Field(description="The P21 API type to get endpoint patterns for"),
        ],
        ctx: Context,
    ) -> str:
        """Get the endpoint URL patterns, HTTP methods, and common entities for a specific P21 API.

        Use this tool when you need the exact URL structure, HTTP methods,
        and available entities/resources for constructing API calls.
        """
        # Static reference data for each API type
        references: dict[str, str] = {
            "odata": (
                "## OData API Endpoint Reference\n\n"
                "**Base URL:** `https://{middleware}/odataservice/odata/{table|view}/{entity}`\n\n"
                "**HTTP Methods:** GET only (read-only)\n\n"
                "**Resource Types:**\n"
                "- `table` — Direct database table access\n"
                "- `view` — Pre-defined database views\n\n"
                "**Query Parameters:**\n"
                "- `$filter` — Filter results (operators: eq, ne, gt, lt, ge, le, startswith, contains)\n"
                "- `$select` — Choose specific fields\n"
                "- `$orderby` — Sort results (asc/desc)\n"
                "- `$top` — Limit number of results\n"
                "- `$skip` — Skip N results (pagination)\n"
                "- `$count` — Include total count\n\n"
                "**Common Entities:** customer, address, inv_mast, oe_hdr, oe_line, po_hdr, contacts\n\n"
                "**Example:** `GET /odataservice/odata/table/address?$filter=City eq 'Chicago'&$select=AddressID,City,State&$top=10`"
            ),
            "transaction": (
                "## Transaction API Endpoint Reference\n\n"
                "**Base URL:** `https://{middleware}/api/transaction/`\n\n"
                "**HTTP Methods:** GET (service discovery), POST (execute)\n\n"
                "**Content Types:** application/json, application/xml\n\n"
                "**Pattern:** Discover available transactions → Build request payload → POST to execute\n\n"
                "**Common Operations:** Sales orders, purchase orders, item creation, bulk record processing\n\n"
                "**Key Feature:** Supports XML and JSON payloads, template-based approach"
            ),
            "interactive": (
                "## Interactive API Endpoint Reference\n\n"
                "**Base URL:** `https://{middleware}/api/interactive/`\n\n"
                "**HTTP Methods:** POST (all operations)\n\n"
                "**Session Lifecycle:**\n"
                "1. Initialize session\n"
                "2. Open window (by WindowID)\n"
                "3. Get/Set field values\n"
                "4. Trigger events / click buttons\n"
                "5. Save changes\n"
                "6. Close window & session\n\n"
                "**Key Operations:** Session init, window open/close, field get/set, event trigger, navigation\n\n"
                "**Common Windows:** SalesOrder, PurchaseOrder, Customer, Item, Invoice, Receiving, Transfer\n\n"
                "**Important:** Stateful — always close sessions to avoid resource leaks. "
                "P21 business logic is triggered in order."
            ),
            "entity": (
                "## Entity API Endpoint Reference\n\n"
                "**Base URL:** `https://{middleware}/api/entity/{resource}/`\n\n"
                "**HTTP Methods:** GET, POST, PUT, DELETE\n\n"
                "**Common Entities:**\n"
                "- `vendors/` — Vendor management\n"
                "- `customers/` — Customer management\n"
                "- `oe_hdr/` — Order headers\n"
                "- `oe_line/` — Order lines\n"
                "- `inv_mast/` — Inventory master\n"
                "- `address/` — Addresses\n"
                "- `contacts/` — Contacts\n\n"
                "**Examples:**\n"
                "- `GET /api/entity/vendors/` — List vendors\n"
                "- `POST /api/entity/vendors/` — Create vendor\n"
                "- `PUT /api/entity/vendors/{id}` — Update vendor\n"
                "- `DELETE /api/entity/vendors/{id}` — Delete vendor\n\n"
                "**Note:** Some records may not support DELETE — use cancel status via PUT instead."
            ),
            "inventory_rest": (
                "## Inventory REST API Endpoint Reference\n\n"
                "**Base URL:** `https://{middleware}/api/inventory/`\n\n"
                "**HTTP Methods:** GET, POST, PUT, DELETE\n\n"
                "**Key Endpoints:**\n"
                "- `/api/inventory/parts/` — Inventory items (inv_mast)\n"
                "- Locations and suppliers management\n\n"
                "**Features:** Multi-company support, item CRUD, location/supplier management\n\n"
                "**Common Operations:** Create items, read items, update items, manage locations and suppliers"
            ),
            "production_labor": (
                "## Production & Labor API Endpoint Reference\n\n"
                "**Base URL:** `https://{middleware}/api/production/`\n\n"
                "**HTTP Methods:** GET, POST, PUT\n\n"
                "**Key Features:**\n"
                "- Production/work orders management\n"
                "- Labor hours tracking\n"
                "- Time entry for manufacturing\n"
                "- Manufacturing order lifecycle\n\n"
                "**Tip:** Enable client tracing in P21 to capture exact service methods and parameters."
            ),
        }

        ref = references.get(api_type)
        if ref is None:
            raise ToolError(f"No endpoint reference for '{api_type}'.")

        await ctx.info(f"Retrieved endpoint reference for {api_type}")
        return ref
