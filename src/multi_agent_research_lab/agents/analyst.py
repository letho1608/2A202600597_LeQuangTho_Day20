"""Analyst agent skeleton."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span

logger = logging.getLogger(__name__)


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self) -> None:
        self._llm = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""
        with trace_span("analyst") as span:
            system_prompt = (
                "You are a research analyst. Given research notes, extract: "
                "1) Key claims with supporting evidence, "
                "2) Conflicting viewpoints or gaps, "
                "3) Strength of evidence assessment. "
                "Be concise and structured."
            )
            user_prompt = (
                f"Research notes:\n\n{state.research_notes}\n\n"
                "Provide structured analysis."
            )

            response = self._llm.complete(system_prompt, user_prompt)
            state.analysis_notes = response.content

            state.agent_results.append(
                AgentResult(agent=AgentName.ANALYST, content=response.content)
            )
            state.add_trace_event("analyst", {"analysis_length": len(response.content)})
            logger.info("Analyst: generated %d chars of analysis", len(response.content))

        return state
