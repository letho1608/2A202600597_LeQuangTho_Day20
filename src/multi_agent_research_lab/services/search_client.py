"""Search client abstraction for ResearcherAgent."""

import logging

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import SourceDocument

logger = logging.getLogger(__name__)


class SearchClient:
    """Provider-agnostic search client with Tavily or mock fallback."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query."""
        if self._settings.tavily_api_key:
            return self._search_tavily(query, max_results)
        return self._search_mock(query, max_results)

    def _search_tavily(self, query: str, max_results: int) -> list[SourceDocument]:
        """Search using Tavily API."""
        from tavily import TavilyClient

        client = TavilyClient(api_key=self._settings.tavily_api_key)
        results = client.search(query=query, max_results=max_results)

        docs = []
        for r in results.get("results", []):
            docs.append(
                SourceDocument(
                    title=r.get("title", ""),
                    url=r.get("url"),
                    snippet=r.get("content", ""),
                    metadata={"score": r.get("score", 0)},
                )
            )
        logger.info("Tavily search: query=%s, results=%d", query[:50], len(docs))
        return docs

    def _search_mock(self, query: str, max_results: int) -> list[SourceDocument]:
        """Return mock results when no search provider is configured."""
        logger.info("Using mock search for query: %s", query[:50])
        mock_docs = [
            SourceDocument(
                title=f"Research result for: {query[:30]}...",
                url="https://example.com/result1",
                snippet=f"This is a mock research result about {query[:50]}. "
                "It provides an overview of the topic and key findings.",
                metadata={"source": "mock"},
            ),
            SourceDocument(
                title=f"Technical paper on: {query[:30]}...",
                url="https://example.com/result2",
                snippet=f"A technical analysis of {query[:50]}, covering methodologies and results.",
                metadata={"source": "mock"},
            ),
            SourceDocument(
                title=f"Review of: {query[:30]}...",
                url="https://example.com/result3",
                snippet=f"A comprehensive review of recent advances in {query[:50]}.",
                metadata={"source": "mock"},
            ),
        ]
        return mock_docs[:max_results]
