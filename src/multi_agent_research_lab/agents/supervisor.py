"""Supervisor / router skeleton."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.state import ResearchState

logger = logging.getLogger(__name__)


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self) -> None:
        self._settings = get_settings()

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route.

        Routing policy:
        - If no research_notes yet -> route to researcher
        - If no analysis_notes yet -> route to analyst
        - If no final_answer yet -> route to writer
        - If all done or max iterations reached -> done
        """
        max_iter = self._settings.max_iterations

        if state.iteration >= max_iter:
            logger.warning("Max iterations (%d) reached, forcing done", max_iter)
            state.record_route("done")
            state.add_trace_event("supervisor", {"decision": "done", "reason": "max_iterations"})
            return state

        if not state.research_notes:
            route = "researcher"
        elif not state.analysis_notes:
            route = "analyst"
        elif not state.final_answer:
            route = "writer"
        elif not any(r.agent == "critic" for r in state.agent_results):
            route = "critic"
        else:
            route = "done"

        state.record_route(route)
        state.add_trace_event("supervisor", {"decision": route, "iteration": state.iteration})
        logger.info("Supervisor routing to: %s (iteration %d)", route, state.iteration)

        return state
