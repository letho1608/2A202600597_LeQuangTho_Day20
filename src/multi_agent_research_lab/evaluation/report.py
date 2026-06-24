"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown with analysis."""
    lines = [
        "# Benchmark Report: Single-Agent vs Multi-Agent",
        "",
        "## Summary",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality | Notes |",
        "|---|---:|---:|---:|---|",
    ]

    for item in metrics:
        cost = "N/A" if item.estimated_cost_usd is None else f"${item.estimated_cost_usd:.4f}"
        quality = "N/A" if item.quality_score is None else f"{item.quality_score:.1f}/10"
        lines.append(f"| {item.run_name} | {item.latency_seconds:.2f} | {cost} | {quality} | {item.notes} |")

    lines.extend(["", "## Analysis", ""])

    if len(metrics) >= 2:
        baseline = next((m for m in metrics if m.run_name == "baseline"), metrics[0])
        multi = next((m for m in metrics if m.run_name == "multi-agent"), metrics[1])

        latency_diff = multi.latency_seconds - baseline.latency_seconds
        pct = (latency_diff / baseline.latency_seconds * 100) if baseline.latency_seconds > 0 else 0

        lines.append(f"- **Latency**: Multi-agent is {latency_diff:+.2f}s ({pct:+.1f}%) compared to baseline")

        if baseline.estimated_cost_usd and multi.estimated_cost_usd:
            cost_diff = multi.estimated_cost_usd - baseline.estimated_cost_usd
            lines.append(f"- **Cost**: Multi-agent is ${cost_diff:+.4f} compared to baseline")

        if baseline.quality_score is not None and multi.quality_score is not None:
            q_diff = multi.quality_score - baseline.quality_score
            lines.append(f"- **Quality**: Multi-agent is {q_diff:+.1f} points compared to baseline")

    lines.extend([
        "",
        "## Methodology",
        "",
        "- Latency measured via wall-clock time",
        "- Cost estimated from token usage (gpt-4o-mini pricing)",
        "- Quality scored on citation count and error presence",
        "",
    ])

    return "\n".join(lines) + "\n"
