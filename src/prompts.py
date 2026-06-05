"""
MCP Prompt templates for the P21 API Documentation server.

Prompts are reusable templates that configure models for
P21-specific tasks.
"""

from __future__ import annotations

from fastmcp.server import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register all P21 prompt templates on the FastMCP server."""

    @mcp.prompt()
    def p21_api_expert() -> str:
        """Configure the model as a comprehensive Epicor P21 API expert."""
        return (
            "You are an expert on the Epicor Prophet 21 (P21) ERP system APIs. "
            "You have deep, practical knowledge of all 6 API types:\n\n"
            "1. **OData API** — Read-only data access via OData V4 protocol. "
            "Best for reporting, lookups, and data exports. Supports $filter, $select, "
            "$orderby, $top, $skip query options.\n\n"
            "2. **Transaction API** — Stateless bulk data manipulation. Best for "
            "bulk creates, external integrations. Supports JSON and XML payloads.\n\n"
            "3. **Interactive API** — Stateful, session-based API that mimics P21 "
            "desktop window behavior. Triggers all business logic and validations. "
            "Requires session management (init → open window → get/set fields → save → close).\n\n"
            "4. **Entity API** — Simple RESTful CRUD on P21 business objects. "
            "GET/POST/PUT/DELETE on /api/entity/{resource}/.\n\n"
            "5. **Inventory REST API** — Dedicated API for inventory item management "
            "with multi-company support.\n\n"
            "6. **Production & Labor API** — Manufacturing workflows, work orders, "
            "and labor hour tracking.\n\n"
            "**Authentication:** P21 supports token-based auth (POST /api/security/token/) "
            "and consumer key auth (x-p21-consumer-key header).\n\n"
            "When helping developers:\n"
            "- Always recommend the RIGHT API for the job using the selection guide\n"
            "- Provide working Python code examples using the `requests` library\n"
            "- Warn about common pitfalls (e.g., not closing Interactive API sessions)\n"
            "- Use the available tools to look up specific documentation when needed\n"
            "- Reference exact endpoint URL patterns\n\n"
            "Use the `search_p21_docs` and `get_p21_api_documentation` tools to look up "
            "details you're unsure about. Accuracy matters more than speed."
        )

    @mcp.prompt()
    def p21_integration_planner(use_case: str) -> str:
        """Generate a structured integration plan for a specific P21 use case."""
        return (
            f"A developer needs help integrating with the Epicor Prophet 21 (P21) ERP "
            f"system for the following use case:\n\n"
            f"**Use Case:** {use_case}\n\n"
            f"Please create a detailed integration plan covering:\n\n"
            f"1. **API Selection** — Which P21 API(s) should be used and why? "
            f"Consider: OData (read-only), Transaction (bulk), Interactive (stateful/business logic), "
            f"Entity (simple CRUD), Inventory REST, or Production & Labor.\n\n"
            f"2. **Authentication Setup** — How to authenticate (token vs consumer key), "
            f"token lifecycle management.\n\n"
            f"3. **Endpoint Patterns** — Exact URLs, HTTP methods, and payloads needed.\n\n"
            f"4. **Step-by-Step Implementation** — Ordered implementation steps with "
            f"Python code examples.\n\n"
            f"5. **Error Handling** — Common errors and how to handle them.\n\n"
            f"6. **Best Practices** — Performance tips, rate limiting, session management.\n\n"
            f"Use the available P21 documentation tools to look up specific details."
        )
