"""
Lightweight TF-IDF search engine for P21 API documentation.

No external dependencies — uses only Python stdlib for tokenization
and scoring. Designed for a small corpus (~10 documents) where
full-text search is more than sufficient.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from src.docs_loader import DocSection


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class SearchResult:
    """A single search result with context."""

    api_type: str
    heading: str
    snippet: str               # ~500 char content preview
    score: float
    code_example: Optional[str]  # First code block in section, if any
    section_content: str       # Full section content for detailed reading


# ── Tokenization ─────────────────────────────────────────────────────────────

_TOKEN_RE = re.compile(r"[a-z0-9_$]+", re.IGNORECASE)

# Common words to skip during indexing
_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "is", "it", "as", "be", "are", "was", "were",
    "this", "that", "from", "can", "will", "has", "have", "had", "not",
    "you", "we", "they", "he", "she", "do", "does", "did", "if", "so",
    "no", "yes", "all", "any", "each", "more", "most", "than", "then",
    "very", "just", "also", "about", "up", "out", "its", "your", "our",
    "their", "which", "what", "when", "where", "how", "who", "why",
    "been", "being", "some", "would", "could", "should", "may", "might",
    "must", "shall", "into", "only", "other", "such", "use", "using",
    "used", "like", "make", "see", "get", "set",
})


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase words, filtering stop words."""
    tokens = _TOKEN_RE.findall(text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


# ── Search engine ────────────────────────────────────────────────────────────

class DocsSearchEngine:
    """TF-IDF based search over documentation sections."""

    def __init__(self, sections: list[DocSection]) -> None:
        self._sections = sections
        self._doc_count = len(sections)

        # Build token → document frequency mapping
        self._df: Counter[str] = Counter()
        self._section_tokens: list[list[str]] = []

        for section in sections:
            tokens = _tokenize(section.search_text)
            self._section_tokens.append(tokens)
            # Document frequency: count each unique token once per section
            unique = set(tokens)
            for token in unique:
                self._df[token] += 1

    def search(
        self,
        query: str,
        api_type: Optional[str] = None,
        max_results: int = 5,
    ) -> list[SearchResult]:
        """
        Search documentation sections for the given query.

        Args:
            query: Free-text search query.
            api_type: Optional filter to restrict results to one API type.
            max_results: Maximum number of results to return.

        Returns:
            Ranked list of SearchResult objects.
        """
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scored: list[tuple[float, int]] = []

        for idx, section in enumerate(self._sections):
            # Apply API type filter
            if api_type and section.api_type != api_type:
                continue

            score = self._score_section(query_tokens, idx, section)
            if score > 0:
                scored.append((score, idx))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # If TF-IDF yields nothing, fall back to substring matching
        if not scored:
            scored = self._substring_fallback(query, api_type)

        results: list[SearchResult] = []
        for score, idx in scored[:max_results]:
            section = self._sections[idx]
            snippet = _make_snippet(section.content, query, max_len=500)
            code_example = section.code_examples[0] if section.code_examples else None

            results.append(
                SearchResult(
                    api_type=section.api_type,
                    heading=section.heading,
                    snippet=snippet,
                    score=round(score, 4),
                    code_example=code_example,
                    section_content=section.content,
                )
            )

        return results

    def _score_section(
        self,
        query_tokens: list[str],
        idx: int,
        section: DocSection,
    ) -> float:
        """Compute a TF-IDF relevance score for a section against query tokens."""
        section_tokens = self._section_tokens[idx]
        if not section_tokens:
            return 0.0

        tf = Counter(section_tokens)
        section_len = len(section_tokens)
        score = 0.0

        for qt in query_tokens:
            if qt not in tf:
                continue

            # Term frequency (normalized)
            term_freq = tf[qt] / section_len

            # Inverse document frequency
            doc_freq = self._df.get(qt, 0)
            if doc_freq == 0:
                continue
            idf = math.log((self._doc_count + 1) / (doc_freq + 1)) + 1

            score += term_freq * idf

        # Boost sections whose heading matches query tokens
        heading_tokens = set(_tokenize(section.heading))
        heading_matches = sum(1 for qt in query_tokens if qt in heading_tokens)
        if heading_matches:
            score *= 1.0 + (heading_matches * 0.5)

        # Boost sections with code examples if query mentions code/example
        code_query_terms = {"example", "code", "sample", "snippet", "python", "script"}
        if section.code_examples and code_query_terms & set(query_tokens):
            score *= 1.3

        return score

    def _substring_fallback(
        self,
        query: str,
        api_type: Optional[str],
    ) -> list[tuple[float, int]]:
        """Fall back to simple substring matching."""
        query_lower = query.lower()
        results: list[tuple[float, int]] = []

        for idx, section in enumerate(self._sections):
            if api_type and section.api_type != api_type:
                continue
            if query_lower in section.content.lower():
                # Score by number of occurrences
                count = section.content.lower().count(query_lower)
                results.append((count * 0.1, idx))

        results.sort(key=lambda x: x[0], reverse=True)
        return results


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_snippet(content: str, query: str, max_len: int = 500) -> str:
    """
    Extract a snippet from content centered around the first occurrence
    of the query (or its tokens). Falls back to the beginning of the content.
    """
    query_lower = query.lower()
    content_lower = content.lower()

    # Try to find the query as a substring
    pos = content_lower.find(query_lower)

    if pos == -1:
        # Try individual tokens
        for token in _tokenize(query):
            pos = content_lower.find(token)
            if pos != -1:
                break

    if pos == -1:
        # No match found, use beginning
        pos = 0

    # Center the snippet around the match
    start = max(0, pos - max_len // 4)
    end = min(len(content), start + max_len)

    snippet = content[start:end].strip()

    # Clean up: don't start/end mid-word
    if start > 0:
        first_space = snippet.find(" ")
        if first_space > 0 and first_space < 30:
            snippet = "..." + snippet[first_space:]
    if end < len(content):
        last_space = snippet.rfind(" ")
        if last_space > len(snippet) - 30:
            snippet = snippet[:last_space] + "..."

    return snippet
