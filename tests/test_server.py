"""
Tests for the P21 API Documentation MCP Server.

Tests cover documentation loading, search functionality,
and basic server operation.
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from src.docs_loader import DocsIndex, DocSection, _parse_sections, _extract_code_blocks
from src.search import DocsSearchEngine, SearchResult, _tokenize


# ── Tokenizer tests ──────────────────────────────────────────────────────────

class TestTokenizer:
    def test_basic_tokenization(self):
        tokens = _tokenize("Hello world, this is a test")
        # "this", "is", "a" are stop words
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens

    def test_stops_words_removed(self):
        tokens = _tokenize("the quick brown fox is a very fast animal")
        assert "the" not in tokens
        assert "is" not in tokens
        assert "a" not in tokens
        assert "very" not in tokens

    def test_single_char_removed(self):
        tokens = _tokenize("I a x go")
        # single chars should be filtered out
        for t in tokens:
            assert len(t) > 1

    def test_preserves_api_terms(self):
        tokens = _tokenize("OData $filter $select endpoint")
        assert "odata" in tokens
        assert "$filter" in tokens
        assert "$select" in tokens
        assert "endpoint" in tokens


# ── Markdown parsing tests ───────────────────────────────────────────────────

class TestMarkdownParsing:
    def test_parse_sections_basic(self):
        md = "# Title\nSome content\n## Section A\nContent A\n## Section B\nContent B"
        sections = _parse_sections("test", md)
        assert len(sections) == 3
        assert sections[0].heading == "Title"
        assert sections[0].level == 1
        assert sections[1].heading == "Section A"
        assert sections[2].heading == "Section B"

    def test_parse_sections_no_headings(self):
        md = "Just plain text without any headings."
        sections = _parse_sections("test", md)
        assert len(sections) == 1
        assert sections[0].api_type == "test"

    def test_parse_sections_with_code(self):
        md = "# Example\nSome text\n```python\nprint('hello')\n```\nMore text"
        sections = _parse_sections("test", md)
        assert len(sections) == 1
        assert len(sections[0].code_examples) == 1
        assert "print('hello')" in sections[0].code_examples[0]

    def test_extract_code_blocks(self):
        md = "Text\n```python\ncode1\n```\nMore\n```json\ncode2\n```"
        blocks = _extract_code_blocks(md)
        assert len(blocks) == 2
        assert "code1" in blocks[0]
        assert "code2" in blocks[1]

    def test_extract_no_code_blocks(self):
        md = "No code blocks here."
        blocks = _extract_code_blocks(md)
        assert blocks == []


# ── Search engine tests ──────────────────────────────────────────────────────

class TestSearchEngine:
    @pytest.fixture
    def sample_sections(self) -> list[DocSection]:
        return [
            DocSection(
                api_type="odata",
                heading="OData Query Options",
                level=2,
                content="The OData API supports $filter, $select, $orderby, $top, and $skip query parameters for data filtering and pagination.",
                code_examples=["requests.get(url, params={'$filter': 'City eq Chicago'})"],
            ),
            DocSection(
                api_type="odata",
                heading="OData Pagination",
                level=2,
                content="Use $top and $skip for pagination. Example: $top=10&$skip=20 to get the third page of 10 results.",
                code_examples=[],
            ),
            DocSection(
                api_type="interactive",
                heading="Session Management",
                level=2,
                content="The Interactive API requires session management. Initialize a session, open a window, perform operations, then close the session.",
                code_examples=["session = requests.post(f'{base}/api/interactive/init')"],
            ),
            DocSection(
                api_type="authentication",
                heading="Token Generation",
                level=2,
                content="POST to /api/security/token/ with username and password to get a Bearer token for authentication.",
                code_examples=["response = requests.post(f'{base}/api/security/token/', json={'username': user, 'password': pwd})"],
            ),
            DocSection(
                api_type="entity",
                heading="Entity CRUD Operations",
                level=2,
                content="The Entity API supports GET, POST, PUT, DELETE on /api/entity/{resource}/ for simple CRUD operations on business objects like vendors and customers.",
                code_examples=["requests.get(f'{base}/api/entity/vendors/')"],
            ),
        ]

    @pytest.fixture
    def engine(self, sample_sections: list[DocSection]) -> DocsSearchEngine:
        return DocsSearchEngine(sample_sections)

    def test_search_returns_results(self, engine: DocsSearchEngine):
        results = engine.search("filter query")
        assert len(results) > 0

    def test_search_odata_filter(self, engine: DocsSearchEngine):
        results = engine.search("$filter query options")
        assert results[0].api_type == "odata"
        assert "OData" in results[0].heading or "filter" in results[0].snippet.lower()

    def test_search_with_api_type_filter(self, engine: DocsSearchEngine):
        results = engine.search("session", api_type="interactive")
        assert all(r.api_type == "interactive" for r in results)

    def test_search_no_results(self, engine: DocsSearchEngine):
        results = engine.search("xyznonexistentterm123")
        assert results == []

    def test_search_max_results(self, engine: DocsSearchEngine):
        results = engine.search("api", max_results=2)
        assert len(results) <= 2

    def test_search_pagination(self, engine: DocsSearchEngine):
        results = engine.search("pagination")
        assert len(results) > 0
        # The pagination section should score well
        headings = [r.heading for r in results]
        assert any("Pagination" in h or "pagination" in h.lower() for h in headings)

    def test_search_authentication(self, engine: DocsSearchEngine):
        results = engine.search("token authentication")
        assert len(results) > 0
        assert results[0].api_type == "authentication"

    def test_search_returns_code_examples(self, engine: DocsSearchEngine):
        results = engine.search("$filter")
        odata_results = [r for r in results if r.api_type == "odata"]
        assert len(odata_results) > 0
        # The OData filter section has code examples
        has_code = any(r.code_example is not None for r in odata_results)
        assert has_code


# ── DocsIndex tests ──────────────────────────────────────────────────────────

class TestDocsIndex:
    @pytest.fixture
    def mock_index(self) -> DocsIndex:
        return DocsIndex(
            documents={
                "odata": "# OData API\nRead-only access...",
                "entity": "# Entity API\nCRUD operations...",
            },
            sections=[
                DocSection(api_type="odata", heading="OData API", level=1, content="Read-only access"),
                DocSection(api_type="entity", heading="Entity API", level=1, content="CRUD operations"),
            ],
            examples={
                "odata": ["requests.get(url)"],
                "entity": ["requests.post(url, json=data)"],
            },
            fetched_at=0.0,
        )

    def test_get_document(self, mock_index: DocsIndex):
        assert mock_index.get_document("odata") is not None
        assert "OData" in mock_index.get_document("odata")

    def test_get_document_missing(self, mock_index: DocsIndex):
        assert mock_index.get_document("nonexistent") is None

    def test_get_sections(self, mock_index: DocsIndex):
        all_sections = mock_index.get_sections()
        assert len(all_sections) == 2

    def test_get_sections_filtered(self, mock_index: DocsIndex):
        odata_sections = mock_index.get_sections("odata")
        assert len(odata_sections) == 1
        assert odata_sections[0].api_type == "odata"

    def test_get_examples(self, mock_index: DocsIndex):
        examples = mock_index.get_examples("odata")
        assert len(examples) == 1

    def test_list_api_types(self, mock_index: DocsIndex):
        types = mock_index.list_api_types()
        assert "odata" in types
        assert "entity" in types

    def test_is_stale(self, mock_index: DocsIndex):
        # fetched_at=0.0 should always be stale
        assert mock_index.is_stale is True


# ── Integration test: fetch from GitHub ──────────────────────────────────────

class TestGitHubFetch:
    @pytest.mark.asyncio
    async def test_fetch_from_github(self):
        """Integration test: actually fetch docs from GitHub."""
        index = await DocsIndex.fetch_from_github()

        # Should have loaded multiple documents
        assert len(index.documents) > 0, "No documents were fetched"

        # Should have parsed sections
        assert len(index.sections) > 0, "No sections were parsed"

        # Key docs should be present
        api_types = index.list_api_types()
        for expected in ["odata", "authentication"]:
            assert expected in api_types, f"Missing expected doc: {expected}"

        # Should not be stale (just fetched)
        assert index.is_stale is False
