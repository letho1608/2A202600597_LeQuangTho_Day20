"""Tests for agent implementations."""

import pytest

from multi_agent_research_lab.agents import (
    AnalystAgent,
    CriticAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.core.schemas import ResearchQuery, AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_routes_to_researcher() -> None:
    state = ResearchState(request=ResearchQuery(query="Test query"))
    supervisor = SupervisorAgent()
    result = supervisor.run(state)
    assert result.route_history[-1] == "researcher"


def test_supervisor_routes_to_analyst_after_research() -> None:
    state = ResearchState(request=ResearchQuery(query="Test query"))
    state.research_notes = "Some research notes"
    supervisor = SupervisorAgent()
    result = supervisor.run(state)
    assert result.route_history[-1] == "analyst"


def test_supervisor_routes_to_writer_after_analysis() -> None:
    state = ResearchState(request=ResearchQuery(query="Test query"))
    state.research_notes = "Some research notes"
    state.analysis_notes = "Some analysis"
    supervisor = SupervisorAgent()
    result = supervisor.run(state)
    assert result.route_history[-1] == "writer"


def test_supervisor_routes_to_done_when_complete() -> None:
    state = ResearchState(request=ResearchQuery(query="Test query"))
    state.research_notes = "notes"
    state.analysis_notes = "analysis"
    state.final_answer = "answer"
    state.agent_results.append(AgentResult(agent=AgentName.CRITIC, content="ok"))

    supervisor = SupervisorAgent()
    result = supervisor.run(state)

    assert result.route_history[-1] == "done"


def test_supervisor_respects_max_iterations() -> None:
    state = ResearchState(request=ResearchQuery(query="Test query"))
    state.iteration = 10
    supervisor = SupervisorAgent()
    result = supervisor.run(state)
    assert result.route_history[-1] == "done"
