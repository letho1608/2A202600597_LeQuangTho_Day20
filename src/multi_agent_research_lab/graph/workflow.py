"""LangGraph workflow skeleton."""

import logging

from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.agents.critic import CriticAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span

logger = logging.getLogger(__name__)

from langgraph.graph import StateGraph, START, END

logger = logging.getLogger(__name__)

AGENT_MAP = {
    "researcher": lambda: ResearcherAgent(),
    "analyst": lambda: AnalystAgent(),
    "writer": lambda: WriterAgent(),
    "critic": lambda: CriticAgent(),
}


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph using LangGraph."""

    def __init__(self) -> None:
        self._supervisor = SupervisorAgent()
        self.app = None

    def build(self) -> None:
        """Build the LangGraph StateGraph."""
        workflow = StateGraph(ResearchState)

        # Add nodes
        workflow.add_node("supervisor", self._supervisor.run)
        workflow.add_node("researcher", AGENT_MAP["researcher"]().run)
        workflow.add_node("analyst", AGENT_MAP["analyst"]().run)
        workflow.add_node("writer", AGENT_MAP["writer"]().run)
        
        # Add critic if it exists in AGENT_MAP
        if "critic" in AGENT_MAP:
            workflow.add_node("critic", AGENT_MAP["critic"]().run)

        # Add edges
        workflow.add_edge(START, "supervisor")

        # Conditional routing from supervisor
        def router(state: ResearchState) -> str:
            route = state.route_history[-1] if state.route_history else "done"
            if route == "done":
                return END
            return route

        workflow.add_conditional_edges("supervisor", router)

        # Workers always return to supervisor
        workflow.add_edge("researcher", "supervisor")
        workflow.add_edge("analyst", "supervisor")
        workflow.add_edge("writer", "supervisor")
        if "critic" in AGENT_MAP:
            workflow.add_edge("critic", "supervisor")

        self.app = workflow.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the LangGraph workflow and return final state."""
        if not self.app:
            self.build()

        with trace_span("multi_agent_workflow", {"query": state.request.query}):
            logger.info("Starting LangGraph workflow")
            
            # Note: langgraph invoke returns a dict if the state isn't strictly Pydantic validated internally,
            # but langgraph >=0.2 supports returning the Pydantic model directly. 
            # We handle both just in case.
            result = self.app.invoke(state)
            if isinstance(result, dict):
                return ResearchState(**result)
            return result
