"""Writer agent skeleton."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span

logger = logging.getLogger(__name__)


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self) -> None:
        self._llm = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""
        with trace_span("writer") as span:
            audience = state.request.audience

            system_prompt = (
                f"You are a technical writer for {audience}. "
                "Given research notes and analysis, write a clear, well-structured final answer. "
                "Include citations where appropriate. Be concise but thorough."
            )
            user_prompt = (
                f"Original query: {state.request.query}\n\n"
                f"Research notes:\n{state.research_notes}\n\n"
                f"Analysis:\n{state.analysis_notes}\n\n"
                "Write the final answer."
            )

            response = self._llm.complete(system_prompt, user_prompt)
            state.final_answer = response.content

            state.agent_results.append(
                AgentResult(agent=AgentName.WRITER, content=response.content)
            )
            state.add_trace_event("writer", {"answer_length": len(response.content)})
            logger.info("Writer: generated %d chars final answer", len(response.content))

        return state
