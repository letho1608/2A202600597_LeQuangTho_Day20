"""Tracing hooks.

This file intentionally avoids binding to one provider. Students can plug in LangSmith,
Langfuse, OpenTelemetry, or simple JSON traces.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Minimal span context used by the skeleton.

    """
    import os
    import logging
    tracer_logger = logging.getLogger("tracing")
    tracer_logger.debug("Span started: %s, attributes: %s", name, attributes)
    
    rt = None
    if os.environ.get("LANGSMITH_API_KEY"):
        try:
            from langsmith import RunTree
            rt = RunTree(
                name=name,
                run_type="chain",
                inputs=attributes or {}
            )
            rt.post()
        except ImportError:
            tracer_logger.warning("langsmith not installed")

    lf_span = None
    lf = None
    if os.environ.get("LANGFUSE_PUBLIC_KEY"):
        try:
            from langfuse import Langfuse
            lf = Langfuse()
            lf_span = lf.start_observation(name=name, as_type="span", input=attributes or {})
        except ImportError:
            tracer_logger.warning("langfuse not installed")

    started = perf_counter()
    span: dict[str, Any] = {"name": name, "attributes": attributes or {}, "duration_seconds": None}
    try:
        yield span
        if rt:
            rt.end(outputs=span)
            rt.patch()
            if hasattr(rt, "get_url") and name in ("multi_agent_workflow", "baseline"):
                tracer_logger.info("LangSmith Trace URL: %s", rt.get_url())
        if lf_span:
            lf_span.update(output=span).end()
            if name in ("multi_agent_workflow", "baseline") and hasattr(lf, "get_trace_url"):
                url = lf.get_trace_url(trace_id=lf_span.trace_id)
                if url:
                    tracer_logger.info("Langfuse Trace URL: %s", url)
    except Exception as e:
        if rt:
            rt.end(error=str(e))
            rt.patch()
        if lf_span:
            lf_span.update(status_message=str(e), level="ERROR").end()
        raise
    finally:
        span["duration_seconds"] = perf_counter() - started
