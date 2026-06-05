"""
Documentation loader that fetches P21 API docs live from GitHub
and parses them into structured, searchable sections.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx


# ── GitHub repository configuration ──────────────────────────────────────────

GITHUB_REPO = "mrwuss/p21-api-documentation"
GITHUB_BRANCH = "master"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"

# Map of logical API type keys → file paths in the repository
DOC_FILES: dict[str, str] = {
    "authentication": "docs/00-Authentication.md",
    "api_selection_guide": "docs/01-API-Selection-Guide.md",
    "odata": "docs/02-OData-API.md",
    "transaction": "docs/03-Transaction-API.md",
    "interactive": "docs/04-Interactive-API.md",
    "entity": "docs/05-Entity-API.md",
    "inventory_rest": "docs/06-Inventory-REST-API.md",
    "production_labor": "docs/07-Production-and-Labor-API.md",
    "changelog": "docs/10-Changelog.md",
}

# Also fetch these root-level files
ROOT_FILES: dict[str, str] = {
    "readme": "README.md",
    "claude_instructions": "CLAUDE.md",
}

# Cache TTL in seconds (default: 1 hour)
CACHE_TTL = 3600


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class DocSection:
    """A single heading-delimited section within a documentation file."""

    api_type: str       # Logical key, e.g. "odata"
    heading: str        # Section heading text
    level: int          # Heading level (1, 2, or 3)
    content: str        # Full section text including the heading line
    code_examples: list[str] = field(default_factory=list)

    @property
    def search_text(self) -> str:
        """Combined text for search indexing."""
        return f"{self.heading}\n{self.content}"


@dataclass
class DocsIndex:
    """
    In-memory index of all P21 API documentation, fetched from GitHub.
    Provides fast lookup by API type and section-level search.
    """

    documents: dict[str, str]          # api_type → full markdown text
    sections: list[DocSection]         # All sections across all docs
    examples: dict[str, list[str]]     # api_type → extracted code blocks
    fetched_at: float = 0.0            # Timestamp of last fetch

    # ── Lookup helpers ────────────────────────────────────────────────────

    def get_document(self, api_type: str) -> Optional[str]:
        """Get the full markdown for an API type."""
        return self.documents.get(api_type)

    def get_sections(self, api_type: Optional[str] = None) -> list[DocSection]:
        """Get sections, optionally filtered by API type."""
        if api_type is None:
            return self.sections
        return [s for s in self.sections if s.api_type == api_type]

    def get_examples(self, api_type: str) -> list[str]:
        """Get all code examples for an API type."""
        return self.examples.get(api_type, [])

    def list_api_types(self) -> list[str]:
        """Return all available API type keys."""
        return list(self.documents.keys())

    @property
    def is_stale(self) -> bool:
        """Check if the cache has expired."""
        return (time.time() - self.fetched_at) > CACHE_TTL

    # ── Factory ───────────────────────────────────────────────────────────

    @classmethod
    async def fetch_from_github(cls) -> "DocsIndex":
        """Fetch all documentation from GitHub and build the index."""
        documents: dict[str, str] = {}
        sections: list[DocSection] = []
        examples: dict[str, list[str]] = {}

        all_files = {**DOC_FILES, **ROOT_FILES}

        async with httpx.AsyncClient(timeout=30.0) as client:
            for api_type, file_path in all_files.items():
                url = f"{GITHUB_RAW_BASE}/{file_path}"
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        content = resp.text
                        documents[api_type] = content

                        # Parse into sections
                        file_sections = _parse_sections(api_type, content)
                        sections.extend(file_sections)

                        # Extract code examples
                        file_examples = _extract_code_blocks(content)
                        if file_examples:
                            examples[api_type] = file_examples
                    else:
                        print(f"  Warning: Could not fetch {file_path} (HTTP {resp.status_code})")
                except httpx.HTTPError as exc:
                    print(f"  Warning: Error fetching {file_path}: {exc}")

        return cls(
            documents=documents,
            sections=sections,
            examples=examples,
            fetched_at=time.time(),
        )


# ── Markdown parsing helpers ─────────────────────────────────────────────────

_HEADING_RE = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)
_CODE_BLOCK_RE = re.compile(r"```[\w]*\n(.*?)```", re.DOTALL)


def _parse_sections(api_type: str, markdown: str) -> list[DocSection]:
    """Split a markdown document into sections by heading."""
    headings = list(_HEADING_RE.finditer(markdown))

    if not headings:
        # No headings — treat the whole file as one section
        return [
            DocSection(
                api_type=api_type,
                heading=api_type,
                level=1,
                content=markdown.strip(),
                code_examples=_extract_code_blocks(markdown),
            )
        ]

    sections: list[DocSection] = []
    for i, match in enumerate(headings):
        level = len(match.group(1))
        heading = match.group(2).strip()
        start = match.start()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(markdown)
        content = markdown[start:end].strip()
        code_examples = _extract_code_blocks(content)

        sections.append(
            DocSection(
                api_type=api_type,
                heading=heading,
                level=level,
                content=content,
                code_examples=code_examples,
            )
        )

    return sections


def _extract_code_blocks(text: str) -> list[str]:
    """Extract fenced code blocks from markdown text."""
    return [m.group(1).strip() for m in _CODE_BLOCK_RE.finditer(text)]
