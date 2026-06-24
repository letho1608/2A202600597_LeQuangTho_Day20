"""Optional critic agent skeleton for bonus work."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span

logger = logging.getLogger(__name__)


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def __init__(self) -> None:
        self._llm = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""
        with trace_span("critic") as span:
            source_summary = "\n".join(
                f"[{i+1}] {s.title}" for i, s in enumerate(state.sources)
            )

            system_prompt = (
                "You are a fact-checker. Review the final answer against the original sources. "
                "Check for: unsupported claims, citation accuracy, hallucination. "
                "Return a brief verification report."
            )
            user_prompt = (
                f"Final answer:\n{state.final_answer}\n\n"
                f"Sources:\n{source_summary}\n\n"
                "Provide verification findings."
            )

            response = self._llm.complete(system_prompt, user_prompt)

            state.agent_results.append(
                AgentResult(agent=AgentName.CRITIC, content=response.content)
            )
            state.add_trace_event("critic", {"findings": response.content[:200]})
            logger.info("Critic: verification complete")

        return state
