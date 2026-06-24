"""Researcher agent skeleton."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span

logger = logging.getLogger(__name__)


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self) -> None:
        self._llm = LLMClient()
        self._search = SearchClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        with trace_span("researcher", {"query": state.request.query}) as span:
            query = state.request.query
            max_sources = state.request.max_sources

            docs = self._search.search(query, max_results=max_sources)
            state.sources = docs
            span["attributes"]["sources_found"] = len(docs)

            source_text = "\n".join(
                f"[{i+1}] {d.title}\n{d.snippet}" for i, d in enumerate(docs)
            )

            system_prompt = (
                "You are a research assistant. Given the following sources, "
                "write a concise research notes document. "
                "Cite sources using [N] notation. Focus on key facts and findings."
            )
            user_prompt = f"Query: {query}\n\nSources:\n{source_text}"

            response = self._llm.complete(system_prompt, user_prompt)
            state.research_notes = response.content

            state.agent_results.append(
                AgentResult(agent=AgentName.RESEARCHER, content=response.content)
            )
            state.add_trace_event("researcher", {
                "sources": len(docs),
                "notes_length": len(response.content),
            })
            logger.info("Researcher: collected %d sources, generated notes", len(docs))

        return state
