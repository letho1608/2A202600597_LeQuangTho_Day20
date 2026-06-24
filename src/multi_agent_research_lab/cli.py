"""Command-line entrypoint for the lab starter."""

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.storage import LocalArtifactStore

app = typer.Typer(help="Multi-Agent Research Lab CLI")
console = Console()
logger = logging.getLogger(__name__)


def _init() -> None:
    from dotenv import load_dotenv
    load_dotenv()
    settings = get_settings()
    configure_logging(settings.log_level)


def _run_baseline(query: str) -> ResearchState:
    """Single-agent baseline: one LLM call does everything."""
    llm = LLMClient()
    state = ResearchState(request=ResearchQuery(query=query))

    system_prompt = (
        "You are a research assistant. Answer the following query thoroughly. "
        "Include key findings, analysis, and cite sources where possible."
    )
    response = llm.complete(system_prompt, query)
    state.final_answer = response.content
    state.add_trace_event("baseline", {"answer_length": len(response.content)})
    return state


def _run_multi_agent(query: str) -> ResearchState:
    """Multi-agent workflow via supervisor loop."""
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    return workflow.run(state)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a single-agent baseline."""
    _init()
    try:
        state = _run_baseline(query)
    except Exception as exc:
        console.print(Panel.fit(f"Error: {exc}", title="Baseline Failed", style="red"))
        raise typer.Exit(code=1) from exc

    console.print(Panel.fit(state.final_answer or "No answer generated", title="Single-Agent Baseline"))


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow."""
    _init()
    try:
        result = _run_multi_agent(query)
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc
    except Exception as exc:
        console.print(Panel.fit(f"Error: {exc}", title="Multi-Agent Failed", style="red"))
        raise typer.Exit(code=1) from exc

    console.print(result.final_answer or "No answer generated")


@app.command()
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run benchmark comparing single-agent vs multi-agent."""
    _init()
    console.print("[bold]Running benchmark...[/bold]")

    _, baseline_metrics = run_benchmark("baseline", query, _run_baseline)
    console.print(f"  Baseline: {baseline_metrics.latency_seconds:.2f}s")

    _, multi_metrics = run_benchmark("multi-agent", query, _run_multi_agent)
    console.print(f"  Multi-agent: {multi_metrics.latency_seconds:.2f}s")

    report_md = render_markdown_report([baseline_metrics, multi_metrics])
    store = LocalArtifactStore(Path("reports"))
    report_path = store.write_text("benchmark_report.md", report_md)
    console.print(f"\n[green]Report saved to {report_path}[/green]")
    console.print(report_md)


if __name__ == "__main__":
    app()
