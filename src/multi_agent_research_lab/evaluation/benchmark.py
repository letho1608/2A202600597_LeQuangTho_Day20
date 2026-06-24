"""Benchmark skeleton for single-agent vs multi-agent."""

import logging
from time import perf_counter
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState

logger = logging.getLogger(__name__)

Runner = Callable[[str], ResearchState]


def _estimate_cost(state: ResearchState) -> float | None:
    """Estimate cost from agent results."""
    total_cost = 0.0
    for result in state.agent_results:
        meta = result.metadata
        if "cost_usd" in meta:
            total_cost += meta["cost_usd"]
    return total_cost if total_cost > 0 else None


def _count_citations(state: ResearchState) -> int:
    """Count inline citations in the final answer."""
    if not state.final_answer:
        return 0
    import re
    return len(re.findall(r"\[\d+\]", state.final_answer))


def run_benchmark(run_name: str, query: str, runner: Runner) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, track cost, and return metrics."""
    started = perf_counter()
    try:
        state = runner(query)
        latency = perf_counter() - started
    except Exception as exc:
        latency = perf_counter() - started
        state = ResearchState(request=ResearchQuery(query=query))
        state.errors.append(str(exc))
        logger.error("Benchmark run '%s' failed: %s", run_name, exc)

    cost = _estimate_cost(state)
    citations = _count_citations(state)
    has_error = len(state.errors) > 0

    quality_score = None
    if state.final_answer:
        quality_score = min(10.0, 5.0 + citations * 0.5 + (0 if has_error else 2.0))

    notes_parts = []
    if citations > 0:
        notes_parts.append(f"{citations} citations")
    if has_error:
        notes_parts.append("errors occurred")

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=cost,
        quality_score=quality_score,
        notes="; ".join(notes_parts),
    )
    logger.info("Benchmark '%s': latency=%.2fs, cost=%s", run_name, latency, cost)
    return state, metrics
